# Task 001: Probe one public source

## Goal

`harness/probe.py` fetches the MET Norway weather forecast for Hamar and writes it to `out/probe.json`.

## Context

- Source: MET Norway Locationforecast 2.0, compact, for Hamar (lat 60.7945, lon 11.068):
  https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.7945&lon=11.068
- API docs: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- Terms of service: https://api.met.no/doc/TermsOfService
- Input: `properties.timeseries[]` in the response; each entry has `time`,
  `data.instant.details.air_temperature`, and `data.next_1_hours.summary.symbol_code`
  (fall back to `next_6_hours`, then `next_12_hours`, when it is missing).
- Output: `out/probe.json`, UTF-8:
  ```json
  {"source_url": "https://api.met.no/...",
   "items": [{"title": "<symbol_code>", "date": "<time, ISO 8601>", "air_temperature": 10.8}]}
  ```
- Check: `eval/check_probe.py` (committed before this task; do not edit).

## Constraints

- Do not edit `eval/`
- No personal data; public sources only; follow the source's terms:
  - send an identifying `User-Agent` (app name + contact, e.g. the repo URL); requests without one are blocked
  - cache: honour `Expires`, send `If-Modified-Since` with the stored `Last-Modified`, and do not re-fetch before the cache expires
  - at most 4 decimals in coordinates
- Python 3 standard library only
- Save the raw response as `fixtures/met_hamar.json`; `python3 harness/probe.py --offline` reads it instead of the network

## Acceptance (all must pass)

- `python3 harness/probe.py && python3 eval/check_probe.py` prints PASS
- `python3 harness/probe.py --offline && python3 eval/check_probe.py` prints PASS
- The check failed before this task started (red first)

## Out of scope

Summarisation, scheduling, anything with an LLM (later tasks)
