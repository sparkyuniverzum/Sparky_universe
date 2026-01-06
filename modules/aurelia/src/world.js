// src/world.js

import { createAureliaCore } from "./core/aureliaCore.js";
import { addEvent } from "./core/eventLog.js";
import { analyzeText } from "./core/textAnalysis.js";
import { saveLocal, loadLocal, loadLegacyLocal } from "./persistence/localStore.js";
import { syncToCloud } from "./persistence/syncStub.js";
import { generateDialogue } from "./core/dialogue.js";

let aurelia = null;
let activeUserId = "local";

/* ================================
   INIT / GET
================================ */

export function initWorld(options = {}) {
  const resolved = normalizeInitOptions(options);
  activeUserId = resolved.userId;

  const stored = loadLocal(activeUserId) || (activeUserId === "local" ? loadLegacyLocal() : null);
  const baseOptions = { userId: activeUserId, planetSeed: resolved.planetSeed };
  aurelia = stored ? normalizeWorld(stored, baseOptions) : createAureliaCore(baseOptions);
  ensureDerivedState(aurelia, baseOptions);
  return aurelia;
}

export function setActiveUser(userId, planetSeed = null) {
  return initWorld({ userId, planetSeed });
}

export function getActiveUserId() {
  return activeUserId;
}

export function getWorld() {
  return aurelia;
}

/* ================================
   JOURNAL ENTRY
================================ */

export function applyJournalEntry(text) {
  if (!aurelia) return null;

  const signals = analyzeText(text);
  applyDecay(aurelia);

  const { sentiment, intensity, themeWeight } = signals;
  const conflict = themeWeight.conflict;
  const stability = themeWeight.stability;
  const curiosity = themeWeight.curiosity;

  updateLongMemory(aurelia, signals);
  updateMidMemory(aurelia, signals);
  updateEpochs(aurelia, signals);

  // Presence
  aurelia.presence.awareness = clamp(
    aurelia.presence.awareness + intensity * 0.05,
    0,
    1
  );
  aurelia.presence.tension = clamp(
    aurelia.presence.tension + intensity * (conflict * 0.22 + Math.max(0, -sentiment) * 0.08),
    0,
    1
  );
  aurelia.presence.entropy = clamp(
    aurelia.presence.entropy + intensity * (1 - stability) * 0.18,
    0,
    1
  );
  aurelia.presence.curiosity = clamp(
    aurelia.presence.curiosity + intensity * curiosity * 0.22,
    0,
    1
  );

  // Inner state
  aurelia.innerState.fear = clamp(
    aurelia.innerState.fear + Math.max(0, -sentiment) * intensity * 0.25,
    0,
    1
  );
  aurelia.innerState.trust = clamp(
    aurelia.innerState.trust + Math.max(0, sentiment) * intensity * 0.25,
    0,
    1
  );
  aurelia.innerState.stability = clamp(
    aurelia.innerState.stability + (stability - conflict) * intensity * 0.25,
    0,
    1
  );

  if (typeof aurelia.innerState.curiosity === "number") {
    aurelia.innerState.curiosity = clamp(
      aurelia.innerState.curiosity + intensity * curiosity * 0.12,
      0,
      1
    );
  } else {
    aurelia.innerState.curiosity = aurelia.presence.curiosity;
  }

  aurelia.presence.mood = deriveMood(aurelia.presence, aurelia.innerState);

  if (aurelia.daily) {
    aurelia.daily.lastIntensity = signals.intensity;
  }

  if (needsDailyQuestion()) {
    setDailyDraft(aurelia, text, signals);
  } else {
    upsertDailyLog(aurelia, text, signals, 0);
  }

  addEvent(aurelia, "journal", { text, signals });

  persist();

  return signals;
}

export function needsDailyQuestion() {
  if (!aurelia || !aurelia.daily) return false;
  const today = getLocalDateKey();
  return aurelia.daily.lastQuestionDate !== today;
}

