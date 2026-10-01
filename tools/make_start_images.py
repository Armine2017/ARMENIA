#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ստեղծում է ամենապարզ ուղեցույցի նկարները՝ guide/img/start/*.png
Դրանք Windows-ի պատուհանների հայերեն «նկարազարդումներ» են, որպեսզի տեսնես,
թե ինչ է լինելու էկրանիդ։"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import (Fig, WIN_BAR, WIN_BG, PRIM, PRIM_L, ORANGE, ORANGE_L, GREEN, GREEN_L,
                    RED, RED_L, GRAY, LINE, CARD, taskbar)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "guide", "img", "start")

DESKTOP_BG = "#2f5f8f"


DESK_BG = "#2f5f8f"


def desktop(fig, icons=True):
    fig.rect(0, 0, fig.w, fig.h - 62, DESKTOP_BG, None, 0)
    if icons:
        for i, label in enumerate(["Զամբյուղ", "Փաստաթղթեր", "Նկարներ"]):
            x, y = 96, 44 + i * 132
            if label == "Զամբյուղ":
                fig.rect(x, y, 34, 40, "#d9d9d9", "#ffffff", 5, 2)
                fig.rect(x - 5, y + 4, 44, 8, "#d9d9d9", "#ffffff", 3, 2)
            elif label == "Փաստաթղթեր":
                fig.folder_icon(x - 4, y, 40, "#f2b134", "#c98a12")
            else:
                fig.rect(x, y, 40, 34, "#ffffff", "#ffffff", 4, 2)
                fig.d.ellipse([(x + 8) * 2, (y + 8) * 2, (x + 18) * 2, (y + 18) * 2], fill="#2e75b6")
                fig.d.polygon([(x + 4, y + 30), (x + 18, y + 16), (x + 30, y + 30)], fill="#548235")
            fig.center(x + 18, y + 54, label, 18, False, "#ffffff")
    taskbar(fig)


# ---------------------------------------------------------------- 1. պանակ ստեղծել
f = Fig(1600, 1000)
f.step_title(1, "Աշխատանքային սեղանին ստեղծիր նոր պանակ", "սա լինելու է ծրագրի «տունը»")
desktop(f)

# աջ սեղմման ընտրացանկ
mx, my, mw = 620, 170, 380
f.rect(mx, my, mw, 470, "#f7f7f7", "#b9b9b9", 8)
items = ["Դիտել", "Տեսակավորել ըստ", "Թարմացնել", None, "Նոր", "Այլ…"]
yy = my + 14
for it in items:
    if it is None:
        f.line(mx + 12, yy + 12, mx + mw - 12, yy + 12, "#d4d4d4", 2)
        yy += 26
        continue
    if it == "Նոր":
        f.rect(mx + 6, yy - 4, mw - 12, 50, PRIM_L, None, 6)
    f.text(mx + 28, yy + 4, it, 24, it == "Նոր", "#1a1a1a")
    if it == "Նոր":
        f.text(mx + mw - 40, yy + 4, "▶", 20, False, "#1a1a1a")
    yy += 62

f.pointer(mx - 40, my + 30)
f.rect(70, 630, 600, 215, CARD, RED, 16, 3)
f.text(96, 652, "1. Սեղմիր ԱՋ կոճակը", 24, True, RED, maxw=550)
f.text(96, 692, "2. Ընտրիր «Նոր» → «Պանակ»", 24, True, RED, maxw=550)
f.text(96, 748, "3. (անգլերեն՝ New → Folder)", 21, False, GRAY, maxw=550)
f.arrow(672, 640, mx - 55, my + 150, RED, 6)
f.caption_bar("Պանակը կհայտնվի էկրանիդ։ Անունը դեռ «Նոր պանակ» կլինի — անցնում ենք Քայլ 2։", y=822)
f.save("s01-պանակ-ստեղծել.png", OUT)

