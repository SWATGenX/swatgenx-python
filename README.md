# swatgenx

[![Public API tests](https://github.com/SWATGenX/swatgenx-python/actions/workflows/tests.yml/badge.svg)](https://github.com/SWATGenX/swatgenx-python/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/swatgenx.svg)](https://pypi.org/project/swatgenx/)

Python client for [SWATGenX](https://www.swatgenx.com) — automated SWAT+ / MODFLOW 6
watershed models and open national water datasets for the conterminous United States.

```
pip install swatgenx
```

## Public data — no account needed

```python
import swatgenx as sg

# Example-model catalog: built SWAT+ models with calibration/validation metrics
models = sg.catalog(state="FL", calibrated_only=True)
sg.calibration("01451800")
# {'mode': 'engineer', 'cal_daily_nse': 0.642, 'val_daily_nse': 0.748, ...}

# National groundwater inventory: 27.7M lithology intervals, 9.28M wells, 48 states (as of 2026-09-29; sg.groundwater_summary() returns the live totals)
sg.groundwater_at(42.73, -84.55)      # nearest well + lithology log (needs an API key: SWATGENX_API_KEY)
sg.groundwater_summary()

# National PFAS monitoring inventory (huc8 = 8-digit hydrologic unit code)
sg.pfas_stations(huc8="04050006")
sg.pfas_summary()
```

## Order and download models — free account + API key

Sign in at [swatgenx.com](https://www.swatgenx.com) → dashboard → API keys, then:

```python
c = sg.Client(api_key="...")                    # or env SWATGENX_API_KEY

order = c.order(usgs_station="04124500")        # any of 25,000+ USGS gauges
c.wait(order["order_id"])                       # typical build: 20 min – 2 h
c.download("04124500", vpuid="0406", dest="model.zip")   # ZIP straight to your disk
```

Builds run on SWATGenX cloud infrastructure from national data (NHDPlus HR, 3DEP,
gSSURGO, NLCD, PRISM, USGS NWIS); delivery is pull-based — no email round-trip.

## Plans and access

These data functions need no account: `catalog()`, `calibration()`, `groundwater_summary()`,
`pfas_stations()`, `pfas_summary()` and `access_info()`. Well records (`groundwater_at()`, or
`Client.groundwater_at()`) need a free account's API key, and so do ordering and downloading models,
within your plan's allocation; cloud calibration is paid from account credit. The plans and what each
includes are at [swatgenx.com/pricing](https://www.swatgenx.com/pricing), and `sg.access_info()`
returns them live from the API. Quota and plan errors raise `SwatGenXError` with the next step.

## AI agents

The same platform is agent-native via a public MCP server:
**https://www.swatgenx.com/mcp** (see the site's `llms.txt`). Every call needs a SWATGenX
sign-in or an API key. From 15 October 2026, agent access to the model, data and order tools is
part of the paid plans (Starter, MAX or Department); four tools stay open to any account
(`search_docs`, `get_doc`, `get_access_info` and `get_engine_info`). This package calls the REST
API, which that date does not change: the public data functions need no account, and model orders
use the same fair-use allocation as the web application.

## Data citations

- Groundwater inventory: Zenodo DOI [10.5281/zenodo.21196958](https://doi.org/10.5281/zenodo.21196958)
- Soil PFAS inventory: Zenodo DOI [10.5281/zenodo.21096358](https://doi.org/10.5281/zenodo.21096358)

MIT-licensed client; platform terms at swatgenx.com.
