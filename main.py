#!/usr/bin/env python3
"""News image for Friday 20 November 2026.

Draws a warm-cream atlas poster summarising the day's world news and
writes it as entry.png (1024x1024, deterministic, stdlib only).

Everything is drawn in code: a software rasteriser (rectangles, circles,
polygon fills, a star), a hand-drawn 5x7 bitmap font, and a small PNG
encoder built on zlib + struct. No external files, no network, no
randomness, no timestamps.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# Palette
CREAM = (247, 241, 227)   # warm paper
TEAL = (15, 76, 92)       # main type
SAGE = (122, 158, 140)    # continents
OCHRE = (217, 164, 65)    # accents
RED = (192, 57, 43)       # hero marker / date banner
GREY = (74, 74, 68)       # summary type
WHITE = (255, 255, 255)
BAND = (243, 231, 200)    # hero band tint
DARKRED = (140, 40, 30)   # pin outline


# ---------------------------------------------------------------- font
# 5x7 bitmap font, drawn by hand. Each glyph is 7 rows of 5 bits;
# bit 4 is the leftmost column. Only uppercase is needed: draw_text
# upper-cases its input.
FONT = {
    'A': (14, 17, 17, 31, 17, 17, 17),
    'B': (30, 17, 17, 30, 17, 17, 30),
    'C': (15, 16, 16, 16, 16, 16, 15),
    'D': (30, 17, 17, 17, 17, 17, 30),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'F': (31, 16, 16, 30, 16, 16, 16),
    'G': (15, 16, 16, 23, 17, 17, 14),
    'H': (17, 17, 17, 31, 17, 17, 17),
    'I': (14, 4, 4, 4, 4, 4, 14),
    'J': (7, 2, 2, 2, 2, 18, 12),
    'K': (17, 18, 20, 24, 20, 18, 17),
    'L': (16, 16, 16, 16, 16, 16, 31),
    'M': (17, 27, 21, 21, 17, 17, 17),
    'N': (17, 25, 25, 21, 19, 19, 17),
    'O': (14, 17, 17, 17, 17, 17, 14),
    'P': (30, 17, 17, 30, 16, 16, 16),
    'Q': (14, 17, 17, 17, 21, 18, 13),
    'R': (30, 17, 17, 30, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'U': (17, 17, 17, 17, 17, 17, 14),
    'V': (17, 17, 17, 17, 17, 10, 4),
    'W': (17, 17, 17, 21, 21, 27, 17),
    'X': (17, 17, 10, 4, 10, 17, 17),
    'Y': (17, 17, 10, 4, 4, 4, 4),
    'Z': (31, 1, 2, 4, 8, 16, 31),
    '0': (14, 17, 19, 21, 25, 17, 14),
    '1': (4, 12, 4, 4, 4, 4, 14),
    '2': (14, 17, 1, 2, 4, 8, 31),
    '3': (14, 17, 1, 6, 1, 17, 14),
    '4': (2, 6, 10, 18, 31, 2, 2),
    '5': (31, 16, 30, 1, 1, 17, 14),
    '6': (14, 16, 16, 30, 17, 17, 14),
    '7': (31, 1, 2, 4, 4, 4, 4),
    '8': (14, 17, 17, 14, 17, 17, 14),
    '9': (14, 17, 17, 15, 1, 1, 14),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 12, 12),
    ',': (0, 0, 0, 0, 12, 12, 8),
    '-': (0, 0, 0, 14, 0, 0, 0),
    "'": (4, 4, 8, 0, 0, 0, 0),
    '"': (10, 10, 0, 0, 0, 0, 0),
    '!': (4, 4, 4, 4, 4, 0, 4),
    '?': (14, 17, 1, 2, 4, 0, 4),
    '(': (2, 4, 8, 8, 8, 4, 2),
    ')': (8, 4, 2, 2, 2, 4, 8),
    ':': (0, 12, 12, 0, 12, 12, 0),
    ';': (0, 12, 12, 0, 12, 12, 8),
    '/': (1, 1, 2, 4, 8, 16, 16),
    '&': (12, 18, 18, 8, 21, 18, 13),
    '%': (17, 18, 2, 4, 8, 18, 17),
    '+': (0, 4, 4, 14, 4, 4, 0),
    '=': (0, 0, 14, 0, 14, 0, 0),
    '_': (0, 0, 0, 0, 0, 0, 31),
    '$': (4, 15, 20, 14, 5, 30, 4),
    '*': (0, 21, 14, 31, 14, 21, 0),
}


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = r
                self.buf[i + 1] = g
                self.buf[i + 2] = b

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.px(cx - dx, cy + dy, color)
            self.px(cx + dx, cy + dy, color)
        for dx in range(-r, r + 1):
            dy = int((r * r - dx * dx) ** 0.5)
            self.px(cx + dx, cy - dy, color)
            self.px(cx + dx, cy + dy, color)

    def fill_polygon(self, pts, color):
        """Scanline polygon fill. pts is a list of (x, y) in order."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, min(ys))
        y1 = min(self.h - 1, max(ys))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, y1p = pts[i]
                x2, y2p = pts[(i + 1) % n]
                if (y1p <= y < y2p) or (y2p <= y < y1p):
                    if y2p != y1p:
                        x = x1 + (y - y1p) * (x2 - x1) / (y2p - y1p)
                        xs.append(x)
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                xa = int(round(xs[j]))
                xb = int(round(xs[j + 1]))
                if xb > xa:
                    self.fill_rect(xa, y, xb - xa, 1, color)

    def star(self, cx, cy, r_out, r_in, color):
        import math
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            r = r_out if k % 2 == 0 else r_in
            pts.append((int(round(cx + r * math.cos(ang))),
                        int(round(cy + r * math.sin(ang)))))
        self.fill_polygon(pts, color)


