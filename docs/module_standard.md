% Module Standard (Expanded)

This document defines the unified standard for every Sparky module.
Standard version: 1.0 (frozen). Changes require a new version.

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
- standard_version: "1.0"

Optional (v1.0 extensions):
- tags: list of short labels for discovery
- status: alpha | beta | stable
- priority: P0 | P1 | P2
- owner: responsible person or team
- seo_title, seo_description, canonical
- og_image or og_image_key
- input_spec: freeform input schema or shape (YAML/JSON)
- output_spec: freeform output schema or shape (YAML/JSON)
- sample_input, sample_output (string or YAML/JSON)
- privacy.no_raw_inputs: true/false

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

## 9) Example extensions (v1.0)
```yaml
standard_version: "1.0"
tags: [csv, clean, normalize]
status: beta
priority: P2
owner: "growth"
seo_title: "CSV Cleaner"
seo_description: "Clean CSV files by trimming and removing empty rows."
canonical: "https://sparky-universe.com/csv/clean"
og_image: "/brand/og/csv-clean.png"
input_spec:
  type: file
  format: csv
output_spec:
  format: csv
sample_input: "name,price\\nWidget,10\\n"
sample_output: "name,price\\nWidget,10\\n"
privacy:
  no_raw_inputs: true
```
