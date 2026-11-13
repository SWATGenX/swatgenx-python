"""swatgenx — Python client for SWATGenX (https://www.swatgenx.com).

No account needed:

    import swatgenx as sg
    models = sg.catalog(state="MI")       # built example models (e.g. 04112500)
    sg.groundwater_summary()              # national well-inventory totals
    sg.pfas_summary()                     # PFAS-inventory totals

The map's data is for verified accounts and the agencies we work with; pass an API key
(or set SWATGENX_API_KEY):

    sg.groundwater_at(42.73, -84.55, api_key="...")    # nearest well + lithology log
    sg.pfas_stations(huc8="04050006", api_key="...")   # PFAS stations (8-digit HUC)

Building and downloading models needs model access or a demo, and an API key
(request access at https://www.swatgenx.com/signup; once we have approved the request,
open dashboard -> API keys):

    c = sg.Client(api_key="...")          # or env SWATGENX_API_KEY
    order = c.order(usgs_station="04124500")
    c.status(order["order_id"])
    c.download("04124500", vpuid="0406", dest="model.zip")

Accounts are by invitation, for a named research collaboration or a funded study, and
access_info() returns these rules. Calibration runs on cloud compute
from an account's calibration credit; calibration we do for you, and a MODFLOW 6 groundwater
model, are part of a study (https://www.swatgenx.com/work-with-us). AI agents can use the
same platform via MCP: https://www.swatgenx.com/mcp
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

__version__ = "0.1.5"
__all__ = [
    "Client", "SwatGenXError", "access_info", "calibration", "catalog",
    "groundwater_at", "groundwater_summary", "pfas_stations", "pfas_summary",
]
