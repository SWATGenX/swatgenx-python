# Changelog

## 0.1.2 — 2026-09-29

- `groundwater_at()` sends an API key: `api_key=...`, or `SWATGENX_API_KEY`, or `Client(...).groundwater_at()`.
  The well-record endpoint has been signed-in only since 2026-09-25, and 0.1.1 had no way to send a key, so the call
  failed for everyone, with the false message "invalid or revoked API key" (no key was sent). A 401 on a keyless
  request now says the endpoint needs a key. (Ported from the public mirror's #1, which had not reached this source.)
- `catalog(calibrated_only=True)` returns only the models the website shows as calibrated
  (`calibration_advertised`). It returned every model with a calibration record, failed runs included:
  `catalog(state="MI", calibrated_only=True)` gave 3 models where /example-models badges 1. `calibrated`
  is accepted as an alias, the name the public MCP tool uses.
- README: the groundwater totals are written from the live API by `tools/refresh_readme_counts.py`, re-run at every
  release, with their date (they had read
  28.8M intervals, 7.9M wells, 46 states); the access section points to the plans on /pricing and to
  `access_info()` instead of a typed ladder and lists which data calls need no account (checked against the server's
  own rules: only the well records need a key); the AI-agents paragraph states the 15 October 2026 MCP change.
- `access_info()` reads the plans live from `/api/billing/plans` instead of returning a typed
  ladder. The typed one had gone false: it offered a "guest" tier, listed HUC8 whole-basin
  orders as extended access granted on request (open to every plan since 2026-07-23), and
  named tiers older than the current plans (free, Starter, MAX, Department by quote).
- The quota-refusal note no longer mentions extended access.
- `groundwater_*` docstrings: the stale national well counts were replaced by a pointer to the
  live summary (in the tree since ea04545c0, never released).

## 0.1.1 — 2026-07-19

- Fixed the PFAS example in the README and module docstring: `pfas_stations(huc8=...)`
  takes an 8-digit hydrologic unit code (e.g. `"04050006"`); the old example passed a
  4-digit code and returned an empty result.
- Public source repository: https://github.com/SWATGenX/swatgenx-python, with a
  guest-tier test suite running daily against the live API (badge in the README).
- Added `Repository` and `Changelog` links to the package metadata.
- No code changes to the client itself.

## 0.1.0 — 2026-07-19

- Initial release: public data functions (`catalog`, `calibration`, `groundwater_at`,
  `groundwater_summary`, `pfas_stations`, `pfas_summary`, `access_info`) and the
  authenticated `Client` (orders, status, downloads).
