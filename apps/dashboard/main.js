import { BASE_URL, TOKEN } from "./config.js";

const runsTable = document.getElementById("runs");
const evidenceTable = document.getElementById("evidence");
const runDetail = document.getElementById("runDetail");
const evidenceDetail = document.getElementById("evidenceDetail");
const runSummary = document.getElementById("runSummary");
const evidenceSummary = document.getElementById("evidenceSummary");
const runContext = document.getElementById("runContext");
const runMetrics = document.getElementById("runMetrics");
const runHighlights = document.getElementById("runHighlights");
const runWhatIfs = document.getElementById("runWhatIfs");
const runArtifacts = document.getElementById("runArtifacts");
const evidenceArtifacts = document.getElementById("evidenceArtifacts");
const runOverview = document.getElementById("runOverview");
const evidenceOverview = document.getElementById("evidenceOverview");
const runToggle = document.getElementById("runToggle");
const evidenceToggle = document.getElementById("evidenceToggle");
const runCopy = document.getElementById("runCopy");
const evidenceCopy = document.getElementById("evidenceCopy");

const STATUS_COLORS = {
  succeeded: "#22c55e",
  completed: "#22c55e",
  running: "#0ea5e9",
  "in-progress": "#0ea5e9",
  initializing: "#0ea5e9",
  pending: "#facc15",
  created: "#facc15",
  queued: "#facc15",
  failed: "#f97316",
  error: "#ef4444",
  canceled: "#94a3b8",
  unknown: "#94a3b8",
  default: "#94a3b8",
};

function getInputs() {
  return {
    baseUrl: document.getElementById("baseUrl").value || BASE_URL,
    token: document.getElementById("token").value || TOKEN,
  };
}

async function fetchJSON(url, token, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${text}`);
  }
  return response.json();
}

async function loadRuns() {
  const { baseUrl, token } = getInputs();
  try {
    const payload = await fetchJSON(`${baseUrl}/v1/runs`, token, { method: "GET" });
    renderRuns(payload.runs ?? []);
  } catch (err) {
    alert(`Failed to load runs: ${err.message}`);
  }
}

async function loadEvidence() {
  const { baseUrl, token } = getInputs();
  try {
    const payload = await fetchJSON(`${baseUrl}/v1/evidence?limit=20`, token, { method: "GET" });
    renderEvidence(payload.items ?? []);
  } catch (err) {
    alert(`Failed to load evidence: ${err.message}`);
  }
}

function renderRuns(runs) {
  runsTable.innerHTML = "";
  updateRunOverview(runs);
  runs.forEach((run) => {
    const row = document.createElement("tr");
    const statusKey = normalizeStatus(run.status);
    row.innerHTML = `
      <td><button class="link" data-run="${run.run_id}">${run.run_id}</button></td>
      <td><span class="status-pill status-${statusKey}">${formatStatus(run.status)}</span></td>
      <td>${run.goal ?? "-"}</td>
      <td>${run.archetype_id ?? "-"}</td>
      <td>${run.result?.solution?.metadata?.solver ?? "-"}</td>
      <td>${formatDate(run.result?.solution?.metadata?.generated_at)}</td>
    `;
    runsTable.appendChild(row);
  });
}

function renderEvidence(items) {
  evidenceTable.innerHTML = "";
  updateEvidenceOverview(items);
  items.forEach((item) => {
    const artifacts = Object.keys(item.artifacts ?? {}).join(", ") || "-";
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><button class="link" data-evidence="${item.run_id}">${item.run_id}</button></td>
      <td>${formatDate(item.stored_at)}</td>
      <td>${artifacts}</td>
    `;
    evidenceTable.appendChild(row);
  });
}

runsTable.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-run]");
  if (!button) return;
  const runId = button.dataset.run;
  const { baseUrl, token } = getInputs();
  try {
    const run = await fetchJSON(`${baseUrl}/v1/runs/${runId}`, token, { method: "GET" });
    renderRunDetail(run);
  } catch (err) {
    alert(`Failed to fetch run ${runId}: ${err.message}`);
  }
});

