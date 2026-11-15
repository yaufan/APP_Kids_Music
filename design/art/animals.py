"""The ten band animals, in neon (docs/art.md animals/): `animals/<id>_<pose>.svg`, 200 x 200, the feet at
y = 188, facing us, faces always showing.

Poses: idle (standing, smiling), sing (eyes happily closed, mouth open, a note), frozen (stiff, arms
down, big round eyes: 音樂木頭人), cheer (arms up, a big smile).

Every animal is built the same way (back parts, body, arms, feet, head, front parts, face) so they read
as one band; each has its own colour and two or three things that say what it is (the bear's round
ears and muzzle, the frog's eye bumps, the 台灣黑熊's white V, the 石虎's forehead stripes, the 藍鵲's
black head, red beak and long tail...).
"""
import sys

sys.dont_write_bytecode = True

import kit  # noqa: E402
from kit import (BLUE, CORAL, CREAM, CYAN, DARK, GOLD, GREEN, LILAC, ORANGE, PINK, SKY, WHITE, YELLOW,  # noqa: E402
                 Shape, arc, circle, ellipse, path, poly, rrect)

W = H = 200
UNIT = 1.55            # drawn about 130 pt wide
POSES = ("idle", "sing", "frozen", "cheer")
BASE = "#24204A"       # an opaque dark under every part, so the parts in front hide the lines behind

ANIMALS = {            # id: (colour, 中文)
    "bear": (ORANGE, "小熊"),
    "frog": (GREEN, "青蛙"),
    "bird": (CYAN, "小鳥"),
    "cat": (PINK, "小貓"),
    "dog": (LILAC, "小狗"),
    "elephant": (SKY, "小象"),
    "blackbear": ("#DAD4FF", "台灣黑熊"),
    "leopard": (GOLD, "石虎"),
    "magpie": (BLUE, "藍鵲"),
    "duck": (YELLOW, "小鴨"),
}


def part(c, shape, col, glass=0.18, w=3.0, glow=1.0):
    """One solid neon part: an opaque base (hides what is behind), the glass and the tube."""
    c.fill(shape, BASE)
    c.tube(shape, col, w=w, glass=glass, glow=glow)


def arms(c, col, pose, at_y=138, spread=44, size=(11, 19)):
    """Two round arms, by the pose."""
    rx, ry = size
    for side in (-1, 1):
        x = 100 + side * spread
        if pose == "cheer":
            s = ellipse(x + side * 6, at_y - 34, rx, ry + 2).rotate(side * 28, x + side * 6, at_y - 34)
        elif pose == "sing":
            s = ellipse(x + side * 4, at_y - 4, rx, ry).rotate(side * 50, x + side * 4, at_y - 4)
        elif pose == "frozen":
            s = ellipse(x - side * 2, at_y + 6, rx * 0.9, ry + 1)
        else:
            s = ellipse(x, at_y + 2, rx, ry).rotate(side * 18, x, at_y + 2)
        part(c, s, col)


def feet(c, col, y=180, gap=22, size=(15, 9)):
    for side in (-1, 1):
        part(c, ellipse(100 + side * gap, y, *size), col)


def sing_note(c, col, pose, x=150, y=48):
    if pose == "sing":
        c.halo(x, y, 9, col, 0.15)
        c.note(x, y, 14, col)
    if pose == "cheer":
        for (sx, sy, r) in ((40, 40, 4), (162, 34, 5), (172, 70, 3)):
            c.glowdot(sx, sy, r, YELLOW, 0.3)


def face_mood(pose):
    return {"idle": "idle", "sing": "sing", "frozen": "frozen", "cheer": "cheer"}[pose]


def frozen_marks(c, pose, col):
    """Stiff as a statue: two little lines beside the head."""
    if pose != "frozen":
        return
    for side in (-1, 1):
        x = 100 + side * 70
        c.line(path([(x, 50), (x + side * 8, 44)]), WHITE, 2, glow=0.4, core=0)
        c.line(path([(x + side * 2, 62), (x + side * 11, 60)]), WHITE, 2, glow=0.4, core=0)


