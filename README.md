# Smart Task Analyzer

A mini-application that intelligently scores and prioritizes tasks based on urgency, importance, effort, and dependencies.

## Setup Instructions

### Prerequisites

- Python 3.8+
- Django 4.0+

### Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations to set up the database:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://localhost:8000/api/tasks/analyze/`.

### Frontend Setup

1. Navigate to the `frontend` directory.
2. Open `index.html` in your web browser.
   - You can simply double-click the file or serve it using a local server (e.g., `python -m http.server` inside `frontend`).

## Algorithm Explanation

The core of the Smart Task Analyzer is the "Smart Balance" scoring algorithm, designed to surface the most impactful tasks while preventing "analysis paralysis." The scoring logic calculates a numerical priority score for each task based on four key dimensions. The algorithm is implemented in `backend/tasks/scoring.py`.

**1. Urgency (Time Sensitivity)**
The algorithm first evaluates the temporal pressure of a task. It calculates the difference between the `due_date` and today.

- **Overdue Tasks**: These are treated as critical emergencies. Any task with a negative "days remaining" value receives a massive base score boost (+40) to ensure it jumps to the top of the queue immediately.
- **Imminent Deadlines**: Tasks due today (+30) or within the next 2 days (+20) receive significant boosts.
- **Approaching Deadlines**: Tasks due within a week get a moderate bump (+10).
  This non-linear scaling ensures that as a deadline approaches, the task naturally climbs the priority list without user intervention.

**2. Importance (Strategic Value)**
User-defined importance (1-10 scale) acts as a multiplier. We multiply the importance rating by a factor of 3. This means a highly important task (10/10) contributes 30 points to the score, roughly equivalent to a task being due "today." This balance allows important long-term tasks to compete with urgent but trivial ones, preventing the "tyranny of the urgent."

**3. Effort (Momentum & Quick Wins)**
To encourage productivity momentum, the algorithm rewards "Quick Wins."

- **Low Effort (< 2 hours)**: Tasks estimated to take less than 2 hours receive a +15 point bonus. This psychological trick encourages users to clear small tasks quickly, reducing mental clutter.
- **High Effort (> 20 hours)**: Very large tasks receive a slight penalty (-5). This subtle "friction" encourages users to break large tasks down into smaller sub-tasks, as smaller tasks will naturally score higher.

**4. Dependencies (Blocking Power)**
A unique feature of this system is its awareness of task relationships. A task that blocks other tasks is inherently more critical than an isolated task.

- The algorithm checks if a task ID appears in the `dependencies` list of any other task.
- For _each_ task that is blocked by the current task, the current task receives a +15 point boost.
- This ensures that "bottleneck" tasks are prioritized, unblocking the rest of the workflow.

**Cycle Detection**
Before scoring, the system runs a Depth-First Search (DFS) cycle detection algorithm. If a circular dependency is found (e.g., A blocks B, and B blocks A), the system rejects the input with a 400 error, preventing infinite logic loops and forcing the user to resolve the logical fallacy.

## Design Decisions & Trade-offs

**1. Stateless Analysis Endpoint**

- **Decision**: The `/analyze` endpoint accepts a list of tasks and returns them sorted, without necessarily saving them to the database.
- **Reasoning**: This allows for a flexible "What-If" analysis. Users can paste a JSON blob to see how priorities shift without polluting their persistent database. It perfectly supports the "Bulk Import" requirement.
- **Trade-off**: Data persistence is separate. If the browser is refreshed, the "analyzed" state is lost unless explicitly saved (which is handled by the `suggest` endpoint flow or future save features).

**2. Client-Side vs. Server-Side Sorting**

- **Decision**: The "Smart Balance" score is calculated on the server, but the "Fastest Wins" and "Deadline" sorting is handled on the client side.
- **Reasoning**: "Smart Balance" requires complex business logic (dependency graph traversal) that belongs on the backend. Simple property sorts (by date or hours) are instant on the frontend and don't require a round-trip, providing a snappier UX.

**3. Cycle Detection Strategy**

- **Decision**: Strict rejection of cycles.
- **Reasoning**: Allowing cycles in a dependency graph makes prioritization mathematically impossible (which comes first?). Rejecting the input with a clear error message is the safest and most correct approach for a dependency-based system.

## Time Breakdown

- **Backend Development (1.5 hours)**:
  - Project setup & configuration: 15 mins
  - Task Model & API Views: 30 mins
  - Scoring Algorithm & Cycle Detection: 45 mins
- **Frontend Development (1.5 hours)**:
  - HTML Structure & CSS Styling: 45 mins
  - JS Logic (API integration, UI updates): 45 mins
- **Testing & Documentation (1 hour)**:
  - Unit Tests: 30 mins
  - README & Walkthrough: 30 mins

## Bonus Challenges Attempted

- **Cycle Detection**: Implemented a graph-based cycle detection algorithm to validate dependencies.
- **Bulk Import**: Added a dedicated JSON import tab for power users.
- **Strategy Toggle**: Implemented a dynamic switcher to re-order tasks based on different user needs (Speed vs. Impact vs. Deadline).
- **Visual Priority Indicators**: Added color-coded badges (Red/Orange/Green) based on the calculated score thresholds.

## Future Improvements

- **User Authentication**: Allow multiple users to manage their own private task lists.
- **Persistent "Analyze"**: Save the results of the bulk analysis to the database.
- **Drag-and-Drop Dependencies**: A visual graph editor to draw lines between tasks to set dependencies.
- **Sub-tasks**: Native support for breaking down large tasks, automatically inheriting priority from the parent.
