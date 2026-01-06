import {
  initWorld,
  getWorld,
  applyJournalEntry,
  needsDailyQuestion,
  applyDailyAnswer,
  setWeeklySummaryWeek,
} from "./world.js";
import { createRenderer } from "./visual/glRenderer.js";

document.addEventListener("DOMContentLoaded", () => {
  const identity = resolveUserIdentity();
  const aurelia = initWorld(identity);
  console.log("Aurelia loaded:", aurelia);
  window.AURELIA = getWorld;

  const canvas = document.getElementById("worldCanvas");
  if (!canvas) {
    console.error("Canvas not found in DOM!");
    return;
  }

  const renderer = createRenderer(canvas);
  if (!renderer) {
    console.error("WebGL not available.");
    return;
  }

  const submitBtn = document.getElementById("submitJournal");
  const journalInput = document.getElementById("journalInput");
  const body = document.body;
  const dailyPanel = document.getElementById("dailyQuestion");
  const dailyYes = document.getElementById("dailyYes");
  const dailyNo = document.getElementById("dailyNo");
  const calendarGrid = document.getElementById("calendarGrid");
  const dayOverlay = document.getElementById("dayOverlay");
  const dayPreview = document.getElementById("dayPreview");
  const dayEntry = document.getElementById("dayEntry");
  const closeOverlay = document.getElementById("closeOverlay");
  const weeklySummary = document.getElementById("weeklySummary");
  const focusOverlay = document.getElementById("focusOverlay");
  const focusCanvas = document.getElementById("focusCanvas");
  const closeFocus = document.getElementById("closeFocus");

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const width = Math.floor(rect.width * dpr);
    const height = Math.floor(rect.height * dpr);

    canvas.width = width;
    canvas.height = height;
    renderer.resize(width, height);

    if (focusOverlay && !focusOverlay.hidden) {
      resizeFocusCanvas();
    }
  }

  window.addEventListener("resize", resize);
  resize();

  let cinematic = true;
  const storedCinematic = localStorage.getItem("aurelia_cinematic");
  if (storedCinematic !== null) {
    cinematic = storedCinematic === "1";
  }
  renderer.setCinematic(cinematic);

  window.addEventListener("keydown", (event) => {
    if (event.key && event.key.toLowerCase() === "c") {
      cinematic = !cinematic;
      renderer.setCinematic(cinematic);
      localStorage.setItem("aurelia_cinematic", cinematic ? "1" : "0");
    }
  });

  function animate(now) {
    const world = getWorld();
    renderer.render(world, now * 0.001);
    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);

  const RITUAL_DELAY_MS = 6000;
  const GLYPH_CANVAS_SIZE = 24;
  let ritualTimer = null;
  let summaryTimer = null;
  let focusRenderer = null;
  let focusLoopId = null;
  let focusState = null;

  if (focusCanvas) {
    focusRenderer = createRenderer(focusCanvas);
  }

  function setRitualState(active) {
    if (journalInput) {
      journalInput.disabled = active;
    }
    if (submitBtn) {
      submitBtn.disabled = active;
    }
    if (body) {
      body.classList.toggle("is-ritual", active);
    }
  }

  function showDailyQuestion(show) {
    if (!dailyPanel) {
      if (show) {
        setRitualState(false);
      }
      return;
    }
    dailyPanel.hidden = !show;
    if (show) {
      setRitualState(true);
    }
  }

  function handleDailyAnswer(isPositive) {
    applyDailyAnswer(isPositive);
    showDailyQuestion(false);
    setRitualState(false);
    refreshCalendar();
    maybeShowWeeklySummary();
  }

  if (!submitBtn || !journalInput) {
    console.warn("Journal UI not found, skipping journal hooks.");
  } else {
    const updateTypingState = () => {
      if (!body) return;
      body.classList.toggle("is-typing", journalInput.value.trim().length > 0);
    };

    journalInput.addEventListener("input", updateTypingState);
    journalInput.addEventListener("blur", () => {
      if (body) body.classList.remove("is-typing");
    });

    submitBtn.addEventListener("click", () => {
      if (ritualTimer) {
        return;
      }

      const text = journalInput.value.trim();
      if (!text) {
        return;
      }

      journalInput.value = "";
      updateTypingState();
      setRitualState(true);
      ritualTimer = window.setTimeout(() => {
        applyJournalEntry(text);
        ritualTimer = null;
        if (needsDailyQuestion()) {
          showDailyQuestion(true);
        } else {
          setRitualState(false);
          refreshCalendar();
          maybeShowWeeklySummary();
        }
      }, RITUAL_DELAY_MS);
    });
  }

  if (dailyYes && dailyNo) {
    dailyYes.addEventListener("click", () => handleDailyAnswer(true));
    dailyNo.addEventListener("click", () => handleDailyAnswer(false));
  }

  if (closeOverlay && dayOverlay) {
    closeOverlay.addEventListener("click", () => hideDayOverlay());
    dayOverlay.addEventListener("click", (event) => {
      if (event.target === dayOverlay) {
        hideDayOverlay();
      }
    });
  }

  if (focusOverlay && closeFocus) {
    closeFocus.addEventListener("click", () => closeFocusView());
    focusOverlay.addEventListener("click", (event) => {
      if (event.target === focusOverlay) {
        closeFocusView();
      }
    });
  }

  if (canvas) {
    canvas.addEventListener("click", () => openFocusView());
  }

  refreshCalendar();
  maybeShowWeeklySummary();

  function refreshCalendar() {
    if (!calendarGrid) return;
    const world = getWorld();
    const logs = world?.dailyLogs || {};
    const grid = buildMonthGrid(new Date());

    calendarGrid.innerHTML = "";
    grid.forEach((cell) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "calendar-cell";
      const canvas = document.createElement("canvas");
      canvas.width = GLYPH_CANVAS_SIZE;
      canvas.height = GLYPH_CANVAS_SIZE;
      button.appendChild(canvas);

      if (!cell) {
        button.disabled = true;
        calendarGrid.appendChild(button);
        return;
      }

      const log = logs[cell.dateKey];
      drawGlyph(canvas, log, cell.dateKey);

      if (log) {
        button.addEventListener("click", () => showDayOverlay(log));
      } else {
        button.disabled = true;
      }

      calendarGrid.appendChild(button);
    });
  }

  function openFocusView() {
    if (!focusOverlay || !focusRenderer) return;
    const world = getWorld();
    const logs = getSortedLogs(Object.values(world?.dailyLogs || {}));
    if (!logs.length) return;

    const toLog = logs[0];
    const fromLog = logs[1] || logs[0];
    const fromState = buildStateFromLog(fromLog);
    const toState = buildStateFromLog(toLog);

    focusOverlay.hidden = false;
    resizeFocusCanvas();

    const start = performance.now();
    const duration = 2000;

    function animateStep(now) {
      if (!focusOverlay || focusOverlay.hidden) return;
      const t = Math.min((now - start) / duration, 1);
      const eased = easeInOut(t);
      focusState = interpolateState(fromState, toState, eased);
      focusRenderer.render(focusState, now * 0.001);

      if (t < 1) {
        focusLoopId = requestAnimationFrame(animateStep);
      } else {
        focusState = toState;
        startFadeOut();
        focusLoopId = requestAnimationFrame(loopFocus);
      }
    }

    if (focusLoopId) {
      cancelAnimationFrame(focusLoopId);
    }
    focusLoopId = requestAnimationFrame(animateStep);
  }

  function loopFocus(now) {
    if (!focusOverlay || focusOverlay.hidden || !focusRenderer || !focusState) return;
    focusRenderer.render(focusState, now * 0.001);
    focusLoopId = requestAnimationFrame(loopFocus);
  }

  function closeFocusView() {
    if (!focusOverlay) return;
    focusOverlay.hidden = true;
    focusState = null;
    if (focusLoopId) {
      cancelAnimationFrame(focusLoopId);
      focusLoopId = null;
    }
  }

  function startFadeOut() {
    if (!focusOverlay) return;
    focusOverlay.classList.add("focus-fade");
    window.setTimeout(() => {
      focusOverlay.classList.remove("focus-fade");
    }, 300);
  }

  function resizeFocusCanvas() {
    if (!focusCanvas || !focusRenderer) return;
    const size = Math.min(window.innerWidth, window.innerHeight) * 0.94;
    const dpr = window.devicePixelRatio || 1;
    focusCanvas.width = Math.floor(size * dpr);
    focusCanvas.height = Math.floor(size * dpr);
    focusRenderer.resize(focusCanvas.width, focusCanvas.height);
  }

  function buildMonthGrid(now) {
    const year = now.getFullYear();
    const month = now.getMonth();
    const first = new Date(year, month, 1);
    const start = (first.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const cells = [];

    for (let i = 0; i < 35; i += 1) {
      const dayIndex = i - start + 1;
      if (dayIndex < 1 || dayIndex > daysInMonth) {
        cells.push(null);
        continue;
      }
      const date = new Date(year, month, dayIndex);
      cells.push({ dateKey: toDateKey(date) });
    }

    return cells;
  }

  function drawGlyph(canvas, log, seedKey) {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const snapshot = log?.visualSnapshot;
    drawPlanetGlyph(ctx, canvas.width, snapshot, seedKey, 0.8);
  }

  function showDayOverlay(log) {
    if (!dayOverlay || !dayPreview || !dayEntry) return;
    dayOverlay.hidden = false;
    dayEntry.value = log.journalEntry || "";
    drawLargePreview(dayPreview, log);
  }

  function hideDayOverlay() {
    if (!dayOverlay) return;
    dayOverlay.hidden = true;
  }

  function drawLargePreview(canvas, log) {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const snapshot = log?.visualSnapshot;
    const seed = log?.date || "preview";
    drawPlanetGlyph(ctx, canvas.width, snapshot, seed, 1.2);
  }

  function maybeShowWeeklySummary() {
    if (!weeklySummary) return;
    const world = getWorld();
    if (!world || !world.dailyLogs) return;

    const now = new Date();
    const weekKey = getWeekKey(now);
    if (world.daily?.lastSummaryWeek === weekKey) return;

    const logs = Object.values(world.dailyLogs).filter(Boolean);
    if (logs.length < 7) return;

    const last14 = getRecentLogs(logs, 14);
    const recent = last14.slice(0, 7);
    if (recent.length < 7) return;

    const previous = last14.slice(7, 14);
    const summary = buildWeeklySummary(recent, previous);

    weeklySummary.textContent = summary;
    weeklySummary.hidden = false;
    if (summaryTimer) {
      clearTimeout(summaryTimer);
    }
    summaryTimer = window.setTimeout(() => {
      weeklySummary.hidden = true;
    }, 2600);

    setWeeklySummaryWeek(weekKey);
  }

  function buildWeeklySummary(recent, previous) {
    const avg = averageMetrics(recent);
    const prev = previous.length ? averageMetrics(previous) : null;

    if (prev && avg.storm - prev.storm > 0.12) return "Storms are rising.";
    if (prev && prev.storm - avg.storm > 0.12) return "Storms are calming.";
    if (prev && avg.dayLength - prev.dayLength > 0.08) return "Days grow longer.";
    if (prev && avg.flora - prev.flora > 0.08) return "New regions emerge.";
    if (prev && avg.stability - prev.stability > 0.08) return "The planet stabilized.";

    if (avg.storm > 0.5) return "The atmosphere is restless.";
    if (avg.dayLength > 0.6) return "The days are brighter.";
    if (avg.flora > 0.35) return "Continents are waking.";
    if (avg.stability > 0.6) return "The planet is calmer.";
    return "The world shifted softly.";
  }

  function averageMetrics(logs) {
    const total = { storm: 0, dayLength: 0, flora: 0, stability: 0 };
    logs.forEach((log) => {
      total.storm += log.visualSnapshot?.storm ?? 0;
      total.dayLength += log.visualSnapshot?.dayLength ?? 0.5;
      total.flora += log.visualSnapshot?.flora ?? 0;
      total.stability += log.presence?.stability ?? 0;
    });
    const count = logs.length || 1;
    return {
      storm: total.storm / count,
      dayLength: total.dayLength / count,
      flora: total.flora / count,
      stability: total.stability / count,
    };
  }

  function getRecentLogs(logs, days) {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days + 1);
    return logs
      .map((log) => ({ ...log, dateObj: fromDateKey(log.date) }))
      .filter((log) => log.dateObj && log.dateObj >= cutoff)
      .sort((a, b) => b.dateObj - a.dateObj);
  }

  function getSortedLogs(logs) {
    return logs
      .map((log) => ({ ...log, dateObj: fromDateKey(log.date) }))
      .filter((log) => log.dateObj)
      .sort((a, b) => b.dateObj - a.dateObj);
  }

  function buildStateFromLog(log) {
    const world = getWorld();
    const fallback = world || {};
    const snapshot = log?.renderSnapshot;

    return {
      presence: {
        mood: snapshot?.presence?.mood ?? fallback.presence?.mood ?? "observing",
        tension: snapshot?.presence?.tension ?? fallback.presence?.tension ?? 0.05,
        entropy: snapshot?.presence?.entropy ?? fallback.presence?.entropy ?? 0.03,
        curiosity: snapshot?.presence?.curiosity ?? fallback.presence?.curiosity ?? 0.3,
      },
      innerState: {
        trust: snapshot?.innerState?.trust ?? fallback.innerState?.trust ?? 0.5,
        fear: snapshot?.innerState?.fear ?? fallback.innerState?.fear ?? 0.2,
        stability: snapshot?.innerState?.stability ?? fallback.innerState?.stability ?? 0.5,
      },
      identity: snapshot?.identity ?? fallback.identity ?? null,
      longMemory: snapshot?.longMemory ?? fallback.longMemory ?? {},
      midMemory: snapshot?.midMemory ?? fallback.midMemory ?? {},
      geography: snapshot?.geography ?? fallback.geography ?? {},
      daily: snapshot?.daily ?? fallback.daily ?? {},
      epochs: Array.isArray(snapshot?.epochs) ? snapshot.epochs : fallback.epochs ?? [],
    };
  }

  function interpolateState(a, b, t) {
    const mood = t < 0.5 ? a.presence.mood : b.presence.mood;
    return {
      presence: {
        mood,
        tension: lerp(a.presence.tension, b.presence.tension, t),
        entropy: lerp(a.presence.entropy, b.presence.entropy, t),
        curiosity: lerp(a.presence.curiosity, b.presence.curiosity, t),
      },
      innerState: {
        trust: lerp(a.innerState.trust, b.innerState.trust, t),
        fear: lerp(a.innerState.fear, b.innerState.fear, t),
        stability: lerp(a.innerState.stability, b.innerState.stability, t),
      },
      longMemory: interpolateMemory(a.longMemory, b.longMemory, t),
      midMemory: interpolateMemory(a.midMemory, b.midMemory, t),
      geography: {
        seedA: lerp(a.geography.seedA ?? 0.37, b.geography.seedA ?? 0.37, t),
        seedB: lerp(a.geography.seedB ?? 0.61, b.geography.seedB ?? 0.61, t),
      },
      daily: {
        trend: lerp(a.daily.trend ?? 0, b.daily.trend ?? 0, t),
        imprint: lerp(a.daily.imprint ?? 0, b.daily.imprint ?? 0, t),
        lastIntensity: lerp(a.daily.lastIntensity ?? 0, b.daily.lastIntensity ?? 0, t),
      },
      epochs: interpolateEpochs(a.epochs, b.epochs, t),
    };
  }

  function interpolateMemory(a, b, t) {
    return {
      conflict: lerp(a?.conflict ?? 0.35, b?.conflict ?? 0.35, t),
      stability: lerp(a?.stability ?? 0.5, b?.stability ?? 0.5, t),
      curiosity: lerp(a?.curiosity ?? 0.4, b?.curiosity ?? 0.4, t),
      sentiment: lerp(a?.sentiment ?? 0, b?.sentiment ?? 0, t),
    };
  }

  function interpolateEpochs(aEpochs, bEpochs, t) {
    const out = [];
    const max = Math.max(aEpochs?.length || 0, bEpochs?.length || 0, 2);
    for (let i = 0; i < max; i += 1) {
      const a = aEpochs?.[i];
      const b = bEpochs?.[i];
      const mixed = mixEpoch(a, b, t);
      if (mixed) out.push(mixed);
    }
    return out;
  }

  function mixEpoch(a, b, t) {
    if (!a && !b) return null;
    if (!a) return b;
    if (!b) return a;
    return {
      id: a.id || b.id,
      createdAt: t < 0.5 ? a.createdAt : b.createdAt,
      conflict: lerp(a.conflict ?? 0, b.conflict ?? 0, t),
      stability: lerp(a.stability ?? 0, b.stability ?? 0, t),
      curiosity: lerp(a.curiosity ?? 0, b.curiosity ?? 0, t),
      sentiment: lerp(a.sentiment ?? 0, b.sentiment ?? 0, t),
      seedA: lerp(a.seedA ?? 0.37, b.seedA ?? 0.37, t),
      seedB: lerp(a.seedB ?? 0.61, b.seedB ?? 0.61, t),
    };
  }

  function easeInOut(t) {
    return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  }

  function toDateKey(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function fromDateKey(key) {
    if (!key) return null;
    const parts = key.split("-");
    if (parts.length !== 3) return null;
    const year = Number(parts[0]);
    const month = Number(parts[1]);
    const day = Number(parts[2]);
    if (!year || !month || !day) return null;
    return new Date(year, month - 1, day);
  }

  function getWeekKey(date) {
    const temp = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const day = (temp.getDay() + 6) % 7;
    temp.setDate(temp.getDate() - day + 3);
    const weekYear = temp.getFullYear();
    const firstThursday = new Date(weekYear, 0, 4);
    const diff = temp - firstThursday;
    const weekNumber = Math.floor(diff / (7 * 24 * 60 * 60 * 1000)) + 1;
    return `${weekYear}-W${String(weekNumber).padStart(2, "0")}`;
  }

  function mixColor(a, b, t) {
    return [
      a[0] + (b[0] - a[0]) * t,
      a[1] + (b[1] - a[1]) * t,
      a[2] + (b[2] - a[2]) * t,
    ];
  }

  function drawPlanetGlyph(ctx, size, snapshot, seedKey, detailScale) {
    ctx.clearRect(0, 0, size, size);
    const center = size * 0.5;
    const radius = size * 0.38;

    const dayLength = clamp(snapshot?.dayLength ?? 0.5, 0, 1);
    const storm = clamp(snapshot?.storm ?? 0, 0, 1);
    const flora = clamp(snapshot?.flora ?? 0, 0, 1);

    const rand = seededRandom(seedKey || "aurelia");
    const lightAngle = rand() * Math.PI * 2;

    const base = mixColor([12, 20, 36], [80, 140, 200], dayLength);
    const deep = mixColor(base, [5, 8, 12], 0.6 + storm * 0.2);
    const bright = mixColor(base, [130, 190, 230], 0.5 + flora * 0.2);

    const lx = center + Math.cos(lightAngle) * radius * 0.4;
    const ly = center + Math.sin(lightAngle) * radius * 0.4;
    const gradient = ctx.createRadialGradient(lx, ly, radius * 0.15, center, center, radius);
    gradient.addColorStop(0, rgb(bright, 1));
    gradient.addColorStop(0.6, rgb(base, 1));
    gradient.addColorStop(1, rgb(deep, 1));

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(center, center, radius, 0, Math.PI * 2);
    ctx.fill();

    const shadowShift = (0.5 - dayLength) * 0.6;
    const shadowAngle = lightAngle + Math.PI + shadowShift;
    const sx = center + Math.cos(shadowAngle) * radius * 0.6;
    const sy = center + Math.sin(shadowAngle) * radius * 0.6;
    const shadow = ctx.createRadialGradient(sx, sy, radius * 0.2, center, center, radius * 1.1);
    shadow.addColorStop(0, "rgba(10, 12, 20, 0.12)");
    shadow.addColorStop(0.6, `rgba(8, 12, 18, ${0.45 + storm * 0.25})`);
    shadow.addColorStop(1, "rgba(3, 5, 8, 0.95)");

    ctx.fillStyle = shadow;
    ctx.beginPath();
    ctx.arc(center, center, radius, 0, Math.PI * 2);
    ctx.fill();

    const ringStart = lightAngle + Math.PI * 0.2;
    const ringArc = Math.PI * (0.8 + dayLength * 1.0);
    ctx.strokeStyle = `rgba(120, 190, 230, ${0.2 + dayLength * 0.45})`;
    ctx.lineWidth = Math.max(1, size * 0.04 * detailScale);
    ctx.beginPath();
    ctx.arc(center, center, radius * 1.08, ringStart, ringStart + ringArc);
    ctx.stroke();

    if (storm > 0.05) {
      const stormCount = Math.floor(1 + storm * 2 * detailScale);
      ctx.strokeStyle = `rgba(160, 180, 210, ${0.12 + storm * 0.35})`;
      ctx.lineWidth = Math.max(1, size * 0.02 * detailScale);
      for (let i = 0; i < stormCount; i += 1) {
        const arcLen = Math.PI * (0.15 + rand() * 0.4);
        const start = lightAngle + rand() * Math.PI * 2;
        ctx.beginPath();
        ctx.arc(center, center, radius * (0.92 + rand() * 0.25), start, start + arcLen);
        ctx.stroke();
      }
    }

    if (flora > 0.05) {
      const dotCount = Math.floor((1 + flora * 6) * detailScale);
      ctx.fillStyle = `rgba(90, 150, 120, ${0.2 + flora * 0.5})`;
      for (let i = 0; i < dotCount; i += 1) {
        const angle = rand() * Math.PI * 2;
        const dist = radius * (0.15 + rand() * 0.65);
        const x = center + Math.cos(angle) * dist;
        const y = center + Math.sin(angle) * dist;
        const dotSize = Math.max(1, size * 0.02 * (0.5 + rand() * 0.8));
        ctx.fillRect(x, y, dotSize, dotSize);
      }
    }

    if (detailScale > 1) {
      ctx.strokeStyle = `rgba(140, 200, 235, ${0.12 + flora * 0.2})`;
      ctx.lineWidth = Math.max(1, size * 0.015);
      ctx.beginPath();
      ctx.arc(center, center, radius * 1.15, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  function resolveUserIdentity() {
    const fromWindow = window.AURELIA_USER || window.aureliaUser;
    let userId = null;
    let planetSeed = null;

    if (fromWindow && typeof fromWindow === "object") {
      userId = fromWindow.id || fromWindow.userId || null;
      planetSeed = fromWindow.planetSeed || null;
    }

    if (!userId && window.AURELIA_USER_ID) {
      userId = window.AURELIA_USER_ID;
    }
    if (!planetSeed && window.AURELIA_PLANET_SEED) {
      planetSeed = window.AURELIA_PLANET_SEED;
    }

    const metaUser = document.querySelector('meta[name="aurelia-user-id"]');
    const metaSeed = document.querySelector('meta[name="aurelia-planet-seed"]');
    if (!userId && metaUser?.content) {
      userId = metaUser.content;
    }
    if (!planetSeed && metaSeed?.content) {
      planetSeed = metaSeed.content;
    }

    const root = document.documentElement;
    if (!userId && root?.dataset?.userId) {
      userId = root.dataset.userId;
    }
    if (!planetSeed && root?.dataset?.planetSeed) {
      planetSeed = root.dataset.planetSeed;
    }

    return {
      userId: userId || "local",
      planetSeed: planetSeed || null,
    };
  }

  function rgb(color, alpha) {
    return `rgba(${Math.round(color[0])}, ${Math.round(color[1])}, ${Math.round(color[2])}, ${alpha})`;
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

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }
});
