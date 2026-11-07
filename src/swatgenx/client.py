"""HTTP client for the SWATGenX public API (thin, dependency-light).

Every call maps 1:1 onto a documented endpoint at https://www.swatgenx.com — the same
surface the website and the MCP server (https://www.swatgenx.com/mcp) use. The example-model
catalog, the inventory summaries and access_info() need no account. The map's data (well records,
PFAS stations) needs an API key whose account may see it, and actions that create state (model
orders, downloads) need an invited account or a demo; the Client class carries the key.
Authentication, ownership and allocations are enforced server-side.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE = os.environ.get("SWATGENX_BASE_URL", "https://www.swatgenx.com")
_UA = {"User-Agent": "swatgenx-python/0.1.4"}


class SwatGenXError(RuntimeError):
    """API error with the server's message and, when relevant, upgrade guidance."""

    def __init__(self, message: str, status: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


# Lane GM P7 (WORDS_RD_COMPANY_GM 7.5's access_note): the fallback only. Since 2026-11-01 every 403 carries the site's own
# sentence, which _request raises when the body has one.
# 0.1.4: the MCP server's access_note (Q1616 Am.6); Client.whoami() stands for get_access_info.
_ACCESS_NOTE = (
    "This action exceeds your current access or fair-use allocation. "
    "Client.whoami() reports your account's plan. Work that is part of a study is quoted at "
    "https://www.swatgenx.com/work-with-us, and calibration runs on account credit."
)


def _request(method: str, path: str, *, key: str | None = None, json: dict | None = None,
             params: dict | None = None, timeout: int = 90) -> Any:
    headers = dict(_UA)
    if key:
        headers["X-SWATGenX-Api-Key"] = key
    r = requests.request(method, f"{BASE}{path}", json=json, params=params,
                         headers=headers, timeout=timeout)
    try:
        body = r.json()
    except ValueError:
        body = {"raw": (r.text or "")[:500]}
    if r.status_code == 401:
        if not key:
            # No key was sent, so "invalid or revoked" would be false: the endpoint needs one.
            raise SwatGenXError(
                "This endpoint needs an API key: pass api_key=... or set SWATGENX_API_KEY. "
                "Create one at https://www.swatgenx.com -> dashboard -> API keys.", 401, body)
        raise SwatGenXError(
            "Authentication failed — invalid or revoked API key. Sign in at "
            "https://www.swatgenx.com -> dashboard -> API keys.", 401, body)
    if r.status_code in (402, 403, 413, 429):
        said = body.get("message") if isinstance(body, dict) else None
        raise SwatGenXError(str(said) if said else _ACCESS_NOTE, r.status_code, body)
    if r.status_code >= 400:
        msg = body.get("message") or body.get("error") or f"HTTP {r.status_code}"
        raise SwatGenXError(str(msg), r.status_code, body)
    return body


# ------------------------------------------------------------------ public (no account)
def catalog(state: str | None = None, calibrated_only: bool = False,
            min_channels: int | None = None, max_channels: int | None = None,
            calibrated: bool | None = None) -> list[dict]:
    """Public example-model catalog: built SWAT+ models across the conterminous US,
    each with structure counts and (when calibrated) cal/val NSE. Filter by two-letter
    state, calibration status (`calibrated_only`, alias `calibrated`), and channel-count
    bounds. A model counts as calibrated only when the website shows it as calibrated
    (`calibration_advertised`); a failed or below-satisfactory run does not."""
    # 0.1.2: the filter was 'any calibration record', so calibrated_only=True returned failed runs (Lane V, 2026-09-29:
    # state="MI" gave 3 models, one graded failed and one below satisfactory, where /example-models badges one).
    want_calibrated = bool(calibrated_only) or bool(calibrated)
    payload = _request("GET", "/api/public/example-swat-models")
    out = []
    for m in payload.get("models") or []:
        if state and str(m.get("state") or "").upper() != state.upper():
            continue
        if want_calibrated and not m.get("calibration_advertised"):
            continue
        ch = m.get("n_channels")
        if min_channels is not None and (ch is None or ch < min_channels):
            continue
        if max_channels is not None and (ch is None or ch > max_channels):
            continue
        out.append(m)
    return out


def calibration(site_no: str) -> dict | None:
    """Calibration + held-out validation metrics for one public example model
    (daily/monthly NSE, PBIAS, method, window). None if never calibrated."""
    for m in catalog():
        if str(m.get("site_no")) == str(site_no):
            return m.get("calibration")
    return None


def groundwater_at(lat: float, lon: float, tol_deg: float = 0.05, api_key: str | None = None) -> dict:
    """Nearest well to a point from the national groundwater inventory (live totals at
    /api/gw-wells/summary), with its lithology log when available. tol_deg is the search
    box half-width in degrees (~0.05 = 5 km).

    Needs an API key: pass api_key=... or set SWATGENX_API_KEY. The well records have been signed-in
    only since 2026-09-25 and, since 2026-11-01, are for verified accounts and the agencies we work with:
    without a key the site answers 401, and with a key whose account lacks that access, 403.
    groundwater_summary() stays open."""
    key = (api_key or os.environ.get("SWATGENX_API_KEY") or "").strip() or None
    return _request("GET", "/api/gw-wells/at", key=key,
                    params={"lat": lat, "lon": lon, "tol": tol_deg})


def groundwater_summary() -> dict:
    """Live national groundwater-inventory counts (wells, intervals, per-state)."""
    return _request("GET", "/api/gw-wells/summary")


def pfas_stations(bbox: str | None = None, huc12: str | None = None,
                  huc8: str | None = None, api_key: str | None = None) -> dict:
    """PFAS monitoring stations in an area (GeoJSON). Name the area by bbox
    ('minLon,minLat,maxLon,maxLat'), huc12, or huc8 (an 8-digit code).

    Needs an API key: pass api_key=... or set SWATGENX_API_KEY. Since 2026-11-01 the map's feature
    data is for verified accounts and the agencies we work with: without a key the site answers 401,
    and with a key whose account lacks that access, 403. The error carries the site's own sentence.
    pfas_summary() stays open."""
    # 0.1.3: the station endpoint answers 401 to a keyless call since 2026-11-01 15:00 UTC, so this sends a key as
    # groundwater_at does; a keyless call raises SwatGenXError(401, 'needs an API key').
    key = (api_key or os.environ.get("SWATGENX_API_KEY") or "").strip() or None
    params = {k: v for k, v in (("bbox", bbox), ("huc12", huc12), ("huc8", huc8)) if v}
    return _request("GET", "/api/pfas/stations", key=key, params=params)


def pfas_summary() -> dict:
    """Live PFAS-inventory summary counts."""
    return _request("GET", "/api/pfas/summary")


def access_info() -> dict:
    """How SWATGenX access works. Since 2026-11-07 the site is invitation only and sells no plan online, so the site's plans API
    answers 404 and this returns the invitation rules with an empty plan list; when that API answers, each plan is its name and the
    models it keeps (None = by quote), never a price. These are the words the site's MCP server's get_access_info returns."""
    try:
        body = _request("GET", "/api/billing/plans")
    except SwatGenXError as e:
        # 0.1.4: the plans API's 404 means "not sold online"; any other error still reaches the caller.
        if e.status != 404:
            raise
        body = None
    plans = []
    for row in (body or {}).get("plans") or []:
        # The plan name and models_kept only: no price field and no free-text notes, whatever the API answers.
        plans.append({"plan": row.get("display_name") or row.get("plan_name"), "models_kept": row.get("models_held_limit")})
    live = isinstance(body, dict) and isinstance(body.get("plans"), list)
    return {
        "source": ("live: https://www.swatgenx.com/api/billing/plans" if live else
                   "Plans are not sold online; accounts are by invitation, for a named research collaboration or a funded study."),
        "pricing_url": "https://www.swatgenx.com/contact",
        "free_account": {"note": "Building, calibrating and downloading models needs an invited account or a demo. "
                                 "Request access at https://www.swatgenx.com/signup."},
        "paid_plans": plans,
        "calibration": ("Calibration runs on cloud compute from an account's calibration credit; credit is not sold online. "
                        "Calibration we do for you is part of a study."),
        "swat_with_modflow6": ("Part of a study we do for you, for a watershed in the states we offer: a steady-state MODFLOW 6 "
                               "groundwater model built for the same watershed. Request a proposal at "
                               "https://www.swatgenx.com/work-with-us."),
        "api_key": ("Request access at https://www.swatgenx.com/signup; once we have approved the request, your API key is "
                    "issued the first time you open dashboard -> API keys. Pass it as api_key=... or set SWATGENX_API_KEY."),
        "agent_access": "AI agents can use the same platform via MCP: https://www.swatgenx.com/mcp",
    }


# ------------------------------------------------------------------ authenticated
class Client:
    """Authenticated client. Get a key: sign in at swatgenx.com -> dashboard -> API keys,
    or set the SWATGENX_API_KEY environment variable."""

    def __init__(self, api_key: str | None = None):
        self.api_key = (api_key or os.environ.get("SWATGENX_API_KEY") or "").strip()
        if not self.api_key:
            raise SwatGenXError(
                "API key required: pass Client(api_key=...) or set SWATGENX_API_KEY. "
                "Keys: request access at https://www.swatgenx.com/signup; once we have approved the request, open dashboard -> API keys.")

    # -- account
    def whoami(self) -> dict:
        """Subscription status for the key's account."""
        return _request("GET", "/api/user/subscription-status", key=self.api_key)

    # -- data that needs an account
    def groundwater_at(self, lat: float, lon: float, tol_deg: float = 0.05) -> dict:
        """sg.groundwater_at with this client's key (well records are for verified accounts and the agencies we work
        with)."""
        return groundwater_at(lat, lon, tol_deg=tol_deg, api_key=self.api_key)

    def pfas_stations(self, bbox: str | None = None, huc12: str | None = None, huc8: str | None = None) -> dict:
        """sg.pfas_stations with this client's key."""
        return pfas_stations(bbox=bbox, huc12=huc12, huc8=huc8, api_key=self.api_key)

    # -- ordering
    def order(self, usgs_station: str | None = None, huc12_outlet: str | None = None,
              force_rebuild: bool = False) -> dict:
        """Order a real SWAT+ model build (consumes your fair-use allocation).
        Provide either a USGS gauge id or a 12-digit HUC12 outlet. Returns the order
        record incl. order_id; typical build 20 min - 2 h."""
        if huc12_outlet:
            return _request("POST", "/api/model-settings/explorer-watershed", key=self.api_key,
                            json={"outlet_huc12": str(huc12_outlet).strip(),
                                  "force_rebuild": bool(force_rebuild)})
        if usgs_station:
            return _request("POST", "/api/model-settings", key=self.api_key,
                            json={"site_no": str(usgs_station).strip(),
                                  "force_rebuild": bool(force_rebuild)})
        raise SwatGenXError("provide usgs_station or huc12_outlet")

    def status(self, order_id: str) -> dict:
        """State/stage/timing of a build order."""
        return _request("GET", f"/api/model-orders/{str(order_id).strip()}", key=self.api_key)

    def orders(self) -> dict:
        """All of your build orders, newest first."""
        return _request("GET", "/api/model-orders", key=self.api_key)

    # The server's terminal order states (web_application/app/model_order_queue.py STATE_*). Everything else, including
    # QUEUED_APP, DISPATCHING, RUNNING and any state this client does not know yet, means "keep waiting".
    TERMINAL_STATES = frozenset({"SUCCESS", "FAILURE", "CANCELLED", "ORPHANED"})

    def wait(self, order_id: str, poll_seconds: int = 60, timeout_hours: float = 4.0) -> dict:
        """Block until an order reaches a terminal state; returns the final status() record.

        GET /api/model-orders/<id> nests the record under "order" ({"status": "success", "order": {"state": ...}}).
        Until 2026-10-09 this read a top-level "state" that the route never sends, so it could only end at the deadline,
        and its "not QUEUED/RUNNING/PENDING" test would also have returned on DISPATCHING."""
        deadline = time.time() + timeout_hours * 3600
        while True:
            rec = self.status(order_id)
            order = rec.get("order") if isinstance(rec.get("order"), dict) else rec
            state = str(order.get("state") or order.get("order_state") or "").upper()
            if state in self.TERMINAL_STATES:
                return rec
            if time.time() > deadline:
                raise SwatGenXError(f"order {order_id} not terminal after {timeout_hours} h "
                                    f"(last state: {state or 'unknown'})")
            time.sleep(max(10, poll_seconds))

    # -- delivery (pull-based: the ZIP lands on YOUR disk; no email needed)
    def download_link(self, site_no: str, vpuid: str, level: str = "usgs_station") -> dict:
        """Mint a fresh 24 h download link for a model you own."""
        return _request("POST", "/api/download_model/link", key=self.api_key,
                        json={"site_no": str(site_no).strip(), "vpuid": str(vpuid).strip(),
                              "level": level})

    def download(self, site_no: str, vpuid: str, dest: str,
                 level: str = "usgs_station", timeout: int = 1800) -> str:
        """Download a model you own to a local path (streams the ZIP). Returns dest."""
        link = self.download_link(site_no, vpuid, level)
        url = link.get("download_url")
        if not url:
            raise SwatGenXError("no download_url in response", detail=link)
        with requests.get(url, headers=_UA, stream=True, timeout=timeout) as r:
            if r.status_code >= 400:
                raise SwatGenXError(f"download failed: HTTP {r.status_code}", r.status_code)
            with open(dest, "wb") as fh:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)
        return dest
