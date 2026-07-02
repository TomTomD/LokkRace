// LokkRace web app — full event flow (registration → start & goal → matching →
// results). Static / client-side; state persists to localStorage.
//
//   - roster      = every known kayaker with season race_history. The shareable
//                   "data bundle" (import/export). Persisted under STORE_KEY.
//   - race        = the current competition. A transient snapshot is persisted
//                   under RACE_KEY so a browser refresh mid-event loses nothing.
//   - finishOrder = the secretary's ordered list of bib numbers at the line.

import { Participant, Race, getTimeString, parseTimeString, formatRaceStamp } from "./racebase.js";

const STORE_KEY = "lokkrace.bundle.v1";
const RACE_KEY = "lokkrace.race.v1";
const BUNDLE_VERSION = 1;

let roster = [];          // Participant[]
let selectedName = null;
let race = new Race();
let finishOrder = [];     // bib-number strings, in crossing order
let matchState = [];      // matching screen: selected name per crossing (or null)
let currentScreen = "registration";

const $ = (id) => document.getElementById(id);

// ============================ persistence ============================

function loadRoster() {
  try {
    const bundle = JSON.parse(localStorage.getItem(STORE_KEY));
    return (bundle?.participants || []).map(Participant.fromJSON);
  } catch { return []; }
}

function saveRoster() {
  const bundle = { version: BUNDLE_VERSION, participants: roster.map((p) => p.toJSON()) };
  localStorage.setItem(STORE_KEY, JSON.stringify(bundle));
  renderRosterCount();
}

function saveRaceState() {
  const state = { snap: race.snapshot(), finishOrder, screen: currentScreen };
  localStorage.setItem(RACE_KEY, JSON.stringify(state));
}

function loadRaceState() {
  try {
    const state = JSON.parse(localStorage.getItem(RACE_KEY));
    if (!state) return;
    race = Race.fromSnapshot(state.snap, roster);
    finishOrder = state.finishOrder || [];
    currentScreen = state.screen || "registration";
  } catch { /* ignore corrupt state */ }
}

function exportBundle() {
  const bundle = { version: BUNDLE_VERSION, participants: roster.map((p) => p.toJSON()) };
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `lokkrace-data-${formatRaceStamp(new Date())}.json`;
  a.click();
  URL.revokeObjectURL(url);
  toast("Data sparad till fil");
}

function importBundle(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const bundle = JSON.parse(reader.result);
      if (!Array.isArray(bundle?.participants)) throw new Error("fel format");
      // Clear all current in-memory data before loading the new bundle.
      roster = bundle.participants.map(Participant.fromJSON);
      roster.sort((a, b) => a.name.localeCompare(b.name, "sv"));
      race = new Race();
      finishOrder = [];
      selectedName = null;
      localStorage.removeItem(RACE_KEY);
      saveRoster();
      showScreen("registration");
      renderAll();
      toast(`Öppnade ${roster.length} kanotister`);
    } catch (e) { toast("Kunde inte läsa filen: " + e.message); }
  };
  reader.readAsText(file);
}

// ============================ screen routing ============================

const SCREENS = ["registration", "start", "match", "results", "stats", "help"];

function showScreen(name) {
  currentScreen = name;
  for (const s of SCREENS) $(`screen-${s}`).hidden = s !== name;
  for (const btn of document.querySelectorAll(".phase")) {
    btn.classList.toggle("active", btn.dataset.screen === name);
  }
  if (name === "match") renderMatch();
  if (name === "results") renderResults();
  if (name === "start") { renderRunStartList(); renderGoalLists(); updateFinishMode(); }
  if (name === "stats") renderStats();
  saveRaceState();
}

// ============================ registration ============================

function rosterEntry(name) { return roster.find((p) => p.name === name) || null; }

