#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ստեղծում է guide/img/*.png սխեմաները հայերեն տեքստով։"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "guide", "img")
os.makedirs(OUT, exist_ok=True)

F = "/usr/share/fonts/truetype/dejavu/"
SANS = F + "DejaVuSans.ttf"
BOLD = F + "DejaVuSans-Bold.ttf"
K = 2  # supersampling (ավելի սուր տեքստ)

BG = "#f4f7fb"; CARD = "#ffffff"; PRIM = "#1f4e79"; PRIM_L = "#dce9f7"
BLUE = "#2e75b6"; ORANGE = "#c55a11"; ORANGE_L = "#fdeada"
GREEN = "#548235"; GREEN_L = "#e2efda"; PURPLE = "#7030a0"; PURPLE_L = "#eee1f5"
GRAY = "#595959"; LINE = "#8ea9c9"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else SANS, size * K)


def _wrap(draw, s, f, maxw):
    """Տողադարձ՝ բառերով, իսկ շատ երկար բառերը (օր. ֆայլի ուղիները)՝ մեջտեղից։"""
    lines = []
    for para in s.split("\n"):
        cur = ""
        for wd in para.split(" "):
            trial = (cur + " " + wd).strip()
            if maxw and draw.textlength(trial, font=f) > maxw * K and cur:
                lines.append(cur); cur = ""
            if maxw and draw.textlength(wd, font=f) > maxw * K:
                piece = ""
                for ch in wd:
                    if draw.textlength(piece + ch, font=f) > maxw * K and piece:
                        lines.append(piece); piece = ""
                    piece += ch
                cur = piece
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
    return lines


class Fig:
    def __init__(self, w, h, bg=BG):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w * K, h * K), bg)
        self.d = ImageDraw.Draw(self.img)

    def rect(self, x, y, w, h, fill=CARD, outline=None, radius=14, width=2):
        self.d.rounded_rectangle([x * K, y * K, (x + w) * K, (y + h) * K],
                                 radius=radius * K, fill=fill,
                                 outline=outline, width=width * K if outline else 0)

    def text(self, x, y, s, size=26, bold=False, fill="#1a1a1a", maxw=None, gap=8):
        """Բազմանվագ տեքստ. վերադարձնում է բարձրությունը։"""
        f = font(size, bold)
        lines = _wrap(self.d, s, f, maxw)
        lh = size * K * 1.32 + gap * K
        yy = y * K
        for ln in lines:
            self.d.text((x * K, yy), ln, font=f, fill=fill)
            yy += lh
        return (yy - y * K) / K

    def center(self, cx, y, s, size=26, bold=False, fill="#1a1a1a", maxw=None):
        f = font(size, bold)
        lines = _wrap(self.d, s, f, maxw)
        lh = size * K * 1.32
        for i, ln in enumerate(lines):
            xx = cx * K - self.d.textlength(ln, font=f) / 2
            self.d.text((xx, y * K + i * lh), ln, font=f, fill=fill)
        return len(lines) * lh / K

    def arrow(self, x1, y1, x2, y2, fill=BLUE, width=5, head=16):
        import math
        x1, y1, x2, y2 = x1 * K, y1 * K, x2 * K, y2 * K
        ang = math.atan2(y2 - y1, x2 - x1)
        hx, hy = x2 - head * K * math.cos(ang), y2 - head * K * math.sin(ang)
        self.d.line([x1, y1, hx, hy], fill=fill, width=width * K)
        bx, by = head * K * 0.95, head * K * 0.62
        p2 = (x2 - bx * math.cos(ang) + by * math.sin(ang), y2 - bx * math.sin(ang) - by * math.cos(ang))
        p3 = (x2 - bx * math.cos(ang) - by * math.sin(ang), y2 - bx * math.sin(ang) + by * math.cos(ang))
        self.d.polygon([(x2, y2), p2, p3], fill=fill)

    def badge(self, x, y, s, size=22, fill=ORANGE, tcolor="#ffffff", padx=26, pady=12):
        f = font(size, True)
        w = self.d.textlength(s, font=f) / K + padx * 2
        h = size * 1.35 + pady * 2
        self.rect(x, y, w, h, fill=fill, radius=h / 2)
        self.d.text((x * K + padx * K, y * K + pady * K), s, font=f, fill=tcolor)
        return w

    def circle_num(self, x, y, n, r=28, fill=PRIM, tcolor="#ffffff", size=30):
        self.d.ellipse([x * K, y * K, (x + 2 * r) * K, (y + 2 * r) * K], fill=fill)
        f = font(size, True)
        self.d.text(((x + r) * K - self.d.textlength(str(n), font=f) / 2,
                     (y + r) * K - size * K * 0.72), str(n), font=f, fill=tcolor)

    def save(self, name):
        path = os.path.join(OUT, name)
        self.img.resize((self.w, self.h), Image.LANCZOS).save(path, "PNG", optimize=True)
        print("ok", os.path.relpath(path, BASE))


