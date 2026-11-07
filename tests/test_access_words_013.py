"""Offline: 0.1.3's access words (Lane GM, PIP_PACKAGE_0_1_3_WORDS_2026-11-01.md P1-P10) and P7's 403 message.

Since 2026-11-01 15:00 UTC every 403 carries the site's own sentence (map data, services, a study), and 0.1.2 replaced it with a
typed note naming /pricing (a 301 now) and 'every plan'. BROKEN BUILD (0.1.2 / c3edc286e1): the 403 test raises the typed note,
not the server's sentence; the phrase census finds 2 'MAX ... Department', 2 'free account', 1 "a free account's API key" and
3 'every plan' in client.py; free_account carries model_orders_per_day."""
import json
import pathlib
import re

import pytest

import swatgenx.client as c

_SRC = pathlib.Path(c.__file__)


class _Resp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.text = json.dumps(body)

    def json(self):
        return self._body


def _serve(monkeypatch, status, body):
    monkeypatch.setattr(c.requests, "request", lambda *a, **kw: _Resp(status, body))


def test_403_raises_the_sites_own_sentence(monkeypatch):
    said = "Map feature data is for verified accounts (example sentence from the site)."
    _serve(monkeypatch, 403, {"status": "error", "message": said})
    with pytest.raises(c.SwatGenXError) as e:
        c.groundwater_at(42.7, -84.5, api_key="k-test")
    assert str(e.value) == said and e.value.status == 403, str(e.value)


def test_403_without_a_message_falls_back_to_the_access_note(monkeypatch):
    _serve(monkeypatch, 429, {"status": "error"})          # CONTROL: no message -> the note, still a SwatGenXError
    with pytest.raises(c.SwatGenXError) as e:
        c.pfas_summary()
    assert str(e.value) == c._ACCESS_NOTE and e.value.status == 429
    assert "access_info() lists the developer plans" in c._ACCESS_NOTE and "/pricing" not in c._ACCESS_NOTE


def test_no_typed_plan_or_free_account_words_remain():
    text = re.sub(r'"\s*\n\s*"', "", _SRC.read_text())   # join wrapped string literals
    text = re.sub(r"\s+", " ", text)
    counts = {p: len(re.findall(p, text)) for p in
              (r"MAX (or|and) Department", r"free account", r"every plan", r"\bStarter\b", r"swatgenx\.com/pricing[\"' ;)]")}
    assert counts == {k: 0 for k in counts}, counts
    assert "swatgenx.com/signup" in text       # CONTROL: the census can see a URL it must keep (0.1.4: /pricing/developer left with the plans)


def test_access_info_free_account_states_no_allowance(monkeypatch):
    payload = {"free_tier": {"models_held_limit": 1, "orders_per_day": 5},
               "plans": [{"plan_name": "starter", "display_name": "Developer", "monthly_price_usd": 100, "models_held_limit": 5}]}
    monkeypatch.setattr(c, "_request", lambda method, path, **kw: payload)
    info = c.access_info()
    assert info["paid_plans"][0]["plan"] == "Developer"   # CONTROL: the payload was read
    assert "model_orders_per_day" not in info["free_account"] and "models_kept" not in info["free_account"], info
    # 0.1.4 re-pin (invitation only, 2026-11-07; was "needs a developer plan or a demo."): the MCP server's Q1616 Am.6 words.
    assert info["free_account"]["note"].startswith("Building, calibrating and downloading models needs an invited account or a demo.")
    assert info["pricing_url"] == "https://www.swatgenx.com/contact"            # 0.1.4 re-pin (was /pricing/developer)
    assert info["calibration"].startswith("Calibration runs on cloud compute from an account's calibration credit")  # 0.1.4 re-pin
    assert info["swat_with_modflow6"].startswith("Part of a study we do for you")
    assert info["api_key"].startswith("Request access at https://www.swatgenx.com/signup")    # 0.1.4 re-pin (was "Request developer access")


def test_client_without_a_key_names_the_request_route(monkeypatch):
    monkeypatch.delenv("SWATGENX_API_KEY", raising=False)
    with pytest.raises(c.SwatGenXError) as e:
        c.Client()
    assert "request developer access at https://www.swatgenx.com/signup" in str(e.value), str(e.value)
