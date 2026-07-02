// Domain logic for LokkRace, ported from racebase.py.
// Pure logic + in-memory model — no file I/O, no DOM. Persistence is handled
// by the caller via toBundle()/fromBundle() (see app.js). This module is the
// single source of truth for race calculations and is what the tests exercise.

// RACE_INITIAL_TIME: initial best time for new racers AND the maximum
// start-in-advance time, so we don't spread the starting field out too much.
export const RACE_INITIAL_TIME = 14 * 60;
export const DEFAULT_BEST_TIME = 50 * 60;

// Left-justify to width `n` with spaces (mirrors Python str.ljust).
function ljust(str, n) {
  str = String(str);
  return str.length >= n ? str : str + " ".repeat(n - str.length);
}

// Format seconds as MM:SS. Negative (e.g. a racer who hasn't started yet)
// renders as "**:**". Mirrors racebase.get_time_string.
export function getTimeString(timeInSeconds) {
  const rounded = Math.round(timeInSeconds);
  if (timeInSeconds >= 0) {
    const mins = String(Math.trunc(rounded / 60)).padStart(2, "0");
    const secs = String(rounded % 60).padStart(2, "0");
    return `${mins}:${secs}`;
  }
  return "**:**";
}

// Parse an "MM:SS" string into seconds. Returns null on bad input.
export function parseTimeString(text) {
  const m = /^\s*(\d+):(\d{1,2})\s*$/.exec(String(text));
  if (!m) return null;
  return parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
}

export class Participant {
  constructor(name, bestTimeSeconds = null) {
    this.name = name;
    this.best_time_seconds = bestTimeSeconds != null ? bestTimeSeconds : DEFAULT_BEST_TIME;
    this.number = 0;
    this.race_time_seconds = 0;
    this.race_finish_time_seconds = 0;
    this.race_improvement_seconds = 0;
    this.race_history = [];
  }

  storeRace(raceString) {
    this.race_history.push({ race: raceString, time_seconds: this.race_time_seconds });
  }

  // Season report: total string + a summary object (or null if no season data),
  // mirroring Participant.get_report. `year` is injectable for testing.
  getReport(year = new Date().getFullYear()) {
    let out = this.name + "\n";
    out += "Bästa tid:" + getTimeString(this.best_time_seconds) + "\n";
    let lastSeasonBest = null;
    let seasonFirst = null;
    let seasonBest = 10000;
    let seasonCount = 0;
    let seasonResult = null;
    const currentYear = String(year);
    const lastYear = String(year - 1);

    for (const h of this.race_history) {
      out += h.race + " - " + getTimeString(h.time_seconds) + "\n";
      const time = h.time_seconds;
      if (h.race.startsWith(currentYear)) {
        seasonCount += 1;
        if (seasonFirst === null) seasonFirst = time;
        if (seasonBest > time) seasonBest = time;
      }
      if (h.race.startsWith(lastYear)) {
        if (lastSeasonBest === null) lastSeasonBest = time;
        else if (lastSeasonBest > time) lastSeasonBest = time;
      }
    }

    if (seasonFirst !== null) {
      let compareTime;
      out += "Säsong " + currentYear + " resultat\n";
      if (lastSeasonBest === null) {
        out += "Säsongens första:      " + getTimeString(seasonFirst) + "\n";
        compareTime = seasonFirst;
      } else {
        out += "Förra säsongens bästa:      " + getTimeString(lastSeasonBest) + "\n";
        compareTime = lastSeasonBest;
      }
      out += "Säsongens bästa:       " + getTimeString(seasonBest) + "\n";
      out += "Säsongens förbättring: " + getTimeString(compareTime - seasonBest) + "\n";
      out += "Säsongens antal race:  " + seasonCount + "\n";
      seasonResult = {
        name: this.name,
        count: seasonCount,
        improvement: compareTime - seasonBest,
      };
    }

    return { report: out, seasonResult };
  }

  toJSON() {
    return {
      name: this.name,
      best_time_seconds: this.best_time_seconds,
      number: this.number,
      race_history: this.race_history,
    };
  }

  static fromJSON(data) {
    const p = new Participant(data.name, data.best_time_seconds);
    if (data.number != null) p.number = data.number;
    if (Array.isArray(data.race_history)) p.race_history = data.race_history;
    return p;
  }
}

