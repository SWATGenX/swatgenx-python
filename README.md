# swatgenx

[![Public API tests](https://github.com/SWATGenX/swatgenx-python/actions/workflows/tests.yml/badge.svg)](https://github.com/SWATGenX/swatgenx-python/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/swatgenx.svg)](https://pypi.org/project/swatgenx/)

Python client for [SWATGenX](https://www.swatgenx.com): SWAT+ watershed models built from national data for any USGS
gauge in the continental United States.

```
pip install swatgenx
```

## Data

```python
import swatgenx as sg

# Example-model catalog: built SWAT+ models, with their channel counts and locations
models = sg.catalog(state="MI")      # e.g. 04112500, 541 channels
# sg.calibration(site_no) returns a card's calibration record, or None; no example card carries one today.

# National groundwater inventory: 27.7M lithology intervals, 9.28M wells, 48 states (as of 2026-09-29; sg.groundwater_summary() returns the live totals)
sg.groundwater_at(42.73, -84.55)      # nearest well + lithology log (needs an API key whose account may see the map's data: SWATGENX_API_KEY)
sg.groundwater_summary()

# PFAS monitoring stations in an area (huc8 = 8-digit hydrologic unit code; needs an API key, as groundwater_at does)
sg.pfas_stations(huc8="04050006")
sg.pfas_summary()
```

## Build and download models — model access or a demo, and an API key

Request access at [swatgenx.com/signup](https://www.swatgenx.com/signup); once we have approved the request, open
dashboard → API keys, then:

```python
c = sg.Client(api_key="...")                    # or env SWATGENX_API_KEY

order = c.order(usgs_station="04124500")        # any of 25,000+ USGS gauges
c.wait(order["order_id"])                       # typical build: 20 min – 2 h
c.download("04124500", vpuid="0406", dest="model.zip")   # ZIP straight to your disk
```

Builds run on SWATGenX cloud infrastructure from national data (NHDPlus HR, 3DEP,
gSSURGO, NLCD, PRISM, USGS NWIS); delivery is pull-based — no email round-trip.

## Access

These calls need no account: `catalog()`, `calibration()`, `groundwater_summary()`, `pfas_summary()` and
`access_info()`. Since 1 November 2026 the map's data, the well records (`groundwater_at()`) and the
PFAS stations (`pfas_stations()`), is for verified accounts and the agencies we work with: pass an API
key, or call them on a `Client`. Accounts are by invitation, for a named research collaboration or a
funded study: request access at
[swatgenx.com/signup](https://www.swatgenx.com/signup). Building, calibrating and downloading models
needs model access or a demo. Calibration runs on cloud compute from an account's calibration
credit; calibration we do for you, and a MODFLOW 6 groundwater model, are part of a study, quoted at
[swatgenx.com/work-with-us](https://www.swatgenx.com/work-with-us). `sg.access_info()` returns these
rules, and `Client.whoami()` your account's access. A refusal raises `SwatGenXError` with the site's own
sentence.

## AI agents

The same platform is agent-native via a public MCP server: **https://www.swatgenx.com/mcp** (see the
site's `llms.txt`). Every call needs a SWATGenX sign-in or an API key. The model, data
and build tools need model access, and accounts are by invitation; four tools stay open to any
account (`search_docs`, `get_doc`, `get_access_info` and `get_engine_info`). This package calls the REST
API, under the rules in Access.

## Data citations

- Groundwater inventory: Zenodo DOI [10.5281/zenodo.21196958](https://doi.org/10.5281/zenodo.21196958)
- Soil PFAS inventory: Zenodo DOI [10.5281/zenodo.21096358](https://doi.org/10.5281/zenodo.21096358)

MIT-licensed client; platform terms at swatgenx.com.
