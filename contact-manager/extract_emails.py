#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_emails.py — կոնտակտների/հասցեների հավաքում ՄԵԿ ֆայլով (կամ երկուսով՝ մարդիկ + ծառայություններ)։

Աջակցվող մուտքեր
  • Գուգլ Կոնտակտների CSV (առաջնահերթ)  — ներառյալ անուն/քաղաք/ծննդյան օր/կազմակերպություն/պիտակներ
  • .csv այլ ցանկեր, .txt, .json          — հասցեների սկանավորում
  • .mbox / .eml / .zip (Takeout)         — նամակներից հասցեների հավաքում

ԱՆՎՏԱՆԳՈՒԹՅԱՆ ԿԱՆՈՆՆԵՐ (պարտադիր)
  1. Միայն ԿԱՐԴՈՒՄ է. մուտքային ֆայլերը երբեք չեն փոփոխվում, չեն ջնջվում, չեն տեղափոխվում։
  2. Ցանց ՉԻ օգտագործվում. միայն Python ստանդարտ գրադարան, ամբողջովին օֆլայն։
  3. Ոչինչ չի ուղարկվում, ոչ մի նամակի չի պատասխանվում, ոչինչ չի նշվում կարդացված։
  4. Նամակների բովանդակությունը և հավելվածները ՉԵՆ պահվում. միայն անուն/հասցե/հեռախոս/ամսաթիվ։
  5. Տերմինալում հասցեները ցուցադրվում են ԴԻՄԱԿԱՎՈՐՎԱԾ (բացելու համար՝ --show-emails)։
  6. Արդյունքային ֆայլերի իրավունքները՝ 0600 (միայն սեփականատերը)։
  7. Ոչ մի կոնտակտ չի ՄԻԱՎՈՐՎՈՒՄ կամ ՋՆՋՎՈՒՄ. ցուցադրվում են միայն առաջարկներ ու նշումներ։

Օրինակներ
  # Գուգլ Կոնտակտների CSV → երկու ֆայլ (մարդիկ + ծառայություններ)
  python3 extract_emails.py --input inbox/google-contacts.csv \
      --against contacts.csv --out reports/contacts-import.csv

  # Takeout / mbox (նամակներից)
  python3 extract_emails.py --input inbox/takeout.zip --phones \
      --against contacts.csv --out reports/email-contacts.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from email import policy
from email.header import decode_header, make_header
from email.message import Message
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contacts import CATEGORIES, FIELDS, PHONE_FIELDS, digits, norm_email, read_contacts  # noqa: E402

HELPER_FIELDS = ["Դոմեն", "Աղբյուր", "Հանդիպումներ", "Առաջին անգամ", "Վերջին անգամ"]
OUT_FIELDS = FIELDS + HELPER_FIELDS

DEFAULT_HEADERS = ["From", "To", "Cc", "Reply-To", "Sender"]
SELF_CANDIDATE_MIN = 3
SERVICES_CATEGORY = "Ծառայություններ"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
NAME_ADDR_RE = re.compile(
    r"([^<>\"',;\n\r]{2,60}?)\s*<\s*([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})\s*>"
)
PHONE_RE = re.compile(
    r"(?:\+\d[\d\s\-()]{7,}\d)"
    r"|(?:\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{2}[\s\-]?\d{2})"
    r"|(?:0\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2})"
    r"|(?:8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})"
)
ROLE_LOCAL_RE = re.compile(
    r"^(no[-_.]?reply|do[-_.]?not[-_.]?reply|donotreply|mailer[-_.]?daemon|postmaster|bounce[sd]?|"
    r"notifications?|notify|news(letters?)?|info|support|help|admin|administrator|sales|marketing|"
    r"billing|office|hello|contact|team|hr|jobs|careers|press|security|abuse|webmaster|feedback|"
    r"service|noreply\+.*)$",
    re.I,
)
BOUNCE_LOCAL_RE = re.compile(r"^(mailer[-_.]?daemon|postmaster|bounce[sd]?|.*[-_.]bounces(\+.*)?)$", re.I)
HEADER_LINE_RE = re.compile(rb"^[A-Za-z][A-Za-z0-9\-]{1,38}:")
HEADER_LIKE_NAMES = {
    "from", "to", "cc", "bcc", "subject", "date", "message-id", "reply-to", "sender",
    "return-path", "received", "delivered-to", "content-type", "mime-version", "dkim-signature",
    "authentication-results", "list-unsubscribe", "x-mailer", "in-reply-to", "references",
    "list-id", "precedence", "errors-to", "x-original-to", "x-spam-status",
}

FREE_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "hotmail.com", "outlook.com",
    "live.com", "msn.com", "icloud.com", "me.com", "mac.com", "aol.com", "proton.me",
    "protonmail.com", "mail.ru", "bk.ru", "inbox.ru", "list.ru", "yandex.ru", "yandex.com",
    "rambler.ru", "zoho.com", "gmx.com", "gmx.de", "mail.com", "tutanota.com",
}