function createKayaker(name, bestSeconds) {
  name = name.trim();
  if (!name) return toast("Ange ett namn");
  if (rosterEntry(name)) return toast("Kanotisten finns redan");
  roster.push(new Participant(name, bestSeconds));
  roster.sort((a, b) => a.name.localeCompare(b.name, "sv"));
  saveRoster();
  selectedName = name;
  $("roster-filter").value = name; // filter to the new kayaker so it's visibly selected
  renderRoster();
  const n = $("add-number"); // ready for the bib number
  n.focus();
  n.select();
  toast(`La till ${name}`);
}

function numberTaken(number) {
  return race.participants.some((p) => String(p.number) === String(number));
}

function addToRace(name, number) {
  // Best time comes from the roster data — never overridden here.
  race.addParticipant(name, number, null, roster);
  saveRaceState();
  renderParticipants();
}

function removeFromRace(name) {
  race.removeParticipant(name);
  saveRaceState();
  renderParticipants();
}

function renderRosterCount() {
  $("roster-count").textContent = `${roster.length} kanotister i data`;
}

function renderRoster() {
  const filter = $("roster-filter").value.trim().toUpperCase();
  const inRace = new Set(race.participants.map((p) => p.name));
  const list = $("roster-list");
  list.innerHTML = "";
  for (const p of roster) {
    if (inRace.has(p.name)) continue;
    if (filter && !p.name.toUpperCase().includes(filter)) continue;
    const li = document.createElement("li");
    if (p.name === selectedName) li.classList.add("selected");
    li.append(el("span", p.name), el("span", getTimeString(p.best_time_seconds), "meta"));
    li.addEventListener("click", () => {
      selectedName = p.name;
      renderRoster();
      const n = $("add-number"); // ready to type the bib number immediately
      n.focus();
      n.select();
    });
    list.appendChild(li);
  }
}

function renderParticipants() {
  const table = $("participants-list");
  table.innerHTML = "";
  if (race.participants.length) {
    const head = document.createElement("tr");
    head.append(el("th", "Nr"), el("th", "Namn"), el("th", "Start"), el("th", "Bästa"), el("th", ""));
    table.appendChild(head);
  }
  // Rows are in start order (slowest starts first).
  for (const p of race.participants) {
    const tr = document.createElement("tr");
    const remove = el("button", "✕", "remove");
    remove.title = "Ta bort";
    remove.addEventListener("click", () => removeFromRace(p.name));
    const rmTd = document.createElement("td");
    rmTd.appendChild(remove);
    tr.append(
      el("td", String(p.number), "num"),
      el("td", p.name, "nm"),
      el("td", getTimeString(race.getParticipantStartTime(p)), "start"),
      el("td", getTimeString(p.best_time_seconds), "best"),
      rmTd,
    );
    table.appendChild(tr);
  }
  $("participants-title").textContent = `Deltagare (${race.participants.length})`;
  renderRoster();
}

// ============================ start & goal (2–4) ============================

// START is hidden once running; MÅL is only enabled while running.
function updateStartControls() {
  const running = race.start_time != null;
  $("start-btn").hidden = running;
  $("goal-btn").disabled = !running;
}

function startRace() {
  if (!race.participants.length) return toast("Inga deltagare");
  race.start();
  updateStartControls();
  saveRaceState();
  renderClock();
  renderRunStartList();
  updateFinishMode();
}

function resetRace() {
  if (!confirm("Nollställa loppet? Tiden och alla måltider raderas. Deltagarna behålls.")) return;
  race.resetTiming();
  finishOrder = [];
  updateStartControls();
  saveRaceState();
  renderClock();
  renderRunStartList();
  renderGoalLists();
  updateFinishMode();
  toast("Loppet nollställt");
}

function pressGoal() {
  if (!race.start_time) return;
  race.timestampGoal();
  saveRaceState();
  renderGoalLists();
}

function addOrderNumber(num) {
  num = String(num).trim();
  if (!num) return;
  finishOrder.push(num);
  $("order-number").value = "";
  saveRaceState();
  renderOrderList();
}

function participantByNumber(num) {
  return race.participants.find((p) => String(p.number) === String(num)) || null;
}

