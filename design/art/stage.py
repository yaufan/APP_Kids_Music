"""The stage (docs/art.md stage/): the night background, the neon curtains and the swags over them, the
glowing floor the band stands on, a spotlight beam and the audience's little eyes.

- `stage/bg.svg` 400 x 860 (drawn to cover the screen): deep navy to purple, soft stars.
- `stage/curtain_left.svg`, `stage/curtain_right.svg` 110 x 700: neon drapes, tied back.
- `stage/valance.svg` 400 x 90: the row of swags across the top.
- `stage/floor.svg` 400 x 150: the glowing stage floor (the band's spots are drawn on it by the app).
- `stage/spot.svg` 200 x 560: a soft beam of light (see-through; the app tints it by colouring under it).
- `stage/audience.svg` 400 x 70: a row of happy glowing eyes in the dark (they clap now and then).
"""
import sys

sys.dont_write_bytecode = True

import kit  # noqa: E402
from kit import BG_BOT, BG_TOP, CORAL, CREAM, MINT, PINK, WHITE, YELLOW, Shape, arc, circle, ellipse, path, poly, rrect  # noqa: E402


def bg():
    c = kit.Ctx(400, 860, unit=1.0)
    c.fill(rrect(0, 0, 400, 860, 0), c.gradient([(0, BG_TOP, 1), (0.6, "#221F48", 1), (1, BG_BOT, 1)]))
    c.fill(ellipse(200, 520, 260, 300), c.radial([(0, "#3A3270", 0.55), (1, "#3A3270", 0)]))
    r = kit.rnd("stars")
    for _ in range(70):
        x, y = r.uniform(4, 396), r.uniform(4, 820)
        s = r.choice((0.8, 1.0, 1.2, 1.6, 2.2))
        c.fill(circle(x, y, s), WHITE, op=r.uniform(0.25, 0.7))
    for x, y in ((60, 120), (330, 200), (300, 640), (90, 560)):
        c.glowdot(x, y, 2.4, CREAM, 0.25)
    return c.svg()


def curtain(right=False):
    w, h = 110, 700
    c = kit.Ctx(w, h, unit=1.2)
    folds = []
    for k in range(4):
        x0 = 8 + k * 24
        tie_y = 430
        tie_x = 14 + k * 8
        s = Shape([("M", x0, -10), ("C", x0 + 8, 160, tie_x + 30, 300, tie_x, tie_y),
                   ("C", tie_x - 4, 520, x0 - 6 + k * 4, 620, x0 + k * 3, h - 6)])
        folds.append(s)
    body = Shape([("M", 0, 0), ("L", 104, 0), ("C", 92, 180, 60, 330, 40, 430), ("C", 52, 520, 70, 620, 92, h),
                  ("L", 0, h), ("Z",)])
    if right:
        body = body.flip(w / 2)
        folds = [f.map(lambda x, y: (w - x, y)) for f in folds]
    c.fill(body, PINK, op=0.07)
    for f in folds:
        c.line(f, CORAL if not right else PINK, 2.6, glow=1.0, core=0.6)
    tie = ellipse(w - 70 if right else 70, 432, 18, 9)
    c.tube(tie, YELLOW, w=2.6, glass=0.3)
    return c.svg()


def valance():
    c = kit.Ctx(400, 90, unit=1.2)
    for k in range(-1, 6):
        x = 40 + k * 80
        swag = Shape([("M", x - 44, 10), ("C", x - 30, 72, x + 30, 72, x + 44, 10)])
        c.line(swag, PINK, 3.2, glow=1.2)
        c.line(Shape([("M", x - 36, 8), ("C", x - 20, 48, x + 20, 48, x + 36, 8)]), CORAL, 2.0, glow=0.6, core=0.4)
        c.glowdot(x + 44, 14, 4, YELLOW, 0.3)
    c.line(path([(0, 6), (400, 6)]), PINK, 3.0, glow=1.0)
    return c.svg()


def floor():
    c = kit.Ctx(400, 150, unit=1.2)
    top = rrect(10, 12, 380, 96, 40)
    c.fill(top, c.gradient([(0, MINT, 0.22), (1, MINT, 0.06)]))
    for k in range(9):
        x = 40 + k * 40
        c.fill(rrect(x - 7, 26, 14, 70, 7), MINT, op=0.10)
    c.line(top, MINT, 3.2, glow=1.2)
    lip = Shape([("M", 30, 108), ("C", 120, 128, 280, 128, 370, 108)])
    c.line(lip, MINT, 2.4, glow=0.8, core=0.4)
    for k in range(12):
        x = 30 + k * 31
        c.glowdot(x, 132, 3, YELLOW if k % 2 else PINK, 0.3)
    return c.svg()


def spot():
    c = kit.Ctx(200, 560, unit=1.0)
    beam = poly([(80, 0), (120, 0), (196, 560), (4, 560)])
    c.fill(beam, c.gradient([(0, "#FFF4C8", 0.5), (0.7, "#FFF4C8", 0.14), (1, "#FFF4C8", 0.0)]))
    return c.svg()


def audience():
    c = kit.Ctx(400, 70, unit=1.0)
    r = kit.rnd("audience")
    for k in range(9):
        x = 24 + k * 44 + r.uniform(-6, 6)
        y = 34 + r.uniform(-8, 8)
        head = ellipse(x, y + 8, 18, 16)
        c.fill(head, "#3A3470", op=0.8)
        for side in (-1, 1):
            c.line(arc(x + side * 6, y + 6, 4, 200, 340), WHITE, 1.8, glow=0.5, core=0)
        c.fill(ellipse(x, y + 14, 3, 2), PINK, op=0.8)
    return c.svg()


def build():
    out = kit.ART / "stage"
    kit.write_svg(out / "bg.svg", bg(), (400, 860))
    kit.write_svg(out / "curtain_left.svg", curtain(False), (110, 700))
    kit.write_svg(out / "curtain_right.svg", curtain(True), (110, 700))
    kit.write_svg(out / "valance.svg", valance(), (400, 90))
    kit.write_svg(out / "floor.svg", floor(), (400, 150))
    kit.write_svg(out / "spot.svg", spot(), (200, 560))
    kit.write_svg(out / "audience.svg", audience(), (400, 70))
    print("stage: 7 files")


if __name__ == "__main__":
    build()