CATEGORY_ORDER = {c: i for i, c in enumerate(CATEGORIES)}
CATEGORY_KEYWORDS = [
    (SERVICES_CATEGORY, ("service", "ծառայություն", "doctor", "բժիշկ", "վարպետ", "մատուցող", "delivery")),
    ("Ընտանիք", ("family", "ընտանիք", "մայրիկ", "հայրիկ", "mom", "dad", "mother", "father",
                 "brother", "sister", "եղբայր", "քույր")),
    ("Մոտ ընկերներ", ("close friend", "best friend", "մոտ ընկեր", "լավագույն ընկեր")),
    ("Աշխատանքային կապեր", ("work", "job", "աշխատանք", "colleague", "գործընկեր", "client", "հաճախորդ")),
]
GOOGLE_FIELD_RE = re.compile(
    r"^(e-?mail\s*\d*\s*-\s*value|phone\s*\d*\s*-\s*value|given name|first name|family name|"
    r"last name|nickname|group membership|labels|organization 1 - name|birthday|notes|"
    r"address \d+ - city|name)$",
    re.I,
)


# ---------------------------------------------------------------- օժանդակ


def decode_header_value(value) -> str:
    try:
        return str(make_header(decode_header(str(value))))
    except Exception:
        return str(value)


def clean_name(name: str, email_addr: str) -> str:
    name = (name or "").strip().strip('"\'').strip()
    name = re.sub(r"\s+", " ", name)
    if not name or name.casefold() == email_addr.casefold() or "@" in name:
        return ""
    if ":" in name or name.casefold().rstrip(":") in HEADER_LIKE_NAMES:
        return ""
    if re.fullmatch(r"[<>()\[\].,;:!?\-_=+0-9\s]+", name):
        return ""
    if len(name) < 2:
        return ""
    return name


def email_key(addr: str) -> str:
    return (addr or "").strip().casefold()


def plus_base(addr: str) -> str:
    local, _, domain = email_key(addr).partition("@")
    return f"{local.split('+', 1)[0]}@{domain}"


def mask_email(addr: str, show: bool = False) -> str:
    addr = (addr or "").strip()
    if show or not addr:
        return addr or "—"
    local, _, domain = addr.partition("@")
    head = local[:2] if len(local) > 2 else local[:1]
    return f"{head}…@{domain}" if domain else f"{head}…"


def is_role_address(addr: str) -> bool:
    return bool(ROLE_LOCAL_RE.match(email_key(addr).partition("@")[0]))


def is_bounce_address(addr: str) -> bool:
    return bool(BOUNCE_LOCAL_RE.match(email_key(addr).partition("@")[0]))


def clean_phone(raw: str) -> str:
    raw = re.sub(r"\s+", " ", (raw or "").strip()).strip(" ,;.")
    return raw


def plausible_phone(raw: str) -> bool:
    d = digits(raw)
    return 8 <= len(d) <= 15 and not d.startswith("000")


def normalize_birthday(value: str) -> str:
    """Վերադարձնում է DD.MM.YYYY կամ DD.MM, կամ "" եթե հնարավոր չէ վերլուծել։"""
    v = (value or "").strip()
    if not v:
        return ""
    v = re.sub(r"^[-–—\s]+", "", v)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y.%m.%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(v, fmt).date().strftime("%d.%m.%Y")
        except ValueError:
            continue
    for fmt in ("%m-%d", "%m/%d", "%d.%m", "%d-%m"):
        try:
            d = datetime.strptime(v, fmt)
            return d.strftime("%d.%m")
        except ValueError:
            continue
    return ""


def message_text(msg: Message) -> str:
    """Նամակի տեքստը՝ ՄԻԱՅՆ վերլուծության համար. ոչ մի տեղ չի պահվում։"""
    chunks: list[str] = []
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype not in ("text/plain", "text/html"):
                    continue
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if ctype == "text/html":
                    text = re.sub(r"<[^>]+>", " ", text)
                chunks.append(text)
        else:
            payload = msg.get_payload(decode=True)
            if payload is None:
                payload = str(msg.get_payload()).encode("utf-8", "replace")
            chunks.append(payload.decode(msg.get_content_charset() or "utf-8", errors="replace"))
    except Exception:
        return ""
    return "\n".join(chunks)


def msg_date(msg: Message):
    raw = msg.get("Date")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(str(raw))
        if dt and dt.tzinfo:
            dt = dt.astimezone(tz=None)
        return dt
    except Exception:
        return None


# ---------------------------------------------------------------- կատեգորիայի առաջարկ


def propose_category(addr: str, org: str = "", labels: list[str] | None = None, default: str = "Այլ"):
    """Վերադարձնում է (կատեգորիա, պիտակներ, հիմնավորում)։ Միշտ հիմնված է տրամադրված դաշտերի վրա։"""
    labels = labels or []
    tags: list[str] = []
    haystack = " ".join(labels + ([org] if org else [])).casefold()

    if is_role_address(addr) or is_bounce_address(addr):
        tags.append("noreply/ծանուցում" if is_role_address(addr) else "bounce")
        return SERVICES_CATEGORY, tags, "հասցեն ավտոմատ/ծանուցման տիպի է"

    for category, keywords in CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in haystack:
                tags.append("պիտակ՝ " + kw) if kw in " ".join(labels).casefold() else tags.append("կազմակերպություն՝ " + org)
                return category, tags, f"«{kw}» ակնարկը գտնվեց պիտակների/կազմակերպության դաշտում. ստուգել"

    if org:
        tags.append("կազմակերպություն")
        return "Աշխատանքային կապեր", tags, "կազմակերպության դաշտը լրացված է. ստուգել"

    domain = email_key(addr).partition("@")[2]
    if domain in FREE_DOMAINS:
        tags.append("անվճար դոմեն")
        return "Ընկերներ և ծանոթներ", tags, "անվճար դոմեն. առաջարկ"
    if domain:
        tags.append("կորպորատիվ դոմեն")
        return "Աշխատանքային կապեր", tags, "կորպորատիվ դոմեն. առաջարկ"
    return default, tags, ""


