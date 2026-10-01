#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_emails.py — փոստարկղի արտահանումից կոնտակտների/հասցեների հավաքում ՄԵԿ ֆայլով։

Աջակցվող մուտքեր
  • .mbox            — Gmail/Thunderbird արտահանում
  • .eml             — մեկ ֆայլ կամ .eml ֆայլերով պանակ
  • .zip             — օր.՝ Google Takeout արխիվ (կարդացվում է հիշողության մեջ, արխիվը սկավառակի վրա չի բացվում)
  • .txt / .json / .csv — հասցեների պարզ սկանավորում

ԱՆՎՏԱՆԳՈՒԹՅԱՆ ԿԱՆՈՆՆԵՐ (պարտադիր)
  1. Միայն ԿԱՐԴՈՒՄ է. մուտքային ֆայլերը երբեք չեն փոփոխվում, չեն ջնջվում, չեն տեղափոխվում։
  2. Ցանց ՉԻ օգտագործվում. միայն Python ստանդարտ գրադարան, ամբողջովին օֆլայն։
  3. Ոչինչ չի ուղարկվում, ոչ մի նամակի չի պատասխանվում, ոչինչ չի նշվում կարդացված։
  4. Նամակների ԲՈՎԱՆԴԱԿՈՒԹՅՈՒՆԸ և հավելվածները ՉԵՆ պահվում. միայն անուն/հասցե/հեռախոս/ամսաթիվ։
  5. Տերմինալում հասցեները ցուցադրվում են ԴԻՄԱԿԱՎՈՐՎԱԾ (բացելու համար՝ --show-emails)։
  6. Արդյունքային ֆայլի իրավունքները՝ 0600 (միայն սեփականատերը)։
  7. Ոչ մի կոնտակտ չի ՄԻԱՎՈՐՎՈՒՄ կամ ՋՆՋՎՈՒՄ. ցուցադրվում են միայն առաջարկներ ու նշումներ։

Օրինակ
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
from contacts import (  # noqa: E402
    CATEGORIES,
    FIELDS,
    PHONE_FIELDS,
    digits,
    mask_phone,
    norm_email,
    read_contacts,
)

HELPER_FIELDS = ["Դոմեն", "Աղբյուր (header)", "Հանդիպումներ", "Առաջին անգամ", "Վերջին անգամ"]
OUT_FIELDS = FIELDS + HELPER_FIELDS

DEFAULT_HEADERS = ["From", "To", "Cc", "Reply-To", "Sender"]
SELF_CANDIDATE_MIN = 3

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
    "authentication-results", "list-unsubscribe", "x-mailer", "message-id", "in-reply-to",
    "references", "list-id", "precedence", "errors-to", "x-original-to", "x-spam-status",
}

FREE_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "hotmail.com", "outlook.com",
    "live.com", "msn.com", "icloud.com", "me.com", "mac.com", "aol.com", "proton.me",
    "protonmail.com", "mail.ru", "bk.ru", "inbox.ru", "list.ru", "yandex.ru", "yandex.com",
    "rambler.ru", "zoho.com", "gmx.com", "gmx.de", "mail.com", "tutanota.com",
}

CATEGORY_ORDER = {c: i for i, c in enumerate(CATEGORIES)}


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
    local = email_key(addr).partition("@")[0]
    return bool(ROLE_LOCAL_RE.match(local))


def is_bounce_address(addr: str) -> bool:
    local = email_key(addr).partition("@")[0]
    return bool(BOUNCE_LOCAL_RE.match(local))


def clean_phone(raw: str) -> str:
    return re.sub(r"\s+", " ", (raw or "").strip()).strip(" ,;.")


def plausible_phone(raw: str) -> bool:
    d = digits(raw)
    return 8 <= len(d) <= 15 and not d.startswith("000")


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
            charset = msg.get_content_charset() or "utf-8"
            chunks.append(payload.decode(charset, errors="replace"))
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


# ---------------------------------------------------------------- հավաքում


class Collector:
    def __init__(self):
        self.entries: dict[str, dict] = {}
        self.plus_groups: dict[str, set] = defaultdict(set)
        self.header_stats: Counter = Counter()
        self.from_counts: Counter = Counter()
        self.to_cc_counts: Counter = Counter()
        self.messages = 0
        self.errors = 0

    def add(self, addr: str, name: str, header: str, when, source: str, status_hint: str = "") -> None:
        addr = (addr or "").strip().strip(".,;:")
        if not addr or "@" not in addr:
            return
        if addr.casefold().endswith((".local",)):
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
        key = email_key(addr)
        entry = self.entries.get(key)
        if not entry:
            return
        entry["phones"][clean_phone(phone)] += 1
        if when:
            if entry["first"] is None or when < entry["first"]:
                entry["first"] = when
            if entry["last"] is None or when > entry["last"]:
                entry["last"] = when