function renderClock() { $("race-clock").textContent = getTimeString(race.getRaceDuration()); }

// The latest start moment in the field (seconds from race start).
function lastStartTime() {
  return race.participants.reduce(
    (max, p) => Math.max(max, race.getParticipantStartTime(p)), 0);
}

// Big, readable start list. Rows are in start order (slowest starts first).
// Started racers are greyed; racers starting within 30 s are highlighted.
function renderRunStartList() {
  const table = $("run-start-list");
  table.innerHTML = "";
  const dur = race.getRaceDuration();
  const running = race.start_time != null;

  for (const p of race.participants) {
    const countdown = race.getParticipantStartTime(p) - dur;
    const tr = document.createElement("tr");
    let cd;
    if (running && countdown <= 0) {
      tr.className = "started";
      cd = "✔";
    } else if (running && countdown <= 5) {
      tr.className = "start-now";
      cd = getTimeString(countdown);
    } else if (countdown <= 30) {
      tr.className = "upcoming";
      cd = getTimeString(countdown);
    } else {
      cd = getTimeString(countdown);
    }
    tr.append(
      el("td", cd, "cd"),
      el("td", String(p.number), "num"),
      el("td", p.name, "nm"),
    );
    table.appendChild(tr);
  }
}

// 20 s after the last racer has started, shift emphasis to goal stamping.
// MÅL is always available once started, so finishing early still works.
function updateFinishMode() {
  const dur = race.getRaceDuration();
  const finishing = race.start_time != null && dur >= lastStartTime() + 20;
  $("finish-area").hidden = !finishing; // måltider + ordning only matter at the finish
  $("screen-start").classList.toggle("finishing", finishing);
}

function renderGoalLists() {
  const times = $("goal-times");
  times.innerHTML = "";
  race.goal_time_list_seconds.forEach((t) => times.appendChild(el("li", getTimeString(t))));
  $("goal-count").textContent =
    `${race.goal_time_list_seconds.length}/${race.participants.length} mål`;
  renderOrderList();
}

function renderOrderList() {
  const list = $("order-list");
  list.innerHTML = "";
  finishOrder.forEach((num, i) => {
    const p = participantByNumber(num);
    const li = el("li", `${num} — ${p ? p.name : "okänt nr"}`);
    if (!p) li.style.color = "#b00020";
    const remove = el("button", "✕", "remove");
    remove.addEventListener("click", () => {
      finishOrder.splice(i, 1);
      saveRaceState();
      renderOrderList();
    });
    li.appendChild(remove);
    list.appendChild(li);
  });
  renderOrderButtons();
}

// One button per not-yet-recorded number, so the secretary just taps them in
// crossing order instead of typing.
function renderOrderButtons() {
  const box = $("order-buttons");
  box.innerHTML = "";
  const used = new Set(finishOrder.map(String));
  const available = race.participants
    .filter((p) => !used.has(String(p.number)))
    .sort((a, b) => String(a.number).localeCompare(String(b.number), undefined, { numeric: true }));
  for (const p of available) {
    const b = el("button", `${p.number} ${p.name}`, "btn num-btn");
    b.addEventListener("click", () => addOrderNumber(p.number));
    box.appendChild(b);
  }
}

// ============================ matching (5) ============================

function renderMatch() {
  // Seed selections from the secretary's order, then render.
  matchState = race.goal_time_list_seconds.map((_, i) => {
    const p = finishOrder[i] ? participantByNumber(finishOrder[i]) : null;
    return p ? p.name : null;
  });
  renderMatchTable();
}

