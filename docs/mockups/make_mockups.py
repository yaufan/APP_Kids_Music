"""Design-stage sketches for 「小小音波」 (a music toy for 2-5 year olds).

    python3 make_mockups.py          # writes docs/mockups/*.png (needs Node.js + Playwright)
    python3 make_mockups.py 3        # only one page: 0 = style page, 1..8 = a screen, c = contact sheet

Every picture is drawn here as SVG by code (no outside pictures, no emoji). render.js turns each page
into a PNG with Playwright's Chromium at 2x. The font is jf open-huninn from a sibling app's checkout.

    0_畫風選擇.png     the same stage (two animals, five xylophone keys, a floating balloon) in the three
                       candidate styles side by side: A 氣球充氣風, B 霓虹舞台風 (chosen), C 彩繪玻璃風
    1_舞台.png         home: the curtain stage, the band waving, six big balloon buttons
    2_敲敲樂.png       the xylophone: eight balloon keys, a tap, the frog bouncing
    3_動物樂團.png     Loopimal-style: six slots on stage, three animals singing, the cat being dragged in
    4_音樂木頭人.png   the music stopped: the big red 停 balloon, everybody frozen, the finger must wait
    5_高低快慢.png     the bird on the balloon stairs (pitch), the snail/rabbit slider (tempo), elephant/mouse (loud/soft)
    6_錄下來.png       recording taps onto an 8-beat tape, saved tapes below
    7_聽聽看.png       what sound is this? the speaker, three picture cards, the garbage truck chosen
    8_家長模式.png     parents' settings
    contact_sheet.png  screens 1-8 small, with titles

Style B 「霓虹舞台風」 (chosen, screens 1-8): a deep navy stage; every piece is a glowing neon tube: a faint
translucent fill (brighter towards the rim), the tube colour as a thick line, the same line blurred into a
soft bloom, a thin white core. Words are pale lavender with no glow so they stay readable; eyes are bright
white dots so every face shows. Style A 「氣球充氣風」: inflated glossy balloons. Style C 「彩繪玻璃風」:
translucent glass panes with dark lead lines. A and C only appear on the style page.
"""
import hashlib
import math
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
FONT = None
for _c in ("app_kids_falsecharge", "app_kids_maze", "app_kids_live_circ", "app_kids_brainstorming", "app_kids_card_game", "app_kids_cook"):
    _p = pathlib.Path("/home/user") / _c / "app" / "assets" / "fonts" / "jf-openhuninn-2.1.ttf"
    if _p.exists():
        FONT = _p
        break
SCRATCH = pathlib.Path("/dev/shm") if pathlib.Path("/dev/shm").is_dir() else pathlib.Path(tempfile.gettempdir())
W, H = 390, 844

# ---------------------------------------------------------------- colours (party balloons)
RED = "#FF6B7A"
ORA = "#FFA052"
YEL = "#FFD93D"
GRN = "#7ED96A"
TEAL = "#4FD1C5"
BLUE = "#5DB3F0"
PURP = "#B48CF5"
PINK = "#FF8FCB"
BROWN = "#D9A06B"
GREY = "#C9D3E3"
WHITE = "#FFFFFF"
CREAM = "#FFF7E8"
INK = "#3B3F66"         # words: deep night blue
SOFT = "#7B82A8"
DARK = "#2E2A3E"        # eyes
CHEEK = "#FF9FB0"
SKIN = "#FFE1CF"
NOTE_COLS = [RED, ORA, YEL, GRN, BLUE, PURP, PINK, TEAL]    # Do Re Mi Sol La Do Re Mi
STYLE = "neon"          # "neon" (B, chosen), "balloon" (A) or "glass" (C)
NEON_BG = ("#1B1A3A", "#2A2550")
NEON_INK = "#F2EEFF"
NEON_SOFT = "#B6AEDC"
NEON_MAP = {INK: NEON_INK, SOFT: NEON_SOFT, DARK: "#FFFFFF", GREY: "#6F6A99", "#F2F3F8": "#8A84B8", "#E3E6EF": "#6F6A99",
            "#FFFFFF": "#D9D2FF", CREAM: "#D9D2FF", "#FFF6D0": YEL, "#FFE2E2": PINK, "#E0F0FF": BLUE, "#FFF3C4": YEL, "#BFC6D6": "#6F6A99", "#C4C8D8": "#7F7AA8"}


def nc(col):
    """The colour to really use: on the neon stage dark inks become light, white pieces become lavender."""
    return NEON_MAP.get(col, col) if STYLE == "neon" else col



# ---------------------------------------------------------------- defs registry
class Defs:
    def __init__(self):
        self.d = {}

    def add(self, key, svg):
        self.d.setdefault(key, svg)
        return key

    def svg(self):
        return "<defs>" + "".join(self.d.values()) + "</defs>"


D = Defs()


