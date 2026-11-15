"""聽聽看's picture cards (docs/art.md listen/): `listen/<id>.svg`, 160 x 160, one thing of Taiwanese daily
life each, big and simple, with a small face where a thing can have one. The cat, the dog and the frog
use the band animals (animals/<id>_idle.svg).

garbage (the garbage truck), scooter, mrt, rain, temple, bike, crossing, ricecooker, stirfry.
"""
import math
import sys

sys.dont_write_bytecode = True

import kit  # noqa: E402
from kit import (CORAL, CREAM, CYAN, GOLD, GREEN, LAVENDER, LILAC, MINT, ORANGE, PINK, SKY, WHITE, YELLOW,  # noqa: E402
                 Shape, arc, circle, ellipse, path, poly, rrect)

BASE = "#24204A"


def solid(c, shape, col, glass=0.2, w=3.0, glow=1.0):
    c.fill(shape, BASE)
    c.tube(shape, col, w=w, glass=glass, glow=glow)


def wheel(c, x, y, r, col=LAVENDER):
    solid(c, circle(x, y, r), col, glass=0.15)
    c.glowdot(x, y, r * 0.3, col, 0.2)


def garbage():
    c = kit.Ctx(160, 160, unit=1.3)
    solid(c, rrect(14, 52, 92, 64, 10), YELLOW)          # the yellow body
    solid(c, rrect(104, 66, 44, 50, 10, rtr=18), YELLOW)   # the cab
    solid(c, rrect(116, 74, 24, 18, 5), CYAN, glass=0.35)  # window
    wheel(c, 40, 120, 14)
    wheel(c, 124, 120, 14)
    c.face(60, 80, 12, "idle")
    for k, (x, y) in enumerate(((30, 30), (52, 18), (78, 26))):
        c.note(x, y, 12, (PINK, CYAN, GREEN)[k])
    return c.svg()


def scooter():
    c = kit.Ctx(160, 160, unit=1.3)
    wheel(c, 36, 116, 18)
    wheel(c, 126, 116, 18)
    body = Shape([("M", 30, 96), ("C", 34, 72, 70, 70, 84, 86), ("L", 110, 86), ("L", 122, 50), ("L", 132, 50),
                  ("L", 124, 100), ("L", 30, 100), ("Z",)])
    solid(c, body, PINK)
    solid(c, rrect(40, 68, 40, 12, 6), LILAC)               # the seat
    c.line(path([(118, 46), (140, 40)]), LAVENDER, 3.4)    # the handlebar
    c.face(58, 88, 9, "idle", cheeks=False)
    for k in range(3):                                      # 噗噗噗
        c.fill(circle(14 - k * 2, 100 - k * 14, 5 + k * 2), WHITE, op=0.35 - k * 0.08)
    return c.svg()


def mrt():
    c = kit.Ctx(160, 160, unit=1.3)
    solid(c, rrect(16, 30, 128, 100, 22), SKY, glass=0.15)
    solid(c, rrect(40, 52, 38, 66, 6), LAVENDER, glass=0.15)   # the two doors, closing
    solid(c, rrect(82, 52, 38, 66, 6), LAVENDER, glass=0.15)
    for x in (52, 108):
        c.fill(rrect(x - 8, 60, 16, 22, 4), CYAN, op=0.4)
    c.line(path([(16, 44), (144, 44)]), CYAN, 2.4)
    for k in range(3):
        c.glowdot(62 + k * 18, 20, 4, CORAL, 0.35)               # 嗶嗶嗶
    c.face(80, 96, 8, "idle", cheeks=False)
    return c.svg()


def rain():
    c = kit.Ctx(160, 160, unit=1.3)
    cloud = circle(56, 60, 24) + circle(86, 50, 30) + circle(112, 64, 22) + rrect(36, 60, 96, 26, 13)
    c.fill(cloud, BASE)
    c.fill(cloud, SKY, op=0.2)
    for s in (circle(56, 60, 24), circle(86, 50, 30), circle(112, 64, 22)):
        c.line(s, SKY, 3, glow=0.8)
    c.fill(rrect(38, 58, 92, 26, 13), BASE)
    c.fill(rrect(38, 58, 92, 26, 13), SKY, op=0.2)
    c.line(Shape([("M", 36, 84), ("L", 132, 84)]), SKY, 3)
    c.face(84, 64, 10, "idle")
    for x, y in ((46, 104), (70, 118), (94, 104), (118, 118), (58, 136), (106, 140)):
        drop = Shape([("M", x, y - 10), ("C", x + 8, y, x + 6, y + 8, x, y + 8), ("C", x - 6, y + 8, x - 8, y, x, y - 10), ("Z",)])
        c.tube(drop, CYAN, w=2.2, glass=0.4)
    return c.svg()


