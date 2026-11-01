"""Offline: pfas_stations sends an API key (0.1.3), and a keyless call says a key is needed.

Since 2026-11-01 15:00 UTC the server's /api/pfas/stations answers 401 to a keyless call (the map's feature data is for
signed-in accounts with map access), and 0.1.2's pfas_stations had no key parameter, so it failed for every caller.
BROKEN BUILD (0.1.2): api_key= raises TypeError, the Client has no pfas_stations, and no X-SWATGenX-Api-Key header is sent.
CONTROLS: a keyless call raises 401 'needs an API key' on both builds (the server half); a public call (pfas_summary)
sends no key. The HTTP layer is mocked; nothing touches the network.
"""
import pytest

import swatgenx as sg
import swatgenx.client as client


class _Resp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.text = ""

    def json(self):
        return self._body


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def fake(method, url, json=None, params=None, headers=None, timeout=None):
        headers = dict(headers or {})
        seen.append({"url": url, "headers": headers, "params": params})
        if url.endswith("/api/pfas/stations"):
            if not headers.get("X-SWATGenX-Api-Key"):
                return _Resp(401, {"code": "sign_in_required"})
            return _Resp(200, {"type": "FeatureCollection", "features": [{"id": 1}]})
        return _Resp(200, {"ok": True})

    monkeypatch.setattr(client.requests, "request", fake)
    monkeypatch.delenv("SWATGENX_API_KEY", raising=False)
    return seen


def _key(call):
    return call["headers"].get("X-SWATGenX-Api-Key")


def test_pfas_stations_sends_the_key_it_is_given(calls):
    assert sg.pfas_stations(huc8="04050006", api_key="sgx_given")["features"]
    assert _key(calls[-1]) == "sgx_given" and calls[-1]["params"] == {"huc8": "04050006"}


def test_pfas_stations_reads_the_environment_key(calls, monkeypatch):
    monkeypatch.setenv("SWATGENX_API_KEY", "sgx_env")
    sg.pfas_stations(huc8="04050006")
    assert _key(calls[-1]) == "sgx_env"


def test_the_client_sends_its_own_key(calls):
    sg.Client(api_key="sgx_client").pfas_stations(huc8="04050006")
    assert _key(calls[-1]) == "sgx_client"


def test_a_keyless_call_says_a_key_is_needed(calls):
    with pytest.raises(sg.SwatGenXError) as e:
        sg.pfas_stations(huc8="04050006")
    assert e.value.status == 401 and "needs an API key" in str(e.value)
    assert _key(calls[-1]) is None


def test_a_public_call_sends_no_key(calls):
    sg.pfas_summary()
    assert _key(calls[-1]) is None