evidenceTable.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-evidence]");
  if (!button) return;
  const runId = button.dataset.evidence;
  const { baseUrl, token } = getInputs();
  try {
    const evidence = await fetchJSON(`${baseUrl}/v1/evidence/${runId}`, token, { method: "GET" });
    renderEvidenceDetail(evidence);
  } catch (err) {
    alert(`Failed to fetch evidence for ${runId}: ${err.message}`);
  }
});

document.getElementById("refreshRuns").addEventListener("click", loadRuns);
document.getElementById("refreshEvidence").addEventListener("click", loadEvidence);

document.getElementById("submitRun").addEventListener("click", async () => {
  const { baseUrl, token } = getInputs();
  const payload = {
    goal: "Reduce holding cost",
    project_id: `ui-${Date.now()}`,
    horizon: 2,
    archetype_id: "inventory_basic",
    data_inputs: {
      demand: [
        { sku: "widget", quantity: 120 },
        { sku: "gadget", quantity: 95 }
      ],
      holding_cost: [
        { sku: "widget", cost: 2.5 },
        { sku: "gadget", cost: 1.75 }
      ]
    }
  };
  try {
    const response = await fetchJSON(`${baseUrl}/v1/runs`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    alert(`Run submitted: ${response.run_id}`);
    await loadRuns();
  } catch (err) {
    alert(`Failed to submit run: ${err.message}`);
  }
});

runToggle.addEventListener("click", () => {
  runDetail.classList.toggle("hidden");
});

evidenceToggle.addEventListener("click", () => {
  evidenceDetail.classList.toggle("hidden");
});

runCopy.addEventListener("click", () => copyToClipboard(runDetail.dataset.json, runCopy));
evidenceCopy.addEventListener("click", () => copyToClipboard(evidenceDetail.dataset.json, evidenceCopy));

document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener("click", () => {
    const fieldId = button.dataset.copy;
    const textarea = document.getElementById(fieldId);
    if (textarea) {
      copyToClipboard(textarea.value, button);
    }
  });
});

document.getElementById("runCompile").addEventListener("click", async () => {
  await invokeEndpoint("compilePayload", "compileResult", "/v1/compile");
});

document.getElementById("runForecast").addEventListener("click", async () => {
  await invokeEndpoint("forecastPayload", "forecastResult", "/v1/forecast");
});

document.getElementById("runOrchestrate").addEventListener("click", async () => {
  await invokeEndpoint("orchestratePayload", "orchestrateResult", "/v1/runs");
  await loadRuns();
});

loadRuns();
loadEvidence();

function renderRunDetail(run) {
  const { run_id, status, goal, archetype_id, result } = run;
  const solution = result?.solution ?? {};
  const explanation = result?.explanation ?? run.explanation ?? null;
  const artifacts = result?.artifacts ?? run.artifacts ?? {};
  const solver = solution.metadata?.solver ?? "-";
  const objective = solution.kpis?.objective_value ?? "-";
  const generatedAt =
    solution.metadata?.generated_at ?? run.updated_at ?? run.created_at ?? null;

  runSummary.innerHTML = `
    <div><strong>Run:</strong> ${run_id}</div>
    <div><strong>Status:</strong> <span class="status-pill status-${normalizeStatus(
      status
    )}">${formatStatus(status)}</span></div>
    <div><strong>Goal:</strong> ${goal ?? "-"}</div>
    <div><strong>Archetype:</strong> ${archetype_id ?? "-"}</div>
    <div><strong>Solver:</strong> ${solver}</div>
    <div><strong>Objective:</strong> ${formatNumber(objective)}</div>
    <div><strong>Updated:</strong> ${formatDate(generatedAt)}</div>
  `;
  renderContext(runContext, explanation);
  renderMetrics(runMetrics, solution.kpis ?? {});
  renderListBlock(runHighlights, "Highlights", explanation?.highlights ?? []);
  renderListBlock(runWhatIfs, "What-ifs", explanation?.what_ifs ?? []);
  renderArtifactList(runArtifacts, artifacts);
  renderJsonViewer(runDetail, run);
  runDetail.classList.remove("hidden");
}