# ---------------------------------------------------------------- 2. անվանել
f = Fig(1600, 1000)
f.step_title(2, "Անվանիր պանակը՝ ՏԵՆԴԵՐ", "գրիր անունը և սեղմիր Enter")
desktop(f, icons=False)
f.rect(120, 150, 520, 470, "#3a6ea5", "#ffffff", 12, 2)
f.folder_icon(170, 175, 120, "#f2b134", "#c98a12")
name_x, name_y = 120, 300
f.rect(name_x, name_y, 520, 60, "#ffffff", PRIM, 6, 3)
f.text(name_x + 20, name_y + 12, "ՏԵՆԴԵՐ", 30, True, "#1a1a1a")
f.highlight(name_x - 6, name_y - 6, 532, 72, RED, 5)
f.text(140, 380, "Անունը գրիր մեծատառերով կամ\nփոքրատառերով՝ ինչպես ուզում ես։", 24, False, "#ffffff", maxw=480)
f.text(140, 470, "Մի՛ մոռացիր սեղմել Enter։", 26, True, "#ffe08a")

f.arrow(760, 330, 1200, 330, RED, 6)
f.rect(830, 430, 690, 260, CARD, GREEN, 14, 3)
f.text(860, 452, "Ինչպե՞ս գրել հայերեն տառեր", 27, True, GREEN, maxw=640)
f.text(860, 500, "Ստեղնաշարի ներքևի աջ անկյունում կա լեզվի ցուցիչ (հայերեն/РУС/ENG)։\n"
                 "Սեղմիր դրա վրա կամ Alt+Shift և ընտրիր Հայերեն։", 22, False, "#243a12", maxw=640)
f.text(860, 590, "Եթե հայերեն չկա՝ անունը դիր «TENDER»։ Միևնույնն է։", 22, True, ORANGE, maxw=640)
f.caption_bar("Հիմա աշխատանքային սեղանիդ վրա ունես «ՏԵՆԴԵՐ» պանակը։ Անցնում ենք ծրագիրը ներբեռնելուն։", y=822)
f.save("s02-անվանիր-պանակը.png", OUT)

# ---------------------------------------------------------------- 3. ներբեռնել ծրագիրը
f = Fig(1600, 1000)
f.step_title(3, "Ներբեռնիր ծրագիրը (մեկ ֆայլ)", "քո պահոցից՝ ARMENIA → TenderBot.zip")
body = f.window(140, 120, 1320, 700, "Microsoft Edge  —  github.com/Armine2017/ARMENIA", WIN_BAR, "#ffffff")
bx, by = body[0], body[1]
f.rect(bx + 30, by + 18, 1260, 54, "#f2f2f2", "#cfcfcf", 26)
f.lock_icon(bx + 52, by + 32, 22)
f.text(bx + 86, by + 30, "github.com/Armine2017/ARMENIA", 22, False, "#333333", maxw=1160)
f.text(bx + 40, by + 100, "Armine2017 / ARMENIA", 32, True, "#1a1a1a")
f.text(bx + 40, by + 148, "Տենդերների ամենօրյա ավտոմատ հավաքում", 22, False, GRAY)

f.button(bx + 40, by + 200, 230, 62, "Code  ▾", "#2ea44f", "#ffffff", 24)
f.highlight(bx + 34, by + 194, 242, 74, RED, 5)
f.rect(bx + 40, by + 274, 420, 150, "#ffffff", "#cfcfcf", 10)
f.text(bx + 66, by + 292, "Download ZIP", 26, True, "#1a1a1a")
f.text(bx + 66, by + 336, "ամբողջ պահոցը՝ մեկ արխիվով", 20, False, GRAY)
f.text(bx + 66, by + 372, "Կտպվի առաջին տողի վրա։", 20, False, GRAY)

