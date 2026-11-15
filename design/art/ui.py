"""Buttons and little things (docs/art.md toys/ and ui/).

- `toys/<toy>.svg` 120 x 120: the six toys' pictures for the round buttons on the stage
  (xylo, band, freeze, highlow, record, listen).
- `ui/<name>.svg` 100 x 100: home, lock, sun, moon, snail, rabbit, play, stop, rec, replay, mute, plus,
  star, mouse, slot (an empty spot on the stage).
- `ui/hand.svg` 200 x 200: the big red 「停！」 light with a hand in it (音樂木頭人).
- `ui/balloon_<i>.svg` 100 x 140 (i = 0..2: pink, cyan, yellow), `ui/note_<i>.svg` 60 x 60 (the five
  notes' colours), `ui/tape_<i>.svg` 120 x 80 (eight colours: the saved songs).
"""
import math
import sys

sys.dont_write_bytecode = True

import kit  # noqa: E402
from kit import (BLUE, CORAL, CREAM, CYAN, DARK, GOLD, GREEN, LAVENDER, LILAC, MINT, NOTE_COLOURS, ORANGE, PINK,  # noqa: E402
                 SKY, WHITE, YELLOW, Shape, arc, circle, ellipse, heart, path, poly, rrect, star)

BASE = "#24204A"
TAPE_COLOURS = (PINK, CYAN, YELLOW, GREEN, LILAC, ORANGE, SKY, CORAL)


def solid(c, shape, col, glass=0.2, w=3.0, glow=1.0):
    c.fill(shape, BASE)
    c.tube(shape, col, w=w, glass=glass, glow=glow)


# ---------------------------------------------------------------- the six toys
def toy(name):
    c = kit.Ctx(120, 120, unit=1.7)
    if name == "xylo":
        for k, (x, h) in enumerate(((22, 70), (44, 60), (66, 50), (88, 40))):
            solid(c, rrect(x - 8, 94 - h, 16, h, 8), NOTE_COLOURS[k], w=2.4)
        c.line(path([(30, 30), (60, 56)]), CREAM, 3.2)
        c.glowdot(28, 28, 7, PINK, 0.3)
    elif name == "band":
        solid(c, circle(60, 64, 34), GREEN)
        for side in (-1, 1):
            solid(c, circle(60 + side * 18, 34, 13), GREEN)
        c.face(60, 34, 18, "sing", cheeks=False)
        for side in (-1, 1):
            c.fill(ellipse(60 + side * 24, 72, 6, 4), PINK, op=0.8)
        c.fill(ellipse(60, 76, 8, 10), kit.MOUTH)
        c.note(96, 30, 12, YELLOW)
    elif name == "freeze":
        hand_shape(c, 60, 62, 0.9, WHITE)
    elif name == "highlow":
        for k, h in enumerate((20, 34, 48, 62)):
            solid(c, rrect(18 + k * 22, 100 - h, 18, h, 6), NOTE_COLOURS[k], w=2.2)
        c.glowdot(95, 26, 9, CYAN, 0.3)
        c.fill(poly([(102, 24), (112, 28), (102, 31)]), ORANGE)
        c.fill(circle(97, 24, 2.2), DARK)
    elif name == "record":
        c.tube(circle(60, 60, 40), WHITE, w=3, glass=0.1)
        c.glowdot(60, 60, 22, CORAL, 0.35)
    elif name == "listen":
        speaker(c, 52, 60, 1.0, LAVENDER)
    return c.svg()


def hand_shape(c, cx, cy, s, col):
    """An open hand, palm towards us (stop)."""
    palm = rrect(cx - 26 * s, cy - 6 * s, 52 * s, 50 * s, 18 * s)
    shape = palm
    for k, (dx, h) in enumerate(((-19, 34), (-6, 42), (7, 42), (20, 34))):
        shape = shape + rrect(cx + dx * s - 6 * s, cy - h * s, 12 * s, h * s + 10 * s, 6 * s)
    thumb = rrect(cx - 44 * s, cy + 2 * s, 30 * s, 13 * s, 6.5 * s).rotate(-35, cx - 26 * s, cy + 10 * s)
    c.fill(shape + thumb, col, op=0.95)