function renderMatchTable() {
  const table = $("match-table");
  table.innerHTML = "";
  const head = document.createElement("tr");
  head.append(el("th", "#"), el("th", "Måltid"), el("th", "Kanotist"));
  table.appendChild(head);

  const chosen = new Set(matchState.filter(Boolean));
  race.goal_time_list_seconds.forEach((t, i) => {
    const tr = document.createElement("tr");
    const select = document.createElement("select");
    select.appendChild(new Option("(ingen)", ""));
    for (const p of race.participants) {
      // Only list competitors not already chosen elsewhere, plus this row's own.
      if (!chosen.has(p.name) || matchState[i] === p.name) {
        select.appendChild(new Option(`${p.number} · ${p.name}`, p.name));
      }
    }
    select.value = matchState[i] || "";
    select.addEventListener("change", () => {
      matchState[i] = select.value || null;
      renderMatchTable(); // refresh which names remain available
      validateMatch();
    });
    const td = document.createElement("td");
    td.appendChild(select);
    tr.append(el("td", String(i + 1)), el("td", getTimeString(t)), td);
    table.appendChild(tr);
  });
  validateMatch();
}

function matchSelections() {
  return matchState.slice();
}

function validateMatch() {
  const names = matchSelections().filter(Boolean);
  const dupes = names.filter((n, i) => names.indexOf(n) !== i);
  const warn = $("match-warning");
  if (dupes.length) {
    warn.hidden = false;
    warn.textContent = "Samma kanotist är vald flera gånger: " + [...new Set(dupes)].join(", ");
  } else {
    warn.hidden = true;
  }
}

// Insert a manually entered finish time, keeping times chronological and the
// matchState aligned to them.
function addManualMatchTime(seconds) {
  const pairs = race.goal_time_list_seconds.map((t, i) => ({ t, name: matchState[i] || null }));
  pairs.push({ t: seconds, name: null });
  pairs.sort((a, b) => a.t - b.t);
  race.goal_time_list_seconds = pairs.map((p) => p.t);
  matchState = pairs.map((p) => p.name);
  saveRaceState();
  renderMatchTable();
}

function calcResults() {
  race.assignResults(matchSelections());
  saveRaceState();
  showScreen("results");
}

// ============================ results (6) ============================

function renderResults() {
  const table = $("results-table");
  table.innerHTML = "";
  const head = document.createElement("tr");
  ["#", "Nr", "Namn", "Bästa", "Tid", "Förbättring"].forEach((h) => head.appendChild(el("th", h)));
  table.appendChild(head);

  const finishers = race.participants.filter((p) => p.race_finish_time_seconds > 0);
  finishers.forEach((p, i) => {
    const tr = document.createElement("tr");
    if (i === 0) tr.className = "winner";
    tr.append(
      el("td", String(i + 1)),
      el("td", String(p.number)),
      el("td", p.name),
      el("td", getTimeString(p.best_time_seconds)),
      el("td", getTimeString(p.race_time_seconds)),
      el("td", getTimeString(p.race_improvement_seconds)),
    );
    table.appendChild(tr);
  });
  if (!finishers.length) {
    const tr = document.createElement("tr");
    const td = el("td", "Inga resultat ännu — gör matchningen först.");
    td.colSpan = 6;
    tr.appendChild(td);
    table.appendChild(tr);
  }
}

function finalizeRace() {
  const finishers = race.participants.filter((p) => p.race_finish_time_seconds > 0);
  if (!finishers.length) return toast("Inga resultat att spara");
  race.finalize();      // folds best times + appends race_history onto roster objects
  saveRoster();         // persist the updated bundle
  exportBundle();       // hand the organizer the updated data file
  // Start a fresh race, keep the roster.
  race = new Race();
  finishOrder = [];
  localStorage.removeItem(RACE_KEY);
  toast("Loppet sparat i data");
  showScreen("registration");
  renderAll();
}

// ============================ statistics (separate tab) ============================

function fmtImprovement(seconds) {
  const sign = seconds >= 0 ? "+" : "−";
  return sign + getTimeString(Math.abs(seconds));
}

// "YYYYMMDD-HHMMSS" → "YYYY-MM-DD" / "D/M"
function fmtRaceDate(stamp) {
  const s = String(stamp);
  return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
}
function fmtRaceShort(stamp) {
  const s = String(stamp);
  return `${+s.slice(6, 8)}/${+s.slice(4, 6)}`;
}

