% Module Standard (Expanded)

This document defines the unified standard for every Sparky module.

## 1) Module layout
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

## 2) module.yaml contract
Required:
- name: snake_case (unique, used as package name)
- title: human readable name
- version: semver
- description: one line
- public: true/false
- category: one of the existing categories (or "Other")
- entrypoints.api: "modules.<name>.tool.app:app"
- mount: URL path (starts with "/")

Recommended:
- slug: kebab-case (default from name)
- flow_label: short label for flow cards
- flows.after_success: list of flow targets

## 3) API contract
- GET / returns HTML UI (template)
- POST /<action> returns JSON
- Validation errors return 400 + {"error": "..."}
- Server errors return 500 + {"error": "..." } (catch and normalize)
- Keep heavy logic in core/ and call from tool/app.py

## 4) UI contract
- Template extends "module_base.html"
- Form + Result sections always present
- JS uses fetch(), handles errors, shows result and flow links
- "Open API docs" link to /docs

## 5) Ads + flows
In tool/app.py:
- attach_ads_globals(templates)
- resolve_flow_links("<name>", base_url=SPARKY_FLOW_BASE_URL)

In index.html:
- {% from "partials/ads.html" import ad_block %}
- {% from "partials/flow.html" import flow_section %}

## 6) Telemetry and privacy
- Do not store raw input in telemetry payloads
- Only include counts/lengths/boolean flags
- Rely on server middleware for default events

## 7) Quality bars
- Handle None/empty input
- Validate numeric inputs, regex compile errors
- Avoid external network calls in core
- Keep response time under ~500ms for normal inputs

## 8) Naming and mounts
- module name: snake_case
- URL mount: /<category>/<slug> when possible
- Avoid collisions with existing mounts
