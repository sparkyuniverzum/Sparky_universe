% Planet Standard (Expanded)

This document defines the unified standard for Sparky planets.
Standard version: 1.0 (frozen). Changes require a new version.

## 1) Planet principles
- Standalone, situation-first tools (not orchestration).
- No ads, no accounts, no history, no data storage.
- Optional monetization only after a result and never blocking.
- No flow links to other modules.

## 2) Planet layout
- modules/<name>/
  - module.yaml
  - __init__.py
  - core/
    - __init__.py
    - <logic>.py
  - tool/
    - app.py
    - templates/
      - index.html
  - story.md

## 3) module.yaml contract
Required:
- name: snake_case (unique, used as package name)
- title: human readable name
- version: semver
- description: one line
- public: true/false
- category: "Planets"
- entrypoints.api: "modules.<name>.tool.app:app"
- mount: URL path (recommended prefix "/planet/")
- standard_version: "1.0"

Recommended:
- status: alpha | beta | stable
- priority: P0 | P1 | P2
- owner: responsible person or team

## 4) UI contract
- Template extends "planet_base.html".
- UI focuses on intent selection, simple inputs, and one primary result.
- No ads, no flow sections, no extra navigation.

## 5) Planet palette (v1.0)
Use the shared variables from `planet_base.html`:
- --planet-bg: #f6f2ea
- --planet-bg-accent: #e5f0f3
- --planet-card: #ffffff
- --planet-text: #1e1f23
- --planet-muted: #6b6f76
- --planet-accent: #1f8a70
- --planet-accent-dark: #146654
- --planet-border: rgba(30, 31, 35, 0.12)

## 6) Telemetry and privacy
- Aggregate metrics only (page views and action counts).
- Do not store raw inputs in telemetry payloads.

## 7) Quality bars
- Validate numeric inputs, handle empty states.
- Return 400 with {"error": "..."} for validation issues.
- Keep core logic independent and deterministic.
