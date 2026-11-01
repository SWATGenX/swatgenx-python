"""Offline: the shipped text of 0.1.3 (README = PyPI's page, the docstrings, the 0.1.3 CHANGELOG entry, PyPI's summary) says what
the site does since 2026-11-01 (Lane GM's PIP_PACKAGE_0_1_3_WORDS_2026-11-01.md Am.3, 1cb85a773b + 3c3f93ceab).
BROKEN BUILD (1b4395d8b6): 'free account' 4, '25-station' 3, 'Starter' 2, 'MAX' 2, 'every plan' 1 and 'open national' 2 across these
files; version 0.1.2. CONTROLS: 'pip install swatgenx' 1 in the README, the MCP URL in README and __init__, and the CHANGELOG's one
allowed '25-station' (the preview is gone)."""
import pathlib
import re

import swatgenx

_PKG = pathlib.Path(swatgenx.__file__).resolve().parent
_ROOT = _PKG.parent.parent


def _flat(text):
    return re.sub(r"\s+", " ", text)


def _shipped():
    changelog = (_ROOT / "CHANGELOG.md").read_text()
    head = "## 0.1.3" if "## 0.1.3" in changelog else "## Unreleased"   # the broken build has no 0.1.3 entry yet
    a = changelog.index(head); b = changelog.index("## 0.1.2")
    desc = re.search(r'^description = "(.*)"$', (_ROOT / "pyproject.toml").read_text(), re.M).group(1)
    return {"README.md": (_ROOT / "README.md").read_text(), "__init__.py": swatgenx.__doc__,
            "client.py": swatgenx.client.__doc__, "CHANGELOG 0.1.3": changelog[a:b], "pyproject description": desc}


def test_no_old_access_words_in_the_shipped_text():
    found = {}
    for name, text in _shipped().items():
        flat = _flat(text)
        for pat in (r"free account", r"\bStarter\b", r"\bMAX\b", r"every plan", r"open national", r"/MODFLOW",
                    r"swatgenx\.com/pricing\)", r"25-station"):
            n = len(re.findall(pat, flat))
            if pat == r"25-station" and name == "CHANGELOG 0.1.3" and "## 0.1.3" in text:
                assert n == 1, (name, n)     # CONTROL: the one allowed copy ('the keyless 25-station preview is gone')
                continue
            if n:
                found[(name, pat)] = n
    assert found == {}, found


def test_controls_and_version():
    s = _shipped()
    assert s["README.md"].count("pip install swatgenx") == 1
    assert "https://www.swatgenx.com/mcp" in s["README.md"] and "https://www.swatgenx.com/mcp" in s["__init__.py"]
    assert swatgenx.__version__ == "0.1.3" and 'version = "0.1.3"' in (_ROOT / "pyproject.toml").read_text()
    assert swatgenx.client._UA["User-Agent"] == "swatgenx-python/0.1.3"
