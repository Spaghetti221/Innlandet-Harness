"""Task 001: fetch the MET Norway forecast for Hamar and write out/probe.json.

Usage:
    python3 harness/probe.py            # network, honouring MET's cache rules
    python3 harness/probe.py --offline  # read fixtures/met_hamar.json instead
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "met_hamar.json"
OUT = ROOT / "out" / "probe.json"
CACHE_META = ROOT / "out" / "met_cache.json"  # stores Expires / Last-Modified

# Hamar; MET terms allow at most 4 decimals in coordinates
SOURCE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.7945&lon=11.068"
USER_AGENT = "Innlandet-Harness/0.1 https://github.com/Spaghetti221/Innlandet-Harness"


def load_meta():
    try:
        return json.loads(CACHE_META.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def cache_is_fresh(meta):
    expires = meta.get("expires")
    if not expires or not FIXTURE.exists():
        return False
    try:
        return parsedate_to_datetime(expires) > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False


def fetch():
    """Return the raw forecast, re-fetching only when MET's cache has expired."""
    meta = load_meta()
    if cache_is_fresh(meta):
        print(f"cache fresh until {meta['expires']}; not re-fetching", file=sys.stderr)
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if meta.get("last_modified") and FIXTURE.exists():
        headers["If-Modified-Since"] = meta["last_modified"]

    req = urllib.request.Request(SOURCE_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            resp_headers = resp.headers
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_bytes(body)
        print("fetched new forecast (200)", file=sys.stderr)
    except urllib.error.HTTPError as e:
        if e.code != 304:
            raise
        resp_headers = e.headers
        print("forecast not modified (304); using stored copy", file=sys.stderr)

    meta = {
        "expires": resp_headers.get("Expires", meta.get("expires")),
        "last_modified": resp_headers.get("Last-Modified", meta.get("last_modified")),
    }
    CACHE_META.parent.mkdir(parents=True, exist_ok=True)
    CACHE_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def symbol_code(data):
    for period in ("next_1_hours", "next_6_hours", "next_12_hours"):
        code = data.get(period, {}).get("summary", {}).get("symbol_code")
        if code:
            return code
    return None


def to_items(raw):
    items = []
    for entry in raw["properties"]["timeseries"]:
        code = symbol_code(entry["data"])
        temp = entry["data"].get("instant", {}).get("details", {}).get("air_temperature")
        if code is None or temp is None:
            continue
        items.append({"title": code, "date": entry["time"], "air_temperature": temp})
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help=f"read {FIXTURE.relative_to(ROOT)}")
    args = parser.parse_args()

    raw = json.loads(FIXTURE.read_text(encoding="utf-8")) if args.offline else fetch()
    result = {"source_url": SOURCE_URL, "items": to_items(raw)}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(result['items'])} items to {OUT.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
