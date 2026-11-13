"""Offline: the shipped text of 0.1.4 (README = PyPI's page, the docstrings, the 0.1.4 CHANGELOG entry, PyPI's summary) says what the
site does since it became invitation only on 2026-11-07 (Lane GM's PIP_PACKAGE_0_1_4_WORDS_2026-11-07.md, in the site's repository).
BROKEN BUILD (2dfa686017, the code half alone): 'developer plan' 4/2/2 (README/__init__/client.py), 'developer access' 1/1/1,
'verified you' 1/1/0, 'pricing/developer' 2/0/0, 'Department' 1/0/0, 'Plans and access' 2/0/0, 'invitation' 0/0/3; no 0.1.4 entry;
version 0.1.3. CONTROLS: 'pip install swatgenx' 1 in the README, the MCP URL in README and __init__, swatgenx.com/signup found."""
import pathlib
import re

import swatgenx

_PKG = pathlib.Path(swatgenx.__file__).resolve().parent
_ROOT = _PKG.parent.parent


def _flat(text):
    return re.sub(r"\s+", " ", text)


def _shipped():
    changelog = (_ROOT / "CHANGELOG.md").read_text()
    a = changelog.index("## 0.1.4"); b = changelog.index("## 0.1.3")
    desc = re.search(r'^description = "(.*)"$', (_ROOT / "pyproject.toml").read_text(), re.M).group(1)
    src = re.sub(r'"\s*\n\s*"', "", (_PKG / "client.py").read_text())     # the whole client.py, wrapped literals joined
    return {"README.md": (_ROOT / "README.md").read_text(), "__init__.py": swatgenx.__doc__, "client.py": src,
            "CHANGELOG 0.1.4": changelog[a:b], "pyproject description": desc}


def test_no_plan_sale_words_in_the_shipped_text():
    found = {}
    for name, text in _shipped().items():
        flat = _flat(text)
        for pat in (r"developer plan", r"developer access", r"verified you", r"pricing/developer", r"\bDepartment\b",
                    r"Plans and access", r"\$\d"):
            n = len(re.findall(pat, flat, re.I))
            if n:
                found[(name, pat)] = n
    assert found == {}, found


def test_the_invitation_words_and_controls():
    s = _shipped()
    count = {k: len(re.findall(r"invitation", _flat(v), re.I)) for k, v in s.items() if k in ("README.md", "__init__.py", "client.py")}
    assert count == {"README.md": 2, "__init__.py": 1, "client.py": 3}, count
    # 0.1.5 re-pin (Lane GM's 0.1.5 words; was "reports your account's plan"): the MCP server's access_note.
    assert "Client.whoami() reports your account's access" in _flat(s["client.py"])
    assert s["README.md"].count("pip install swatgenx") == 1                                   # CONTROL
    assert "https://www.swatgenx.com/mcp" in s["README.md"] and "https://www.swatgenx.com/mcp" in s["__init__.py"]
    assert "swatgenx.com/signup" in s["README.md"] and "swatgenx.com/signup" in s["__init__.py"]   # CONTROL: the census sees URLs


def test_version_moved_to_015():
    # The version rows moved to test_shipped_text_015.py (0.1.5); this file keeps the 0.1.4 entry's census.
    assert swatgenx.__version__ != "0.1.3"
