"""Offline: groundwater_at sends an API key, and a keyless call says a key is needed.

Found by Lane S (2026-09-29) on the 0.1.2 branch and on 0.1.1 from PyPI: since 2026-09-25 the server's /api/gw-wells/at
answers 401 to a keyless call (gw_wells_api.py's identified-caller gate), and groundwater_at had no key parameter, so it
failed for every caller, with the false message 'invalid or revoked API key' although no key was sent.
BROKEN BUILD (0.1.1, and 0.1.2 before this fix): no X-SWATGenX-Api-Key header (api_key= raises TypeError; the Client has
no groundwater_at), and the keyless 401 reads 'invalid or revoked'. CONTROLS, both builds: a keyed 401 still says
'invalid or revoked'; a public call (pfas_summary) sends no key. The HTTP layer is mocked; nothing touches the network.
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
        seen.append({"url": url, "headers": headers})
        if url.endswith("/api/gw-wells/at"):
            if not headers.get("X-SWATGenX-Api-Key"):
                return _Resp(401, {"error": "sign_in_required"})
            return _Resp(200, {"found": True, "well_id": "W1"})
        return _Resp(200, {"ok": True})

    monkeypatch.setattr(client.requests, "request", fake)
    monkeypatch.delenv("SWATGENX_API_KEY", raising=False)
    return seen


def _key(call):
    return call["headers"].get("X-SWATGenX-Api-Key")


def test_groundwater_at_sends_the_key_it_is_given(calls):
    assert sg.groundwater_at(42.73, -84.55, api_key="sgx_given")["found"] is True
    assert _key(calls[-1]) == "sgx_given"


def test_groundwater_at_sends_the_environment_key(calls, monkeypatch):
    monkeypatch.setenv("SWATGENX_API_KEY", "sgx_env")
    assert sg.groundwater_at(42.73, -84.55)["found"] is True
    assert _key(calls[-1]) == "sgx_env"


def test_a_client_sends_its_own_key(calls):
    assert sg.Client(api_key="sgx_client").groundwater_at(42.73, -84.55)["found"] is True
    assert _key(calls[-1]) == "sgx_client"


def test_a_keyless_call_says_a_key_is_needed(calls):
    with pytest.raises(sg.SwatGenXError) as e:
        sg.groundwater_at(42.73, -84.55)
    assert e.value.status == 401
    assert "needs an API key" in str(e.value) and "invalid or revoked" not in str(e.value)


def test_control_a_keyed_401_still_says_invalid_or_revoked(monkeypatch):
    # Through Client.whoami, a keyed call both builds have, so the control cannot fail on a missing parameter.
    monkeypatch.setattr(client.requests, "request", lambda *a, **k: _Resp(401, {"error": "bad key"}))
    with pytest.raises(sg.SwatGenXError) as e:
        sg.Client(api_key="sgx_revoked").whoami()
    assert "invalid or revoked" in str(e.value)


def test_control_a_public_call_sends_no_key(calls):
    sg.pfas_summary()
    assert _key(calls[-1]) is None