# ---------------------------------------------------------------- text
def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, color, bold=False):
    """Draw text at (x, y); returns the pixel width drawn."""
    text = text.upper()
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
                    if bold:
                        cv.fill_rect(cx + col * scale + 1, y + row * scale,
                                     scale, scale, color)
        cx += 6 * scale
    return cx - x - scale


def draw_text_centered(cv, cx, y, text, scale, color, bold=False):
    w = text_width(text, scale)
    draw_text(cv, cx - w // 2, y, text, scale, color, bold)
    return w


# ---------------------------------------------------------------- png
def write_png(cv, path):
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.buf[y * stride:(y + 1) * stride]
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', ihdr)
           + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
           + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)


# ---------------------------------------------------------------- map
# Map window: x 20..1004, y 150..480. Equirectangular, lon -180..180,
# lat 75..-60. Simplified, stylised continent outlines (lon, lat).
MAP_X0, MAP_Y0 = 20, 150
MAP_W, MAP_H = 984, 330


def project(lon, lat):
    x = MAP_X0 + (lon + 180) * MAP_W / 360.0
    y = MAP_Y0 + (75 - lat) * MAP_H / 135.0
    return (int(round(x)), int(round(y)))


def poly(cv, lonlat, color):
    cv.fill_polygon([project(lo, la) for lo, la in lonlat], color)


NORTH_AMERICA = [(-165, 60), (-150, 70), (-135, 69), (-125, 72), (-120, 70),
                 (-110, 68), (-95, 69), (-85, 66), (-80, 73), (-70, 62),
                 (-60, 55), (-55, 47), (-65, 45), (-70, 42), (-75, 35),
                 (-80, 32), (-85, 29), (-90, 21), (-95, 19), (-100, 23),
                 (-105, 20), (-110, 23), (-115, 28), (-120, 34), (-125, 40),
                 (-125, 48), (-135, 58), (-150, 60)]
GREENLAND = [(-58, 64), (-45, 60), (-40, 64), (-32, 68), (-25, 70),
             (-20, 74), (-30, 76), (-45, 76), (-58, 74)]
SOUTH_AMERICA = [(-80, 10), (-75, 5), (-70, 0), (-65, -2), (-60, 2),
                 (-50, 0), (-40, -5), (-35, -8), (-40, -15), (-45, -22),
                 (-50, -30), (-55, -35), (-60, -40), (-65, -50),
                 (-70, -55), (-75, -50), (-75, -40), (-75, -30),
                 (-78, -20), (-80, -10), (-80, 0), (-78, 8)]