export function applyDailyAnswer(isPositive) {
  if (!aurelia || !aurelia.daily) return;

  const intensity = clamp(aurelia.daily.lastIntensity ?? 0.5, 0, 1);
  const delta = DAILY_STEP * (0.5 + intensity * 0.5) * (isPositive ? 1 : -1);

  aurelia.daily.trend = clamp(aurelia.daily.trend + delta, -1, 1);

  if (isPositive) {
    aurelia.innerState.trust = clamp(aurelia.innerState.trust + 0.06, 0, 1);
    aurelia.innerState.stability = clamp(aurelia.innerState.stability + 0.05, 0, 1);
    aurelia.presence.tension = clamp(aurelia.presence.tension - 0.04, 0, 1);
    aurelia.presence.entropy = clamp(aurelia.presence.entropy - 0.03, 0, 1);
  } else {
    aurelia.innerState.fear = clamp(aurelia.innerState.fear + 0.06, 0, 1);
    aurelia.innerState.stability = clamp(aurelia.innerState.stability - 0.05, 0, 1);
    aurelia.presence.tension = clamp(aurelia.presence.tension + 0.05, 0, 1);
    aurelia.presence.entropy = clamp(aurelia.presence.entropy + 0.04, 0, 1);
  }

  const reachedImprint = Math.abs(aurelia.daily.trend) >= DAILY_IMPRINT_THRESHOLD;
  let imprintDelta = 0;
  if (reachedImprint) {
    const sign = Math.sign(aurelia.daily.trend);
    imprintDelta = sign * DAILY_IMPRINT_STEP;
    aurelia.daily.imprint = clamp(aurelia.daily.imprint + imprintDelta, -1, 1);
    aurelia.daily.trend = 0;
    aurelia.daily.lastImprintAt = Date.now();

    aurelia.longMemory.stability = clamp(
      aurelia.longMemory.stability + sign * 0.04,
      0,
      1
    );
    aurelia.longMemory.conflict = clamp(
      aurelia.longMemory.conflict - sign * 0.03,
      0,
      1
    );
    aurelia.longMemory.sentiment = clamp(
      aurelia.longMemory.sentiment + sign * 0.05,
      -1,
      1
    );
  }

  aurelia.presence.mood = deriveMood(aurelia.presence, aurelia.innerState);
  aurelia.daily.lastQuestionDate = getLocalDateKey();

  finalizeDailyLog(aurelia, imprintDelta);

  addEvent(aurelia, "daily_answer", { isPositive, trend: aurelia.daily.trend });
  persist();
}

export function setWeeklySummaryWeek(weekKey) {
  if (!aurelia || !aurelia.daily) return;
  aurelia.daily.lastSummaryWeek = weekKey;
  persist();
}

/* ================================
   ANSWERS (DECISIONS)
================================ */

export function applyAnswers(answers) {
  if (!aurelia) return;

  const { truth, responsibility, facing } = answers;

  // Laws
  if (truth === "truth") aurelia.laws.permeability += 0.1;
  if (truth === "comfort") aurelia.laws.stability += 0.1;

  // Presence
  if (responsibility === "responsibility") aurelia.presence.tension -= 0.05;
  if (responsibility === "reaction") aurelia.presence.tension += 0.1;

  // Thresholds
  if (facing === "facing") aurelia.thresholds.major += 0.05;
  if (facing === "escape") aurelia.thresholds.major -= 0.05;

  // Conflicts
  if (facing === "escape") aurelia.conflicts.controlVsFreedom += 0.1;
  if (facing === "facing") aurelia.conflicts.controlVsFreedom -= 0.05;

  aurelia.conflicts.controlVsFreedom = clamp(aurelia.conflicts.controlVsFreedom, -1, 1);

  addEvent(aurelia, "answer", { ...answers });

  persist();
}

/* ================================
   DIALOGUE
================================ */

