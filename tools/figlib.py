#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Նկարների գրադարանը՝ guide/img/*.png ստեղծելու համար (հայերեն տեքստով)։"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

F = "/usr/share/fonts/truetype/dejavu/"
SANS = F + "DejaVuSans.ttf"
BOLD = F + "DejaVuSans-Bold.ttf"
K = 2  # supersampling

BG = "#f4f7fb"; CARD = "#ffffff"; PRIM = "#1f4e79"; PRIM_L = "#dce9f7"
BLUE = "#2e75b6"; ORANGE = "#c55a11"; ORANGE_L = "#fdeada"
GREEN = "#548235"; GREEN_L = "#e2efda"; PURPLE = "#7030a0"; PURPLE_L = "#eee1f5"
RED = "#c00000"; RED_L = "#ffe1e1"; GRAY = "#595959"; LINE = "#8ea9c9"
WIN_BG = "#f0f0f0"; WIN_BAR = "#2b579a"; TASKBAR = "#1f1f1f"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else SANS, size * K)


def wrap(draw, s, f, maxw):
    """Տողադարձ՝ բառերով. շատ երկար բառերը՝ մեջտեղից։"""
    lines = []
    for para in str(s).split("\n"):
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

    # ---------------- հիմնական ձևեր
    def rect(self, x, y, w, h, fill=CARD, outline=None, radius=14, width=2):
        self.d.rounded_rectangle([x * K, y * K, (x + w) * K, (y + h) * K],
                                 radius=radius * K, fill=fill,
                                 outline=outline, width=width * K if outline else 0)

    def text(self, x, y, s, size=26, bold=False, fill="#1a1a1a", maxw=None, gap=8):
        f = font(size, bold)
        lines = wrap(self.d, s, f, maxw)
        lh = size * K * 1.32 + gap * K
        yy = y * K
        for ln in lines:
            self.d.text((x * K, yy), ln, font=f, fill=fill)
            yy += lh
        return (yy - y * K) / K

    def center(self, cx, y, s, size=26, bold=False, fill="#1a1a1a", maxw=None):
        f = font(size, bold)
        lines = wrap(self.d, s, f, maxw)
        lh = size * K * 1.32
        for i, ln in enumerate(lines):
            self.d.text((cx * K - self.d.textlength(ln, font=f) / 2, y * K + i * lh), ln, font=f, fill=fill)
        return len(lines) * lh / K

    def line(self, x1, y1, x2, y2, fill=LINE, width=2):
        self.d.line([x1 * K, y1 * K, x2 * K, y2 * K], fill=fill, width=width * K)

    def arrow(self, x1, y1, x2, y2, fill=RED, width=6, head=18):
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

    # ---------------- Windows-ի նման տարրեր
    def window(self, x, y, w, h, title, bar_color=WIN_BAR, body=WIN_BG, radius=10):
        self.rect(x, y, w, h, CARD, "#c9c9c9", radius)
        self.d.rounded_rectangle([x * K, y * K, (x + w) * K, (y + 44) * K], radius=radius * K,
                                 fill=bar_color)
        self.d.rectangle([x * K, (y + 30) * K, (x + w) * K, (y + 44) * K], fill=bar_color)
        self.text(x + 16, y + 10, title, 20, True, "#ffffff", maxw=w - 120)
        # փակելու կոճակ
        self.text(x + w - 34, y + 8, "✕", 20, True, "#ffffff")
        self.rect(x, y + 44, w, h - 44, body, None, radius)
        return (x, y + 44, w, h - 44)

    def button(self, x, y, w, h, label, fill=WIN_BAR, tcolor="#ffffff", size=20, bold=True, radius=8,
               outline=None):
        self.rect(x, y, w, h, fill, outline, radius)
        f = font(size, bold)
        cy = y + h / 2 - size * 0.68
        self.d.text((x * K + w * K / 2 - self.d.textlength(label, font=f) / 2, cy * K), label, font=f, fill=tcolor)

    def checkbox(self, x, y, checked=False, size=26, label="", label_size=22, label_fill="#1a1a1a"):
        self.rect(x, y, size, size, "#ffffff", "#4d4d4d", radius=4, width=2)
        if checked:
            self.line(x + 6, y + size / 2, x + size / 2 - 2, y + size - 7, fill=GREEN, width=5)
            self.line(x + size / 2 - 2, y + size - 7, x + size - 5, y + 6, fill=GREEN, width=5)
        if label:
            self.text(x + size + 14, y + size / 2 - label_size * 0.72, label, label_size, False, label_fill)

    def highlight(self, x, y, w, h, color=RED, width=4, radius=8):
        self.d.rounded_rectangle([x * K, y * K, (x + w) * K, (y + h) * K], radius=radius * K,
                                 outline=color, width=width * K)

    def pointer(self, x, y, scale=1.0):
        """Մկնիկի սլաքը։"""
        pts = [(0, 0), (0, 22), (6, 16), (10, 26), (15, 24), (11, 14), (18, 13)]
        self.d.polygon([(x * K + px * scale * K, y * K + py * scale * K) for px, py in pts],
                       fill="#ffffff", outline="#000000", width=int(2 * K))

    # ---------------- պատկերանշաններ (emoji-ի փոխարեն՝ նկարված)
    def folder_icon(self, x, y, size=34, color="#f2b134", outline="#c98a12"):
        w = size; h = size * 0.78
        self.d.rounded_rectangle([(x + size * 0.18) * K, y * K, (x + size * 0.62) * K, (y + h * 0.30) * K],
                                 radius=3 * K, fill=outline)
        self.d.rounded_rectangle([x * K, (y + h * 0.18) * K, (x + w) * K, (y + h) * K],
                                 radius=4 * K, fill=color, outline=outline, width=int(1.6 * K))

    def page_icon(self, x, y, size=34, color="#ffffff", outline="#7a7a7a", lines=3):
        w = size * 0.78; h = size
        self.d.rounded_rectangle([x * K, y * K, (x + w) * K, (y + h) * K], radius=3 * K,
                                 fill=color, outline=outline, width=int(1.6 * K))
        for i in range(lines):
            yy = y + h * (0.34 + 0.20 * i)
            self.d.line([(x + w * 0.18) * K, yy * K, (x + w * 0.82) * K, yy * K],
                        fill=outline, width=int(1.4 * K))

    def monitor_icon(self, x, y, size=34, color="#3c3c3c"):
        w = size; h = size * 0.68
        self.d.rounded_rectangle([x * K, y * K, (x + w) * K, (y + h) * K], radius=3 * K,
                                 fill="#ffffff", outline=color, width=int(2 * K))
        self.d.rectangle([(x + w * 0.42) * K, (y + h) * K, (x + w * 0.58) * K, (y + h * 1.22) * K], fill=color)
        self.d.rectangle([(x + w * 0.2) * K, (y + h * 1.22) * K, (x + w * 0.8) * K, (y + h * 1.38) * K], fill=color)

    def lock_icon(self, x, y, size=30, color="#4d4d4d"):
        w = size * 0.78; h = size * 0.62
        self.d.arc([(x + w * 0.18) * K, y * K, (x + w * 0.82) * K, (y + h * 1.1) * K],
                   start=180, end=360, fill=color, width=int(2.4 * K))
        self.d.rounded_rectangle([x * K, (y + h * 0.5) * K, (x + w) * K, (y + h * 1.6) * K],
                                 radius=3 * K, fill=color)

    def zip_icon(self, x, y, size=34, color="#5b5b5b"):
        w = size * 0.8; h = size
        self.d.rounded_rectangle([x * K, y * K, (x + w) * K, (y + h) * K], radius=4 * K,
                                 fill="#f0f0f0", outline=color, width=int(1.8 * K))
        for i in range(4):
            yy = y + 6 + i * (h / 5.4)
            self.d.rectangle([(x + w * 0.42) * K, yy * K, (x + w * 0.58) * K, (yy + h / 9) * K], fill=color)

    def caption_bar(self, text, y=None, size=26, fill=PRIM, bar="#ffffff"):
        """Ներքևի բացատրությունը՝ սպիտակ քարտի վրա, որ միշտ ընթեռնելի լինի։"""
        y = (self.h - 96) if y is None else y
        f = font(size, True)
        lines = wrap(self.d, text, f, self.w - 200)
        h = 26 + len(lines) * size * 1.5
        self.rect(60, y, self.w - 120, h, bar, None, 12)
        for i, ln in enumerate(lines):
            self.d.text((self.w * K / 2 - self.d.textlength(ln, font=f) / 2,
                         (y + 12 + i * size * 1.5) * K), ln, font=f, fill=fill)
        return h

    def caption(self, text, y=None, size=27, fill=PRIM, bold=True, cx=None):
        cx = self.w / 2 if cx is None else cx
        y = self.h - 60 if y is None else y
        self.center(cx, y, text, size, bold, fill, maxw=self.w - 120)

    def step_title(self, n, text, sub=None):
        self.circle_num(40, 26, n, 32, ORANGE)
        self.text(120, 16, text, 36, True, PRIM, maxw=self.w - 200)
        if sub:
            self.text(120, 66, sub, 23, False, GRAY, maxw=self.w - 200)

    def save(self, name, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, name)
        self.img.resize((self.w, self.h), Image.LANCZOS).save(path, "PNG", optimize=True)
        print("ok", name)


def taskbar(fig, y=None, active=""):
    """Windows-ի ներքևի սև գոտին։"""
    h = 62
    y = (fig.h - h) if y is None else y
    fig.rect(0, y, fig.w, h, TASKBAR, None, 0)
    fig.text(24, y + 16, "⊞", 30, True, "#ffffff")
    for i, item in enumerate(["Edge", "Explorer", "Word", "Excel"]):
        col = "#3a3a3a" if item == active else "#2b2b2b"
        fig.rect(100 + i * 150, y + 9, 140, 44, col, None, 6)
        fig.text(120 + i * 150, y + 20, item, 18, False, "#dddddd")
