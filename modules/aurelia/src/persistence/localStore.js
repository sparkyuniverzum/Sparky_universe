// src/persistence/localStore.js

const KEY_PREFIX = "aurelia_core_v1";
const LEGACY_KEY = "aurelia_core_v1";

function buildKey(userId) {
  const safeId = userId ? String(userId) : "local";
  return `${KEY_PREFIX}_${safeId}`;
}

export function saveLocal(aurelia, userId) {
  localStorage.setItem(buildKey(userId), JSON.stringify(aurelia));
}

export function loadLocal(userId) {
  const key = buildKey(userId);
  const raw = localStorage.getItem(key);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function loadLegacyLocal() {
  const raw = localStorage.getItem(LEGACY_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