function renderEvidenceDetail(evidence) {
  const artifacts = Object.keys(evidence.artifacts ?? {}).join(", ") || "-";
  evidenceSummary.innerHTML = `
    <div><strong>Run:</strong> ${evidence.run_id}</div>
    <div><strong>Stored:</strong> ${formatDate(evidence.stored_at)}</div>
    <div><strong>Artifacts:</strong> ${artifacts}</div>
  `;
  renderArtifactList(evidenceArtifacts, evidence.artifacts ?? {});
  renderJsonViewer(evidenceDetail, evidence);
  evidenceDetail.classList.remove("hidden");
}

function copyToClipboard(value = "", button) {
  navigator.clipboard.writeText(value).then(() => {
    const original = button.textContent;
    button.textContent = "Copied!";
    setTimeout(() => (button.textContent = original), 1200);
  });
}

async function invokeEndpoint(textareaId, resultId, path) {
  const { baseUrl, token } = getInputs();
  const resultContainer = document.getElementById(resultId);
  const input = document.getElementById(textareaId)?.value || "{}";
  try {
    const response = await fetchJSON(`${baseUrl}${path}`, token, {
      method: "POST",
      body: input,
    });
    resultContainer.textContent = JSON.stringify(response, null, 2);
  } catch (err) {
    resultContainer.textContent = `Error: ${err.message}`;
  }
}

function renderJsonViewer(container, data) {
  container.innerHTML = "";
  const tree = buildJsonTree(data);
  container.appendChild(tree);
  container.dataset.json = JSON.stringify(data, null, 2);
}

function buildJsonTree(data) {
  if (data === null) {
    const span = document.createElement("span");
    span.className = "json-null";
    span.textContent = "null";
    return span;
  }

  if (Array.isArray(data)) {
    const ul = document.createElement("ul");
    data.forEach((value, index) => {
      const li = document.createElement("li");
      li.appendChild(buildJsonTree(value));
      ul.appendChild(li);
    });
    return ul;
  }

  if (typeof data === "object") {
    const ul = document.createElement("ul");
    Object.entries(data).forEach(([key, value]) => {
      const li = document.createElement("li");
      const keySpan = document.createElement("span");
      keySpan.className = "json-key";
      keySpan.textContent = `${key}: `;
      li.appendChild(keySpan);
      li.appendChild(buildJsonTree(value));
      ul.appendChild(li);
    });
    return ul;
  }

  const span = document.createElement("span");
  if (typeof data === "string") {
    span.className = "json-string";
    span.textContent = `"${data}"`;
  } else if (typeof data === "number") {
    span.className = "json-number";
    span.textContent = data;
  } else if (typeof data === "boolean") {
    span.className = "json-boolean";
    span.textContent = data;
  } else {
    span.textContent = data;
  }
  return span;
}

