
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

# Test Case 1: Simple Cycle
tasks1 = [
    {"id": 7, "dependencies": [6]},
    {"id": 6, "dependencies": [9]},
    {"id": 9, "dependencies": [7]}
]
print(f"Test Case 1 (7->6->9->7): {detect_cycles(tasks1)}")

# Test Case 2: User's Example (Interpretation A)
# "one with 7,6,9 and the other with 7,8,10"
# Maybe they mean:
# Task 1 (id=1): deps [7, 6, 9]
# Task 2 (id=2): deps [7, 8, 10]
# And existing tasks 7, 6, 9, 8, 10 have no cycles among themselves?
tasks2 = [
    {"id": 1, "dependencies": [7, 6, 9]},
    {"id": 2, "dependencies": [7, 8, 10]},
    {"id": 7, "dependencies": []},
    {"id": 6, "dependencies": []},
    {"id": 9, "dependencies": []},
    {"id": 8, "dependencies": []},
    {"id": 10, "dependencies": []}
]
print(f"Test Case 2 (No Cycle): {detect_cycles(tasks2)}")

# Test Case 3: Cycle involving tasks NOT in the payload
# Task 1 -> 7. Task 7 -> 1 (but 7 is not in payload).
tasks3 = [
    {"id": 1, "dependencies": [7]}
]
# 7 is not in graph.
print(f"Test Case 3 (External Cycle): {detect_cycles(tasks3)}")

# Test Case 4: Disconnected components with cycle
tasks4 = [
    {"id": 1, "dependencies": [2]},
    {"id": 2, "dependencies": [1]},
    {"id": 3, "dependencies": []}
]
print(f"Test Case 4 (Disconnected Cycle): {detect_cycles(tasks4)}")

# Test Case 5: Self loop
tasks5 = [
    {"id": 1, "dependencies": [1]}
]
print(f"Test Case 5 (Self Loop): {detect_cycles(tasks5)}")