def speaker(c, cx, cy, s, col):
    body = Shape([("M", cx - 26 * s, cy - 12 * s), ("L", cx - 12 * s, cy - 12 * s), ("L", cx + 6 * s, cy - 30 * s),
                  ("L", cx + 6 * s, cy + 30 * s), ("L", cx - 12 * s, cy + 12 * s), ("L", cx - 26 * s, cy + 12 * s), ("Z",)])
    solid(c, body, col, w=2.8)
    for k, r in enumerate((16, 30)):
        c.line(arc(cx + 8 * s, cy, r * s, -45, 45), col, 3.0)


# ---------------------------------------------------------------- the icons
def icon(name):
    c = kit.Ctx(100, 100, unit=1.6)
    if name == "home":
        roof = poly([(50, 16), (86, 48), (14, 48)])
        solid(c, rrect(24, 44, 52, 40, 6), CREAM)
        solid(c, roof, PINK)
        solid(c, rrect(42, 60, 16, 24, 6), YELLOW, glass=0.4)
    elif name == "lock":
        c.line(Shape([("M", 32, 46), ("L", 32, 34), ("C", 32, 12, 68, 12, 68, 34), ("L", 68, 46)]), LAVENDER, 4)
        solid(c, rrect(22, 44, 56, 42, 12), LAVENDER)
        c.glowdot(50, 62, 5, WHITE, 0.3)
        c.fill(rrect(48, 62, 4, 12, 2), WHITE)
    elif name == "sun":
        for k in range(8):
            a = math.radians(k * 45)
            c.line(path([(50 + 30 * math.cos(a), 50 + 30 * math.sin(a)), (50 + 42 * math.cos(a), 50 + 42 * math.sin(a))]), YELLOW, 3)
        solid(c, circle(50, 50, 22), YELLOW, glass=0.35)
        c.face(50, 48, 9, "idle", cheeks=True)
    elif name == "moon":
        m = Shape([("M", 62, 14), ("C", 30, 18, 22, 62, 46, 80), ("C", 60, 90, 80, 86, 88, 70),
                   ("C", 60, 74, 44, 40, 62, 14), ("Z",)])
        solid(c, m, CREAM, glass=0.35)
        c.face(50, 54, 7, "sleep", cheeks=False)
        c.glowdot(80, 26, 3, WHITE, 0.3)
    elif name == "snail":
        solid(c, Shape([("M", 10, 78), ("L", 82, 78), ("C", 92, 78, 94, 62, 84, 58), ("L", 76, 58),
                        ("C", 70, 70, 20, 72, 10, 78), ("Z",)]), GREEN)
        solid(c, circle(46, 52, 24), ORANGE)
        c.line(arc(46, 52, 13, 0, 300), ORANGE, 2.4, glow=0.6)
        for x in (80, 88):
            c.line(path([(x, 60), (x + 2, 42)]), GREEN, 2.2)
            c.glowdot(x + 2, 40, 3, GREEN, 0.3)
    elif name == "rabbit":
        for side in (-1, 1):
            solid(c, ellipse(50 + side * 12, 26, 8, 22).rotate(side * 10, 50 + side * 12, 26), PINK)
        solid(c, ellipse(50, 66, 26, 22), WHITE, glass=0.2)
        c.face(50, 62, 9, "idle", cheeks=True)
    elif name == "play":
        solid(c, poly([(32, 20), (82, 50), (32, 80)]), GREEN, glass=0.35)
    elif name == "stop":
        solid(c, rrect(26, 26, 48, 48, 10), PINK, glass=0.35)
    elif name == "rec":
        c.tube(circle(50, 50, 36), WHITE, w=2.6, glass=0.08)
        c.glowdot(50, 50, 20, CORAL, 0.35)
    elif name == "replay":
        speaker(c, 44, 50, 0.85, LAVENDER)
    elif name == "mute":
        speaker(c, 40, 50, 0.8, LAVENDER)
        c.line(path([(18, 82), (84, 18)]), CORAL, 3.2)
    elif name == "plus":
        c.tube(circle(50, 50, 36), LAVENDER, w=2.4, glass=0.08)
        c.line(path([(50, 32), (50, 68)]), LAVENDER, 3.2)
        c.line(path([(32, 50), (68, 50)]), LAVENDER, 3.2)
    elif name == "star":
        solid(c, star(50, 52, 40, 18), YELLOW, glass=0.4)
    elif name == "mouse":
        for side in (-1, 1):
            solid(c, circle(50 + side * 22, 34, 14), LAVENDER)
            c.fill(circle(50 + side * 22, 34, 7), PINK, op=0.5)
        solid(c, ellipse(50, 60, 28, 24), LAVENDER)
        c.face(50, 56, 9, "idle", cheeks=True)
        for side in (-1, 1):
            c.line(path([(50 + side * 12, 68), (50 + side * 32, 64)]), WHITE, 1.2, glow=0.3, core=0)
        c.fill(circle(50, 66, 3), PINK)
    elif name == "slot":
        c.fill(ellipse(50, 70, 44, 14), WHITE, op=0.06)
        for k in range(16):
            a0 = k * 22.5
            c.line(arc(50, 70, 44, a0, a0 + 11, steps=1).map(lambda x, y: (x, 70 + (y - 70) * 14 / 44)), WHITE, 2.0, glow=0.5, core=0)
    return c.svg()


