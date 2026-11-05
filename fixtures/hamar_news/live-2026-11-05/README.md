# Saved real inputs, 05.11.2026

Ten public notices from <https://www.hamar.kommune.no/lokaldemokrati/>, as fetched by run 4 on
05.11.2026 and cleaned by the harness (names, e-mail addresses and phone numbers replaced; the
page author never read). The raw HTML is not kept. The eleventh article on the page that day was
rejected because its title names people, so it is not here.

They make runs reproducible after the live articles expire:

    python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --out out/replay
    python eval/check_summaries.py --out out/replay

Only what the evaluation needs is kept: title, lead, body text and the page's dates.