# ---------------------------------------------------------------- Գուգլ Կոնտակտներ


def is_google_contacts(fieldnames) -> bool:
    hits = sum(1 for f in (fieldnames or []) if f and GOOGLE_FIELD_RE.match(f.strip()))
    return hits >= 2


def looks_like_contacts_list(fieldnames) -> bool:
    """Արդյոք CSV-ն կոնտակտների ցանկ է (այլ ոչ թե ինչ-որ այլ ցուցակ)։"""
    has_email = any(
        any(k in (f or "").casefold() for k in ("mail", "փոստ", "էլ."))
        for f in (fieldnames or [])
    )
    has_name = any(
        (f or "").strip().casefold() in ("name", "given name", "first name", "family name", "last name", "անուն")
        for f in (fieldnames or [])
    )
    return has_email and has_name


def _gvalue(row: dict, fieldnames, wanted: set[str]) -> str:
    for f in fieldnames or []:
        if f and f.strip().casefold() in wanted:
            value = (row.get(f) or "").strip()
            if value:
                return re.sub(r"\s+", " ", value)
    return ""


def _gvalues(row: dict, fieldnames, pattern: re.Pattern) -> list[str]:
    out: list[str] = []
    for f in fieldnames or []:
        if not f or not pattern.match(f.strip()):
            continue
        value = (row.get(f) or "").strip()
        if value:
            out.append(re.sub(r"\s+", " ", value))
    return out


def parse_google_row(row: dict, fieldnames, row_no: int) -> dict:
    first = _gvalue(row, fieldnames, {"given name", "first name", "անուն"})
    last = _gvalue(row, fieldnames, {"family name", "last name", "ազգանուն"})
    middle = _gvalue(row, fieldnames, {"additional name", "middle name", "միջին անուն"})
    nickname = _gvalue(row, fieldnames, {"nickname", "մականուն"})
    full = _gvalue(row, fieldnames, {"name", "full name", "display name", "անուն ազգանուն"})

    emails: list[str] = []
    for f in fieldnames or []:
        low = (f or "").strip().casefold()
        if not any(k in low for k in ("email", "e-mail", "mail", "փոստ", "էլ.")):
            continue
        for addr in EMAIL_RE.findall((row.get(f) or "").strip()):
            if email_key(addr) not in [email_key(e) for e in emails]:
                emails.append(addr)

    phones: list[str] = []
    for f in fieldnames or []:
        low = (f or "").strip().casefold()
        if "fax" in low:
            continue
        if not any(k in low for k in ("phone", "mobile", "telephone", "հեռախոս", "tel")):
            continue
        value = (row.get(f) or "").strip()
        if value and digits(value) and digits(value) not in [digits(p) for p in phones]:
            phones.append(clean_phone(value))
    cities = _gvalues(row, fieldnames, re.compile(r"^(address\s*\d+\s*-\s*city|city|քաղաք)$", re.I))
    org = _gvalue(row, fieldnames, {"organization 1 - name", "organization name", "company", "կազմակերպություն"})
    title = _gvalue(row, fieldnames, {"organization 1 - title", "job title", "title", "պաշտոն"})
    birthday_raw = _gvalue(row, fieldnames, {"birthday", "ծննդյան օր", "ծննդյան ամսաթիվ"})
    notes = _gvalue(row, fieldnames, {"notes", "note", "նշումներ"})

    labels: list[str] = []
    for value in _gvalues(row, fieldnames,
                          re.compile(r"^(group membership|labels|categories|category|պիտակներ)$", re.I)):
        for part in re.split(r":::|\||,|;", value):
            part = part.strip().lstrip("*").strip()
            if part and part.casefold() not in ("mycontacts", "my contacts", "իմ կոնտակտները"):
                labels.append(part)

    return {
        "row_no": row_no,
        "first": first,
        "last": last,
        "middle": middle,
        "nickname": nickname,
        "full": full,
        "emails": emails,
        "phones": phones,
        "city": cities[0] if cities else "",
        "org": org,
        "title": title,
        "birthday_raw": birthday_raw,
        "birthday": normalize_birthday(birthday_raw),
        "notes": notes,
        "labels": labels,
    }


# ---------------------------------------------------------------- հավաքում


