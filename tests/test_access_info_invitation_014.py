"""0.1.4: access_info() after the site became invitation only (2026-11-07), offline (no network).

Since the site's Q1616 server half, /api/billing/plans answers 404 ('not_found'): plans are not sold online. 0.1.3 called _request on it
and raised SwatGenXError('not_found') to every caller (the scheduled live run of 2026-11-07 12:58 UTC failed on exactly that). 0.1.4
never raises there, and its words are the site's own MCP get_access_info words (Q1616 Am.6), so a pip user and an agent read one rule.
BROKEN (0.1.3): R1 raises SwatGenXError; R2 returns price_usd_per_month 100/200, a 'price' and the free-text notes.
"""
import json

import pytest

import swatgenx.client as c

INVITE = ("Plans are not sold online; accounts are by invitation, for a named research collaboration or a funded study.")


def _not_found(method, path, **kw):
    raise c.SwatGenXError("not_found", 404, {"error": "not_found"})


def test_R1_a_404_from_the_plans_api_is_not_an_error(monkeypatch):
    monkeypatch.setattr(c, "_request", _not_found)
    info = c.access_info()                                   # BROKEN: raises SwatGenXError('not_found')
    assert info["paid_plans"] == [] and info["source"] == INVITE, info
    assert info["pricing_url"] == "https://www.swatgenx.com/contact", info
    text = json.dumps(info)
    assert "$" not in text and "price_usd" not in text and "pricing/developer" not in text, text[:300]


def test_R1b_other_errors_still_raise(monkeypatch):
    """Control: only the plans API's 404 is read as 'not sold online'; a 500 or a network failure still reaches the caller."""
    def boom(method, path, **kw):
        raise c.SwatGenXError("HTTP 500", 500, {})
    monkeypatch.setattr(c, "_request", boom)
    with pytest.raises(c.SwatGenXError):
        c.access_info()


def test_R2_a_plans_payload_with_prices_never_reaches_the_caller(monkeypatch):
    payload = {"plans": [
        {"plan_name": "starter", "display_name": "Developer", "monthly_price_usd": 100, "models_held_limit": 5,
         "notes": "One account, $100/month"},
        {"plan_name": "max", "display_name": "Developer Pro", "monthly_price_usd": 200, "models_held_limit": 20},
        {"plan_name": "department", "display_name": "Department", "quote_only": True, "models_held_limit": None},
    ]}
    monkeypatch.setattr(c, "_request", lambda method, path, **kw: payload)
    info = c.access_info()
    text = json.dumps(info)
    # BROKEN: price_usd_per_month 100 and 200, 'price': 'by quote...', and the notes with '$100/month'.
    assert "$" not in text and "price" not in json.dumps(info["paid_plans"]) and "notes" not in json.dumps(info["paid_plans"]), text
    kept = {p["plan"]: p["models_kept"] for p in info["paid_plans"]}
    assert kept == {"Developer": 5, "Developer Pro": 20, "Department": None}, kept     # CONTROL: the payload was read
    assert info["source"] == "live: https://www.swatgenx.com/api/billing/plans"


def test_R3_the_access_words_are_the_mcp_servers(monkeypatch):
    monkeypatch.setattr(c, "_request", _not_found)
    info = c.access_info()
    # BROKEN: 'needs a developer plan or a demo' and 'Request developer access ... once we have verified you'.
    assert info["free_account"]["note"] == ("Building, calibrating and downloading models needs an invited account or a demo. "
                                            "Request access at https://www.swatgenx.com/signup.")
    assert info["calibration"] == ("Calibration runs on cloud compute from an account's calibration credit; credit is not sold "
                                   "online. Calibration we do for you is part of a study.")
    assert "developer plan" not in json.dumps(info).lower()