def _h(*parts):
    return hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:10]


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mixc(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return "#" + "".join(f"{round(ra[i] + (rb[i] - ra[i]) * t):02X}" for i in range(3))


def darker(c, t=.25):
    return mixc(c, "#000000", t)


def lighter(c, t=.35):
    return mixc(c, "#FFFFFF", t)


def _stops(stops):
    return "".join(f'<stop offset="{s[0]}" stop-color="{s[1]}"' + (f' stop-opacity="{s[2]}"' if len(s) > 2 else "") + "/>" for s in stops)


def lg(stops, x1=0, y1=0, x2=0, y2=1, user=False):
    k = "lg" + _h(stops, x1, y1, x2, y2, user)
    u = ' gradientUnits="userSpaceOnUse"' if user else ""
    D.add(k, f'<linearGradient id="{k}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{u}>{_stops(stops)}</linearGradient>')
    return f"url(#{k})"


def rg(stops, cx=.5, cy=.5, r=.5, fx=None, fy=None, user=False):
    k = "rg" + _h(stops, cx, cy, r, fx, fy, user)
    u = ' gradientUnits="userSpaceOnUse"' if user else ""
    f = f' fx="{fx}" fy="{fy}"' if fx is not None else ""
    D.add(k, f'<radialGradient id="{k}" cx="{cx}" cy="{cy}" r="{r}"{f}{u}>{_stops(stops)}</radialGradient>')
    return f"url(#{k})"


def clip(d):
    k = "cp" + _h(d)
    D.add(k, f'<clipPath id="{k}"><path d="{d}"/></clipPath>')
    return f"url(#{k})"


def blur(sd):
    k = "bl" + str(sd).replace(".", "_")
    D.add(k, f'<filter id="{k}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{sd}"/></filter>')
    return f"url(#{k})"


def glow(col, sd=4):
    k = "gw" + _h(col, sd)
    D.add(k, f'<filter id="{k}" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="{sd}" result="b"/>'
               f'<feFlood flood-color="{col}" flood-opacity=".9"/><feComposite in2="b" operator="in" result="g"/>'
               f'<feMerge><feMergeNode in="g"/><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    return f"url(#{k})"


# ================================================================ PATHS
def ell_d(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return f"M{cx - rx:.1f},{cy:.1f} A{rx:.1f},{ry:.1f} 0 1 0 {cx + rx:.1f},{cy:.1f} A{rx:.1f},{ry:.1f} 0 1 0 {cx - rx:.1f},{cy:.1f}Z"


def rr_d(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    return (f"M{x + r:.1f},{y:.1f} H{x + w - r:.1f} A{r},{r} 0 0 1 {x + w:.1f},{y + r:.1f} V{y + h - r:.1f} A{r},{r} 0 0 1 {x + w - r:.1f},{y + h:.1f} "
            f"H{x + r:.1f} A{r},{r} 0 0 1 {x:.1f},{y + h - r:.1f} V{y + r:.1f} A{r},{r} 0 0 1 {x + r:.1f},{y:.1f}Z")


def saus_d(x1, y1, x2, y2, r):
    """A sausage: a thick line with round ends (a twisted balloon segment)."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * r, dx / L * r
    return (f"M{x1 + nx:.1f},{y1 + ny:.1f} L{x2 + nx:.1f},{y2 + ny:.1f} A{r},{r} 0 0 0 {x2 - nx:.1f},{y2 - ny:.1f} "
            f"L{x1 - nx:.1f},{y1 - ny:.1f} A{r},{r} 0 0 0 {x1 + nx:.1f},{y1 + ny:.1f}Z")


def poly_d(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"


def star_d(cx, cy, R, r=None, n=5):
    r = R * .5 if r is None else r
    pts = []
    for i in range(2 * n):
        a = math.radians(-90 + 180 * i / n)
        rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return poly_d(pts)


def heart_d(cx, cy, s):
    pts = []
    for i in range(48):
        t = 2 * math.pi * i / 48
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s / 16, cy + y * s / 16))
    return poly_d(pts)


# ================================================================ THE BALLOON KIT (and the two other styles)
def blob(d, bb, col, sh=1, knot=None, op=1.0, gloss=True, extra=""):
    """One inflated piece. d: path; bb: (x, y, w, h) of the path; sh: 0 none, 1 resting, 2 lifted (buttons).
    knot: (x, y) of the tied end, if it should show."""
    x, y, w, h = bb
    if STYLE == "neon":
        return neon(d, nc(col), extra)
    if STYLE == "glass":
        return glass(d, bb, col, extra)
    o = []
    if sh:
        dy, sd, so = {1: (5, 3, .22), 2: (10, 6, .25), 3: (16, 9, .25)}[sh]
        o.append(f'<path d="{d}" fill="#3B2A55" opacity="{so}" transform="translate({dy * .3:.1f} {dy})" filter="{blur(sd)}"/>')
    fill = rg([(0, lighter(col, .5)), (.35, col), (.82, darker(col, .18)), (1, darker(col, .38))], .42, .36, .78, .32, .25)
    o.append(f'<path d="{d}" fill="{fill}" opacity="{op}"{extra}/>')
    cp = clip(d)
    o.append(f'<g clip-path="{cp}">'
             f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-opacity=".55" stroke-width="{max(2, min(w, h) * .09):.1f}" transform="translate({-min(w, h) * .05:.1f} {-min(w, h) * .05:.1f})" filter="{blur(1.2)}"/>'
             f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-opacity=".28" stroke-width="{max(2, min(w, h) * .08):.1f}" transform="translate({min(w, h) * .06:.1f} {min(w, h) * .06:.1f})" filter="{blur(1.5)}"/></g>')
    if gloss:
        if w > 1.8 * h:        # a wide piece: a soft pill along the top left
            gx, gy, rx, ry, rot = x + w * .18, y + h * .22, min(w * .13, 40), min(h * .09, 8), 0
        elif h > 1.8 * w:      # a tall piece: a pill down the left side
            gx, gy, rx, ry, rot = x + w * .3, y + h * .2, w * .1, h * .09, 0
        else:
            gx, gy, rx, ry, rot = x + w * .32, y + h * .25, min(w * .14, 34), min(h * .09, 14), -28
        o.append(f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#FFFFFF" opacity=".85" transform="rotate({rot} {gx:.1f} {gy:.1f})" filter="{blur(.7)}"/>')
        o.append(f'<circle cx="{x + w * .2:.1f}" cy="{y + h * .45:.1f}" r="{min(w, h) * .045:.1f}" fill="#FFFFFF" opacity=".75"/>')
    if knot:
        kx, ky = knot
        o.append(f'<path d="{ell_d(kx, ky, 3.2, 2.4)}" fill="{darker(col, .3)}"/><path d="M{kx - 2:.1f},{ky:.1f} l-1.5,4 h7 l-1.5,-4Z" fill="{darker(col, .2)}"/>')
    return "".join(o)


def neon(d, col, extra=""):
    fill = rg([(0, col, .1), (.7, col, .18), (1, col, .42)], .5, .5, .62)
    return (f'<path d="{d}" fill="{fill}"{extra}/>'
            f'<path d="{d}" fill="none" stroke="{col}" stroke-width="7" stroke-opacity=".45" stroke-linejoin="round" filter="{blur(3)}"/>'
            f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-width="1.1" stroke-opacity=".85" stroke-linejoin="round"/>')


def glass(d, bb, col, extra=""):
    x, y, w, h = bb
    fill = lg([(0, lighter(col, .45)), (.5, col), (1, darker(col, .12))], 0, 0, 1, 1)
    cp = clip(d)
    streak = f'<path d="M{x - w:.1f},{y + h * .2:.1f} L{x + w * .6:.1f},{y - h:.1f} L{x + w * .9:.1f},{y - h:.1f} L{x - w * .7:.1f},{y + h * .6:.1f}Z" fill="#FFFFFF" opacity=".32"/>'
    return (f'<path d="{d}" fill="{fill}" fill-opacity=".88"{extra}/>'
            f'<g clip-path="{cp}">{streak}</g>'
            f'<path d="{d}" fill="none" stroke="#3A2E3C" stroke-width="4" stroke-linejoin="round"/>')


def bell(cx, cy, rx, ry=None, col=RED, rot=0.0, sh=1, knot=False, op=1.0, gloss=True):
    ry = rx if ry is None else ry
    o = blob(ell_d(cx, cy, rx, ry), (cx - rx, cy - ry, 2 * rx, 2 * ry), col, sh, (cx, cy + ry) if knot else None, op, gloss)
    return f'<g transform="rotate({rot:.1f} {cx:.1f} {cy:.1f})">{o}</g>' if rot else o


def brect(x, y, w, h, r, col, sh=1, op=1.0, gloss=True):
    return blob(rr_d(x, y, w, h, r), (x, y, w, h), col, sh, None, op, gloss)


def bsaus(x1, y1, x2, y2, r, col, sh=1):
    return blob(saus_d(x1, y1, x2, y2, r), (min(x1, x2) - r, min(y1, y2) - r, abs(x2 - x1) + 2 * r, abs(y2 - y1) + 2 * r), col, sh, gloss=False) + _saus_gloss(x1, y1, x2, y2, r)


def _saus_gloss(x1, y1, x2, y2, r):
    if STYLE != "balloon":
        return ""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * r * .45, dx / L * r * .45
    return f'<path d="M{x1 + dx * .15 + nx:.1f},{y1 + dy * .15 + ny:.1f} L{x1 + dx * .85 + nx:.1f},{y1 + dy * .85 + ny:.1f}" stroke="#FFFFFF" stroke-opacity=".7" stroke-width="{r * .45:.1f}" stroke-linecap="round" filter="{blur(.8)}"/>'


def bpath(d, bb, col, sh=1, gloss=True):
    return blob(d, bb, col, sh, None, 1.0, gloss)


def flat(d, col, op=1.0, extra=""):
    if STYLE == "neon":
        col = nc(col)
        return f'<path d="{d}" fill="{col}" fill-opacity="{op * .9:.2f}" filter="{glow(col, 2)}"{extra}/>'
    return f'<path d="{d}" fill="{col}" fill-opacity="{op}"{extra}/>'


def stroke(d, col, w, op=1.0, cap="round", dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    col = nc(col)
    f = f' filter="{glow(col, 2)}"' if STYLE == "neon" else ""
    return f'<path d="{d}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="round"{da}{f}/>'


def text(x, y, s, size=18, col=INK, anchor="middle", weight="normal", op=1.0, extra=""):
    col = nc(col)
    return f'<text x="{x}" y="{y}" font-family="Huninn, sans-serif" font-size="{size}" fill="{col}" text-anchor="{anchor}" font-weight="{weight}" opacity="{op}"{extra}>{s}</text>'


# ---------------------------------------------------------------- faces
def eye(cx, cy, r, look=(0, 0), wide=False):
    rr = r * 1.25 if wide else r
    if STYLE == "neon":
        o = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * 1.35:.1f}" fill="#FFFFFF" filter="{glow("#FFFFFF", 2)}"/>'
        o += f'<circle cx="{cx + look[0] * .6:.1f}" cy="{cy + look[1] * .6:.1f}" r="{rr * .7:.1f}" fill="{NEON_BG[0]}"/>'
        o += f'<circle cx="{cx + look[0] * .6 - rr * .25:.1f}" cy="{cy + look[1] * .6 - rr * .25:.1f}" r="{rr * .22:.1f}" fill="#FFFFFF"/>'
        return o
    o = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * 1.35:.1f}" fill="#FFFFFF"/>' if wide else ""
    o += f'<circle cx="{cx + look[0]:.1f}" cy="{cy + look[1]:.1f}" r="{r:.1f}" fill="{DARK}"/>'
    o += f'<circle cx="{cx + look[0] - r * .33:.1f}" cy="{cy + look[1] - r * .33:.1f}" r="{r * .36:.1f}" fill="#FFFFFF"/>'
    return o


def happy_eye(cx, cy, r):
    return stroke(f"M{cx - r:.1f},{cy + r * .3:.1f} Q{cx:.1f},{cy - r * 1.1:.1f} {cx + r:.1f},{cy + r * .3:.1f}", DARK, 2.6)


def cheeks(cx, cy, dx, r):
    if STYLE == "neon":
        return flat(ell_d(cx - dx, cy, r, r * .8), CHEEK, .7) + flat(ell_d(cx + dx, cy, r, r * .8), CHEEK, .7)
    return f'<circle cx="{cx - dx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{CHEEK}" opacity=".6"/><circle cx="{cx + dx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{CHEEK}" opacity=".6"/>'


def mouth(cx, cy, w, mood="smile"):
    if mood == "sing":
        return flat(ell_d(cx, cy + 2, w * .55, w * .65), "#B5405A" if STYLE != "neon" else PINK) + flat(ell_d(cx, cy + 5, w * .3, w * .25), "#FF8FA3")
    if mood == "freeze":
        return stroke(f"M{cx - w * .5:.1f},{cy + 1} L{cx + w * .5:.1f},{cy + 1}", DARK, 2.4)
    if mood == "sleep":
        return stroke(f"M{cx - w * .3:.1f},{cy} Q{cx:.1f},{cy + 3} {cx + w * .3:.1f},{cy}", DARK, 2)
    return stroke(f"M{cx - w:.1f},{cy:.1f} Q{cx:.1f},{cy + w * .9:.1f} {cx + w:.1f},{cy:.1f}", DARK, 2.4)


def face(cx, cy, s=1.0, mood="smile", look=(0, 0)):
    o = []
    if mood == "happy" or mood == "sing":
        o.append(happy_eye(cx - 6 * s, cy, 3 * s) + happy_eye(cx + 6 * s, cy, 3 * s))
    elif mood == "freeze":
        o.append(eye(cx - 6 * s, cy, 2.6 * s, look, wide=True) + eye(cx + 6 * s, cy, 2.6 * s, look, wide=True))
    elif mood == "sleep":
        o.append(stroke(f"M{cx - 9 * s},{cy} Q{cx - 6 * s},{cy + 3 * s} {cx - 3 * s},{cy} M{cx + 3 * s},{cy} Q{cx + 6 * s},{cy + 3 * s} {cx + 9 * s},{cy}", DARK, 2.2))
    else:
        o.append(eye(cx - 6 * s, cy, 3 * s, look) + eye(cx + 6 * s, cy, 3 * s, look))
    o.append(mouth(cx, cy + 7 * s, 5 * s, mood))
    o.append(cheeks(cx, cy + 6 * s, 11 * s, 3 * s))
    return "".join(o)


# ---------------------------------------------------------------- music bits
def note(cx, cy, s=1.0, col=INK, rot=0.0):
    """A single quaver."""
    col = nc(col)
    d = (f"{ell_d(cx - 4 * s, cy + 6 * s, 5 * s, 3.6 * s)} M{cx + .2 * s:.1f},{cy + 5 * s:.1f} V{cy - 12 * s:.1f} "
         f"Q{cx + 9 * s:.1f},{cy - 10 * s:.1f} {cx + 8 * s:.1f},{cy - 1 * s:.1f} Q{cx + 7 * s:.1f},{cy - 7 * s:.1f} {cx + .2 * s:.1f},{cy - 8 * s:.1f}Z")
    o = f'<g transform="rotate({rot} {cx} {cy})"><path d="{ell_d(cx - 4 * s, cy + 6 * s, 5 * s, 3.6 * s)}" fill="{col}" transform="rotate(-20 {cx - 4 * s} {cy + 6 * s})"/>'
    o += stroke(f"M{cx + .5 * s:.1f},{cy + 5 * s:.1f} V{cy - 12 * s:.1f}", col, 2.4 * s)
    o += f'<path d="M{cx + .5 * s:.1f},{cy - 12 * s:.1f} Q{cx + 10 * s:.1f},{cy - 9 * s:.1f} {cx + 7 * s:.1f},{cy + 1 * s:.1f} Q{cx + 8 * s:.1f},{cy - 5 * s:.1f} {cx + .5 * s:.1f},{cy - 6 * s:.1f}Z" fill="{col}"/></g>'
    return o


def sparkle(cx, cy, r, col=YEL, op=1.0):
    return (f'<path d="M{cx},{cy - r} Q{cx + r * .16},{cy - r * .16} {cx + r},{cy} Q{cx + r * .16},{cy + r * .16} {cx},{cy + r} '
            f'Q{cx - r * .16},{cy + r * .16} {cx - r},{cy} Q{cx - r * .16},{cy - r * .16} {cx},{cy - r}Z" fill="{col}" opacity="{op}"/>')


def confetti(seed, n, x0, y0, x1, y1, s=1.0):
    o = []
    rnd = _rand(seed)
    for i in range(n):
        x = x0 + (x1 - x0) * rnd()
        y = y0 + (y1 - y0) * rnd()
        c = NOTE_COLS[int(rnd() * 8)]
        k = rnd()
        if k < .4:
            o.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{7 * s}" height="{4 * s}" rx="1.5" fill="{c}" opacity=".8" transform="rotate({rnd() * 360:.0f} {x:.0f} {y:.0f})"/>')
        elif k < .7:
            o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{3 * s}" fill="{c}" opacity=".8"/>')
        else:
            o.append(sparkle(x, y, 5 * s, c, .8))
    return "".join(o)


def _rand(seed):
    st = [seed * 9301 + 49297]

    def r():
        st[0] = (st[0] * 1103515245 + 12345) % 2147483648
        return st[0] / 2147483648
    return r


def finger(x, y, rot=-25.0, drag=None):
    """A see-through grown-up fingertip pressing at (x, y). drag: (dx, dy) draws a motion arrow."""
    o = ""
    if drag:
        dx, dy = drag
        o += stroke(f"M{x - dx:.1f},{y - dy:.1f} L{x - dx * .25:.1f},{y - dy * .25:.1f}", "#FFFFFF", 7, .9, dash="2 11")
        o += stroke(f"M{x - dx:.1f},{y - dy:.1f} L{x - dx * .25:.1f},{y - dy * .25:.1f}", INK, 3.5, .6, dash="2 11")
    o += (f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot})">'
          f'<circle cx="0" cy="0" r="34" fill="#FFFFFF" opacity=".4"/>'
          f'<path d="{saus_d(0, 0, 0, 96, 24)}" fill="#FFE1CF" fill-opacity=".66" stroke="#D99D82" stroke-opacity=".6" stroke-width="2"/>'
          f'<path d="M-12,-8 Q0,-17 12,-8 L12,8 Q0,14 -12,8Z" fill="#FFFFFF" fill-opacity=".55"/>'
          f'<path d="M-16,10 Q-18,40 -14,64" stroke="#FFFFFF" stroke-opacity=".6" stroke-width="4" fill="none" stroke-linecap="round"/></g>')
    return o


# ================================================================ BALLOON ANIMALS (feet at (0, 0), about 90 units tall, facing the viewer)
def a_frog(mood="smile", look=(0, 0)):
    o = [bell(-16, -8, 15, 8, GRN, sh=1), bell(16, -8, 15, 8, GRN, sh=1)]              # feet
    o.append(bell(0, -38, 34, 28, GRN, knot=True))                                      # body
    o.append(flat(ell_d(0, -30, 20, 12), lighter(GRN, .55), .8))
    for sx in (-1, 1):
        o.append(bell(sx * 16, -66, 12, 12, GRN))
        o.append(eye(sx * 16, -66, 4.5, look))
    o.append(mouth(0, -46, 11, "sing" if mood == "sing" else mood))
    o.append(cheeks(0, -42, 20, 4))
    return "".join(o)


def a_bird(mood="smile", look=(0, 0), col=BLUE, magpie=False):
    o = [stroke("M-8,0 L-8,-10 M-14,0 L-8,-8 M-2,0 L-8,-8 M10,0 L10,-10 M4,0 L10,-8 M16,0 L10,-8", ORA if not magpie else RED, 3)]
    if magpie:   # the long blue tail with white tips
        o.append(bsaus(-18, -28, -52, -4, 6, col) + bsaus(-14, -22, -44, 4, 5, col) + flat(ell_d(-52, -4, 6, 5), "#FFFFFF", .9) + flat(ell_d(-44, 4, 5, 4), "#FFFFFF", .9))
    o.append(bell(0, -34, 24, 26, col, knot=True))                                       # body
    o.append(bell(-22, -40, 13, 8, darker(col, .1), rot=-30, sh=0))                     # wing
    o.append(bell(5, -64, 19, 18, col))                                                  # head
    o.append(bell(2, -78, 5, 7, lighter(col, .2), rot=-20, sh=0))                       # crest
    o.append(bpath("M18,-60 L34,-54 L18,-50Z", (18, -60, 16, 10), ORA if not magpie else RED, sh=0, gloss=False))
    if magpie:   # dark head, white belly
        o.append(flat(ell_d(5, -70, 15, 11), "#2B2A48" if STYLE != "neon" else "#6A66A8", .8))
        o.append(flat(ell_d(2, -28, 14, 12), "#FFFFFF", .6))
    o.append(eye(2, -66, 3.6, look) + eye(12, -66, 3.6, look) if mood != "sing" else happy_eye(2, -66, 3) + happy_eye(12, -66, 3))
    o.append(cheeks(7, -58, 10, 3))
    if mood == "sing":
        o.append(flat(ell_d(22, -56, 5, 4), PINK))
    return "".join(o)


def a_dog(mood="smile", look=(0, 0), col=YEL):
    """The classic twisted balloon dog, side on, facing right."""
    o = []
    for lx in (-28, -14, 16, 30):
        o.append(bsaus(lx, -28, lx, -6, 6, col))
    o.append(bsaus(-30, -34, 30, -34, 12, col))                                          # body
    o.append(bsaus(-32, -40, -46, -58, 6, col))                                          # tail
    o.append(bsaus(32, -40, 40, -60, 9, col))                                            # neck
    o.append(bsaus(40, -66, 58, -62, 10, col))                                           # head
    o.append(bsaus(36, -74, 30, -92, 6, col) + bsaus(48, -76, 52, -94, 6, col))         # ears
    o.append(flat(ell_d(60, -64, 3.5, 3.5), DARK))
    o.append(eye(47, -70, 3.2, look) if mood != "sing" else happy_eye(47, -70, 3))
    o.append(mouth(56, -58, 4, "sing" if mood == "sing" else "smile"))
    o.append(cheeks(47, -62, 0, 3))
    return "".join(o)


def a_cat(mood="smile", look=(0, 0), col=ORA, leopard=False):
    o = [bell(-13, -7, 12, 7, col, sh=1), bell(13, -7, 12, 7, col, sh=1)]
    o.append(bsaus(26, -24, 44, -48, 6, col))                                            # tail
    o.append(bell(0, -36, 28, 26, col, knot=True))
    o.append(flat(ell_d(0, -30, 16, 12), lighter(col, .6), .85))
    if leopard:   # spots on the body, white spots behind the ears
        for (px, py) in ((-14, -40), (8, -46), (18, -30), (-6, -22), (34, -40)):
            o.append(flat(ell_d(px, py, 4, 3), darker(col, .45), .8))
    o.append(bell(0, -70, 23, 21, col))
    for sx in (-1, 1):
        o.append(bpath(f"M{sx * 8},-86 L{sx * 20},-100 L{sx * 22},-82Z", (min(sx * 8, sx * 22), -100, 14, 18), col, sh=0, gloss=False))
        if leopard:
            o.append(flat(ell_d(sx * 16, -90, 3, 3), "#FFFFFF", .9))
    if leopard:
        o.append(stroke("M-10,-84 L-6,-78 M10,-84 L6,-78", "#FFFFFF", 2.5, .9))
    o.append(face(0, -73, .9, mood, look))
    o.append(stroke("M-24,-66 L-36,-68 M-24,-62 L-36,-60 M24,-66 L36,-68 M24,-62 L36,-60", DARK, 1.6, .7))
    return "".join(o)


def a_bear(mood="smile", look=(0, 0), col=BROWN, formosan=False):
    o = [bell(-14, -8, 13, 8, col, sh=1), bell(14, -8, 13, 8, col, sh=1)]
    o.append(bell(0, -38, 30, 28, col, knot=True))
    if formosan:   # the white V on the chest
        o.append(stroke("M-14,-50 L0,-32 L14,-50", "#FFFFFF", 5))
    else:
        o.append(flat(ell_d(0, -32, 17, 13), lighter(col, .55), .85))
    for sx in (-1, 1):
        o.append(bsaus(sx * 24, -50, sx * 38, -34, 7, col))                              # arms
        o.append(bell(sx * 20, -94, 9, 9, col))                                          # ears
    o.append(bell(0, -74, 25, 23, col))
    o.append(flat(ell_d(0, -68, 11, 8), lighter(col, .55), .9))
    o.append(flat(ell_d(0, -71, 4, 3), DARK))
    o.append(eye(-8, -78, 3.2, look) + eye(8, -78, 3.2, look) if mood != "sing" else happy_eye(-8, -78, 3) + happy_eye(8, -78, 3))
    o.append(mouth(0, -66, 4, "sing" if mood == "sing" else "smile"))
    o.append(cheeks(0, -70, 15, 3.5))
    return "".join(o)


def a_elephant(mood="smile", look=(0, 0), col=PURP):
    o = [bell(-16, -8, 13, 8, col, sh=1), bell(16, -8, 13, 8, col, sh=1)]
    o.append(bell(0, -38, 32, 28, col, knot=True))
    for sx in (-1, 1):
        o.append(bell(sx * 30, -74, 15, 17, lighter(col, .15), rot=sx * 10))            # ears
    o.append(bell(0, -74, 24, 22, col))
    o.append(bsaus(0, -66, 2, -40, 6, col) + bsaus(2, -40, 14, -34, 6, col))            # trunk
    o.append(eye(-9, -78, 3.2, look) + eye(9, -78, 3.2, look) if mood != "sing" else happy_eye(-9, -78, 3) + happy_eye(9, -78, 3))
    o.append(cheeks(0, -70, 16, 3.5))
    if mood == "sing":
        o.append(flat(ell_d(16, -34, 5, 4), PINK))
    return "".join(o)


def a_duck(mood="smile", look=(0, 0), col=YEL):
    o = [bell(-10, -6, 11, 6, ORA, sh=1), bell(10, -6, 11, 6, ORA, sh=1)]
    o.append(bell(0, -32, 27, 23, col, knot=True))
    o.append(bell(-20, -36, 12, 7, darker(col, .06), rot=20, sh=0))
    o.append(bell(6, -62, 18, 17, col))
    o.append(bell(22, -58, 10, 5, ORA, sh=0))
    o.append(eye(4, -65, 3.4, look) + eye(13, -65, 3.4, look) if mood != "sing" else happy_eye(4, -65, 3) + happy_eye(13, -65, 3))
    o.append(cheeks(8, -58, 10, 3))
    return "".join(o)


def a_lion(mood="smile", look=(0, 0), col=ORA):
    o = [bell(-14, -8, 13, 8, col, sh=1), bell(14, -8, 13, 8, col, sh=1)]
    o.append(bell(0, -38, 30, 27, col, knot=True))
    for i in range(8):
        a = math.radians(i * 45)
        o.append(bell(26 * math.cos(a), -74 + 26 * math.sin(a), 11, 11, darker(col, .2), sh=0))
    o.append(bell(0, -74, 24, 22, col))
    o.append(flat(ell_d(0, -66, 10, 7), lighter(col, .55), .9))
    o.append(flat(ell_d(0, -69, 4, 3), DARK))
    o.append(eye(-8, -78, 3.2, look) + eye(8, -78, 3.2, look))
    o.append(cheeks(0, -70, 15, 3.5))
    return "".join(o)


ANIMALS = {"青蛙": a_frog, "小鳥": a_bird, "小狗": a_dog, "小貓": a_cat, "小熊": a_bear, "小象": a_elephant, "小鴨": a_duck, "獅子": a_lion,
           "台灣黑熊": lambda m, l: a_bear(m, l, "#7B76B0", True), "石虎": lambda m, l: a_cat(m, l, "#E8B04E", True),
           "藍鵲": lambda m, l: a_bird(m, l, "#4C8BF0", True)}


def animal(name, x, y, s=1.0, mood="smile", look=(0, 0), flip=False, rot=0.0):
    f = " scale(-1 1)" if flip else ""
    r = f" rotate({rot})" if rot else ""
    return f'<g transform="translate({x:.1f} {y:.1f}){r} scale({s:.3f}){f}">{ANIMALS[name](mood, look)}</g>'


# ================================================================ SHARED PARTS
def bg(top="#CFEFFF", bottom="#FFF3E0", w=W, h=H, seed=3, dots=True):
    if STYLE == "neon":
        top, bottom = NEON_BG
    o = [f'<rect width="{w}" height="{h}" fill="{lg([(0, top), (1, bottom)])}"/>']
    if dots:
        rnd = _rand(seed)
        for _ in range(28 if STYLE != "neon" else 44):
            x, y, r = rnd() * w, rnd() * h, 2 + rnd() * 3
            if STYLE == "neon":
                o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r * .45:.1f}" fill="#FFFFFF" opacity="{.35 + rnd() * .45:.2f}"/>')
            else:
                o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#FFFFFF" opacity=".5"/>')
    return "".join(o)


def curtain(x, w, h, left=True):
    """A red balloon curtain hanging from the top, gathered to one side."""
    o = []
    n = 4
    for i in range(n):
        fx = x + (i + .5) * w / n
        hh = h * (1 - .18 * (i if left else n - 1 - i))
        o.append(bell(fx, hh / 2 - 8, w / n * .62, hh / 2, RED if i % 2 == 0 else darker(RED, .08), sh=0, gloss=i % 2 == 0))
    return "".join(o)


def valance(y=0):
    o = []
    for i in range(7):
        o.append(bell(28 + i * 56, y + 10, 32, 20, RED if i % 2 == 0 else darker(RED, .08), sh=1, gloss=i % 2 == 0))
    return "".join(o)


def floor(y, h=110, col=TEAL):
    """The bouncy-castle stage floor."""
    o = [brect(-10, y, W + 20, h + 20, 36, col, sh=2)]
    for i in range(7):
        o.append(f'<rect x="{8 + i * 56}" y="{y + 10}" width="22" height="{h - 4}" rx="10" fill="#FFFFFF" opacity="{.1 if STYLE == "neon" else .14}"/>')
    return "".join(o)


def spotlight(x, col, w=120, h=420, op=.22):
    op = op * 1.6 if STYLE == "neon" else op
    return f'<path d="M{x - 10},-10 L{x + 10},-10 L{x + w / 2},{h} L{x - w / 2},{h}Z" fill="{lg([(0, col, .9), (1, col, 0)])}" opacity="{op}"/>'


def pill(x, y, w, h, col, label, size=17, tcol=INK, icon="", sh=2):
    return brect(x, y, w, h, h / 2, col, sh=sh) + icon + text(x + w / 2 + (14 if icon else 0), y + h / 2 + size * .36, label, size, tcol)


def lock_icon(cx, cy, col=SOFT):
    return stroke(f"M{cx - 5},{cy - 1} V{cy - 6} A5,5 0 0 1 {cx + 5},{cy - 6} V{cy - 1}", col, 2.6) + f'<rect x="{cx - 8}" y="{cy - 2}" width="16" height="13" rx="3" fill="{nc(col)}"/>'


def sun_timer(cx, cy, frac=.3):
    """The little sun that walks to the moon: how much of this play time is left."""
    o = [brect(cx - 52, cy - 18, 104, 36, 18, "#FFFFFF", sh=1, op=.85, gloss=False)]
    o.append(stroke(f"M{cx - 36},{cy} H{cx + 36}", GREY, 4))
    o.append(stroke(f"M{cx - 36},{cy} H{cx - 36 + 72 * frac}", YEL, 4))
    sx = cx - 36 + 72 * frac
    o.append(bell(sx, cy, 11, 11, YEL, sh=0))
    o.append(f'<path d="{ell_d(cx + 36, cy, 8, 8)}" fill="{nc(GREY)}"/><path d="{ell_d(cx + 39, cy - 2, 7, 7)}" fill="{NEON_BG[1] if STYLE == "neon" else "#FFFFFF"}"/>')
    return "".join(o)


def top_bar(frac=.3):
    return (pill(14, 44, 96, 40, "#FFFFFF", "家長", 18, INK, lock_icon(38, 64), sh=1)
            + sun_timer(318, 64, frac))


def home_btn(x=20, y=H - 96):
    o = bell(x + 28, y + 28, 28, 28, PINK, sh=2)
    o += bpath(f"M{x + 14},{y + 32} L{x + 28},{y + 18} L{x + 42},{y + 32} V{y + 42} H{x + 14}Z", (x + 14, y + 18, 28, 24), "#FFFFFF", sh=0, gloss=False)
    o += stroke(f"M{x + 12},{y + 33} L{x + 28},{y + 17} L{x + 44},{y + 33}", "#FFFFFF", 3)
    return o + text(x + 28, y + 76, "回舞台", 14, SOFT)


def speech(x, y, w, h, s, size=20, tail="left"):
    tx = x + 40 if tail == "left" else x + w - 40
    o = brect(x, y, w, h, 20, "#FFFFFF", sh=1, gloss=False)
    if STYLE == "neon":
        o += stroke(f"M{tx - 10},{y + h} L{tx},{y + h + 14} L{tx + 10},{y + h}", "#FFFFFF", 3)
    else:
        o += f'<path d="M{tx - 10},{y + h - 1} L{tx},{y + h + 14} L{tx + 10},{y + h - 1}Z" fill="#FFFFFF"/>'
    return o + text(x + w / 2, y + h / 2 + size * .36, s, size, INK)


def speaker(cx, cy, s=1.0, col=INK, waves=True):
    o = flat(f"M{cx - 14 * s},{cy - 6 * s} H{cx - 6 * s} L{cx + 2 * s},{cy - 14 * s} V{cy + 14 * s} L{cx - 6 * s},{cy + 6 * s} H{cx - 14 * s}Z", col)
    if waves:
        o += stroke(f"M{cx + 7 * s},{cy - 6 * s} A8,8 0 0 1 {cx + 7 * s},{cy + 6 * s} M{cx + 12 * s},{cy - 12 * s} A15,15 0 0 1 {cx + 12 * s},{cy + 12 * s}", col, 2.6 * s)
    return o


def xylo_key(x, y, w, h, col, pressed=False, label=""):
    sq = .9 if pressed else 1
    o = f'<g transform="translate({x + w / 2} {y + h}) scale(1 {sq}) translate({-x - w / 2} {-y - h})">'
    if pressed and STYLE == "neon":     # the key lights up
        o += f'<path d="{rr_d(x, y, w, h, w / 2)}" fill="{col}" opacity=".75" filter="{blur(6)}"/><path d="{rr_d(x, y, w, h, w / 2)}" fill="{col}" opacity=".55"/>'
    o += brect(x, y, w, h, w / 2, col, sh=2)
    o += "</g>"
    if label:
        o += text(x + w / 2, y + h - 14, label, 13, "#FFFFFF", op=.9)
    return o


def xylophone(x, y, w, n=8, top=190, step=14, pressed=None, labels=None):
    gap = 8
    kw = (w - gap * (n - 1)) / n
    o = []
    for i in range(n):
        h = top - i * step
        ky = y + (top - h)
        o.append(xylo_key(x + i * (kw + gap), ky, kw, h, NOTE_COLS[i], pressed == i, labels[i] if labels else ""))
    return "".join(o)


def mallet(x, y, rot=30):
    return (f'<g transform="rotate({rot} {x} {y})">' + bsaus(x, y, x, y + 70, 5, BROWN) + bell(x, y - 4, 13, 13, RED, sh=1) + "</g>")


def stop_hand(cx, cy, s=1.0, col="#FFFFFF"):
    d = (f"M{cx - 16 * s},{cy + 4 * s} V{cy - 10 * s} a4,4 0 0 1 8,0 V{cy - 18 * s} a4,4 0 0 1 8,0 V{cy - 20 * s} a4,4 0 0 1 8,0 V{cy - 14 * s} a4,4 0 0 1 8,0 V{cy + 6 * s} "
         f"Q{cx + 16 * s},{cy + 22 * s} {cx},{cy + 24 * s} Q{cx - 16 * s},{cy + 22 * s} {cx - 16 * s},{cy + 4 * s}Z")
    return f'<path d="{d}" fill="{col}" transform="scale({s}) translate({cx * (1 / s - 1):.1f} {cy * (1 / s - 1):.1f})"/>' if s != 1 else f'<path d="{d}" fill="{col}"/>'


def tape(cx, cy, col, cols=None, s=1.0, label=""):
    """A little cassette balloon (a saved tune)."""
    o = brect(cx - 34 * s, cy - 22 * s, 68 * s, 44 * s, 10 * s, col, sh=2)
    o += f'<rect x="{cx - 26 * s}" y="{cy - 14 * s}" width="{52 * s}" height="{18 * s}" rx="{6 * s}" fill="#FFFFFF" opacity=".75"/>'
    for sx in (-1, 1):
        o += f'<circle cx="{cx + sx * 14 * s}" cy="{cy - 5 * s}" r="{5 * s}" fill="{darker(col, .3)}"/><circle cx="{cx + sx * 14 * s}" cy="{cy - 5 * s}" r="{2 * s}" fill="#FFFFFF"/>'
    if cols:
        for i, c in enumerate(cols[:6]):
            o += f'<circle cx="{cx - 20 * s + i * 8 * s}" cy="{cy + 11 * s}" r="{3 * s}" fill="{c}"/>'
    if label:
        o += text(cx, cy + 40 * s, label, 13, SOFT)
    return o


def check_box(x, y, on, label):
    o = brect(x, y, 30, 30, 9, GRN if on else "#FFFFFF", sh=1, gloss=on)
    if on:
        o += stroke(f"M{x + 8},{y + 15} L{x + 13},{y + 21} L{x + 23},{y + 9}", "#FFFFFF", 3.5)
    return o + text(x + 42, y + 21, label, 17, INK, "start")


def toggle(x, y, on):
    o = brect(x, y, 56, 30, 15, GRN if on else GREY, sh=1, gloss=False)
    return o + bell(x + (41 if on else 15), y + 15, 11, 11, "#FFFFFF", sh=1, gloss=False)


def card(x, y, w, h, title=""):
    o = brect(x, y, w, h, 18, "#FFFFFF", sh=1, op=.92, gloss=False)
    if title:
        o += text(x + 18, y + 30, title, 18, INK, "start", "bold")
    return o


# ================================================================ SCREENS
def page(body, bgc, w=W, h=H):
    css = (f"@font-face {{ font-family: Huninn; src: url('file://{FONT}'); }}"
           f"* {{ margin: 0; padding: 0; }} body {{ width: {w}px; height: {h}px; overflow: hidden; background: {bgc}; }}")
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{D.svg()}{body}</svg>'
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{svg}</body></html>'


def render(html, out, w, h, scale):
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        p = pathlib.Path(tmp) / "page.html"
        p.write_text(html)
        subprocess.run(["node", str(HERE / "render.js"), str(p), str(out), str(w), str(h), str(scale)], check=True)
    if pathlib.Path(out).stat().st_size > 450_000:
        from PIL import Image
        im = Image.open(out).convert("RGB")
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, kmeans=2, dither=Image.Dither.FLOYDSTEINBERG).save(out, optimize=True)


def screen_home():
    o = [bg("#BFE6FF", "#FFF1DC")]
    o.append(spotlight(120, YEL, 160, 520) + spotlight(270, PINK, 160, 520))
    o.append(curtain(-6, 80, 330, True) + curtain(W - 74, 80, 330, False))
    o.append(valance(76))
    o.append(floor(372, 70, TEAL))
    # the band waving
    o.append(animal("小熊", 92, 390, .85, "happy"))
    o.append(animal("青蛙", 190, 395, .9, "sing"))
    o.append(animal("小鳥", 285, 392, .85, "sing"))
    for (nx, ny, r, c) in ((150, 250, 0, RED), (225, 232, 15, BLUE), (300, 262, -10, PURP), (120, 300, 10, GRN)):
        o.append(note(nx, ny, 1.4, c, r))
    o.append(confetti(5, 14, 40, 150, 350, 330, 1.1))
    # title balloon letters
    o.append(brect(70, 118, 250, 58, 29, "#FFFFFF", sh=2, op=.92, gloss=False))
    o.append(text(W / 2, 158, "小小音波", 34, INK, weight="bold"))
    o.append(top_bar(.3))
    # six toy buttons
    toys = [("敲敲樂", RED, "mallet"), ("動物樂團", ORA, "frog"), ("音樂木頭人", GRN, "hand"),
            ("高低快慢", BLUE, "stairs"), ("錄下來", PINK, "rec"), ("聽聽看", PURP, "ear")]
    for i, (name, col, ic) in enumerate(toys):
        r, c = divmod(i, 3)
        cx, cy = 72 + c * 123, 540 + r * 150
        o.append(bell(cx, cy, 50, 50, col, sh=2, knot=True))
        if ic == "mallet":
            o.append(f'<g transform="translate({cx - 4} {cy - 22}) scale(.75)">' + mallet(0, 0, 35) + "</g>")
        elif ic == "frog":
            o.append(animal("青蛙", cx, cy + 36, .5, "sing"))
        elif ic == "hand":
            o.append(stop_hand(cx, cy, 1.0))
        elif ic == "stairs":
            for k in range(4):
                o.append(f'<rect x="{cx - 28 + k * 14}" y="{cy + 20 - (k + 1) * 11}" width="12" height="{(k + 1) * 11}" rx="4" fill="#FFFFFF" opacity=".95"/>')
            o.append(animal("小鳥", cx + 22, cy - 24, .28, "smile"))
        elif ic == "rec":
            o.append(f'<circle cx="{cx}" cy="{cy}" r="19" fill="#FFFFFF" opacity=".95"/><circle cx="{cx}" cy="{cy}" r="11" fill="{RED}"/>')
        elif ic == "ear":
            o.append(speaker(cx - 2, cy, 1.25, "#FFFFFF"))
        o.append(text(cx, cy + 82, name, 18, INK))
    # saved tunes hint
    return page("".join(o), "#BFE6FF")


def screen_xylo():
    o = [bg("#FFF1DC", "#CFEFFF", seed=7)]
    o.append(top_bar(.35))
    o.append(text(W / 2, 125, "敲敲樂", 30, INK, weight="bold"))
    # instrument choice
    inst = [("木琴", RED, True), ("鼓", ORA, False), ("鍋碗瓢盆", TEAL, False)]
    for i, (n, c, on) in enumerate(inst):
        x = 30 + i * 115
        o.append(brect(x, 146, 102, 44, 22, c if on else "#FFFFFF", sh=2 if on else 1, gloss=on))
        o.append(text(x + 51, 176, n, 18, "#FFFFFF" if on else SOFT, weight="bold" if on else "normal"))
    # the frog bouncing above key 3
    o.append(floor(690, 60, PURP))
    o.append(animal("青蛙", 135, 330, 1.0, "sing", rot=-8))
    for (nx, ny, r, c) in ((190, 250, 10, YEL), (90, 240, -15, RED), (215, 300, 25, BLUE)):
        o.append(note(nx, ny, 1.5, c, r))
    o.append(sparkle(70, 300, 12, YEL) + sparkle(205, 215, 9, PINK) + sparkle(240, 340, 8, ORA))
    o.append(animal("小鳥", 320, 405, .7, "smile", look=(-2, 0), flip=True))
    o.append(xylophone(22, 400, W - 44, 8, 280, 16, pressed=2, labels=["Do", "Re", "Mi", "Sol", "La", "Do", "Re", "Mi"]))
    o.append(finger(128, 520, -20))
    o.append(speech(176, 196, 170, 46, "滑過去「刷～」", 17, "right"))
    o.append(home_btn())
    return page("".join(o), "#FFF1DC")


def screen_band():
    o = [bg("#BFE6FF", "#FFE9F2", seed=11)]
    o.append(spotlight(195, YEL, 300, 560, .18))
    o.append(curtain(-6, 60, 250, True) + curtain(W - 54, 60, 250, False))
    o.append(valance(44))
    o.append(text(W / 2, 128, "動物樂團", 30, INK, weight="bold"))
    # beat dots
    for i in range(4):
        o.append(bell(150 + i * 30, 152, 9, 9, ORA if i == 1 else "#FFFFFF", sh=1, gloss=i == 1))
    # tempo balloon
    o.append(bell(338, 108, 30, 30, GRN, sh=2))
    o.append(f'<path d="{ell_d(338, 112, 11, 8)}" fill="#FFFFFF"/><path d="{ell_d(338, 112, 6, 4)}" fill="{GRN}"/>' + stroke("M330,104 Q326,96 322,100 M346,104 Q350,96 354,100", "#FFFFFF", 3))
    o.append(text(338, 154, "慢·中·快", 12, SOFT))
    o.append(floor(400, 228, TEAL))
    # slots: 3 back, 3 front
    slots = [(90, 480), (195, 472), (300, 480), (120, 600), (270, 600), (195, 640)]
    occupied = {0: "小熊", 1: "小鳥", 2: "小狗"}
    for i, (sx, sy) in enumerate(slots):
        glow_ = i == 4
        o.append(f'<ellipse cx="{sx}" cy="{sy}" rx="46" ry="16" fill="{YEL if glow_ else "#FFFFFF"}" opacity="{.75 if glow_ else .35}"/>')
        if glow_:
            o.append(f'<ellipse cx="{sx}" cy="{sy}" rx="54" ry="20" fill="none" stroke="{YEL}" stroke-width="4" stroke-dasharray="8 7" opacity=".9"/>')
    o.append(animal("小熊", 90, 480, .8, "sing"))
    o.append(animal("小鳥", 195, 472, .8, "sing"))
    o.append(f'<g opacity=".7">' + animal("小狗", 285, 478, .75, "smile") + "</g>")
    o.append(bell(330, 395, 16, 16, "#FFFFFF", sh=1, gloss=False) + speaker(328, 395, .8, SOFT, waves=False) + stroke("M320,385 L340,405", RED, 3))
    for (nx, ny, r, c) in ((60, 350, -10, BROWN), (215, 340, 10, BLUE), (330, 360, 20, YEL), (150, 300, 0, GRN)):
        o.append(note(nx, ny, 1.3, c, r))
    o.append(speech(40, 236, 180, 44, "噓～小狗先不唱", 16, "right"))
    o.append(stroke("M225,280 Q290,310 318,380", SOFT, 2, .5, dash="4 6"))
    # the cat being dragged to the glowing slot
    o.append(animal("小貓", 262, 610, .8, "smile", look=(0, 2)))
    o.append(finger(286, 590, -25, drag=(40, 110)))
    # tray: the six animals not on stage yet
    o.append(brect(14, 652, W - 28, 92, 26, "#FFFFFF", sh=1, op=.9, gloss=False))
    o.append(text(W / 2, 672, "拖一隻上台（一共 10 隻）", 13, SOFT))
    for i, nm in enumerate(["青蛙", "小象", "小鴨", "台灣黑熊", "石虎", "藍鵲"]):
        o.append(animal(nm, 46 + i * 60, 738, .42, "smile"))
    o.append(home_btn(16, 756))
    o.append(text(W / 2 + 30, 812, "小小 4 個位子，大 6 個", 13, SOFT))
    return page("".join(o), "#BFE6FF")


def screen_freeze():
    o = [bg("#DCE6FF", "#FFE9D6", seed=13)]
    o.append(spotlight(195, BLUE, 320, 560, .16))
    o.append(curtain(-6, 60, 220, True) + curtain(W - 54, 60, 220, False))
    o.append(valance(44))
    o.append(text(W / 2, 128, "音樂木頭人", 30, INK, weight="bold"))
    # traffic balloons
    o.append(bell(56, 172, 24, 24, RED, sh=2) + bell(56, 228, 22, 22, "#BFC6D6", sh=1, gloss=False))
    o.append(text(56, 268, "停", 15, RED) )
    o.append(floor(560, 100, PURP))
    # frozen animals mid-dance
    o.append(animal("青蛙", 110, 540, .95, "freeze", look=(3, -1), rot=-12))
    o.append(animal("小鳥", 300, 540, .9, "freeze", look=(-3, 0), rot=12))
    o.append(animal("小熊", 205, 610, .95, "freeze", look=(0, -2)))
    o.append(animal("小貓", 345, 640, .8, "freeze", look=(-3, 0)))
    # grey (silent) notes
    for (nx, ny, r) in ((70, 380, -10), (330, 400, 15), (240, 350, 5)):
        o.append(note(nx, ny, 1.3, "#C4C8D8", r))
    # the big STOP balloon
    o.append(bell(W / 2, 330, 92, 92, RED, sh=3, knot=True))
    o.append(f'<g transform="translate({W / 2} 296) scale(1.5) translate({-W / 2} -296)">' + stop_hand(W / 2, 296) + "</g>")
    o.append(text(W / 2, 395, "停！", 44, "#FFFFFF", weight="bold"))
    o.append(speech(70, 178, 250, 46, "停！不要動～手也不要動", 16, "left"))
    # the finger waits (hovering, not touching)
    o.append(f'<g opacity=".55">' + finger(300, 760, -25) + "</g>")
    o.append(text(300, 700, "忍住，不要點", 15, SOFT))
    o.append(stroke("M270,712 Q300,730 300,745", SOFT, 2, .5, dash="3 5"))
    o.append(home_btn())
    return page("".join(o), "#DCE6FF")


def screen_pitch():
    o = [bg("#FFF1DC", "#D8F5EC", seed=17)]
    o.append(top_bar(.6))
    o.append(text(W / 2, 125, "高低快慢", 30, INK, weight="bold"))
    # balloon stairs
    cols = [RED, ORA, YEL, GRN, BLUE]
    for i in range(5):
        x, h = 40 + i * 60, 60 + i * 60
        o.append(brect(x, 480 - h, 54, h, 20, cols[i], sh=2))
    o.append(animal("小鳥", 247, 240, .95, "sing"))
    o.append(finger(262, 238, 35))
    o.append(stroke("M180,330 V266", "#FFFFFF", 7, .9, dash="2 9") + stroke("M180,330 V266", INK, 3.5, .6, dash="2 9") + flat("M180,250 L170,266 H190Z", INK, .7))
    o.append(note(312, 160, 1.5, BLUE, 15) + note(345, 212, 1.3, GRN, -10) + note(290, 110, 1.2, YEL, 0))
    o.append(speech(40, 150, 150, 46, "高～", 24, "right"))
    o.append(text(67, 470, "低", 18, "#FFFFFF", weight="bold") + text(307, 230, "高", 18, "#FFFFFF", weight="bold"))
    # tempo slider: snail to rabbit
    o.append(card(20, 520, W - 40, 110))
    o.append(text(40, 550, "快慢", 18, INK, "start", "bold"))
    o.append(brect(100, 580, 190, 14, 7, GREY, sh=0, gloss=False))
    o.append(brect(100, 580, 85, 14, 7, GRN, sh=0, gloss=False))
    o.append(bell(185, 587, 18, 18, "#FFFFFF", sh=2, gloss=False))
    # snail
    o.append(bell(60, 586, 12, 12, ORA, sh=1) + bsaus(50, 596, 76, 596, 6, YEL) + stroke("M76,592 L80,580 M72,592 L74,580", YEL, 2.5) + eye(78, 594, 2) + text(62, 622, "慢", 13, SOFT))
    # rabbit
    o.append(bell(330, 592, 15, 13, "#FFFFFF", sh=1, gloss=False) + bsaus(322, 582, 318, 562, 4.5, "#FFFFFF") + bsaus(336, 582, 342, 562, 4.5, "#FFFFFF") + eye(326, 590, 2) + eye(336, 590, 2) + cheeks(331, 596, 7, 2) + text(330, 622, "快", 13, SOFT))
    # loud / soft
    o.append(card(20, 648, W - 40, 110))
    o.append(text(40, 678, "大小聲", 18, INK, "start", "bold"))
    o.append(brect(130, 660, 110, 84, 24, PURP, sh=2))
    o.append(animal("小象", 185, 740, .48, "sing"))
    o.append(brect(255, 660, 110, 84, 24, "#FFFFFF", sh=1, gloss=False))
    o.append(bell(310, 712, 16, 13, GREY, sh=0, gloss=False) + bell(300, 700, 6, 9, PINK, rot=-20, sh=0, gloss=False) + bell(320, 700, 6, 9, PINK, rot=20, sh=0, gloss=False) + eye(305, 712, 2) + eye(315, 712, 2) + stroke("M326,718 Q340,724 344,714", GREY, 2.5))
    o.append(speaker(60, 712, 1.2, PURP))
    o.append(home_btn())
    return page("".join(o), "#FFF1DC")


def screen_record():
    o = [bg("#FFE9F2", "#CFEFFF", seed=19)]
    o.append(top_bar(.45))
    o.append(text(W / 2, 125, "錄下來", 30, INK, weight="bold"))
    # record and play buttons
    o.append(f'<circle cx="120" cy="196" r="46" fill="{RED}" opacity=".25"/>')
    o.append(bell(120, 196, 36, 36, RED, sh=2, knot=True))
    o.append(f'<circle cx="120" cy="196" r="13" fill="#FFFFFF"/>')
    o.append(text(120, 252, "錄", 16, INK))
    o.append(bell(270, 196, 36, 36, GRN, sh=2, knot=True))
    o.append(f'<path d="M260,180 L286,196 L260,212Z" fill="#FFFFFF"/>')
    o.append(text(270, 252, "放", 16, INK))
    # the tape: 8 beats
    o.append(card(16, 268, W - 32, 118))
    o.append(text(30, 292, "磁帶：8 格（小小 4 格）", 13, SOFT, "start"))
    hits = {0: RED, 1: YEL, 3: GRN, 4: BLUE, 6: YEL}
    for i in range(8):
        x = 30 + i * 43
        cur = i == 4
        o.append(f'<rect x="{x}" y="306" width="36" height="62" rx="10" fill="{"#FFF3C4" if cur else "#F2F3F8"}" stroke="{YEL if cur else "#E3E6EF"}" stroke-width="{3 if cur else 1.5}"/>')
        if i in hits:
            o.append(bell(x + 18, 337, 13, 13, hits[i], sh=1))
    o.append(f'<path d="M{30 + 4 * 43 + 18},300 l-7,-10 h14Z" fill="{RED}"/>')
    # animals performing the tape
    o.append(animal("小鳥", 70, 470, .62, "sing") + animal("青蛙", 180, 475, .62, "sing") + animal("小貓", 300, 472, .62, "smile"))
    o.append(note(110, 400, 1.2, BLUE, -10) + note(225, 395, 1.2, GRN, 10))
    # small xylophone
    o.append(xylophone(22, 488, W - 44, 8, 120, 7, pressed=4, labels=None))
    o.append(finger(222, 570, -20))
    # saved tapes
    o.append(brect(14, 640, W - 28, 100, 26, "#FFFFFF", sh=1, op=.9, gloss=False))
    o.append(text(W / 2, 660, "我的小曲子", 15, INK, weight="bold"))
    o.append(tape(70, 700, PINK, [RED, YEL, GRN, BLUE, YEL], .8) + tape(160, 700, BLUE, [GRN, GRN, RED, PURP], .8) + tape(250, 700, YEL, [BLUE, RED, YEL], .8))
    o.append(brect(312, 683, 50, 34, 10, "#F2F3F8", sh=0, gloss=False) + text(337, 708, "＋", 20, SOFT))
    o.append(home_btn())
    return page("".join(o), "#FFE9F2")


def pic_card(x, y, w, h, col, on=False):
    o = brect(x, y, w, h, 24, col, sh=2 if on else 1, gloss=True)
    if on:
        o += f'<rect x="{x - 5}" y="{y - 5}" width="{w + 10}" height="{h + 10}" rx="29" fill="none" stroke="{YEL}" stroke-width="5"/>'
    return o


def garbage_truck(cx, cy, s=1.0):
    o = f'<g transform="translate({cx} {cy}) scale({s})">'
    o += brect(-52, -34, 70, 46, 14, YEL, sh=1) + brect(18, -22, 34, 34, 10, YEL, sh=1)
    o += f'<rect x="26" y="-14" width="18" height="14" rx="4" fill="#DDF6FF"/>'
    o += f'<rect x="-42" y="-24" width="50" height="26" rx="8" fill="{darker(YEL, .12)}" opacity=".6"/>'
    for wx in (-32, 30):
        o += bell(wx, 14, 11, 11, INK, sh=1, gloss=False) + f'<circle cx="{wx}" cy="14" r="4" fill="#FFFFFF"/>'
    o += note(-20, -52, 1.0, INK, -15) + note(5, -58, .9, INK, 10)
    return o + "</g>"


def scooter(cx, cy, s=1.0):
    o = f'<g transform="translate({cx} {cy}) scale({s})">'
    o += bell(-26, 14, 12, 12, INK, sh=1, gloss=False) + bell(26, 14, 12, 12, INK, sh=1, gloss=False)
    o += bpath("M-30,-4 L-6,-4 L14,-30 L30,-30 L30,-22 L20,-22 L10,2 L30,2 L30,10 L-34,10Z", (-34, -30, 64, 40), RED, sh=1, gloss=False)
    o += brect(-18, -16, 30, 14, 7, darker(RED, .1), sh=0)
    o += stroke("M14,-30 L8,-42 M8,-42 h-10 M8,-42 h10", INK, 3)
    o += text(28, -48, "噗噗", 13, SOFT)
    return o + "</g>"


def rain(cx, cy, s=1.0):
    o = f'<g transform="translate({cx} {cy}) scale({s})">'
    o += bell(-14, -20, 22, 16, "#FFFFFF", sh=1, gloss=False) + bell(14, -24, 24, 18, "#FFFFFF", sh=1, gloss=False) + bell(0, -12, 32, 16, "#FFFFFF", sh=1, gloss=False)
    for i, dx in enumerate((-26, -10, 6, 22)):
        o += bell(dx, 20 + (i % 2) * 10, 5, 8, BLUE, sh=0)
    return o + "</g>"


def screen_listen():
    o = [bg("#E8E2FF", "#FFF1DC", seed=23)]
    o.append(top_bar(.7))
    o.append(text(W / 2, 125, "聽聽看", 30, INK, weight="bold"))
    # big speaker balloon
    o.append(bell(W / 2, 232, 64, 64, PURP, sh=3, knot=True))
    o.append(speaker(W / 2 - 8, 232, 2.2, "#FFFFFF"))
    o.append(note(300, 190, 1.4, PURP, 10) + note(80, 205, 1.3, PINK, -15) + note(320, 262, 1.1, BLUE, 20))
    o.append(speech(60, 300, 270, 48, "這是什麼聲音？", 22, "left"))
    # three cards
    o.append(pic_card(30, 380, 150, 150, "#FFF6D0", on=True))
    o.append(garbage_truck(105, 462, 1.0))
    o.append(text(105, 560, "垃圾車", 17, INK, weight="bold"))
    o.append(pic_card(210, 380, 150, 150, "#FFE2E2"))
    o.append(scooter(285, 460, 1.0))
    o.append(text(285, 560, "機車", 17, INK))
    o.append(pic_card(120, 580, 150, 150, "#E0F0FF"))
    o.append(rain(195, 655, 1.0))
    o.append(text(195, 760, "下雨", 17, INK))
    o.append(finger(150, 515, -25))
    o.append(sparkle(40, 372, 10, YEL) + sparkle(185, 395, 8, PINK) + sparkle(60, 540, 7, ORA))
    # listen again
    o.append(bell(330, 700, 30, 30, GRN, sh=2) + speaker(324, 700, 1.1, "#FFFFFF") + text(330, 748, "再聽一次", 13, SOFT))
    o.append(home_btn())
    return page("".join(o), "#E8E2FF")


def screen_parents():
    o = [bg("#EEF2FA", "#FFFFFF", seed=29, dots=False)]
    o.append(brect(14, 44, 40, 40, 20, "#FFFFFF", sh=1, gloss=False) + stroke("M38,54 L28,64 L38,74", INK, 3))
    o.append(lock_icon(132, 66, INK) + text(W / 2 + 12, 72, "家長模式", 24, INK, weight="bold"))
    y = 104
    o.append(card(14, y, W - 28, 88, "年齡（難度）"))
    o.append(brect(30, y + 42, 150, 36, 18, BLUE, sh=1) + text(105, y + 67, "小小 2～3 歲", 15, "#FFFFFF"))
    o.append(brect(200, y + 42, 160, 36, 18, "#F2F3F8", sh=0, gloss=False) + text(280, y + 67, "大 4～5 歲", 15, SOFT))
    y += 100
    o.append(card(14, y, W - 28, 76, "每次玩多久"))
    o.append(bell(230, y + 40, 17, 17, "#F2F3F8", sh=0, gloss=False) + text(230, y + 46, "－", 18, SOFT))
    o.append(text(290, y + 47, "15 分鐘", 18, INK, weight="bold"))
    o.append(bell(350, y + 40, 17, 17, GRN, sh=1) + text(350, y + 46, "＋", 18, "#FFFFFF"))
    o.append(text(30, y + 58, "時間到了燈慢慢暗、布幕合起來", 13, SOFT, "start"))
    y += 88
    o.append(card(14, y, W - 28, 150, "要開哪些玩具"))
    toys = [("敲敲樂", True), ("動物樂團", True), ("音樂木頭人", True), ("高低快慢", True), ("錄下來", True), ("聽聽看", False)]
    for i, (n, on) in enumerate(toys):
        r, c = divmod(i, 2)
        o.append(check_box(30 + c * 170, y + 44 + r * 34, on, n))
    y += 162
    o.append(card(14, y, W - 28, 108, "聲音"))
    o.append(text(30, y + 60, "音量上限", 16, INK, "start"))
    o.append(brect(120, y + 54, 200, 12, 6, GREY, sh=0, gloss=False) + brect(120, y + 54, 140, 12, 6, PURP, sh=0, gloss=False) + bell(260, y + 60, 13, 13, "#FFFFFF", sh=1, gloss=False) + text(345, y + 65, "70%", 14, SOFT))
    o.append(text(30, y + 94, "國語念出來", 16, INK, "start") + toggle(300, y + 78, True))
    y += 120
    o.append(card(14, y, W - 28, 92, "今天"))
    o.append(text(30, y + 58, "玩了 12 分鐘 · 最常玩：動物樂團", 15, INK, "start"))
    o.append(text(30, y + 80, "我的小曲子：3 首", 15, INK, "start") + tape(330, y + 62, PINK, [RED, YEL, GRN], .55))
    y += 104
    o.append(brect(14, y, W - 28, 64, 20, ORA, sh=2))
    o.append(lock_icon(36, y + 32, "#FFFFFF") + text(56, y + 38, "完整版：10 隻動物、錄下來、聽聽看（一次買斷）", 14, "#FFFFFF", "start", "bold"))
    return page("".join(o), "#EEF2FA")


# ================================================================ STYLE PAGE
def style_scene(sx, sy, w, h):
    """The same little stage drawn in whatever STYLE is set."""
    dark = STYLE == "neon"
    o = [f'<g transform="translate({sx} {sy})">']
    bgc = "#1B1A3A" if dark else ("#FFF4DE" if STYLE == "glass" else "#CFEFFF")
    o.append(f'<rect width="{w}" height="{h}" rx="26" fill="{bgc}"/>')
    if STYLE == "glass":
        for i in range(6):
            o.append(f'<path d="M{w / 2},-10 L{-60 + i * 110},{h + 10} L{-20 + i * 110},{h + 10}Z" fill="#FFFFFF" opacity=".28"/>')
    if dark:
        rnd = _rand(4)
        for _ in range(30):
            o.append(f'<circle cx="{rnd() * w:.0f}" cy="{rnd() * h * .6:.0f}" r="{1 + rnd() * 1.5:.1f}" fill="#FFFFFF" opacity=".7"/>')
    cp = clip(rr_d(0, 0, w, h, 26))
    o.append(f'<g clip-path="{cp}">')
    o.append(f'<g transform="scale({w / W:.3f})">')
    o.append(curtain(-6, 70, 230, True) + curtain(W - 64, 70, 230, False))
    o.append(valance(50))
    o.append(floor(430, 90, TEAL if not dark else "#2C7A72"))
    o.append(animal("青蛙", 120, 440, 1.0, "sing"))
    o.append(animal("小鳥", 275, 436, .95, "sing"))
    o.append(note(190, 300, 1.6, YEL if not dark else PINK, 10) + note(330, 330, 1.4, PINK, -10) + note(70, 320, 1.3, BLUE, 0))
    o.append(bell(330, 190, 34, 42, PINK, sh=1, knot=True) + stroke("M330,236 q6,16 -4,30 q-6,14 2,24", PINK if dark else darker(PINK, .3), 2))
    o.append(xylophone(30, 515, W - 60, 5, 140, 18, pressed=1))
    o.append("</g></g></g>")
    return "".join(o)


def style_sheet():
    global STYLE
    STYLE = "balloon"      # the page itself is light; each column sets its own style
    w, h = 1170, 844
    o = [f'<rect width="{w}" height="{h}" fill="#F5F0E8"/>']
    o.append(text(w / 2, 58, "選一個畫風", 38, INK, weight="bold"))
    o.append(text(w / 2, 92, "同一個舞台，三種畫法", 20, SOFT))
    items = [("balloon", "A 氣球充氣風（候選）", "每樣東西都像充了氣的氣球：圓滾滾、亮面反光、有一點透、會彈。", False),
             ("neon", "B 霓虹舞台風（決定）", "深藍紫的舞台，所有東西是柔柔發光的霓虹燈管，臉亮亮的看得到。", True),
             ("glass", "C 彩繪玻璃風（候選）", "一片片透光的彩色玻璃，粗粗的鉛條，光從後面照進來。", False)]
    cw = 360
    for i, (st, title, desc, rec) in enumerate(items):
        x = 30 + i * (cw + 15)
        o.append(f'<rect x="{x}" y="112" width="{cw}" height="{h - 136}" rx="30" fill="#FFFFFF" stroke="{GRN if rec else "#E3DED6"}" stroke-width="{5 if rec else 2}"/>')
        if rec:
            o.append(f'<rect x="{x + cw - 150}" y="100" width="140" height="34" rx="17" fill="{GRN}"/>' + text(x + cw - 80, 124, "已經選這個", 17, "#FFFFFF", weight="bold"))
        STYLE = "balloon"
        o.append(text(x + 24, 160, title, 25, INK, "start", "bold"))
        o.append(text(x + 24, 190, desc[:19], 15, SOFT, "start") + text(x + 24, 212, desc[19:], 15, SOFT, "start"))
        STYLE = st
        o.append(style_scene(x + 20, 230, cw - 40, 560))
    STYLE = "neon"
    return page("".join(o), "#F5F0E8", w, h), w, h


# ================================================================ CONTACT SHEET AND MAIN
def contact_sheet(names):
    cw_, ch_, gap, m = 232, 502, 24, 30
    per = 4
    rows = (len(names) + per - 1) // per
    w = per * cw_ + (per - 1) * gap + 2 * m
    rowh = ch_ + 64
    h = rows * rowh + 40
    items = []
    for i, n in enumerate(names):
        r, c = divmod(i, per)
        x = m + c * (cw_ + gap)
        y = 28 + r * rowh
        items.append(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{cw_}px;text-align:center">'
                     f'<img src="file://{HERE / (n + ".png")}" style="width:{cw_}px;height:{ch_}px;border-radius:18px;box-shadow:0 6px 16px rgba(60,60,110,.2)">'
                     f'<div style="font:19px Huninn, sans-serif;color:{INK};margin-top:10px">{n.replace("_", " ")}</div></div>')
    css = f"@font-face {{ font-family: Huninn; src: url('file://{FONT}'); }} * {{ margin:0; padding:0 }} body {{ width:{w}px; height:{h}px; background:#F5F0E8; position:relative }}"
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{"".join(items)}</body></html>', w, h


SCREENS = {"1_舞台": screen_home, "2_敲敲樂": screen_xylo, "3_動物樂團": screen_band, "4_音樂木頭人": screen_freeze,
           "5_高低快慢": screen_pitch, "6_錄下來": screen_record, "7_聽聽看": screen_listen, "8_家長模式": screen_parents}


def main(only=None):
    global D
    if only in (None, "0"):
        D = Defs()
        html, w, h = style_sheet()
        render(html, HERE / "0_畫風選擇.png", w, h, 2)
        print("0_畫風選擇")
    for name, make in SCREENS.items():
        if only not in (None, name.split("_")[0]):
            continue
        D = Defs()
        render(make(), HERE / f"{name}.png", W, H, 2)
        print(name)
    if only in (None, "c"):
        html, w, h = contact_sheet(list(SCREENS))
        render(html, HERE / "contact_sheet.png", w, h, 1.25)
        print("contact_sheet")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