def collect_message(msg: Message, collector: Collector, args, source: str) -> None:
    collector.messages += 1
    when = msg_date(msg)
    for header in args.headers:
        for raw in msg.get_all(header, []):
            decoded = decode_header_value(raw)
            for name, addr in getaddresses([decoded]):
                collector.add(addr, name, header, when, source)
    if args.phones:
        text = message_text(msg)
        if text:
            for match in PHONE_RE.finditer(text):
                raw_phone = match.group(0)
                if not plausible_phone(raw_phone):
                    continue
                for _, addr in getaddresses([decode_header_value(msg.get("From", ""))]):
                    collector.add_phone(addr, raw_phone, when)
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
        addr = match.group(0)
        if email_key(addr) in taken:
            continue
        collector.add(addr, "", "տեքստ", None, source)
    if args.phones:
        for match in PHONE_RE.finditer(text):
            if plausible_phone(match.group(0)):
                # հասցեին կապելու հիմք չկա. գրանցվում է միայն հաշվետվության նշման համար
                collector.header_stats["հեռախոս (առանց հասցեի)"] += 1


def collect_csv_text(text: str, collector: Collector, args, source: str) -> None:
    collector.messages += 1
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except Exception:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        collect_text(text, collector, args, source)
        return
    name_keys = {
        "name", "full name", "display name", "contact", "first name", "given name",
        "անուն", "անուն ազգանուն", "ազգանուն",
    }
    name_cols = [f for f in reader.fieldnames if (f or "").strip().casefold() in name_keys]
    for row in reader:
        found = False
        for field, value in row.items():
            if not value:
                continue
            if "@" in value:
                addr_match = EMAIL_RE.search(value)
                if not addr_match:
                    continue
                name = ""
                for nc in name_cols:
                    if row.get(nc):
                        name = " ".join(str(row[nc]).split())
                        break
                collector.add(addr_match.group(0), name, "CSV", None, source)
                found = True
        if not found:
            collect_text(" ".join(str(v) for v in row.values() if v), collector, args, source)


def iter_mbox(fh):
    """mbox հոսքը բաժանում է առանձին նամակների՝ մեկական, առանց ամբողջ ֆայլը հիշողության մեջ պահելու։

    Բաժանիչ է համարվում «From »-ով սկսվող այն տողը, որին հաջորդում է header-անման տող
    (ստորագրության «From …» տողերը չեն բաժանում)։
    """
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
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.is_file())
    return [path]


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
                                msg = BytesParser(policy=policy.default).parsebytes(zf.read(info))
                                collect_message(msg, collector, args, f"{source}:{info.filename}")
                            except Exception:
                                collector.errors += 1
                        elif low.endswith(".csv"):
                            collect_csv_text(
                                zf.read(info).decode("utf-8", errors="replace"), collector, args, f"{source}:{info.filename}"
                            )
                        else:
                            collect_text(
                                zf.read(info).decode("utf-8", errors="replace"), collector, args, f"{source}:{info.filename}"
                            )
            elif suffix in (".mbox", ".mbx"):
                with path.open("rb") as fh:
                    collect_mbox_stream(fh, collector, args, source)
            elif suffix == ".eml":
                msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
                collect_message(msg, collector, args, source)
            elif suffix == ".csv":
                collect_csv_text(path.read_text(encoding="utf-8-sig", errors="replace"), collector, args, source)
            else:
                collect_text(path.read_text(encoding="utf-8", errors="replace"), collector, args, source)
        except Exception as exc:  # noqa: BLE001
            collector.errors += 1
            print(f"⚠ Չհաջողվեց կարդալ `{path.name}`՝ {exc}", file=sys.stderr)


# ---------------------------------------------------------------- արդյունք


def split_name(full: str) -> tuple[str, str, str]:
    """Վերադարձնում է (անուն, ազգանուն, նշում)։ Ենթադրությունը միշտ նշվում է։"""
    tokens = [t for t in re.split(r"\s+", full.strip()) if t]
    if len(tokens) == 2:
        return tokens[0], tokens[1], "անուն/ազգանուն բաժանումը ենթադրությամբ է (Header-ի ձևաչափից). ստուգել"
    return full, "", "անունը մեկ դաշտում է. անուն/ազգանուն բաժանելը՝ ձեռքով"


def propose_category(addr: str, default: str = "Այլ") -> tuple[str, list[str]]:
    local, _, domain = email_key(addr).partition("@")
    tags: list[str] = []
    if is_role_address(addr) or is_bounce_address(addr):
        tags.append("noreply/ծանուցում" if is_role_address(addr) else "bounce")
        return "Ծառայություններ", tags
    if domain in FREE_DOMAINS:
        tags.append("անվճար դոմեն")
        return "Ընկերներ և ծանոթներ", tags
    if domain:
        tags.append("կորպորատիվ դոմեն")
        return "Աշխատանքային կապեր", tags
    return default, tags


