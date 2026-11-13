"""Offline: the shipped text of 0.1.5 (README = PyPI's page, the docstrings, the strings the code returns or raises, the 0.1.5
CHANGELOG entry) tells a reader 'build', never 'order', and 'model access', never 'plan' (Lane GM's PIP_PACKAGE_0_1_5_WORDS_2026-11-13.md,
in the site's repository: Lane P's NOTE-O-ORDER-WORD of 2026-11-09 and Q1616). Method, argument and field names stay as they are:
order(), orders(), status(), order_id, paid_plans, pricing_url, free_account.
BROKEN BUILD (3df984165a, the README half alone): words README 0, __init__.py 1, client.py 15, and no 0.1.5 entry; version 0.1.4;
access_info()'s source starts 'Plans are not sold online'; wait()'s timeout reads 'order o1 not terminal after 1 h'.
CONTROLS: a planted prose line 'Order a plan today.' is caught (2 words), an inline-code `order_id` is not, and the .py reader sees a
planted string literal."""
import ast
import pathlib
import re

import pytest

import swatgenx
import swatgenx.client as cm

_PKG = pathlib.Path(swatgenx.__file__).resolve().parent
_ROOT = _PKG.parent.parent

# Lane GM's census (pip_package_0_1_5_words_check_2026-11-13.py.txt): the order words and the Q1616 words.
WORDS = (r"\b(order|orders|ordered|ordering|plan|plans|tier|tiers|pricing|price|prices|priced|free|upgrade|checkout|buy|purchase|"
         r"subscribe|subscription|subscriptions|paid|pay)\b")
# The four sentences the package takes from the site's MCP server (get_access_info and its instructions).
MIRRORS = ("Accounts are by invitation, for a named research collaboration or a funded study.",
           "Building, calibrating and downloading models needs model access or a demo. ",
           "reports your account's access.",
           "The model, data and build tools need model access")


def _prose_md(text):
    """What a reader is shown of a Markdown text: no fenced code, no inline code, no URLs."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    return re.sub(r"\(https?://[^)]*\)|https?://\S+", " ", text)


def _prose_py(src):
    """Every docstring and string literal, less keys and identifiers, API paths, URLs, f-string fields and indented sample code."""
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", s) or s.startswith("/"):
                continue
            s = "\n".join(line for line in s.split("\n") if not line.startswith("    ") or not re.search(r"[=(]", line))
            out.append(re.sub(r"https?://\S+|/api/\S+|\{[^}]*\}", " ", s))
    return "\n".join(out)


def _words(prose):
    return [m.group(0) for m in re.finditer(WORDS, prose, re.I)]


def _read(name):
    return (_ROOT / name).read_text(encoding="utf-8") if name.endswith(".md") else (_PKG / name).read_text(encoding="utf-8")


def test_the_census_sees_a_word_and_spares_code():
    assert _words(_prose_md("# x\n\nOrder a plan today.\n")) == ["Order", "plan"]      # CONTROL: prose is read
    assert _words(_prose_md("# x\n\nPass `order_id` to wait.\n")) == []                # CONTROL: inline code is not
    assert _words(_prose_py('x = "Order a real SWAT+ model build."')) == ["Order"]     # CONTROL: a .py literal is read


def test_no_order_or_plan_word_a_reader_is_shown():
    changelog = _read("CHANGELOG.md")
    assert "## 0.1.5" in changelog                                                     # BROKEN: no 0.1.5 entry
    entry = changelog[changelog.index("## 0.1.5"):changelog.index("## 0.1.4")]
    found = {"README.md": _words(_prose_md(_read("README.md"))),
             "__init__.py": _words(_prose_py(_read("__init__.py"))),
             "client.py": _words(_prose_py(_read("client.py"))),
             "CHANGELOG 0.1.5": _words(_prose_md(entry))}
    assert found == {k: [] for k in found}, found                                      # BROKEN: 0 / 1 / 15


def test_the_mcp_servers_sentences_are_in_the_package():
    text = "\n".join(_read(n) for n in ("README.md", "__init__.py", "client.py"))
    flat = re.sub(r"\s+", " ", re.sub(r'"\s*\n\s*"', "", text))                       # wrapped literals joined
    missing = [s for s in MIRRORS if s not in flat]
    assert missing == [], missing                                                      # BROKEN: M1, M2, M3 (M4 is the README's)


def test_access_info_says_model_access(monkeypatch):
    def not_found(method, path, **kw):
        raise cm.SwatGenXError("not_found", 404, {"error": "not_found"})
    monkeypatch.setattr(cm, "_request", not_found)
    info = cm.access_info()
    assert info["paid_plans"] == [], info                                              # CONTROL: the 404 path was taken
    assert info["source"] == MIRRORS[0], info["source"]                                # BROKEN: 'Plans are not sold online; ...'
    assert info["free_account"]["note"].startswith(MIRRORS[1]), info["free_account"]["note"]
    assert "Client.whoami() reports your account's access." in cm._ACCESS_NOTE, cm._ACCESS_NOTE


def test_wait_timeout_names_the_build(monkeypatch):
    c = cm.Client.__new__(cm.Client)
    monkeypatch.setattr(c, "status", lambda oid: {"status": "success", "order": {"state": "RUNNING"}}, raising=False)
    monkeypatch.setattr(cm.time, "sleep", lambda s: None)
    clock = iter(range(0, 10**9, 4000))
    monkeypatch.setattr(cm.time, "time", lambda: next(clock))
    with pytest.raises(cm.SwatGenXError) as e:
        c.wait("o1", poll_seconds=10, timeout_hours=1)
    assert str(e.value).startswith("build o1 not terminal after 1 h"), str(e.value)   # BROKEN: 'order o1 not terminal ...'


def test_version_is_015():
    assert swatgenx.__version__ == "0.1.5" and 'version = "0.1.5"' in (_ROOT / "pyproject.toml").read_text()
    assert swatgenx.client._UA["User-Agent"] == "swatgenx-python/0.1.5"