# ---------------------------------------------------------------- the animals
def bear(c, pose, col=ORANGE, chest_v=False):
    for side in (-1, 1):
        part(c, circle(100 + side * 36, 44, 15), col)
        c.fill(circle(100 + side * 36, 44, 7), PINK, op=0.55)
    part(c, ellipse(100, 146, 44, 38), col)
    if chest_v:
        c.line(path([(76, 124), (100, 150), (124, 124)]), CREAM, 4.2, glow=1.4)
    else:
        c.fill(ellipse(100, 152, 24, 20), CREAM, op=0.22)
    arms(c, col, pose)
    feet(c, col)
    part(c, circle(100, 80, 46), col)
    part(c, ellipse(100, 98, 20, 15), CREAM, glass=0.25, w=2.4, glow=0.7)
    c.fill(ellipse(100, 91, 7, 5), DARK)
    c.face(100, 76, 22, face_mood(pose), cheeks=True)


def frog(c, pose):
    col = GREEN
    part(c, ellipse(100, 148, 46, 36), col)
    c.fill(ellipse(100, 154, 28, 20), CREAM, op=0.2)
    arms(c, col, pose, spread=46)
    for side in (-1, 1):       # big flat feet
        part(c, ellipse(100 + side * 26, 182, 20, 8), col)
    for side in (-1, 1):       # the eye bumps
        part(c, circle(100 + side * 26, 50, 22), col)
    part(c, ellipse(100, 88, 54, 38), col)
    c.fill(circle(74, 50, 22), BASE)
    c.fill(circle(126, 50, 22), BASE)
    for side in (-1, 1):
        c.tube(circle(100 + side * 26, 50, 22), col, glass=0.18)
    c.face(100, 50, 26, face_mood(pose), cheeks=False)
    for side in (-1, 1):
        c.halo(100 + side * 34, 98, 7, PINK, 0.25)
        c.fill(ellipse(100 + side * 34, 98, 9, 6), PINK, op=0.75)
    if pose in ("idle", "frozen"):
        if pose == "idle":
            c.line(arc(100, 70, 34, 50, 130), kit.MOUTH, 2.4, glow=0.5, core=0)
        else:
            c.line(path([(86, 102), (114, 102)]), kit.MOUTH, 2.2, glow=0.5, core=0)


def bird(c, pose, col=CYAN, magpie=False):
    # tail
    if magpie:   # 藍鵲's long tail with white tips, out to the side
        for ang in (34, 50):
            t = rrect(112, 132, 78, 12, 6).rotate(ang, 112, 138)
            part(c, t, col, w=2.4)
            c.fill(circle(184, 138, 6).rotate(ang, 112, 138), WHITE, op=0.85)
    else:
        part(c, poly([(132, 140), (166, 120), (162, 150)]), col, w=2.6)
    # the round body that is also the head
    body = ellipse(100, 112, 58, 66)
    part(c, body, col)
    c.fill(ellipse(100, 134, 34, 34), CREAM, op=0.18)
    if magpie:   # the black head
        hood = Shape([("M", 46, 100), ("C", 46, 52, 76, 46, 100, 46), ("C", 124, 46, 154, 52, 154, 100),
                      ("C", 134, 92, 66, 92, 46, 100), ("Z",)])
        c.fill(hood, "#0E0C24", op=0.85)
        c.line(hood, LILAC, 2.0, glow=0.6, core=0)
    else:        # a little crest
        c.line(Shape([("M", 96, 48), ("C", 92, 34, 100, 26, 106, 30)]), col, 3, glow=0.8)
        c.line(Shape([("M", 102, 48), ("C", 104, 36, 114, 32, 118, 38)]), col, 3, glow=0.8)
    # wings
    for side in (-1, 1):
        if pose == "cheer":
            w_ = ellipse(100 + side * 58, 92, 12, 26).rotate(side * 35, 100 + side * 58, 92)
        elif pose == "frozen":
            w_ = ellipse(100 + side * 52, 126, 10, 24)
        else:
            w_ = ellipse(100 + side * 56, 122, 11, 26).rotate(side * 20, 100 + side * 56, 122)
        part(c, w_, col)
    beak_col = CORAL if magpie else ORANGE
    for side in (-1, 1):
        part(c, ellipse(100 + side * 16, 182, 11, 6), beak_col, w=2.4)
    c.face(100, 84, 22, face_mood(pose), cheeks=True)
    # the beak (the mouth)
    if pose in ("sing", "cheer"):
        part(c, poly([(88, 100), (112, 100), (100, 110)]), beak_col, glass=0.5, w=2.4)
        part(c, poly([(90, 114), (110, 114), (100, 124)]), beak_col, glass=0.5, w=2.4)
    else:
        part(c, poly([(88, 100), (112, 100), (100, 116)]), beak_col, glass=0.5, w=2.4)


