"""Guest-tier live tests — run against the production API, no account or key needed.

These are the public subset of the SWATGenX two-doors QA gate. They exercise every
no-auth function in the package against https://www.swatgenx.com, so a green run
means both the client and the live service are healthy. Authenticated paths
(orders, downloads) are covered by a private gate on the server side.

Run: pip install pytest && pytest tests/ -v
"""
import pytest

import swatgenx as sg


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
    assert models and all(m.get("calibration") or m.get("calibrated") for m in models)


def test_catalog_channel_bounds():
    models = sg.catalog(min_channels=100, max_channels=600)
    assert models and all(100 <= m["n_channels"] <= 600 for m in models)


def test_calibration_known_model():
    cal = sg.calibration("01451800")
    assert cal is not None
    assert cal.get("cal_daily_nse") is not None


def test_calibration_nonexistent_returns_none():
    assert sg.calibration("00000000") is None


def test_groundwater_at_michigan():
    well = sg.groundwater_at(42.73, -84.55)
    assert well.get("found") and well.get("well_id")


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
    assert len(info.get("tiers", [])) == 4


def test_client_requires_key():
    with pytest.raises(sg.SwatGenXError, match="API key"):
        sg.Client(api_key="")


def test_client_bad_key_auth_guidance():
    with pytest.raises(sg.SwatGenXError):
        sg.Client(api_key="not-a-real-key").whoami()