class Collector:
    def __init__(self):
        self.entries: dict[str, dict] = {}
        self.google: dict[str, dict] = {}
        self.no_email: list[dict] = []
        self.csv_rows: Counter = Counter()
        self.plus_groups: dict[str, set] = defaultdict(set)
        self.header_stats: Counter = Counter()
        self.from_counts: Counter = Counter()
        self.to_cc_counts: Counter = Counter()
        self.sources: Counter = Counter()
        self.messages = 0
        self.files = 0
        self.errors = 0

    def add(self, addr: str, name: str, header: str, when, source: str, status_hint: str = "") -> None:
        addr = (addr or "").strip().strip(".,;:")
        if not addr or "@" not in addr or addr.casefold().endswith(".local"):
            return
        key = email_key(addr)
        entry = self.entries.setdefault(
            key,
            {
                "email": addr,
                "names": Counter(),
                "headers": Counter(),
                "sources": Counter(),
                "phones": Counter(),
                "first": None,
                "last": None,
                "status_hints": Counter(),
            },
        )
        clean = clean_name(name, addr)
        if clean:
            entry["names"][clean] += 2 if header == "From" else 1
        entry["headers"][header] += 1
        entry["sources"][source] += 1
        if status_hint:
            entry["status_hints"][status_hint] += 1
        if when:
            if entry["first"] is None or when < entry["first"]:
                entry["first"] = when
            if entry["last"] is None or when > entry["last"]:
                entry["last"] = when
        self.plus_groups[plus_base(addr)].add(key)
        self.header_stats[header] += 1
        if header in ("To", "Cc", "Bcc"):
            self.to_cc_counts[key] += 1
        elif header in ("From", "Reply-To", "Sender"):
            self.from_counts[key] += 1

    def add_phone(self, addr: str, phone: str, when) -> None:
        entry = self.entries.get(email_key(addr))
        if not entry:
            return
        entry["phones"][clean_phone(phone)] += 1
        if when:
            if entry["first"] is None or when < entry["first"]:
                entry["first"] = when
            if entry["last"] is None or when > entry["last"]:
                entry["last"] = when

    def add_google_record(self, rec: dict, source: str) -> None:
        self.sources[source] += 1
        if not rec["emails"]:
            self.no_email.append(rec)
            return
        for addr in rec["emails"]:
            self.add(addr, rec["full"] or f"{rec['first']} {rec['last']}".strip(), "CSV", None, source)
        self.google.setdefault(email_key(rec["emails"][0]), rec)
        for addr in rec["emails"][1:]:
            self.google.setdefault(email_key(addr), rec)
        for addr in rec["emails"]:
            self.csv_rows[email_key(addr)] += 1


def collect_message(msg: Message, collector: Collector, args, source: str) -> None:
    collector.messages += 1
    when = msg_date(msg)
    for header in args.headers:
        for raw in msg.get_all(header, []):
            for name, addr in getaddresses([decode_header_value(raw)]):
                collector.add(addr, name, header, when, source)
    if args.phones:
        text = message_text(msg)
        if text:
            for match in PHONE_RE.finditer(text):
                if plausible_phone(match.group(0)):
                    for _, addr in getaddresses([decode_header_value(msg.get("From", ""))]):
                        collector.add_phone(addr, match.group(0), when)
    if args.from_body:
        text = message_text(msg)
        if text:
            for match in NAME_ADDR_RE.finditer(text):
                collector.add(match.group(2), match.group(1), "մարմին", when, source, "մարմնի տեքստից՝ ստուգել")


def collect_text(text: str, collector: Collector, args, source: str) -> None:
    collector.messages += 1
    taken: set[str] = set()
    for match in NAME_ADDR_RE.finditer(text):
        addr = match.group(2)
        collector.add(addr, match.group(1), "տեքստ", None, source)
        taken.add(email_key(addr))
    for match in EMAIL_RE.finditer(text):
        if email_key(match.group(0)) not in taken:
            collector.add(match.group(0), "", "տեքստ", None, source)


def collect_csv_text(text: str, collector: Collector, args, source: str) -> None:
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except Exception:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    fieldnames = reader.fieldnames or []
    if not fieldnames:
        collect_text(text, collector, args, source)
        return
    collector.files += 1
    if is_google_contacts(fieldnames) or looks_like_contacts_list(fieldnames):
        for n, row in enumerate(reader, 1):
            collector.add_google_record(parse_google_row(row, fieldnames, n), source)
        return
    name_cols = [f for f in fieldnames if (f or "").strip().casefold() in
                 ("name", "full name", "display name", "contact", "first name", "given name", "անուն", "ազգանուն")]
    for row in reader:
        found = False
        for field, value in row.items():
            if value and "@" in value:
                match = EMAIL_RE.search(value)
                if not match:
                    continue
                name = ""
                for nc in name_cols:
                    if row.get(nc):
                        name = " ".join(str(row[nc]).split())
                        break
                collector.add(match.group(0), name, "CSV", None, source)
                found = True
        if not found:
            collect_text(" ".join(str(v) for v in row.values() if v), collector, args, source)


def iter_mbox(fh):
    """mbox հոսքը բաժանում է առանձին նամակների՝ առանց ամբողջ ֆայլը հիշողության մեջ պահելու։"""
    current: list[bytes] = []
    candidate = None
    for line in fh:
        if candidate is not None:
            if HEADER_LINE_RE.match(line):
                if current:
                    yield b"".join(current)
                current = [candidate]
            else:
                current.append(candidate)
            candidate = None
        if line.startswith(b"From ") and len(line) > 6:
            candidate = line
        else:
            current.append(line)
    if candidate is not None:
        if current:
            yield b"".join(current)
        current = [candidate]
    if current:
        yield b"".join(current)


def collect_mbox_stream(fh, collector: Collector, args, source: str) -> None:
    processed = 0
    for raw in iter_mbox(fh):
        if args.max_messages and collector.messages >= args.max_messages:
            break
        if not raw.strip():
            continue
        processed += 1
        try:
            collect_message(BytesParser(policy=policy.default).parsebytes(raw), collector, args, source)
        except Exception:
            collector.errors += 1
    if processed == 0:
        try:
            fh.seek(0)
        except Exception:
            return
        collect_text(fh.read().decode("utf-8", errors="replace"), collector, args, source)


def input_files(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]


