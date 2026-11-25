#!/usr/bin/env python3
"""news-image-20261124 generator — "Tuesday 24 November 2026" broadsheet.

Renders a 1024x1024 newspaper front page: 36 stories (3 illustrated leads,
10 illustrated cards, 23 briefs), six-number stat strip, UTC timeline
strip, six-segment region bar, dotted world map (navy block, cream dots)
with pins for the 13 pictured stories, and a full-width DATE CHECK box.

Formula (from the ni22 top-3 study + pixel dissection of the leaders):
  * newspaper front page, cream paper, navy + red, kicker
    "THE WORLD IN ONE DAY", huge date headline "Tuesday 24 November 2026";
  * 36 stories, every one dated Tuesday 24 November 2026 (it happened on
    Tuesday where it happened, or was first reported on Tuesday — any
    earlier timing is disclosed in the story body), source named beside
    each story, claim labels REPORTED / CLAIM / FORECAST on every story;
  * the world map is drawn from continent polygons as DOTS, 150 px tall,
    continents recognisable, every pin on land;
  * the strap sits between two rules with clear padding — no rule ever
    touches the strap text;
  * lead banners are 150 px tall, one scene each, with a consistent
    white stat chip top-right and red tag chip top-left;
  * every secondary uses the same chip format: a label, or a label plus
    one number that its headline explains — never a bare unexplained
    number;
  * DATE CHECK is a full-width box ("CHECKED, AND LEFT OUT ON PURPOSE");
  * every region with stories is a segment of the region bar;
  * the "also on" list is black text on the paper, roomy leading.

All artwork is drawn programmatically in this file (flat-vector style);
no photographs, no external assets beyond system fonts.

Usage: python3 generate_ni24.py
  -> output/entry.png (1024) + output/preview-300.png
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ fonts
FONT_DIR = "/usr/share/fonts/truetype/noto"
SERIF_BLACK = f"{FONT_DIR}/NotoSerif-Black.ttf"
SERIF_BOLD = f"{FONT_DIR}/NotoSerif-Bold.ttf"
SERIF = f"{FONT_DIR}/NotoSerif-Regular.ttf"
SERIF_IT = f"{FONT_DIR}/NotoSerif-Italic.ttf"
SANS_BLACK = f"{FONT_DIR}/NotoSans-Black.ttf"
SANS_XB = f"{FONT_DIR}/NotoSans-ExtraBold.ttf"
SANS_BOLD = f"{FONT_DIR}/NotoSans-Bold.ttf"
SANS = f"{FONT_DIR}/NotoSans-Regular.ttf"

_font_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# ------------------------------------------------------------------ palette
PAPER = (248, 243, 228)
INK = (18, 18, 20)
NAVY = (22, 38, 76)
NAVY_DARK = (13, 22, 46)
RED = (178, 24, 32)
RED_DARK = (140, 16, 24)
GREY = (96, 96, 100)
RULE = (40, 40, 44)
CREAM_LINE = (214, 205, 182)
SKY_DAWN = (250, 196, 120)
SKY_DAY = (168, 205, 226)
SEA = (64, 110, 158)

W = H = 1024
M = 26                      # page margin
CW = W - 2 * M              # content width = 972

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img, "RGBA")

WARNINGS = []


# ------------------------------------------------------------------ helpers
def tw(s, f):
    return d.textlength(s, font=f)


def fit(s, path, start, max_w, min_size=7):
    """Largest font (<= start) whose rendering of s fits max_w."""
    size = start
    while size > min_size and tw(s, F(path, size)) > max_w:
        size -= 1
    if tw(s, F(path, size)) > max_w:
        WARNINGS.append(f"fit() could not fit {s!r} in {max_w}px")
    return F(path, size)


def wrap(s, f, max_w):
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(t, f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def text_block(x, y, s, f, max_w, leading, fill=INK, max_lines=None):
    lines = wrap(s, f, max_w)
    if max_lines and len(lines) > max_lines:
        WARNINGS.append(f"text truncated to {max_lines} lines: {s[:40]!r}...")
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        d.text((x, y + i * leading), ln, font=f, fill=fill)
    return y + len(lines) * leading


def centre(s, cx, y, f, fill=INK):
    d.text((cx - tw(s, f) / 2, y), s, font=f, fill=fill)


def chip(x, y, text, bg, fg=(255, 255, 255), font_size=9, pad_x=5, pad_y=2):
    f = F(SANS_BOLD, font_size)
    w_ = tw(text, f) + 2 * pad_x
    h_ = font_size + 2 * pad_y + 2
    d.rectangle([x, y, x + w_, y + h_], fill=bg)
    d.text((x + pad_x, y + pad_y), text, font=f, fill=fg)
    return w_, h_


def rule(x0, x1, y, fill=RULE, width=1):
    d.line([x0, y, x1, y], fill=fill, width=width)


def person(cx, cy, s, colour):
    """Tiny delegate/pedestrian figure: head + shoulders, s = height px."""
    r = s * 0.16
    d.ellipse([cx - r, cy - s, cx + r, cy - s + 2 * r], fill=colour)
    d.pieslice([cx - s * 0.30, cy - s + 2 * r - 2, cx + s * 0.30,
                cy + s * 0.35], 180, 360, fill=colour)


# ------------------------------------------------------------------ content
# Every story below is dated Tuesday 24 November 2026 (it happened on
# Tuesday where it happened, or was first reported / confirmed on Tuesday)
# and carries its source on the page. Labels: REPORTED = confirmed by the
# outlet named · CLAIM = one side's claim, unverified · FORECAST =
# scheduled, has not happened yet. See STORIES.md for the audit.

STRAP = ("Nikkei closes 58,675.80, up 3.97% · Russian jets enter "
         "Korea's air zone · China to fly first foreign astronaut")

STATS = [
    ("58,675.80", "NIKKEI 225 CLOSE, TOKYO"),
    ("+3.97%", "NIKKEI SURGE, AI TRADE BACK"),
    ("07:52", "KST ULLEUNG SHELTER ALERT"),
    ("00:18", "UTC WED: SHENZHOU-24 LAUNCH"),
    ("M5.3", "NEPAL QUAKE, KOSHI PROVINCE"),
    ("353–128", "BRAZIL VOTE, LULA FISCAL PLAN"),
]

# (name, count, colour) — counts are the true tally of the 36 stories.
# No Tuesday story is set in Oceania, so the bar has six segments.
REGIONS = [
    ("AMERICAS", 5, (104, 62, 140)),
    ("EUROPE", 8, (38, 84, 150)),
    ("ASIA-PACIFIC", 19, (44, 128, 74)),
    ("MIDDLE EAST", 1, (178, 24, 32)),
    ("AFRICA", 1, (196, 116, 30)),
    ("WORLD", 2, (13, 22, 46)),
]

UTC_STRIP = [
    ("00:01", "Met: 266 arrests"),
    ("01:32", "Nepal quake M5.3"),
    ("06:30", "Nikkei +3.97%"),
    ("09:30", "Bangkok fuel march"),
    ("14:53", "Supermoon peaks"),
    ("17:45", "Champions League"),
]

LEADS = [
    {
        "tag": "NIKKEI: +3.97%", "stat": "58,675.80",
        "kicker": "MARKETS · TOKYO", "label": "REPORTED",
        "headline": "Tokyo roars back as the AI trade returns",
        "body": ("The Nikkei 225 closes at 58,675.80 as Tokyo reopens "
                 "after the holiday, recouping most of Friday's rout. "
                 "Chip stocks lead: Advantest +15%, Tokyo Electron "
                 "+12%, SoftBank +8%."),
        "source": "NIKKEI / AP · TOKYO",
        "scene": "nikkei",
    },
    {
        "tag": "KADIZ: SCRAMBLE", "stat": "07:52 KST",
        "kicker": "AIR ZONE · EAST SEA", "label": "REPORTED",
        "headline": "Russian jets buzz Korea's air zone; Seoul scrambles",
        "body": ("Russian aircraft enter the KADIZ over the East Sea "
                 "and near Ulleung Island; fighters scramble and "
                 "islanders shelter at 07:52 KST. No airspace "
                 "violation, Seoul clarifies."),
        "source": "REUTERS / YONHAP · SEOUL",
        "scene": "kadiz",
    },
    {
        "tag": "SHENZHOU-24", "stat": "00:18 UTC",
        "kicker": "SPACE · JIUQUAN", "label": "REPORTED + FORECAST",
        "headline": "China to fly its first foreign astronaut",
        "body": ("China announces Shenzhou-24 launches Wednesday "
                 "00:18 UTC with a Pakistani aboard — the first "
                 "foreign astronaut to Tiangong. The launch is a "
                 "forecast; the announcement is Tuesday's."),
        "source": "REUTERS · JIUQUAN",
        "scene": "shenzhou",
    },
]

# Cards: (num, tag, stat, kicker place, label, headline, body, source, scene)
CARDS = [
    (4, "NEPAL", "M5.3", "KATHMANDU", "REPORTED",
     "Nepal shaken by a 5.3 quake",
     "M5.3 in Koshi province, 01:32 UTC; tremors felt in north Bengal, "
     "no casualties.",
     "REUTERS / EMSC", "quake"),
    (5, "DHAKA", "16 DEC", "DHAKA", "REPORTED",
     "Hasina plans her return home",
     "Ousted PM to return from exile in India on 16 December, her "
     "spokesperson says.",
     "REUTERS", "plane"),
    (6, "INDIA–NEPAL", "$1.6BN", "NEW DELHI", "REPORTED",
     "India pledges $1.6bn to Nepal",
     "Flood relief pledged as Shah visits Modi; new cross-border "
     "train flagged off.",
     "AL JAZEERA / REUTERS", "train"),
    (7, "LIBYA", "CONDEMNED", "TRIPOLI", "REPORTED",
     "Libya condemns Kyiv's port strike",
     "Tripoli calls Ukraine's Benghazi drone strike a violation of "
     "Libyan sovereignty.",
     "THE GUARDIAN", "tanker"),
    (8, "CHIP STOCKS", "+3% STAR 50", "SHANGHAI", "REPORTED",
     "China chip stocks join AI rally",
     "STAR 50 opens +3%; TSMC +9.85% and Foxconn +9.95% ride the "
     "global AI rebound.",
     "MARKET TAPE", "chip"),
    (9, "CHESS", "GAME 1", "GENEVA", "FORECAST",
     "Gukesh begins his title defence",
     "Youngest title match ever: Gukesh, 20, v Sindarov, 20 — Game 1 "
     "from 15:00 CET.",
     "FIDE / CHESSBASE", "chess"),
    (10, "BRAZIL", "353–128", "BRASÍLIA", "REPORTED",
     "Brazil's lower house backs Lula's fiscal plan",
     "Approved 353–128 in a late-night vote; spending growth capped "
     "at 2%.",
     "THE BRIEFBRIEF", "congress"),
    (11, "SINGAPORE", "NO CONDUIT", "SINGAPORE", "REPORTED",
     "Singapore: no conduit for chip smuggling, PM says",
     "PM Wong says Singapore won't help evade US export controls; "
     "Megaspeed probed.",
     "MARKET TAPE", "skyline"),
    (12, "PACIFIC", "GOES ALONE", "SUVA", "REPORTED",
     "Pacific goes it alone after COP31 collapses",
     "Island nations will form their own climate coalitions after "
     "COP31's collapse.",
     "PINA", "island"),
    (13, "VANUATU PACT", "$500M", "CANBERRA", "REPORTED",
     "Australia's Vanuatu deal stalls on climate",
     "Coalition refuses to back the $500m Nakamal pact over binding "
     "climate clauses.",
     "PINA / AAP", "parliament"),
]

# Briefs: (num, text, source, label-or-None) — REPORTED unless tagged.
BRIEFS = [
    (14, "India holds 3rd in Asia Power Index", "Lowy", None),
    (15, "Kyiv drone-debris fire, 3 hurt", "Kyiv Independent", None),
    (16, "Walk-off FG: Commanders 22–20", "NBC", None),
    (17, "Both-coasts Thanksgiving storm", "NWS", "FORECAST"),
    (18, "Bitcoin $61,000; gold at $3,628", "Finnhub / KuCoin", None),
    (19, "Bucks end 13-game skid, 116–111", "TSN", None),
    (20, "Lisbon unions rally again", "Euronews", "FORECAST"),
    (21, "Solomons PM flies to Canberra", "PINA", "FORECAST"),
    (22, "Fiji schools shut 5 days from 30 Nov", "PINA", None),
    (23, "Kanton Island evacuated, a day's notice", "PINA", None),
    (24, "Saryu-Kamala Express flagged off", "Jagran Josh", None),
    (25, "Seoul to summon Russian attaché", "Reuters / AJP", None),
    (26, "Supermoon peaks 14:53 UTC", "NASA", "FORECAST"),
    (27, "Arsenal–Dortmund, City–Napoli", "UEFA", "FORECAST"),
    (28, "UK destitution hits record 3.8m", "Sky News / JRF", None),
    (29, "Polanski backs NATO, nuclear arms", "The Guardian", None),
    (30, "Met: 266 arrests, 500 knives seized", "Met Police", None),
    (31, "Abusers could lose their house keys", "LBC", None),
    (32, "Bangkok fuel march: 250 walk 16 km", "The Nation", None),
    (33, "NBA: Rockets 116–104 Clippers", "Sportradar / NBA", None),
    (34, "Gaza strike kills 3 near Khan Younis", "Reuters", None),
    (35, "Murmu opens Bali Jatra in Cuttack", "Utkal Post", None),
    (36, "SCO: Pakistan to invite India", "Times of India", None),
]

DATE_CHECK = (
    "Not Tuesday's news: Kyiv bridges barrage (Fri 20 Nov) · Kyiv-region "
    "strikes kill 15 (Sun–Mon) · COP31 ends with no deal (Sun) · NATO "
    "session over Poland (Mon) · Nvidia reinstates Huang (Mon) · EU's "
    "22nd sanctions package (Mon) · FIFA names World Cup hosts (Mon) · "
    "Hormuz tankers mined (Mon) · GTA 6 sales estimate (Mon) · Sparta II "
    "strike (Sat) · Stacy Keach dies (10 Nov)."
)

FOOTER = ("Every story here happened, or was first reported, on Tuesday "
          "24 November 2026. Claims are labelled as claimed; briefs are "
          "REPORTED unless tagged. Pictures and map: original, drawn in code.")


# ------------------------------------------------------------------ scenes
def scene_cop31(x, y, w, h):
    """Dawn sky, sun rising, long conference table with delegates —
    and an empty chair where the deal should be."""
    for i in range(h):
        t = i / h
        c = tuple(int(SKY_DAWN[j] * (1 - t) + SKY_DAY[j] * t) for j in range(3))
        d.line([x, y + i, x + w, y + i], fill=c)
    # sun low on the horizon, right of centre
    sx, sy, sr = x + w * 0.66, y + h * 0.52, h * 0.30
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 214, 90))
    d.ellipse([sx - sr * 0.72, sy - sr * 0.72, sx + sr * 0.72, sy + sr * 0.72],
              fill=(255, 228, 130))
    # distant headland + sea band
    d.polygon([(x, y + h * 0.62), (x + w * 0.2, y + h * 0.52),
               (x + w * 0.42, y + h * 0.62), (x + w, y + h * 0.62)],
              fill=(110, 130, 140))
    d.rectangle([x, y + h * 0.62, x + w, y + h * 0.70], fill=SEA)
    # conference table (perspective slab) and delegates
    ty = y + h * 0.82
    d.polygon([(x + w * 0.06, ty), (x + w * 0.94, ty),
               (x + w * 0.88, y + h), (x + w * 0.12, y + h)],
              fill=(96, 62, 34))
    d.rectangle([x + w * 0.06, ty - 3, x + w * 0.94, ty], fill=(70, 44, 22))
    cols = [(178, 24, 32), (22, 38, 76), (44, 128, 74), (196, 116, 30),
            (104, 62, 140), (30, 128, 128), (150, 60, 90), (70, 90, 160),
            (120, 120, 40), (160, 90, 40), (60, 130, 110)]
    for i, c in enumerate(cols):
        fx = x + w * (0.12 + 0.065 * i)
        person(fx, ty - 2, h * 0.34, c)
    # one empty chair at the head of the table — the missing deal
    ex = x + w * 0.88
    d.rectangle([ex - 7, ty - 26, ex + 7, ty - 2], outline=(60, 40, 24),
                width=2)
    d.line([ex - 7, ty - 14, ex + 7, ty - 14], fill=(60, 40, 24), width=2)
    # torn paper sheet on the table — the rejected text
    d.polygon([(x + w * 0.44, ty + 4), (x + w * 0.56, ty + 4),
               (x + w * 0.545, y + h - 4), (x + w * 0.455, y + h - 4)],
              fill=(252, 250, 240))
    d.line([x + w * 0.50, ty + 6, x + w * 0.50, y + h - 6],
           fill=(178, 24, 32), width=2)
    for k in range(3):
        ly = ty + 9 + k * 6
        d.line([x + w * 0.465, ly, x + w * 0.535, ly], fill=(150, 150, 150),
               width=1)


def scene_nato(x, y, w, h):
    """NATO council chamber: blue wall, compass-star emblem, long table
    with member flags and delegates, wall map with three red markers."""
    d.rectangle([x, y, x + w, y + h], fill=(28, 52, 96))
    # compass star emblem, centre-top: white circle, four-point star
    cx, cy, r = x + w * 0.50, y + h * 0.30, h * 0.24
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255),
              width=3)
    d.polygon([(cx, cy - r * 0.95), (cx + r * 0.16, cy - r * 0.16),
               (cx + r * 0.95, cy), (cx + r * 0.16, cy + r * 0.16),
               (cx, cy + r * 0.95), (cx - r * 0.16, cy + r * 0.16),
               (cx - r * 0.95, cy), (cx - r * 0.16, cy - r * 0.16)],
              fill=(255, 255, 255))
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(28, 52, 96))
    # wall map strip, left: simplified Poland outline with 3 red markers
    mx, my, mw, mh = x + w * 0.05, y + h * 0.10, w * 0.20, h * 0.34
    d.rectangle([mx, my, mx + mw, my + mh], fill=(16, 30, 62),
                outline=(120, 140, 180))
    d.polygon([(mx + 4, my + mh * 0.30), (mx + mw * 0.30, my + 4),
               (mx + mw - 4, my + mh * 0.25), (mx + mw * 0.85, my + mh * 0.55),
               (mx + mw * 0.60, my + mh - 4), (mx + mw * 0.25, my + mh * 0.80),
               (mx + 4, my + mh * 0.60)], fill=(70, 100, 140))
    for (px, py) in [(0.30, 0.35), (0.62, 0.55), (0.78, 0.30)]:
        d.ellipse([mx + mw * px - 3, my + mh * py - 3,
                   mx + mw * px + 3, my + mh * py + 3], fill=RED,
                  outline=(255, 255, 255))
    # long council table + flags + delegates
    ty = y + h * 0.78
    d.polygon([(x + w * 0.04, ty), (x + w * 0.96, ty),
               (x + w * 0.90, y + h), (x + w * 0.10, y + h)],
              fill=(84, 56, 32))
    d.rectangle([x + w * 0.04, ty - 3, x + w * 0.96, ty], fill=(58, 38, 20))
    flag_cols = [(178, 24, 32), (255, 255, 255), (22, 38, 76),
                 (44, 128, 74), (196, 116, 30), (104, 62, 140),
                 (30, 128, 128), (150, 60, 90), (70, 90, 160),
                 (120, 120, 40)]
    for i, c in enumerate(flag_cols):
        fx = x + w * (0.10 + 0.085 * i)
        d.rectangle([fx, ty - 16, fx + 12, ty - 6], fill=c,
                    outline=(200, 200, 200))
        d.line([fx + 2, ty - 16, fx + 2, ty - 2], fill=(200, 200, 200),
               width=1)
    cols = [(220, 220, 220), (200, 200, 210), (210, 210, 200),
            (230, 225, 215), (205, 205, 205)]
    for i, c in enumerate(cols):
        fx = x + w * (0.16 + 0.17 * i)
        person(fx, ty - 2, h * 0.30, c)


def scene_libya(x, y, w, h):
    """Night harbour at Benghazi: warship ablaze, drone boats closing in."""
    d.rectangle([x, y, x + w, y + h], fill=(14, 18, 40))
    # stars + moon
    for i in range(40):
        px = x + (i * 71) % int(w)
        py = y + (i * 41) % int(h * 0.45)
        d.point((px, py), fill=(220, 224, 240))
    d.ellipse([x + w * 0.86, y + h * 0.08, x + w * 0.93, y + h * 0.08 + w * 0.07],
              fill=(232, 232, 210))
    # sea with moonlight band
    d.rectangle([x, y + h * 0.66, x + w, y + h], fill=(24, 48, 84))
    d.rectangle([x + w * 0.80, y + h * 0.66, x + w * 0.96, y + h],
                fill=(60, 90, 130))
    # warship (Merkury) centre-right, listing, on fire
    sx = x + w * 0.52
    sy = y + h * 0.62
    d.polygon([(sx, sy), (sx + w * 0.34, sy), (sx + w * 0.30, sy + h * 0.10),
               (sx + w * 0.04, sy + h * 0.10)], fill=(52, 58, 66))
    d.rectangle([sx + w * 0.10, sy - h * 0.16, sx + w * 0.20, sy],
                fill=(70, 76, 84))
    d.rectangle([sx + w * 0.22, sy - h * 0.10, sx + w * 0.26, sy],
                fill=(70, 76, 84))
    d.line([sx + w * 0.15, sy - h * 0.16, sx + w * 0.15, sy - h * 0.26],
           fill=(90, 96, 104), width=2)
    # fireball + smoke over the ship
    fx, fy = sx + w * 0.16, sy - h * 0.22
    d.ellipse([fx - 16, fy - 12, fx + 16, fy + 12], fill=(255, 170, 50))
    d.ellipse([fx - 9, fy - 7, fx + 9, fy + 7], fill=(255, 220, 120))
    d.polygon([(fx - 10, fy - 8), (fx, fy - 26), (fx + 10, fy - 8)],
              fill=(240, 110, 36))
    for (ox, oy, orr) in [(0.10, 0.18, 10), (0.20, 0.12, 14), (0.28, 0.08, 18)]:
        d.ellipse([x + w * ox - orr, y + h * oy - orr * 0.6,
                   x + w * ox + orr, y + h * oy + orr * 0.6],
                  fill=(70, 64, 70, 170))
    # sea drones closing in from the left, with wakes
    for (dx, dy, s) in [(0.08, 0.74, 1.0), (0.20, 0.82, 0.8), (0.30, 0.70, 0.9)]:
        bx, by = x + w * dx, y + h * dy
        d.line([bx - 34 * s, by + 6, bx, by], fill=(200, 220, 240), width=2)
        d.polygon([(bx, by - 4), (bx + 18 * s, by), (bx, by + 4)],
                  fill=(16, 16, 20))
        d.ellipse([bx + 14 * s - 2, by - 2, bx + 14 * s + 2, by + 2],
                  fill=(255, 90, 60))


def scene_nikkei(x, y, w, h):
    """Tokyo at dawn: skyline silhouette, the Skytree, and a rising
    candlestick chart across the foreground — the market roaring back."""
    for i in range(h):
        t = i / h
        c = tuple(int(SKY_DAWN[j] * (1 - t) + SKY_DAY[j] * t) for j in range(3))
        d.line([x, y + i, x + w, y + i], fill=c)
    # sun disc, left of centre
    sx, sy, sr = x + w * 0.30, y + h * 0.40, h * 0.20
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 214, 90))
    d.ellipse([sx - sr * 0.7, sy - sr * 0.7, sx + sr * 0.7, sy + sr * 0.7],
              fill=(255, 228, 130))
    # skyline blocks along the bottom, with lit windows
    base = y + h * 0.86
    blocks = [(0.00, 0.30), (0.09, 0.44), (0.18, 0.26), (0.26, 0.50),
              (0.36, 0.34), (0.44, 0.42), (0.54, 0.28), (0.62, 0.46),
              (0.72, 0.32), (0.80, 0.40), (0.90, 0.30)]
    for bx, bh in blocks:
        bw = w * 0.075
        d.rectangle([x + w * bx, base - h * bh, x + w * bx + bw, base],
                    fill=NAVY_DARK)
        for r in range(3):
            for cidx in range(2):
                if (int(bx * 100) + r + cidx) % 2 == 0:
                    d.rectangle([x + w * bx + 4 + cidx * 9,
                                 base - h * bh + 5 + r * 9,
                                 x + w * bx + 7 + cidx * 9,
                                 base - h * bh + 8 + r * 9],
                                fill=(255, 214, 90))
    # the Skytree: tapered tower with antenna, right of centre
    tx = x + w * 0.585
    d.polygon([(tx - 7, base), (tx - 2, y + h * 0.16),
               (tx + 2, y + h * 0.16), (tx + 7, base)], fill=NAVY_DARK)
    d.line([tx, y + h * 0.16, tx, y + h * 0.05], fill=NAVY_DARK, width=2)
    d.ellipse([tx - 5, y + h * 0.30, tx + 5, y + h * 0.30 + 6],
              fill=NAVY_DARK)
    # candlestick chart climbing across the foreground
    candles = [(0.06, 0.66, 0.80, (178, 24, 32)),
               (0.16, 0.62, 0.74, (178, 24, 32)),
               (0.26, 0.54, 0.68, (44, 128, 74)),
               (0.36, 0.47, 0.60, (44, 128, 74)),
               (0.46, 0.40, 0.52, (44, 128, 74)),
               (0.56, 0.33, 0.45, (44, 128, 74)),
               (0.66, 0.27, 0.38, (44, 128, 74)),
               (0.76, 0.20, 0.31, (44, 128, 74)),
               (0.86, 0.13, 0.24, (44, 128, 74))]
    for cx0, top, bot, col in candles:
        cx = x + w * cx0
        d.line([cx + 6, y + h * (top - 0.04), cx + 6, y + h * (bot + 0.04)],
               fill=col, width=2)
        d.rectangle([cx, y + h * top, cx + 12, y + h * bot], fill=col)
    d.line([x + w * 0.05, y + h * 0.72, x + w * 0.93, y + h * 0.12],
           fill=(255, 255, 255), width=3)
    d.polygon([(x + w * 0.93, y + h * 0.12), (x + w * 0.86, y + h * 0.11),
               (x + w * 0.92, y + h * 0.20)], fill=(255, 255, 255))
    d.rectangle([x, base, x + w, y + h], fill=NAVY_DARK)


def scene_kadiz(x, y, w, h):
    """East Sea morning: two jets with contrails over the sea, Ulleung
    Island below, a dashed red alert ring around the island."""
    for i in range(h):
        t = i / h
        top = (196, 222, 238) if i < h * 0.62 else SEA
        c = tuple(int(SKY_DAY[j] * (1 - t) + top[j] * t) for j in range(3))
        d.line([x, y + i, x + w, y + i], fill=c)
    d.rectangle([x, y + h * 0.62, x + w, y + h], fill=SEA)
    for k in range(5):
        wy = y + h * (0.70 + 0.06 * k)
        d.line([x + w * (0.04 + 0.07 * k), wy, x + w * (0.20 + 0.07 * k), wy],
               fill=(200, 220, 240), width=1)
    # Ulleung Island: steep green cone on a rocky base, right of centre
    ix, iy = x + w * 0.68, y + h * 0.64
    d.polygon([(ix - w * 0.17, iy + h * 0.10), (ix - w * 0.05, iy - h * 0.20),
               (ix + w * 0.03, iy - h * 0.24), (ix + w * 0.13, iy + h * 0.10)],
              fill=(44, 96, 60))
    d.polygon([(ix - w * 0.17, iy + h * 0.10), (ix + w * 0.13, iy + h * 0.10),
               (ix + w * 0.09, iy + h * 0.17), (ix - w * 0.12, iy + h * 0.17)],
              fill=(90, 86, 80))
    # dashed red alert ring around the island
    import math as _m
    for a0 in range(0, 360, 18):
        a1 = _m.radians(a0)
        a2 = _m.radians(a0 + 9)
        d.line([ix + 62 * _m.cos(a1), iy + 34 * _m.sin(a1),
                ix + 62 * _m.cos(a2), iy + 34 * _m.sin(a2)],
               fill=RED, width=2)
    # two jets, upper left and centre, with contrails
    for (jx, jy, s) in [(0.16, 0.20, 1.0), (0.42, 0.32, 0.8)]:
        bx, by = x + w * jx, y + h * jy
        d.line([bx - 74 * s, by + 7 * s, bx - 8 * s, by + 1 * s],
               fill=(255, 255, 255), width=3)
        d.line([bx - 70 * s, by + 12 * s, bx - 8 * s, by + 5 * s],
               fill=(255, 255, 255), width=2)
        d.polygon([(bx, by), (bx + 30 * s, by + 5 * s), (bx + 40 * s, by + 9 * s),
                   (bx + 28 * s, by + 11 * s), (bx + 8 * s, by + 9 * s),
                   (bx - 4 * s, by + 13 * s), (bx - 2 * s, by + 5 * s)],
                  fill=(40, 46, 58))
        d.polygon([(bx + 12 * s, by + 2 * s), (bx + 4 * s, by - 8 * s),
                   (bx + 18 * s, by + 1 * s)], fill=(40, 46, 58))
    # alert triangle, right sky (clear of the stat chip and the ring)
    tx, ty, ts = x + w * 0.865, y + h * 0.34, 15
    d.polygon([(tx, ty), (tx + ts, ty + ts * 0.92), (tx - ts, ty + ts * 0.92)],
              fill=(255, 196, 0), outline=(20, 20, 20))
    d.rectangle([tx - 1.5, ty + 6, tx + 1.5, ty + 12], fill=(20, 20, 20))
    d.ellipse([tx - 1.5, ty + 13, tx + 1.5, ty + 16], fill=(20, 20, 20))


def scene_shenzhou(x, y, w, h):
    """Jiuquan at dawn: a Long March rocket on the pad between its
    service tower and a low sun; China and Pakistan flags on the body;
    the Tiangong station a small silhouette in the brightening sky."""
    for i in range(h):
        t = i / h
        c = tuple(int(SKY_DAWN[j] * (1 - t) + SKY_DAY[j] * t) for j in range(3))
        d.line([x, y + i, x + w, y + i], fill=c)
    for i in range(16):
        d.point((x + (i * 67) % int(w), y + (i * 23) % int(h * 0.3)),
                fill=(255, 255, 255))
    sx, sy, sr = x + w * 0.86, y + h * 0.34, h * 0.16
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 214, 90))
    # Tiangong silhouette, mid-left sky (below the tag chip):
    # core module + two panels
    gx, gy = x + w * 0.10, y + h * 0.34
    d.rectangle([gx, gy, gx + 30, gy + 9], fill=NAVY_DARK)
    d.polygon([(gx - 24, gy + 1), (gx, gy + 1), (gx, gy + 8),
               (gx - 24, gy + 8)], fill=(38, 84, 150))
    d.polygon([(gx + 30, gy + 1), (gx + 54, gy + 1), (gx + 54, gy + 8),
               (gx + 30, gy + 8)], fill=(38, 84, 150))
    d.rectangle([gx + 12, gy - 6, gx + 18, gy], fill=NAVY_DARK)
    # ground + pad
    d.rectangle([x, y + h * 0.86, x + w, y + h], fill=(168, 138, 96))
    d.rectangle([x + w * 0.30, y + h * 0.84, x + w * 0.62, y + h * 0.88],
                fill=(110, 104, 98))
    # service tower, right of the rocket
    tx = x + w * 0.545
    d.rectangle([tx, y + h * 0.18, tx + 10, y + h * 0.86], fill=(96, 100, 108))
    for k in range(5):
        d.line([tx, y + h * (0.26 + 0.12 * k), tx + 10,
                y + h * (0.26 + 0.12 * k)], fill=(70, 74, 82), width=2)
    d.line([tx, y + h * 0.30, x + w * 0.475, y + h * 0.30],
           fill=(96, 100, 108), width=3)
    # the rocket: boosters, core, fairing, escape tower
    rx = x + w * 0.44
    for bx in (rx - 13, rx + 7):
        d.rectangle([bx, y + h * 0.52, bx + 6, y + h * 0.84],
                    fill=(232, 230, 224), outline=(150, 148, 140))
        d.polygon([(bx, y + h * 0.52), (bx + 3, y + h * 0.46),
                   (bx + 6, y + h * 0.52)], fill=(232, 230, 224))
    d.rectangle([rx - 6, y + h * 0.34, rx + 6, y + h * 0.84],
                fill=(246, 244, 238), outline=(150, 148, 140))
    d.polygon([(rx - 6, y + h * 0.34), (rx, y + h * 0.22),
               (rx + 6, y + h * 0.34)], fill=(246, 244, 238))
    d.line([rx, y + h * 0.22, rx, y + h * 0.13], fill=(90, 90, 96), width=2)
    # flags on the core: China (red) above Pakistan (green)
    d.rectangle([rx - 4, y + h * 0.42, rx + 4, y + h * 0.47],
                fill=(178, 24, 32))
    d.ellipse([rx - 2.5, y + h * 0.435, rx + 0.5, y + h * 0.435 + 3],
              fill=(255, 214, 90))
    d.rectangle([rx - 4, y + h * 0.50, rx + 4, y + h * 0.55],
                fill=(20, 110, 50))
    d.rectangle([rx - 4, y + h * 0.50, rx - 2, y + h * 0.55],
                fill=(246, 244, 238))
    # vapour puffs at the base
    for (ox, oy, orr) in [(0.40, 0.84, 12), (0.47, 0.86, 15),
                          (0.36, 0.87, 9), (0.52, 0.85, 10)]:
        d.ellipse([x + w * ox - orr, y + h * oy - orr * 0.55,
                   x + w * ox + orr, y + h * oy + orr * 0.55],
                  fill=(250, 248, 242, 200))


LEAD_SCENES = {"cop31": scene_cop31, "nato": scene_nato,
               "libya": scene_libya, "nikkei": scene_nikkei,
               "kadiz": scene_kadiz, "shenzhou": scene_shenzhou}


# ------------------------------------------------------- card mini-scenes
def mini_tanker(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(24, 34, 62))
    d.rectangle([x, y + h * 0.66, x + w, y + h], fill=SEA)
    hx = x + w * 0.12
    d.polygon([(hx, y + h * 0.60), (hx + w * 0.66, y + h * 0.60),
               (hx + w * 0.56, y + h * 0.78), (hx + w * 0.06, y + h * 0.78)],
              fill=(30, 30, 34))
    d.rectangle([hx + w * 0.08, y + h * 0.42, hx + w * 0.30, y + h * 0.60],
                fill=(150, 60, 50))
    d.rectangle([hx + w * 0.34, y + h * 0.48, hx + w * 0.52, y + h * 0.60],
                fill=(60, 90, 140))
    for fx in (0.50, 0.60):
        gx = hx + w * fx
        d.polygon([(gx - 6, y + h * 0.44), (gx, y + h * 0.20),
                   (gx + 6, y + h * 0.44)], fill=(240, 110, 36))
        d.polygon([(gx - 3, y + h * 0.44), (gx, y + h * 0.30),
                   (gx + 3, y + h * 0.44)], fill=(255, 190, 80))
    d.ellipse([x + w * 0.82, y + h * 0.12, x + w * 0.82 + 12,
               y + h * 0.12 + 12], fill=(255, 214, 90))


def mini_gaza(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(196, 178, 140))
    # rubble skyline: broken blocks, tilted slabs
    d.rectangle([x, y + h * 0.78, x + w, y + h], fill=(140, 124, 96))
    for (bx, bw, bh, tilt) in [(0.04, 0.20, 0.44, 0), (0.28, 0.16, 0.60, 1),
                               (0.48, 0.22, 0.36, 0), (0.72, 0.20, 0.52, 1)]:
        if tilt:
            d.polygon([(x + w * bx, y + h * 0.78),
                       (x + w * (bx + bw), y + h * 0.78 - h * 0.10),
                       (x + w * (bx + bw), y + h * 0.78),
                       (x + w * bx, y + h * 0.78)], fill=(110, 96, 74))
        d.rectangle([x + w * bx, y + h * (0.78 - bh), x + w * (bx + bw),
                     y + h * 0.78], fill=(126, 112, 88))
        for r in range(2):
            for cidx in range(2):
                d.rectangle([x + w * (bx + 0.03 + 0.07 * cidx),
                             y + h * (0.78 - bh + 0.08 + 0.14 * r),
                             x + w * (bx + 0.07 + 0.07 * cidx),
                             y + h * (0.78 - bh + 0.14 + 0.14 * r)],
                            fill=(60, 54, 46))
    # hazard triangle with exclamation, centre-right
    tx, ty, ts = x + w * 0.66, y + h * 0.12, 26
    d.polygon([(tx, ty), (tx + ts, ty + ts * 0.9), (tx - ts, ty + ts * 0.9)],
              fill=(255, 196, 0), outline=(20, 20, 20))
    d.rectangle([tx - 2, ty + 8, tx + 2, ty + 18], fill=(20, 20, 20))
    d.ellipse([tx - 2, ty + 20, tx + 2, ty + 24], fill=(20, 20, 20))


def mini_cikande(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(70, 62, 66))
    # factory block + chimney
    d.rectangle([x + w * 0.08, y + h * 0.42, x + w * 0.62, y + h * 0.86],
                fill=(52, 50, 56))
    d.polygon([(x + w * 0.08, y + h * 0.42), (x + w * 0.22, y + h * 0.30),
               (x + w * 0.36, y + h * 0.42), (x + w * 0.50, y + h * 0.30),
               (x + w * 0.62, y + h * 0.42)], fill=(40, 38, 44))
    d.rectangle([x + w * 0.70, y + h * 0.18, x + w * 0.78, y + h * 0.86],
                fill=(46, 44, 50))
    for r in range(2):
        for cidx in range(4):
            d.rectangle([x + w * (0.13 + 0.11 * cidx), y + h * (0.52 + 0.16 * r),
                         x + w * (0.19 + 0.11 * cidx),
                         y + h * (0.62 + 0.16 * r)], fill=(250, 196, 92))
    # flames along the roofline
    for fx in (0.16, 0.30, 0.44, 0.56):
        gx = x + w * fx
        d.polygon([(gx - 7, y + h * 0.34), (gx, y + h * 0.12),
                   (gx + 7, y + h * 0.34)], fill=(240, 110, 36))
        d.polygon([(gx - 3.5, y + h * 0.34), (gx, y + h * 0.22),
                   (gx + 3.5, y + h * 0.34)], fill=(255, 190, 80))
    # smoke
    for (sx, sy, sr) in [(0.70, 0.10, 9), (0.80, 0.06, 12)]:
        d.ellipse([x + w * sx - sr, y + h * sy - sr * 0.55,
                   x + w * sx + sr, y + h * sy + sr * 0.55],
                  fill=(96, 90, 96, 170))
    d.rectangle([x, y + h * 0.86, x + w, y + h], fill=(30, 28, 32))


def mini_grok(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(36, 40, 58))
    # smartphone with a photo silhouette, left
    px, py, pw, ph = x + w * 0.10, y + h * 0.14, w * 0.34, h * 0.72
    # int() the box: rounded_rectangle computes y0+width-1 in floats,
    # and 7.000000000000001+1-1 rounds DOWN to 7.0 < y0 -> ValueError
    d.rounded_rectangle([int(px), int(py), int(px + pw), int(py + ph)],
                        radius=6, fill=(16, 16, 20),
                        outline=(120, 124, 140))
    d.rectangle([px + 4, py + 8, px + pw - 4, py + ph - 8], fill=(168, 205, 226))
    d.ellipse([px + pw * 0.32, py + ph * 0.16, px + pw * 0.68,
               py + ph * 0.16 + pw * 0.36], fill=(240, 200, 170))
    d.pieslice([px + pw * 0.14, py + ph * 0.44, px + pw * 0.86,
                py + ph * 0.98], 180, 360, fill=(90, 60, 120))
    # red prohibition ring over the phone — small, inside the banner
    cx, cy, r = px + pw * 0.5, py + ph * 0.5, 16
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED, width=4)
    d.line([cx - r * 0.7, cy + r * 0.7, cx + r * 0.7, cy - r * 0.7],
           fill=RED, width=4)
    # gavel, right
    gx, gy = x + w * 0.62, y + h * 0.30
    d.rectangle([gx, gy, gx + w * 0.28, gy + 10], fill=(120, 84, 40))
    d.rectangle([gx + w * 0.06, gy - 6, gx + w * 0.22, gy - 2],
                fill=(150, 108, 54))
    d.line([gx + w * 0.14, gy + 10, gx + w * 0.10, gy + h * 0.34],
           fill=(120, 84, 40), width=4)
    d.rectangle([x + w * 0.58, y + h * 0.68, x + w * 0.92, y + h * 0.74],
                fill=(150, 108, 54))


def mini_satellite(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(8, 8, 18))
    for i in range(28):
        d.point((x + (i * 53) % int(w), y + (i * 29) % int(h)),
                fill=(225, 228, 240))
    # Earth arc along the bottom
    d.ellipse([x - w * 0.3, y + h * 0.78, x + w * 1.3, y + h * 1.7],
              fill=(44, 96, 160))
    d.ellipse([x + w * 0.18, y + h * 0.86, x + w * 0.44, y + h * 1.1],
              fill=(44, 128, 74))
    d.ellipse([x + w * 0.62, y + h * 0.90, x + w * 0.80, y + h * 1.06],
              fill=(44, 128, 74))
    # satellite body + panels, upper right
    sx, sy = x + w * 0.56, y + h * 0.22
    d.rectangle([sx, sy, sx + 34, sy + 20], fill=(210, 214, 220))
    d.polygon([(sx - 30, sy + 2), (sx, sy + 2), (sx, sy + 18),
               (sx - 30, sy + 18)], fill=(44, 68, 140))
    d.polygon([(sx + 34, sy + 2), (sx + 64, sy + 2), (sx + 64, sy + 18),
               (sx + 34, sy + 18)], fill=(44, 68, 140))
    for k in range(3):
        d.line([sx - 24 + k * 10, sy + 3, sx - 24 + k * 10, sy + 17],
               fill=(90, 120, 190), width=1)
        d.line([sx + 40 + k * 10, sy + 3, sx + 40 + k * 10, sy + 17],
               fill=(90, 120, 190), width=1)
    d.line([sx + 17, sy + 20, sx + 17, sy + 30], fill=(200, 200, 210),
           width=2)
    # radiation trefoil, left
    rx, ry, rr = x + w * 0.24, y + h * 0.34, 13
    d.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], fill=(255, 206, 60))
    for a in (90, 210, 330):
        d.pieslice([rx - rr - 5, ry - rr - 5, rx + rr + 5, ry + rr + 5],
                   a - 28, a + 28, fill=(255, 206, 60))
    d.ellipse([rx - 3, ry - 3, rx + 3, ry + 3], fill=(8, 8, 18))


def mini_denmark(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(0, 32, 91))
    # circle of EU stars
    cx, cy, r = x + w * 0.30, y + h * 0.48, h * 0.30
    for k in range(12):
        a = math.radians(k * 30 - 90)
        sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.ellipse([sx - 2.5, sy - 2.5, sx + 2.5, sy + 2.5],
                  fill=(255, 204, 0))
    # passport, right, with red DENIED stamp
    px, py, pw, ph = x + w * 0.58, y + h * 0.16, w * 0.34, h * 0.68
    d.rectangle([px, py, px + pw, py + ph], fill=(120, 20, 28),
                outline=(230, 200, 160))
    d.ellipse([px + pw * 0.30, py + ph * 0.14, px + pw * 0.70,
               py + ph * 0.14 + pw * 0.40], fill=(240, 200, 170))
    d.line([px + 6, py + ph * 0.52, px + pw - 6, py + ph * 0.52],
           fill=(230, 200, 160), width=2)
    d.line([px + 6, py + ph * 0.62, px + pw - 6, py + ph * 0.62],
           fill=(230, 200, 160), width=1)
    d.line([px + 4, py + ph * 0.78, px + pw * 0.72, py + ph * 0.30],
           fill=(255, 60, 60), width=3)
    d.line([px + 4, py + ph * 0.30, px + pw * 0.72, py + ph * 0.78],
           fill=(255, 60, 60), width=3)


def mini_dymer(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(58, 66, 84))
    # damaged apartment block: broken top edge, dark windows
    bx, by, bw, bh = x + w * 0.14, y + h * 0.30, w * 0.46, h * 0.56
    d.polygon([(bx, by + 10), (bx + bw * 0.25, by), (bx + bw * 0.45, by + 8),
               (bx + bw * 0.70, by + 2), (bx + bw, by + 12),
               (bx + bw, by + bh), (bx, by + bh)], fill=(150, 146, 138))
    for r in range(3):
        for cidx in range(3):
            d.rectangle([bx + 6 + cidx * (bw / 3.4),
                         by + 14 + r * (bh / 3.4),
                         bx + 6 + cidx * (bw / 3.4) + 8,
                         by + 14 + r * (bh / 3.4) + 9],
                        fill=(30, 28, 34) if (r + cidx) % 2 else (90, 86, 80))
    # fallen slab + rubble at the base
    d.polygon([(bx - 6, by + bh), (bx + bw * 0.4, by + bh - 12),
               (bx + bw * 0.7, by + bh), (bx + bw * 0.2, by + bh + 6)],
              fill=(110, 106, 98))
    # crane arm + hook, right
    d.line([x + w * 0.78, y + h * 0.10, x + w * 0.78, y + h * 0.86],
           fill=(240, 200, 60), width=3)
    d.line([x + w * 0.78, y + h * 0.10, x + w * 0.96, y + h * 0.22],
           fill=(240, 200, 60), width=3)
    d.line([x + w * 0.94, y + h * 0.22, x + w * 0.94, y + h * 0.40],
           fill=(200, 200, 210), width=1)
    d.rectangle([x + w * 0.92, y + h * 0.40, x + w * 0.96, y + h * 0.46],
                fill=(200, 60, 60))
    # searchlight beam
    d.polygon([(x + w * 0.78, y + h * 0.30), (bx + bw * 0.8, by + bh * 0.5),
               (bx + bw * 0.8, by + bh * 0.5 + 8)],
              fill=(255, 240, 180, 90))


def mini_markets(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(246, 244, 238))
    # grid lines
    for gy in (0.25, 0.5, 0.75):
        d.line([x + 4, y + h * gy, x + w - 4, y + h * gy],
               fill=(220, 216, 200), width=1)
    # candlesticks: red down, then green up
    candles = [(0.08, 0.55, 0.70, 0.62, (178, 24, 32)),
               (0.22, 0.48, 0.62, 0.55, (178, 24, 32)),
               (0.36, 0.42, 0.55, 0.48, (44, 128, 74)),
               (0.50, 0.34, 0.46, 0.40, (44, 128, 74)),
               (0.64, 0.26, 0.38, 0.32, (44, 128, 74)),
               (0.78, 0.16, 0.28, 0.22, (44, 128, 74))]
    for (cx0, top, bot, _, col) in candles:
        cx = x + w * cx0
        d.line([cx + 5, y + h * (top - 0.05), cx + 5, y + h * (bot + 0.05)],
               fill=col, width=1)
        d.rectangle([cx, y + h * top, cx + 10, y + h * bot], fill=col)
    # rising arrow
    d.line([x + w * 0.10, y + h * 0.62, x + w * 0.88, y + h * 0.16],
           fill=(22, 38, 76), width=3)
    d.polygon([(x + w * 0.88, y + h * 0.16), (x + w * 0.78, y + h * 0.16),
               (x + w * 0.88, y + h * 0.26)], fill=(22, 38, 76))
    # gold coin
    d.ellipse([x + w * 0.78, y + h * 0.60, x + w * 0.78 + 20,
               y + h * 0.60 + 20], fill=(255, 206, 60),
              outline=(180, 140, 20))
    d.text((x + w * 0.78 + 7, y + h * 0.60 + 4), "$", font=F(SANS_BLACK, 11),
           fill=(120, 90, 10))


def mini_whitehouse(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(168, 205, 226))
    # lawn
    d.rectangle([x, y + h * 0.78, x + w, y + h], fill=(86, 148, 74))
    # White House: central block + dome + wings
    bx, by, bw, bh = x + w * 0.22, y + h * 0.34, w * 0.56, h * 0.44
    d.rectangle([bx, by, bx + bw, by + bh], fill=(250, 250, 246),
                outline=(180, 180, 170))
    d.pieslice([bx + bw * 0.32, by - h * 0.24, bx + bw * 0.68, by + 2],
               180, 360, fill=(250, 250, 246), outline=(180, 180, 170))
    for i in range(5):
        cx = bx + bw * (0.12 + 0.19 * i)
        d.rectangle([cx, by + 6, cx + 6, by + bh - 6], fill=(210, 210, 200))
    d.rectangle([bx + bw * 0.42, by + bh * 0.55, bx + bw * 0.58,
                 by + bh], fill=(60, 60, 66))
    # document with red seal, front
    dx, dy = x + w * 0.68, y + h * 0.58
    d.rectangle([dx, dy, dx + 26, dy + 20], fill=(252, 250, 240),
                outline=(150, 150, 150))
    d.ellipse([dx + 17, dy + 11, dx + 25, dy + 19], fill=RED)
    for k in range(2):
        d.line([dx + 4, dy + 5 + k * 4, dx + 15, dy + 5 + k * 4],
               fill=(150, 150, 150), width=1)


def mini_seoul(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(168, 205, 226))
    # N Seoul Tower on Namsan, centre
    tx = x + w * 0.50
    d.polygon([(tx - 16, y + h * 0.86), (tx - 6, y + h * 0.30),
               (tx + 6, y + h * 0.30), (tx + 16, y + h * 0.86)],
              fill=(120, 130, 140))
    d.ellipse([tx - 12, y + h * 0.22, tx + 12, y + h * 0.22 + 12],
              fill=(200, 60, 60))
    d.line([tx, y + h * 0.10, tx, y + h * 0.22], fill=(200, 60, 60), width=2)
    # skyline blocks
    bx = x + 4
    for bw, bh in [(18, 0.34), (14, 0.46), (20, 0.30), (14, 0.40), (16, 0.32)]:
        d.rectangle([bx, y + h - h * bh - 4, bx + bw, y + h - 4],
                    fill=(70, 92, 118))
        bx += bw + 5
    d.rectangle([x, y + h - 4, x + w, y + h], fill=(90, 100, 112))
    # taegeuk swirl, small, bottom right
    sx, sy, sr = x + w * 0.84, y + h * 0.72, 8
    d.pieslice([sx - sr, sy - sr, sx + sr, sy + sr], 90, 270,
               fill=(178, 24, 32))
    d.pieslice([sx - sr, sy - sr, sx + sr, sy + sr], 270, 90,
               fill=(22, 38, 76))


def mini_quake(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(196, 220, 236))
    # Himalaya ridge: two ranges, snow caps
    d.polygon([(x, y + h * 0.78), (x + w * 0.18, y + h * 0.30),
               (x + w * 0.34, y + h * 0.62), (x + w * 0.50, y + h * 0.22),
               (x + w * 0.66, y + h * 0.58), (x + w * 0.82, y + h * 0.34),
               (x + w, y + h * 0.66), (x + w, y + h * 0.78)],
              fill=(110, 128, 150))
    for (px, py) in [(0.18, 0.30), (0.50, 0.22), (0.82, 0.34)]:
        d.polygon([(x + w * px - 8, y + h * py + 7), (x + w * px, y + h * py),
                   (x + w * px + 8, y + h * py + 7),
                   (x + w * px + 3, y + h * py + 4),
                   (x + w * px, y + h * py + 8),
                   (x + w * px - 3, y + h * py + 4)],
                  fill=(250, 250, 248))
    d.rectangle([x, y + h * 0.78, x + w, y + h], fill=(140, 124, 96))
    # epicentre rings + crack, front centre
    cx, cy = x + w * 0.50, y + h * 0.88
    for r in (5, 10, 15):
        d.ellipse([cx - r, cy - r * 0.45, cx + r, cy + r * 0.45],
                  outline=RED, width=2)
    d.line([x + w * 0.06, y + h * 0.92, x + w * 0.30, y + h * 0.86,
            x + w * 0.44, y + h * 0.93], fill=(60, 50, 40), width=2)
    d.line([x + w * 0.58, y + h * 0.90, x + w * 0.78, y + h * 0.85,
            x + w * 0.94, y + h * 0.92], fill=(60, 50, 40), width=2)


def mini_plane(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY_DAY)
    d.ellipse([x + w * 0.80, y + h * 0.08, x + w * 0.80 + 13,
               y + h * 0.08 + 13], fill=(255, 214, 90))
    # airliner silhouette, centre: fuselage, wing, tail, windows
    bx, by = x + w * 0.16, y + h * 0.34
    d.polygon([(bx, by + 8), (bx + w * 0.52, by + 2), (bx + w * 0.62, by + 6),
               (bx + w * 0.62, by + 11), (bx + w * 0.50, by + 14),
               (bx + w * 0.10, by + 13)], fill=(246, 246, 242),
              outline=(120, 124, 132))
    d.polygon([(bx + w * 0.26, by + 10), (bx + w * 0.38, by + 22),
               (bx + w * 0.44, by + 22), (bx + w * 0.36, by + 9)],
              fill=(220, 60, 60))
    d.polygon([(bx + w * 0.02, by + 6), (bx - w * 0.03, by - 4),
               (bx + w * 0.05, by - 3), (bx + w * 0.08, by + 5)],
              fill=(220, 60, 60))
    for k in range(6):
        d.ellipse([bx + w * (0.14 + 0.06 * k), by + 6,
                   bx + w * (0.14 + 0.06 * k) + 3, by + 9],
                  fill=(90, 110, 140))
    # runway strip
    d.rectangle([x, y + h * 0.82, x + w, y + h], fill=(52, 54, 60))
    for k in range(7):
        d.rectangle([x + w * (0.05 + 0.14 * k), y + h * 0.90,
                     x + w * (0.10 + 0.14 * k), y + h * 0.93],
                    fill=(240, 240, 235))


def mini_train(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(206, 226, 208))
    d.polygon([(x, y + h * 0.52), (x + w * 0.3, y + h * 0.30),
               (x + w * 0.62, y + h * 0.52)], fill=(120, 160, 110))
    d.rectangle([x, y + h * 0.62, x + w, y + h], fill=(150, 138, 110))
    # locomotive + two coaches
    ty = y + h * 0.44
    d.rectangle([x + w * 0.06, ty, x + w * 0.30, ty + h * 0.30],
                fill=(178, 24, 32))
    d.rectangle([x + w * 0.20, ty - h * 0.12, x + w * 0.30, ty],
                fill=(150, 20, 28))
    d.rectangle([x + w * 0.09, ty + h * 0.06, x + w * 0.16, ty + h * 0.16],
                fill=(200, 226, 240))
    for cx0 in (0.34, 0.62):
        d.rectangle([x + w * cx0, ty + h * 0.02, x + w * (cx0 + 0.24),
                     ty + h * 0.30], fill=(240, 180, 60))
        for k in range(3):
            d.rectangle([x + w * (cx0 + 0.03 + 0.07 * k), ty + h * 0.07,
                         x + w * (cx0 + 0.07 + 0.07 * k), ty + h * 0.17],
                        fill=(90, 110, 140))
    for wx in (0.10, 0.24, 0.40, 0.52, 0.68, 0.80):
        d.ellipse([x + w * wx, ty + h * 0.30, x + w * wx + 8,
                   ty + h * 0.30 + 8], fill=(30, 30, 34))
    d.line([x, ty + h * 0.42, x + w, ty + h * 0.42], fill=(80, 76, 70),
           width=2)
    # steam puffs
    for (ox, oy, orr) in [(0.24, 0.16, 5), (0.30, 0.10, 7)]:
        d.ellipse([x + w * ox - orr, y + h * oy - orr * 0.6,
                   x + w * ox + orr, y + h * oy + orr * 0.6],
                  fill=(250, 250, 248, 210))


def mini_chip(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(16, 22, 40))
    # circuit traces with pads
    for (x0, y0, x1, y1) in [(0.04, 0.24, 0.30, 0.24), (0.04, 0.76, 0.30, 0.76),
                             (0.70, 0.24, 0.96, 0.24), (0.70, 0.76, 0.96, 0.76),
                             (0.12, 0.06, 0.12, 0.24), (0.88, 0.76, 0.88, 0.94)]:
        d.line([x + w * x0, y + h * y0, x + w * x1, y + h * y1],
               fill=(44, 128, 74), width=2)
        d.ellipse([x + w * x0 - 2, y + h * y0 - 2, x + w * x0 + 2,
                   y + h * y0 + 2], fill=(120, 200, 140))
    # the chip: body, inner die, pins
    cx, cy, cs = x + w * 0.38, y + h * 0.18, w * 0.24
    for k in range(4):
        d.line([cx + 6 + k * 9, cy - 5, cx + 6 + k * 9, cy],
               fill=(200, 204, 210), width=2)
        d.line([cx + 6 + k * 9, cy + cs, cx + 6 + k * 9, cy + cs + 5],
               fill=(200, 204, 210), width=2)
        d.line([cx - 5, cy + 6 + k * 9, cx, cy + 6 + k * 9],
               fill=(200, 204, 210), width=2)
        d.line([cx + cs, cy + 6 + k * 9, cx + cs + 5, cy + 6 + k * 9],
               fill=(200, 204, 210), width=2)
    d.rectangle([cx, cy, cx + cs, cy + cs], fill=(58, 64, 74),
                outline=(200, 204, 210))
    d.rectangle([cx + cs * 0.28, cy + cs * 0.28, cx + cs * 0.72,
                 cy + cs * 0.72], fill=(90, 98, 112))
    # green up-triangle: the rally
    d.polygon([(x + w * 0.80, y + h * 0.62), (x + w * 0.88, y + h * 0.38),
               (x + w * 0.96, y + h * 0.62)], fill=(44, 180, 84))


def mini_chess(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 234, 216))
    # board: two rows of squares along the bottom
    sq = w / 8
    for r in range(2):
        for cidx in range(8):
            if (r + cidx) % 2 == 0:
                d.rectangle([x + cidx * sq, y + h - (2 - r) * sq * 0.42,
                             x + (cidx + 1) * sq, y + h - (1 - r) * sq * 0.42],
                            fill=(90, 62, 40))
    # black king, left: base, body, cross
    kx, ky = x + w * 0.24, y + h * 0.16
    d.rectangle([kx - 10, ky + 22, kx + 10, ky + 27], fill=(24, 24, 28))
    d.polygon([(kx - 7, ky + 22), (kx - 4, ky + 8), (kx + 4, ky + 8),
               (kx + 7, ky + 22)], fill=(24, 24, 28))
    d.rectangle([kx - 1.5, ky - 4, kx + 1.5, ky + 8], fill=(24, 24, 28))
    d.rectangle([kx - 4, ky - 1, kx + 4, ky + 2], fill=(24, 24, 28))
    # white knight, right: base + horse-head profile
    nx, ny = x + w * 0.68, y + h * 0.16
    d.rectangle([nx - 10, ny + 22, nx + 10, ny + 27], fill=(248, 248, 244),
                outline=(120, 118, 110))
    d.polygon([(nx - 6, ny + 22), (nx - 6, ny + 6), (nx - 1, ny - 2),
               (nx + 7, ny + 3), (nx + 9, ny + 10), (nx + 3, ny + 12),
               (nx + 4, ny + 22)], fill=(248, 248, 244),
              outline=(120, 118, 110))
    d.ellipse([nx + 1, ny + 4, nx + 4, ny + 7], fill=(24, 24, 28))


def mini_congress(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY_DAY)
    d.rectangle([x, y + h * 0.80, x + w, y + h], fill=(86, 148, 74))
    # Brasilia: twin towers centre, dome (senate) left, bowl (chamber)
    cx = x + w * 0.50
    for tx in (cx - 11, cx + 3):
        d.rectangle([tx, y + h * 0.14, tx + 8, y + h * 0.80],
                    fill=(236, 234, 228), outline=(150, 148, 140))
    for k in range(5):
        d.line([cx - 11, y + h * (0.24 + 0.11 * k), cx + 11,
                y + h * (0.24 + 0.11 * k)], fill=(170, 168, 160), width=1)
    d.pieslice([cx - w * 0.30, y + h * 0.52, cx - w * 0.08, y + h * 0.96],
               180, 360, fill=(236, 234, 228), outline=(150, 148, 140))
    d.pieslice([cx + w * 0.08, y + h * 0.50, cx + w * 0.30, y + h * 0.94],
               0, 180, fill=(236, 234, 228), outline=(150, 148, 140))
    # reflecting pool strip
    d.rectangle([x + w * 0.06, y + h * 0.86, x + w * 0.94, y + h * 0.92],
                fill=(120, 170, 205))


def mini_skyline(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(250, 214, 150))
    d.rectangle([x, y + h * 0.30, x + w, y + h * 0.78], fill=(240, 178, 120))
    # towers along the bay
    bx = x + 3
    for bw, bh in [(13, 0.52), (9, 0.66), (15, 0.44), (10, 0.58), (13, 0.48)]:
        d.rectangle([bx, y + h * 0.78 - h * bh, bx + bw, y + h * 0.78],
                    fill=(38, 52, 84))
        bx += bw + 5
    # the Flyer: big wheel, right
    cx, cy, r = x + w * 0.80, y + h * 0.42, h * 0.30
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(38, 52, 84),
              width=2)
    for a in (0, 45, 90, 135):
        import math as _m
        dx = r * _m.cos(_m.radians(a))
        dy = r * _m.sin(_m.radians(a))
        d.line([cx - dx, cy - dy, cx + dx, cy + dy], fill=(38, 52, 84),
               width=1)
    d.line([cx - 6, y + h * 0.78, cx, cy + r * 0.6], fill=(38, 52, 84),
           width=2)
    d.line([cx + 6, y + h * 0.78, cx, cy + r * 0.6], fill=(38, 52, 84),
           width=2)
    # water + a bumboat
    d.rectangle([x, y + h * 0.78, x + w, y + h], fill=SEA)
    d.polygon([(x + w * 0.30, y + h * 0.86), (x + w * 0.44, y + h * 0.86),
               (x + w * 0.41, y + h * 0.93), (x + w * 0.33, y + h * 0.93)],
              fill=(24, 24, 28))
    d.rectangle([x + w * 0.345, y + h * 0.80, x + w * 0.405, y + h * 0.86],
                fill=(246, 244, 238))


def mini_island(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA)
    d.rectangle([x, y, x + w, y + h * 0.36], fill=(168, 205, 226))
    d.ellipse([x + w * 0.06, y + h * 0.06, x + w * 0.06 + 12,
               y + h * 0.06 + 12], fill=(255, 214, 90))
    # sand island
    d.ellipse([x + w * 0.26, y + h * 0.52, x + w * 0.78, y + h * 0.94],
              fill=(238, 220, 170))
    d.ellipse([x + w * 0.33, y + h * 0.58, x + w * 0.71, y + h * 0.86],
              fill=(120, 170, 90))
    # palm: curved trunk + fronds
    px, py = x + w * 0.52, y + h * 0.60
    d.line([px, py + 12, px + 3, py], fill=(110, 80, 44), width=3)
    for (ex, ey) in [(-13, -6), (-7, -10), (0, -11), (8, -9), (13, -4)]:
        d.line([px + 3, py, px + 3 + ex, py + ey], fill=(34, 120, 60),
               width=2)
    # wave strokes
    for (wx, wy) in [(0.10, 0.66), (0.84, 0.60), (0.16, 0.86)]:
        d.arc([x + w * wx, y + h * wy, x + w * wx + 16, y + h * wy + 7],
              180, 360, fill=(220, 236, 248), width=2)


def mini_parliament(x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SKY_DAY)
    # Parliament House, Canberra: white wall under a grass slope,
    # the great flagpole in front
    d.polygon([(x + w * 0.16, y + h * 0.78), (x + w * 0.38, y + h * 0.40),
               (x + w * 0.62, y + h * 0.40), (x + w * 0.84, y + h * 0.78)],
              fill=(96, 160, 84))
    d.rectangle([x + w * 0.30, y + h * 0.56, x + w * 0.70, y + h * 0.80],
                fill=(246, 246, 242), outline=(170, 168, 160))
    for k in range(4):
        d.rectangle([x + w * (0.35 + 0.09 * k), y + h * 0.64,
                     x + w * (0.39 + 0.09 * k), y + h * 0.74],
                    fill=(90, 110, 140))
    px = x + w * 0.50
    d.line([px, y + h * 0.06, px, y + h * 0.56], fill=(60, 60, 66), width=2)
    d.polygon([(px, y + h * 0.06), (px + 13, y + h * 0.10),
               (px, y + h * 0.15)], fill=(22, 38, 76))
    d.rectangle([x, y + h * 0.80, x + w, y + h], fill=(110, 175, 95))


CARD_SCENES = {"tanker": mini_tanker, "gaza": mini_gaza,
               "cikande": mini_cikande, "grok": mini_grok,
               "satellite": mini_satellite, "denmark": mini_denmark,
               "dymer": mini_dymer, "markets": mini_markets,
               "whitehouse": mini_whitehouse, "seoul": mini_seoul,
               "quake": mini_quake, "plane": mini_plane,
               "train": mini_train, "chip": mini_chip,
               "chess": mini_chess, "congress": mini_congress,
               "skyline": mini_skyline, "island": mini_island,
               "parliament": mini_parliament}


# ------------------------------------------------------------------ world map
# Coastline-free dotted continents: 12-px grid, land-test by polygon.
# Polygons drawn in lon/lat. Map height 150 px (was ~60 px on ni21),
# dots cream on navy so every pin and the dot pattern read at full size.
def point_in_poly(lon, lat, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > lat) != (yj > lat)) and \
           (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def lon_lat_to_xy(lon, lat, mx, my, mw, mh):
    px = mx + (lon + 180.0) / 360.0 * mw
    py = my + (90.0 - lat) / 180.0 * mh
    return px, py


def lon_lat_rect(lon0, lon1, lat0, lat1, mx, my, mw, mh):
    x0, y1 = lon_lat_to_xy(lon0, lat0, mx, my, mw, mh)
    x1, y0 = lon_lat_to_xy(lon1, lat1, mx, my, mw, mh)
    return x0, y0, x1, y1


# (lon, lat) — verified against a real world map for ni22.
CONTINENTS = [
    ([(-168, 66), (-156, 71), (-140, 70), (-130, 71), (-125, 62), (-125, 48),
      (-124, 40), (-118, 34), (-110, 23), (-97, 16), (-87, 13), (-83, 9),
      (-79, 9), (-81, 15), (-85, 16), (-90, 18), (-95, 19), (-97, 26),
      (-90, 30), (-82, 31), (-76, 35), (-75, 40), (-70, 43), (-66, 45),
      (-60, 47), (-55, 52), (-65, 60), (-68, 58), (-72, 62), (-78, 62),
      (-90, 66), (-95, 69), (-110, 68), (-125, 70), (-140, 70),
      (-155, 71), (-168, 66)], "NORTH AMERICA"),
    ([(-80, 10), (-79, 4), (-77, -4), (-81, -6), (-77, -12), (-71, -18),
      (-70, -23), (-70, -30), (-71, -35), (-73, -44), (-74, -50),
      (-70, -54), (-66, -55), (-66, -47), (-62, -41), (-58, -34),
      (-52, -32), (-48, -27), (-40, -22), (-35, -9), (-35, -6),
      (-41, -3), (-44, -2), (-50, 0), (-52, 4), (-57, 6), (-61, 9),
      (-65, 10), (-71, 12), (-75, 10), (-80, 10)], "SOUTH AMERICA"),
    ([(-10, 37), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 50),
      (2, 51), (5, 53), (7, 54), (8, 57), (10, 59), (5, 60), (5, 62),
      (10, 64), (12, 66), (18, 69), (25, 71), (31, 70), (40, 68),
      (44, 66), (42, 60), (40, 56), (38, 54), (40, 50), (35, 46),
      (31, 46), (30, 46), (28, 45), (23, 40), (19, 42), (13, 44),
      (8, 44), (3, 42), (0, 39), (-2, 37), (-6, 36), (-10, 37)],
     "EUROPE"),
    ([(-6, 35), (0, 36), (10, 37), (11, 34), (19, 30), (20, 32),
      (25, 32), (30, 31), (32, 31), (35, 28), (39, 21), (43, 12),
      (48, 11), (51, 11), (56, 16), (58, 21), (55, 25), (52, 28),
      (48, 30), (44, 30), (38, 20), (35, 15), (33, 12), (32, 10),
      (30, 12), (26, 17), (21, 16), (15, 15), (12, 14), (9, 9),
      (9, 4), (6, 4), (3, 6), (-8, 4), (-13, 8), (-17, 12), (-17, 15),
      (-15, 20), (-15, 25), (-13, 28), (-10, 30), (-6, 35)],
     "AFRICA"),
    ([(26, 38), (30, 36), (36, 36), (36, 30), (39, 27), (41, 29),
      (44, 29), (47, 30), (50, 29), (54, 26), (57, 26), (58, 24),
      (61, 25), (66, 25), (70, 22), (73, 20), (76, 10), (80, 8),
      (81, 9), (84, 19), (88, 22), (91, 22), (93, 17), (95, 16),
      (98, 8), (100, 6), (101, 3), (104, 2), (105, 9), (107, 11),
      (109, 15), (106, 21), (110, 20), (113, 22), (116, 23),
      (120, 25), (122, 31), (120, 35), (122, 38), (127, 40),
      (130, 42), (133, 43), (136, 44), (140, 47), (142, 50),
      (142, 54), (140, 59), (142, 60), (158, 59), (162, 60),
      (170, 66), (178, 65), (180, 66), (180, 62), (170, 60),
      (162, 60), (158, 53), (150, 59), (142, 54), (142, 48),
      (138, 44), (132, 43), (128, 40), (124, 39), (121, 36),
      (116, 36), (113, 30), (110, 24), (108, 18), (104, 8),
      (100, 13), (96, 16), (92, 21), (89, 22), (86, 20), (82, 16),
      (77, 8), (73, 16), (68, 23), (62, 25), (57, 25), (53, 26),
      (48, 30), (44, 29), (41, 29), (36, 36), (33, 39), (26, 41),
      (26, 38)], "ASIA"),
    ([(114, -22), (114, -32), (115, -35), (118, -35), (124, -33),
      (130, -32), (133, -32), (137, -35), (140, -38), (145, -38),
      (150, -37), (153, -32), (153, -27), (150, -22), (146, -19),
      (142, -15), (142, -11), (136, -12), (132, -11), (127, -14),
      (122, -17), (118, -20), (114, -22)], "AUSTRALIA"),
]

# Pin positions (lon, lat) — the 13 pictured stories, from STORIES.md.
PINS = [
    (1, 139.69, 35.68, RED),  # Tokyo
    (2, 130.90, 37.50, RED),  # Ulleung Island
    (3, 100.29, 40.96, RED),  # Jiuquan
    (4, 87.91, 27.86, RED),   # Koshi, Nepal
    (5, 90.41, 23.81, RED),   # Dhaka
    (6, 77.21, 28.61, RED),   # New Delhi
    (7, 13.18, 32.90, RED),   # Tripoli
    (8, 121.47, 31.23, RED),  # Shanghai
    (9, 6.14, 46.20, RED),    # Geneva
    (10, -47.88, -15.79, RED),  # Brasília
    (11, 103.85, 1.35, RED),  # Singapore
    (12, 178.44, -17.73, RED),  # Suva
    (13, 149.13, -35.28, RED),  # Canberra
]


# Map projection (equirectangular, cropped to the inhabited latitudes so
# continents read at 150 px tall): lon -168..192, lat 78..-57.
MAP_LON = (-168.0, 192.0)
MAP_LAT = (78.0, -57.0)


# Pins drawn with a pixel offset + leader line (their true spot is
# crowded by a neighbour's disc): the East Asia pair 1 Tokyo /
# 2 Ulleung, and the South Asia cluster 4 Koshi / 5 Dhaka / 6 Delhi.
PIN_OFFSETS = {1: (10, -6), 2: (-6, -9), 4: (-4, -14), 5: (16, 10),
               6: (-14, -4)}


def draw_map(mx, my, mw, mh):
    d.rectangle([mx, my, mx + mw, my + mh], fill=NAVY_DARK)
    cols, rows = 118, 36
    cw_, ch_ = mw / cols, mh / rows
    for r in range(rows):
        lat = MAP_LAT[0] + (r + 0.5) * (MAP_LAT[1] - MAP_LAT[0]) / rows
        for c in range(cols):
            lon = MAP_LON[0] + (c + 0.5) * (MAP_LON[1] - MAP_LON[0]) / cols
            if any(point_in_poly(lon, lat, poly) for poly, _ in
                   CONTINENTS):
                cx = mx + (c + 0.5) * cw_
                cy = my + (r + 0.5) * ch_
                d.ellipse([cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5],
                          fill=(238, 232, 205))
    # equator / tropics graticule
    for lat in (0, 23.5, -23.5):
        gy = my + (MAP_LAT[0] - lat) / (MAP_LAT[0] - MAP_LAT[1]) * mh
        d.line([mx, gy, mx + mw, gy], fill=(110, 120, 160), width=1)
    # pins: number in a red disc, white ring (radius 7 — the European and
    # US east-coast clusters are tight; two pins use a leader line)
    for num, lon, lat, col in PINS:
        px = mx + (lon - MAP_LON[0]) / (MAP_LON[1] - MAP_LON[0]) * mw
        py = my + (MAP_LAT[0] - lat) / (MAP_LAT[0] - MAP_LAT[1]) * mh
        ox, oy = PIN_OFFSETS.get(num, (0, 0))
        if (ox, oy) != (0, 0):
            d.line([px, py, px + ox, py + oy], fill=(255, 255, 255),
                   width=1)
            px, py = px + ox, py + oy
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col,
                  outline=(255, 255, 255), width=2)
        ns = str(num)
        f = F(SANS_BLACK, 8)
        d.text((px - tw(ns, f) / 2, py - 5), ns, font=f, fill=(255, 255, 255))
    # caption INSIDE the map, on a solid strip (Patagonia's dots reach
    # the bottom edge and would cross the text otherwise)
    d.rectangle([mx, my + mh - 16, mx + mw, my + mh], fill=NAVY_DARK)
    d.text((mx + 6, my + mh - 12),
           "WHERE THE NEWS IS  ·  13 PICTURED STORIES PINNED",
           font=F(SANS, 8), fill=(200, 204, 220))



# ------------------------------------------------------------------ page
# Vertical budget (proven on ni22): masthead 0–24 · headline 30–88 ·
# strap rules 100/138 · stats 146–192 · region bar 196–216 · UTC 224–238
# · leads 254–540 · cards 540/662 · bottom 794–960 · DATE CHECK 966–1008
# · footer 1012.
def header():
    d.rectangle([0, 0, W, 24], fill=NAVY_DARK)
    centre("THE WORLD IN ONE DAY · 36 STORIES · 6 REGIONS · EVERY ONE "
           "DATED TUESDAY 24 NOVEMBER 2026", W / 2, 5, F(SANS_BOLD, 11),
           fill=(248, 243, 228))
    centre("Tuesday 24 November 2026", W / 2, 30,
           fit("Tuesday 24 November 2026", SERIF_BLACK, 58, CW))
    # strap: rules at 100 and 138, text between with clear padding
    rule(M, M + CW, 100, fill=INK, width=2)
    centre(STRAP, W / 2, 109, fit(STRAP, SERIF_IT, 16, CW), fill=RED)
    rule(M, M + CW, 138, fill=INK, width=1)


def stat_strip():
    y = 146
    colw = CW / 6
    for i, (num, lab) in enumerate(STATS):
        cx = M + colw * i + colw / 2
        centre(num, cx, y, fit(num, SANS_BLACK, 27, colw - 8), fill=RED)
        lf = F(SANS_BOLD, 8)
        lines = wrap(lab, lf, colw - 10)
        for j, ln in enumerate(lines[:2]):
            centre(ln, cx, y + 34 + j * 10, lf, fill=GREY)
        if i:
            d.line([M + colw * i, y + 2, M + colw * i, y + 46],
                   fill=CREAM_LINE, width=1)


def region_bar():
    y = 196
    total = sum(c for _, c, _ in REGIONS)
    assert total == 36, f"region tally {total} != 36"
    x = M
    f = F(SANS_BOLD, 10)
    spans = {}
    for name, count, colour in REGIONS:
        w_ = CW * count / total
        d.rectangle([x, y, x + w_, y + 20], fill=colour)
        spans[name] = (x, x + w_)
        if name in ("AMERICAS", "EUROPE", "ASIA-PACIFIC"):
            centre(f"{name} {count}", x + w_ / 2, y + 5, f,
                   fill=(255, 255, 255))
        x += w_
    # MIDDLE EAST 1, AFRICA 1 and WORLD 2 segments are too narrow for
    # separate labels — one joint label centred across all three,
    # shrunk to fit their combined span.
    jx = (spans["MIDDLE EAST"][0] + spans["WORLD"][1]) / 2
    jw = spans["WORLD"][1] - spans["MIDDLE EAST"][0]
    jtext = "MIDEAST 1 · AFRICA 1 · WORLD 2"
    centre(jtext, jx, y + 6, fit(jtext, SANS_BOLD, 10, jw + 4),
           fill=(255, 255, 255))


def utc_strip():
    y = 224
    lw, _ = chip(M, y, "THE DAY IN UTC", NAVY_DARK, font_size=10)
    x = M + lw + 10
    f_t, f_s = F(SANS_BLACK, 11), F(SANS, 10)
    for t, s in UTC_STRIP:
        d.text((x, y + 2), t, font=f_t, fill=RED)
        x += tw(t, f_t) + 4
        d.text((x, y + 3), s, font=f_s, fill=INK)
        x += tw(s, f_s) + 14
    if x - 14 > M + CW:
        WARNINGS.append(f"UTC strip overflows: ends at {x - 14}")


def draw_scene_clipped(scene_fn, x, y, w, h):
    """Render a scene on its own layer and paste it — nothing the scene
    draws (Earth arcs, smoke, rings) may spill past its banner box."""
    global d
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    old_d = d
    d = ImageDraw.Draw(layer, "RGBA")
    try:
        scene_fn(0, 0, w, h)
    finally:
        d = old_d
    img.paste(layer, (x, y), layer)


def lead_panel(i, x, y, lead):
    w = 317
    draw_scene_clipped(LEAD_SCENES[lead["scene"]], x, y, w, 150)
    d.rectangle([x, y, x + w, y + 150], outline=INK, width=1)
    chip(x + 8, y + 8, lead["tag"], RED, font_size=10)
    sf = F(SANS_BOLD, 10)
    sw = tw(lead["stat"], sf) + 10
    d.rectangle([x + w - sw - 8, y + 8, x + w - 8, y + 8 + 15],
                fill=(255, 255, 255))
    d.text((x + w - sw - 3, y + 10), lead["stat"], font=sf, fill=INK)
    ty = y + 158
    # number badge + kicker + label
    d.rectangle([x, ty, x + 19, ty + 15], fill=INK)
    nf = F(SANS_BOLD, 10)
    d.text((x + 9 - tw(str(i + 1), nf) / 2, ty + 2), str(i + 1), font=nf,
           fill=(255, 255, 255))
    kf = F(SANS_BOLD, 10)
    d.text((x + 25, ty + 2), lead["kicker"] + "  ·", font=kf, fill=NAVY)
    lx = x + 25 + tw(lead["kicker"] + "  ·", kf) + 4
    lc = RED if lead["label"] == "CLAIM" else (44, 128, 74)
    d.ellipse([lx, ty + 5, lx + 7, ty + 12], fill=lc)
    d.text((lx + 10, ty + 2), lead["label"], font=kf, fill=lc)
    hy = ty + 19
    # fixed 21 pt, wraps to two lines (fit() would shrink a 50-char
    # headline to one line — never use it on a wrapped headline)
    hy = text_block(x, hy, lead["headline"], F(SERIF_BOLD, 21), w, 24,
                    max_lines=2)
    by = text_block(x, hy + 2, lead["body"], F(SANS, 10), w, 13.5,
                    fill=(40, 40, 44), max_lines=3)
    d.text((x, by + 3), lead["source"], font=F(SANS_BOLD, 8), fill=GREY)
    return by + 14


def card(i, x, y, cnum, tag, stat, place, label, head, body, source, scene):
    w = 188
    draw_scene_clipped(CARD_SCENES[scene], x, y, w, 50)
    d.rectangle([x, y, x + w, y + 50], outline=INK, width=1)
    chip(x + 5, y + 5, tag, RED, font_size=8)
    sf = F(SANS_BOLD, 8)
    sw = tw(stat, sf) + 8
    d.rectangle([x + w - sw - 5, y + 5, x + w - 5, y + 5 + 13],
                fill=(255, 255, 255))
    d.text((x + w - sw - 1, y + 7), stat, font=sf, fill=INK)
    # source credit as a caption strip along the banner's bottom edge
    d.rectangle([x, y + 39, x + w, y + 50], fill=(12, 12, 16))
    d.text((x + 5, y + 41), source, font=F(SANS_BOLD, 7),
           fill=(235, 232, 220))
    ky = y + 54
    d.rectangle([x, ky, x + 15, ky + 12], fill=INK)
    nf = F(SANS_BOLD, 8)
    d.text((x + 7 - tw(str(cnum), nf) / 2, ky + 2), str(cnum), font=nf,
           fill=(255, 255, 255))
    kf = F(SANS_BOLD, 8)
    d.text((x + 19, ky + 2), place + " ·", font=kf, fill=NAVY)
    lx = x + 19 + tw(place + " ·", kf) + 3
    lc = RED if label == "CLAIM" else (44, 128, 74)
    d.ellipse([lx, ky + 3, lx + 6, ky + 9], fill=lc)
    d.text((lx + 8, ky + 2), label, font=kf, fill=lc)
    hy = text_block(x, ky + 14, head, F(SERIF_BOLD, 13), w, 14.5,
                    max_lines=2)
    text_block(x, hy + 1, body, F(SANS, 9), w, 11, fill=(40, 40, 44),
               max_lines=2)


def bottom():
    y = 794
    d.text((M, y), "WHERE IT HAPPENED", font=F(SANS_BLACK, 11), fill=NAVY)
    mw = tw("WHERE IT HAPPENED", F(SANS_BLACK, 11))
    d.text((M + mw + 8, y + 2), "pins match story numbers",
           font=F(SANS, 9), fill=GREY)
    draw_map(M, y + 16, 474, 150)
    # also-on list (black text on the paper, roomy leading)
    ax = M + 486
    d.text((ax, y), "ALSO ON TUESDAY 24 NOVEMBER", font=F(SANS_BLACK, 11),
           fill=RED)
    aw = tw("ALSO ON TUESDAY 24 NOVEMBER", F(SANS_BLACK, 11))
    d.text((ax + aw + 8, y + 2), "— 23 more stories", font=F(SANS, 9),
           fill=GREY)
    nf, tf, gf = F(SANS_BOLD, 9), F(SANS, 9), F(SANS, 8)
    col_w = (W - M - ax - 12) / 2
    for j, (num, text, source, label) in enumerate(BRIEFS):
        col = 0 if j < 12 else 1
        row = j if j < 12 else j - 12
        bx = ax + col * (col_w + 12)
        by = y + 18 + row * 12.5
        d.text((bx, by), f"{num}", font=nf, fill=RED)
        tx = bx + tw(f"{num}", nf) + 5
        suffix = f" ({source}" + (f" · {label})" if label else ")")
        full = text + suffix
        if tw(full, tf) > col_w - (tx - bx):
            WARNINGS.append(f"brief {num} too wide: {tw(full, tf):.0f}px "
                            f"> {col_w - (tx - bx):.0f}px")
        d.text((tx, by), text, font=tf, fill=INK)
        d.text((tx + tw(text, tf), by), suffix, font=gf, fill=GREY)


def date_check():
    y = 966
    d.rectangle([M, y, M + CW, 1008], outline=RED, width=2)
    d.text((M + 10, y + 6), "DATE CHECK — CHECKED, AND LEFT OUT ON PURPOSE",
           font=F(SANS_BLACK, 11), fill=RED)
    text_block(M + 10, y + 21, DATE_CHECK, F(SANS, 9), CW - 20, 10.5,
               fill=(40, 40, 44), max_lines=2)


def main():
    header()
    stat_strip()
    region_bar()
    utc_strip()
    ends = []
    for i, lead in enumerate(LEADS):
        ends.append(lead_panel(i, M + i * 327, 254, lead))
    for j, c in enumerate(CARDS):
        row, col = divmod(j, 5)
        card(j, M + col * 196, 540 + row * 122, *c)
    bottom()
    date_check()
    # footer: one short line squeezed under the date-check box
    centre(FOOTER, W / 2, 1012, fit(FOOTER, SANS, 8, CW), fill=GREY)
    if max(ends) > 540:
        WARNINGS.append(f"lead text ends at {max(ends)} > 540")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "output")
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, "entry.png"))
    img.resize((300, 300), Image.LANCZOS).save(
        os.path.join(out, "preview-300.png"))
    for wn in WARNINGS:
        print("WARNING:", wn)
    print("wrote output/entry.png + output/preview-300.png")


if __name__ == "__main__":
    main()