def cat(c, pose, col=PINK, stripes=False, spots=False):
    # tail
    c.line(Shape([("M", 136, 166), ("C", 172, 168, 178, 130, 160, 116)]), col, 6, glow=1.0)
    if spots:
        for y in (120, 132, 146):
            c.fill(circle(170 - (y - 116) * 0.3, y, 3.2), DARK, op=0.9)
    part(c, ellipse(100, 148, 40, 36), col)
    c.fill(ellipse(100, 154, 22, 18), CREAM, op=0.2)
    if spots:
        for x, y in ((80, 136), (118, 132), (90, 162), (122, 158), (106, 144)):
            c.fill(circle(x, y, 4), DARK, op=0.85)
            c.line(circle(x, y, 4), col, 1.0, glow=0, core=0)
    arms(c, col, pose, spread=40, size=(10, 17))
    feet(c, col, gap=20, size=(13, 8))
    for side in (-1, 1):   # ears
        if spots:   # 石虎: rounder ears with a white spot
            e = ellipse(100 + side * 34, 46, 15, 17).rotate(side * 15, 100 + side * 34, 46)
            part(c, e, col)
            c.fill(circle(100 + side * 34, 46, 5), WHITE, op=0.85)
        else:
            e = poly([(100 + side * 18, 52), (100 + side * 46, 20), (100 + side * 48, 64)])
            part(c, e, col)
            c.fill(poly([(100 + side * 26, 52), (100 + side * 43, 32), (100 + side * 43, 56)]), PINK, op=0.5)
    part(c, ellipse(100, 82, 48, 42), col)
    if stripes:  # 石虎's two white stripes over the forehead, from the eyes up
        for side in (-1, 1):
            c.line(Shape([("M", 100 + side * 10, 66), ("C", 100 + side * 8, 56, 100 + side * 6, 50, 100 + side * 4, 42)]),
                   WHITE, 3.2, glow=0.8)
        for x in (80, 120):
            c.fill(circle(x, 52, 3), DARK, op=0.8)
    for side in (-1, 1):   # whiskers
        for dy in (-4, 4):
            c.line(path([(100 + side * 30, 96 + dy), (100 + side * 58, 92 + dy * 2.2)]), WHITE, 1.4, glow=0.4, core=0)
    c.fill(poly([(94, 90), (106, 90), (100, 96)]), PINK)
    c.face(100, 80, 20, face_mood(pose), cheeks=True)


def dog(c, pose):
    col = LILAC
    c.line(Shape([("M", 136, 160), ("C", 160, 156, 166, 136, 160, 124)]), col, 6, glow=1.0)
    part(c, ellipse(100, 148, 40, 36), col)
    c.fill(ellipse(100, 154, 22, 18), CREAM, op=0.2)
    arms(c, col, pose, spread=40, size=(10, 17))
    feet(c, col, gap=20, size=(13, 8))
    part(c, ellipse(100, 82, 46, 42), col)
    for side in (-1, 1):   # floppy ears
        e = ellipse(100 + side * 46, 84, 14, 28).rotate(side * -15, 100 + side * 46, 84)
        part(c, e, col)
        c.fill(ellipse(100 + side * 46, 90, 7, 16).rotate(side * -15, 100 + side * 46, 90), PINK, op=0.4)
    c.fill(circle(78, 72, 9), CREAM, op=0.25)   # a patch round one eye
    part(c, ellipse(100, 100, 18, 13), CREAM, glass=0.25, w=2.2, glow=0.6)
    c.fill(ellipse(100, 94, 8, 6), DARK)
    if pose in ("idle", "cheer"):
        c.fill(ellipse(100, 112, 6, 7), PINK)   # a little tongue
    c.face(100, 76, 20, face_mood(pose), cheeks=True)


