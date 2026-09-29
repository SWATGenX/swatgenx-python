"""HTTP client for the SWATGenX public API (thin, dependency-light).

Every call maps 1:1 onto a documented endpoint at https://www.swatgenx.com — the same
surface the website and the MCP server (https://www.swatgenx.com/mcp) use. Public
functions need no account; the Client class carries a per-user API key for actions
that create state (model orders, downloads), where authentication, ownership, and
fair-use quotas are enforced server-side.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE = os.environ.get("SWATGENX_BASE_URL", "https://www.swatgenx.com")
_UA = {"User-Agent": "swatgenx-python/0.1.0"}


class SwatGenXError(RuntimeError):
    """API error with the server's message and, when relevant, upgrade guidance."""

    def __init__(self, message: str, status: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


_ACCESS_NOTE = (
    "This action exceeds your current plan or fair-use allocation. "
    "See swatgenx.access_info() for the plans (read live) or https://www.swatgenx.com/pricing; "
    "cloud calibration runs on account credit on every plan."
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
        raise SwatGenXError(_ACCESS_NOTE, r.status_code, body)
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

    Needs a free account's API key: pass api_key=... or set SWATGENX_API_KEY. The well-record
    endpoint has been signed-in only since 2026-09-25, so a keyless call cannot succeed."""
    key = (api_key or os.environ.get("SWATGENX_API_KEY") or "").strip() or None
    return _request("GET", "/api/gw-wells/at", key=key,
                    params={"lat": lat, "lon": lon, "tol": tol_deg})


def groundwater_summary() -> dict:
    """Live national groundwater-inventory counts (wells, intervals, per-state)."""
    return _request("GET", "/api/gw-wells/summary")


def pfas_stations(bbox: str | None = None, huc12: str | None = None,
                  huc8: str | None = None) -> dict:
    """National PFAS monitoring inventory (GeoJSON stations). Filter by bbox
    ('minLon,minLat,maxLon,maxLat'), huc12, or huc8."""
    params = {k: v for k, v in (("bbox", bbox), ("huc12", huc12), ("huc8", huc8)) if v}
    return _request("GET", "/api/pfas/stations", params=params)


def pfas_summary() -> dict:
    """Live PFAS-inventory summary counts."""
    return _request("GET", "/api/pfas/summary")


def access_info() -> dict:
    """The SWATGenX plans, read LIVE from the site's pricing API (the figures the pricing page
    sells), plus the rules that are not in that payload. Nothing here is typed: a plan that
    changes on the site changes here without a package release."""
    body = _request("GET", "/api/billing/plans")
    free = (body or {}).get("free_tier") or {}
    plans = []
    for row in (body or {}).get("plans") or []:
        entry = {"plan": row.get("display_name") or row.get("plan_name"), "notes": row.get("notes")}
        if row.get("quote_only"):
            entry["price"] = "by quote: info@swatgenx.com"
        else:
            entry["price_usd_per_month"] = row.get("monthly_price_usd")
            # models_unlimited rows carry an abuse backstop, not an allowance; never print it
            entry["model_builds_per_month"] = ("unlimited" if row.get("models_unlimited")
                                               else row.get("monthly_model_creation_limit"))
        plans.append(entry)
    return {
        "source": "live: https://www.swatgenx.com/api/billing/plans",
        "pricing_url": "https://www.swatgenx.com/pricing",
        "free_account": {"lifetime_model_builds": free.get("builds_lifetime"),
                         "note": "Failed builds are refunded. HUC8 whole-basin orders are open "
                                 "to every plan."},
        "paid_plans": plans,
        "calibration": "Pay per credit on every plan, run on cloud compute (website dashboard). "
                       "Coupled SWAT+/MODFLOW-6 calibration needs MAX or Department.",
        "coupled_swat_modflow6": "MAX and Department.",
        "api_key": "Sign in at swatgenx.com -> dashboard -> API keys (a free account works).",
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
                "Keys: swatgenx.com -> dashboard -> API keys (free account).")

    # -- account
    def whoami(self) -> dict:
        """Subscription status for the key's account."""
        return _request("GET", "/api/user/subscription-status", key=self.api_key)

    # -- data that needs an account
    def groundwater_at(self, lat: float, lon: float, tol_deg: float = 0.05) -> dict:
        """sg.groundwater_at with this client's key (well records are signed-in only)."""
        return groundwater_at(lat, lon, tol_deg=tol_deg, api_key=self.api_key)

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

    def wait(self, order_id: str, poll_seconds: int = 60, timeout_hours: float = 4.0) -> dict:
        """Block until an order reaches a terminal state; returns the final record."""
        deadline = time.time() + timeout_hours * 3600
        while True:
            rec = self.status(order_id)
            state = str(rec.get("state") or rec.get("order_state") or "").upper()
            if state and not any(s in state for s in ("QUEUED", "RUNNING", "PENDING")):
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
