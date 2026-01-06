// src/core/reactions.js

import { addEvent } from "./eventLog.js";

export function evaluateReaction(aurelia) {
  const p = aurelia.presence;
  const t = aurelia.thresholds;
  const l = aurelia.laws;
  const perception = aurelia.perception;

  // vnímaný tlak světa
  const pressure =
    p.awareness * 0.4 +
    p.tension * 0.4 +
    p.entropy * 0.2 +
    perception.interferenceLevel * 0.6;

  const chance = Math.random();

  // jemná reakce – častá, kultivovaná
  if (pressure > t.notice && chance > 0.3) {
    triggerNoticeReaction(aurelia);
  }

  // micro reakce – citlivá, ale ne dramatická
  if (pressure > t.micro && chance > 0.5) {
    triggerMicroReaction(aurelia);
    return "micro";
  }

  // major shift – vzácný, ale silný
  if (pressure > t.major && chance > 0.75) {
    triggerMajorShift(aurelia);
    return "major";
  }

  return "none";
}

function triggerNoticeReaction(aurelia) {
  aurelia.presence.mood = "observing";
  aurelia.perception.patternConfidence += 0.05;

  addEvent(aurelia, "reaction", {
    type: "notice",
    message: "Aurelia noticed a pattern",
  });
}

function triggerMicroReaction(aurelia) {
  aurelia.presence.mood = "curious";
  aurelia.laws.distortion += 0.03;
  aurelia.presence.lastReactionAt = Date.now();

  addEvent(aurelia, "reaction", {
    type: "micro",
    message: "Aurelia subtly adjusted reality",
    distortion: aurelia.laws.distortion,
  });
}

function triggerMajorShift(aurelia) {
  aurelia.presence.mood = "hostile";
  aurelia.laws.stability -= 0.15;
  aurelia.laws.permeability += 0.15;
  aurelia.laws.distortion += 0.25;
  aurelia.presence.lastMajorShiftAt = Date.now();

  addEvent(aurelia, "major_shift", {
    message: "Aurelia initiated a reality shift",
    laws: { ...aurelia.laws },
  });
}

