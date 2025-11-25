
import os
import sys
import django
from django.core.management import call_command

# Setup Django
sys.path.append('c:/Users/shyam/OneDrive/Desktop/assignment/task-analyzer/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_analyzer.settings')
django.setup()

def run_migrations():
    with open('migration_log.txt', 'w') as log:
        sys.stdout = log
        sys.stderr = log
        print("Starting migration process...")
        
        # Ensure migrations directory exists
        migrations_dir = os.path.join('c:/Users/shyam/OneDrive/Desktop/assignment/task-analyzer/backend/tasks', 'migrations')
        if not os.path.exists(migrations_dir):
            print(f"Creating migrations directory: {migrations_dir}")
            os.makedirs(migrations_dir)
            with open(os.path.join(migrations_dir, '__init__.py'), 'w') as f:
                pass
        
        try:
            print("Running makemigrations tasks...")
            call_command('makemigrations', 'tasks')
            print("makemigrations success")
        except Exception as e:
            print(f"makemigrations failed: {e}")
            import traceback
            traceback.print_exc()
            
        try:
            print("Running migrate...")
            call_command('migrate')
            print("migrate success")
        except Exception as e:
            print(f"migrate failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    run_migrations()
