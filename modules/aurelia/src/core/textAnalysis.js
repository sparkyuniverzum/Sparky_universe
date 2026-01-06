// src/core/textAnalysis.js

const POSITIVE_WORDS = new Map([
  ["calm", 0.6],
  ["ok", 0.3],
  ["fine", 0.4],
  ["good", 0.6],
  ["great", 0.8],
  ["better", 0.5],
  ["improve", 0.5],
  ["progress", 0.5],
  ["hope", 0.5],
  ["hopeful", 0.6],
  ["safe", 0.6],
  ["secure", 0.6],
  ["comfort", 0.5],
  ["thanks", 0.4],
  ["thank", 0.4],
  ["grateful", 0.6],
  ["love", 0.7],
  ["trust", 0.7],
  ["support", 0.5],
  ["care", 0.4],
  ["relief", 0.6],
  ["peace", 0.6],
  ["joy", 0.7],
  ["happy", 0.7],
  ["smile", 0.4],
  ["light", 0.4],
  ["warm", 0.4],
  ["heal", 0.5],
  ["healing", 0.5],
  ["klid", 0.6],
  ["dobre", 0.6],
  ["diky", 0.4],
  ["vdecny", 0.6],
  ["spokojeny", 0.6],
  ["spokojenost", 0.6],
  ["uleva", 0.6],
  ["radost", 0.7],
  ["rad", 0.5],
  ["nadeje", 0.5],
  ["bezpeci", 0.6],
]);

const NEGATIVE_WORDS = new Map([
  ["bad", 0.6],
  ["sad", 0.6],
  ["hurt", 0.7],
  ["angry", 0.7],
  ["fear", 0.8],
  ["anxiety", 0.8],
  ["anxious", 0.8],
  ["depression", 0.9],
  ["depressed", 0.9],
  ["hopeless", 0.8],
  ["helpless", 0.8],
  ["tired", 0.5],
  ["exhausted", 0.7],
  ["sick", 0.6],
  ["lost", 0.6],
  ["empty", 0.6],
  ["alone", 0.7],
  ["panic", 0.8],
  ["pain", 0.7],
  ["stress", 0.6],
  ["stres", 0.6],
  ["worry", 0.6],
  ["danger", 0.7],
  ["broken", 0.7],
  ["rage", 0.7],
  ["cold", 0.4],
  ["smutek", 0.7],
  ["strach", 0.8],
  ["bojim", 0.7],
  ["uzkost", 0.8],
  ["deprese", 0.9],
  ["zoufalstvi", 0.8],
  ["bezmoc", 0.8],
  ["tma", 0.5],
  ["temno", 0.6],
  ["bolest", 0.7],
  ["sam", 0.7],
  ["samota", 0.8],
  ["vycerpany", 0.7],
  ["zlomeny", 0.8],
  ["zlost", 0.7],
]);

const INTENSIFIERS = new Map([
  ["very", 0.5],
  ["really", 0.4],
  ["deeply", 0.5],
  ["strongly", 0.5],
  ["extremely", 0.7],
  ["so", 0.2],
  ["too", 0.4],
  ["mega", 0.5],
  ["super", 0.4],
  ["totally", 0.5],
  ["quite", 0.2],
  ["fakt", 0.4],
  ["hodne", 0.4],
  ["moc", 0.4],
  ["uplne", 0.5],
  ["totalne", 0.5],
  ["vazne", 0.4],
  ["silne", 0.4],
  ["strasne", 0.5],
]);

const NEGATIONS = new Set([
  "not",
  "no",
  "never",
  "none",
  "ne",
  "neni",
  "nejsi",
  "nejsem",
  "nikdy",
  "bez",
  "nic",
  "nikdo",
  "zadny",
  "zadna",
  "zadne",
]);

const THEMES = {
  conflict: new Set([
    "fight",
    "argue",
    "broken",
    "chaos",
    "pressure",
    "conflict",
    "attack",
    "confuse",
    "war",
    "tension",
    "clash",
    "friction",
    "battle",
    "rage",
    "konflikt",
    "boj",
    "chaos",
    "tlak",
    "napeti",
    "hadka",
    "spor",
    "krize",
    "hnev",
  ]),
  stability: new Set([
    "stable",
    "balance",
    "home",
    "safe",
    "steady",
    "order",
    "routine",
    "peace",
    "anchor",
    "ground",
    "rest",
    "sleep",
    "harmonie",
    "rovnovaha",
    "klid",
    "stabilita",
    "rad",
    "rutina",
    "domov",
    "bezpeci",
    "jistota",
  ]),
  curiosity: new Set([
    "why",
    "wonder",
    "learn",
    "explore",
    "new",
    "change",
    "curious",
    "question",
    "discover",
    "seek",
    "search",
    "unknown",
    "interest",
    "investigate",
    "zvedavy",
    "proc",
    "objev",
    "objevovat",
    "novy",
    "nove",
    "zmena",
    "zkoumat",
    "zvedavost",
    "zajima",
    "hledat",
    "otazka",
    "prekvapeni",
  ]),
};

