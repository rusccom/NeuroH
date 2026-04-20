import { createCharts } from "./charts.js";
import { renderMap } from "./map.js";
import { renderBlob } from "./blob3d.js";

const mode = document.body.dataset.mode;
const mapCanvas = document.getElementById("map-canvas");
const kpiGrid = document.getElementById("kpi-grid");
const eventList = document.getElementById("event-list");
const runState = document.getElementById("run-state");
const connectionState = document.getElementById("connection-state");
const episodeState = document.getElementById("episode-state");
const targetState = document.getElementById("target-state");
const lifePanel = document.getElementById("life-panel");
const slider = document.getElementById("replay-slider");
const charts = createCharts(document.getElementById("chart-root"));
const history = [];

boot();

async function boot() {
  if (mode === "replay") {
    await loadReplay();
    return;
  }
  bindControls();
  const bootstrap = await fetchJson("/api/monitor/bootstrap");
  renderBootstrap(bootstrap);
  connectStream();
}

function bindControls() {
  document.querySelectorAll("[data-command]").forEach((button) => {
    button.addEventListener("click", async () => {
      const command = button.dataset.command;
      await fetch("/api/monitor/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
      });
    });
  });
}

function renderBootstrap(data) {
  if (data.latest_frame) renderSnapshot(data.latest_frame);
  (data.recent_alerts || []).forEach(renderEvent);
  runState.textContent = data.run_state;
}

function connectStream() {
  const source = new EventSource("/api/monitor/stream");
  connectionState.textContent = "live";
  source.addEventListener("frame", (event) => renderSnapshot(JSON.parse(event.data)));
  source.addEventListener("alert", (event) => renderEvent(JSON.parse(event.data)));
  source.addEventListener("summary", (event) => renderEvent(JSON.parse(event.data)));
  source.onerror = () => {
    connectionState.textContent = "stale";
  };
}

function renderSnapshot(snapshot) {
  history.push(toSignals(baseSnapshot(snapshot)));
  if (history.length > 120) history.shift();
  charts.update(history);
  renderMap(mapCanvas, baseSnapshot(snapshot));
  renderBlob(document.getElementById("blob-root"), baseSnapshot(snapshot));
  runState.textContent = snapshot.run_state;
  episodeState.textContent = snapshot.life_id === undefined
    ? `episode ${snapshot.episode_id} / step ${snapshot.world.step_idx}`
    : `life ${snapshot.life_id} / tick ${snapshot.current_tick}`;
  targetState.textContent = `Target: ${snapshot.world.target ? snapshot.world.target.join(", ") : "-"}`;
  renderKpis(snapshot);
  renderLifePanel(snapshot);
}

function renderKpis(snapshot) {
  const cards = [
    card("Energy", snapshot.body.energy),
    card("Water", snapshot.body.water),
    card("Need", snapshot.need.active_need ?? "none"),
    card("Behavior", snapshot.behavior_mode),
    card("Source", snapshot.memory.decision_source),
    card("Confidence", snapshot.memory.selected_confidence.toFixed(2)),
    card("Reward", snapshot.world.total_reward.toFixed(2)),
    card("Biome", snapshot.world.biome_id ?? "-"),
  ];
  kpiGrid.innerHTML = cards.join("");
}

function renderEvent(event) {
  const item = document.createElement("div");
  item.className = `event-item ${event.level || ""}`;
  item.innerHTML = `<strong>${event.code || "summary"}</strong><p>${event.message || JSON.stringify(event)}</p>`;
  eventList.prepend(item);
}

function renderLifePanel(snapshot) {
  if (snapshot.life_id === undefined) {
    lifePanel.textContent = "episodic snapshot";
    return;
  }
  lifePanel.textContent = [
    `life_id: ${snapshot.life_id}`,
    `tick: ${snapshot.current_tick}/${snapshot.life_max_ticks}`,
    `energy_ratio_100: ${formatMetric(snapshot.current_energy_ratio_100)}`,
    `water_ratio_100: ${formatMetric(snapshot.current_water_ratio_100)}`,
    `deficit_variance_100: ${formatMetric(snapshot.current_deficit_variance)}`,
    `energy_ratio_1000: ${formatMetric(snapshot.long_window_energy_ratio)}`,
    `water_ratio_1000: ${formatMetric(snapshot.long_window_water_ratio)}`,
    `food_count: ${snapshot.current_food_count}`,
    `water_count: ${snapshot.current_water_count}`,
    `next_relocation_tick: ${snapshot.next_relocation_tick ?? "-"}`,
    `completed_lives: ${formatCompletedLives(snapshot.completed_lives || [])}`,
  ].join("\n");
}

async function loadReplay() {
  const [,, runId, episodeId] = window.location.pathname.split("/").slice(-4);
  const payload = await fetchJson(`/api/monitor/history/${runId}/${episodeId}`);
  const frames = payload.records.filter((item) => item.type === "frame").map((item) => item.payload);
  payload.records.filter((item) => item.type !== "frame").forEach((item) => renderEvent(item.payload));
  slider.max = Math.max(frames.length - 1, 0);
  slider.addEventListener("input", () => renderSnapshot(frames[Number(slider.value)]));
  if (frames.length) renderSnapshot(frames[0]);
}

function card(label, value) {
  return `<article class="metric-card"><span>${label}</span><strong>${value}</strong></article>`;
}

function baseSnapshot(snapshot) {
  return snapshot.base_snapshot ?? snapshot;
}

function toSignals(snapshot) {
  return {
    energy_deficit: snapshot.need.energy_deficit,
    water_deficit: snapshot.need.water_deficit,
    uncertainty: snapshot.blob.uncertainty,
    selected_confidence: snapshot.memory.selected_confidence,
  };
}

function formatMetric(value) {
  return value === null || value === undefined ? "-" : Number(value).toFixed(3);
}

function formatCompletedLives(completedLives) {
  if (!completedLives.length) return "-";
  return completedLives.map((item) => `${item.life_id}:${item.end_reason}@${item.duration_ticks}`).join(", ");
}

async function fetchJson(url) {
  const response = await fetch(url);
  return response.json();
}
