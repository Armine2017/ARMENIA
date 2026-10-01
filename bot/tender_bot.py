#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ՏԵԴԵՐԱՅԻՆ ՄՈՆԻՏՈՐ — ամենօրյա ավտոմատ բեռնիչ
=================================================
Ինչ է անում.
  * Ստուգում է config.json-ում նշված կայքերը,
  * գտնում է ՄԱՅՆ ՆՈՐ հայտարարությունները (հին չի կրկնում),
  * պահպանում է դրանք թղթապանակներում`  data/<ԱՄՍԱԹԻՎ>/<ԿԱՏԵԳՈՐԻԱ>/...,
  * դուրս է գրում հեռախոսները, էլ. փոստները, նպատակը և այլն CSV աղյուսակում` reports/,
  * տպում է օրական ամփոփագիր։

Գործարկում.
  python tender_bot.py            # մեկ անգամ ստուգել բոլոր կայքերը
  python tender_bot.py --demo     # փորձնական ռեժիմ` առանց ինտերնետի (լոկալ օրինակներով)
  python tender_bot.py --loop     # մնում է բաց և ամեն օր config-ի run_time-ին աշխատում
  python tender_bot.py --reset    # մաքրում է «արդեն բեռնված»-ների հիշողությունը (ամբողջ արխիվ)

Հեղինակային նշում. սա «սկզբնական կիտ» է, որը կարող եք տալ AI օգնականին` ձեր կայքերին հարմարեցնելու համար։
"""

import argparse
import csv
import datetime as dt
import hashlib
import html as htmllib
import json
import logging
import re
import sys
import time
import urllib.request
from urllib.parse import urljoin
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG_PATH = BASE / "config.json"
SEEN_PATH = BASE / "seen.json"
LOG_DIR = BASE / "logs"

# ---------------------------------------------------------------- կարգավորումներ
DEFAULT_CONFIG = {
    "run_time": "08:00",                 # ամենօրյա գործարկման ժամը (--loop ռեժիմի համար)
    "delay_seconds": 2,                  # դադար հարցումների միջև (քաղաքավարի սկրեյպինգ)
    "fetch_detail_pages": True,          # բացել նաև ամեն հայտարարության էջը (հեռախոս/էլ.փոստ գտնելու համար)
    "only_keywords": [],                 # օր. ["ճանապարհ", "ծրագրակազմ"] — դատարկ = բոլորը
    "sources": [
        {"name": "ARMEPS", "url": "https://armeps.am/ppcm/public/tenders", "kind": "html"},
        {"name": "MinFin", "url": "https://gnumner.minfin.am/hy/page/norutyunner/", "kind": "html"},
    ],
    "categories": {
        "Շինարարություն": ["շին", "կառուց", "վերանորոգ", "շենք", "construction"],
        "ՏՏ և ծրագրակազմ": ["համակարգչ", "ծրագր", "սերվեր", "տեղեկատվական", "ինտերնետ",
                            "ցանց", "software", "server"],
        "Բժշկական": ["բժշկ", "դեղ", "հիվանդանոց", "բուժ", "կլինիկ", "լաբորատոր"],
        "Տրանսպորտ": ["տրանսպորտ", "մեքենա", "ճանապարհ", "վառելիք", "ավտոբուս"],
        "Ծառայություններ": ["ծառայություն", "սպասարկում", "խորհրդատվ", "մաքր"],
        "Այլ": [],
    },
}

CSV_COLUMNS = [
    "Ամսաթիվ", "Աղբյուր", "Կատեգորիա", "Կազմակերպություն", "Նպատակ / Վերնագիր",
    "Ծածկագիր", "Վերջնաժամկետ", "Հեռախոս", "Էլ. փոստ", "Հղում", "Պահպանված ֆայլ",
]

# ------------------------------------------------- տվյալների դուրսգրման կանոններ
PHONE_RE = re.compile(
    r"(?:\+374[\s.\-]?\d{2}[\s.\-]?\d{3}[\s.\-]?\d{3}"
    r"|\(\+374[\s.\-]?\d{2}\)[\s.\-]?\d{3}[\s.\-]?\d{3}"
    r"|0\d{2}[\s.\-]?\d{3}[\s.\-]?\d{3})"
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
DATE_RE = re.compile(r"\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}")
CODE_RE = re.compile(r"[A-ZԱ-Ֆ0-9]{2,}[‐\-–/][A-ZԱ-Ֆ0-9/‐\-–]{4,}")
ORG_RE = re.compile(r"(?:Պատվիրատու|պատվիրատու|Կազմակերպություն|կազմակերպություն)\s*[:\-–՝]?\s*([^,\n]{3,80})")
DEADLINE_RE = re.compile(r"(?:ժամկետ|մինչև|deadline)\D{0,40}?(\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4})", re.I)

log = logging.getLogger("tender_bot")


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    fh = logging.FileHandler(LOG_DIR / f"run-{dt.datetime.now():%Y-%m-%d_%H%M%S}.log", encoding="utf-8")
    sh = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    log.setLevel(logging.INFO)
    log.addHandler(fh)
    log.addHandler(sh)


def load_config():
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Ստեղծվեց նոր config.json — կարող եք խմբագրել այն Notepad-ով։")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for key, val in DEFAULT_CONFIG.items():
        cfg.setdefault(key, val)
    return cfg


def load_seen():
    if SEEN_PATH.exists():
        return json.loads(SEEN_PATH.read_text(encoding="utf-8"))
    return {}


def sanitize(name, limit=60):
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:limit] or "անանուն"


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "TenderMonitor/1.0 (personal use; contact: admin@example.com)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    enc = resp.headers.get_content_charset() if resp.headers else None
    return raw.decode(enc or "utf-8", errors="replace")


def fetch(url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            return http_get(url)
        except Exception as exc:  # ցանկացած սխալ` գրում ենք log և փորձում նորից
            log.warning("Չհաջողվեց բացել %s (փորձ %d/%d): %s", url, attempt, retries, exc)
            time.sleep(10 if attempt < retries else 0)
    return None