export function getDialogue() {
  if (!aurelia) return "";
  return generateDialogue(aurelia);
}

/* ================================
   PERSISTENCE
================================ */

function persist() {
  if (aurelia?.meta) {
    aurelia.meta.userId = activeUserId;
  }
  saveLocal(aurelia, activeUserId);
  syncToCloud(aurelia);
}

/* ================================
   HELPERS
================================ */

const BASELINE = {
  presence: {
    awareness: 0.2,
    tension: 0.05,
    entropy: 0.03,
    curiosity: 0.3,
  },
  innerState: {
    trust: 0.5,
    fear: 0.2,
    stability: 0.5,
    curiosity: 0.4,
  },
  midMemory: {
    conflict: 0.4,
    stability: 0.5,
    curiosity: 0.4,
    sentiment: 0.0,
  },
  longMemory: {
    conflict: 0.35,
    stability: 0.5,
    curiosity: 0.4,
    sentiment: 0.0,
  },
  daily: {
    lastQuestionDate: null,
    trend: 0.0,
    imprint: 0.0,
    lastIntensity: 0.0,
    lastImprintAt: null,
    lastSummaryWeek: null,
  },
  dailyLogs: {},
  dailyDraft: null,
  geography: {
    seedA: 0.37,
    seedB: 0.61,
  },
};

const DECAY_RATE = 0.92;
const LONG_MEMORY_RATE = 0.04;
const MID_MEMORY_RATE = 0.12;
const EPOCH_SIZE = 7;
const MAX_EPOCHS = 12;
const MAX_DAILY_LOGS = 400;
const DAILY_STEP = 0.1;
const DAILY_IMPRINT_THRESHOLD = 0.8;
const DAILY_IMPRINT_STEP = 0.12;

function normalizeWorld(stored, options = {}) {
  const base = createAureliaCore(options);
  const normalized = {
    ...base,
    ...stored,
    meta: { ...base.meta, ...stored.meta, userId: options.userId || stored.meta?.userId || base.meta.userId },
    presence: { ...base.presence, ...stored.presence },
    drives: { ...base.drives, ...stored.drives },
    laws: { ...base.laws, ...stored.laws },
    perception: { ...base.perception, ...stored.perception },
    thresholds: { ...base.thresholds, ...stored.thresholds },
    innerState: { ...base.innerState, ...stored.innerState },
    conflicts: { ...base.conflicts, ...stored.conflicts },
    midMemory: { ...base.midMemory, ...stored.midMemory },
    longMemory: { ...base.longMemory, ...stored.longMemory },
    geography: { ...base.geography, ...stored.geography },
    identity: { ...base.identity, ...stored.identity },
    daily: { ...base.daily, ...stored.daily },
    dailyLogs: stored.dailyLogs && typeof stored.dailyLogs === "object" ? stored.dailyLogs : {},
    dailyDraft: stored.dailyDraft ?? null,
    epochs: Array.isArray(stored.epochs) ? stored.epochs : [],
    epochBuffer: { ...base.epochBuffer, ...stored.epochBuffer },
    memory: Array.isArray(stored.memory) ? stored.memory : [],
    marks: Array.isArray(stored.marks) ? stored.marks : [],
  };
  ensureDerivedState(normalized, options);
  return normalized;
}

function applyDecay(state) {
  const p = state.presence;
  const i = state.innerState;

  p.awareness = decayValue(p.awareness, BASELINE.presence.awareness);
  p.tension = decayValue(p.tension, BASELINE.presence.tension);
  p.entropy = decayValue(p.entropy, BASELINE.presence.entropy);
  p.curiosity = decayValue(p.curiosity ?? BASELINE.presence.curiosity, BASELINE.presence.curiosity);

  i.trust = decayValue(i.trust, BASELINE.innerState.trust);
  i.fear = decayValue(i.fear, BASELINE.innerState.fear);
  i.stability = decayValue(i.stability ?? BASELINE.innerState.stability, BASELINE.innerState.stability);

  if (typeof i.curiosity === "number") {
    i.curiosity = decayValue(i.curiosity, BASELINE.innerState.curiosity);
  }
}

