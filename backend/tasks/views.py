from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TaskAnalysisSerializer, TaskSerializer
from .scoring import calculate_priority_score, detect_cycles, get_score_explanation
from .models import Task

class AnalyzeTasksView(APIView):
    def post(self, request):
        # Allow single object or list
        data = request.data
        if not isinstance(data, list):
            data = [data]
            
        serializer = TaskAnalysisSerializer(data=data, many=True)
        if serializer.is_valid():
            tasks = serializer.validated_data
            
            # Check cycles
            if detect_cycles(tasks):
                return Response(
                    {"error": "Circular dependencies detected. Please resolve dependencies before analyzing."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Map for O(1) lookup
            tasks_map = {t.get('id'): t for t in tasks if t.get('id') is not None}
            
            # Calculate scores
            results = []
            for task in tasks:
                score = calculate_priority_score(task, tasks_map)
                explanation = get_score_explanation(task, score, tasks_map)
                
                # Convert OrderedDict to dict for response
                task_data = dict(task)
                task_data['score'] = score
                task_data['explanation'] = explanation
                results.append(task_data)
            
            # Sort by score desc
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return Response(results)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SuggestTasksView(APIView):
    def get(self, request):
        db_tasks = Task.objects.all()
        if not db_tasks.exists():
            return Response([])
            
        tasks_data = TaskSerializer(db_tasks, many=True).data
        tasks_map = {t['id']: t for t in tasks_data}
        
        scored_tasks = []
        for task in tasks_data:
            score = calculate_priority_score(task, tasks_map)
            explanation = get_score_explanation(task, score, tasks_map)
            task['score'] = score
            task['explanation'] = explanation
            scored_tasks.append(task)
            
        scored_tasks.sort(key=lambda x: x['score'], reverse=True)
        return Response(scored_tasks[:3])
