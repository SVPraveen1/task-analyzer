const API_URL = "http://localhost:8000/api/tasks/analyze/";

let currentTasks = [];
let analyzedTasks = [];

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupForm();
  setupControls();

  // Initial example data
  const initialData = [
    {
      id: 1,
      title: "Fix login bug",
      due_date: "2025-11-30",
      estimated_hours: 3,
      importance: 8,
      dependencies: [],
    },
    {
      id: 2,
      title: "Write documentation",
      due_date: "2025-12-05",
      estimated_hours: 2,
      importance: 5,
      dependencies: [1],
    },
    {
      id: 3,
      title: "Redesign homepage",
      due_date: "2025-11-28",
      estimated_hours: 20,
      importance: 9,
      dependencies: [],
    },
  ];
  document.getElementById("json-input").value = JSON.stringify(
    initialData,
    null,
    4
  );
  loadFromJson();
});

function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      document
        .querySelectorAll(".tab-btn")
        .forEach((b) => b.classList.remove("active"));
      document
        .querySelectorAll(".tab-content")
        .forEach((c) => c.classList.remove("active"));

      tab.classList.add("active");
      document.getElementById(`${tab.dataset.tab}-tab`).classList.add("active");
    });
  });
}

function setupForm() {
  const form = document.getElementById("task-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const newTask = {
      id: document.getElementById("task_id").value
        ? parseInt(document.getElementById("task_id").value)
        : Date.now(),
      title: document.getElementById("title").value,
      due_date: document.getElementById("due_date").value,
      estimated_hours: parseFloat(
        document.getElementById("estimated_hours").value
      ),
      importance: parseInt(document.getElementById("importance").value),
      dependencies: document.getElementById("dependencies").value
        ? document
            .getElementById("dependencies")
            .value.split(",")
            .map((id) => parseInt(id.trim()))
        : [],
    };

    currentTasks.push(newTask);
    updateJsonView();
    form.reset();
    alert("Task added to list! Check the Bulk Import tab to see all tasks.");
  });

  document
    .getElementById("load-json-btn")
    .addEventListener("click", loadFromJson);
}

function updateJsonView() {
  document.getElementById("json-input").value = JSON.stringify(
    currentTasks,
    null,
    4
  );
}

function loadFromJson() {
  try {
    const json = document.getElementById("json-input").value;
    currentTasks = JSON.parse(json);
    // alert(`Loaded ${currentTasks.length} tasks.`);
  } catch (e) {
    alert("Invalid JSON format");
  }
}

function setupControls() {
  document
    .getElementById("analyze-btn")
    .addEventListener("click", analyzeTasks);
  document.getElementById("strategy-select").addEventListener("change", (e) => {
    sortAndRender(e.target.value);
  });
}

async function analyzeTasks() {
  const loading = document.getElementById("loading");
  const errorMsg = document.getElementById("error-msg");
  const resultsContainer = document.getElementById("results-container");

  // Ensure we have the latest data
  loadFromJson();

  if (currentTasks.length === 0) {
    alert("No tasks to analyze!");
    return;
  }

  loading.classList.remove("hidden");
  errorMsg.classList.add("hidden");
  resultsContainer.innerHTML = "";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(currentTasks),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || "Failed to analyze tasks");
    }

    analyzedTasks = await response.json();
    sortAndRender(document.getElementById("strategy-select").value);
  } catch (err) {
    errorMsg.textContent = err.message;
    errorMsg.classList.remove("hidden");
  } finally {
    loading.classList.add("hidden");
  }
}

function sortAndRender(strategy) {
  if (analyzedTasks.length === 0) return;

  let sorted = [...analyzedTasks];

  switch (strategy) {
    case "fastest":
      sorted.sort((a, b) => a.estimated_hours - b.estimated_hours);
      break;
    case "impact":
      sorted.sort((a, b) => b.importance - a.importance);
      break;
    case "deadline":
      sorted.sort((a, b) => new Date(a.due_date) - new Date(b.due_date));
      break;
    case "smart":
    default:
      sorted.sort((a, b) => b.score - a.score);
      break;
  }

  renderResults(sorted);
}

function renderResults(tasks) {
  const container = document.getElementById("results-container");
  container.innerHTML = "";

  tasks.forEach((task) => {
    const scoreClass =
      task.score >= 50
        ? "score-high"
        : task.score >= 20
        ? "score-med"
        : "score-low";

    const card = document.createElement("div");
    card.className = "task-card";
    card.innerHTML = `
            <div class="task-info">
                <h3>${task.title}</h3>
                <div class="task-meta">
                    <span>Due: ${task.due_date}</span>
                    <span>Effort: ${task.estimated_hours}h</span>
                    <span>Imp: ${task.importance}/10</span>
                </div>
                <div class="explanation">💡 ${task.explanation}</div>
            </div>
            <div class="task-score">
                <span class="score-badge ${scoreClass}">${Math.round(
      task.score
    )}</span>
            </div>
        `;
    container.appendChild(card);
  });
}
