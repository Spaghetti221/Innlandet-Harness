# Hamar Reader

Expo app that shows the summaries the harness writes to `out/`, in English and Norwegian.
Opens in Expo Go.

Needs Node.js (LTS) and the Expo Go app on the phone.

```bash
# from the repo root: export a run (here the offline eval run) into app data
python -m harness.hamar_news.export --run out/eval
# optional: also a Norwegian run, then export both (one --run per language)
#   python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --out out/eval-no \
#       --config <copy of config.json with "language": "Norwegian (bokmål)">
#   python -m harness.hamar_news.export --run out/eval --run out/eval-no

cd app
npm install      # first time only
npm start        # QR code: scan with the phone (same Wi-Fi), or press w for the browser
```

If the phone cannot connect, use `npx expo start --tunnel`. Press `r` to reload after a new export.

### Testing

- `npm run lint` and `npx tsc --noEmit` in `app/`; `python -m pytest tests/test_export.py` in the repo root.
- By hand: list shows type and deadline for each notice; EN/NO switch; warning on a summary that
  failed the check; detail view with bullets and a link to the original; reminder three days before
  the deadline (phone only).

The data is bundled into the app from `src/data/summaries.json`, which is git-ignored.
Without it, `npm start` uses the synthetic `src/data/sample.json`. Re-run the export and
reload the app to see new summaries.

- The header switch (EN / NO) changes both the interface and the summaries. The choice is
  stored on the phone; the first launch follows the phone's language.
- Deadlines come from the source text ("frist", "innen", "senest"), not from the page's
  expiry date. Reminders are local notifications at 09:00 three days before the deadline.
- Notice types (Have your say, Grant, New plan, Decision, Information) come from keywords
  in the Norwegian title.
