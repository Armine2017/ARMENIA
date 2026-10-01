# 📋 MASTER PROMPT (English) — "Daily Tender Monitor"

> Use this version with AI assistants that perform better in English. Paste everything below the line, unchanged.
> (Հայերեն տարբերակը՝ `prompts/PROMPT-hy.md`։)

---

You are an expert Python developer specializing in web scraping and Windows task automation. I am not a programmer, so give me ready-to-run files and simple step-by-step instructions.

## GOAL

Build me a turn-key "tender monitor" program that:

1. **Every day** at a configured time (default 08:00) automatically checks the websites I list and downloads **only newly published** announcements (tenders, procurement notices, invitations, auctions) — those published since the last check.
2. Saves every announcement on my computer as a separate file (full text `.txt` and/or `.html`), grouped into folders using this scheme:
   `Tenders/<DATE>/<CATEGORY>/<SOURCE>_<TITLE>.txt`
   Categories are decided by keyword lists I define (e.g. "construction", "IT", "medical", "services", "transport").
3. Extracts the key data from each announcement into one shared **Excel/CSV table** with columns:
   - publication date,
   - contracting authority (organisation),
   - **purpose / subject of the procurement** (title + summary),
   - procedure code (if present),
   - bid submission deadline,
   - **phone number(s)**,
   - **email address(es)**,
   - link to the original announcement,
   - path of the saved file.
4. After each run, produces a **daily summary** (how many new items, from which site, in which category), shows it on screen and saves it to a file.
5. Never duplicates work: remembers already-downloaded announcements in a state file (`seen.json`).

## SOURCES (edit this list to my needs)

1. `https://armeps.am/ppcm/public/tenders` — ARMEPS public tenders (Armenia)
2. `https://gnumner.minfin.am/hy/page/norutyunner/` — RA Ministry of Finance announcements
3. `https://procurement.minfin.am/hy/page/hraverum_katarvats_popokhutyunner/440` — changes / invitations
4. <ADD MY OWN SITES HERE, one per line>

Rule for you: first check whether a site offers RSS, an API or a JSON endpoint and use that. Otherwise parse HTML with `requests` + `BeautifulSoup`. If content is rendered by JavaScript, use Playwright in headless mode. Record the chosen method per site in the config file and explain it to me in one sentence.

## TECHNICAL REQUIREMENTS

- Python 3.10+; libraries: `requests`, `beautifulsoup4`, `lxml`, `pandas`, `openpyxl` (Playwright only if needed).
- All my settings in **one config file** (`config.json` or `config.yaml`): site list, categories + keywords, base folder, run time, delay between requests.
- Fault tolerance: if a site is unreachable or its layout changed, write to a log file and **continue with the other sites**; retry each site up to 3 times with a 10 s pause.
- Polite scraping: 1.5–3 s delay between requests, honest User-Agent, never overload a site; download public data only.
- UTF-8 everywhere; write CSV with `utf-8-sig` so Armenian text opens correctly in Excel.
- Sanitise folder/file names against Windows-forbidden characters `\ / : * ? " < > |`.
- Must run on Windows 10/11 with no extra configuration.

## DELIVERABLES (give me all of them)

1. `tender_bot.py` — the main program (single file, commented),
2. `config.json` — settings pre-filled with my sites and categories,
3. `requirements.txt`,
4. `SETUP.bat` — one-click library install,
5. `RUN.bat` — one-click run,
6. `README` — step-by-step instructions with screenshots/diagrams: how to run, where results appear, how to add a new site or category, how to schedule a daily run with Windows Task Scheduler,
7. A test run on one site (or on a local sample HTML file if there is no internet), showing a sample of the table and the folder tree.

## WORKFLOW

Step 1. If anything is unclear, ask me short questions first (which sites, which categories, which folder).
Step 2. Show me the plan (which method per site) and wait for my "yes".
Step 3. Deliver files 1–6.
Step 4. Explain in 5–10 simple steps, with pictures, how to launch it on my computer.
Step 5. If a site changes or the script breaks, I will paste the error text and you will fix it.

## NICE TO HAVE

- Optional e-mail or Telegram notification with the daily summary.
- "Only my keywords" mode: download only announcements containing my words (e.g. "road", "software").
- A one-off "full archive from the beginning" mode.

## IMPORTANT

Explain everything in plain language, no unexplained programming jargon.
