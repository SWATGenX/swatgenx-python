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

# National groundwater inventory: 28.8M lithology intervals, 7.9M wells, 46 states
sg.groundwater_at(42.73, -84.55)      # nearest well + lithology log
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

## Access ladder

| tier | requires | unlocks |
|---|---|---|
| guest | nothing | all public data functions |
| member | free account + API key | model orders (fair-use), downloads |
| extended | request via info@swatgenx.com | HUC8 whole-basin, SWAT+MODFLOW-6, HUC14 30 m site models |
| calibration | account credit | cloud calibration campaigns |

`sg.access_info()` returns this ladder programmatically; quota/tier errors raise
`SwatGenXError` with upgrade guidance.

## AI agents

The same platform is agent-native via a public MCP server:
**https://www.swatgenx.com/mcp** (see the site's `llms.txt`). This package and the MCP
server expose the same surface, enforced by the same server-side quotas.

## Data citations

- Groundwater inventory: Zenodo DOI [10.5281/zenodo.21196958](https://doi.org/10.5281/zenodo.21196958)
- Soil PFAS inventory: Zenodo DOI [10.5281/zenodo.21096358](https://doi.org/10.5281/zenodo.21096358)

MIT-licensed client; platform terms at swatgenx.com.
