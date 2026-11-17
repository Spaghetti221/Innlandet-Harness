# Oversikt over programmet (per 17.11.2026)

Innlandet Harness henter nye kunngjøringer fra <https://www.hamar.kommune.no/lokaldemokrati/>,
fjerner personopplysninger, oppsummerer dem med en lokal språkmodell (Llama 3.2 3B via Ollama),
sjekker resultatet med kode og prøver på nytt med tilbakemelding. Oppsummeringene kan eksporteres
til mobilappen Hamar Reader. Mål og suksesskriterier står i [SPEC.md](../SPEC.md).

## Dataflyt

```
listeside ──fetch──▶ artikkel-URL-er ──fetch──▶ HTML
   │                                              │
   │                                    extract (+ names: fjern navn, e-post, telefon;
   │                                              anonymiser artikler med navn i tittelen)
   ▼                                              ▼
robots.txt / Crawl-delay 5 s           Article (renset) ──store──▶ out/source/*.json, out/text/*.txt
                                                  │
                         summarise (system-prompt + glossar + hint)  ◀───────────────┐
                                                  │                                   │
                                     check.validate_summary ── feil ──▶ ny runde med │
                                                  │              problemene (maks 3) ─┘
                                                  ▼ ok / gir opp
                                 out/summaries/*.md, out/attempts/, state.json, INDEX.md
                                                  │
                                    export ──▶ app/src/data/summaries.json ──▶ Hamar Reader
```

## Viktige mapper

| Mappe / fil | Innhold |
|---|---|
| `harness/hamar_news/` | Selve programmet (moduler beskrevet under) |
| `harness/hamar_news/prompts/` | `summarise_system.md` (system-prompten, 9 regler), `translate_title_system.md` (tittelprompten) og `glossary_en.md` (faste engelske fagord) |
| `harness/hamar_news/data/first_names.txt` | Fornavnsliste brukt av navneregel 1 og NER-filteret |
| `harness/probe.py` | Task 001: henter værvarsel for Hamar fra MET (kun standardbiblioteket) |
| `eval/` | `check_summaries.py` og `check_probe.py`. **Endres ikke uten avtale** |
| `fixtures/hamar_news/live-2026-11-05/` | Ti ekte, rensede kunngjøringer for offline eval-kjøringer (`--replay`) |
| `fixtures/hamar_news/*.html`, `fixtures/met_hamar.json` | Syntetiske sider og lagret værvarsel for testene |
| `tests/` | 114 offline tester (se *Tester*) |
| `tasks/` | Én fil per oppgave med akseptkriterier (001–014) |
| `config.json` | Språk, modell, intervaller, forsinkelse, antall forsøk |
| `out/` | Alle kjøringer (git-ignorert): `summaries/`, `attempts/`, `source/`, `text/`, `state.json`, `check.json`, `run.log`; mock-kjøringer under `out/<kjøring>/mock/` |
| `app/` | Hamar Reader (Expo/React Native) |
| `docs/` | Prompt-logger, møtereferater, denne oversikten |
| `report/c2/` | Rapporten for Compulsory 2 (LaTeX) |

## Moduler og funksjoner

### `__main__.py`: kommandolinjen
- `parse_args`: flagg: `--once`, `--mock`, `--replay DIR`, `--profile`, `--interval`, `--language`, `--set-language`, `--config`, `--out`.
- `main`: setter opp logging, lagrer språk, krever NER for ekte kjøringer (stopper med kode 2 ellers), og starter én runde, replay eller pollingløkka.

### `config.py`: innstillinger
- `load_config`: standardverdier + `config.json` + `OLLAMA_URL` fra miljøet / `.env`.
- `save_config`, `set_language`: lagrer bare språket (aldri verdier fra `.env`).
- `interval_for`: pollingintervall for en profil (`prod` 6 t, `test` 30 s).
- `_load_env_file`: enkel `.env`-leser; eksisterende miljøvariabler vinner.

### `fetch.py`: høflig henting
- `is_article_url`, `normalise_url`, `slug_of`: kjenner igjen og normaliserer artikkel-URL-er.
- `digest`, `anonymous_slug`: kort hash / `anon-<hash>` for artikler med navn i URL-en.
- `article_links`, `pagination_links`, `discover_articles`: finner artikler på listesidene.
- `Fetcher.get`: følger `robots.txt` og `Crawl-delay`, og prøver én gang til ved brutt tilkobling. `Fetcher._allowed` leser `robots.txt` én gang.

### `extract.py`: fra HTML til renset artikkel
- `Article` (med `text`): tittel, ingress, brødtekst og datoer; aldri forfatter eller rå HTML.
- `is_article_page`, `_meta`, `element_text`: plukker ut artikkelinnholdet.
- `scrub_contact_details`, `scrub_personal_data`: erstatter e-post, telefon og navn med faste engelske plassholdere: `[email removed]`, `[phone removed]`, `[name removed]`.
- `english_placeholders`, `load_saved_article`: gjør om de norske plassholderne i kjøringer fra før 18.11, slik at gamle kjøringer kan sjekkes på nytt.
- `extract_article`: alt over; ved navn i tittelen blir slug `anon-<hash>` og lenken listesiden.

### `names.py`: fjerning av personnavn (fire lag)
1. Kjent fornavn (også med bindestrek) + 1–3 ord med stor forbokstav.
2. Ord etter et stikkord som «rettes til», «kontaktperson», «saksbehandler».
3. Ord rett før en kontaktdetalj («…, e-post:»).
4. Ord koblet med «og»/«,» til et navn som alt er fjernet.
5. I tillegg: spaCy NER (`nb_core_news_md` / `en_core_web_sm`), filtrert av `accept_ner_span`.