export function analyzeText(text) {
  const tokens = tokenize(text);
  if (tokens.length === 0) {
    return emptySignals();
  }

  let pos = 0;
  let neg = 0;
  let intensityBoost = 0;
  const themeCounts = { conflict: 0, stability: 0, curiosity: 0 };

  let negateNext = false;

  for (const token of tokens) {
    const base = normalizeToken(token);
    if (!base) {
      continue;
    }

    if (NEGATIONS.has(base)) {
      negateNext = true;
      continue;
    }

    const stem = stemToken(base);
    const key = base;

    const intensifier = getWeight(INTENSIFIERS, key, stem);
    if (intensifier) {
      intensityBoost += intensifier;
      continue;
    }

    let polarity = 0;
    polarity += getWeight(POSITIVE_WORDS, key, stem);
    polarity -= getWeight(NEGATIVE_WORDS, key, stem);

    if (polarity !== 0) {
      if (negateNext) {
        polarity *= -1;
        negateNext = false;
      }

      if (polarity > 0) {
        pos += polarity;
      } else {
        neg += Math.abs(polarity);
      }
    } else if (negateNext) {
      negateNext = false;
    }

    if (hasTheme(THEMES.conflict, key, stem)) themeCounts.conflict += 1;
    if (hasTheme(THEMES.stability, key, stem)) themeCounts.stability += 1;
    if (hasTheme(THEMES.curiosity, key, stem)) themeCounts.curiosity += 1;
  }

  const totalPolarity = pos + neg;
  const sentiment = totalPolarity > 0
    ? clamp((pos - neg) / totalPolarity, -1, 1)
    : 0;

  const themeSum = themeCounts.conflict + themeCounts.stability + themeCounts.curiosity;
  const themeWeight = themeSum > 0
    ? {
      conflict: themeCounts.conflict / themeSum,
      stability: themeCounts.stability / themeSum,
      curiosity: themeCounts.curiosity / themeSum,
    }
    : { conflict: 0, stability: 0, curiosity: 0 };

  const lengthFactor = clamp(tokens.length / 30, 0, 1);
  const polarityFactor = totalPolarity > 0
    ? clamp(totalPolarity / (tokens.length || 1), 0, 1)
    : 0;
  const themeFactor = themeSum > 0
    ? clamp(themeSum / (tokens.length || 1), 0, 1)
    : 0;
  const intensity = clamp(
    0.4 * lengthFactor + 0.35 * (polarityFactor + themeFactor) + 0.25 * clamp(intensityBoost, 0, 1),
    0,
    1
  );

  return { sentiment, intensity, themeWeight };
}

function tokenize(text) {
  const match = text.toLowerCase().match(/[\p{L}\p{N}']+/gu);
  return match ? match : [];
}

function normalizeToken(token) {
  return token
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/['’`]/g, "");
}

function stemToken(token) {
  if (token.length <= 3) return token;

  const suffixes = [
    "ingly",
    "edly",
    "tions",
    "tion",
    "ment",
    "ovat",
    "ing",
    "ed",
    "ly",
    "es",
    "s",
    "ami",
    "emi",
    "ovi",
    "ova",
    "ove",
    "ovy",
    "ich",
    "ych",
    "ymi",
    "mi",
    "ni",
    "mu",
    "me",
    "ne",
    "na",
    "ny",
    "ho",
    "he",
    "ka",
    "ke",
    "ku",
    "ky",
    "ce",
    "ci",
  ];

  for (const suffix of suffixes) {
    if (token.length - suffix.length >= 3 && token.endsWith(suffix)) {
      return token.slice(0, -suffix.length);
    }
  }

  return token;
}

function getWeight(map, base, stem) {
  if (map.has(base)) return map.get(base);
  if (stem && map.has(stem)) return map.get(stem);
  return 0;
}

function hasTheme(set, base, stem) {
  return set.has(base) || (stem && set.has(stem));
}

function emptySignals() {
  return {
    sentiment: 0,
    intensity: 0,
    themeWeight: { conflict: 0, stability: 0, curiosity: 0 },
  };
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