def build_rows(collector: Collector, args, db_index: dict) -> list[dict]:
    rows: list[dict] = []
    for key, entry in collector.entries.items():
        name_counts = entry["names"]
        full_name = name_counts.most_common(1)[0][0] if name_counts else ""
        notes: list[str] = []
        if len(name_counts) > 1:
            variants = "; ".join(n for n, _ in name_counts.most_common())
            notes.append(f"անվան տարբերակներ՝ {variants}. ստուգել")
        if full_name:
            first, last, note = split_name(full_name) if not args.no_split_names else (full_name, "", "անունը մեկ դաշտում է (--no-split-names)")
            if note:
                notes.append(note)
        else:
            first, last = "", ""
            notes.append("անուն չի գտնվել. Ստուգման ենթակա")

        phones = [p for p, _ in entry["phones"].most_common()]
        main_phone = phones[0] if phones else ""
        alt_phone = phones[1] if len(phones) > 1 else ""
        if phones and not main_phone.startswith("+"):
            notes.append("Երկիրը ստուգել")
        if len(phones) > 2:
            notes.append(f"այլ համարներ էլ կան ({len(phones) - 2}). ստուգել")

        domain = key.partition("@")[2]
        category, cat_tags = propose_category(key, args.default_category)
        tags = ["փոստարկղից"] + cat_tags
        if is_bounce_address(key):
            tags.append("չուղարկել")

        status = "Նոր"
        if not full_name or is_role_address(key) or is_bounce_address(key):
            status = "Ստուգման ենթակա"
        if entry["status_hints"]:
            notes.extend(f"{h} ({c})" for h, c in entry["status_hints"].most_common())
            status = "Ստուգման ենթակա"

        count = sum(entry["headers"].values())
        if db_index.get("emails", {}).get(key):
            row_ref = db_index["emails"][key]
            notes.append(f"հնարավոր կրկնվող՝ արդեն բազայում (տող {row_ref}). ՄԻԱՎՈՐՈՒՄ ՉԻ ԿԱՏԱՐՎԵԼ")
            tags.append("արդեն բազայում")
            status = "Ստուգման ենթակա"

        headers_txt = ", ".join(f"{h}·{c}" for h, c in entry["headers"].most_common())
        rows.append(
            {
                "Անուն": first,
                "Ազգանուն": last,
                "Մականուն": "",
                "Հիմնական հեռախոս": main_phone,
                "Լրացուցիչ հեռախոս": alt_phone,
                "Էլ. փոստ": entry["email"] if not args.mask_file else mask_email(entry["email"], False),
                "Կատեգորիա": category,
                "Պիտակներ": "; ".join(tags),
                "Քաղաք": "",
                "Ծննդյան օր": "",
                "Կարևորություն": "",
                "Ծանոթության աղբյուր": "Էլ. փոստի արտահանում",
                "Վերջին շփում": entry["last"].date().isoformat() if entry["last"] else "",
                "Նշումներ": "; ".join(notes),
                "Կարգավիճակ": status,
                "Դոմեն": domain,
                "Աղբյուր (header)": headers_txt,
                "Հանդիպումներ": str(count),
                "Առաջին անգամ": entry["first"].date().isoformat() if entry["first"] else "",
                "Վերջին անգամ": entry["last"].date().isoformat() if entry["last"] else "",
            }
        )

    rows.sort(key=lambda r: (CATEGORY_ORDER.get(r["Կատեգորիա"], 99), -(int(r["Հանդիպումներ"] or 0)), r["Էլ. փոստ"]))
    return rows


def load_db_index(path: Path | None) -> dict:
    index: dict = {"emails": {}}
    if not path or not path.exists():
        return index
    rows, _, _ = read_contacts(path)
    for i, row in enumerate(rows, 1):
        email_addr = norm_email(row.get("Էլ. փոստ", ""))
        if email_addr:
            index["emails"].setdefault(email_addr, i)
    return index


def write_file(rows: list[dict], out_path: Path, delimiter: str = ",") -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    try:
        os.chmod(out_path, 0o600)
    except OSError:
        pass