f.rect(bx + 560, by + 100, 660, 420, "#f6f8fa", "#dfe3e8", 12)
f.page_icon(bx + 588, by + 126, 26)
f.text(bx + 628, by + 128, "README.md", 22, False, "#333333")
f.folder_icon(bx + 588, by + 172, 26)
f.text(bx + 628, by + 174, "bot/          ← ծրագիրը", 22, True, PRIM)
f.folder_icon(bx + 588, by + 217, 26)
f.text(bx + 628, by + 219, "guide/       ← ուղեցույցները", 22, False, "#333333")
f.folder_icon(bx + 588, by + 262, 26)
f.text(bx + 628, by + 264, "prompts/   ← AI-ի պատվերը", 22, False, "#333333")
f.zip_icon(bx + 588, by + 310, 26)
f.text(bx + 628, by + 312, "TenderBot.zip  ← մեզ պետք է սա", 22, True, ORANGE)
f.text(bx + 590, by + 370, "Ֆայլը ներբեռնելուց հետո կգտնես\n«Ներբեռնումներ / Downloads» պանակում։", 20, False, GRAY, maxw=600)

f.arrow(bx + 260, by + 240, bx + 470, by + 300, RED, 6)
f.caption_bar("Եթե GitHub-ը քեզ անծանոթ է. բացիր զննարկիչը, հասցեների տողում գրիր github.com/Armine2017/ARMENIA", y=850, size=23)
f.save("s03-ներբեռնիր.png", OUT)

# ---------------------------------------------------------------- 4. բացել ZIP-ը
f = Fig(1600, 1010)
f.step_title(4, "Բացիր ներբեռնված ZIP-ը", "«Ներբեռնումներ / Downloads» պանակում")
body = f.window(140, 120, 1320, 720, "Ներբեռնումներ (Downloads)", "#3c3c3c", "#ffffff")
bx, by = body[0], body[1]
f.rect(bx + 20, by + 16, 1270, 56, "#f3f3f3", "#dcdcdc", 6)
f.folder_icon(bx + 42, by + 28, 24)
f.text(bx + 80, by + 30, "Այս համակարգիչը › Ներբեռնումներ", 21, False, "#444444", maxw=960)
for i, (name, size, highlight) in enumerate([("TenderBot.zip", "24 KB", True),
                                             ("ուղեցույց.html", "2.5 MB", False),
                                             ("նկար.jpg", "1.2 MB", False)]):
    y = by + 100 + i * 84
    bg = PRIM_L if highlight else "#ffffff"
    f.rect(bx + 20, y, 1270, 74, bg, "#ececec", 6, 2)
    if highlight:
        f.zip_icon(bx + 46, y + 20, 30)
    else:
        f.page_icon(bx + 46, y + 18, 30)
    f.text(bx + 96, y + 24, name, 23, highlight, "#1a1a1a", maxw=700)
    f.text(bx + 1080, y + 24, size, 21, False, GRAY)
    if highlight:
        f.highlight(bx + 14, y - 6, 1282, 86, RED, 5)

f.rect(bx + 20, by + 380, 1270, 300, ORANGE_L, None, 12)
f.text(bx + 50, by + 402, "Ի՞նչ անել հիմա", 26, True, ORANGE, maxw=1200)
f.text(bx + 50, by + 452, "1. Սեղմիր ԱՋ կոճակը TenderBot.zip ֆայլի վրա", 23, False, "#3a2000", maxw=1200)
f.text(bx + 50, by + 496, "2. Ընտրիր «Extract All…» (հայերեն՝ «Հանել բոլորը…»)", 23, True, "#3a2000", maxw=1200)
f.text(bx + 50, by + 540, "3. Կհայտնվի նոր պանակ՝ TenderBot։ Բացիր այն։", 23, False, "#3a2000", maxw=1200)
f.text(bx + 50, by + 588, "Եթե «Հանել» բառը չես գտնում. պարզապես կրկնակի սեղմիր ZIP-ի վրա և ներսից ֆայլերը դուրս քաշիր։",
       21, False, GRAY, maxw=1200)
f.caption("Պանակի մեջ կտեսնես ֆայլեր՝ tender_bot.py, RUN.bat, SETUP.bat և այլն։", y=f.h - 100, size=25)
f.save("s04-բացիր-zip.png", OUT)