export class Race {
  constructor() {
    // Instance state (the desktop version used shared class attributes — a bug
    // once more than one Race can exist; fixed here).
    this.participants = [];
    this.goal_time_list_seconds = [];
    this.goal_list_participant = [];
    this.start_time = null; // Date, or null before the race starts
    this.longest_time = RACE_INITIAL_TIME;
  }

  getParticipantStartTime(participant) {
    const calc = participant.best_time_seconds > RACE_INITIAL_TIME
      ? RACE_INITIAL_TIME // cap so the field isn't spread out too much
      : participant.best_time_seconds;
    return this.longest_time - calc;
  }

  getRaceDuration() {
    if (this.start_time !== null) {
      return (Date.now() - this.start_time.getTime()) / 1000;
    }
    return 0;
  }

  // Fixed-width text table; byte-for-byte compatible with racebase.get_start_list.
  getStartList() {
    let out = "";
    out += ljust("start", 6);
    out += "Nr ";
    out += ljust("Namn", 20);
    out += ljust("best", 6);
    out += ljust("start", 6);
    out += ljust("mål", 6);
    out += ljust("tid", 6);
    out += ljust("förbättring", 12);
    out += "\n";

    const raceDuration = this.getRaceDuration();

    for (const a of this.participants) {
      out += ljust(getTimeString(this.getParticipantStartTime(a) - raceDuration), 6);
      out += ljust(String(a.number), 2).slice(0, 2) + " ";
      out += ljust(a.name, 20).slice(0, 20);
      out += ljust(getTimeString(a.best_time_seconds), 6);
      out += ljust(getTimeString(this.getParticipantStartTime(a)), 6);
      out += ljust(getTimeString(a.race_finish_time_seconds), 6);
      out += ljust(getTimeString(a.race_time_seconds), 6);
      out += ljust(getTimeString(a.race_improvement_seconds), 12);
      out += "\n";
    }
    return out;
  }

  getGoalTimeList() {
    const list = [];
    let index = 0;
    for (const timeEntry of this.goal_time_list_seconds) {
      let entry = getTimeString(timeEntry);
      if (this.goal_list_participant.length && index < this.goal_list_participant.length) {
        entry += " - " + this.goal_list_participant[index].name;
      }
      index += 1;
      list.push(entry);
    }
    return list;
  }

  findParticipant(name) {
    return this.participants.find((p) => p.name === name) || null;
  }

  // Add a participant to the current race. `time` (seconds) sets a new best time.
  addParticipant(name, number, time = null, roster = null) {
    let participant = this.findParticipant(name);
    if (participant === null) {
      // Pull existing history from the roster if we know this kayaker.
      const known = roster ? roster.find((p) => p.name === name) : null;
      participant = known || new Participant(name);
      this.participants.push(participant);
    }
    if (time !== null) participant.best_time_seconds = time;
    participant.number = number;

    this.participants.sort((a, b) => b.best_time_seconds - a.best_time_seconds);
    const longestBest = this.participants[0].best_time_seconds;
    this.longest_time = longestBest > RACE_INITIAL_TIME
      ? RACE_INITIAL_TIME
      : this.participants[0].best_time_seconds;
  }

  removeParticipant(name) {
    const p = this.findParticipant(name);
    if (p !== null) this.participants.splice(this.participants.indexOf(p), 1);
  }

  start() {
    this.start_time = new Date();
  }

  // Reset timing/goal data back to a pre-start state, keeping the participants
  // so the same field is ready for a fresh start.
  resetTiming() {
    this.start_time = null;
    this.goal_time_list_seconds = [];
    this.goal_list_participant = [];
    for (const p of this.participants) {
      p.race_finish_time_seconds = 0;
      p.race_time_seconds = 0;
      p.race_improvement_seconds = 0;
    }
  }

  // Step 4: stamp a goal-line crossing (a bare time, not yet tied to a racer).
  timestampGoal() {
    if (this.start_time === null) return;
    this.goal_time_list_seconds.push((Date.now() - this.start_time.getTime()) / 1000);
  }

