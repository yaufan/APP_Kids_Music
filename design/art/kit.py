"""Neon stage drawing kit for 小小音波 (霓虹舞台風).

Everything is a soft neon tube on a deep navy-purple stage: a shape is filled with its own colour
at ~16 % (glass), then its outline is drawn as a tube: two wide, see-through strokes of the same
colour under it (the glow), the tube itself, and a thin white line inside it (the hot core).
flutter_svg cannot blur (no <filter>), so the glow is ALWAYS those widened strokes. No masks, no
CSS, no text, no images: only plain paths with fill / stroke / opacity, so flutter_svg draws exactly
what Chromium draws (docs/art.md).

    import kit
    c = kit.Ctx(200, 200, unit=1.8)                 # viewBox 0 0 200 200, drawn about 110 pt wide
    c.tube(kit.circle(100, 90, 50), kit.PINK)       # glass + glow + tube + core
    c.line(kit.arc(100, 95, 20, 30, 150), kit.PINK) # an open neon line (no glass)
    c.face(100, 90, 24, "idle")                     # white eyes, glowing cheeks, a pink smile
    kit.write_svg(path, c.svg())                    # checks the rules, then writes

`unit` is how many viewBox units make one point on the phone: every tube is TUBE points thick
whatever the file's size, so all the art has the same weight on screen. Shapes (`Shape`) are lists
of path commands; `+` unions them, `.move .scale .flip .rotate` make new ones (from 小小生活家's kit).
"""
import hashlib
import math
import pathlib
import random
import re
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ART = ROOT / "app" / "assets" / "art"

# ---------------------------------------------------------------- palette (docs/design.md 「畫風」)
BG_TOP = "#1B1A3A"      # the stage at night, top
BG_BOT = "#2A2550"      # and bottom
NIGHT = "#141331"       # darker (behind the curtains)
INK = "#F2EEFF"         # words
INK_SOFT = "#B6AEDC"
WHITE = "#FFFFFF"
DARK = "#1B1A3A"        # pupils, things drawn "in" the glass
# pastel neon (soft, never the harsh fluorescent ones)
PINK = "#FF8FC8"
CORAL = "#FF8A8A"
ORANGE = "#FFA66B"
YELLOW = "#FFE16E"
GOLD = "#FFC86B"
GREEN = "#8EF09A"
MINT = "#7FF0D2"
CYAN = "#63DCF5"
SKY = "#8FB8FF"
BLUE = "#5E8CFF"
LILAC = "#C7A6FF"
LAVENDER = "#DCD3FF"
CREAM = "#FFF1B8"
CHEEK = "#FF8FB8"
MOUTH = "#FF7AA8"
# the five notes' colours, everywhere in the app (Do red, Re orange, Mi yellow, Sol green, La blue)
NOTE_COLOURS = ("#FF7A8A", "#FFA65E", "#FFE066", "#7EEB8F", "#6EC8FF")
TUBE = 3.0              # points


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(r, g, b):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in (r, g, b))


def mix(a, b, t):
    """Colour a moved t (0..1) of the way to colour b."""
    return _hex(*[x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))])


def lt(c, t):
    """Lighter."""
    return mix(c, "#FFFFFF", t)


def dk(c, t):
    """Darker and warmer (a paper edge)."""
    return mix(c, WARM, t)