def title(fig, text, sub=None, y=34, size=44):
    fig.center(fig.w / 2, y, text, size, True, PRIM)
    if sub:
        fig.center(fig.w / 2, y + 74, sub, 24, False, GRAY)


# ================================================================ 00 ընդհանուր սխեմա
f = Fig(1640, 920)
title(f, "ԻՆՉՊԵՍ Է ԱՇԽԱՏՈՒՄ «ՏԵՆԴԵՐԱՅԻՆ ՄՈՆԻՏՈՐ»-Ը", "ամեն օր՝ ավտոմատ կամ մեկ կտտոցով")

f.rect(45, 175, 415, 555, CARD, LINE, 18)
f.center(252, 200, "ԿԱՅՔԵՐ (ինտերնետ)", 30, True, PRIM)
sites = ["armeps.am — հանրային տենդերներ", "gnumner.minfin.am — հայտարարություններ",
         "procurement.minfin.am", "… և քո ցանկի մյուս կայքերը"]
yy = 262
for s in sites:
    f.rect(70, yy, 365, 88, PRIM_L, None, 12)
    f.text(90, yy + 20, s, 21, False, "#20303f", maxw=325)
    yy += 108

f.rect(520, 260, 500, 470, "#eef4fb", PRIM, 18, 3)
f.center(770, 282, "ՁԵՐ ՀԱՄԱԿԱՐԳԻՉԸ", 30, True, PRIM)
f.rect(550, 345, 440, 350, CARD, LINE, 14)
f.center(770, 360, "tender_bot.py", 28, True, GRAY)
f.text(578, 415, "1. բացում է կայքերը\n2. գտնում է միայն ՆՈՐ հայտարարությունները\n"
                 "3. հանում է հեռախոսն ու էլ. փոստը\n4. գրում է աղյուսակն ու ամփոփագիրը",
       20, False, "#20303f", maxw=390)

f.rect(1130, 175, 460, 555, CARD, GREEN, 18, 3)
f.center(1360, 200, "ԱՐԴՅՈՒՆՔԸ", 30, True, GREEN)
outs = [("Ֆայլերը՝ թղթապանակներով", "data\\2026-10-01\\Շինարարություն\\…"),
        ("Աղյուսակը (Excel)", "reports\\Հաշվետվություն-2026-10-01.csv — նպատակ, հեռախոս, էլ. փոստ"),
        ("Ամփոփագիրը", "քանի նոր հայտարարություն եկավ և որ կայքից")]
yy = 262
for head, body in outs:
    f.rect(1155, yy, 410, 150, GREEN_L, None, 12)
    f.text(1175, yy + 16, head, 22, True, "#243a12", maxw=370)
    f.text(1175, yy + 58, body, 20, False, "#3c5c22", maxw=370)
    yy += 165

f.arrow(475, 470, 515, 470)
f.arrow(1025, 470, 1125, 470)
f.badge(160, 830, "ԱՄԵՆ ՕՐ ԺԱՄԸ 08:00", 24)
f.center(f.w / 2, 890, "Ծրագիրն ինքն է արթնանում (Windows Task Scheduler) կամ դու կրկնակի սեղմում ես RUN.bat-ը",
         22, False, GRAY)
f.save("00-ընդհանուր-սխեմա.png")

