% Satellite Standard (Brief)

This document defines the unified standard for Sparky satellites.
Standard version: 1.0 (frozen). Changes require a new version.

## 1) Satellite principles
- Public, standalone data sources (not tools, not orchestration).
- No ads, no accounts, no user data storage.
- Optional monetization only outside the data flow.
- Removable without breaking modules or planets.

## 2) Files and registry
- universe/satellite_<name>.py (data collection + storage)
- universe/templates/satellite_<name>.html (public page)
- universe/satellites.py (registry entry)
- universe/engine.py (public routes)

## 3) Payload contract
Snapshot must be JSON with:
- satellite: unique id string
- source: canonical source domain
- collected_at: ISO timestamp or date
- period: "daily" | "hourly" | "weekly" | "monthly"
- data: list of objects with at least { key, type }

Optional:
- unit, value, currency, valid_from, valid_to, rank, meta

## 4) Storage contract
- Store snapshots in Postgres table: sparky_satellite_snapshots
- Keep one row per snapshot; latest fetch returns most recent payload.

## 5) Public interface
- Public page: /satellites/<slug>
- Public API: /satellites/<slug>/latest (JSON)
- Refresh endpoint (optional): POST /satellites/<slug>/refresh
  - Must require token header x-satellite-token

## 6) Refresh schedule
- Daily satellites: cron daily
- Hourly satellites: cron hourly
- On-demand refresh allowed only with token

## 7) Telemetry
- Track page_view and action_submit only.
- Do not store raw inputs or private data in telemetry payloads.
