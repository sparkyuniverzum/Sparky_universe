# Aurelia Behavior Spec v1 (lightweight)

Purpose: define expected behavior of Aurelia as an entity driven by journal text.
Scope: behavior only (no UI/QA formalities). Inputs are journal text, outputs are state shift + visuals.

Implementation mapping:
- Journal text -> `analyzeText()` in `src/core/textAnalysis.js`
- Decay + state update -> `applyJournalEntry()` in `src/world.js`
- Mood derivation -> `deriveMood()` in `src/world.js`
- Visual mapping -> WebGL uniforms in `src/visual/glRenderer.js`

General rules:
- Tokens are normalized (diacritics removed).
- Negation flips only the next token.
- State values stay in 0..1 and decay toward baseline on each entry.
- Mood priority: hostile > disturbed > curious > calm > observing.
- No text response; only visual change.

Case 01: Empty / whitespace
Input: "   "
Signals: none (entry not submitted)
State: no change
Mood: no change
Visual: no change

Case 02: Neutral routine
Input: "Dnes je to ok, rutina."
Signals: sentiment slightly +, intensity low, theme -> stability
State: trust up, stability up, tension/entropy near baseline
Mood: observing
Visual: calmer surface, cleaner atmosphere

Case 03: Calm + safety (positive)
Input: "Citim klid a bezpeci, jsem vdecny."
Signals: sentiment +, intensity medium, theme -> stability
State: trust up, stability up, tension down (via decay)
Mood: calm after repetition
Visual: brighter atmosphere, calmer surface

Case 04: Pure curiosity
Input: "Chci objevovat nove veci, proc se to deje?"
Signals: sentiment ~0, intensity medium, theme -> curiosity
State: presence.curiosity up, innerState.curiosity up, awareness up
Mood: curious (if curiosity > 0.6)
Visual: livelier colors, faster/softer animation

Case 05: Conflict + negative pressure
Input: "Bojim se, je to chaos, tlak a stres."
Signals: sentiment -, intensity high, theme -> conflict
State: tension up, entropy up, fear up, stability down
Mood: disturbed (hostile after accumulation)
Visual: darker surface, stronger deformation, visible ring

Case 06: Negation (next token only)
Input: "ne klid, ne bezpeci"
Signals: sentiment -, intensity low-medium
State: trust down, fear up, stability down
Mood: observing -> disturbed with repetition
Visual: darker tone + harder contrast
Note: "nejsem v bezpeci" does NOT negate "bezpeci" (one-token rule).

Case 07: Mixed entry
Input: "Dnes good, ale mam strach."
Signals: mixed, intensity medium
State: trust up and fear up, tension slightly up
Mood: observing
Visual: subtle contrast shift, darker night side

Case 08: Long entry (high intensity)
Input: long text with multiple keywords
Signals: intensity high (length factor)
State: stronger delta across relevant axes
Mood: disturbed/curious depending on themes
Visual: stronger noise + atmosphere

Case 09: Curiosity + fear
Input: "Mam strach, ale chci zkoumat a objevovat."
Signals: sentiment -, intensity medium, themes mix (conflict + curiosity)
State: fear up + curiosity up, tension up
Mood: disturbed overrides curious when tension/entropy high
Visual: darker but with livelier accents

Case 10: Stability vs conflict (balanced)
Input: "Je tu klid, ale i konflikt."
Signals: theme stability + conflict, similar weights
State: stability shift small, entropy moderate
Mood: observing
Visual: mild tension haze, no big shifts

Case 11: Repeated small positives
Input: short positive entries repeated
Signals: low intensity, stable positive sentiment
State: trust slowly up, tension decays down
Mood: calm over time
Visual: clean glow, stable surface

Case 12: Strong negative accumulation
Input: multiple high-intensity negative entries
Signals: sentiment -, intensity high, conflict high
State: fear/tension/entropy rise strongly
Mood: hostile
Visual: very dark planet, aggressive ring, hard shadows
