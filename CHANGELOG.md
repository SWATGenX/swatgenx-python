# Changelog

## 0.1.3 — 2026-11-01

SWATGenX changed who can reach what on 1 November 2026. This release says what the site does now.

- `pfas_stations()` takes `api_key=...` (or `SWATGENX_API_KEY`), and `Client.pfas_stations()` sends the client's key, as
  `groundwater_at()` does. Since 2026-11-01 the PFAS stations and the well records are for verified accounts and the agencies we
  work with: a keyless call answers 401, and a key whose account lacks that access answers 403. The keyless 25-station preview is
  gone.
- A 402, 403, 413 or 429 raises the site's own sentence when the response carries one (for example "Building, calibrating and
  downloading models needs a developer plan or a demo. Request access at swatgenx.com/signup."); the package's note is now only the
  fallback.
- `access_info()`:
  - each plan reads `models_kept` (the models a plan keeps; `None` = by quote); `model_builds_per_month` and
    `lifetime_model_builds` are gone, since the site counts the models kept, not the builds.
  - `free_account` carries only a note: building, calibrating and downloading models needs a developer plan or a demo. It no longer
    prints `models_kept` and `model_orders_per_day`, because since 2026-11-01 an account with no plan and no demo is refused every
    build.
  - `coupled_swat_modflow6` is renamed `swat_with_modflow6`. It and `calibration` say that calibration we do for you and a
    steady-state MODFLOW 6 groundwater model are part of a study, quoted at swatgenx.com/work-with-us; calibration you run yourself
    is paid from credit, on cloud compute.
  - `api_key` says how to request developer access, and `pricing_url` is the developer plans page (/pricing now redirects to
    Work with us).
- The README and the docstrings say which calls need no account (`catalog()`, `calibration()`, `groundwater_summary()`,
  `pfas_summary()`, `access_info()`) and which need a key.

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
