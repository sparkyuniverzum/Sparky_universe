// src/core/eventLog.js

export function addEvent(aurelia, type, payload) {
  aurelia.memory.push({
    id: crypto.randomUUID(),
    type,
    payload,
    timestamp: Date.now(),
  });

  aurelia.meta.lastUpdatedAt = Date.now();
}