# ---------------------------------------------------------------- 5. տեղափոխել
f = Fig(1600, 1010)
f.step_title(5, "Ֆայլերը տեղափոխիր ՏԵՆԴԵՐ պանակը", "պատճենիր-տեղադրիր կամ քաշիր մկնիկով")
body = f.window(70, 120, 700, 700, "TenderBot (հանված ZIP-ից)", "#3c3c3c", "#ffffff")
bx, by = body[0], body[1]
files = ["tender_bot.py", "config.json", "requirements.txt", "SETUP.bat", "RUN.bat",
         "README-hy.md", "samples", "inbox"]
for i, name in enumerate(files):
    y = by + 30 + i * 62
    if name in ("samples", "inbox"):
        f.folder_icon(bx + 40, y - 2, 26)
    else:
        f.page_icon(bx + 40, y - 4, 26)
    f.text(bx + 82, y, name, 23, False, "#1a1a1a")
f.rect(bx + 30, by + 540, 640, 130, PRIM_L, None, 10)
f.text(bx + 50, by + 558, "1. Սեղմիր Ctrl+A (ընտրել բոլորը)\n2. Ctrl+C (պատճենել)", 22, False, "#12395c", maxw=600)

body2 = f.window(830, 250, 700, 570, "Աշխատանքային սեղան › ՏԵՆԴԵՐ", "#3c3c3c", "#ffffff")
bx2, by2 = body2[0], body2[1]
f.rect(bx2 + 20, by2 + 20, 660, 520, "#ffffff", "#e0e0e0", 8, 2)
f.text(bx2 + 50, by2 + 60, "3. Սեղմիր Ctrl+V (տեղադրել)", 23, True, GREEN, maxw=600)
for i, name in enumerate(files):
    y = by2 + 120 + i * 46
    if y > by2 + 480:
        break
    if name in ("samples", "inbox"):
        f.folder_icon(bx2 + 50, y - 2, 24)
    else:
        f.page_icon(bx2 + 50, y - 4, 24)
    f.text(bx2 + 90, y, name, 21, False, "#1a1a1a")

f.arrow(790, 380, 820, 380, RED, 6)
f.arrow(790, 430, 820, 430, RED, 6)
f.caption("Ամենակարևորը. վերջում ՏԵՆԴԵՐ պանակում պետք է լինեն tender_bot.py, RUN.bat և SETUP.bat ֆայլերը։", size=23)
f.save("s05-տեղափոխիր-ֆայլերը.png", OUT)

# ---------------------------------------------------------------- 6. Python ներբեռնում
f = Fig(1600, 1000)
f.step_title(6, "Տեղադրիր Python-ը (միայն մեկ անգամ)", "առանց դրա ծրագիրը չի աշխատի")
body = f.window(140, 120, 1320, 700, "Microsoft Edge  —  python.org/downloads", WIN_BAR, "#ffffff")
bx, by = body[0], body[1]
f.rect(bx + 30, by + 18, 1260, 54, "#f2f2f2", "#cfcfcf", 26)
f.lock_icon(bx + 52, by + 32, 22)
f.text(bx + 86, by + 30, "www.python.org/downloads", 22, False, "#333333")
f.text(bx + 60, by + 110, "Download the latest version of Python", 30, True, "#1a1a1a")
f.text(bx + 60, by + 160, "Կայքը ինքը կորոշի քո Windows-ի տարբերակը։", 21, False, GRAY)
f.button(bx + 60, by + 215, 520, 84, "Download Python 3.13", "#ffd343", "#1a1a1a", 26)
f.highlight(bx + 54, by + 209, 532, 96, RED, 5)
f.arrow(bx + 700, by + 150, bx + 640, by + 250, RED, 6)
f.rect(bx + 620, by + 90, 640, 300, ORANGE_L, None, 12)
f.text(bx + 650, by + 115, "The yellow button is your friend", 22, True, ORANGE, maxw=580)
f.text(bx + 650, by + 160, "Դեղին կոճակը սեղմելուց հետո կներբեռնվի մեկ ֆայլ՝\n"
                          "python-3.13.x-amd64.exe", 22, False, "#3a2000", maxw=580)
f.text(bx + 650, by + 240, "Այդ ֆայլը բացում ես կրկնակի սեղմելով և անցնում\nհաջորդ քայլին։",
       22, True, "#3a2000", maxw=580)