def strip_tags(fragment):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", htmllib.unescape(text)).strip()


# ------------------------------------------------------------------ վերլուծություն
def parse_html_items(page_html, base_url):
    """Գտնում է հայտարարությունների հղումները (վերնագրով <a> պիտակներ)։"""
    items = []
    for href, inner in re.findall(r"<a[^>]+href=[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", page_html, re.S | re.I):
        title = strip_tags(inner)
        if len(title) < 12:
            continue
        url = href if href.startswith(("http://", "https://")) else urljoin(base_url, href)
        items.append({"title": title, "url": url, "snippet": title})
    # պահպանում ենք առաջին հանդիպումը
    uniq, seen_urls = [], set()
    for it in items:
        if it["url"] not in seen_urls:
            seen_urls.add(it["url"])
            uniq.append(it)
    return uniq


def parse_rss_items(page_xml):
    items = []
    for block in re.findall(r"<(?:item|entry)[^>]*>(.*?)</(?:item|entry)>", page_xml, re.S | re.I):
        title = strip_tags(re.search(r"<title[^>]*>(.*?)</title>", block, re.S | re.I).group(1)) if re.search(r"<title[^>]*>(.*?)</title>", block, re.S | re.I) else ""
        link_m = re.search(r"<link[^>]*href=[\"']([^\"']+)[\"']", block, re.I) or re.search(
            r"<link[^>]*>(?:<!\[CDATA\[)?\s*([^>\]]*?)\s*(?:\]\]>)?</link>", block, re.S | re.I)
        desc_m = re.search(r"<(?:description|summary)[^>]*>(.*?)</(?:description|summary)>", block, re.S | re.I)
        items.append({
            "title": title,
            "url": (link_m.group(1).strip() if link_m else ""),
            "snippet": strip_tags(desc_m.group(1))[:600] if desc_m else title,
        })
    return [i for i in items if i["title"]]