function makeKpi(num, label) {
  const tile = el("div", null, "kpi");
  tile.append(el("div", String(num), "num"), el("div", label, "label"));
  return tile;
}

// Single-series bar chart. items: [{label, value, title?}]
function barChart(container, items, emptyText) {
  container.innerHTML = "";
  if (!items.length) { container.textContent = emptyText || "Ingen data ännu."; return; }
  const max = Math.max(1, ...items.map((i) => i.value));
  for (const it of items) {
    const col = el("div", null, "bar-col");
    const track = el("div", null, "bar-track");
    const bar = el("div", null, "bar");
    bar.style.height = `${(it.value / max) * 100}%`;
    bar.title = it.title || `${it.label}: ${it.value}`;
    track.appendChild(bar);
    col.append(el("div", String(it.value), "bar-value"), track, el("div", it.label, "bar-label"));
    container.appendChild(col);
  }
}

// Inline SVG line chart of times over races. Faster times sit higher.
function lineChart(points) {
  if (!points.length) return null;
  const NS = "http://www.w3.org/2000/svg";
  const W = 640, H = 200, padX = 44, padY = 18;
  const values = points.map((p) => p.value);
  const min = Math.min(...values), max = Math.max(...values);
  const span = max - min || 1;
  const n = points.length;
  const xAt = (i) => (n === 1 ? W / 2 : padX + (W - 2 * padX) * (i / (n - 1)));
  const yAt = (v) => padY + (H - 2 * padY) * ((v - min) / span); // min (fastest) at top

  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("class", "line-chart");

  const line = document.createElementNS(NS, "polyline");
  line.setAttribute("points", points.map((p, i) => `${xAt(i)},${yAt(p.value)}`).join(" "));
  line.setAttribute("class", "lc-line");
  svg.appendChild(line);

  points.forEach((p, i) => {
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("cx", xAt(i));
    c.setAttribute("cy", yAt(p.value));
    c.setAttribute("r", "4");
    c.setAttribute("class", "lc-dot");
    const t = document.createElementNS(NS, "title");
    t.textContent = `${p.label}: ${getTimeString(p.value)}`;
    c.appendChild(t);
    svg.appendChild(c);
  });

  // fastest / slowest reference labels
  const label = (v, y) => {
    const txt = document.createElementNS(NS, "text");
    txt.setAttribute("x", padX - 8);
    txt.setAttribute("y", y + 4);
    txt.setAttribute("text-anchor", "end");
    txt.setAttribute("class", "lc-axis");
    txt.textContent = getTimeString(v);
    svg.appendChild(txt);
  };
  label(min, padY);
  label(max, H - padY);
  return svg;
}

function statTable(table, headers, rows, emptyText) {
  table.innerHTML = "";
  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = el("td", emptyText || "Ingen data");
    td.colSpan = headers.length;
    td.style.color = "var(--muted)";
    tr.appendChild(td);
    table.appendChild(tr);
    return;
  }
  const head = document.createElement("tr");
  headers.forEach((h) => head.appendChild(el("th", h)));
  table.appendChild(head);
  for (const cells of rows) {
    const tr = document.createElement("tr");
    cells.forEach((c) => tr.appendChild(el("td", c)));
    table.appendChild(tr);
  }
}

