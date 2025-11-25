from datetime import date, datetime

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
    days_until_due = (due_date - today).days
    
    if days_until_due < 0:
        score += 40 # Overdue - High Priority
    elif days_until_due == 0:
        score += 30 # Due Today
    elif days_until_due <= 2:
        score += 20 # Due Soon
    elif days_until_due <= 7:
        score += 10 # Due this week
    
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

def detect_cycles(tasks):
    """
    Detect circular dependencies in a list of tasks.
    Returns True if cycle detected, False otherwise.
    """
    graph = {t.get('id'): t.get('dependencies', []) for t in tasks if t.get('id') is not None}
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
            # Only traverse if neighbor exists in our dataset
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
        days_until_due = (due_date - date.today()).days
        if days_until_due < 0:
            explanations.append("Overdue")
        elif days_until_due == 0:
            explanations.append("Due today")
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