- `_spans`: slår sammen treff fra alle lag. `scrub_person_names`: erstatter dem og leter på nytt (maks 3 runder).
- `find_person_names`, `has_person_name`: brukes av sjekken og eksporten.
- `_ner_model`, `ner_available`, `require_ner`, `ner_lang`: laster modellene; ekte kjøringer stopper uten dem.

### `summarise.py`: modellen
- `system_prompt`: prompten med språk, pluss glossaret for engelsk.
- `build_hints`: påminnelser etter artikkelen (språk, flat liste, ansvarlig organ).
- `build_messages`: samtalen til modellen; ved nytt forsøk følger forrige svar og problemene med.
- `truncate`: kutter for lange artikler ved avsnitt eller setning.
- `needs_title_translation`, `title_messages`: eget, kort kall for tittelen når språket ikke er norsk (task 014).
- `OllamaSummariser.summarise` / `.translate_title`: kaller Ollama lokalt (temperatur 0,2). `MockSummariser`: faste svar uten modell.

### `check.py`: sjekk uten modell (Nivå 1 i SPEC)
- `validate_summary`: alle sjekker for én oppsummering. Disse sendes tilbake til modellen ved feil: form (3–6 flate punkter), kontaktinfo, personnavn, språk, ansvarlig organ, egne plassholdere, uoversatte glossarord, oppdiktede datoer, frist bevart.
- Hjelpere: `find_dates`, `date_in_source`, `source_deadlines`, `language_problem`, `source_actors`, `responsible_body_problem`, `placeholder_problem`, `untranslated_problems`.
- `clean_title`, `title_problems`: rydder bort anførselstegn og «Title:», og sjekker en oversatt tittel (én linje, oversatt, navn, datoer, plassholdere, glossar).
- `check_article`, `check_run`, `main`: sjekker en hel kjøring (topptekst, lenke, datoer, én fil per artikkel) og skriver `check.json`. Exit 0/1.

### `pipeline.py`: arbeidsflyten
- `run_once`: én runde mot nettsiden.
- `run_replay`: samme løp fra lagrede fixtures, uten nett.
- `process_article`: lagrer, oppsummerer og skriver én artikkel.
- `summarise_checked`: løkka med forsøk og sjekk.
- `translate_title_checked`: samme løkke for tittelen; består ingen, brukes den norske tittelen.
- `run_forever`: polling; en feilet runde stopper ikke løkka.

### `store.py`: filer på disk
- `Store`: `is_done`, `mark_skipped`, `mark_done`, `save_source`, `save_text`, `save_attempt`, `write_summary`, `write_index`. Holder `state.json` (også `title_translated`), slik at ingen artikkel oppsummeres to ganger. Oversatt tittel blir overskrift, med `Original title:` under; filnavnet beholder slugen.

### `export.py`: til appen
- `export_runs`, `main`: lager `app/src/data/summaries.json` av én eller flere kjøringer; hopper over oppsummeringer med navn. Hvert språk får sin egen `title`; appen viser den via `titleFor()`.
- `kind_of` (høring/tilskudd/plan/vedtak), `language_code`, `parse_bullets`, `deadline_from_source`.

### `harness/probe.py`: task 001 (MET)
- `fetch`: respekterer MET sine cache-regler (`Expires`, `If-Modified-Since`, 304).
- `load_meta`, `cache_is_fresh`, `symbol_code`, `to_items`, `main` (`--offline`).

## Tester

`python -m pytest`: 114 tester, alle offline. Dekning av `harness/` er 97 %; alle funksjoner kjøres minst én gang. Det som gjenstår er stort sett `if __name__ == "__main__"`.

| Fil | Dekker |
|---|---|
| `test_hamar_news.py` | URL-filter, listesider, uttrekk, state, replay-fixtures uten personopplysninger |
| `test_check.py` | Alle sjekkene, retry med tilbakemelding, feil på kjøringsnivå (manglende state, foreldreløse filer, duplikater, topptekst, lenke, datoer) |
| `test_names.py` | Alle navnelag, NER-filteret, anonymisering, glossar, hint |
| `test_cli.py` | Kommandolinjen, config og `.env`, pollingløkka, Ollama-klienten, `truncate`, stopp når modellserveren er nede |
| `test_probe.py` | MET-proben: cache, 200, 304, andre feil, `--offline` |
| `test_title.py` | Tittel-oversettelse: prompt, opprydding, sjekk, nye forsøk, fallback til norsk, topptekst og eksport |
| `test_export.py` | Eksport til appen |
| `test_politeness.py` | `robots.txt`, Crawl-delay, nytt forsøk etter brutt tilkobling |

Testdekning måles med:

```
python -m coverage run --source=harness -m pytest
python -m coverage report -m
```

Appen (`app/`) har ingen tester ennå, bare `npm run lint`.

## Vanlige kommandoer

| Hva | Kommando |
|---|---|
| Tester | `python -m pytest` |
| Røyktest uten modell | `python -m harness.hamar_news --once --mock` |
| Eval-kjøring (offline input, ekte modell) | `python -m harness.hamar_news --replay fixtures/hamar_news/live-2026-11-05 --out out/<navn>` |
| Sjekk en kjøring | `python eval/check_summaries.py --out out/<navn>` |
| Live-kjøring | `python -m harness.hamar_news --once --out out/<navn>` |
| Bytt språk | `python -m harness.hamar_news --set-language Norwegian` |
| Eksport til appen | `python -m harness.hamar_news.export --run out/<navn>` |
| MET-proben | `scripts/check.sh` eller `scripts/check.sh --offline` |

Bruk en ny `--out`-mappe når du vil sammenligne kjøringer; `state.json` gjør at ferdige artikler hoppes over.