f.text(bx + 60, by + 380, "ԱՄԵՆԱԿԱՐԵՎՈՐԸ ՀԻՄԱ. տեղադրման առաջին էկրանին նայիր ներքևի ձախ անկյունը (Քայլ 7)։",
       24, True, RED, maxw=1200)
f.text(bx + 60, by + 440, "Այնտեղ կա մի փոքրիկ վանդակ՝ «Add python.exe to PATH»։ Առանց դրա ծրագիրը չի գտնի Python-ը։",
       22, False, GRAY, maxw=1200)
f.caption_bar("Եթե կայքը անգլերեն է՝ մի՛ վախեցիր. քեզ պետք է միայն այդ դեղին կոճակը։", y=850, size=24)
f.save("s06-python-ներբեռնում.png", OUT)

# ---------------------------------------------------------------- 7. PATH վանդակ
f = Fig(1600, 1010)
f.step_title(7, "ՊԱՐՏԱԴԻՐ. նշիր «Add python.exe to PATH» վանդակը", "սա ամենից հաճախ մոռացվող քայլն է")
body = f.window(180, 130, 1240, 720, "Python 3.13.0 (64-bit) Setup", "#4a4a4a", "#ffffff")
bx, by = body[0], body[1]

f.text(bx + 60, by + 40, "Install Python 3.13.0 (64-bit)", 30, True, "#1a1a1a")
f.text(bx + 60, by + 90, "Select Install Now to install Python with default settings, or choose\nCustomize to enable or disable features.",
       21, False, "#333333")
f.button(bx + 60, by + 160, 300, 70, "Install Now", "#e1e1e1", "#1a1a1a", 22)
f.text(bx + 80, by + 245, "C:\\Users\\...\\AppData\\Local\\Programs\\Python\\Python313", 17, False, GRAY, maxw=560)
f.button(bx + 60, by + 300, 300, 70, "Customize installation", "#e1e1e1", "#1a1a1a", 22)

# PATH վանդակը
f.checkbox(bx + 60, by + 520, checked=True, size=30)
f.text(bx + 120, by + 516, "Add python.exe to PATH", 27, True, "#1a1a1a")
f.text(bx + 120, by + 560, "(Ավելացնել Python-ը PATH-ին)", 21, False, GRAY)
f.highlight(bx + 40, by + 500, 640, 100, RED, 6)
f.arrow(bx + 330, by + 440, bx + 180, by + 520, RED, 7)

f.rect(bx + 760, by + 460, 460, 210, RED_L, RED, 14, 3)
f.text(bx + 790, by + 482, "ՊԱՐՏԱԴԻՐ է", 28, True, RED, maxw=400)
f.text(bx + 790, by + 532, "Այս վանդակը նշելուց հետո միայն\nսեղմիր Install Now։", 22, False, "#5a0000", maxw=400)
f.text(bx + 790, by + 616, "Տեղադրումը տևում է 1–3 րոպե։", 21, True, RED, maxw=400)
f.caption("Վերջում կտեսնես «Setup was successful»։ Սեղմիր Close։", size=25)
f.save("s07-path-վանդակ.png", OUT)

# ---------------------------------------------------------------- 8. SETUP.bat
f = Fig(1600, 1010)
f.step_title(8, "Կրկնակի սեղմիր SETUP.bat-ը", "միայն մեկ անգամ՝ գրադարանների տեղադրման համար")
body = f.window(90, 120, 1420, 700, "ՏԵՆԴԵՐ  (Աշխատանքային սեղան)", "#3c3c3c", "#ffffff")
bx, by = body[0], body[1]
files = [("tender_bot.py", "Ծրագիրը"), ("config.json", "Կարգավորումները"),
         ("requirements.txt", "Գրադարանների ցանկը"), ("SETUP.bat", "1) ՏԵԼԱԴՐՈՒՄ (այս մեկը)"),
         ("RUN.bat", "2) ԳՈՐԾԱՐԿՈՒՄ (հաջորդ քայլին)"),
         ("samples", "Օրինակներ"), ("inbox", "Ձեռքով բացված էջերի պանակ")]