function decayValue(current, baseline) {
  return baseline + (current - baseline) * DECAY_RATE;
}

function deriveMood(presence, innerState) {
  if (innerState.fear > 0.7 && presence.tension > 0.6) return "hostile";
  if (presence.tension > 0.65 || presence.entropy > 0.65) return "disturbed";
  if (presence.curiosity > 0.6) return "curious";
  if (innerState.trust > 0.65 && presence.tension < 0.3) return "calm";
  return "observing";
}

function updateLongMemory(state, signals) {
  const lm = state.longMemory ?? { ...BASELINE.longMemory };
  const intensity = signals.intensity;
  const mix = clamp(LONG_MEMORY_RATE * (0.4 + intensity * 0.6), 0.01, 0.12);

  lm.conflict = clamp(lerp(lm.conflict, signals.themeWeight.conflict, mix), 0, 1);
  lm.stability = clamp(lerp(lm.stability, signals.themeWeight.stability, mix), 0, 1);
  lm.curiosity = clamp(lerp(lm.curiosity, signals.themeWeight.curiosity, mix), 0, 1);
  lm.sentiment = clamp(lerp(lm.sentiment, signals.sentiment, mix), -1, 1);

  state.longMemory = lm;
  updateGeography(state, intensity);
}

function updateMidMemory(state, signals) {
  const mm = state.midMemory ?? { ...BASELINE.midMemory };
  const intensity = signals.intensity;
  const mix = clamp(MID_MEMORY_RATE * (0.55 + intensity * 0.45), 0.05, 0.25);

  mm.conflict = clamp(lerp(mm.conflict, signals.themeWeight.conflict, mix), 0, 1);
  mm.stability = clamp(lerp(mm.stability, signals.themeWeight.stability, mix), 0, 1);
  mm.curiosity = clamp(lerp(mm.curiosity, signals.themeWeight.curiosity, mix), 0, 1);
  mm.sentiment = clamp(lerp(mm.sentiment, signals.sentiment, mix), -1, 1);

  state.midMemory = mm;
}

function updateEpochs(state, signals) {
  const buffer = state.epochBuffer ?? {
    count: 0,
    conflict: 0,
    stability: 0,
    curiosity: 0,
    sentiment: 0,
  };

  buffer.count += 1;
  buffer.conflict += signals.themeWeight.conflict;
  buffer.stability += signals.themeWeight.stability;
  buffer.curiosity += signals.themeWeight.curiosity;
  buffer.sentiment += signals.sentiment;

  if (buffer.count >= EPOCH_SIZE) {
    const epochIndex = Array.isArray(state.epochs) ? state.epochs.length : 0;
    const seeds = deriveEpochSeeds(state, epochIndex);
    const epoch = {
      id: makeId(),
      createdAt: Date.now(),
      conflict: clamp(buffer.conflict / buffer.count, 0, 1),
      stability: clamp(buffer.stability / buffer.count, 0, 1),
      curiosity: clamp(buffer.curiosity / buffer.count, 0, 1),
      sentiment: clamp(buffer.sentiment / buffer.count, -1, 1),
      seedA: seeds.seedA,
      seedB: seeds.seedB,
    };

    const epochs = Array.isArray(state.epochs) ? state.epochs : [];
    epochs.push(epoch);
    while (epochs.length > MAX_EPOCHS) {
      epochs.shift();
    }
    state.epochs = epochs;

    buffer.count = 0;
    buffer.conflict = 0;
    buffer.stability = 0;
    buffer.curiosity = 0;
    buffer.sentiment = 0;
  }

  state.epochBuffer = buffer;
}

function setDailyDraft(state, text, signals) {
  const date = getLocalDateKey();
  state.dailyDraft = {
    date,
    journalEntry: text,
    signals,
  };
}

