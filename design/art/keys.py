"""The things a child hits (docs/art.md keys/): each in two states, `idle` and `lit` (just hit: the glass
fills with light and the glow doubles, like a neon sign flashing).

- `keys/xylo_<i>_<state>.svg` 80 x 400: the xylophone bars, C5 D5 E5 G5 A5 C6 D6 E6, each a little
  shorter than the one before, standing on the bottom edge; the colour is the note's (Do red, Re
  orange, Mi yellow, Sol green, La blue), the same everywhere in the app.
- `keys/drum_<i>_<state>.svg` 160 x 160: bass drum, low tom, high tom, snare, tambourine.
- `keys/pot_<i>_<state>.svg` 160 x 160: pot, lid, bowl, cup, spoon (with small faces).
- `keys/step_<i>_<state>.svg` 80 x 400: the 高低 stairs, five steps, each taller (same colours).
"""
import sys

sys.dont_write_bytecode = True

import math  # noqa: E402

import kit  # noqa: E402
from kit import (CORAL, CREAM, CYAN, GOLD, LAVENDER, LILAC, MINT, NOTE_COLOURS, ORANGE, PINK, SKY, WHITE, YELLOW,  # noqa: E402
                 Shape, arc, circle, ellipse, path, rrect)

STATES = ("idle", "lit")
BASE = "#24204A"


def glassy(c, shape, col, lit, w=3.2):
    c.fill(shape, BASE)
    c.tube(shape, col, w=w, glass=0.55 if lit else 0.17, glow=2.2 if lit else 1.0, core=0.95 if lit else 0.7)


def sparkles(c, pts, col=WHITE):
    for x, y, r in pts:
        c.glowdot(x, y, r, col, 0.35)


def xylo(i, lit):
    c = kit.Ctx(80, 400, unit=1.35)
    col = NOTE_COLOURS[i % 5]
    top = 18 + i * 24
    bar = rrect(12, top, 56, 388 - top, 26)
    if lit:
        c.fill(ellipse(40, (top + 388) / 2, 40, (388 - top) / 2 + 8), col, op=0.12)
    glassy(c, bar, col, lit)
    for y in (top + 26, 362):      # the two pins that hold a real bar
        c.glowdot(40, y, 5.5 if lit else 4.5, WHITE if lit else col, 0.3)
    if i >= 5:                      # the second octave: a small dot more
        c.glowdot(40, top + 48, 3.5, WHITE, 0.25)
    if lit:
        c.line(path([(26, top + 70), (26, 330)]), WHITE, 2.4, glow=0.6, core=0)
    return c.svg()


def step(i, lit):
    c = kit.Ctx(80, 400, unit=1.35)
    col = NOTE_COLOURS[i]
    top = 300 - i * 70
    bar = rrect(10, top, 60, 390 - top, 18)
    glassy(c, bar, col, lit)
    c.line(path([(24, top + 14), (56, top + 14)]), WHITE, 2.0, glow=0.5, core=0)   # the tread
    if lit:
        sparkles(c, [(22, top - 14, 3), (60, top - 20, 4)])
    return c.svg()


def drum(i, lit):
    c = kit.Ctx(160, 160, unit=1.25)
    if i == 0:      # the bass drum, seen from the front
        col = PINK
        glassy(c, circle(80, 82, 64), col, lit)
        c.line(circle(80, 82, 50), col, 2.0, glow=0.6, core=0.4)
        for a in range(0, 360, 45):
            x, y = 80 + 64 * math.cos(math.radians(a)), 82 + 64 * math.sin(math.radians(a))
            c.glowdot(x, y, 4, CREAM, 0.3)
        c.face(80, 80, 18, "cheer" if lit else "idle")
    elif i in (1, 2):   # toms: a drum seen a little from above
        col = LILAC if i == 1 else CYAN
        r = 58 if i == 1 else 48
        top_y = 60 if i == 1 else 70
        h = 64 if i == 1 else 52
        side = Shape([("M", 80 - r, top_y), ("L", 80 - r, top_y + h),
                      ("C", 80 - r, top_y + h + r * 0.5, 80 + r, top_y + h + r * 0.5, 80 + r, top_y + h),
                      ("L", 80 + r, top_y), ("Z",)])
        glassy(c, side, col, lit)
        for k in range(5):
            x = 80 - r + 2 * r * (k + 0.5) / 5
            c.line(path([(x, top_y + 6), (x, top_y + h + 10 - abs(k - 2) * 2)]), col, 1.6, glow=0.4, core=0)
        glassy(c, ellipse(80, top_y, r, r * 0.38), col, lit)
        c.face(80, top_y + h * 0.62, 12, "cheer" if lit else "idle", cheeks=False)
    elif i == 3:    # the snare: flatter, with the wires
        col = ORANGE
        side = rrect(22, 64, 116, 50, 14)
        glassy(c, side, col, lit)
        glassy(c, ellipse(80, 64, 58, 20), col, lit)
        for k in range(6):
            x = 30 + k * 20
            c.line(path([(x, 70), (x + 10, 110)]), CREAM, 1.4, glow=0.4, core=0)
        c.line(path([(40, 30), (70, 56)]), CREAM, 3.0)       # a drumstick
        c.glowdot(40, 30, 6, CREAM, 0.3)
    else:           # the tambourine, with its little cymbals
        col = YELLOW
        glassy(c, circle(80, 80, 60), col, lit)
        c.fill(circle(80, 80, 40), BASE)
        c.line(circle(80, 80, 40), col, 2.2, glow=0.6, core=0.5)
        for k in range(6):
            a = math.radians(k * 60 + 30)
            x, y = 80 + 50 * math.cos(a), 80 + 50 * math.sin(a)
            c.fill(ellipse(x, y, 9, 6).rotate(k * 60 + 120, x, y), BASE)
            c.tube(ellipse(x, y, 9, 6).rotate(k * 60 + 120, x, y), CREAM, w=2.0, glass=0.5 if lit else 0.25,
                   glow=1.5 if lit else 0.7)
        c.face(80, 76, 12, "cheer" if lit else "idle")
    if lit:
        sparkles(c, [(18, 22, 4), (142, 20, 5), (148, 120, 3)])
    return c.svg()


