% Station Standard (Brief)

This document defines the unified standard for Sparky stations.
Standard version: 1.0 (frozen). Changes require a new version.

## 1) Station principles
- Public, static guidance (no AI, no accounts, no history).
- Plain, verified steps. No story. No fluff.
- Optional monetization only after the procedure (checklist, alerts).
- Removable without breaking modules, planets, or satellites.

## 2) Data contract
Required fields:
- id, slug, title, summary
- country, region
- status, last_verified (YYYY-MM-DD)
- sections (ordered)
- sources (official links)

Optional:
- pro (list of paid extras)

## 3) Section order (v1)
1) What you're solving
2) What you need
3) Where to go / what to open
4) What to fill
5) How much it costs
6) Common mistakes
7) Official sources
8) Last verified

## 4) UI contract
- Same layout across stations.
- Minimal cards and clear lists.
- No ads inside station content.

## 5) SEO / routing
- /stations (index)
- /stations/{slug} (detail)