function finalizeDailyLog(state, imprintDelta) {
  const date = getLocalDateKey();
  if (state.dailyDraft && state.dailyDraft.date === date) {
    const draft = state.dailyDraft;
    upsertDailyLog(state, draft.journalEntry, draft.signals, imprintDelta);
    state.dailyDraft = null;
  } else {
    upsertDailyLog(state, "", null, imprintDelta);
  }
}

function upsertDailyLog(state, text, signals, imprintDelta) {
  const date = getLocalDateKey();
  const snapshot = buildDailySnapshot(state);
  const entry = {
    date,
    journalEntry: text || "",
    signals: signals || null,
    presence: snapshot.presence,
    imprintDelta,
    visualSnapshot: snapshot.visualSnapshot,
    renderSnapshot: snapshot.renderSnapshot,
  };

  state.dailyLogs[date] = entry;
  pruneDailyLogs(state);
}

function buildDailySnapshot(state) {
  const p = state.presence;
  const i = state.innerState;
  const daily = state.daily ?? BASELINE.daily;
  const dailyValue = clamp(daily.trend + daily.imprint * 0.6, -1, 1);
  const storm = clamp(-dailyValue, 0, 1);
  const flora = clamp(dailyValue, 0, 1);
  const dayShift = dailyValue * 0.16;
  const dayLength = clamp(0.5 + dayShift * 0.5, 0.2, 0.8);
  const jitter = storm * 0.022;

  return {
    presence: {
      trust: clamp(i.trust ?? 0, 0, 1),
      fear: clamp(i.fear ?? 0, 0, 1),
      tension: clamp(p.tension ?? 0, 0, 1),
      entropy: clamp(p.entropy ?? 0, 0, 1),
      curiosity: clamp(p.curiosity ?? 0, 0, 1),
      stability: clamp(i.stability ?? 0, 0, 1),
    },
    visualSnapshot: {
      dayLength,
      storm,
      flora,
      jitter,
    },
    renderSnapshot: {
      presence: {
        mood: p.mood ?? "observing",
        tension: clamp(p.tension ?? 0, 0, 1),
        entropy: clamp(p.entropy ?? 0, 0, 1),
        curiosity: clamp(p.curiosity ?? 0, 0, 1),
      },
      innerState: {
        trust: clamp(i.trust ?? 0, 0, 1),
        fear: clamp(i.fear ?? 0, 0, 1),
        stability: clamp(i.stability ?? 0, 0, 1),
      },
      identity: state.identity ? { ...state.identity } : null,
      longMemory: { ...state.longMemory },
      midMemory: { ...state.midMemory },
      geography: { ...state.geography },
      daily: {
        trend: daily.trend ?? 0,
        imprint: daily.imprint ?? 0,
        lastIntensity: daily.lastIntensity ?? 0,
      },
      epochs: Array.isArray(state.epochs) ? state.epochs.slice(-2).map((epoch) => ({ ...epoch })) : [],
    },
  };
}

function pruneDailyLogs(state) {
  const keys = Object.keys(state.dailyLogs);
  if (keys.length <= MAX_DAILY_LOGS) return;

  keys.sort();
  const excess = keys.length - MAX_DAILY_LOGS;
  for (let i = 0; i < excess; i += 1) {
    delete state.dailyLogs[keys[i]];
  }
}

