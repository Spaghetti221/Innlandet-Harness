import json
from datetime import datetime

data = json.load(open("out/probe.json", encoding="utf-8"))
assert data["source_url"].startswith("https://")
assert len(data["items"]) >= 1, "no items"
for it in data["items"]:
    assert it["title"].strip(), "empty title"
    d = it["date"].replace("Z", "+00:00")
    datetime.fromisoformat(d)
    # Domain: MET Norway forecast for Hamar, plausible air temperature (°C)
    t = it["air_temperature"]
    assert isinstance(t, (int, float)) and -60 <= t <= 50, f"bad temperature {t!r}"
assert "api.met.no" in data["source_url"], "not the MET Norway API"
print("PASS")