function renderContext(container, explanation) {
  container.innerHTML = "";
  if (!explanation) {
    container.innerHTML = "<p>No explanation available.</p>";
    return;
  }
  const { summary, narrative, context } = explanation;
  const addParagraph = (text) => {
    if (!text) return;
    const p = document.createElement("p");
    p.textContent = text;
    container.appendChild(p);
  };

  if (Array.isArray(summary)) {
    summary.forEach(addParagraph);
  } else {
    addParagraph(summary);
  }

  if (Array.isArray(narrative)) {
    narrative.forEach(addParagraph);
  } else {
    addParagraph(narrative);
  }

  if (Array.isArray(context) && context.length) {
    const list = document.createElement("ul");
    context.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = typeof item === "string" ? item : formatInlineValue(item);
      list.appendChild(li);
    });
    container.appendChild(list);
  } else if (context && typeof context === "object") {
    const entries = Object.entries(context);
    if (entries.length) {
      const list = document.createElement("ul");
      entries.forEach(([key, value]) => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${key}:</strong> ${formatInlineValue(value)}`;
        list.appendChild(li);
      });
      container.appendChild(list);
    }
  }

  if (!container.hasChildNodes()) {
    container.innerHTML = "<p>No explanation available.</p>";
  }
}

function renderMetrics(container, kpis) {
  container.innerHTML = "";
  const entries = Object.entries(kpis);
  if (!entries.length) {
    container.innerHTML = "<p>No KPIs available.</p>";
    return;
  }
  entries.forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `<span class="label">${label.replace(/_/g, " ")}</span><span class="value">${formatNumber(value)}</span>`;
    container.appendChild(card);
  });
}

function renderListBlock(container, title, items) {
  if (!items || !items.length) {
    container.innerHTML = "";
    return;
  }
  const ul = document.createElement("ul");
  items.forEach((entry) => {
    const li = document.createElement("li");
    li.textContent = entry;
    ul.appendChild(li);
  });
  container.innerHTML = `<h4>${title}</h4>`;
  container.appendChild(ul);
}

function renderArtifactList(container, artifacts) {
  container.innerHTML = "";
  const entries = Object.entries(artifacts ?? {});
  if (!entries.length) {
    container.innerHTML = "";
    return;
  }
  const ul = document.createElement("ul");
  entries.forEach(([key, info]) => {
    const li = document.createElement("li");
    const path = info.path || info.uri;
    if (path) {
      const relative = path.startsWith("http") ? path : `../${path}`;
      li.innerHTML = `<strong>${key}:</strong> <a href="${relative}" target="_blank" rel="noopener">${path}</a>`;
    } else {
      li.innerHTML = `<strong>${key}:</strong> (unavailable)`;
    }
    ul.appendChild(li);
  });
  container.innerHTML = "<h4>Artifacts</h4>";
  container.appendChild(ul);
}

function formatInlineValue(value) {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") return formatNumber(value);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map((entry) => formatInlineValue(entry)).join(", ");
  }
  return JSON.stringify(value);
}

function formatNumber(value) {
  if (typeof value === "number") {
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return value;
}

function updateRunOverview(runs = []) {
  if (!runOverview) return;
  runOverview.innerHTML = "";
  if (!runs.length) {
    runOverview.innerHTML =
      "<p>No runs yet. Launch an orchestration to see trends here.</p>";
    return;
  }

  const statusCounts = runs.reduce((acc, run) => {
    const key = normalizeStatus(run.status);
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
  const total = runs.length;
  const completedCount = (statusCounts.succeeded ?? 0) + (statusCounts.completed ?? 0);
  const activeCount = ["running", "in-progress", "pending", "created"].reduce(
    (sum, key) => sum + (statusCounts[key] ?? 0),
    0
  );
  const failedCount = (statusCounts.failed ?? 0) + (statusCounts.error ?? 0);
  const latestRunDate = runs
    .map((run) =>
      toDate(run.result?.solution?.metadata?.generated_at ?? run.updated_at ?? run.created_at)
    )
    .filter(Boolean)
    .sort((a, b) => b.getTime() - a.getTime())[0];

  const overviewGrid = document.createElement("div");
  overviewGrid.className = "overview-grid";
  overviewGrid.innerHTML = `
    <div class="overview-card">
      <span class="label">Total Runs</span>
      <span class="value">${total}</span>
    </div>
    <div class="overview-card">
      <span class="label">Succeeded</span>
      <span class="value">${completedCount}</span>
    </div>
    <div class="overview-card">
      <span class="label">Active</span>
      <span class="value">${activeCount}</span>
    </div>
    <div class="overview-card">
      <span class="label">Failed</span>
      <span class="value">${failedCount}</span>
    </div>
  `;
  runOverview.appendChild(overviewGrid);

  const segments = Object.entries(statusCounts).filter(([, count]) => count > 0);
  if (segments.length > 0) {
    const statusBar = document.createElement("div");
    statusBar.className = "status-bar";
    segments.forEach(([key, count]) => {
      const segment = document.createElement("div");
      segment.className = `status-segment status-${key}`;
      segment.style.flex = count;
      segment.style.background = statusColor(key);
      segment.title = `${formatStatus(key)}: ${count}`;
      statusBar.appendChild(segment);
    });
    runOverview.appendChild(statusBar);

    const legend = document.createElement("div");
    legend.className = "overview-helper";
    segments
      .sort((a, b) => b[1] - a[1])
      .forEach(([key, count]) => {
        const entry = document.createElement("span");
        entry.innerHTML = `<span class="status-dot" style="background:${statusColor(
          key
        )};"></span>${formatStatus(key)} (${count})`;
        legend.appendChild(entry);
      });
    if (latestRunDate) {
      const entry = document.createElement("span");
      entry.innerHTML = `<strong>Latest update:</strong> ${latestRunDate.toLocaleString()}`;
      legend.appendChild(entry);
    }
    runOverview.appendChild(legend);
  }
}