  // Step 5: pair the next unassigned crossing time (by index) with a racer,
  // computing their result and improvement.
  assignNextFinishTime(name) {
    const participant = this.findParticipant(name);
    const index = this.goal_list_participant.length;
    if (this.goal_time_list_seconds.length && index < this.goal_time_list_seconds.length) {
      const finishTime = this.goal_time_list_seconds[index];
      this.goal_list_participant.push(participant);
      const startTime = this.getParticipantStartTime(participant);
      const result = finishTime - startTime;
      participant.race_finish_time_seconds = finishTime;
      participant.race_time_seconds = result;
      participant.race_improvement_seconds = participant.best_time_seconds - result;
      this.participants.sort(
        (a, b) => b.race_improvement_seconds - a.race_improvement_seconds
      );
      return true;
    }
    return false;
  }

  // Matching (step 5): given bib-crossing order as a list of names aligned to
  // captured crossing times (index i = i-th crossing), compute every result.
  // `orderedNames[i]` may be null/undefined for an unmatched crossing.
  assignResults(orderedNames) {
    // Reset any previous matching.
    this.goal_list_participant = [];
    for (const p of this.participants) {
      p.race_finish_time_seconds = 0;
      p.race_time_seconds = 0;
      p.race_improvement_seconds = 0;
    }
    const n = Math.min(orderedNames.length, this.goal_time_list_seconds.length);
    for (let i = 0; i < n; i++) {
      const name = orderedNames[i];
      const p = name ? this.findParticipant(name) : null;
      this.goal_list_participant[i] = p; // may be null (a gap)
      if (!p) continue;
      const finishTime = this.goal_time_list_seconds[i];
      const startTime = this.getParticipantStartTime(p);
      const result = finishTime - startTime;
      p.race_finish_time_seconds = finishTime;
      p.race_time_seconds = result;
      p.race_improvement_seconds = p.best_time_seconds - result;
    }
    this.participants.sort((a, b) => b.race_improvement_seconds - a.race_improvement_seconds);
  }

  removeLastAssigned() {
    if (this.goal_list_participant.length) {
      return this.goal_list_participant.pop().name;
    }
    return null;
  }

  removeFinishTimeIndex(index) {
    if (index < this.goal_time_list_seconds.length && index >= this.goal_list_participant.length) {
      // Only allow removal if no participant is assigned to this time.
      this.goal_time_list_seconds.splice(index, 1);
    }
  }

  addFinishTime(timeInSeconds) {
    this.goal_time_list_seconds.push(timeInSeconds);
    this.goal_time_list_seconds.sort((a, b) => a - b);
  }

  // Fold each finisher's result into their best time and append to their
  // history. Non-finishers (no crossing assigned) are skipped — unlike the
  // desktop save(), which recorded a 0-second race for them. Returns the race
  // identifier string. Callers persist via the bundle.
  finalize() {
    const raceString = formatRaceStamp(this.start_time || new Date());
    for (const a of this.participants) {
      if (a.race_finish_time_seconds > 0) {
        if (a.best_time_seconds > a.race_time_seconds) {
          a.best_time_seconds = a.race_time_seconds;
        }
        a.storeRace(raceString);
      }
    }
    return raceString;
  }

  // Snapshot of an in-progress race, for surviving a browser refresh. NOT the
  // shareable bundle — this is transient per-event state.
  snapshot() {
    return {
      participants: this.participants.map((p) => ({
        name: p.name,
        number: p.number,
        best_time_seconds: p.best_time_seconds,
      })),
      start_time: this.start_time ? this.start_time.toISOString() : null,
      goal_time_list_seconds: this.goal_time_list_seconds.slice(),
    };
  }

  // Rebuild a Race from a snapshot, re-linking to live roster objects by name so
  // that finalize() writes back to the roster.
  static fromSnapshot(snap, roster = []) {
    const race = new Race();
    for (const s of snap.participants || []) {
      race.addParticipant(s.name, s.number, s.best_time_seconds, roster);
    }
    if (snap.start_time) race.start_time = new Date(snap.start_time);
    race.goal_time_list_seconds = (snap.goal_time_list_seconds || []).slice();
    return race;
  }
}

// "YYYYMMDD-HHMMSS" — the year prefix is what season reports bucket on.
export function formatRaceStamp(date) {
  const p = (n, w = 2) => String(n).padStart(w, "0");
  return (
    `${date.getFullYear()}${p(date.getMonth() + 1)}${p(date.getDate())}` +
    `-${p(date.getHours())}${p(date.getMinutes())}${p(date.getSeconds())}`
  );
}
