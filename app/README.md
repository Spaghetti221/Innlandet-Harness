# Hamar Reader

Expo app that shows the summaries the harness writes to `out/`, in English and Norwegian.
Opens in Expo Go.

```bash
# from the repo root: one run per summary language (Norwegian into out/no)
python -m harness.hamar_news --once
python -m harness.hamar_news --once --out out/no --config <copy of config.json with "language": "Norwegian (bokmål)">

# turn both runs into app data (add --mock for the mock runs)
python -m harness.hamar_news.export

cd app
npm install
npx expo start   # in a normal terminal, so the QR code shows; add --tunnel if the phone can't connect
```

The data is bundled into the app from `src/data/summaries.json`, which is git-ignored.
Without it, `npm start` uses the synthetic `src/data/sample.json`. Re-run the export and
reload the app to see new summaries.

- The header switch (EN / NO) changes both the interface and the summaries. The choice is
  stored on the phone; the first launch follows the phone's language.
- Deadlines come from the source text ("frist", "innen", "senest"), not from the page's
  expiry date. Reminders are local notifications at 09:00 three days before the deadline.
- Notice types (Have your say, Grant, New plan, Decision, Information) come from keywords
  in the Norwegian title.