for i, (name, desc) in enumerate(files):
    y = by + 24 + i * 84
    hl = name == "SETUP.bat"
    bg = ORANGE_L if hl else "#ffffff"
    f.rect(bx + 20, y, 1380, 72, bg, "#ececec", 6, 2)
    if "." in name:
        f.page_icon(bx + 46, y + 18, 28)
    else:
        f.folder_icon(bx + 46, y + 20, 28)
    f.text(bx + 96, y + 22, name, 24, hl, "#1a1a1a", maxw=520)
    f.text(bx + 640, y + 24, desc, 21, hl, GRAY if not hl else ORANGE, maxw=720)
    if hl:
        f.highlight(bx + 14, y - 8, 1392, 88, RED, 5)

f.rect(bx + 20, by + 620, 1380, 60, GREEN_L, None, 8)
f.text(bx + 46, by + 634, "Կրկնակի սեղմում = բացվում է սև պատուհան, որն ինքը կտեղադրի անհրաժեշտ գրադարանները։", 22, True, GREEN, maxw=1320)
f.caption("Երբ էկրանին գրվի «Press any key to continue», սեղմիր ստեղնաշարից որևէ կոճակ։", size=24)
f.save("s08-setup-կրկնակի-սեղմիր.png", OUT)

# ---------------------------------------------------------------- 9. RUN.bat
f = Fig(1600, 1010)
f.step_title(9, "Ամեն օր կրկնակի սեղմիր RUN.bat-ը", "և ծրագիրն ինքը ամեն ինչ կանի")
body = f.window(90, 120, 1420, 540, "ՏԵՆԴԵՐ  (Աշխատանքային սեղան)", "#3c3c3c", "#ffffff")
bx, by = body[0], body[1]
for i, (name, desc) in enumerate([("tender_bot.py", "Ծրագիրը"), ("config.json", "Կարգավորումները"),
                                  ("requirements.txt", "Գրադարանների ցանկը"), ("SETUP.bat", "Տեղադրումը (արված է)"),
                                  ("RUN.bat", "ԱՅՍ ՄԵԿԸ՝ ամեն օր")]):
    y = by + 24 + i * 88
    hl = name == "RUN.bat"
    f.rect(bx + 20, y, 1380, 74, GREEN_L if hl else "#ffffff", "#ececec", 6, 2)
    f.text(bx + 46, y + 22, "📄", 24, False, "#333333")
    f.text(bx + 96, y + 22, name, 24, hl, "#1a1a1a", maxw=520)
    f.text(bx + 640, y + 24, desc, 21, hl, GRAY if not hl else GREEN, maxw=720)
    if hl:
        f.highlight(bx + 14, y - 8, 1392, 90, RED, 6)

f.arrow(760, 700, 760, 780, RED, 7)
f.rect(180, 790, 1240, 190, CARD, PRIM, 14, 3)
f.text(210, 812, "Ի՞նչ կլինի հետո", 27, True, PRIM, maxw=1160)
f.text(210, 862, "Կբացվի սև պատուհան, կաշխատի մոտ մեկ րոպե, կցուցադրի ամփոփագիրը և կասի՝\n"
                 "«Պատրաստ է։ Արդյունքները՝ reports\\ և data\\ թղթապանակներում»։", 23, False, "#20303f", maxw=1160)
f.text(210, 928, "Պատուհանը փակելու համար սեղմիր ստեղնաշարից որևէ կոճակ։", 22, True, ORANGE, maxw=1160)
f.save("s09-run-կրկնակի-սեղմիր.png", OUT)