AFRICA = [(-10, 35), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28),
          (40, 20), (45, 11), (50, 10), (45, 0), (40, -10), (35, -20),
          (30, -30), (20, -35), (15, -30), (10, -20), (10, -10), (5, 0),
          (0, 5), (-8, 5), (-15, 10), (-17, 15), (-15, 25), (-10, 30)]
EUROPE = [(-10, 36), (-9, 43), (0, 44), (5, 43), (10, 44), (15, 40),
          (20, 40), (25, 36), (30, 36), (28, 41), (25, 45), (20, 45),
          (15, 45), (10, 46), (5, 48), (0, 50), (-5, 50), (-10, 48),
          (-10, 40)]
BRITAIN = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
           (-2, 51)]
ASIA = [(30, 36), (35, 36), (40, 38), (45, 40), (50, 40), (55, 42),
        (60, 45), (65, 45), (70, 50), (75, 55), (80, 60), (85, 65),
        (90, 70), (100, 72), (110, 73), (120, 72), (130, 70), (140, 72),
        (150, 70), (160, 68), (170, 66), (178, 65), (170, 60), (160, 60),
        (155, 55), (150, 60), (145, 60), (140, 55), (135, 50), (130, 45),
        (127, 40), (122, 38), (120, 32), (115, 25), (110, 20), (105, 15),
        (100, 10), (98, 8), (95, 15), (92, 20), (88, 22), (85, 18),
        (80, 15), (78, 10), (75, 12), (72, 20), (70, 22), (65, 25),
        (60, 25), (55, 26), (50, 28), (48, 30), (45, 30), (42, 35),
        (38, 36), (35, 36)]
AUSTRALIA = [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32),
             (130, -32), (135, -35), (140, -38), (145, -38), (150, -37),
             (153, -30), (150, -25), (145, -20), (142, -15), (140, -12),
             (135, -12), (132, -11), (130, -13), (126, -14), (122, -17),
             (118, -20)]
# Island groups, drawn as small blobs (lon, lat, radius in px).
ISLANDS = [(100, 0, 9), (104, -2, 7), (112, -2, 10), (117, -1, 6),
           (122, 12, 6), (138, 36, 8), (140, -5, 11), (130, -3, 6),
           (95, 5, 6), (105, 2, 5)]


def draw_map(cv):
    for cont in (NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EUROPE,
                 BRITAIN, ASIA, AUSTRALIA):
        poly(cv, cont, SAGE)
    for lon, lat, r in ISLANDS:
        x, y = project(lon, lat)
        cv.fill_circle(x, y, r, SAGE)


def pin(cv, lon, lat, num, color=RED):
    x, y = project(lon, lat)
    cv.fill_circle(x, y, 12, color)
    cv.ring(x, y, 12, DARKRED)
    draw_text_centered(cv, x, y - 7, str(num), 2, WHITE, bold=True)
    return x, y


def dot(cv, lon, lat, color=OCHRE):
    x, y = project(lon, lat)
    cv.fill_circle(x, y, 7, color)
    cv.ring(x, y, 7, DARKRED)
    return x, y


# ---------------------------------------------------------------- content
LEAD = [
    # (headline, summary line) — one summary line per story so rows
    # never crowd each other.
    ("UN COURT: MYANMAR COMMITTED GENOCIDE",
     ["Historic verdict from the International Court of Justice.",
      "A landmark ruling for the Rohingya after years of proceedings."]),
    ("TRUMP, XI AND PUTIN MEET IN SHENZHEN",
     ["First trilateral summit on nuclear risks and energy; no breakthrough."]),
    ("MISSILE HITS RIYADH FINANCIAL DISTRICT",
     ["Suspected Houthi missile strikes Saudi Arabia's financial centre, KAFD."]),
    ("VOYAGER 1 REACHES ONE LIGHT-DAY OUT",
     ["A signal now takes a full day to reach it; its data flow has stopped."]),
    ("ANTHROPIC DEBUTS AT $1.5 TRILLION",
     ["One of the world's most valuable companies on its first trading day."]),
    ("CYCLONE AKVAN NEARS ODISHA COAST",
     ["Schools closed and evacuations under way as the storm bears down."]),
]