# ================================================================ 01 հինգ քայլ
f = Fig(1640, 1000)
title(f, "5 ՔԱՅԼ՝ ՄԻՆՉԵՎ ԱՌԱՋԻՆ ԱՐԴՅՈՒՆՔ", "միայն առաջին անգամն է պետք անել")
steps = [
    ("Տեղադրիր Python-ը", "Բացիր python.org → Downloads → «Download Python 3.x»։\nՏեղադրման պատուհանում ՊԱՐՏԱԴԻՐ նշիր «Add python.exe to PATH» վանդակը։", PRIM),
    ("Պահիր ծրագրի ֆայլերը", "Ստեղծիր C:\\TenderBot թղթապանակը և մեջը դիր 5 ֆայլերը.\ntender_bot.py, config.json, requirements.txt, SETUP.bat, RUN.bat", BLUE),
    ("Կարգավորիր config.json-ը", "Բացիր Notepad-ով. ավելացրու քո կայքերը, կատեգորիաները\nու ամենօրյա աշխատանքի ժամը (run_time)։", ORANGE),
    ("Տեղադրիր և գործարկիր", "1) Կրկնակի սեղմիր SETUP.bat (միայն մեկ անգամ)\n2) Կրկնակի սեղմիր RUN.bat — ծրագիրը կաշխատի։", GREEN),
    ("Ստուգիր արդյունքը", "data\\ թղթապանակում՝ հայտարարությունները ըստ օրվա ու կատեգորիայի,\nreports\\-ում՝ CSV աղյուսակը (Excel-ով) և ամփոփագիրը։", PURPLE),
]
yy = 150
for i, (t, sub, col) in enumerate(steps, 1):
    f.rect(70, yy, 1500, 148, CARD, None, 16)
    f.rect(70, yy, 10, 148, col, None, 0)
    f.circle_num(112, yy + 44, i, 30, col)
    f.text(195, yy + 24, t, 30, True, col)
    f.text(195, yy + 72, sub, 21, False, "#333333")
    yy += 164
f.save("01-հինգ-քայլ.png")

# ================================================================ 02 թղթապանակների ծառ
f = Fig(1640, 900)
title(f, "ԻՆՉՊԵՍ ԿԽՄԲԱՎՈՐՎԵՆ ՖԱՅԼԵՐԸ", "ամեն հայտարարություն՝ առանձին ֆայլ՝ ըստ օրվա և կատեգորիայի")
f.rect(70, 175, 700, 660, CARD, LINE, 18)
f.text(100, 200, "data\\", 30, True, PRIM)
tree = [(0, "2026-10-01\\", True), (1, "Շինարարություն\\", True),
        (2, "ARMEPS_Դպրոցի-շենքի-վերանորոգում.txt", False),
        (1, "ՏՏ-և-ծրագրակազմ\\", True),
        (2, "ARMEPS_Համակարգչային-սարքավորումներ.txt", False),
        (1, "Բժշկական\\", True),
        (2, "MinFin_Բժշկական-սարքավորումներ.txt", False),
        (0, "2026-10-02\\", True), (1, "…", True)]
yy = 265
for depth, name, isdir in tree:
    f.text(110 + depth * 50, yy, ("[ + ] " if isdir else "      ") + name, 23, isdir, "#1a1a1a")
    yy += 58
f.rect(840, 175, 730, 660, CARD, GREEN, 18, 3)
f.text(870, 200, "reports\\", 30, True, GREEN)
rep = [("Հաշվետվություն-2026-10-01.csv", "Excel-ով բացվող աղյուսակ այս օրվա բոլոր նոր հայտարարություններով"),
       ("MASTER.csv", "Բոլոր օրերի միացյալ աղյուսակը՝ գլխավոր ֆայլը"),
       ("Ամփոփագիր-2026-10-01.txt", "«Այսօր 4 նոր հայտարարություն՝ 2-ը շինարարություն» և այլն"),
       ("logs\\", "Սխալների և աշխատանքի պատմությունը (եթե կայքը չի բացվել)")]
yy = 280
for n, s in rep:
    f.rect(870, yy, 670, 120, GREEN_L, None, 12)
    f.text(892, yy + 16, n, 23, True, "#243a12", maxw=630)
    f.text(892, yy + 56, s, 19, False, "#3c5c22", maxw=630)
    yy += 136
f.save("02-թղթապանակներ.png")

# ================================================================ 03 աղյուսակ
f = Fig(1640, 800)
title(f, "ԱՂՅՈՒՍԱԿԸ (CSV/EXCEL) ԻՆՉ ՏԵՍՔ ՈՒՆԻ", "բացվում է Excel-ով, հայերեն տառերը՝ ճիշտ")
cols = ["Ամսաթիվ", "Աղբյուր", "Կատեգորիա", "Գնման նպատակը / Վերնագիրը", "Հեռախոս", "Էլ. փոստ"]
xs = [82, 255, 400, 660, 1105, 1285]
ws = [168, 140, 255, 440, 175, 200]
rows = [
    ["01.10.2026", "ARMEPS", "Շինարարություն", "Դպրոցի շենքի վերանորոգում", "+374 10 123456", "info@yerevan.am"],
    ["01.10.2026", "ARMEPS", "ՏՏ և ծրագրակազմ", "Համակարգիչների ձեռքբերում", "+374 10 123456", "info@yerevan.am"],
    ["01.10.2026", "MinFin", "Բժշկական", "Բժշկական սարքավորումների հրավեր", "010 555444", "tenders@med.am"],
    ["02.10.2026", "ARMEPS", "Տրանսպորտ", "Ճանապարհի հիմնանորոգում", "+374 11 987654", "road@arm.am"],
]
f.rect(70, 175, 1420, 70, PRIM, None, 0)
for i, c in enumerate(cols):
    f.text(xs[i] + 12, 192, c, 22, True, "#ffffff", maxw=ws[i] - 24)
