from datetime import date, datetime, timedelta

def calculate_priority_score(task, all_tasks_map):
    """
    Calculate priority score for a single task.
    task: dict containing task details
    all_tasks_map: dict of {id: task_dict} for looking up relationships
    """
    score = 0
    
    # 1. Urgency
    try:
        if isinstance(task['due_date'], str):
            due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
        else:
            due_date = task['due_date']
    except (ValueError, TypeError, KeyError):
        due_date = date.today() # Default fallback

    today = date.today()
    
    def get_business_days(start, end):
        """Calculate business days between start and end date (inclusive-ish)."""
        if start > end:
            return (end - start).days # Return negative calendar days for overdue
            
        days = 0
        current = start
        # Hardcoded holidays for demonstration (Month-Day)
        holidays = ["01-01", "12-25", "07-04"] 
        
        while current < end:
            # 0=Monday, 6=Sunday. Skip 5 (Sat) and 6 (Sun)
            if current.weekday() < 5:
                # Check holiday
                md = current.strftime("%m-%d")
                if md not in holidays:
                    days += 1
            current += timedelta(days=1)
        return days

    days_until_due = get_business_days(today, due_date)
    
    if days_until_due < 0:
        score += 40 # Overdue - High Priority
    elif days_until_due == 0:
        score += 30 # Due Today
    elif days_until_due <= 2:
        score += 20 # Due in <= 2 business days
    elif days_until_due <= 5:
        score += 10 # Due in <= 1 business week (5 days)
    
    # 2. Importance (1-10)
    importance = float(task.get('importance', 5))
    score += importance * 3 # Weight importance
    
    # 3. Effort (Quick Wins)
    try:
        hours = float(task.get('estimated_hours', 0))
    except (ValueError, TypeError):
        hours = 0
        
    if hours > 0 and hours <= 2:
        score += 15 # Quick win
    elif hours <= 5:
        score += 10
    elif hours >= 20:
        score -= 5 # De-prioritize very large tasks slightly to favor momentum
        
    # 4. Dependencies (Blockers rank higher)
    # If this task blocks others, it's important.
    task_id = task.get('id')
    if task_id:
        dependents_count = 0
        for other_task in all_tasks_map.values():
            deps = other_task.get('dependencies', [])
            if task_id in deps:
                dependents_count += 1
        
        score += dependents_count * 15 # Significant boost for blockers
        
    return round(score, 2)

def detect_cycles(tasks, dependency_fetcher=None):
    """
    Detect circular dependencies in a list of tasks.
    Returns True if cycle detected, False otherwise.
    
    dependency_fetcher: Optional callable that takes a list of task IDs 
                        and returns a list of task dictionaries (with 'id' and 'dependencies').
                        Used to fetch dependencies that are not in the initial tasks list.
    """
    # Build initial graph from input tasks
    graph = {t.get('id'): t.get('dependencies', []) for t in tasks if t.get('id') is not None}
    
    # Identify dependencies that are missing from the graph
    missing_deps = set()
    for deps in graph.values():
        for dep_id in deps:
            if dep_id not in graph:
                missing_deps.add(dep_id)
                
    # Fetch missing dependencies if fetcher is provided
    if dependency_fetcher and missing_deps:
        # We might need to fetch recursively if the fetched tasks have more missing dependencies
        # Use a queue or repeated fetching. 
        # For simplicity and safety, let's do a breadth-first expansion until no new missing deps.
        
        processed_missing = set()
        
        while missing_deps:
            # Get a batch of missing IDs that we haven't processed yet
            batch = list(missing_deps - processed_missing)
            if not batch:
                break
            
            # Mark these as processed so we don't fetch them again, 
            # even if they don't exist in the DB.
            processed_missing.update(batch)
                
            fetched_tasks = dependency_fetcher(batch)
            
            # Add fetched tasks to graph
            for t in fetched_tasks:
                t_id = t.get('id')
                if t_id:
                    graph[t_id] = t.get('dependencies', [])
            
            # Check for new missing dependencies in the newly fetched tasks
            new_missing = set()
            for t in fetched_tasks:
                for dep_id in t.get('dependencies', []):
                    if dep_id not in graph and dep_id not in processed_missing:
                        new_missing.add(dep_id)
            
            missing_deps.update(new_missing)
            
            # Safety break to prevent infinite loops if fetcher returns garbage or graph is huge
            if len(graph) > 1000: # Arbitrary limit for safety
                break

    visited = set()
    path = set()

    def visit(node):
        if node in path:
            return True
        if node in visited:
            return False
        
        visited.add(node)
        path.add(node)
        
        for neighbor in graph.get(node, []):
            # Only traverse if neighbor exists in our graph
            if neighbor in graph:
                if visit(neighbor):
                    return True
        
        path.remove(node)
        return False

    for node in graph:
        if visit(node):
            return True
            
    return False

def get_score_explanation(task, score, all_tasks_map):
    """Generate a human-readable explanation for the score."""
    explanations = []
    
    # Urgency
    try:
        if isinstance(task['due_date'], str):
            due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
        else:
            due_date = task['due_date']
            
        # Re-use the business days logic (ideally refactor to shared function, but duplicating for safety in this snippet)
        def get_bd(start, end):
            if start > end: return (end - start).days
            days = 0
            current = start
            holidays = ["01-01", "12-25", "07-04"] 
            while current < end:
                if current.weekday() < 5 and current.strftime("%m-%d") not in holidays:
                    days += 1
                current += timedelta(days=1)
            return days

        days_until_due = get_bd(date.today(), due_date)
        
        if days_until_due < 0:
            explanations.append(f"Overdue by {abs(days_until_due)} days")
        elif days_until_due == 0:
            explanations.append("Due today")
        else:
            explanations.append(f"Due in {days_until_due} business days")
    except:
        pass

    # Importance
    if float(task.get('importance', 0)) >= 8:
        explanations.append("High importance")
        
    # Effort
    hours = float(task.get('estimated_hours', 0))
    if hours <= 2:
        explanations.append("Quick win")
        
    # Dependencies
    task_id = task.get('id')
    if task_id:
        dependents = [t['title'] for t in all_tasks_map.values() if task_id in t.get('dependencies', [])]
        if dependents:
            explanations.append(f"Blocks {len(dependents)} task(s)")

    return ", ".join(explanations) if explanations else "Standard priority"