function ensureDerivedState(state, options = {}) {
  if (!state.longMemory) {
    state.longMemory = { ...BASELINE.longMemory };
  }
  if (!state.midMemory) {
    state.midMemory = { ...BASELINE.midMemory };
  }
  if (!state.daily) {
    state.daily = { ...BASELINE.daily };
  }
  if (!state.dailyLogs || typeof state.dailyLogs !== "object") {
    state.dailyLogs = {};
  }
  if (!state.dailyDraft) {
    state.dailyDraft = null;
  }

  if (!state.identity || typeof state.identity.seedA !== "number" || typeof state.identity.seedB !== "number") {
    state.identity = createIdentity(state.meta?.userId || options.userId, options.planetSeed);
  }
  const needsGeo = !state.geography
    || typeof state.geography.seedA !== "number"
    || typeof state.geography.seedB !== "number"
    || (state.geography.seedA === BASELINE.geography.seedA && state.geography.seedB === BASELINE.geography.seedB);

  if (needsGeo) {
    state.geography = deriveGeography(state.longMemory, state.identity);
  }

  if (!Array.isArray(state.epochs)) {
    state.epochs = [];
  }
  state.epochs = state.epochs.map((epoch, index) => {
    if (!epoch || typeof epoch !== "object") return epoch;
    const hasSeeds = typeof epoch.seedA === "number" && typeof epoch.seedB === "number";
    if (hasSeeds) return epoch;
    const seeds = deriveEpochSeeds(state, index);
    return { ...epoch, seedA: seeds.seedA, seedB: seeds.seedB };
  });
  if (!state.epochBuffer) {
    state.epochBuffer = { count: 0, conflict: 0, stability: 0, curiosity: 0, sentiment: 0 };
  }
}

function updateGeography(state, intensity) {
  const geo = state.geography ?? deriveGeography(state.longMemory, state.identity);
  const target = deriveGeography(state.longMemory, state.identity);
  const rate = clamp(0.006 + intensity * 0.03, 0.006, 0.05);

  geo.seedA = lerp(geo.seedA, target.seedA, rate);
  geo.seedB = lerp(geo.seedB, target.seedB, rate);
  state.geography = geo;
}

function deriveGeography(longMemory, identity) {
  const sentimentBias = (longMemory.sentiment + 1) * 0.5;
  const baseA = typeof identity?.seedA === "number" ? identity.seedA : BASELINE.geography.seedA;
  const baseB = typeof identity?.seedB === "number" ? identity.seedB : BASELINE.geography.seedB;
  const seedA = fract(
    baseA +
    longMemory.conflict * 0.37 +
    longMemory.curiosity * 0.29 +
    sentimentBias * 0.11
  );
  const seedB = fract(
    baseB +
    longMemory.stability * 0.33 +
    longMemory.curiosity * 0.21 +
    (1 - Math.abs(longMemory.sentiment)) * 0.17
  );

  return { seedA, seedB };
}

function deriveEpochSeeds(state, index) {
  const lm = state.longMemory ?? BASELINE.longMemory;
  const base =
    Date.now() * 0.0001 +
    lm.conflict * 3.13 +
    lm.stability * 5.71 +
    lm.curiosity * 2.97 +
    lm.sentiment * 1.41 +
    index * 0.77;

  const seedA = fract(Math.sin(base) * 43758.5453);
  const seedB = fract(Math.sin(base + 1.234) * 24634.6345);

  return { seedA, seedB };
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function fract(value) {
  return value - Math.floor(value);
}

function makeId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `epoch_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
}

function getLocalDateKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function normalizeInitOptions(options) {
  if (!options) return { userId: "local", planetSeed: null };
  if (typeof options === "string") return { userId: options, planetSeed: null };

  const userId = options.userId ? String(options.userId) : "local";
  const planetSeed = options.planetSeed ? String(options.planetSeed) : null;
  return { userId, planetSeed };
}

function createIdentity(userId, planetSeed) {
  const baseSeed = planetSeed || userId || (crypto.randomUUID ? crypto.randomUUID() : `local_${Date.now()}`);
  const seed = String(baseSeed);
  const rand = seededRandom(seed);

  return {
    seed,
    seedA: rand(),
    seedB: rand(),
    paletteBias: rand() * 2 - 1,
    ringTilt: rand() * 2 - 1,
    cloudSeed: rand(),
  };
}

function seededRandom(seed) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i += 1) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }

  return function rand() {
    h += 0x6d2b79f5;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}