// All stats are computed from the roster's race_history (the season record).
function renderStats() {
  const year = new Date().getFullYear();
  const yearStr = String(year);

  const raceStamps = new Set();
  const startsByYear = {};
  let totalStarts = 0;
  for (const p of roster) {
    for (const h of p.race_history) {
      raceStamps.add(h.race);
      totalStarts += 1;
      const y = String(h.race).slice(0, 4);
      startsByYear[y] = (startsByYear[y] || 0) + 1;
    }
  }
  const seasonRaces = [...raceStamps].filter((s) => String(s).startsWith(yearStr)).length;
  const seasonStarts = startsByYear[yearStr] || 0;

  // --- KPI tiles ---
  const kpis = $("stats-kpis");
  kpis.innerHTML = "";
  [
    [roster.length, "Kanotister"],
    [raceStamps.size, "Race totalt"],
    [totalStarts, "Starter totalt"],
    [seasonRaces, `Race ${year}`],
    [seasonStarts, `Starter ${year}`],
  ].forEach(([num, label]) => kpis.appendChild(makeKpi(num, label)));

  // --- starts per season ---
  const years = Object.keys(startsByYear).sort();
  barChart($("stats-year-chart"), years.map((y) => ({ label: y, value: startsByYear[y] })));

  // --- competitors per race this year ---
  const perRace = {};
  for (const p of roster) {
    for (const h of p.race_history) {
      if (String(h.race).startsWith(yearStr)) perRace[h.race] = (perRace[h.race] || 0) + 1;
    }
  }
  $("stats-perrace-title").textContent = `Deltagare per race ${year}`;
  const raceKeys = Object.keys(perRace).sort();
  barChart($("stats-perrace-chart"),
    raceKeys.map((s) => ({ label: fmtRaceShort(s), value: perRace[s], title: `${fmtRaceDate(s)}: ${perRace[s]} deltagare` })),
    `Inga race ${year} ännu.`);

  // --- individual athlete selector ---
  const sel = $("stats-athlete");
  const prev = sel.value;
  sel.innerHTML = "";
  sel.appendChild(new Option("(välj kanotist)", ""));
  for (const p of [...roster].sort((a, b) => a.name.localeCompare(b.name, "sv"))) {
    sel.appendChild(new Option(p.name, p.name));
  }
  sel.value = prev;
  renderIndividual(sel.value);

  // --- season leaderboards ---
  const seasonResults = roster.map((p) => p.getReport(year).seasonResult).filter(Boolean);
  $("stats-starts-title").textContent = `Flest starter ${year}`;
  $("stats-impr-title").textContent = `Störst förbättring ${year}`;

  const byStarts = [...seasonResults].sort((a, b) => b.count - a.count).slice(0, 10);
  statTable($("stats-most-starts"), ["Namn", "Starter"],
    byStarts.map((r) => [r.name, String(r.count)]), "Inga starter i år");

  const byImpr = [...seasonResults].sort((a, b) => b.improvement - a.improvement).slice(0, 10);
  statTable($("stats-improvement"), ["Namn", "Förbättring"],
    byImpr.map((r) => [r.name, fmtImprovement(r.improvement)]), "Inga resultat i år");

  // --- fastest ever (best times among racers with history) ---
  const fastest = roster
    .filter((p) => p.race_history.length)
    .sort((a, b) => a.best_time_seconds - b.best_time_seconds)
    .slice(0, 10);
  statTable($("stats-fastest"), ["#", "Namn", "Bästa tid"],
    fastest.map((p, i) => [String(i + 1), p.name, getTimeString(p.best_time_seconds)]));
}

function renderIndividual(name) {
  const box = $("stats-individual");
  box.innerHTML = "";
  const p = name ? rosterEntry(name) : null;
  if (!p) { box.textContent = "Välj en kanotist ovan."; return; }

  const year = new Date().getFullYear();
  const { seasonResult } = p.getReport(year);

  const kpiRow = el("div", null, "kpi-row");
  kpiRow.append(
    makeKpi(getTimeString(p.best_time_seconds), "Bästa tid"),
    makeKpi(p.race_history.length, "Antal race"),
    makeKpi(seasonResult ? seasonResult.count : 0, `Race ${year}`),
    makeKpi(seasonResult ? fmtImprovement(seasonResult.improvement) : "—", `Förbättring ${year}`),
  );
  box.appendChild(kpiRow);

  const chrono = [...p.race_history].sort((a, b) => String(a.race).localeCompare(String(b.race)));
  const svg = lineChart(chrono.map((h) => ({ label: fmtRaceDate(h.race), value: h.time_seconds })));
  if (svg) {
    const wrap = el("div", null, "line-wrap");
    wrap.appendChild(svg);
    box.appendChild(wrap);
  }

  const table = el("table", null, "stat-table");
  const recent = [...p.race_history].sort((a, b) => String(b.race).localeCompare(String(a.race)));
  statTable(table, ["Datum", "Tid"],
    recent.map((h) => [fmtRaceDate(h.race), getTimeString(h.time_seconds)]), "Inga race");
  box.appendChild(table);
}

