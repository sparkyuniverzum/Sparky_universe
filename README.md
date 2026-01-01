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
- `modules/<name>/module.yaml` with `name`, `title`, `version`, `description`, `public`, `category`, `entrypoints.api`, and `mount`.
- `modules/<name>/tool/app.py` exporting a FastAPI `app`.
- `modules/<name>/tool/templates/index.html` as the module UI.
- `modules/<name>/core/` with the business logic.

Expanded standard: `docs/module_standard.md`.

Internal shared modules (like `sparky_ui`) are `public: false` and can omit entrypoints and runtime code.

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

## Flow fallback (optional)
If a module has no `flows.after_success`, the UI can show fallback links from the same
category.

Configure with:
- `SPARKY_FLOW_FALLBACK=on|off` (default on)
- `SPARKY_FLOW_FALLBACK_LIMIT=3`

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
Reusable UI lives in the internal module `modules/sparky_ui` (public: false):
- `modules/sparky_ui/tool/templates/partials/ads.html`
- `modules/sparky_ui/tool/templates/partials/flow.html`
- `modules/sparky_ui/tool/templates/module_base.html`

Module pages should extend `{% extends "module_base.html" %}`.

Module templates can import them with:
```html
{% from "partials/ads.html" import ad_block %}
{% from "partials/flow.html" import flow_section %}
```

## Telemetry (optional)
Server-side telemetry captures aggregate metrics only (no raw input).

Enable with:
```bash
export SPARKY_TELEMETRY=on
export SPARKY_DB_DSN="postgresql://..."
```

Optional settings:
- `SPARKY_TELEMETRY_AUTO_MIGRATE=on` (default on)
- `SPARKY_TENANT` to tag events per domain
- `SPARKY_TRUST_PROXY=on` to honor `X-Forwarded-For`
- `SPARKY_TELEMETRY_SALT` for hashing user agent/IP

## Ads (optional)
Enable ad/affiliate slots in module templates.

```bash
export SPARKY_ADS=on
export SPARKY_ADS_INLINE=on
export SPARKY_ADS_FOOTER=on
export SPARKY_ADS_PREVIEW=on
```

## Admin panel (optional)
Private control panel at `/admin` with Basic Auth and module enable/disable overrides.

```bash
export SPARKY_ADMIN_USER="admin"
export SPARKY_ADMIN_PASSWORD="change-me"
export SPARKY_ADMIN_DB_DSN="postgresql://..."
```
If `SPARKY_ADMIN_DB_DSN` is not set, it falls back to `SPARKY_DB_DSN`/`DATABASE_URL`
and stores overrides in memory only (not persistent).

Retention cleanup (default 90 days):
```bash
python scripts/telemetry_cleanup.py
```
