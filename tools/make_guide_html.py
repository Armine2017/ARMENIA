#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ստեղծում է guide/Ուղեցույց.html — ինքնուրույն HTML ֆայլ՝ նկարները ներսում (base64)։
Կարելի է բացել ցանկացած զննարկիչով կամ տպել PDF-ով։"""
import base64
import html
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(BASE, "guide", "step-by-step-hy.md")
OUT = os.path.join(BASE, "guide", "Ուղեցույց.html")

CSS = """
:root { --prim:#1f4e79; --orange:#c55a11; --green:#548235; --bg:#f6f8fb; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:#1a1a1a;
       font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; line-height:1.65; }
.wrap { max-width: 980px; margin: 0 auto; padding: 40px 26px 90px; background:#fff;
        box-shadow: 0 0 40px rgba(31,78,121,.10); }
h1 { color:var(--prim); font-size: 2.1em; border-bottom:4px solid var(--prim); padding-bottom:12px; }
h2 { color:var(--prim); margin-top:52px; padding-top:10px; border-top:1px solid #e3ebf5; }
h3 { color:var(--orange); margin-top:34px; }
a { color:var(--prim); }
blockquote { margin:22px 0; padding:14px 20px; background:#eef4fb; border-right:6px solid var(--prim);
             border-radius:8px; }
blockquote p { margin:.35em 0; }
table { border-collapse:collapse; width:100%; margin:22px 0; font-size:.96em; }
th { background:var(--prim); color:#fff; text-align:left; }
th, td { border:1px solid #d7e2f0; padding:9px 12px; vertical-align:top; }
tr:nth-child(even) td { background:#f7fafd; }
code { background:#f2f5f9; padding:2px 6px; border-radius:4px; font-size:.94em;
       font-family: Consolas, "Courier New", monospace; }
pre { background:#1f2937; color:#e6edf3; padding:16px 18px; border-radius:10px; overflow-x:auto; line-height:1.5; }
pre code { background:none; color:inherit; padding:0; }
img { max-width:100%; height:auto; display:block; margin:28px auto; border-radius:12px;
      box-shadow:0 6px 22px rgba(31,78,121,.14); }
ul, ol { padding-left:26px; }
li { margin:6px 0; }
hr { border:none; border-top:1px solid #e3ebf5; margin:46px 0; }
.toc { background:#eef4fb; border-radius:12px; padding:16px 24px; margin:26px 0; }
.footer { margin-top:60px; font-size:.9em; color:#666; text-align:center; }
@media print {
  body { background:#fff; } .wrap { box-shadow:none; max-width:none; padding:0; }
  h2 { page-break-before: auto; } img { box-shadow:none; }
}
"""


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: m.group(0), s)  # images handled earlier
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def img_tag(base_dir, path, alt=""):
    full = os.path.join(base_dir, path)
    if not os.path.exists(full):
        return f'<p><em>(նկարը չի գտնվել՝ {html.escape(path)})</em></p>'
    data = base64.b64encode(open(full, "rb").read()).decode()
    return f'<img src="data:image/png;base64,{data}" alt="{html.escape(alt)}">'


def convert(md_text, base_dir):
    out, lines, i = [], md_text.split("\n"), 0
    para, table, in_code = [], [], False

    def flush_para():
        nonlocal para
        if para:
            block = "\n".join(para)
            # նկարները՝ առանձին
            parts = []
            for chunk in re.split(r"(!\[[^\]]*\]\([^)]+\))", block):
                m = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", chunk.strip())
                if m:
                    parts.append(img_tag(base_dir, m.group(2), m.group(1)))
                elif chunk.strip():
                    parts.append(f"<p>{inline(chunk.strip())}</p>")
            out.append("\n".join(parts))
            para = []

    def flush_table():
        nonlocal table
        if not table:
            return
        rows = [r for r in table if not re.fullmatch(r"\|[\s:|-]+\|", r.strip())]
        if rows:
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            head, body = cells[0], cells[1:]
            t = ["<table><thead><tr>"] + [f"<th>{inline(c)}</th>" for c in head] + ["</tr></thead><tbody>"]
            for row in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
        table = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para(); flush_table()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i]); i += 1
            out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
            i += 1
            continue

        if stripped.startswith("|"):
            flush_para()
            table.append(line)
            i += 1
            continue
        else:
            flush_table()

        if not stripped:
            flush_para()
        elif stripped.startswith("#"):
            flush_para()
            m = re.match(r"(#{1,6})\s*(.*)", stripped)
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
        elif stripped.startswith("<a name="):
            flush_para()
            out.append(stripped)
        elif stripped == "---":
            flush_para()
            out.append("<hr>")
        elif stripped.startswith(">"):
            flush_para()
            quote = [stripped.lstrip("> ").strip()]
            while i + 1 < len(lines) and lines[i + 1].strip().startswith(">"):
                i += 1
                quote.append(lines[i].strip().lstrip("> ").strip())
            out.append("<blockquote>" + "".join(f"<p>{inline(q)}</p>" for q in quote if q) + "</blockquote>")
        elif re.match(r"^[-*]\s+", stripped):
            flush_para()
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            i -= 1
            out.append("<ul>" + "".join(f"<li>{inline(it)}</li>" for it in items) + "</ul>")
        elif re.match(r"^\d+\.\s+", stripped):
            flush_para()
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            i -= 1
            out.append("<ol>" + "".join(f"<li>{inline(it)}</li>" for it in items) + "</ol>")
        else:
            para.append(stripped)
        i += 1

    flush_para(); flush_table()
    return "\n".join(out)


def build(md_path, out_path, title):
    md = open(md_path, encoding="utf-8").read()
    body = convert(md, os.path.dirname(md_path))
    doc = f"""<!DOCTYPE html>
<html lang="hy">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{body}
<p class="footer">Պատրաստվել է ARMENIA նախագծի համար • Տպելու համար՝ Ctrl+P (կամ «Save as PDF»)։</p>
</div>
</body>
</html>
"""
    open(out_path, "w", encoding="utf-8").write(doc)
    print("ok", os.path.relpath(out_path, BASE), f"({os.path.getsize(out_path) / 1024:.0f} KB)")


def main():
    build(MD, OUT, "Տենդերների ավտոմատացում — քայլ առ քայլ")
    # 1) մեծ ուղեցույցը  2) ամենապարզը («ՍԿՍԻՐ ԱՅՍՏԵՂԻՑ»)
    build(MD, OUT, "Տենդերների ավտոմատացում — քայլ առ քայլ")
    build(os.path.join(BASE, "guide", "ՍԿՍԻՐ-ԱՅՍՏԵՂԻՑ.md"),
          os.path.join(BASE, "guide", "ՍԿՍԻՐ-ԱՅՍՏԵՂԻՑ.html"),
          "ՍԿՍԻՐ ԱՅՍՏԵՂԻՑ — 12 պարզ քայլ")


if __name__ == "__main__":
    main()
