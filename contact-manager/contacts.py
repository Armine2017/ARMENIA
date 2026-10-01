#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contacts.py — անձնական կոնտակտների օգնականի գործիքակազմ (Python 3, առանց արտաքին կախվածությունների)։

Ռեժիմներ
  check    Կրկնվողների հայտնաբերում, անավարտ/անվավեր դաշտեր, «Երկիրը ստուգել» նշումներ։
  format   Հեռախոսահամարի միջազգային ձևաչափի ԱՌԱՋԱՐԿ (միայն հաստատված երկրի դեպքում)։
  summary  Ամփոփում քանակներով (նոր / կրկնվող / ստուգման ենթակա / անավարտ)։

Խիստ կանոններ (համապատասխանում են օգնականի աշխատանքի սկզբունքներին)
  • Մուտքային CSV-ն ԵՐԵԲԵՔ չի փոփոխվում։
  • Ոչ մի գրառում չի միավորվում և չի ջնջվում. տրվում է միայն հաշվետվություն/առաջարկ։
  • Երկիրը չի ենթադրվում. առանց հաստատված երկրի համարը մնում է անփոփոխ՝ «Երկիրը ստուգել» նշումով։
  • Հաշվետվություններում հեռախոսահամարները դիմակավորվում են. բացելու համար՝ --show-phones։

Օրինակներ
  python3 contacts.py check  contacts.csv --out reports/check-2026-10-01.md
  python3 contacts.py format contacts.csv --country AM --out contacts_formatted.csv
  python3 contacts.py summary contacts.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------- սահմանումներ

FIELDS = [
    "Անուն",
    "Ազգանուն",
    "Մականուն",
    "Հիմնական հեռախոս",
    "Լրացուցիչ հեռախոս",
    "Էլ. փոստ",
    "Կատեգորիա",
    "Պիտակներ",
    "Քաղաք",
    "Ծննդյան օր",
    "Կարևորություն",
    "Ծանոթության աղբյուր",
    "Վերջին շփում",
    "Նշումներ",
    "Կարգավիճակ",
]

# «Էլ. փոստ» դաշտը ավելացվել է 14 դաշտանոց ցանկին, որովհետև առաջադրանք B-ն
# պահանջում է համեմատել նաև էլ. փոստերը, եթե դրանք տրամադրված են։
# Եթե ցանկանում ես առանց այս սյունակի՝ հանիր այն CSV-ից, սցենարը կաշխատի առանց դրա։

PHONE_FIELDS = ["Հիմնական հեռախոս", "Լրացուցիչ հեռախոս"]

CATEGORIES = [
    "Ընտանիք",
    "Մոտ ընկերներ",
    "Ընկերներ և ծանոթներ",
    "Աշխատանքային կապեր",
    "Ծառայություններ",
    "Այլ",
]
STATUSES = ["Նոր", "Ստուգման ենթակա", "Հաստատված"]
IMPORTANCE = ["A", "B", "C"]

REQUIRED_FIELDS = ["Անուն", "Հիմնական հեռախոս", "Կատեգորիա", "Կարգավիճակ"]
RECOMMENDED_FIELDS = ["Ազգանուն", "Քաղաք", "Ծանոթության աղբյուր", "Վերջին շփում"]

HEADER_ALIASES = {
    "Հեռախոս": "Հիմնական հեռախոս",
    "Հեռախոսահամար": "Հիմնական հեռախոս",
    "Լրացուցիչ հեռախոսահամար": "Լրացուցիչ հեռախոս",
    "Էլ.հասցե": "Էլ. փոստ",
    "Էլ. հասցե": "Էլ. փոստ",
    "Email": "Էլ. փոստ",
    "E-mail": "Էլ. փոստ",
    "Կարգավիճակը": "Կարգավիճակ",
    "Կարեւորություն": "Կարևորություն",
}

DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y.%m.%d", "%d-%m-%Y")
BIRTHDAY_FORMATS = ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d.%m", "%d/%m", "%d-%m")

STALE_DAYS = 365
UPCOMING_BIRTHDAY_DAYS = 30

# ---------------------------------------------------------------- օժանդակներ


def g(row: dict, field: str) -> str:
    return (row.get(field) or "").strip()


def digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def norm_phone(value: str) -> str:
    """Համեմատության բանալի. սկզբնական տարբերակը չի փոխարինվում, միայն նորմալացվում է համեմատելու համար։"""
    d = digits(value)
    if not d:
        return ""
    return ("+" + d) if (value or "").strip().startswith("+") else d


def phone_tail(value: str, n: int = 7) -> str:
    d = digits(value)
    return d[-n:] if len(d) >= n else d


def norm_name(*parts: str) -> str:
    text = " ".join(p for p in parts if p)
    text = unicodedata.normalize("NFKD", text).casefold()
    return re.sub(r"[^\w\u0531-\u058f]+", "", text, flags=re.UNICODE)


def norm_email(value: str) -> str:
    return (value or "").strip().casefold()


def value_key(value: str) -> str:
    """Ընդհանուր համեմատության բանալի հեռախոսի/փոստի համար։"""
    value = (value or "").strip()
    if not value:
        return ""
    return norm_email(value) if "@" in value else norm_phone(value)


def parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_birthday(value: str):
    """Վերադարձնում է (ամիս, օր) կամ None, եթե հնարավոր չէ վերլուծել։"""
    value = (value or "").strip()
    if not value:
        return None
    for fmt in BIRTHDAY_FORMATS:
        try:
            d = datetime.strptime(value, fmt).date()
            return (d.month, d.day)
        except ValueError:
            continue
    return None


def mask_phone(value: str, show: bool = False) -> str:
    value = (value or "").strip()
    if not value:
        return "—"
    if show:
        return value
    d = digits(value)
    return f"…{d[-4:]}" if len(d) >= 4 else "…"


def display_name(row: dict) -> str:
    parts = [g(row, "Անուն"), g(row, "Ազգանուն")]
    name = " ".join(p for p in parts if p)
    if not name:
        name = g(row, "Մականուն") or "—"
    nick = g(row, "Մականուն")
    if nick and g(row, "Անուն"):
        name = f"{name} («{nick}»)"
    return name


def row_ref(index: int) -> str:
    """CSV/Excel տողի համարը (վերնագիրը՝ 1, առաջին գրառումը՝ 2)։"""
    return str(index + 1)


def md_escape(text: str) -> str:
    return (text or "").replace("|", "\\|")


# ---------------------------------------------------------------- ընթերցում


def detect_delimiter(sample: str) -> str:
    first = sample.splitlines()[0] if sample.splitlines() else ""
    return ";" if first.count(";") > first.count(",") else ","