ALSO = [
    "MUSK: 'I'M NOT MAGA' AFTER $500M BET",
    "TRUMP PARDONS BASEBALL'S PETE ROSE",
    "MUSLIMS LARGEST FAITH BY 2035: PEW",
    "TANKER BURNS AFTER MINE NEAR HORMUZ",
    "ISRAELI STRIKE ON HEZBOLLAH SITE",
    "NZ 243-5 AS NICHOLLS HITS 100*",
]


def draw(cv):
    # Date banner
    cv.fill_rect(0, 0, W, 70, RED)
    draw_text_centered(cv, W // 2, 21, "FRIDAY, 20 NOVEMBER 2026", 4,
                       WHITE, bold=True)

    # Title
    draw_text_centered(cv, W // 2, 84, "ONE DAY, ONE WORLD", 5, TEAL,
                       bold=True)
    cv.fill_rect(312, 132, 400, 4, OCHRE)

    # Map
    draw_map(cv)
    # Lead-story pins (numbers match the list below)
    pin(cv, 96, 21, 1)        # Myanmar
    pin(cv, 114, 22.5, 2)     # Shenzhen
    pin(cv, 46.7, 24.6, 3)    # Riyadh
    pin(cv, -74, 40.7, 5)     # New York / Anthropic debut
    pin(cv, 85.5, 20, 6)      # Odisha
    # Voyager: deep space, in the open Pacific east of Japan
    vx, vy = 955, 250
    draw_text_centered(cv, vx, vy + 18, "VOYAGER 1", 2, TEAL, bold=True)
    cv.fill_circle(vx, vy, 12, RED)
    cv.ring(vx, vy, 12, DARKRED)
    draw_text_centered(cv, vx, vy - 7, "4", 2, WHITE, bold=True)
    cv.star(988, 228, 9, 4, OCHRE)
    cv.star(922, 232, 6, 3, OCHRE)
    # Also-today dots
    dot(cv, 56.5, 26.5)       # Strait of Hormuz
    dot(cv, 35.8, 33.8)       # Lebanon
    dot(cv, -42, 72)          # Greenland

    # Legend
    draw_text_centered(cv, W // 2, 490,
                       "RED PINS: LEAD STORIES  -  AMBER DOTS: ALSO TODAY",
                       2, GREY)

    # Hero story (band)
    cv.fill_rect(40, 516, 944, 92, BAND)
    cv.fill_rect(40, 516, 8, 92, RED)
    cv.fill_circle(72, 562, 15, RED)
    draw_text_centered(cv, 72, 555, "1", 2, WHITE, bold=True)
    draw_text(cv, 100, 530, LEAD[0][0], 3, TEAL, bold=True)
    draw_text(cv, 100, 560, LEAD[0][1][0], 2, GREY)
    draw_text(cv, 100, 580, LEAD[0][1][1], 2, GREY)

    # Stories 2-6: one summary line each, generous row spacing so
    # nothing crowds the next headline.
    y = 624
    for i in range(1, 6):
        headline, lines = LEAD[i]
        cv.fill_rect(48, y, 26, 26, TEAL)
        draw_text_centered(cv, 61, y + 6, str(i + 1), 2, WHITE, bold=True)
        draw_text(cv, 88, y + 2, headline, 3, TEAL, bold=True)
        draw_text(cv, 88, y + 28, lines[0], 2, GREY)
        y += 54

    # Also today strip
    cv.fill_rect(40, 908, 944, 3, OCHRE)
    draw_text(cv, 40, 920, "ALSO TODAY", 3, TEAL, bold=True)
    # order: col 1 top-to-bottom, then col 2
    order = [0, 2, 4, 1, 3, 5]
    for k, idx in enumerate(order):
        col = 0 if k < 3 else 1
        row = k % 3
        x = 40 if col == 0 else 540
        yy = 952 + row * 28
        cv.fill_rect(x, yy + 4, 8, 8, OCHRE)
        draw_text(cv, x + 16, yy, ALSO[idx], 2, GREY)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, CREAM)
    draw(cv)
    write_png(cv, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
