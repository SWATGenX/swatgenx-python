"""swatgenx — Python client for SWATGenX (https://www.swatgenx.com).

Public data needs no account:

    import swatgenx as sg
    models = sg.catalog(state="FL", calibrated_only=True)
    sg.calibration("01451800")            # cal/val NSE, PBIAS, method
    sg.groundwater_at(42.73, -84.55)      # nearest well + lithology log
    sg.pfas_stations(huc8="04050006")     # PFAS monitoring inventory (8-digit HUC)

Ordering and downloading models needs a free account + API key
(sign in at swatgenx.com -> dashboard -> API keys):

    c = sg.Client(api_key="...")          # or env SWATGENX_API_KEY
    order = c.order(usgs_station="04124500")
    c.status(order["order_id"])
    c.download("04124500", vpuid="0406", dest="model.zip")

Access ladder: guest (public data) -> member (free key: fair-use orders + downloads)
-> extended access (info@swatgenx.com: HUC8 / SWAT+MODFLOW-6 / HUC14 site models)
-> calibration (account credit). AI agents can use the same platform via MCP:
https://www.swatgenx.com/mcp
"""
from .client import (
    Client,
    SwatGenXError,
    access_info,
    calibration,
    catalog,
    groundwater_at,
    groundwater_summary,
    pfas_stations,
    pfas_summary,
)

__version__ = "0.1.1"
__all__ = [
    "Client", "SwatGenXError", "access_info", "calibration", "catalog",
    "groundwater_at", "groundwater_summary", "pfas_stations", "pfas_summary",
]