def rnd(*key):
    """A seeded random generator: the same key always gives the same numbers."""
    h = hashlib.md5("|".join(map(str, key)).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


def n(v):
    """A number, short: one decimal, no trailing .0, no -0."""
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    if s == "-0":
        s = "0"
    return s


KAPPA = 0.5522847498


class Shape:
    """Path commands: ('M', x, y) ('L', x, y) ('C', x1, y1, x2, y2, x, y) ('Z',). All shapes the kit
    makes wind clockwise on screen, so unions (`a + b`) fill with the default nonzero rule."""

    def __init__(self, cmds=None):
        self.cmds = list(cmds or [])

    def __add__(self, other):
        return Shape(self.cmds + other.cmds)

    def move(self, dx, dy):
        return self.map(lambda x, y: (x + dx, y + dy))

    def scale(self, s, cx=0.0, cy=0.0, sy=None):
        sy = s if sy is None else sy
        return self.map(lambda x, y: (cx + (x - cx) * s, cy + (y - cy) * sy))

    def flip(self, cx):
        """Mirror left-right about x = cx (winding is fixed afterwards)."""
        return self.map(lambda x, y: (2 * cx - x, y)).reverse()

    def rotate(self, deg, cx, cy):
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)
        return self.map(lambda x, y: (cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca))

    def map(self, f):
        out = []
        for c in self.cmds:
            if c[0] == "Z":
                out.append(c)
            else:
                pts = [f(c[i], c[i + 1]) for i in range(1, len(c), 2)]
                out.append((c[0],) + tuple(v for p in pts for v in p))
        return Shape(out)

    def reverse(self):
        """The same outline the other way round (one subpath at a time)."""
        out = []
        for sub in self.subpaths():
            pts = []   # (point, incoming control pair or None)
            cur = None
            for c in sub:
                if c[0] == "M":
                    cur = (c[1], c[2])
                    pts.append((cur, None))
                elif c[0] == "L":
                    cur = (c[1], c[2])
                    pts.append((cur, None))
                elif c[0] == "C":
                    cur = (c[5], c[6])
                    pts.append((cur, (c[1], c[2], c[3], c[4])))
            rev = pts[::-1]
            out.append(("M",) + rev[0][0])
            for i in range(1, len(rev)):
                p, _ = rev[i]
                _, ctrl = rev[i - 1]      # the control pair that led INTO rev[i-1] from rev[i]
                if ctrl is None:
                    out.append(("L",) + p)
                else:
                    out.append(("C", ctrl[2], ctrl[3], ctrl[0], ctrl[1]) + p)
            out.append(("Z",))
        return Shape(out)

    def subpaths(self):
        subs, cur = [], []
        for c in self.cmds:
            if c[0] == "M" and cur:
                subs.append(cur)
                cur = []
            cur.append(c)
        if cur:
            subs.append(cur)
        return subs

    def bbox(self):
        xs = [c[i] for c in self.cmds if c[0] != "Z" for i in range(1, len(c), 2)]
        ys = [c[i] for c in self.cmds if c[0] != "Z" for i in range(2, len(c), 2)]
        return min(xs), min(ys), max(xs), max(ys)

    def d(self, dx=0.0, dy=0.0):
        out = []
        for c in self.cmds:
            if c[0] == "Z":
                out.append("Z")
            else:
                nums = [n(c[i] + (dx if i % 2 else dy)) for i in range(1, len(c))]
                out.append(c[0] + " ".join(nums))
        return "".join(out)


def poly(points, close=True):
    """A polygon through points (any winding; it is made clockwise)."""
    pts = [tuple(p) for p in points]
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if area < 0:      # counter-clockwise on screen (y down) -> reverse
        pts = pts[::-1]
    cmds = [("M",) + pts[0]] + [("L",) + p for p in pts[1:]]
    if close:
        cmds.append(("Z",))
    return Shape(cmds)


def rrect(x, y, w, h, r=8.0, rtl=None, rtr=None, rbr=None, rbl=None):
    """A rounded rectangle; corner radii can differ."""
    r = min(r, w / 2, h / 2)
    a, b, c_, d = [min(v if v is not None else r, w / 2, h / 2) for v in (rtl, rtr, rbr, rbl)]
    k = KAPPA
    cmds = [("M", x + a, y), ("L", x + w - b, y)]
    if b:
        cmds.append(("C", x + w - b + b * k, y, x + w, y + b - b * k, x + w, y + b))
    cmds.append(("L", x + w, y + h - c_))
    if c_:
        cmds.append(("C", x + w, y + h - c_ + c_ * k, x + w - c_ + c_ * k, y + h, x + w - c_, y + h))
    cmds.append(("L", x + d, y + h))
    if d:
        cmds.append(("C", x + d - d * k, y + h, x, y + h - d + d * k, x, y + h - d))
    cmds.append(("L", x, y + a))
    if a:
        cmds.append(("C", x, y + a - a * k, x + a - a * k, y, x + a, y))
    cmds.append(("Z",))
    return Shape(cmds)


