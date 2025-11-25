
import os
import django
import sys

# Setup Django environment
sys.path.append('c:/Users/shyam/OneDrive/Desktop/assignment/task-analyzer/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_analyzer.settings')
django.setup()

from tasks.models import Task
from tasks.scoring import detect_cycles
from tasks.views import AnalyzeTasksView
from rest_framework.test import APIRequestFactory

def verify_fix():
    print("Verifying fix...")
    sys.stdout.flush()
    
    # Clean up
    Task.objects.all().delete()
    
    # Create Task A in DB
    task_a = Task.objects.create(
        title="A", 
        due_date="2025-01-01", 
        estimated_hours=1, 
        importance=5
    )
    print(f"Created Task A: {task_a.id}")
    sys.stdout.flush()
    
    # Create Task B in DB
    task_b = Task.objects.create(
        title="B",
        due_date="2025-01-01",
        estimated_hours=1,
        importance=5
    )
    print(f"Created Task B: {task_b.id}")
    
    # A depends on B
    task_a.dependencies.add(task_b)
    print(f"Task A depends on Task B")
    
    # Request: Update B to depend on A.
    # Cycle: B -> A -> B
    data = [
        {
            "id": task_b.id,
            "title": "B",
            "due_date": "2025-01-01",
            "estimated_hours": 1,
            "importance": 5,
            "dependencies": [task_a.id]
        }
    ]
    
    # We need to test the View logic because that's where the fetcher is defined.
    factory = APIRequestFactory()
    view = AnalyzeTasksView.as_view()
    request = factory.post('/api/tasks/analyze/', data, format='json')
    
    response = view(request)
    print(f"Response Status: {response.status_code}")
    print(f"Response Data: {response.data}")
    
    if response.status_code == 400 and "Circular dependencies detected" in str(response.data):
        print("SUCCESS: Cycle detected!")
    else:
        print("FAILURE: Cycle NOT detected!")

if __name__ == "__main__":
    verify_fix()
