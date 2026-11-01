"""access_info() on a fixed payload, offline (no network): the site's BUILD-LIMITS cleanup (2026-10-24).

The site counts the models a plan keeps, not the builds, and no build count refuses an order, so the plans payload no longer carries a
monthly build allowance, the unlimited flag or the free tier's lifetime builds. This row is B10 of the server's registration
(documents/ops/build-limits-cleanup-2026-10-24/REGISTRATION.md in the site's repository).
BROKEN (0.1.2): model_builds_per_month and lifetime_model_builds are read from the payload, so they come back as None or the old figures.
"""
import json

import swatgenx.client as c

_PAYLOAD = {
    "free_tier": {"models_held_limit": 1, "orders_per_day": 5, "storage_limit_bytes": 2 * 1024 ** 3},
    "plans": [
        {"plan_name": "starter", "display_name": "Starter", "monthly_price_usd": 100, "annual_price_usd": 1000, "models_held_limit": 5},
        {"plan_name": "max", "display_name": "MAX", "monthly_price_usd": 200, "annual_price_usd": 2000, "models_held_limit": 20},
        {"plan_name": "department", "display_name": "Department", "quote_only": True, "models_held_limit": None},
    ],
}


def test_access_info_states_models_kept_not_builds(monkeypatch):
    monkeypatch.setattr(c, "_request", lambda method, path, **kw: _PAYLOAD)
    info = c.access_info()
    text = json.dumps(info)
    assert "model_builds_per_month" not in text and "lifetime_model_builds" not in text, text[:300]
    kept = {p["plan"]: p.get("models_kept", "absent") for p in info["paid_plans"]}
    assert kept == {"Starter": 5, "MAX": 20, "Department": None}, kept      # CONTROL: the payload was read
    free = info["free_account"]
    # 0.1.3 (Lane GM P4): no allowance figure; a no-plan, no-demo account is refused every build since 2026-11-01.
    assert "models_kept" not in free and "model_orders_per_day" not in free, free
    assert "refunded" not in free["note"], free
    # MCP-COUPLED-WORDS: an order delivers a steady-state MODFLOW 6 model for the same watershed, not a coupled run. Broken (0.1.2): 'Coupled'.
    assert "coupled" not in text.lower() and "swat_with_modflow6" in info, text[:300]
    assert "in the states we offer" in info["swat_with_modflow6"] and "part of a study" in info["calibration"], info
