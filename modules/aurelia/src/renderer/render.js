// ===== HVĚZDY (JEDNOU) =====
const stars = Array.from({ length: 250 }, () => ({
  x: Math.random(),
  y: Math.random(),
  r: Math.random() * 1.5
}));

export function render(ctx, world) {
  const w = ctx.canvas.width;
  const h = ctx.canvas.height;

  // ===== POZADÍ =====
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, w, h);

  // ===== HVĚZDY =====
  ctx.fillStyle = "white";
  ctx.globalAlpha = 0.6;
  stars.forEach(s => {
    ctx.fillRect(s.x * w, s.y * h, s.r, s.r);
  });
  ctx.globalAlpha = 1;

  const cx = w / 2;
  const cy = h / 2;
  const r = world.radius;

  // ===== TĚLO PLANETY =====
  const lx = Math.cos(world.angle) * r * 0.4;
  const ly = Math.sin(world.angle) * r * 0.4;

  const surface = ctx.createRadialGradient(
    cx + lx, cy + ly, r * 0.2,
    cx, cy, r
  );

  surface.addColorStop(0, "#b5f2e6");
  surface.addColorStop(1, "#163a47");

  ctx.fillStyle = surface;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();

  // ===== DEN / NOC (TERMINÁTOR) =====
  ctx.save();
  ctx.globalCompositeOperation = "multiply";

  ctx.translate(cx, cy);
  ctx.rotate(world.angle);

  const shadow = ctx.createLinearGradient(-r, 0, r, 0);
  shadow.addColorStop(0, "rgba(0,0,0,0.8)");
  shadow.addColorStop(0.5, "rgba(0,0,0,0)");
  shadow.addColorStop(1, "rgba(0,0,0,0.9)");

  ctx.fillStyle = shadow;
  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
  ctx.globalCompositeOperation = "source-over";

  // ===== ATMOSFÉRA =====
  ctx.save();
  ctx.globalCompositeOperation = "lighter";

  const atmo = ctx.createRadialGradient(cx, cy, r, cx, cy, r * 1.15);
  atmo.addColorStop(0, "rgba(120,200,255,0.05)");
  atmo.addColorStop(1, "rgba(120,200,255,0.35)");

  ctx.fillStyle = atmo;
  ctx.beginPath();
  ctx.arc(cx, cy, r * 1.1, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();

  // ===== POPISEK =====
  ctx.fillStyle = "#aaa";
  ctx.font = "13px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(
    "Aurelia · živý svět · den / noc · atmosféra",
    cx,
    h - 24
  );
}