yy = 245
for r_i, r in enumerate(rows):
    bg = "#ffffff" if r_i % 2 == 0 else "#f3f7fc"
    f.rect(70, yy, 1420, 70, bg, "#d7e2f0", 8, 2)
    for i, c in enumerate(r):
        col = ORANGE if i in (4, 5) else ("#1a1a1a" if i != 2 else PRIM)
        f.text(xs[i] + 12, yy + 20, c, 21, i in (4, 5), col, maxw=ws[i] - 24)
    yy += 80
f.badge(70, 610, "ՆԱՐԱՆՋԱԳՈՒՅՆԸ", 22, ORANGE)
f.text(70, 690, "— հեռախոսների և էլ. փոստերի սյունակներն են. դա է գլխավոր նպատակը", 23, False, GRAY)
f.text(70, 730, "Լրացուցիչ սյունակներ՝ Ծածկագիր • Վերջնաժամկետ • Կազմակերպություն • Հղում • Պահպանված ֆայլ",
       21, False, GRAY)
f.save("03-աղյուսակ.png")

# ================================================================ 04 Task Scheduler
f = Fig(1640, 1170)
title(f, "ԱՄԵՆՕՐՅԱ ԱՎՏՈՄԱՏ ԳՈՐԾԱՐԿՈՒՄ (Windows)", "մեկ անգամ կարգավորիր՝ ծրագիրն ամեն օր ինքը կաշխատի")
steps = [
    ("1", "Բացիր Task Scheduler-ը", "Ստեղնաշարից սեղմիր Win+R, գրիր taskschd.msc և Enter։", PRIM),
    ("2", "Աջ կողմում՝ Create Basic Task…", "Անվանում դաշտում գրիր՝ TenderBot ։ Սեղմիր Next։", BLUE),
    ("3", "Trigger՝ Daily", "Օրը՝ ամեն օր (Daily), ժամը՝ 08:00։ Սեղմիր Next։", BLUE),
    ("4", "Action՝ Start a program", "Program/script՝ python\nAdd arguments՝ tender_bot.py\nStart in՝ C:\\TenderBot", BLUE),
    ("5", "Finish", "Պատրաստ է. ամեն օր 08:00-ին ծրագիրն ինքը կաշխատի։", GREEN),
    ("6", "Կարևոր է", "Այդ պահին համակարգիչը միացած պետք է լինի։\nԱյլընտրանք՝ թող RUN.bat-ը բաց մնա ամբողջ օրը։", ORANGE),
]
yy = 150
for n, t, s, col in steps:
    f.rect(70, yy, 1500, 148, ORANGE_L if col == ORANGE else CARD, None, 16)
    f.circle_num(112, yy + 44, n, 29, col)
    f.text(195, yy + 22, t, 28, True, col)
    f.text(195, yy + 68, s, 19 if s.count(chr(10)) > 1 else 21, False, "#333333")
    yy += 164
f.save("04-ավտոմատ-գործարկում.png")

# ================================================================ 05 AI-ի հետ աշխատելը
f = Fig(1600, 900)
title(f, "ԻՆՉՊԵՍ ԱՇԽԱՏԵԼ AI ՕԳՆԱԿԱՆԻ ՀԵՏ (պատրաստի PROMPT-ով)", size=36)
f.rect(100, 170, 1400, 600, CARD, LINE, 18)
f.rect(100, 170, 1400, 76, PRIM, None, 18)
f.text(140, 190, "AI օգնական (Arena.ai • ChatGPT • Claude • Gemini)", 28, True, "#ffffff")

f.rect(150, 290, 780, 130, "#eef4fb", None, 14)
f.text(178, 310, "Ես ծրագրավորող չեմ. ուզում եմ ամեն օր տենդերային կայքերից", 21, False, "#1a1a1a")
f.text(178, 342, "բեռնել միայն նոր հայտարարությունները, դասավորել", 21, False, "#1a1a1a")
f.text(178, 374, "թղթապանակներում և ստանալ հեռախոսներն ու էլ. փոստերը։", 21, False, "#1a1a1a")