def read_contacts(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    delimiter = detect_delimiter(text)
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    raw_fields = reader.fieldnames or []
    mapped = []
    unmapped = []
    for f in raw_fields:
        target = HEADER_ALIASES.get((f or "").strip(), (f or "").strip())
        mapped.append(target)
        if target not in FIELDS:
            unmapped.append(f)
    rows = []
    for raw in reader:
        row = {}
        for src, dst in zip(raw_fields, mapped):
            if dst in FIELDS:
                row[dst] = (raw.get(src) or "").strip()
        rows.append(row)
    return rows, mapped, unmapped


# ---------------------------------------------------------------- վերլուծություն


def analyze(rows, today: date | None = None):
    today = today or date.today()
    info = []
    for i, row in enumerate(rows, 1):
        info.append(
            {
                "i": i,
                "phones": [g(row, f) for f in PHONE_FIELDS if g(row, f)],
                "email": norm_email(g(row, "Էլ. փոստ")),
                "name": norm_name(g(row, "Անուն"), g(row, "Ազգանուն")),
                "nick": norm_name(g(row, "Անուն"), g(row, "Մականուն")) if g(row, "Մականուն") else "",
            }
        )

    exact_groups: list[dict] = []
    exact_pairs: set[frozenset] = set()

    def add_exact(label: str, key: str, group: set[int], note: str = "") -> None:
        group = sorted(group)
        if len(group) < 2:
            return
        names = {info[j - 1]["name"] or f"row{j}" for j in group}
        if label == "Հեռախոս" and len(names) > 1:
            note = (note + " " if note else "") + "նույն համարը տարբեր անուններով. ստուգել՝ նույն մարդն է, թե ընդհանուր համար"
        exact_groups.append({"label": label, "key": key, "rows": group, "note": note.strip()})
        for a in group:
            for b in group:
                if a < b:
                    exact_pairs.add(frozenset((a, b)))

    by_phone = defaultdict(set)
    by_email = defaultdict(set)
    by_tail = defaultdict(set)
    by_name = defaultdict(set)
    by_nick = defaultdict(set)

    for item in info:
        i = item["i"]
        for p in item["phones"]:
            if len(digits(p)) >= 5:
                by_phone[norm_phone(p)].add(i)
                by_tail[phone_tail(p)].add(i)
        if item["email"]:
            by_email[item["email"]].add(i)
        if item["name"]:
            by_name[item["name"]].add(i)
        if item["nick"] and item["nick"] != item["name"]:
            by_nick[item["nick"]].add(i)

    for key, group in sorted(by_phone.items()):
        add_exact("Հեռախոս", key, group)
    for key, group in sorted(by_email.items()):
        add_exact("Էլ. փոստ", key, group)

    possible: list[dict] = []
    seen_pairs: set[frozenset] = set()

    def add_possible(pair, note: str) -> None:
        key = frozenset(pair)
        if key in exact_pairs or key in seen_pairs:
            return
        seen_pairs.add(key)
        possible.append({"rows": sorted(pair), "note": note})

    def has_shared_phone(a: int, b: int) -> bool:
        pa = {norm_phone(p) for p in info[a - 1]["phones"]}
        pb = {norm_phone(p) for p in info[b - 1]["phones"]}
        return bool(pa & pb)

    for key, group in sorted(by_name.items()):
        group = sorted(group)
        for x in range(len(group)):
            for y in range(x + 1, len(group)):
                a, b = group[x], group[y]
                if has_shared_phone(a, b):
                    continue
                add_possible((a, b), "նույն անուն-ազգանունը, տարբեր (կամ բացակայող) համար. ձեռքով ստուգել, մի՛ ենթադրել նույն մարդը")

    for key, group in sorted(by_nick.items()):
        group = sorted(group)
        for x in range(len(group)):
            for y in range(x + 1, len(group)):
                add_possible((group[x], group[y]), "համընկնող մականուն/անուն-մականուն. ձեռքով ստուգել")

    for key, group in sorted(by_tail.items()):
        group = sorted(group)
        if len(group) < 2:
            continue
        for x in range(len(group)):
            for y in range(x + 1, len(group)):
                a, b = group[x], group[y]
                if has_shared_phone(a, b):
                    continue
                add_possible((a, b), "համընկնող վերջին 7 նիշերը, տարբեր նախածանց/երկիր. ստուգել երկիրը")

    # «Երկիրը ստուգել» և հեռախոսի ձևաչափ
    country_flags = []
    for item in info:
        for p in item["phones"]:
            d = digits(p)
            if not p.strip().startswith("+"):
                country_flags.append((item["i"], p, "առանց միջազգային նախածանցի. Երկիրը ստուգել"))
            elif len(d) < 8 or len(d) > 15:
                country_flags.append((item["i"], p, "անսովոր երկարություն. ստուգել համարը"))

    # անավարտ և անվավեր դաշտեր
    missing = []
    invalid = []
    for i, row in enumerate(rows, 1):
        miss_required = [f for f in REQUIRED_FIELDS if not g(row, f)]
        miss_recommended = [f for f in RECOMMENDED_FIELDS if not g(row, f)]
        if miss_required or miss_recommended:
            missing.append({"i": i, "required": miss_required, "recommended": miss_recommended})
        if g(row, "Կատեգորիա") and g(row, "Կատեգորիա") not in CATEGORIES:
            invalid.append((i, "Կատեգորիա", g(row, "Կատեգորիա")))
        if g(row, "Կարգավիճակ") and g(row, "Կարգավիճակ") not in STATUSES:
            invalid.append((i, "Կարգավիճակ", g(row, "Կարգավիճակ")))
        if g(row, "Կարևորություն") and g(row, "Կարևորություն").upper() not in IMPORTANCE:
            invalid.append((i, "Կարևորություն", g(row, "Կարևորություն")))
        for f in ("Ծննդյան օր", "Վերջին շփում"):
            v = g(row, f)
            if v and (parse_birthday(v) is None if f == "Ծննդյան օր" else parse_date(v) is None):
                invalid.append((i, f, v))

    # վաղուց չշփված և մոտակա ծննդյան օրեր
    stale = []
    upcoming = []
    for i, row in enumerate(rows, 1):
        last = parse_date(g(row, "Վերջին շփում"))
        if last:
            days = (today - last).days
            if days > STALE_DAYS:
                stale.append((i, g(row, "Վերջին շփում"), days))
        bd = parse_birthday(g(row, "Ծննդյան օր"))
        if bd:
            month, day = bd
            try:
                nxt = date(today.year, month, day)
            except ValueError:
                nxt = None
            if nxt and nxt < today:
                try:
                    nxt = date(today.year + 1, month, day)
                except ValueError:
                    nxt = None
            if nxt:
                delta = (nxt - today).days
                if 0 <= delta <= UPCOMING_BIRTHDAY_DAYS:
                    upcoming.append((i, g(row, "Ծննդյան օր"), delta))
    upcoming.sort(key=lambda t: t[2])

    statuses = Counter(g(r, "Կարգավիճակ") or "—" for r in rows)
    categories = Counter(g(r, "Կատեգորիա") or "—" for r in rows)

    return {
        "info": info,
        "exact_groups": exact_groups,
        "possible": possible,
        "country_flags": country_flags,
        "missing": missing,
        "invalid": invalid,
        "stale": stale,
        "upcoming": upcoming,
        "statuses": statuses,
        "categories": categories,
        "today": today,
    }


# ---------------------------------------------------------------- հաշվետվություն


def render_report(rows, result, source: str, show_phones: bool = False) -> str:
    today = result["today"]
    lines: list[str] = []
    lines.append("# Կոնտակտների ստուգման հաշվետվություն")
    lines.append("")
    lines.append(f"- Ֆայլ՝ `{source}`")
    lines.append(f"- Գրառումներ՝ {len(rows)}")
    lines.append(f"- Ստեղծված՝ {today.isoformat()}")
    lines.append(f"- Հեռախոսները՝ {'բաց (--show-phones)' if show_phones else 'դիմակավորված'}")
    lines.append("")

    lines.append("## 1. Ամփոփում")
    lines.append("")
    lines.append("| Ցուցանիշ | Քանակ |")
    lines.append("| --- | --- |")
    lines.append(f"| Ընդամենը գրառում | {len(rows)} |")
    lines.append(f"| Ճշգրիտ կրկնվող խումբ | {len(result['exact_groups'])} |")
    lines.append(f"| Հնարավոր կրկնվող զույգ | {len(result['possible'])} |")
    lines.append(f"| «Երկիրը ստուգել» / կասկածելի համար | {len(result['country_flags'])} |")
    lines.append(f"| Անավարտ գրառում | {len(result['missing'])} |")
    lines.append(f"| Անվավեր արժեք | {len(result['invalid'])} |")
    lines.append(f"| Վաղուց չշփված (>{STALE_DAYS} օր) | {len(result['stale'])} |")
    lines.append("")

    lines.append("| Կարգավիճակ | Քանակ |")
    lines.append("| --- | --- |")
    for st, cnt in sorted(result["statuses"].items()):
        lines.append(f"| {md_escape(st)} | {cnt} |")
    lines.append("")
    lines.append("| Կատեգորիա | Քանակ |")
    lines.append("| --- | --- |")
    for c, cnt in sorted(result["categories"].items()):
        lines.append(f"| {md_escape(c)} | {cnt} |")
    lines.append("")

    def rows_table(indices):
        out = [
            "| CSV տող | Անուն | Հեռախոս | Էլ. փոստ | Քաղաք | Կարգավիճակ |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for i in indices:
            row = rows[i - 1]
            phones = ", ".join(mask_phone(p, show_phones) for p in result["info"][i - 1]["phones"]) or "—"
            out.append(
                "| {ref} | {name} | {phone} | {email} | {city} | {status} |".format(
                    ref=row_ref(i),
                    name=md_escape(display_name(row)),
                    phone=phones,
                    email=md_escape(g(row, "Էլ. փոստ")) or "—",
                    city=md_escape(g(row, "Քաղաք")) or "—",
                    status=md_escape(g(row, "Կարգավիճակ")) or "—",
                )
            )
        return out

    lines.append("## 2. Ճշգրիտ կրկնվողներ (նույն համարը կամ էլ. փոստը)")
    lines.append("")
    if not result["exact_groups"]:
        lines.append("Ճշգրիտ համընկնում չի գտնվել։")
    else:
        lines.append("> Սրանք **առաջարկներ** են. ոչ մի միավորում չի կատարվել։ Հաստատելուց հետո միայն կմիավորենք։")
        lines.append("")
        for n, grp in enumerate(result["exact_groups"], 1):
            key = grp["key"]
            shown_key = key if ("@" in key or show_phones) else mask_phone(key, show_phones)
            lines.append(f"### Խումբ {n} — {grp['label']}՝ `{shown_key}`")
            if grp["note"]:
                lines.append(f"Նշում՝ {grp['note']}")
            lines.append("")
            lines.extend(rows_table(grp["rows"]))
            lines.append("")

    lines.append("## 3. Հնարավոր կրկնվողներ (ձեռքով ստուգել)")
    lines.append("")
    if not result["possible"]:
        lines.append("Հնարավոր կրկնվողներ չեն գտնվել։")
    else:
        lines.append("| # | CSV տողեր | Անուններ | Նշում |")
        lines.append("| --- | --- | --- | --- |")
        for n, item in enumerate(result["possible"], 1):
            a, b = item["rows"]
            names = " / ".join(md_escape(display_name(rows[j - 1])) for j in (a, b))
            lines.append(f"| {n} | {row_ref(a)}, {row_ref(b)} | {names} | {item['note']} |")
        lines.append("")

    lines.append("## 4. Հեռախոսի ձևաչափ / «Երկիրը ստուգել»")
    lines.append("")
    if not result["country_flags"]:
        lines.append("Բոլոր համարները սկսվում են «+»-ով։")
    else:
        lines.append("| CSV տող | Համար | Նշում |")
        lines.append("| --- | --- | --- |")
        for i, phone, note in result["country_flags"]:
            lines.append(f"| {row_ref(i)} | {md_escape(mask_phone(phone, show_phones))} | {note} |")
        lines.append("")
        lines.append(
            "Համարը չի փոխվել։ Միջազգային ձևաչափի անցնելու համար՝ "
            "`format` ռեժիմը հաստատված երկրի հետ (օր.՝ `--country AM`)։"
        )
        lines.append("")

    lines.append("## 5. Անավարտ գրառումներ")
    lines.append("")
    if not result["missing"]:
        lines.append("Բոլոր պարտադիր դաշտերը լրացված են։")
    else:
        lines.append("| CSV տող | Անուն | Պարտադիր բացակայող | Խորհուրդ է լրացնել |")
        lines.append("| --- | --- | --- | --- |")
        for item in result["missing"]:
            i = item["i"]
            lines.append(
                "| {ref} | {name} | {req} | {rec} |".format(
                    ref=row_ref(i),
                    name=md_escape(display_name(rows[i - 1])),
                    req=md_escape(", ".join(item["required"])) or "—",
                    rec=md_escape(", ".join(item["recommended"])) or "—",
                )
            )
        lines.append("")

    lines.append("## 6. Անվավեր արժեքներ")
    lines.append("")
    if not result["invalid"]:
        lines.append("Անվավեր արժեք չի գտնվել։")
    else:
        lines.append("| CSV տող | Դաշտ | Արժեք |")
        lines.append("| --- | --- | --- |")
        for i, field, value in result["invalid"]:
            lines.append(f"| {row_ref(i)} | {md_escape(field)} | {md_escape(value)} |")
        lines.append("")

    lines.append("## 7. Վաղուց չշփված")
    lines.append("")
    if not result["stale"]:
        lines.append(f"Չկան գրառումներ, որոնց վերջին շփումը {STALE_DAYS} օրից ավելի վաղ է։")
    else:
        lines.append("| CSV տող | Անուն | Վերջին շփում | Օր |")
        lines.append("| --- | --- | --- | --- |")
        for i, last, days in sorted(result["stale"], key=lambda t: -t[2]):
            lines.append(f"| {row_ref(i)} | {md_escape(display_name(rows[i - 1]))} | {last} | {days} |")
        lines.append("")

    if result["upcoming"]:
        lines.append("## 8. Մոտակա ծննդյան օրեր (30 օր)")
        lines.append("")
        lines.append("| CSV տող | Անուն | Ծննդյան օր | Օրերից |")
        lines.append("| --- | --- | --- | --- |")
        for i, bd, delta in result["upcoming"]:
            lines.append(f"| {row_ref(i)} | {md_escape(display_name(rows[i - 1]))} | {bd} | {delta} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "Հիշեցում՝ սցենարը ոչինչ չի փոխել, չի միավորել և չի ջնջել. "
        "բոլոր որոշումները կատարվում են քո հաստատումից հետո։"
    )
    lines.append("")
    return "\n".join(lines)


def render_summary(rows, result, source: str) -> str:
    today = result["today"]
    lines = [
        f"# Օրվա ամփոփում — {today.isoformat()}",
        "",
        f"Աղբյուր՝ `{source}`",
        "",
        f"- Ընդամենը գրառում՝ {len(rows)}",
        f"- Ճշգրիտ կրկնվող խումբ՝ {len(result['exact_groups'])}",
        f"- Հնարավոր կրկնվող զույգ՝ {len(result['possible'])}",
        f"- Ստուգման ենթակա («Երկիրը ստուգել» / կասկածելի համար)՝ {len(result['country_flags'])}",
        f"- Անավարտ գրառում՝ {len(result['missing'])}",
        f"- Անվավեր արժեք՝ {len(result['invalid'])}",
        "",
        "## Ըստ կարգավիճակի",
        "",
        "| Կարգավիճակ | Քանակ |",
        "| --- | --- |",
    ]
    for st, cnt in sorted(result["statuses"].items()):
        lines.append(f"| {md_escape(st)} | {cnt} |")
    lines.append("")
    lines.append("## Ըստ կատեգորիայի")
    lines.append("")
    lines.append("| Կատեգորիա | Քանակ |")
    lines.append("| --- | --- |")
    for c, cnt in sorted(result["categories"].items()):
        lines.append(f"| {md_escape(c)} | {cnt} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- ձևաչափում


def propose_phone(raw: str, country: str) -> tuple[str, str]:
    raw = (raw or "").strip()
    if not raw:
        return "", "դատարկ"
    d = digits(raw)
    if raw.startswith("+"):
        if country == "AM" and len(d) == 11 and d.startswith("374"):
            return f"+374 {d[3:5]} {d[5:]}", "միջազգային (ստուգված երկարություն)"
        if country == "RU" and len(d) == 11 and d.startswith("7"):
            return f"+7 {d[1:4]} {d[4:7]}-{d[7:9]}-{d[9:]}", "միջազգային (ստուգված երկարություն)"
        return raw, "արդեն սկսվում է «+»-ով. միայն ձեռքով հաստատելուց հետո փոխել ձևաչափը"

    if country == "AM":
        if len(d) == 9 and d.startswith("0"):
            return f"+374 {d[1:3]} {d[3:]}", "Հայաստան (+374)՝ սկզբնական 0-ը հանված. ստուգել օպերատորի կոդը"
        if len(d) == 8:
            return f"+374 {d[:2]} {d[2:]}", "առանց սկզբնական 0-ի. ստուգել, որ Երևան/մարզի կոդը ճիշտ է"
        if len(d) == 11 and d.startswith("374"):
            return f"+374 {d[3:5]} {d[5:]}", "միջազգային՝ առանց «+»-ի"
        return raw, "ձևաչափը չի համընկել ոչ մի կանոնի. Երկիրը ստուգել, համարը չի փոփոխվել"
    if country == "RU":
        if len(d) == 11 and d.startswith("8"):
            rest = d[1:]
            return f"+7 {rest[:3]} {rest[3:6]}-{rest[6:8]}-{rest[8:]}", "8-ը փոխարինված +7-ով"
        if len(d) == 11 and d.startswith("7"):
            return f"+7 {d[1:4]} {d[4:7]}-{d[7:9]}-{d[9:]}", "միջազգային՝ առանց «+»-ի"
        if len(d) == 10:
            return f"+7 {d[:3]} {d[3:6]}-{d[6:8]}-{d[8:]}", "ենթադրվել է +7՝ 10-նիշ մուտքից. պարտադիր ստուգել"
        return raw, "ձևաչափը չի համընկել ոչ մի կանոնի. Երկիրը ստուգել, համարը չի փոփոխվել"
    return raw, "անհայտ երկիր"


def cmd_format(args) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Ֆայլ չի գտնվել՝ {path}", file=sys.stderr)
        return 2
    rows, _, _ = read_contacts(path)
    out_path = Path(args.out) if args.out else path.with_name(path.stem + "_formatted.csv")
    extra = ["Հիմնական հեռախոս (առաջարկվող)", "Լրացուցիչ հեռախոս (առաջարկվող)", "Հեռախոսի նշում"]
    notes = []
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS + extra, delimiter=args.out_delimiter, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            main_prop, main_note = propose_phone(g(row, "Հիմնական հեռախոս"), args.country)
            alt_prop, alt_note = propose_phone(g(row, "Լրացուցիչ հեռախոս"), args.country)
            if main_note and main_note != "դատարկ":
                notes.append(main_note)
            row = dict(row)
            row["Հիմնական հեռախոս (առաջարկվող)"] = main_prop
            row["Լրացուցիչ հեռախոս (առաջարկվող)"] = alt_prop
            row["Հեռախոսի նշում"] = "; ".join(n for n in (main_note, alt_note) if n and n != "դատարկ")
            writer.writerow(row)
    print(f"Առաջարկը գրված է՝ {out_path}")
    print("Սկզբնական համարները պահպանվել են նույն սյունակներում. ոչինչ չի փոխարինվել։")
    if notes:
        for note, cnt in Counter(notes).most_common():
            print(f"  - {note}: {cnt}")
    print("Հաստատի՛ր առաջարկված ձևաչափերը, որից հետո միայն կկիրառենք դրանք հիմնական սյունակներում։")
    return 0


# ---------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Անձնական կոնտակտների օգնականի գործիքակազմ")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp):
        sp.add_argument("file", help="Մուտքային CSV ֆայլ (չի փոփոխվում)")
        sp.add_argument("--out", help="Արդյունքի ֆայլ (չտրվելու դեպքում՝ reports/ պանակում կամ stdout)")
        sp.add_argument("--show-phones", action="store_true", help="Հեռախոսները ցույց տալ ամբողջությամբ (լռելյայն՝ դիմակավորված)")
        sp.add_argument("--today", help="Ամփոփման ամսաթիվ YYYY-MM-DD (թեստերի համար)")

    sp = sub.add_parser("check", help="Կրկնվողների և անավարտ դաշտերի ստուգում")
    common(sp)

    sp = sub.add_parser("summary", help="Օրվա ամփոփում")
    common(sp)

    sp = sub.add_parser("format", help="Հեռախոսահամարի միջազգային ձևաչափի առաջարկ")
    common(sp)
    sp.add_argument("--country", required=True, choices=["AM", "RU"], help="Հաստատված երկիր (AM=+374, RU=+7)")
    sp.add_argument("--out-delimiter", default=",", choices=[",", ";"], help="Արդյունքային CSV-ի բաժանիչը")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.file)
    if not path.exists():
        print(f"Ֆայլ չի գտնվել՝ {path}", file=sys.stderr)
        return 2

    rows, mapped, unmapped = read_contacts(path)
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if getattr(args, "today", None) else date.today()
    result = analyze(rows, today=today)

    if args.command == "format":
        return cmd_format(args)

    if args.command == "check":
        text = render_report(rows, result, source=str(path), show_phones=args.show_phones)
        if unmapped:
            text += "\nԾանոթություն՝ չճանաչված սյունակներ՝ " + ", ".join(unmapped) + "\n"
    else:
        text = render_summary(rows, result, source=str(path))

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Գրված է՝ {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
