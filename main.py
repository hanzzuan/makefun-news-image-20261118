"""THE WORLD — Wednesday 18 November 2026.

A newspaper front page drawn procedurally in Python 3.13 stdlib only.
No network, no fonts, no image files: every pixel comes from the code
below — a 5x7 bitmap font, rectangles, lines, circles and polygons —
and the PNG bytes are encoded by hand with zlib and CRC32.

Layout (1024 x 1024): masthead and the date in red, one lead story
(Xi and Putin open talks in Shenzhen as APEC opens), then Manila for
the QUAD, the Gulf drone attacks, and three smaller stories — Alaska,
the Siberian plane crash, and the Papua New Guinea earthquake.
"""

import math
import os
import struct
import zlib

from font5x7 import glyph, text_height, text_width

W, H = 1024, 1024

PAPER = (253, 253, 247)
INK = (18, 18, 18)
RED = (186, 39, 32)
BLUE = (28, 68, 110)
GOLD = (176, 112, 24)
GREY = (128, 128, 122)
LIGHT = (236, 236, 229)
SKY = (205, 222, 235)


class Page:
    """An RGB pixel buffer with small drawing helpers."""

    def __init__(self, width, height, colour):
        self.w = width
        self.h = height
        self.buf = bytearray(width * height * 3)
        self.fill_rect(0, 0, width, height, colour)

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = colour

    def fill_rect(self, x, y, w, h, colour):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i], self.buf[i + 1], self.buf[i + 2] = colour

    def hline(self, x, y, w, colour, t=1):
        self.fill_rect(x, y, w, t, colour)

    def vline(self, x, y, h, colour, t=1):
        self.fill_rect(x, y, t, h, colour)

    def rect(self, x, y, w, h, colour, t=1):
        self.hline(x, y, w, colour, t)
        self.hline(x, y + h - t, w, colour, t)
        self.vline(x, y, h, colour, t)
        self.vline(x + w - t, y, h, colour, t)

    def line(self, x0, y0, x1, y1, colour):
        """Bresenham line between two points."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, colour)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, colour, t=3):
        """A line drawn t pixels wide, by offsetting across its normal."""
        dx, dy = x1 - x0, y1 - y0
        length = max(1, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        half = t // 2
        for k in range(-half, half + 1):
            ox, oy = round(nx * k), round(ny * k)
            self.line(x0 + ox, y0 + oy, x1 + ox, y1 + oy, colour)

    def circle(self, cx, cy, r, colour, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, colour)
                elif r - 1 <= math.sqrt(d) <= r:
                    self.set(xx, yy, colour)

    def fill_poly(self, points, colour):
        """Scanline fill of a polygon given as (x, y) vertices."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.set(x, y, colour)

    def star(self, cx, cy, r, colour):
        """A filled five-pointed star."""
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.42
            pts.append((cx + round(rad * math.cos(ang)),
                        cy + round(rad * math.sin(ang))))
        self.fill_poly(pts, colour)


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_png(page):
    """Encode the page as a PNG: header, one IDAT, end marker."""
    raw = bytearray()
    for y in range(page.h):
        raw.append(0)  # filter type 0: none
        raw += page.buf[y * page.w * 3:(y + 1) * page.w * 3]
    ihdr = struct.pack(">IIBBBBB", page.w, page.h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


# ---------------------------------------------------------------- text

def draw_text(page, x, y, text, scale, colour, gap=1):
    """Draw one line of text, left-aligned at (x, y)."""
    cx = x
    for ch in text:
        rows = glyph(ch)
        for r in range(7):
            bits = rows[r]
            for c in range(5):
                if bits & (1 << (4 - c)):
                    page.fill_rect(cx + c * scale, y + r * scale,
                                   scale, scale, colour)
        cx += 5 * scale + gap
    return cx


def draw_centred(page, x, y, w, text, scale, colour, gap=1):
    """Draw one line centred in the band [x, x + w)."""
    tw = text_width(text, scale, gap)
    draw_text(page, x + (w - tw) // 2, y, text, scale, colour, gap)


# ---------------------------------------------------------------- panels

def panel(page, x, y, w, h):
    """A story panel: thin black frame on paper, with a hairline inside."""
    page.rect(x, y, w, h, INK, 2)
    page.rect(x + 4, y + 4, w - 8, h - 8, GREY, 1)


def kicker(page, x, y, text, colour=RED):
    """Small red section label with a square bullet."""
    page.fill_rect(x, y + 2, 10, 10, colour)
    draw_text(page, x + 16, y, text, 2, colour, gap=1)


def headline(page, x, y, w, lines, scale, colour=INK, gap=1, leading=None):
    """Centred headline lines; returns the y below the last line."""
    if leading is None:
        leading = text_height(scale) + 6
    cy = y
    for line in lines:
        draw_centred(page, x, cy, w, line, scale, colour, gap)
        cy += leading
    return cy


def rule(page, x, y, w, colour=INK, t=2):
    page.hline(x, y, w, colour, t)


# ---------------------------------------------------------------- visuals

def flag_china(page, x, y, w, h):
    """Red field, one large yellow star and four small ones."""
    page.fill_rect(x, y, w, h, (222, 41, 16))
    page.star(x + w // 5, y + h // 3, h // 5, GOLD)
    for sx, sy in ((w * 2 // 5, h // 6), (w // 2, h // 8),
                   (w * 3 // 5, h // 5), (w * 3 // 5, h * 2 // 5)):
        page.star(x + sx, y + sy, h // 12, GOLD)


def flag_russia(page, x, y, w, h):
    """White over blue over red horizontal tricolour."""
    third = h // 3
    page.fill_rect(x, y, w, third, (245, 245, 245))
    page.fill_rect(x, y + third, w, third, (0, 57, 166))
    page.fill_rect(x, y + 2 * third, w, h - 2 * third, (213, 0, 50))
    page.rect(x, y, w, h, INK, 1)


def skyline(page, x, y, w, h, colour=BLUE):
    """A row of towers of different heights against the sky."""
    page.fill_rect(x, y, w, h, SKY)
    tops = [0.45, 0.25, 0.6, 0.15, 0.4, 0.55, 0.3, 0.5]
    n = len(tops)
    bw = w // n
    for i, frac in enumerate(tops):
        th = int(h * frac)
        page.fill_rect(x + i * bw + 2, y + h - th, bw - 4, th, colour)
        # A lit window or two on each tower.
        page.fill_rect(x + i * bw + bw // 2 - 2, y + h - th + 6, 4, 5, GOLD)
    page.fill_rect(x, y + h - 4, w, 4, INK)


def jet(page, x, y, s, colour=INK):
    """A simple passenger jet in profile, nose to the right."""
    page.fill_poly([(x, y), (x + 30 * s, y - 3 * s), (x + 44 * s, y),
                    (x + 30 * s, y + 3 * s)], colour)
    page.fill_poly([(x + 8 * s, y), (x + 16 * s, y - 10 * s),
                    (x + 20 * s, y - 10 * s), (x + 18 * s, y)], colour)
    page.fill_poly([(x + 26 * s, y), (x + 32 * s, y - 8 * s),
                    (x + 35 * s, y - 8 * s), (x + 33 * s, y)], colour)
    page.fill_poly([(x + 2 * s, y - 2 * s), (x + 6 * s, y - 9 * s),
                    (x + 9 * s, y - 9 * s), (x + 8 * s, y - 2 * s)], colour)
    page.fill_rect(x + 36 * s, y - 1 * s, 6 * s, 2 * s, colour)


def drone(page, cx, cy, s, colour=INK):
    """A quadcopter seen from the side: body, arms, four rotors."""
    page.fill_rect(cx - 6 * s, cy - 2 * s, 12 * s, 4 * s, colour)
    page.thick_line(cx - 12 * s, cy - 6 * s, cx - 4 * s, cy - 2 * s, colour, 2)
    page.thick_line(cx + 4 * s, cy - 2 * s, cx + 12 * s, cy - 6 * s, colour, 2)
    for rx in (-14 * s, -10 * s, 10 * s, 14 * s):
        page.hline(cx + rx - 6 * s, cy - 7 * s, 12 * s, colour, 2)
    page.circle(cx, cy + 1 * s, 2 * s, RED, fill=True)


def radar(page, cx, cy, r, colour=BLUE):
    """Concentric radar arcs sweeping up to the right."""
    for rr in range(r // 3, r + 1, r // 3):
        for ang in range(-80, 11, 2):
            a = math.radians(ang)
            px = cx + round(rr * math.cos(a))
            py = cy - round(rr * math.sin(a))
            page.fill_rect(px, py, 2, 2, colour)
    page.thick_line(cx, cy, cx + r, cy - r // 2, colour, 2)
    page.circle(cx, cy, 4, RED, fill=True)


def ballot_box(page, x, y, w, h, colour=INK):
    """A ballot box with a paper slip and a big tick."""
    page.fill_rect(x, y + h // 3, w, h * 2 // 3, LIGHT)
    page.rect(x, y + h // 3, w, h * 2 // 3, colour, 2)
    page.fill_rect(x + w // 4, y + h // 3 - 4, w // 2, 4, colour)
    page.fill_rect(x + w // 3, y + 4, w // 3, h // 4, PAPER)
    page.rect(x + w // 3, y + 4, w // 3, h // 4, colour, 1)
    page.thick_line(x + w // 6, y + h * 2 // 3, x + w // 2,
                    y + h - 6, RED, 5)
    page.thick_line(x + w // 2, y + h - 6, x + w - w // 6,
                    y + h // 3 + 6, RED, 5)


def mountains(page, x, y, w, h, colour=BLUE):
    """Snow-capped peaks with a smoke trail above."""
    page.fill_poly([(x, y + h), (x + w // 4, y + h // 3),
                    (x + w // 2, y + h)], colour)
    page.fill_poly([(x + w // 3, y + h), (x + w * 2 // 3, y + h // 5),
                    (x + w, y + h)], colour)
    page.fill_poly([(x + w // 4 - 12, y + h // 3),
                    (x + w // 4 + 12, y + h // 3),
                    (x + w // 4, y + h // 3 + 16)], PAPER)
    page.fill_poly([(x + w * 2 // 3 - 12, y + h // 5),
                    (x + w * 2 // 3 + 12, y + h // 5),
                    (x + w * 2 // 3, y + h // 5 + 16)], PAPER)


def seismograph(page, x, y, w, h, colour=INK):
    """A wavy trace line, calm, then one tall spike, then calm again."""
    page.fill_rect(x, y, w, h, LIGHT)
    page.hline(x, y + h // 2, w, GREY, 1)
    pts = []
    n = 24
    for i in range(n + 1):
        px = x + i * w // n
        if i == 12:
            py = y + 8
        elif i == 11:
            py = y + h // 2 + h // 4
        elif i == 13:
            py = y + h // 2 - h // 4
        else:
            py = y + h // 2 + (5 if i % 2 else -5)
        pts.append((px, py))
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        hot = 10 <= k <= 13
        page.thick_line(a[0], a[1], b[0], b[1], RED if hot else colour, 2)


# ---------------------------------------------------------------- layout

def draw_masthead(page):
    """THE WORLD in large type, then the date in red, large and plain."""
    draw_centred(page, 0, 26, W, "THE WORLD", 8, INK, gap=2)
    rule(page, 24, 96, W - 48, INK, 3)
    rule(page, 24, 102, W - 48, RED, 2)
    draw_centred(page, 0, 112, W, "WEDNESDAY 18 NOVEMBER 2026", 4, RED, gap=2)


def draw_lead(page):
    """Shenzhen: Xi and Putin open talks as APEC opens."""
    x, y, w, h = 24, 152, 976, 296
    panel(page, x, y, w, h)
    kicker(page, x + 18, y + 16, "SHENZHEN  •  SUMMIT WEEK")
    cy = headline(page, x + 18, y + 44, w - 36,
                  ["XI AND PUTIN OPEN TALKS", "IN SHENZHEN AS APEC OPENS"],
                  5, INK, gap=2, leading=42)
    draw_centred(page, x, cy + 6, w,
                 "TRILATERAL SUMMIT WITH TRUMP SET FOR TOMORROW, 19 NOV",
                 3, BLUE, gap=1)
    # Visual strip: the two flags left, the Shenzhen skyline right.
    vy = y + 172
    flag_china(page, x + 40, vy, 220, 96)
    draw_centred(page, x + 40, vy + 104, 220, "CHINA", 2, INK, gap=1)
    flag_russia(page, x + 300, vy, 220, 96)
    draw_centred(page, x + 300, vy + 104, 220, "RUSSIA", 2, INK, gap=1)
    skyline(page, x + 580, vy, 356, 96)
    draw_centred(page, x + 580, vy + 104, 356, "APEC  •  SHENZHEN", 2, INK, gap=1)


def draw_manila(page):
    """Manila: Trump arrives for the QUAD summit."""
    x, y, w, h = 24, 464, 476, 232
    panel(page, x, y, w, h)
    kicker(page, x + 16, y + 14, "MANILA  •  QUAD")
    cy = headline(page, x + 16, y + 40, w - 32,
                  ["TRUMP LANDS IN", "MANILA FOR QUAD"], 4, INK, gap=1)
    draw_centred(page, x, cy + 4, w, "QUAD UNVEILS NEW PLAN", 2, INK, gap=1)
    draw_centred(page, x, cy + 24, w, "US  •  JAPAN  •  INDIA  •  AUSTRALIA",
                 2, GREY, gap=1)
    jet(page, x + 168, y + 194, 3)
    page.thick_line(x + 122, y + 208, x + 146, y + 208, GREY, 2)
    page.thick_line(x + 356, y + 208, x + 380, y + 208, GREY, 2)


def draw_gulf(page):
    """The Gulf: Iranian drones target US bases in Kuwait."""
    x, y, w, h = 524, 464, 476, 232
    panel(page, x, y, w, h)
    kicker(page, x + 16, y + 14, "GULF  •  ESCALATION")
    cy = headline(page, x + 16, y + 40, w - 32,
                  ["IRAN DRONES TARGET", "US BASES IN KUWAIT"], 4, INK, gap=1)
    draw_centred(page, x, cy + 4, w, "BAHRAIN INTERCEPTS MORE", 2, INK, gap=1)
    draw_centred(page, x, cy + 24, w, "US CONFIRMS QESHM STRIKE", 2, GREY, gap=1)
    drone(page, x + 120, y + 178, 4)
    radar(page, x + 372, y + 200, 56)


def draw_alaska(page):
    """Alaska: Democrats take the Senate seat."""
    x, y, w, h = 24, 712, 309, 272
    panel(page, x, y, w, h)
    kicker(page, x + 14, y + 14, "ALASKA  •  USA")
    cy = headline(page, x + 14, y + 40, w - 28,
                  ["DEMOCRATS TAKE", "ALASKA SENATE"], 3, INK, gap=1)
    draw_centred(page, x, cy + 4, w, "SEAT", 3, INK, gap=1)
    draw_centred(page, x, cy + 30, w, "PELTOLA BEATS REPUBLICAN", 2, INK, gap=1)
    draw_centred(page, x, cy + 50, w, "DEMOCRATS NOW 56 SEATS", 2, GREY, gap=1)
    ballot_box(page, x + 95, y + 176, 120, 78)


def draw_siberia(page):
    """Siberia: a Russian military plane crashes, all 19 aboard killed."""
    x, y, w, h = 357, 712, 309, 272
    panel(page, x, y, w, h)
    kicker(page, x + 14, y + 14, "SIBERIA  •  RUSSIA")
    cy = headline(page, x + 14, y + 40, w - 28,
                  ["RUSSIAN PLANE", "CRASHES, 19 DEAD"], 3, INK, gap=1)
    draw_centred(page, x, cy + 4, w, "AN-12 DOWN IN KEMEROVO", 2, INK, gap=1)
    draw_centred(page, x, cy + 24, w, "ALL ABOARD KILLED", 2, GREY, gap=1)
    mountains(page, x + 20, y + 168, 269, 88)
    # Nose-down jet diving into the right-hand slope, smoke at impact.
    page.thick_line(x + 218, y + 168, x + 152, y + 228, INK, 5)
    page.thick_line(x + 208, y + 178, x + 224, y + 158, INK, 4)
    page.thick_line(x + 182, y + 200, x + 168, y + 216, INK, 4)
    page.circle(x + 146, y + 222, 6, GREY, fill=True)
    page.circle(x + 134, y + 212, 8, GREY, fill=True)
    page.circle(x + 158, y + 212, 5, GREY, fill=True)


def draw_quake(page):
    """Papua New Guinea: a magnitude 6.0 earthquake strikes."""
    x, y, w, h = 690, 712, 309, 272
    panel(page, x, y, w, h)
    kicker(page, x + 14, y + 14, "PAPUA NEW GUINEA")
    cy = headline(page, x + 14, y + 40, w - 28,
                  ["MAGNITUDE 6.0", "QUAKE STRIKES PNG"], 3, INK, gap=1)
    draw_centred(page, x, cy + 4, w, "DEPTH 10 KM, NEAR LAE", 2, INK, gap=1)
    draw_centred(page, x, cy + 24, w, "MOROBE PROVINCE, PNG", 2, GREY, gap=1)
    seismograph(page, x + 20, y + 168, 269, 88)


def draw_footer(page):
    draw_centred(page, 0, 994, W,
                 "THE WORLD  •  SIX STORIES, ONE DAY  •  18 NOVEMBER 2026",
                 2, GREY, gap=1)


def build():
    page = Page(W, H, PAPER)
    page.rect(8, 8, W - 16, H - 16, INK, 3)
    draw_masthead(page)
    draw_lead(page)
    draw_manila(page)
    draw_gulf(page)
    draw_alaska(page)
    draw_siberia(page)
    draw_quake(page)
    draw_footer(page)
    return page


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
