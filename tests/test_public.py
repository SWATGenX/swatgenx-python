"""Guest-tier live tests — run against the production API, no account or key needed.

These are the public subset of the SWATGenX two-doors QA gate. They exercise every
no-auth function in the package against https://www.swatgenx.com, so a green run
means both the client and the live service are healthy. Authenticated paths
(orders, downloads) are covered by a private gate on the server side.

Run: pip install pytest && pytest tests/ -v
"""
import os

import pytest

import swatgenx as sg

# groundwater_at needs an account's API key (the well-record endpoint is signed-in only since 2026-09-25). CI passes a
# dedicated test account's key as the SWATGENX_API_KEY secret; without it these two tests SKIP rather than fail.
needs_key = pytest.mark.skipif(not os.environ.get("SWATGENX_API_KEY"), reason="SWATGENX_API_KEY not set")


def test_catalog_unfiltered():
    models = sg.catalog()
    assert len(models) >= 50
    m = models[0]
    assert {"site_no", "vpuid", "state", "n_channels"} <= set(m)


def test_catalog_state_filter():
    models = sg.catalog(state="FL")
    assert models and all(m["state"] == "FL" for m in models)


def test_catalog_calibrated_only():
    models = sg.catalog(calibrated_only=True)
    # 0.1.2: 'calibrated' means what the website shows (calibration_advertised), not 'a record exists'
    assert models and all(m.get("calibration_advertised") for m in models)


def test_catalog_channel_bounds():
    models = sg.catalog(min_channels=100, max_channels=600)
    assert models and all(100 <= m["n_channels"] <= 600 for m in models)


def test_calibration_known_model():
    cal = sg.calibration("01451800")
    assert cal is not None
    assert cal.get("cal_daily_nse") is not None


def test_calibration_nonexistent_returns_none():
    assert sg.calibration("00000000") is None


@needs_key
def test_groundwater_at_michigan():
    well = sg.groundwater_at(42.73, -84.55)
    assert well.get("found") and well.get("well_id")


@needs_key
def test_groundwater_at_pennsylvania():
    well = sg.groundwater_at(40.602, -75.471)
    assert well.get("found") and well.get("well_id")


def test_groundwater_at_open_ocean_clean_error():
    with pytest.raises(sg.SwatGenXError):
        sg.groundwater_at(30.0, -60.0)


def test_groundwater_summary():
    s = sg.groundwater_summary()
    assert "by_state" in s


def test_pfas_summary():
    s = sg.pfas_summary()
    assert s.get("stations", 0) > 5000


def test_pfas_stations_huc8():
    fc = sg.pfas_stations(huc8="04050006")
    assert len(fc.get("features") or []) > 0


def test_access_info_ladder():
    info = sg.access_info()
    assert info.get("paid_plans"), "0.1.2 reads the plans live; the typed 4-tier ladder is gone"


def test_client_requires_key(monkeypatch):
    # Client falls back to SWATGENX_API_KEY, which CI sets; clear it so this still tests the no-key path.
    monkeypatch.delenv("SWATGENX_API_KEY", raising=False)
    with pytest.raises(sg.SwatGenXError, match="API key"):
        sg.Client(api_key="")


def test_client_bad_key_auth_guidance():
    with pytest.raises(sg.SwatGenXError):
        sg.Client(api_key="not-a-real-key").whoami()


def test_access_info_reads_the_live_plans():
    """0.1.2: the plans come from /api/billing/plans. BROKEN BUILD (0.1.1): a typed ladder with a
    'guest' tier and 'extended access'; no paid_plans key."""
    a = sg.access_info()
    names = {p["plan"] for p in a["paid_plans"]}
    assert "Starter" in names and "MAX" in names          # CONTROL: the live payload was read
    text = str(a).lower()
    assert "extended access" not in text and "guest" not in text


def test_groundwater_at_without_a_key_says_a_key_is_needed(monkeypatch):
    """A keyless call must say the endpoint needs a key, never 'invalid or revoked' (no key was sent)."""
    monkeypatch.delenv("SWATGENX_API_KEY", raising=False)
    with pytest.raises(sg.SwatGenXError) as e:
        sg.groundwater_at(42.73, -84.55)
    assert e.value.status == 401 and "needs an API key" in str(e.value)