def console_summary(collector: Collector, rows: list[dict], args, out_path: Path) -> None:
    show = args.show_emails
    total = len(rows)
    by_cat = Counter(r["Կատեգորիա"] for r in rows)
    by_status = Counter(r["Կարգավիճակ"] for r in rows)
    by_domain = Counter(r["Դոմեն"] for r in rows if r["Դոմեն"])
    duplicates = [r for r in rows if "արդեն բազայում" in r["Պիտակներ"]]
    plus_dupes = {base: keys for base, keys in collector.plus_groups.items() if len(keys) > 1}

    print("")
    print("=" * 62)
    print("ԱՄՓՈՓՈՒՄ (հասցեները դիմակավորված են)" if not show else "ԱՄՓՈՓՈՒՄ")
    print("=" * 62)
    print(f"Մշակված նամակ/ֆայլ՝ {collector.messages}")
    print(f"Եզակի հասցե՝ {total}")
    print(f"Կարդալու սխալ՝ {collector.errors}")
    print(f"Արդյունքային ֆայլ՝ {out_path} (իրավունքներ՝ 600)")
    print("")
    print("Ըստ կատեգորիայի (առաջարկ).")
    for cat, cnt in sorted(by_cat.items(), key=lambda t: CATEGORY_ORDER.get(t[0], 99)):
        print(f"  • {cat}: {cnt}")
    print("")
    print("Ըստ կարգավիճակի.")
    for st, cnt in sorted(by_status.items()):
        print(f"  • {st}: {cnt}")
    if by_domain:
        print("")
        print("Լավագույն դոմեններ.")
        for dom, cnt in by_domain.most_common(10):
            print(f"  • {dom}: {cnt}")
    if duplicates:
        print("")
        print(f"⚠ Արդեն բազայում հնարավոր կրկնվող՝ {len(duplicates)} (միավորում ՉԻ կատարվել)")
    if plus_dupes:
        print("")
        print(f"⚠ Նույն հասցեի +tag տարբերակներ՝ {len(plus_dupes)} խումբ (միավորում ՉԻ կատարվել, ստուգել ձեռքով)՝")
        for base, keys in list(plus_dupes.items())[:5]:
            print("   " + ", ".join(mask_email(k, show) for k in sorted(keys)))

    self_candidates = [
        k for k, _ in collector.to_cc_counts.most_common(5)
        if collector.to_cc_counts[k] >= SELF_CANDIDATE_MIN and not collector.from_counts.get(k)
    ]
    if self_candidates:
        print("")
        print("Հնարավոր է քո սեփական հասցեն (միայն To/Cc-ում է հանդիպում)՝")
        for k in self_candidates:
            print(f"   • {mask_email(k, show)} — բաց թողնելու համար՝ --me {mask_email(k, show)}")

    print("")
    print("Առաջին 10 տող (դիմակավորված).")
    for row in rows[:10] if not show else rows[:20]:
        name = " ".join(p for p in (row["Անուն"], row["Ազգանուն"]) if p) or "—"
        print(
            f"  • {name} | {mask_email(row['Էլ. փոստ'], show)} | {row['Կատեգորիա']} | "
            f"{row['Հանդիպումներ']} | {row['Կարգավիճակ']}"
        )
    print("")
    print("Հիշեցում՝ աղբյուր ֆայլերը չեն փոփոխվել, ոչինչ չի ուղարկվել, ոչ մի գրառում միավորված չէ։")


# ---------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Փոստարկղից կոնտակտների/հասցեների հավաքում մեկ ֆայլով")
    p.add_argument("--input", required=True, help="Մուտք՝ .mbox/.eml/.zip/.csv/.txt կամ պանակ (միայն կարդալու)")
    p.add_argument("--out", default="reports/email-contacts.csv", help="Արդյունքային ՄԵԿ ֆայլը")
    p.add_argument("--against", help="Գործող բազայի contacts.csv՝ կրկնվողներին նշելու համար")
    p.add_argument("--headers", default=",".join(DEFAULT_HEADERS), help="Որ header-ներից հավաքել")
    p.add_argument("--from-body", action="store_true", help="Հասցեներ հավաքել նաև նամակի մարմնից (ստորագրություններ)")
    p.add_argument("--phones", action="store_true", help="Ստորագրություններից հեռախոսահամարներ հավաքել")
    p.add_argument("--min-count", type=int, default=1, help="Հեռացնել ավելի քիչ հանդիպումներ ունեցող հասցեները")
    p.add_argument("--me", action="append", default=[], help="Բաց թողնել սեփական հասցեները (կրկնելի)")
    p.add_argument("--default-category", default="Այլ", choices=CATEGORIES)
    p.add_argument("--no-split-names", action="store_true", help="Անուն/ազգանուն չեն բաժանվում")
    p.add_argument("--mask-file", action="store_true", help="Ֆայլում էլ. հասցեները դիմակավորել (կիսելու համար, ներմուծման համար՝ ոչ)")
    p.add_argument("--show-emails", action="store_true", help="Տերմինալում ցույց տալ ամբողջական հասցեները")
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
    skipped_me = set(email_key(a) for a in args.me)
    skipped_me_bases = {plus_base(a) for a in skipped_me}

    scan(input_path, collector, args)

    if skipped_me:
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
        print("Ոչ մի հասցե չգտնվեց։ Ստուգիր մուտքի ֆայլը կամ --headers արժեքը։", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    write_file(rows, out_path)
    console_summary(collector, rows, args, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