def hand():
    c = kit.Ctx(200, 200, unit=1.0)
    c.halo(100, 100, 40, CORAL, 0.3)
    c.tube(circle(100, 100, 82), CORAL, w=6, glass=0.35, glow=1.6)
    c.line(circle(100, 100, 66), "#FFB0B0", 2.5, glow=0.6, core=0.5)
    hand_shape(c, 100, 110, 1.35, WHITE)
    return c.svg()


def balloon(i):
    col = (PINK, CYAN, YELLOW)[i]
    c = kit.Ctx(100, 140, unit=1.4)
    c.line(Shape([("M", 50, 92), ("C", 40, 108, 60, 118, 48, 136)]), LAVENDER, 1.6, glow=0.4, core=0)
    solid(c, ellipse(50, 50, 34, 42), col, glass=0.3)
    solid(c, poly([(44, 96), (56, 96), (50, 88)]), col)
    c.line(arc(38, 38, 14, 200, 260), WHITE, 3, glow=0.4, core=0)
    c.face(50, 52, 10, "idle", cheeks=True)
    return c.svg()


def note_icon(i):
    c = kit.Ctx(60, 60, unit=1.0)
    col = NOTE_COLOURS[i]
    c.halo(24, 42, 8, col, 0.2)
    c.fill(ellipse(22, 44, 11, 8).rotate(-20, 22, 44), col)
    c.stroke(path([(31, 42), (31, 10), (48, 18)]), col, 4)
    return c.svg()


def tape(i):
    col = TAPE_COLOURS[i]
    c = kit.Ctx(120, 80, unit=1.4)
    solid(c, rrect(6, 8, 108, 64, 12), col, glass=0.22)
    c.fill(rrect(22, 20, 76, 26, 10), BASE)
    c.line(rrect(22, 20, 76, 26, 10), col, 2, glow=0.5, core=0.4)
    for x in (42, 78):
        c.tube(circle(x, 33, 8), WHITE, w=1.8, glass=0.2, glow=0.5)
    c.line(poly([(36, 72), (44, 56), (76, 56), (84, 72)], close=False), col, 2.2, glow=0.5, core=0)
    for k in range(5):
        c.fill(circle(26 + k * 17, 64, 2.6), NOTE_COLOURS[(k + i) % 5])
    return c.svg()


TOYS = ("xylo", "band", "freeze", "highlow", "record", "listen")
ICONS = ("home", "lock", "sun", "moon", "snail", "rabbit", "play", "stop", "rec", "replay", "mute", "plus", "star", "mouse", "slot")


def build():
    for t in TOYS:
        kit.write_svg(kit.ART / "toys" / f"{t}.svg", toy(t), (120, 120))
    out = kit.ART / "ui"
    for name in ICONS:
        kit.write_svg(out / f"{name}.svg", icon(name), (100, 100))
    kit.write_svg(out / "hand.svg", hand(), (200, 200))
    for i in range(3):
        kit.write_svg(out / f"balloon_{i}.svg", balloon(i), (100, 140))
    for i in range(5):
        kit.write_svg(out / f"note_{i}.svg", note_icon(i), (60, 60))
    for i in range(8):
        kit.write_svg(out / f"tape_{i}.svg", tape(i), (120, 80))
    print(f"ui: {len(TOYS)} toys, {len(ICONS) + 1 + 3 + 5 + 8} icons")


if __name__ == "__main__":
    build()