def scan(input_path: Path, collector: Collector, args) -> None:
    for path in input_files(input_path):
        suffix = path.suffix.casefold()
        source = path.name
        try:
            if suffix == ".zip":
                with zipfile.ZipFile(path) as zf:
                    for info in zf.infolist():
                        if info.is_dir():
                            continue
                        low = info.filename.casefold()
                        if not low.endswith((".mbox", ".mbx", ".eml", ".txt", ".csv", ".json")):
                            continue
                        if args.max_messages and collector.messages >= args.max_messages:
                            break
                        if low.endswith((".mbox", ".mbx")):
                            with zf.open(info) as fh:
                                collect_mbox_stream(fh, collector, args, f"{source}:{info.filename}")
                        elif low.endswith(".eml"):
                            try:
                                collect_message(
                                    BytesParser(policy=policy.default).parsebytes(zf.read(info)),
                                    collector, args, f"{source}:{info.filename}",
                                )
                            except Exception:
                                collector.errors += 1
                        elif low.endswith(".csv"):
                            collect_csv_text(zf.read(info).decode("utf-8", errors="replace"),
                                             collector, args, f"{source}:{info.filename}")
                        else:
                            collect_text(zf.read(info).decode("utf-8", errors="replace"),
                                         collector, args, f"{source}:{info.filename}")
            elif suffix in (".mbox", ".mbx"):
                with path.open("rb") as fh:
                    collect_mbox_stream(fh, collector, args, source)
            elif suffix == ".eml":
                collect_message(BytesParser(policy=policy.default).parsebytes(path.read_bytes()), collector, args, source)
            elif suffix == ".csv":
                collect_csv_text(path.read_text(encoding="utf-8-sig", errors="replace"), collector, args, source)
            else:
                collect_text(path.read_text(encoding="utf-8-sig", errors="replace"), collector, args, source)
        except Exception as exc:  # noqa: BLE001
            collector.errors += 1
            print(f"⚠ Չհաջողվեց կարդալ `{path.name}`՝ {exc}", file=sys.stderr)


# ---------------------------------------------------------------- տողերի կառուցում


def split_name(full: str) -> tuple[str, str, str]:
    tokens = [t for t in re.split(r"\s+", full.strip()) if t]
    if len(tokens) == 2:
        return tokens[0], tokens[1], "անուն/ազգանուն բաժանումը ենթադրությամբ է (Header-ի ձևաչափից). ստուգել"
    return full, "", "անունը մեկ դաշտում է. անուն/ազգանուն բաժանելը՝ ձեռքով"