# ---------------------------------------------------------------- 10. աշխատում է
f = Fig(1600, 1000)
f.step_title(10, "Ահա թե ինչ կտեսնես պատուհանում", "եթե այս տողերը կան՝ ամեն ինչ ճիշտ է")
f.rect(120, 130, 1360, 720, "#0c0c0c", "#3a3a3a", 10, 3)
f.text(150, 150, "C:\\Users\\Armine\\Desktop\\ՏԵՆԴԵՐ> python tender_bot.py", 22, False, "#d8d8d8")
lines = [
    ("17:40:02 | INFO | Ստուգվում է՝ ARMEPS-Հայտեր (armeps.am/ppcm/public/bid-report)", "#9fe08f"),
    ("17:40:06 | INFO |   → գտնվեց 12 գրառում", "#9fe08f"),
    ("17:40:10 | INFO | Ստուգվում է՝ MinFin-Մրցույթի-հայտարարություն", "#9fe08f"),
    ("17:40:14 | INFO |   → գտնվեց 9 հայտարարություն", "#9fe08f"),
    ("", "#ffffff"),
    ("ԱՄՓՓԱԳԻՐ 2026-10-01", "#ffd479"),
    ("============================================", "#ffd479"),
    ("Նոր հայտարարություններ՝ 21   |   Հայտեր՝ 6", "#ffffff"),
    ("  - [Շինարարություն] Դպրոցի տանիքի վերանորոգում | հեռ.՝ +374 10 123456 | էլ.փ.՝ info@yerevan.am", "#8fd3ff"),
    ("  - [ՏՏ և ծրագրակազմ] Համակարգիչների ձեռքբերում | հեռ.՝ +374 11 987654 | էլ.փ.՝ it@minfin.am", "#8fd3ff"),
    ("  - [Տրանսպորտ] Ճանապարհի հիմնանորոգում | հեռ.՝ +374 77 555444 | էլ.փ.՝ road@arm.am", "#8fd3ff"),
    ("", "#ffffff"),
    ("17:40:20 | INFO | Ավարտվեց։ Տեսեք reports/ և data/ թղթապանակները։", "#9fe08f"),
]
yy = 195
for txt, col in lines:
    f.text(150, yy, txt, 20, False, col, maxw=1300)
    yy += 44
f.caption("Կարևորը. վերջին տողում լինի «Ավարտվեց» բառը։ Եթե ինչ-որ կայք չբացվի, ծրագիրը կշարունակի մյուսներով։", size=22)
f.save("s10-աշխատանքի-ընթացքը.png", OUT)

# ---------------------------------------------------------------- 11. արդյունքը
f = Fig(1600, 1010)
f.step_title(11, "Բացիր արդյունքը՝ reports պանակը", "այստեղ է քո գլխավոր աղյուսակը")
body = f.window(70, 120, 620, 780, "ՏԵՆԴԵՐ", "#3c3c3c", "#ffffff")
bx, by = body[0], body[1]
items = [("data", "F", "հայտարարություններն ըստ օրվա"),
         ("reports", "F", "ԱՂՅՈՒՍԱԿՆԵՐԸ (գլխավորը)"),
         ("inbox", "F", "ձեռքով բացված էջերը"),
         ("tender_bot.py", "P", "ծրագիրը"),
         ("config.json", "P", "կարգավորումները"),
         ("RUN.bat", "P", "գործարկման կոճակը")]
for i, (name, icon, desc) in enumerate(items):
    y = by + 30 + i * 108
    hl = name == "reports"
    f.rect(bx + 20, y, 580, 94, PRIM_L if hl else "#ffffff", "#ececec", 6, 2)
    if icon == "F":
        f.folder_icon(bx + 44, y + 14, 34)
    else:
        f.page_icon(bx + 44, y + 12, 34)
    f.text(bx + 100, y + 12, name, 24, hl, "#1a1a1a")
    f.text(bx + 100, y + 50, desc, 19, False, GRAY, maxw=480)
    if hl:
        f.highlight(bx + 14, y - 8, 592, 110, RED, 5)

body2 = f.window(740, 150, 800, 700, "TenderBot — Excel (reports\\MASTER.csv)", "#217346", "#ffffff")
bx2, by2 = body2[0], body2[1]
cols = ["Ամսաթիվ", "Ապրանք / Նպատակ", "Հեռախոս", "Էլ. փոստ"]
xs = [bx2 + 30, bx2 + 180, bx2 + 455, bx2 + 615]
ws = [145, 275, 155, 195]
f.rect(bx2 + 20, by2 + 20, 780, 50, "#217346", None, 0)
for i, c in enumerate(cols):
    f.text(xs[i], by2 + 32, c, 19, True, "#ffffff", maxw=ws[i])
