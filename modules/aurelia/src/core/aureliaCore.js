// src/core/aureliaCore.js

export function createAureliaCore(options = {}) {
  const { userId = null, planetSeed = null } = options;
  const now = Date.now();
  const identity = createIdentity(userId, planetSeed);

  return {
    /* ================================
       META
    ================================ */
    meta: {
      id: crypto.randomUUID(),
      version: "1.0.0",
      createdAt: now,
      lastUpdatedAt: now,
      userId: userId || null,
    },

    /* ================================
       PRESENCE – VĚDOMÍ
    ================================ */
    presence: {
      awareness: 0.2,
      mood: "observing", // calm | dormant | observing | curious | disturbed | hostile
      tension: 0.05,
      entropy: 0.03,
      curiosity: 0.3,
      lastReactionAt: null,
      lastMajorShiftAt: null,
    },

    /* ================================
       DRIVES – MOTIVACE
    ================================ */
    drives: {
      equilibrium: 0.5,
      change: 0.3,
      resistance: 0.4,
    },

    /* ================================
       LAWS – ZÁKONY SVĚTA
    ================================ */
    laws: {
      stability: 0.6,
      permeability: 0.3,
      entropyRate: 0.02,
      responseForce: 0.4,
      timeFlow: 1.0,
      distortion: 0.0,
    },

    /* ================================
       PERCEPTION – JAK TĚ VNÍMÁ
    ================================ */
    perception: {
      interferenceLevel: 0.0,
      patternConfidence: 0.0,
      unpredictability: 0.5,
    },

    /* ================================
       THRESHOLDS – PRAHY REAKCÍ
    ================================ */
    thresholds: {
      notice: 0.1,
      micro: 0.25,
      major: 0.65,
    },

    /* ================================
       PSYCHOLOGIE – VNITŘNÍ STAV
    ================================ */
    innerState: {
      trust: 0.5,
      fear: 0.2,
      stability: 0.5,
      curiosity: 0.4,
      attachment: 0.3,
    },

    /* ================================
       KONFLIKTY – VNITŘNÍ NAPĚTÍ
    ================================ */
    conflicts: {
      orderVsChaos: 0.0,
      controlVsFreedom: 0.0,
      closenessVsDistance: 0.0,
    },

    /* ================================
       DLOUHODOBÁ PAMĚŤ – STRUKTURA
    ================================ */
    longMemory: {
      conflict: 0.35,
      stability: 0.5,
      curiosity: 0.4,
      sentiment: 0.0,
    },

    /* ================================
       STŘEDNĚDOBÁ PAMĚŤ – KLIMA
    ================================ */
    midMemory: {
      conflict: 0.4,
      stability: 0.5,
      curiosity: 0.4,
      sentiment: 0.0,
    },

    /* ================================
       EPOCHY – VRSTVY PAMĚTI
    ================================ */
    epochs: [],
    epochBuffer: {
      count: 0,
      conflict: 0,
      stability: 0,
      curiosity: 0,
      sentiment: 0,
    },

    /* ================================
       DENNÍ OTÁZKA – DLOUHÝ DOZVUK
    ================================ */
    daily: {
      lastQuestionDate: null,
      trend: 0.0,
      imprint: 0.0,
      lastIntensity: 0.0,
      lastImprintAt: null,
      lastSummaryWeek: null,
    },

    /* ================================
       DENNÍ LOGY
    ================================ */
    dailyLogs: {},
    dailyDraft: null,

    /* ================================
       GEOGRAFIE – SEMÍNKO KONTINENTŮ
    ================================ */
    geography: {
      seedA: identity.seedA,
      seedB: identity.seedB,
    },

    /* ================================
       IDENTITY – UNIKÁTNÍ PLANETA
    ================================ */
    identity,

    /* ================================
       PAMĚŤ + STOPY
    ================================ */
    memory: [],
    marks: [],
  };
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