function updateEvidenceOverview(items = []) {
  if (!evidenceOverview) return;
  evidenceOverview.innerHTML = "";
  if (!items.length) {
    evidenceOverview.innerHTML =
      "<p>No evidence captured yet. When runs finish, artifacts will appear here.</p>";
    return;
  }

  const totalArtifacts = items.reduce(
    (sum, item) => sum + Object.keys(item.artifacts ?? {}).length,
    0
  );
  const artifactCounts = items.reduce((acc, item) => {
    Object.keys(item.artifacts ?? {}).forEach((key) => {
      acc[key] = (acc[key] ?? 0) + 1;
    });
    return acc;
  }, {});
  const latestEvidenceDate = items
    .map((item) => toDate(item.stored_at))
    .filter(Boolean)
    .sort((a, b) => b.getTime() - a.getTime())[0];
  const uniqueArtifacts = Object.keys(artifactCounts).length;

  const overviewGrid = document.createElement("div");
  overviewGrid.className = "overview-grid";
  overviewGrid.innerHTML = `
    <div class="overview-card">
      <span class="label">Evidence Items</span>
      <span class="value">${items.length}</span>
    </div>
    <div class="overview-card">
      <span class="label">Total Artifacts</span>
      <span class="value">${totalArtifacts}</span>
    </div>
    <div class="overview-card">
      <span class="label">Artifact Types</span>
      <span class="value">${uniqueArtifacts}</span>
    </div>
    <div class="overview-card">
      <span class="label">Last Stored</span>
      <span class="value">${latestEvidenceDate ? latestEvidenceDate.toLocaleString() : "-"}</span>
    </div>
  `;
  evidenceOverview.appendChild(overviewGrid);

  if (uniqueArtifacts) {
    const helper = document.createElement("div");
    helper.className = "overview-helper";
    Object.entries(artifactCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .forEach(([key, count]) => {
        const entry = document.createElement("span");
        entry.innerHTML = `<strong>${key}</strong>: ${count}`;
        helper.appendChild(entry);
      });
    evidenceOverview.appendChild(helper);
  }
}

function normalizeStatus(status) {
  const value = (status ?? "unknown").toString().toLowerCase();
  const cleaned = value.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return cleaned || "unknown";
}

function formatStatus(status) {
  if (!status) return "Unknown";
  const value = status.toString().replace(/[_-]+/g, " ");
  return value
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDate(value) {
  const date = toDate(value);
  if (!date) {
    if (!value) return "-";
    return value;
  }
  return date.toLocaleString();
}

function toDate(value) {
  if (!value) return null;
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

function statusColor(statusKey) {
  return STATUS_COLORS[statusKey] || STATUS_COLORS.default;
}
