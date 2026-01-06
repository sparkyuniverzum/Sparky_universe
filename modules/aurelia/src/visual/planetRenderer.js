// src/visual/planetRenderer.js

export function renderPlanet(aurelia, t = 0) {
  if (!aurelia) return;

  const canvas = document.getElementById("worldCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const { presence, innerState, conflicts } = aurelia;

  // Background
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawSpace(ctx, canvas, t, presence);

  const baseRadius = Math.min(canvas.width, canvas.height) * 0.18;

  // Emotions → parameters
  const tension = clamp(presence.tension, 0, 1);
  const fear = clamp(innerState.fear, 0, 1);
  const trust = clamp(innerState.trust ?? 0.5, 0, 1);
  const curiosity = clamp(
    typeof innerState.curiosity === "number" ? innerState.curiosity : presence.curiosity,
    0,
    1
  );

  // LIVING MOTION TUNED
  const driftX = Math.sin(t * 0.3) * (4 + curiosity * 10);
  const driftY = Math.cos(t * 0.25) * (4 + trust * 10);

  const cx = canvas.width / 2 + driftX;
  const cy = canvas.height / 2 + driftY;

  const breathe = Math.sin(t * (0.6 + trust * 0.8)) * (8 + trust * 18);
  const pulse = Math.sin(t * (1.8 + tension * 3.5)) * (tension * 22);

  const radius = baseRadius + breathe + pulse;


  // Mood color
  const moodColorMap = {
    dormant: "#5c6b73",
    observing: "#4fa3d1",
    curious: "#5dd39e",
    disturbed: "#f2b705",
    hostile: "#e63946",
  };
  const baseColor = moodColorMap[presence.mood] || "#ffffff";

  // Atmosphere intensity:
  // fear -> darker fog
  // trust -> clearer glow
  const fog = fear * 0.65;
  const glow = trust * 0.55 + curiosity * 0.25;

  // Atmosphere layer
  drawAtmosphere(ctx, cx, cy, radius, baseColor, glow, fog);

  // Planet body (shaded gradient)
  drawPlanet(ctx, cx, cy, radius, baseColor, tension, fear);

  // Surface “veins” (conflict)
  drawVeins(ctx, cx, cy, radius, conflicts.orderVsChaos, t);

  // Subtle ring when hostile/disturbed
  if (presence.mood === "disturbed" || presence.mood === "hostile") {
    drawWarningRing(ctx, cx, cy, radius, presence.mood, t, tension);
  }
}

/* =========================
   LAYERS
========================= */

function drawSpace(ctx, canvas, t, presence) {
  // soft vignette
  const g = ctx.createRadialGradient(
    canvas.width * 0.5,
    canvas.height * 0.45,
    Math.min(canvas.width, canvas.height) * 0.1,
    canvas.width * 0.5,
    canvas.height * 0.45,
    Math.min(canvas.width, canvas.height) * 0.8
  );
  g.addColorStop(0, "rgba(20, 28, 44, 1)");
  g.addColorStop(1, "rgba(8, 10, 16, 1)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // stars density slightly higher when "observing/curious"
  const moodBoost = presence.mood === "curious" ? 1.2 : presence.mood === "observing" ? 1.1 : 1.0;
  const count = Math.floor(90 * moodBoost);

  // pseudo-random stable stars based on canvas size
  const seed = (canvas.width * 73856093) ^ (canvas.height * 19349663);
  for (let i = 0; i < count; i++) {
    const x = hash01(seed + i * 1013) * canvas.width;
    const y = hash01(seed + i * 2027) * canvas.height * 0.85;

    const twinkle = 0.35 + 0.65 * Math.abs(Math.sin(t * 0.7 + i));
    const r = 0.6 + hash01(seed + i * 3037) * 1.4;

    ctx.fillStyle = `rgba(180, 210, 255, ${0.15 * twinkle})`;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawAtmosphere(ctx, cx, cy, r, baseColor, glow, fog) {
  // outer glow
  const outer = ctx.createRadialGradient(cx, cy, r * 0.7, cx, cy, r * (1.35 + glow));
  outer.addColorStop(0, alphaColor(baseColor, 0.25 + glow * 0.25));
  outer.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = outer;
  ctx.beginPath();
  ctx.arc(cx, cy, r * (1.4 + glow), 0, Math.PI * 2);
  ctx.fill();

  // fog overlay (fear)
  if (fog > 0.02) {
    const fogG = ctx.createRadialGradient(cx, cy, r * 0.6, cx, cy, r * (1.6 + fog));
    fogG.addColorStop(0, `rgba(0,0,0,${0.05 + fog * 0.15})`);
    fogG.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = fogG;
    ctx.beginPath();
    ctx.arc(cx, cy, r * (1.7 + fog), 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawPlanet(ctx, cx, cy, r, baseColor, tension, fear) {
  // light source from top-left
  const lx = cx - r * 0.35;
  const ly = cy - r * 0.35;

  const g = ctx.createRadialGradient(lx, ly, r * 0.2, cx, cy, r * 1.05);
  g.addColorStop(0, alphaColor("#ffffff", 0.18 + (1 - fear) * 0.12));
  g.addColorStop(0.25, alphaColor(baseColor, 0.95));
  g.addColorStop(1, alphaColor("#000000", 0.55 + fear * 0.25));

  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();

  // subtle “tension shading”
  if (tension > 0.05) {
    ctx.strokeStyle = `rgba(255,255,255,${0.08 * tension})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, r * (1.02 + tension * 0.02), 0, Math.PI * 2);
    ctx.stroke();
  }
}

function drawVeins(ctx, cx, cy, r, orderVsChaos = 0, t = 0) {
  const chaos = clamp(orderVsChaos, -1, 1);
  const intensity = Math.max(0, chaos); // only show for chaos positive
  if (intensity < 0.05) return;

  const lines = Math.floor(3 + intensity * 10);
  ctx.lineWidth = 1;

  for (let i = 0; i < lines; i++) {
    const a = (i / lines) * Math.PI * 2 + Math.sin(t * 0.6 + i) * 0.1;
    const len = r * (0.45 + intensity * 0.4);
    const wobble = Math.sin(t * 1.2 + i * 4) * (2 + intensity * 4);

    ctx.strokeStyle = `rgba(0,0,0,${0.08 + intensity * 0.18})`;

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(a) * len + wobble, cy + Math.sin(a) * len - wobble);
    ctx.stroke();
  }
}

function drawWarningRing(ctx, cx, cy, r, mood, t, tension) {
  const amp = mood === "hostile" ? 0.35 : 0.2;
  const a = 0.12 + Math.abs(Math.sin(t * 2.2)) * amp + tension * 0.08;

  ctx.strokeStyle = mood === "hostile"
    ? `rgba(230,57,70,${a})`
    : `rgba(242,183,5,${a})`;

  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, r * 1.12, 0, Math.PI * 2);
  ctx.stroke();
}

/* =========================
   UTILS
========================= */

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function alphaColor(hex, a) {
  // hex "#rrggbb"
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${clamp(a, 0, 1)})`;
}

function hash01(n) {
  // cheap deterministic 0..1
  const x = Math.sin(n) * 10000;
  return x - Math.floor(x);
}