def rect(x, y, w, h):
    return rrect(x, y, w, h, 0)


def ellipse(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    k = KAPPA
    return Shape([
        ("M", cx + rx, cy),
        ("C", cx + rx, cy + ry * k, cx + rx * k, cy + ry, cx, cy + ry),
        ("C", cx - rx * k, cy + ry, cx - rx, cy + ry * k, cx - rx, cy),
        ("C", cx - rx, cy - ry * k, cx - rx * k, cy - ry, cx, cy - ry),
        ("C", cx + rx * k, cy - ry, cx + rx, cy - ry * k, cx + rx, cy),
        ("Z",)])


def circle(cx, cy, r):
    return ellipse(cx, cy, r, r)


def smooth(points, tension=0.5):
    """A closed, smooth (Catmull-Rom) curve through points, clockwise."""
    pts = [tuple(p) for p in points]
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if area < 0:
        pts = pts[::-1]
    m = len(pts)
    cmds = [("M",) + pts[0]]
    for i in range(m):
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        cmds.append(("C",) + c1 + c2 + p2)
    cmds.append(("Z",))
    return Shape(cmds)


def blob(cx, cy, rx, ry=None, lumps=7, wobble=0.12, key="blob"):
    """A soft potato shape (a bush, a cushion, a cloud body): an ellipse with seeded bumps."""
    ry = rx if ry is None else ry
    r = rnd("blob", key, lumps)
    pts = []
    for i in range(lumps):
        a = 2 * math.pi * i / lumps
        f = 1 + r.uniform(-wobble, wobble)
        pts.append((cx + rx * f * math.cos(a), cy + ry * f * math.sin(a)))
    return smooth(pts, 0.9)


def star(cx, cy, R, r=None, points=5, rot=-90.0):
    r = R * .48 if r is None else r
    pts = []
    for i in range(points * 2):
        a = math.radians(rot + 180.0 * i / points)
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return poly(pts)


def heart(cx, cy, s):
    """A heart about s wide, centred on cx, cy."""
    w, h = s, s * .95
    x0, y0 = cx, cy - h * .3          # the notch
    return Shape([
        ("M", x0, y0),
        ("C", x0 + w * .1, y0 - h * .3, x0 + w * .5, y0 - h * .3, x0 + w * .5, y0 + h * .05),
        ("C", x0 + w * .5, y0 + h * .4, x0 + w * .15, y0 + h * .55, x0, y0 + h * .75),
        ("C", x0 - w * .15, y0 + h * .55, x0 - w * .5, y0 + h * .4, x0 - w * .5, y0 + h * .05),
        ("C", x0 - w * .5, y0 - h * .3, x0 - w * .1, y0 - h * .3, x0, y0),
        ("Z",)])


def path(points, closed=False):
    """An open polyline (for strokes) or closed polygon."""
    pts = [tuple(p) for p in points]
    cmds = [("M",) + pts[0]] + [("L",) + p for p in pts[1:]]
    if closed:
        cmds.append(("Z",))
    return Shape(cmds)


def arc(cx, cy, r, a0, a1, steps=None):
    """An open arc (degrees, clockwise on screen) made of cubic pieces, for smiles and the like."""
    span = a1 - a0
    steps = steps or max(1, int(abs(span) / 90) + 1)
    cmds = []
    for i in range(steps):
        t0 = math.radians(a0 + span * i / steps)
        t1 = math.radians(a0 + span * (i + 1) / steps)
        k = 4 / 3 * math.tan((t1 - t0) / 4)
        p0 = (cx + r * math.cos(t0), cy + r * math.sin(t0))
        p3 = (cx + r * math.cos(t1), cy + r * math.sin(t1))
        p1 = (p0[0] - k * r * math.sin(t0), p0[1] + k * r * math.cos(t0))
        p2 = (p3[0] + k * r * math.sin(t1), p3[1] - k * r * math.cos(t1))
        if i == 0:
            cmds.append(("M",) + p0)
        cmds.append(("C",) + p1 + p2 + p3)
    return Shape(cmds)


FORBIDDEN = ("<filter", "<mask", "<style", "style=", "class=", "<text", "<image", "<foreignObject", "<pattern",
             "mix-blend-mode", "mask=", "filter=", "vector-effect", "<symbol", "<marker", "@import", "<clipPath",
             "clip-path=")


_TOK = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


_NARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


DRAWN = {"path", "ellipse", "circle", "rect", "polygon", "polyline", "line", "use"}


MAX_KB = 70


def check_path(d):
    """ValueError unless d is path data flutter_svg reads (it drops the WHOLE picture over one bad
    path, where Chromium only skips that path)."""
    toks = _TOK.findall(d)
    if not toks or toks[0] not in "Mm":
        raise ValueError(f"path does not start with M: {d[:40]!r}")
    if len("".join(toks)) != len(re.sub(r"[\s,]", "", d)):
        raise ValueError(f"stray characters in path: {d[:60]!r}")
    i = 0
    while i < len(toks):
        cmd = toks[i]
        if not cmd.isalpha():
            raise ValueError(f"numbers without a command: {d[:60]!r}")
        i += 1
        k = _NARGS[cmd.upper()]
        j = i
        while j < len(toks) and not toks[j].isalpha():
            j += 1
        cnt = j - i
        if (k == 0 and cnt) or (k and (cnt == 0 or cnt % k)):
            raise ValueError(f"command {cmd} has {cnt} numbers: {d[:60]!r}")
        i = j


def check_svg(name, text, size=None):
    """docs/art.md's rules: no filter/mask/style/text/image/pattern/blend, every drawn element has
    fill or stroke, under 70 KB, well-formed XML ending in </svg>, viewBox 0 0 w h (= size if given),
    parseable path data. Returns the size in KB; SystemExit on a problem."""
    bad = [f for f in FORBIDDEN if f in text]
    if bad:
        raise SystemExit(f"{name}: uses {bad} (flutter_svg cannot draw these)")
    kb = len(text.encode()) / 1024
    if kb > MAX_KB:
        raise SystemExit(f"{name}: {kb:.0f} KB (keep under {MAX_KB} KB)")
    if not text.rstrip().endswith("</svg>"):
        raise SystemExit(f"{name}: does not end with </svg>")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise SystemExit(f"{name}: not well-formed XML: {e}")
    ns = "{http://www.w3.org/2000/svg}"
    if root.tag != f"{ns}svg":
        raise SystemExit(f"{name}: root is not <svg xmlns=...>")
    vb = root.get("viewBox")
    if not vb:
        raise SystemExit(f"{name}: no viewBox")
    vb = [float(v) for v in vb.split()]
    if vb[0] or vb[1]:
        raise SystemExit(f"{name}: viewBox must start at 0 0")
    if size and (abs(vb[2] - size[0]) > .01 or abs(vb[3] - size[1]) > .01):
        raise SystemExit(f"{name}: viewBox {vb[2]:g} x {vb[3]:g}, expected {size[0]:g} x {size[1]:g}")
    defs = root.find(f"{ns}defs")
    in_defs = {id(el) for el in defs.iter()} if defs is not None else set()
    for el in root.iter():
        tag = el.tag.replace(ns, "")
        d = el.get("d")
        if d is not None:
            try:
                check_path(d)
            except ValueError as e:
                raise SystemExit(f"{name}: {e}")
        if tag in DRAWN and id(el) not in in_defs and el.get("fill") is None and el.get("stroke") is None:
            raise SystemExit(f"{name}: a <{tag}> without fill/stroke")
        for a in ("fill", "stroke"):
            v = el.get(a)
            if v and v.startswith("url(#") and root.find(f".//*[@id='{v[5:-1]}']") is None:
                raise SystemExit(f"{name}: {a} points to a missing {v}")
    return kb


def viewbox_of(path):
    """(w, h) of an SVG file's viewBox."""
    vb = [float(v) for v in ET.parse(path).getroot().get("viewBox").split()]
    return vb[2], vb[3]


def write_svg(path, text, size=None):
    """Check, then write. Returns the size in KB."""
    path = pathlib.Path(path)
    name = str(path.relative_to(ROOT)) if ROOT in path.parents else str(path)
    kb = check_svg(name, text, size)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return kb


# ---------------------------------------------------------------- the SVG writer
class Ctx:
    """One SVG file being drawn: viewBox 0 0 w h. `unit` = viewBox units per point on screen."""

    def __init__(self, w, h, unit=1.0):
        self.w, self.h, self.unit = w, h, unit
        self.body = []
        self.defs = []
        self._open = 0
        self._ids = 0

    # ---- raw
    def add(self, text):
        self.body.append(text)

    def path_el(self, d, fill="none", stroke=None, sw=0.0, op=1.0, rule=None, cap="round"):
        a = [f'd="{d}"', f'fill="{fill}"']
        if rule:
            a.append(f'fill-rule="{rule}"')
        if stroke:
            a += [f'stroke="{stroke}"', f'stroke-width="{n(sw)}"', f'stroke-linecap="{cap}"', 'stroke-linejoin="round"']
        if op < 1:
            a.append(f'fill-opacity="{op:.2f}"' if fill != "none" else f'stroke-opacity="{op:.2f}"')
        self.body.append("<path " + " ".join(a) + "/>")

    def gradient(self, stops, x1=0, y1=0, x2=0, y2=1):
        """A linear gradient (fractions of the box) -> its url(#id)."""
        self._ids += 1
        gid = f"g{self._ids}"
        st = "".join(f'<stop offset="{o:.2f}" stop-color="{c}"' + (f' stop-opacity="{op:.2f}"' if op < 1 else "") + "/>"
                     for o, c, op in stops)
        self.defs.append(f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{st}</linearGradient>')
        return f"url(#{gid})"

    def radial(self, stops, cx=0.5, cy=0.5, r=0.5):
        self._ids += 1
        gid = f"g{self._ids}"
        st = "".join(f'<stop offset="{o:.2f}" stop-color="{c}"' + (f' stop-opacity="{op:.2f}"' if op < 1 else "") + "/>"
                     for o, c, op in stops)
        self.defs.append(f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{st}</radialGradient>')
        return f"url(#{gid})"

    # ---- neon
    def fill(self, shape, col, op=1.0, rule=None):
        """A flat fill (glass, a dot)."""
        self.path_el(shape.d(), col, op=op, rule=rule)

    def stroke(self, shape, col, w, op=1.0, cap="round"):
        """A plain line, w in points."""
        self.path_el(shape.d(), "none", col, w * self.unit, op=op, cap=cap)

    def tube(self, shape, col, w=TUBE, glass=0.16, glow=1.0, core=0.75, rule=None):
        """A closed neon shape: glass fill, glow, tube, hot core. glow=0 for none; glass=0 for none."""
        if glass:
            self.fill(shape, col, op=glass, rule=rule)
        self.line(shape, col, w, glow, core)

    def line(self, shape, col, w=TUBE, glow=1.0, core=0.75):
        """An open (or closed, unfilled) neon line."""
        u = self.unit
        d = shape.d()
        if glow:
            self.path_el(d, "none", col, w * 4.2 * u, op=min(1, 0.08 * glow))
            self.path_el(d, "none", col, w * 2.3 * u, op=min(1, 0.2 * glow))
        self.path_el(d, "none", col, w * u)
        if core:
            self.path_el(d, "none", WHITE, max(0.5, w * 0.32) * u, op=core)

    def halo(self, cx, cy, r, col, op=0.18):
        """A soft round glow (three see-through discs)."""
        for k, o in ((2.4, op * 0.35), (1.7, op * 0.6), (1.25, op)):
            self.fill(circle(cx, cy, r * k), col, op=o)

    def glowdot(self, cx, cy, r, col=WHITE, glow=0.25):
        self.halo(cx, cy, r, col, glow)
        self.fill(circle(cx, cy, r), col)

    def note(self, cx, cy, s, col):
        """A little music note (♪)."""
        self.fill(ellipse(cx, cy, s * 0.42, s * 0.32).rotate(-20, cx, cy), col)
        self.stroke(path([(cx + s * 0.36, cy - s * 0.05), (cx + s * 0.36, cy - s * 1.25), (cx + s * 0.85, cy - s * 0.95)]), col, 1.6)

    # ---- faces: white glowing eyes, pink cheeks, a pink mouth
    def face(self, cx, cy, s, mood="idle", gap=1.0, mouth_col=MOUTH, cheek=CHEEK, cheeks=True):
        """s = half the distance between the eyes. moods: idle (open eyes, smile), sing (happy closed eyes,
        an open "o"), frozen (big round eyes, a straight little mouth), cheer (happy closed eyes, a big
        open smile), sleep (closed eyes, small smile)."""
        g = s * gap
        ex = (cx - g, cx + g)
        er = s * 0.3
        my = cy + s * 0.62
        if mood in ("idle", "frozen"):
            big = 1.25 if mood == "frozen" else 1.0
            for x in ex:
                self.glowdot(x, cy, er * big, WHITE, 0.22)
                pr = er * (0.42 if mood == "frozen" else 0.55)
                px = 0 if mood == "frozen" else er * 0.12
                self.fill(circle(x + px, cy + er * 0.1, pr), DARK)
                if mood == "idle":
                    self.fill(circle(x + px + pr * 0.35, cy - pr * 0.25, pr * 0.32), WHITE)
        else:
            for x in ex:
                if mood == "sleep":
                    self.line(arc(x, cy - er * 0.6, er * 1.1, 30, 150), WHITE, 2.0, glow=0.6, core=0)
                else:
                    self.line(arc(x, cy + er * 0.7, er * 1.05, 210, 330), WHITE, 2.2, glow=0.6, core=0)
        if cheeks:
            for x, sx in ((ex[0] - s * 0.35, -1), (ex[1] + s * 0.35, 1)):
                self.halo(x, my - s * 0.12, s * 0.26, cheek, 0.25)
                self.fill(ellipse(x, my - s * 0.12, s * 0.3, s * 0.19), cheek, op=0.75)
        if mood == "idle" or mood == "sleep":
            self.line(arc(cx, my - s * 0.32, s * 0.4, 30, 150), mouth_col, 2.0, glow=0.5, core=0)
        elif mood == "sing":
            self.halo(cx, my + s * 0.05, s * 0.22, mouth_col, 0.2)
            self.fill(ellipse(cx, my + s * 0.05, s * 0.2, s * 0.26), mouth_col)
            self.fill(ellipse(cx, my + s * 0.15, s * 0.12, s * 0.1), "#FFC2D9")
        elif mood == "frozen":
            self.line(path([(cx - s * 0.2, my), (cx + s * 0.2, my)]), mouth_col, 2.0, glow=0.5, core=0)
        else:  # cheer
            m = Shape([("M", cx - s * 0.42, my - s * 0.12),
                       ("C", cx - s * 0.4, my + s * 0.55, cx + s * 0.4, my + s * 0.55, cx + s * 0.42, my - s * 0.12),
                       ("Z",)])
            self.halo(cx, my + s * 0.1, s * 0.3, mouth_col, 0.2)
            self.fill(m, mouth_col)
            self.fill(ellipse(cx, my + s * 0.22, s * 0.18, s * 0.1), "#FFC2D9")

    # ---- groups
    def begin(self, transform=None, op=None):
        a = ""
        if transform:
            a += f' transform="{transform}"'
        if op is not None:
            a += f' opacity="{op:.2f}"'
        self.body.append(f"<g{a}>")
        self._open += 1

    def end(self):
        self.body.append("</g>")
        self._open -= 1

    def svg(self):
        if self._open:
            raise SystemExit("Ctx: a <g> was not closed")
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(self.w)} {n(self.h)}">'
                f'{defs}{"".join(self.body)}</svg>\n')