// ============================ helpers ============================

function el(tag, text, className) {
  const e = document.createElement(tag);
  if (text != null) e.textContent = text;
  if (className) e.className = className;
  return e;
}

let toastTimer = null;
function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 2500);
}

function readTime(inputId) {
  const secs = parseTimeString($(inputId).value);
  if (secs == null) { toast("Tid måste vara MM:SS"); return null; }
  return secs;
}

function renderAll() {
  renderRosterCount();
  renderParticipants();   // also renders roster
  updateStartControls();
}

// ============================ wire up ============================

$("add-existing-btn").addEventListener("click", () => {
  if (!selectedName) return toast("Välj en kanotist i listan");
  const number = $("add-number").value.trim() || "00";
  if (numberTaken(number)) return toast(`Nummer ${number} är redan taget`);
  addToRace(selectedName, number);
  $("add-number").value = "00";
  $("roster-filter").value = ""; // clear filter after adding
  selectedName = null;
  renderRoster();
});

// Select the contents of number fields on focus for quick overtyping.
for (const id of ["add-number", "order-number"]) {
  $(id).addEventListener("focus", (e) => e.target.select());
}

$("add-new-btn").addEventListener("click", () => {
  const best = readTime("new-best");
  if (best == null) return;
  createKayaker($("new-name").value, best);
  $("new-name").value = "";
  $("new-best").value = "50:00";
});

$("roster-filter").addEventListener("input", renderRoster);
$("export-btn").addEventListener("click", exportBundle);
$("import-file").addEventListener("change", (e) => {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  // Guard against wiping an unsaved race in progress.
  if ((race.participants.length || race.start_time) &&
      !confirm("Det finns ett pågående lopp. Öppna ny data och rensa det?")) {
    return;
  }
  importBundle(file);
});

$("start-btn").addEventListener("click", startRace);
$("goal-btn").addEventListener("click", pressGoal);
$("reset-btn").addEventListener("click", resetRace);
$("order-add-btn").addEventListener("click", () => addOrderNumber($("order-number").value));
$("order-number").addEventListener("keydown", (e) => {
  if (e.key === "Enter") addOrderNumber($("order-number").value);
});
$("to-match-btn").addEventListener("click", () => showScreen("match"));
$("match-add-time-btn").addEventListener("click", () => {
  const secs = readTime("match-manual-time");
  if (secs != null) addManualMatchTime(secs);
});
$("calc-btn").addEventListener("click", calcResults);
$("finalize-btn").addEventListener("click", finalizeRace);

for (const btn of document.querySelectorAll(".phase")) {
  btn.addEventListener("click", () => showScreen(btn.dataset.screen));
}

$("stats-athlete").addEventListener("change", (e) => renderIndividual(e.target.value));

// Press M for MÅL while on the start screen (mirrors the desktop app).
document.addEventListener("keydown", (e) => {
  if ((e.key === "m" || e.key === "M") && currentScreen === "start" &&
      !(e.target instanceof HTMLInputElement)) {
    pressGoal();
  }
});

// Live clock + countdown while the race runs.
setInterval(() => {
  if (currentScreen === "start" && race.start_time) {
    renderClock();
    renderRunStartList();
    updateFinishMode();
  }
}, 1000);

// ---- boot ----
roster = loadRoster();
loadRaceState();
renderAll();
showScreen(currentScreen);