def pot(i, lit):
    c = kit.Ctx(160, 160, unit=1.25)
    mood = "cheer" if lit else "idle"
    if i == 0:      # a pot with two handles
        col = SKY
        for side in (-1, 1):
            c.line(path([(80 + side * 56, 74), (80 + side * 72, 74)]), col, 6, glow=1.0)
        body = Shape([("M", 24, 60), ("L", 136, 60), ("L", 130, 118),
                      ("C", 128, 136, 32, 136, 30, 118), ("Z",)])
        glassy(c, body, col, lit)
        glassy(c, rrect(18, 52, 124, 14, 7), col, lit)
        c.face(80, 92, 14, mood)
    elif i == 1:    # a lid with its knob
        col = LAVENDER
        lid = Shape([("M", 14, 104), ("C", 20, 50, 140, 50, 146, 104), ("Z",)])
        glassy(c, lid, col, lit)
        glassy(c, rrect(66, 40, 28, 18, 9), col, lit)
        c.line(path([(14, 104), (146, 104)]), col, 4)
        c.face(80, 84, 13, mood)
    elif i == 2:    # a rice bowl
        col = MINT
        bowl = Shape([("M", 18, 66), ("L", 142, 66), ("C", 140, 110, 112, 130, 80, 130),
                      ("C", 48, 130, 20, 110, 18, 66), ("Z",)])
        glassy(c, bowl, col, lit)
        glassy(c, rrect(58, 128, 44, 12, 6), col, lit)
        c.line(Shape([("M", 30, 82), ("C", 60, 92, 100, 92, 130, 82)]), PINK, 2.2, glow=0.6, core=0)   # a painted line
        c.face(80, 100, 13, mood)
    elif i == 3:    # a cup
        col = PINK
        c.line(Shape([("M", 112, 70), ("C", 146, 66, 146, 112, 112, 108)]), col, 6, glow=1.0)
        cup = rrect(36, 48, 80, 90, 18, rtl=8, rtr=8)
        glassy(c, cup, col, lit)
        c.face(76, 88, 14, mood)
        for x, y in ((60, 36), (78, 28), (96, 36)):      # a little steam
            c.line(Shape([("M", x, y + 8), ("C", x - 6, y + 2, x + 6, y - 2, x, y - 8)]), WHITE, 1.6, glow=0.4, core=0)
    else:           # a spoon
        col = YELLOW
        glassy(c, ellipse(60, 58, 34, 42).rotate(-35, 60, 58), col, lit)
        handle = rrect(84, 70, 16, 84, 8).rotate(-35, 92, 74)
        glassy(c, handle, col, lit)
        c.face(60, 56, 12, mood)
    if lit:
        sparkles(c, [(16, 24, 4), (146, 24, 5), (150, 136, 3)])
    return c.svg()


def build():
    out = kit.ART / "keys"
    count = 0
    for st in STATES:
        lit = st == "lit"
        for i in range(8):
            kit.write_svg(out / f"xylo_{i}_{st}.svg", xylo(i, lit), (80, 400))
            count += 1
        for i in range(5):
            kit.write_svg(out / f"step_{i}_{st}.svg", step(i, lit), (80, 400))
            kit.write_svg(out / f"drum_{i}_{st}.svg", drum(i, lit), (160, 160))
            kit.write_svg(out / f"pot_{i}_{st}.svg", pot(i, lit), (160, 160))
            count += 3
    print(f"keys: {count} files")


if __name__ == "__main__":
    build()
