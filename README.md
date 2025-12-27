# Sparky Universe

## Product statement
Sparky Universe is a network of tiny, standalone utilities ("zrnka") that each solve one job fast. A single module is small on purpose; the value compounds when many modules are discoverable, connected, and monetized with lightweight ad/affiliate slots. The goal is high-volume, low-friction usefulness that scales through aggregation and flows.

## Zrnko standard
- One purpose, one page, no account required.
- Works alone, but exposes clear "what next" links (flows).
- UI includes light ad/affiliate slots without blocking the core task.
- Logic lives in `core/`, the web layer stays thin.

## Module contract (required)
Each module must provide:
- `modules/<name>/module.yaml` with `name`, `title`, `version`, `description`, `public`, `entrypoints.api`, and `mount`.
- `modules/<name>/tool/app.py` exporting a FastAPI `app`.
- `modules/<name>/tool/templates/index.html` as the module UI.
- `modules/<name>/core/` with the business logic.

## Optional fields in module.yaml
- `flow_label`: alternative label shown in flow links.
- `flows`: next-step links shown after success.

Example:
```yaml
flows:
  after_success:
    - target: qrverify
      label: Verify this QR
```

## UI standard (recommended)
- Title + one-line description.
- Ad layout (top + bottom) around the form, non-intrusive.
- "Continue in Sparky Universe" section fed by `resolve_flow_links(...)`.
- Link to `/docs` for API visibility.

## API standard
- `GET /` returns the HTML UI.
- `POST /<action>` performs the work and returns JSON or a file.
- Keep heavy lifting in `core/`, keep request handling in `tool/app.py`.

## Quickstart for a new zrnko
1. Create `modules/<name>/`.
2. Copy the template from `modules/module.yaml`.
3. Implement `tool/app.py` and `tool/templates/index.html`.
4. Add `core/` functions and wire them into the app.
5. Add `flows` in `module.yaml` to connect the loop.

## Generator
Use the scaffold script for a ready-to-run module:
```bash
python scripts/new_module.py qr_batch --title "QR Batch" --description "Batch-generate QR codes."
```

## Run all modules (default)
```bash
bash scripts/run_module.sh
```

## Run a single module (same pattern as QR Forge)
```bash
SPARKY_MODULE=qrforge bash scripts/run_module.sh
```
Set `SPARKY_MODULE` to `qrverify`, `qr_batch`, or any new module name.

## Shared UI templates
Reusable partials live in `universe/templates/partials/`:
- `ads.html` provides the ad slot markup.
- `flow.html` provides the "Continue in Sparky Universe" section.

Base layout lives in `universe/templates/module_base.html` and should be used by module pages via `{% extends "module_base.html" %}`.

Module templates can import them with:
```html
{% from "partials/ads.html" import ad_block %}
{% from "partials/flow.html" import flow_section %}
```