f.text(150, 450, "1. Պատճենիր prompts\\PROMPT-hy.md ֆայլի ամբողջ տեքստը", 23, True, ORANGE)
f.text(150, 486, "    (կամ պարզապես գրիր. «Ահա իմ պահանջը, արա ինձ ծրագիր»)", 20, False, GRAY)
f.badge(150, 525, "2. ՏԵՂԱԴՐԻՐ ՏԵՔՍՏԸ ԶՐՈՒՅՑՈՒՄ ԵՎ ENTER", 22, ORANGE)

f.badge(930, 300, "AI-ն գրում է կոդը", 22, PRIM)
f.badge(930, 360, "ԴՈՒ սեղմում ես կոճակները", 22, GREEN)

f.rect(150, 600, 1300, 150, GREEN_L, None, 14)
f.text(178, 618, "AI-ն՝ «Ահա պլանը. 1) ARMEPS-ից՝ HTML վերլուծություն… 2) ամեն հայտարարության էջից", 20, False, "#3c5c22")
f.text(178, 650, "կհանեմ հեռախոսն ու էլ. փոստը… 3) կդասավորեմ ըստ կատեգորիաների… 4) կստեղծեմ աղյուսակ", 20, False, "#3c5c22")
f.text(178, 682, "ու ամփոփագիր…», և քեզ կտա պատրաստի ֆայլերը + քայլ առ քայլ հայերեն հրահանգներ։", 20, True, "#243a12")
f.center(f.w / 2, 815, "Դու կոդ չես գրում. դու պատվիրում ես, AI-ն գրում է, իսկ ծրագիրը աշխատում է քո համակարգչում։",
         22, True, PRIM)
f.save("05-AI-յով-աշխատելը.png")

# ================================================================ 06 ապահով սկիզբ
f = Fig(1640, 900)
title(f, "ԱՊԱՀՈՎ ՍԿԻԶԲ՝ ՆԱԽ ՓՈՐՁԱՐԿԻՐ, ՀԵՏՈ՝ ԻՐԱԿԱՆ ԿԱՅՔԵՐ", "եթե դեռ չես վստահում ծրագրին")
f.rect(70, 175, 900, 640, CARD, LINE, 18)
f.text(100, 200, "Փորձարկում լոկալ ֆայլերով (առանց ինտերնետի)", 26, True, PRIM, maxw=840)
steps = [
    ("Պահիր 2–3 կայքի էջ որպես .html ֆայլ", "Բացիր կայքը Edge/Chrome-ով → Ctrl+S → «Webpage, HTML only»"),
    ("Դիր ֆայլերը samples\\ թղթապանակում", "samples\\armeps.html, samples\\minfin.html"),
    ("Ավելացրու config.json-ում", "«sources» ցանկում գրիր. \"url\": \"samples/armeps.html\", \"kind\": \"file\""),
    ("Գործարկիր փորձնական ռեժիմը", "Ծրագրի թղթապանակում բացիր հրամանի տողը և գրիր.\npy tender_bot.py --demo"),
]
yy = 265
for i, (t, s) in enumerate(steps, 1):
    f.circle_num(105, yy + 12, i, 26, BLUE)
    f.text(180, yy + 4, t, 24, True, "#1a1a1a", maxw=760)
    f.text(180, yy + 44, s, 20, False, GRAY, maxw=760)
    yy += 130
f.rect(1000, 175, 570, 320, GREEN_L, GREEN, 18, 3)
f.text(1030, 200, "Ստուգիր՝ կրկնություն չկա՞", 26, True, GREEN, maxw=520)
f.text(1030, 250, "1-ին գործարկում   →   4 նոր հայտարարություն\n"
                   "2-րդ գործարկում   →   0 նոր (նույնը չի կրկնվի)\n"
                   "3-րդ օրը՝ նոր հայտարարություն → նորից կբեռնի", 22, False, "#243a12", maxw=520)
f.rect(1000, 515, 570, 300, ORANGE_L, None, 18)
f.text(1030, 540, "Եթե ինչ-որ բան չաշխատի", 26, True, ORANGE, maxw=520)
f.text(1030, 590, "• Չի բացվում կայքը → logs\\ թղթապանակում տեքստ կա, ծրագիրը կշարունակի\n"
                   "• Հայերենը տարօրինակ է → CSV-ն բացիր Excel-ով, UTF-8-ը արդեն կարգին է\n"
                   "• Սխալի տեքստը պատճենիր AI-ին → նա կուղղի ծրագիրը", 21, False, "#703b0d", maxw=520)
f.save("06-ապահով-սկիզբ.png")
print("Պատրաստ է։")