def elephant(c, pose):
    col = SKY
    for side in (-1, 1):   # big ears, behind
        part(c, ellipse(100 + side * 52, 78, 30, 36), col)
        c.fill(ellipse(100 + side * 54, 80, 18, 24), PINK, op=0.35)
    part(c, ellipse(100, 150, 42, 34), col)
    arms(c, col, pose, spread=42, size=(12, 17))
    feet(c, col, gap=22, size=(16, 9))
    part(c, circle(100, 80, 42), col)
    if pose in ("sing", "cheer"):   # the trunk up, trumpeting
        t = Shape([("M", 102, 96), ("C", 128, 104, 142, 84, 140, 56)])
    else:
        t = Shape([("M", 100, 90), ("C", 100, 120, 96, 132, 108, 136)])
    c.line(t, col, 10, glow=1.0, core=0.5)
    c.line(t, BASE, 5.4, glow=0, core=0)
    c.line(t, col, 2.0, glow=0, core=0.6)
    c.face(100, 72, 20, face_mood(pose), cheeks=True, mouth_col=kit.MOUTH)


def duck(c, pose):
    col = YELLOW
    part(c, ellipse(100, 140, 52, 42), col)
    c.fill(ellipse(100, 148, 30, 22), CREAM, op=0.2)
    part(c, poly([(146, 126), (168, 112), (160, 142)]), col, w=2.6)   # tail feathers
    for side in (-1, 1):
        if pose == "cheer":
            w_ = ellipse(100 + side * 56, 112, 11, 24).rotate(side * 40, 100 + side * 56, 112)
        elif pose == "frozen":
            w_ = ellipse(100 + side * 48, 140, 10, 22)
        else:
            w_ = ellipse(100 + side * 52, 140, 11, 24).rotate(side * 25, 100 + side * 52, 140)
        part(c, w_, col)
    for side in (-1, 1):
        part(c, ellipse(100 + side * 20, 184, 14, 6), ORANGE, w=2.4)
    part(c, circle(100, 76, 40), col)
    c.line(Shape([("M", 98, 38), ("C", 92, 26, 104, 22, 108, 30)]), col, 3, glow=0.8)
    c.face(100, 70, 19, face_mood(pose), cheeks=True)
    if pose in ("sing", "cheer"):
        part(c, rrect(84, 90, 32, 10, 5), ORANGE, glass=0.5, w=2.4)
        part(c, rrect(86, 104, 28, 9, 4.5), ORANGE, glass=0.5, w=2.4)
    else:
        part(c, rrect(82, 90, 36, 16, 8), ORANGE, glass=0.5, w=2.4)
        c.line(path([(86, 98), (114, 98)]), ORANGE, 1.4, glow=0, core=0)


DRAW = {
    "bear": lambda c, p: bear(c, p),
    "frog": frog,
    "bird": lambda c, p: bird(c, p),
    "cat": lambda c, p: cat(c, p),
    "dog": dog,
    "elephant": elephant,
    "blackbear": lambda c, p: bear(c, p, col=ANIMALS["blackbear"][0], chest_v=True),
    "leopard": lambda c, p: cat(c, p, col=GOLD, stripes=True, spots=True),
    "magpie": lambda c, p: bird(c, p, col=BLUE, magpie=True),
    "duck": duck,
}
assert set(DRAW) == set(ANIMALS)


def picture(a, pose):
    c = kit.Ctx(W, H, unit=UNIT)
    col = ANIMALS[a][0]
    # a soft pool of light under the feet
    c.fill(ellipse(100, 190, 58, 8), col, op=0.16)
    DRAW[a](c, pose)
    sing_note(c, YELLOW if a != "cat" else CYAN, pose)
    frozen_marks(c, pose, col)
    return c.svg()


def build():
    out = kit.ART / "animals"
    total = 0
    for a in ANIMALS:
        for p in POSES:
            total += kit.write_svg(out / f"{a}_{p}.svg", picture(a, p), (W, H))
    print(f"animals: {len(ANIMALS) * len(POSES)} files, {total:.0f} KB")


if __name__ == "__main__":
    build()