def build_email_row(key: str, entry: dict, collector: Collector, args, db_index: dict) -> dict:
    rec = collector.google.get(key) or {}
    notes: list[str] = []
    source_label = "Էլ. փոստի արտահանում"
    for s, _ in entry["sources"].most_common(1):
        if ".csv" in s.casefold() or "csv" in s.casefold():
            source_label = "Գուգլ Կոնտակտների արտահանում"
        else:
            source_label = "Էլ. փոստի արտահանում"
    if rec:
        source_label = "Գուգլ Կոնտակտների արտահանում"

    first = rec.get("first", "")
    last = rec.get("last", "")
    if rec and not first and not last and rec.get("full"):
        first, last, note = split_name(rec["full"])
        if note:
            notes.append(note)
    if not rec:
        name_counts = entry["names"]
        full_name = name_counts.most_common(1)[0][0] if name_counts else ""
        if len(name_counts) > 1:
            notes.append("անվան տարբերակներ՝ " + "; ".join(n for n, _ in name_counts.most_common()) + ". ստուգել")
        if full_name:
            first, last, note = split_name(full_name)
            if note:
                notes.append(note)
        else:
            notes.append("անուն չի գտնվել. Ստուգման ենթակա")
    if rec.get("middle"):
        notes.append(f"միջին անուն՝ {rec['middle']}. ազգանվան հետ միացնելը՝ ձեռքով")
    if rec.get("title"):
        notes.append(f"պաշտոն՝ {rec['title']}")

    phones = list(rec.get("phones") or []) + [p for p, _ in entry["phones"].most_common()]
    seen: list[str] = []
    for p in phones:
        if digits(p) and digits(p) not in [digits(x) for x in seen]:
            seen.append(p)
    main_phone = seen[0] if seen else ""
    alt_phone = seen[1] if len(seen) > 1 else ""
    if len(seen) > 2:
        notes.append(f"այլ համարներ էլ կան ({len(seen) - 2}). ստուգել")
    if main_phone and not main_phone.startswith("+"):
        notes.append("Երկիրը ստուգել")

    if rec.get("birthday_raw") and not rec.get("birthday"):
        notes.append(f"ծննդյան օրը չհաջողվեց վերլուծել՝ «{rec['birthday_raw']}». Երկիրը/ձևաչափը ստուգել")
    if rec.get("notes"):
        notes.append("աղբյուրի նշում՝ " + re.sub(r"\s+", " ", rec["notes"])[:200])

    primary_addr = email_key(rec["emails"][0]) if rec.get("emails") else ""
    extra_email = bool(primary_addr and key != primary_addr)
    if extra_email:
        main_shown = primary_addr if not args.mask_file else mask_email(primary_addr, False)
        notes.append(f"նույն Կոնտակտների գրառումից լրացուցիչ հասցե է (հիմնական՝ {main_shown}). ՄԻԱՎՈՐՈՒՄ ՉԻ ԿԱՏԱՐՎԵԼ")

    category, cat_tags, reason = propose_category(key, rec.get("org", ""), rec.get("labels", []), args.default_category)
    if reason:
        notes.append(reason)
    base_tag = "Կոնտակտների ցանկից" if rec else "փոստարկղից"
    tags = [base_tag] + cat_tags + [lbl for lbl in rec.get("labels", [])[:3] if lbl.casefold() not in
                                    (t.casefold() for t in cat_tags)]
    if extra_email:
        tags.append("լրացուցիչ հասցե")
    if collector.csv_rows.get(key, 0) > 1:
        notes.append(f"աղբյուրի ցանկում այս հասցեն կա {collector.csv_rows[key]} տողում. կրկնությունը չի միավորվել")
        tags.append("ցանկում կրկնվող")
    tags = [t for t in tags if t]
    if is_bounce_address(key):
        tags.append("չուղարկել")

    status = "Նոր"
    if not (first or last) or not rec and not entry["names"]:
        status = "Ստուգման ենթակա"
    if is_role_address(key) or is_bounce_address(key) or entry["status_hints"]:
        status = "Ստուգման ենթակա"
    if entry["status_hints"]:
        notes.extend(f"{h} ({c})" for h, c in entry["status_hints"].most_common())

    count = sum(entry["headers"].values())
    if db_index.get("emails", {}).get(key):
        notes.append(f"հնարավոր կրկնվող՝ արդեն բազայում (տող {db_index['emails'][key]}). ՄԻԱՎՈՐՈՒՄ ՉԻ ԿԱՏԱՐՎԵԼ")
        tags.append("արդեն բազայում")
        status = "Ստուգման ենթակա"

    domain = key.partition("@")[2]
    header_names = {h for h in entry["headers"]}
    only_csv = header_names.issubset({"CSV"})
    return {
        "_sort_count": count,
        "_primary": not extra_email,
        "Անուն": first,
        "Ազգանուն": last,
        "Մականուն": rec.get("nickname", ""),
        "Հիմնական հեռախոս": main_phone,
        "Լրացուցիչ հեռախոս": alt_phone,
        "Էլ. փոստ": entry["email"] if not args.mask_file else mask_email(entry["email"], False),
        "Կատեգորիա": category,
        "Պիտակներ": "; ".join(tags),
        "Քաղաք": rec.get("city", ""),
        "Ծննդյան օր": rec.get("birthday", ""),
        "Կարևորություն": "",
        "Ծանոթության աղբյուր": source_label,
        "Վերջին շփում": entry["last"].date().isoformat() if entry["last"] else "",
        "Նշումներ": "; ".join(notes),
        "Կարգավիճակ": status,
        "Դոմեն": domain,
        "Աղբյուր": "Գուգլ Կոնտակտների CSV" if rec else
                   (", ".join(f"{h}·{c}" for h, c in entry["headers"].most_common()) or "CSV"),
        "Հանդիպումներ": "" if only_csv else str(count),
        "Առաջին անգամ": entry["first"].date().isoformat() if entry["first"] else "",
        "Վերջին անգամ": entry["last"].date().isoformat() if entry["last"] else "",
    }


def build_no_email_row(rec: dict, args) -> dict:
    notes: list[str] = []
    phones = list(rec.get("phones") or [])
    main_phone = phones[0] if phones else ""
    alt_phone = phones[1] if len(phones) > 1 else ""
    if not main_phone:
        notes.append("ոչ էլ. փոստ, ոչ հեռախոս՝ գրառումը գրեթե դատարկ է. ստուգել")
    else:
        notes.append("էլ. փոստ չկա. ստուգել՝ լրացնե՞լ, թե՞ թողնել առանց հասցեի")
    if main_phone and not main_phone.startswith("+"):
        notes.append("Երկիրը ստուգել")
    if rec.get("birthday_raw") and not rec.get("birthday"):
        notes.append("ծննդյան օրը չհաջողվեց վերլուծել. ձևաչափը ստուգել")
    if rec.get("notes"):
        notes.append("աղբյուրի նշում՝ " + re.sub(r"\s+", " ", rec["notes"])[:200])

    category, cat_tags, reason = propose_category("", rec.get("org", ""), rec.get("labels", []), "Այլ")
    if reason:
        notes.append(reason)
    tags = ["հեռախոսի կոնտակտից", "առանց էլ. փոստի"] + cat_tags
    return {
        "_sort_count": 0,
        "_primary": True,
        "Անուն": rec.get("first", ""),
        "Ազգանուն": rec.get("last", ""),
        "Մականուն": rec.get("nickname", ""),
        "Հիմնական հեռախոս": main_phone,
        "Լրացուցիչ հեռախոս": alt_phone,
        "Էլ. փոստ": "",
        "Կատեգորիա": category,
        "Պիտակներ": "; ".join(t for t in tags if t),
        "Քաղաք": rec.get("city", ""),
        "Ծննդյան օր": rec.get("birthday", ""),
        "Կարևորություն": "",
        "Ծանոթության աղբյուր": "Գուգլ Կոնտակտների արտահանում",
        "Վերջին շփում": "",
        "Նշումներ": "; ".join(notes),
        "Կարգավիճակ": "Ստուգման ենթակա",
        "Դոմեն": "",
        "Աղբյուր": "CSV (առանց էլ. փոստի)",
        "Հանդիպումներ": "1",
        "Առաջին անգամ": "",
        "Վերջին անգամ": "",
    }


