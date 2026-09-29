"""Offline: catalog(calibrated_only=True) returns only the models the website shows as calibrated.

Found by Lane V (2026-09-29) on swatgenx 0.1.1 from PyPI: sg.catalog(state="MI", calibrated_only=True) returned 3
models, including 04124500 (grade failed, daily NSE -0.043) and 04118500 (below satisfactory, not advertised), while
/example-models badges only 040400010207. The filter was 'any calibration record'. BROKEN BUILD (0.1.1): 3 returned,
and the 'calibrated' alias raises TypeError. FIXED: exactly 040400010207. The fixture mirrors the live entries; nothing
here touches the network.
"""
import pytest

import swatgenx.client as client

MI = [
    {"site_no": "04118500", "state": "MI", "n_channels": 120, "calibration": {"cal_daily_nse": 0.103},
     "calibration_advertised": False, "calibration_tier": "uncalibrated", "calibration_grade": "below_satisfactory"},
    {"site_no": "040400010207", "state": "MI", "n_channels": 40, "calibration": {"cal_daily_nse": 0.677},
     "calibration_advertised": True, "calibration_tier": "good", "calibration_grade": "good"},
    {"site_no": "04124500", "state": "MI", "n_channels": 300, "calibration": {"cal_daily_nse": -0.043},
     "calibration_advertised": False, "calibration_tier": "uncalibrated", "calibration_grade": "failed"},
    {"site_no": "04080206", "state": "MI", "n_channels": 500, "calibration": None,
     "calibration_advertised": False, "calibration_tier": "uncalibrated"},
]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(client, "_request", lambda method, path, **kw: {"models": [dict(m) for m in MI]})


def _ids(models):
    return [m["site_no"] for m in models]


def test_calibrated_only_returns_only_the_advertised_model():
    assert _ids(client.catalog(state="MI", calibrated_only=True)) == ["040400010207"]  # 0.1.1: 3 models


def test_the_calibrated_alias_matches_the_mcp_tool():
    assert _ids(client.catalog(state="MI", calibrated=True)) == ["040400010207"]  # 0.1.1: TypeError


def test_control_no_filter_returns_every_model():
    assert _ids(client.catalog(state="MI")) == [m["site_no"] for m in MI]
