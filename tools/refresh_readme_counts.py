"""Rewrite the client README's groundwater line from the LIVE API (Lane P 2026-09-29: take every number from the live
API at release time, never typed). Run at commit time and again at the publish; prints the old and new line.
Usage (from clients/python, at every release): python3 tools/refresh_readme_counts.py README.md"""
import datetime
import json
import re
import sys
import urllib.request

path = sys.argv[1]
req = urllib.request.Request("https://www.swatgenx.com/api/gw-wells/summary",
                             headers={"User-Agent": "swatgenx-python-release/0.1.2"})  # the edge refuses urllib's default UA (403)
with urllib.request.urlopen(req, timeout=30) as r:
    d = json.load(r)
wells, intervals, states = int(d["total_wells"]), int(d["total_intervals"]), len(d["states"])
today = datetime.date.today().isoformat()
new = (f"# National groundwater inventory: {intervals / 1e6:.1f}M lithology intervals, {wells / 1e6:.2f}M wells, "
       f"{states} states (as of {today}; sg.groundwater_summary() returns the live totals)")
s = open(path, encoding="utf-8").read()
pat = re.compile(r"^# National groundwater inventory:.*$", re.M)
old = pat.findall(s)
if len(old) != 1:
    sys.exit(f"REFUSE: expected exactly one groundwater line, found {len(old)}")
open(path, "w", encoding="utf-8").write(pat.sub(new, s))
print("old:", old[0])
print("new:", new)
print(f"source: /api/gw-wells/summary total_wells={wells} total_intervals={intervals} states={states}")