def build_rows(collector: Collector, args, db_index: dict) -> list[dict]:
    rows = [build_email_row(key, entry, collector, args, db_index) for key, entry in collector.entries.items()]
    rows += [build_no_email_row(rec, args) for rec in collector.no_email]
    rows.sort(key=lambda r: (
        CATEGORY_ORDER.get(r["Կատեգորիա"], 99),
        -int(r.get("_sort_count") or 0),
        "" if r.get("_primary") else "~",  # հիմնական հասցեն՝ առաջինը
        r["Ազգանուն"],
        r["Էլ. փոստ"],
    ))
    return rows


def is_service_row(row: dict) -> bool:
    addr = row.get("Էլ. փոստ", "")
    if addr and (is_role_address(addr) or is_bounce_address(addr)):
        return True
    return row.get("Կատեգորիա") == SERVICES_CATEGORY


def load_db_index(path: Path | None) -> dict:
    index: dict = {"emails": {}}
    if not path or not path.exists():
        return index
    rows, _, _ = read_contacts(path)
    for i, row in enumerate(rows, 1):
        addr = norm_email(row.get("Էլ. փոստ", ""))
        if addr:
            index["emails"].setdefault(addr, i)
    return index


def write_file(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    try:
        os.chmod(out_path, 0o600)
    except OSError:
        pass


def services_path_for(out_path: Path) -> Path:
    return out_path.with_name(f"{out_path.stem}-services{out_path.suffix}")


# ---------------------------------------------------------------- ամփոփում


def console_summary(collector: Collector, people: list[dict], services: list[dict], args,
                    out_path: Path, services_path: Path | None) -> str:
    """Կառուցում է ամփոփման տեքստը (հասցեները դիմակավորված), տպում ու վերադարձնում այն։"""
    show = args.show_emails
    lines: list[str] = []
    lines.append("")
    lines.append("=" * 62)
    lines.append("ԱՄՓՈՓՈՒՄ (հասցեները դիմակավորված են)" if not show else "ԱՄՓՈՓՈՒՄ")
    lines.append("=" * 62)
    if collector.messages:
        lines.append(f"Մշակված նամակ/տեքստային ֆայլ՝ {collector.messages}")
    lines.append(f"Մշակված CSV՝ {collector.files}")
    lines.append(f"Մարդկանց գրառում՝ {len(people)}")
    if services:
        lines.append(f"Ծառայությունների/ծանուցումների գրառում՝ {len(services)} → {services_path}")
    lines.append(f"Առանց էլ. փոստի գրառում՝ {sum(1 for r in people if not r['Էլ. փոստ'])}")
    lines.append(f"Կարդալու սխալ՝ {collector.errors}")
    lines.append(f"Արդյունքային ֆայլ՝ {out_path} (իրավունքներ՝ 600)")

    def counts(rows, key):
        return Counter(r[key] for r in rows)

    if people:
        lines.append("")
        lines.append("Հիմնական ֆայլի գրառումները՝ ըստ կատեգորիայի (առաջարկ).")
        for cat, cnt in sorted(counts(people, "Կատեգորիա").items(), key=lambda t: CATEGORY_ORDER.get(t[0], 99)):
            lines.append(f"  • {cat}: {cnt}")
        lines.append("")
        lines.append("Գրառումները՝ ըստ կարգավիճակի.")
        for st, cnt in sorted(counts(people, "Կարգավիճակ").items()):
            lines.append(f"  • {st}: {cnt}")
        domains = Counter(r["Դոմեն"] for r in people if r["Դոմեն"])
        if domains:
            lines.append("")
            lines.append("Լավագույն դոմեններ.")
            for dom, cnt in domains.most_common(10):
                lines.append(f"  • {dom}: {cnt}")

    duplicates = [r for r in people + services if "արդեն բազայում" in r["Պիտակներ"]]
    if duplicates:
        lines.append("")
        lines.append(f"⚠ Արդեն բազայում հնարավոր կրկնվող՝ {len(duplicates)} (միավորում ՉԻ կատարվել)")
    csv_dupes = [r for r in people + services if "ցանկում կրկնվող" in r["Պիտակներ"]]
    if csv_dupes:
        lines.append("")
        lines.append(f"⚠ Աղբյուրի ցանկում կրկնվող հասցեներ՝ {len(csv_dupes)} (միավորում ՉԻ ԿԱՏԱՐՎԵԼ)")
    extra_rows = [r for r in people + services if "լրացուցիչ հասցե" in r["Պիտակներ"]]
    if extra_rows:
        lines.append("")
        lines.append(f"ℹ Նույն գրառումից լրացուցիչ էլ. հասցեներ՝ {len(extra_rows)} (առանձին տողերով)")
    need_check = [r for r in people + services if r["Կարգավիճակ"] == "Ստուգման ենթակա"]
    if need_check:
        lines.append("")
        lines.append(f"ℹ Ստուգման ենթակա գրառումներ՝ {len(need_check)} (նշվա՞ծ են Նշումներ սյունակում)")
    plus_dupes = {base: keys for base, keys in collector.plus_groups.items() if len(keys) > 1}
    if plus_dupes:
        lines.append("")
        lines.append(f"⚠ Նույն հասցեի +tag տարբերակներ՝ {len(plus_dupes)} խումբ (միավորում ՉԻ ԿԱՏԱՐՎԵԼ)՝")
        for base, keys in list(plus_dupes.items())[:5]:
            lines.append("   " + ", ".join(mask_email(k, show) for k in sorted(keys)))

    self_candidates = [
        k for k, _ in collector.to_cc_counts.most_common(5)
        if collector.to_cc_counts[k] >= SELF_CANDIDATE_MIN and not collector.from_counts.get(k)
    ]
    if self_candidates:
        lines.append("")
        lines.append("Հնարավոր է քո սեփական հասցեն (միայն To/Cc-ում է հանդիպում)՝")
        for k in self_candidates:
            lines.append(f"   • {mask_email(k, show)} — բաց թողնելու համար՝ --me {mask_email(k, show)}")

    preview = people[:10] if not show else people[:20]
    if preview:
        lines.append("")
        lines.append("Առաջին տողերը (դիմակավորված).")
        for row in preview:
            name = " ".join(p for p in (row["Անուն"], row["Ազգանուն"]) if p) or "—"
            contact = row["Էլ. փոստ"] or row["Հիմնական հեռախոս"] or "—"
            lines.append(f"  • {name} | {contact} | {row['Կատեգորիա']} | {row['Կարգավիճակ']}")
    lines.append("")
    lines.append("Հիշեցում՝ աղբյուր ֆայլերը չեն փոփոխվել, ոչինչ չի ուղարկվել, ոչ մի գրառում միավորված չէ։")

    text = "\n".join(lines)
    print(text)
    return text


# ---------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Կոնտակտների հավաքում փոստարկղից/Կոնտակտներից՝ մեկ կամ երկու ֆայլով")
    p.add_argument("--input", required=True, help="Մուտք՝ Գուգլ Կոնտակտների CSV / .csv / .txt / .mbox / .eml / .zip / պանակ")
    p.add_argument("--out", default="reports/contacts-import.csv", help="Հիմնական ֆայլը (մարդիկ)")
    p.add_argument("--services-out", help="Ծառայությունների ֆայլը (լռելյայն՝ <out>-services.csv)")
    p.add_argument("--no-split-services", action="store_true", help="Ամեն ինչ մեկ ֆայլում")
    p.add_argument("--against", help="Գործող բազայի contacts.csv՝ կրկնվողներին նշելու համար")
    p.add_argument("--headers", default=",".join(DEFAULT_HEADERS), help="Որ header-ներից հավաքել (նամակների դեպքում)")
    p.add_argument("--from-body", action="store_true", help="Հասցեներ նաև նամակի մարմնից")
    p.add_argument("--phones", action="store_true", help="Հեռախոսահամարներ ստորագրություններից (նամակների դեպքում)")
    p.add_argument("--min-count", type=int, default=1, help="Հեռացնել ավելի քիչ հանդիպումներ ունեցող հասցեները")
    p.add_argument("--me", action="append", default=[], help="Բաց թողնել սեփական հասցեները (կրկնելի)")
    p.add_argument("--default-category", default="Այլ", choices=CATEGORIES)
    p.add_argument("--no-split-names", action="store_true", help="Անուն/ազգանուն չեն բաժանվում (միայն Header-ի ձևաչափի համար)")
    p.add_argument("--mask-file", action="store_true", help="Ֆայլում էլ. հասցեները դիմակավորել (եթե ֆայլը կիսում ես)")
    p.add_argument("--show-emails", action="store_true", help="Տերմինալում ցույց տալ ամբողջական հասցեները")
    p.add_argument("--summary-out", help="Դիմակավորված ամփոփումը գրել այս ֆայլում (կիսելու համար անվտանգ)")
    p.add_argument("--max-messages", type=int, default=0, help="Սահմանափակել նամակների քանակը (թեստի համար)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.headers = [h.strip() for h in args.headers.split(",") if h.strip()]

    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        print(f"Մուտքը չի գտնվել՝ {input_path}", file=sys.stderr)
        return 2

    collector = Collector()
    skipped_me = {email_key(a) for a in args.me}
    skipped_me_bases = {plus_base(a) for a in skipped_me}

    scan(input_path, collector, args)

    for key in list(collector.entries):
        if key in skipped_me or plus_base(key) in skipped_me_bases:
            del collector.entries[key]
    if args.min_count > 1:
        for key in list(collector.entries):
            if sum(collector.entries[key]["headers"].values()) < args.min_count:
                del collector.entries[key]

    db_index = load_db_index(Path(args.against)) if args.against else {"emails": {}}
    rows = build_rows(collector, args, db_index)

    if not rows:
        print("Ոչ մի գրառում չգտնվեց։ Ստուգիր մուտքի ֆայլը կամ --headers արժեքը։", file=sys.stderr)
        return 1

    if args.no_split_services:
        people, services = rows, []
    else:
        people = [r for r in rows if not is_service_row(r)]
        services = [r for r in rows if is_service_row(r)]
        if not people:  # բոլորը ծառայություններ են. մի՛ դատարկիր հիմնական ֆայլը
            people, services = rows, []

    out_path = Path(args.out)
    write_file(people, out_path)
    services_path = None
    if services:
        services_path = Path(args.services_out) if args.services_out else services_path_for(out_path)
        write_file(services, services_path)

    text = console_summary(collector, people, services, args, out_path, services_path)
    if args.summary_out:
        summary_path = Path(args.summary_out)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(text, encoding="utf-8")
        try:
            os.chmod(summary_path, 0o600)
        except OSError:
            pass
        print(f"\nԴիմակավորված ամփոփումը գրված է՝ {summary_path} (բոլոր հասցեները դիմակավորված են)։")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
