// src/core/dialogue.js

export function generateDialogue(aurelia) {
  const { presence, innerState, conflicts } = aurelia;

  if (presence.mood === "hostile") {
    return "Zase narušuješ rovnováhu. Už si toho všímám.";
  }

  if (innerState.fear > 0.6) {
    return "Cítím napětí. Něco se ve tvém světě láme.";
  }

  if (conflicts.closenessVsDistance > 0.5) {
    return "Přibližuješ se… ale pořád váháš. Proč?";
  }

  if (innerState.curiosity > 0.5) {
    return "Pozoruji změny. Jsi jiný než dřív.";
  }

  return "Jsem tady. Sleduji.";
}