def temple():
    c = kit.Ctx(160, 160, unit=1.3)
    roof = Shape([("M", 10, 58), ("C", 40, 54, 60, 40, 80, 22), ("C", 100, 40, 120, 54, 150, 58),
                  ("L", 132, 66), ("L", 28, 66), ("Z",)])
    solid(c, roof, CORAL)
    for x in (12, 148):
        c.line(Shape([("M", x, 58), ("C", x, 50, x + (6 if x < 80 else -6), 44, x + (2 if x < 80 else -2), 38)]), CORAL, 2.6)
    solid(c, rrect(36, 66, 88, 70, 4), GOLD, glass=0.12)
    solid(c, ellipse(80, 104, 26, 26), PINK)                 # the big drum
    c.line(circle(80, 104, 18), PINK, 1.8, glow=0.4, core=0.3)
    c.face(80, 102, 9, "idle", cheeks=False)
    c.glowdot(80, 18, 4, YELLOW, 0.35)
    return c.svg()


def bike():
    c = kit.Ctx(160, 160, unit=1.3)
    wheel(c, 40, 110, 26, MINT)
    wheel(c, 122, 110, 26, MINT)
    c.line(path([(40, 110), (68, 70), (110, 70), (122, 110)]), GREEN, 3.4)
    c.line(path([(68, 70), (80, 110), (110, 70)]), GREEN, 3.0)
    c.line(path([(106, 60), (112, 72)]), GREEN, 3.0)
    c.line(path([(98, 56), (120, 52)]), LAVENDER, 3.4)
    c.line(path([(60, 62), (78, 62)]), LILAC, 4.4)
    solid(c, circle(126, 44, 10), YELLOW, glass=0.5)           # the bell
    for r in (16, 24):
        c.line(arc(126, 44, r, -60, 30), YELLOW, 2.0, glow=0.5, core=0)
    return c.svg()


def crossing():
    c = kit.Ctx(160, 160, unit=1.3)
    c.line(path([(80, 60), (80, 150)]), LAVENDER, 4)
    for ang in (35, -35):                                     # the X sign
        bar = rrect(34, 36, 92, 14, 7).rotate(ang, 80, 43)
        solid(c, bar, YELLOW, glass=0.3)
    solid(c, rrect(46, 66, 68, 30, 15), LAVENDER, glass=0.12)
    c.glowdot(62, 81, 9, CORAL, 0.4)                          # one light on,
    c.tube(circle(98, 81, 9), CORAL, w=2, glass=0.15, glow=0.4)   # the other off
    return c.svg()


def ricecooker():
    c = kit.Ctx(160, 160, unit=1.3)
    body = rrect(24, 58, 112, 76, 30)
    solid(c, body, CREAM, glass=0.15)
    lid = Shape([("M", 28, 64), ("C", 34, 34, 126, 34, 132, 64), ("Z",)])
    solid(c, lid, CREAM, glass=0.15)
    solid(c, rrect(70, 32, 20, 10, 5), LAVENDER)
    solid(c, rrect(64, 102, 32, 16, 6), PINK, glass=0.35)    # the switch, popped up
    c.glowdot(110, 108, 4, CORAL, 0.35)
    c.face(80, 80, 12, "cheer")
    for x in (60, 80, 100):                                    # steam
        c.line(Shape([("M", x, 28), ("C", x - 8, 20, x + 8, 12, x, 4)]), WHITE, 1.8, glow=0.4, core=0)
    return c.svg()


def stirfry():
    c = kit.Ctx(160, 160, unit=1.3)
    c.line(path([(132, 92), (156, 84)]), LAVENDER, 6)        # the handle
    wok = Shape([("M", 14, 82), ("L", 134, 82), ("C", 128, 128, 30, 128, 14, 82), ("Z",)])
    solid(c, wok, LAVENDER, glass=0.12)
    for x, y, col in ((50, 76, GREEN), (72, 72, ORANGE), (96, 76, GREEN), (82, 80, CORAL)):
        c.tube(ellipse(x, y, 10, 6), col, w=2, glass=0.5, glow=0.6)
    c.line(path([(84, 70), (112, 24)]), GOLD, 3.4)             # the spatula
    solid(c, rrect(104, 10, 18, 22, 4).rotate(30, 113, 21), GOLD, glass=0.3)
    c.face(74, 100, 10, "idle", cheeks=True)
    for k, (x, y) in enumerate(((30, 50), (46, 38), (128, 58))):   # 滋～ sparks
        c.glowdot(x, y, 2.6, YELLOW, 0.35)
    return c.svg()


PICTURES = {"garbage": garbage, "scooter": scooter, "mrt": mrt, "rain": rain, "temple": temple, "bike": bike,
            "crossing": crossing, "ricecooker": ricecooker, "stirfry": stirfry}


def build():
    for name, draw in PICTURES.items():
        kit.write_svg(kit.ART / "listen" / f"{name}.svg", draw(), (160, 160))
    print(f"listen: {len(PICTURES)} pictures")


if __name__ == "__main__":
    build()
