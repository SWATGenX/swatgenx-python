# Changelog

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