rows = [["01.10.2026", "Դպրոցի տանիք", "+374 10 123456", "info@yerevan.am"],
        ["01.10.2026", "Համակարգիչներ", "+374 11 987654", "it@minfin.am"],
        ["02.10.2026", "Ճանապարհ", "+374 77 555444", "road@arm.am"],
        ["02.10.2026", "Բժշկական սարք", "010 555444", "tenders@med.am"]]
yy = by2 + 78
for i, r in enumerate(rows):
    bg = "#ffffff" if i % 2 == 0 else "#f2f7f3"
    f.rect(bx2 + 20, yy, 780, 66, bg, "#dbe6de", 4, 2)
    for j, c in enumerate(r):
        col = ORANGE if j >= 2 else "#1a1a1a"
        f.text(xs[j], yy + 20, c, 17 if j == 3 else 18, j >= 2, col, maxw=ws[j])
    yy += 74
f.highlight(bx2 + 445, by2 + 20, 375, 375, RED, 5)
f.text(bx2 + 30, by2 + 420, "Այս երկու սյունակները (Հեռախոս, Էլ. փոստ) հենց այն են,\nինչ դու ուզում էիր։", 22, True, RED, maxw=760)
f.text(bx2 + 30, by2 + 500, "Ֆայլերը բացում ես Excel-ով՝ կրկնակի սեղմելով\nreports պանակի MASTER.csv ֆայլի վրա։", 21, False, "#333333", maxw=760)
f.save("s11-արդյունքը.png", OUT)

# ---------------------------------------------------------------- 12. ամեն օր
f = Fig(1600, 1000)
f.step_title(12, "Վերջին քայլ. թող ամեն օր ինքը աշխատի", "մեկ անգամ կարգավորիր՝ ու մոռացիր")
f.rect(70, 140, 1460, 300, CARD, GREEN, 16, 3)
f.text(110, 165, "Տարբերակ Ա (ամենահեշտը)", 28, True, GREEN, maxw=1380)
f.text(110, 215, "1. Սեղմիր Win+R, գրիր  shell:startup  և Enter։ Բացվում է «Startup» պանակը։\n"
                 "2. Այդ պանակի մեջ քաշիր (պատճենիր) ՏԵՆԴԵՐ պանակի RUN.bat ֆայլը։", 23, False, "#243a12", maxw=1380)
f.text(110, 320, "Այսուհետ ամեն անգամ, երբ համակարգիչը միացնես, ծրագիրը ինքը կստուգի կայքերը։", 23, True, GREEN, maxw=1380)
f.text(110, 380, "💡 Եթե ուզում ես, որ ամեն օր մի քանի անգամ էլ ստուգի՝ RUN.bat-ը կարող է մնալ բաց պատուհանով ամբողջ օրը (−−loop ռեժիմ)։", 21, False, GRAY, maxw=1380)

f.rect(70, 480, 1460, 330, ORANGE_L, None, 16)
f.text(110, 505, "Տարբերակ Բ (եթե սիրում ես կոճակներով պատուհաններ)", 28, True, ORANGE, maxw=1380)
f.text(110, 555, "1. Win+R → taskschd.msc → Enter\n"
                 "2. Աջ կողմում՝ Create Basic Task…\n"
                 "3. Անունը՝ Տենդեր, հաճախականությունը՝ Daily, ժամը՝ 08:00\n"
                 "4. Action՝ Start a program. Program/script՝ python , Add arguments՝ tender_bot.py ,\n"
                 "    Start in՝ C:\\Users\\քո-անունը\\Desktop\\ՏԵՆԴԵՐ\n"
                 "5. Finish։", 22, False, "#5a2b00", maxw=1380)
f.caption("Երկու տարբերակն էլ ճիշտ է։ Առաջինը երաշխավորում եմ ամենապարզը լինելու համար։", size=25)
f.save("s12-ամեն-օր-ավտոմատ.png", OUT)

print("Պատրաստ է։")
