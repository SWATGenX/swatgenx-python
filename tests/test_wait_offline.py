"""Client.wait() ends on the server's terminal order states (offline: status() is stubbed, no network).

The route GET /api/model-orders/<id> returns {"status": "success", "order": {"state": ...}}
(web_application/app/model/order_queue.py, get_model_order_detail). BROKEN-BUILD NUMBERS (client before 2026-10-09):
wait() read a top-level "state", so a SUCCESS order made it poll until the deadline and raise (here: it returns after
3 polls); and with the nesting read, DISPATCHING counted as terminal (here: it keeps polling).
"""
import pytest

import swatgenx.client as cm


def _client(states, monkeypatch):
    seq = iter(states)
    polls = []
    c = cm.Client.__new__(cm.Client)
    monkeypatch.setattr(c, "status", lambda oid: polls.append(oid) or {"status": "success", "order": {"state": next(seq)}},
                        raising=False)
    monkeypatch.setattr(cm.time, "sleep", lambda s: None)
    return c, polls


@pytest.mark.parametrize("terminal", ["SUCCESS", "FAILURE", "CANCELLED", "ORPHANED"])
def test_wait_returns_on_a_nested_terminal_state(terminal, monkeypatch):
    c, polls = _client(["QUEUED_APP", "DISPATCHING", terminal], monkeypatch)
    rec = c.wait("o1", poll_seconds=10, timeout_hours=1)
    assert rec["order"]["state"] == terminal and len(polls) == 3, (rec, polls)


def test_dispatching_and_running_are_not_terminal(monkeypatch):
    c, polls = _client(["DISPATCHING", "RUNNING", "DISPATCHING", "SUCCESS"], monkeypatch)
    c.wait("o1", poll_seconds=10, timeout_hours=1)
    assert len(polls) == 4, polls                       # broken (DISPATCHING terminal): 1


def test_still_raises_at_the_deadline(monkeypatch):
    """RATCHET, not evidence: passes on both builds (the old one ALWAYS ended here)."""
    c, _ = _client(["RUNNING"] * 1000, monkeypatch)
    clock = iter(range(0, 10**9, 4000))
    monkeypatch.setattr(cm.time, "time", lambda: next(clock))
    with pytest.raises(cm.SwatGenXError):
        c.wait("o1", poll_seconds=10, timeout_hours=1)
