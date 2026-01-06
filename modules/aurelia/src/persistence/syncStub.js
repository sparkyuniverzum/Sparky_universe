// src/persistence/syncStub.js

function getBasePath() {
  const root = document.documentElement;
  const fromData = root?.dataset?.basePath || "";
  if (fromData) return fromData;
  const fallback = window.location?.pathname || "";
  return fallback.endsWith("/") ? fallback.slice(0, -1) : fallback;
}

function buildSafeSnapshot(aurelia) {
  if (!aurelia) return null;

  const logs = Object.values(aurelia.dailyLogs || {});
  let lastLog = null;
  for (const log of logs) {
    if (!lastLog || String(log.date || "") > String(lastLog.date || "")) {
      lastLog = log;
    }
  }

  const lastEvent = Array.isArray(aurelia.memory) && aurelia.memory.length
    ? aurelia.memory[aurelia.memory.length - 1]
    : null;

  const eventType = lastEvent?.type ? String(lastEvent.type) : "sync";

  return {
    event_type: eventType,
    user_id: aurelia.meta?.userId || null,
    planet_seed: aurelia.identity?.seed || null,
    schema_version: 1,
    snapshot: {
      meta: {
        id: aurelia.meta?.id || null,
        version: aurelia.meta?.version || null,
        created_at: aurelia.meta?.createdAt || null,
        updated_at: aurelia.meta?.lastUpdatedAt || null,
      },
      identity: {
        seedA: aurelia.identity?.seedA ?? null,
        seedB: aurelia.identity?.seedB ?? null,
        paletteBias: aurelia.identity?.paletteBias ?? null,
        ringTilt: aurelia.identity?.ringTilt ?? null,
        cloudSeed: aurelia.identity?.cloudSeed ?? null,
      },
      presence: {
        mood: aurelia.presence?.mood || null,
        awareness: aurelia.presence?.awareness ?? null,
        tension: aurelia.presence?.tension ?? null,
        entropy: aurelia.presence?.entropy ?? null,
        curiosity: aurelia.presence?.curiosity ?? null,
      },
      inner_state: {
        trust: aurelia.innerState?.trust ?? null,
        fear: aurelia.innerState?.fear ?? null,
        stability: aurelia.innerState?.stability ?? null,
        curiosity: aurelia.innerState?.curiosity ?? null,
      },
      long_memory: {
        conflict: aurelia.longMemory?.conflict ?? null,
        stability: aurelia.longMemory?.stability ?? null,
        curiosity: aurelia.longMemory?.curiosity ?? null,
        sentiment: aurelia.longMemory?.sentiment ?? null,
      },
      mid_memory: {
        conflict: aurelia.midMemory?.conflict ?? null,
        stability: aurelia.midMemory?.stability ?? null,
        curiosity: aurelia.midMemory?.curiosity ?? null,
        sentiment: aurelia.midMemory?.sentiment ?? null,
      },
      daily: {
        lastQuestionDate: aurelia.daily?.lastQuestionDate || null,
        trend: aurelia.daily?.trend ?? null,
        imprint: aurelia.daily?.imprint ?? null,
        lastIntensity: aurelia.daily?.lastIntensity ?? null,
        lastImprintAt: aurelia.daily?.lastImprintAt ?? null,
        lastSummaryWeek: aurelia.daily?.lastSummaryWeek || null,
      },
      geography: {
        seedA: aurelia.geography?.seedA ?? null,
        seedB: aurelia.geography?.seedB ?? null,
      },
    },
    activity: {
      logs_count: logs.length,
      last_log: buildSafeLogSummary(lastLog),
      last_event: buildSafeEventSummary(lastEvent),
      event_count: Array.isArray(aurelia.memory) ? aurelia.memory.length : 0,
    },
  };
}

function buildSafeLogSummary(log) {
  if (!log) return null;
  return {
    date: log.date || null,
    imprint_delta: typeof log.imprintDelta === "number" ? log.imprintDelta : null,
    visual_snapshot: log.visualSnapshot
      ? {
          dayLength: log.visualSnapshot.dayLength ?? null,
          storm: log.visualSnapshot.storm ?? null,
          flora: log.visualSnapshot.flora ?? null,
        }
      : null,
    signals: log.signals
      ? {
          sentiment: log.signals.sentiment ?? null,
          intensity: log.signals.intensity ?? null,
          themeWeight: log.signals.themeWeight ?? null,
        }
      : null,
  };
}

function buildSafeEventSummary(event) {
  if (!event) return null;
  const summary = {
    type: event.type || null,
    timestamp: event.timestamp || null,
  };

  if (event.type === "journal") {
    const text = event.payload?.text;
    summary.text_length = typeof text === "string" ? text.length : 0;
    summary.signals = event.payload?.signals || null;
  }

  if (event.type === "daily_answer") {
    summary.is_positive = !!event.payload?.isPositive;
    summary.trend = event.payload?.trend ?? null;
  }

  if (event.type === "reaction" || event.type === "major_shift") {
    summary.variant = event.payload?.type || null;
  }

  return summary;
}

export async function syncToCloud(aurelia) {
  const payload = buildSafeSnapshot(aurelia);
  if (!payload) return;

  const basePath = getBasePath();
  const url = `${basePath}/api/log`;

  try {
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    });
  } catch (error) {
    // Ignore sync failures.
  }
}
