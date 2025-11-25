from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=200)
    due_date = models.DateField()
    estimated_hours = models.FloatField()
    importance = models.IntegerField(help_text="1-10 scale")
    # dependencies: Tasks that this task depends on.
    # symmetrical=False: If A depends on B, B doesn't necessarily depend on A.
    # related_name='dependents': Tasks that depend on this task.
    dependencies = models.ManyToManyField('self', symmetrical=False, related_name='dependents', blank=True)
    
    def __str__(self):
        return self.title