def extract_fields(text):
    phones = sorted(set(PHONE_RE.findall(text)))
    emails = sorted(set(m.lower() for m in EMAIL_RE.findall(text)))
    org_m = ORG_RE.search(text)
    dead_m = DEADLINE_RE.search(text)
    date_m = DATE_RE.search(text)
    # ծածկագիրը պետք է պարունակի գոնե մեկ տառ և չլինի ամսաթիվ
    code = ""
    for candidate in CODE_RE.findall(text):
        if re.search(r"[A-Za-zԱ-Ֆա-ֆ]", candidate) and not DATE_RE.fullmatch(candidate.strip()):
            code = candidate
            break
    return {
        "phones": "; ".join(phones[:6]),
        "emails": "; ".join(emails[:6]),
        "org": org_m.group(1).strip() if org_m else "",
        "deadline": dead_m.group(1) if dead_m else "",
        "code": code,
        "date": date_m.group(0) if date_m else "",
    }


def categorize(cfg, text):
    low = text.lower()
    for cat, words in cfg["categories"].items():
        for w in words:
            if w and w.lower() in low:
                return cat
    return "Այլ"


# ------------------------------------------------------------------ հիմնական ընթացք
def run_once(cfg, demo=False, ignore_seen=False):
    today = dt.date.today().isoformat()
    data_dir = BASE / "data"
    reports_dir = BASE / "reports"
    data_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    seen = {} if ignore_seen else load_seen()
    rows, per_source, errors = [], {}, []

    sources = cfg["sources"]
    if demo:
        sources = [
            {"name": "Օրինակ-ARMEPS", "url": str(BASE / "samples" / "sample_armeps.html"), "kind": "file"},
            {"name": "Օրինակ-MinFin", "url": str(BASE / "samples" / "sample_minfin.html"), "kind": "file"},
        ]
        log.info("ԴԵՄՈ ռեժիմ. կայքերի փոխարեն կարդացվում են լոկալ օրինակ ֆայլերը։")

    for src in sources:
        name, url, kind = src.get("name", "կայք"), src["url"], src.get("kind", "html")
        per_source.setdefault(name, 0)
        log.info("Ստուգվում է` %s (%s)", name, url)

        if kind == "file" or url.startswith("file://"):
            path = Path(url.replace("file://", ""))
            page = path.read_text(encoding="utf-8") if path.exists() else None
        else:
            page = fetch(url)
            time.sleep(cfg.get("delay_seconds", 2))
        if page is None:
            errors.append(name)
            continue

        if kind == "rss":
            items = parse_rss_items(page)
        else:
            items = parse_html_items(page, url if not kind == "file" else "")

        # Ընդհանուր (ջահմանային) կոնտակտներ ցանկի էջից — օգտագործվում են որպես «պահուստ»,
        # եթե առանձին հայտարարության տեքստում հեռախոս/էլ. փոստ չի գտնվել։
        page_contacts = extract_fields(strip_tags(page))

        log.info("  -> գտնվեց %d հղում/հայտարարություն", len(items))

        for it in items:
            blob = it["title"] + " " + it.get("snippet", "")
            if cfg.get("only_keywords") and not any(k.lower() in blob.lower() for k in cfg["only_keywords"]):
                continue
            item_id = hashlib.md5((it["url"] + it["title"]).encode("utf-8")).hexdigest()[:12]
            if item_id in seen:
                continue

            detail = ""
            if cfg.get("fetch_detail_pages") and it["url"].startswith("http") and not demo:
                detail = strip_tags(fetch(it["url"]) or "")
                time.sleep(cfg.get("delay_seconds", 2))
            full_text = (it.get("snippet", "") + " " + detail).strip() or it["title"]

            fields = extract_fields(full_text + " " + it["title"])
            # եթե հայտարարության մեջ կոնտակտ չկա՝ վերցնում ենք ցանկի ընդհանուր կոնտակտները
            for key in ("phones", "emails"):   # միայն կոնտակտները. կազմակերպությունը՝ հայտարարության տեքստից
                if not fields.get(key):
                    fields[key] = page_contacts.get(key, "")
            category = categorize(cfg, it["title"] + " " + full_text)

            folder = data_dir / today / category
            folder.mkdir(parents=True, exist_ok=True)
            fname = folder / f"{sanitize(name)}_{sanitize(it['title'])}.txt"
            fname.write_text(
                f"ԱՂԲՅՈՒՐ՝ {name}\nՀՂՈՒՄ՝ {it['url']}\nՀԱՅՏՆԱԲԵՐՎԵԼ Է՝ {today}\n"
                f"ՀԵՌԱԽՈՍ՝ {fields['phones'] or '—'}\nԷԼ. ՓՈՍՏ՝ {fields['emails'] or '—'}\n"
                f"{'-' * 60}\n{full_text}\n",
                encoding="utf-8",
            )

            rows.append({
                "Ամսաթիվ": fields["date"] or today,
                "Աղբյուր": name,
                "Կատեգորիա": category,
                "Կազմակերպություն": fields["org"],
                "Նպատակ / Վերնագիր": it["title"],
                "Ծածկագիր": fields["code"],
                "Վերջնաժամկետ": fields["deadline"],
                "Հեռախոս": fields["phones"],
                "Էլ. փոստ": fields["emails"],
                "Հղում": it["url"],
                "Պահպանված ֆայլ": str(fname.relative_to(BASE)),
            })
            seen[item_id] = today
            per_source[name] += 1

    SEEN_PATH.write_text(json.dumps(seen, ensure_ascii=False, indent=0), encoding="utf-8")

    # ---------- հաշվետվություններ
    if rows:
        daily = reports_dir / f"Հաշվետվություն-{today}.csv"
        with daily.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        master = reports_dir / "MASTER.csv"
        new_master = not master.exists()
        with master.open("a", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            if new_master:
                writer.writeheader()
            writer.writerows(rows)

    summary_lines = [f"ԱՄՓՓԱԳԻՐ {today}", "=" * 40, f"Նոր հայտարարություններ՝ {len(rows)}"]
    for name, cnt in per_source.items():
        summary_lines.append(f"  • {name}: {cnt} նոր")
    if errors:
        summary_lines.append("Չբացված կայքեր՝ " + ", ".join(errors))
    for row in rows:
        summary_lines.append(f"  - [{row['Կատեգորիա']}] {row['Նպատակ / Վերնագիր'][:70]}"
                             f" | հեռ.՝ {row['Հեռախոս'] or '—'} | էլ.փ.՝ {row['Էլ. փոստ'] or '—'}")
    summary = "\n".join(summary_lines)
    (reports_dir / f"Ամփոփագիր-{today}.txt").write_text(summary, encoding="utf-8")
    log.info("\n%s", summary)
    return rows


def loop_mode(cfg):
    target = cfg.get("run_time", "08:00")
    log.info("Մշտական ռեժիմ. ամեն օր %s-ին կստուգի կայքերը։ Փակելու համար սեղմեք Ctrl+C։", target)
    while True:
        now = dt.datetime.now()
        hh, mm = map(int, target.split(":"))
        nxt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if nxt <= now:
            nxt += dt.timedelta(days=1)
        wait = (nxt - now).total_seconds()
        log.info("Հաջորդ գործարկումը՝ %s (մնացել է %.1f ժամ)", nxt.strftime("%Y-%m-%d %H:%M"), wait / 3600)
        time.sleep(wait)
        try:
            run_once(cfg)
        except Exception as exc:
            log.exception("Սխալ գործարկման ժամանակ. %s", exc)


def main():
    parser = argparse.ArgumentParser(description="Տենդերային մոնիտոր")
    parser.add_argument("--demo", action="store_true", help="փորձնական ռեժիմ առանց ինտերնետի")
    parser.add_argument("--loop", action="store_true", help="մշտական ռեժիմ՝ ամենօրյա գործարկմամբ")
    parser.add_argument("--reset", action="store_true", help="մոռանալ հին բեռնումները (ամբողջ արխիվ)")
    args = parser.parse_args()

    setup_logging()
    cfg = load_config()
    if args.reset:
        if SEEN_PATH.exists():
            SEEN_PATH.unlink()
        log.info("Հիշողությունը մաքրված է. հաջորդ գործարկումը ամեն ինչ նորից կբեռնի։")
    if args.loop:
        loop_mode(cfg)
    else:
        rows = run_once(cfg, demo=args.demo, ignore_seen=args.reset)
        log.info("Ավարտվեց։ Նոր պահպանված հայտարարություններ՝ %d։ Տեսեք reports/ և data/ թղթապանակները։", len(rows))


if __name__ == "__main__":
    main()
