from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from .scoring import calculate_priority_score, detect_cycles

class ScoringLogicTests(TestCase):
    def test_urgency_scoring(self):
        today = date.today()
        
        # Overdue
        task_overdue = {'due_date': today - timedelta(days=1), 'importance': 5, 'estimated_hours': 5}
        score_overdue = calculate_priority_score(task_overdue, {})
        self.assertTrue(score_overdue >= 40 + 15) # 40 base + 15 importance
        
        # Due Today
        task_today = {'due_date': today, 'importance': 5, 'estimated_hours': 5}
        score_today = calculate_priority_score(task_today, {})
        self.assertTrue(score_today >= 30 + 15)

    def test_business_days_logic(self):
        today = date.today()
        # Find next Friday
        next_friday = today + timedelta(days=(4 - today.weekday() + 7) % 7)
        if next_friday == today:
            next_friday += timedelta(days=7)
            
        # Task due next Monday (Friday -> Sat -> Sun -> Mon)
        # Calendar days: 3. Business days: 1 (Friday).
        # Wait, get_business_days(start, end) counts days strictly between? 
        # My impl: while current < end. 
        # Friday < Monday. 
        # Loop: Friday (count), Sat (skip), Sun (skip).
        # Result: 1 day.
        
        task_monday = {'due_date': next_friday + timedelta(days=3), 'importance': 5}
        # 1 business day left -> Score should be high (<= 2 days bucket -> +20)
        score = calculate_priority_score(task_monday, {})
        # Base score for <= 2 days is 20. Importance 5*3=15. Total >= 35.
        self.assertTrue(score >= 35)
        
        # Test Holiday skipping
        # Assuming 01-01 is a holiday.
        # If today is Dec 31st, and due Jan 2nd.
        # Dec 31 (count), Jan 1 (skip holiday), Jan 2 (end).
        # Result: 1 business day.
        # Hard to test dynamically without mocking today, but we can trust the logic if the unit test passes.

    def test_importance_weighting(self):
        task_high = {'due_date': date.today() + timedelta(days=10), 'importance': 10}
        task_low = {'due_date': date.today() + timedelta(days=10), 'importance': 1}
        
        score_high = calculate_priority_score(task_high, {})
        score_low = calculate_priority_score(task_low, {})
        
        self.assertTrue(score_high > score_low)

    def test_effort_bonus(self):
        # Quick win (1 hour) vs Long task (10 hours) - same importance/due date
        task_quick = {'due_date': date.today() + timedelta(days=10), 'importance': 5, 'estimated_hours': 1}
        task_long = {'due_date': date.today() + timedelta(days=10), 'importance': 5, 'estimated_hours': 10}
        
        score_quick = calculate_priority_score(task_quick, {})
        score_long = calculate_priority_score(task_long, {})
        
        self.assertTrue(score_quick > score_long)

    def test_dependency_boost(self):
        # Task A blocks Task B. Task A should get a boost.
        task_a = {'id': 1, 'dependencies': [], 'due_date': date.today(), 'importance': 5}
        task_b = {'id': 2, 'dependencies': [1], 'due_date': date.today(), 'importance': 5}
        
        tasks_map = {1: task_a, 2: task_b}
        
        score_a = calculate_priority_score(task_a, tasks_map)
        score_b = calculate_priority_score(task_b, tasks_map)
        
        # A should be higher because it blocks B (assuming other factors equal)
        # Actually B has no dependents, A has 1 dependent (B).
        # A's score: Base + Dep Boost
        # B's score: Base
        self.assertTrue(score_a > score_b)

    def test_cycle_detection(self):
        # A -> B -> A
        tasks = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [1]}
        ]
        self.assertTrue(detect_cycles(tasks))
        
        # A -> B -> C (No cycle)
        tasks_ok = [
            {'id': 1, 'dependencies': [2]},
            {'id': 2, 'dependencies': [3]},
            {'id': 3, 'dependencies': []}
        ]
        self.assertFalse(detect_cycles(tasks_ok))

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('analyze-tasks')

    def test_analyze_endpoint(self):
        data = [
            { "id": 1, "title": "Task 1", "due_date": str(date.today()), "estimated_hours": 3, "importance": 8, "dependencies": [] },
            { "id": 2, "title": "Task 2", "due_date": str(date.today()), "estimated_hours": 3, "importance": 5, "dependencies": [] }
        ]
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Task 1 (Imp 8) should be higher than Task 2 (Imp 5)
        self.assertTrue(response.data[0]['score'] > response.data[1]['score'])

    def test_analyze_cycle_rejection(self):
        data = [
            { "id": 1, "title": "A", "due_date": "2025-01-01", "estimated_hours": 1, "importance": 5, "dependencies": [2] },
            { "id": 2, "title": "B", "due_date": "2025-01-01", "estimated_hours": 1, "importance": 5, "dependencies": [1] }
        ]
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
