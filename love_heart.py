"""Multilingual "I love you" heart (turtle + tkinter).

Recreated from the video:
  1. words appear one by one, starting at the top-middle notch and tracing
     the heart OUTLINE clockwise (right side, bottom tip, left side)
  2. then the inside fills in with more words
Each word fades in. Standard library only.
"""
import math as m
import random as r
import turtle as t
import tkinter.font as tkf

FONT = "Segoe UI"          # falls back automatically if missing (try "Arial Unicode MS", "Noto Sans")
SCALE = 23                 # heart size
CX, CY = 0, 10             # heart centre on the canvas

# --- animation timing -------------------------------------------------------
START_DELAY_MS = 400       # pause before the first word
OUTLINE_MS = 60            # delay between words while tracing the outline
FILL_MS = 40               # delay between ticks while filling the inside
FILL_BATCH = 1             # words per tick during the fill (raise to fill faster)
FADE_STEPS = 5             # frames each word takes to fade in
FADE_MS = 30               # time per fade frame

# --- layout knobs -----------------------------------------------------------
OUTLINE_SIZES = [12, 11, 10, 9]                   # text sizes used on the outline
SIZES = [17, 15, 13, 12, 11, 10, 9, 8, 7, 6]      # sizes used to fill the inside
PAD = 1                                           # gap between phrases in px (0-3)
TRIES_PER_SIZE = 20000                            # max attempts per size
FAIL_LIMIT = 3000                                 # give up on a size after this many misses in a row

PHRASES = [
    "I love you", "Seni seviyorum", "Te amo", "Je t'aime",
    "Ich liebe dich", "Ti amo", "Eu te amo", "Я тебя люблю",
    "사랑해", "愛してる", "我爱你", "मैं तुमसे प्यार करता हूँ",
    "Σ' αγαπώ", "Ik hou van jou", "Jag älskar dig", "Kocham cię",
    "ฉันรักเธอ", "Anh yêu em", "Aku cinta kamu", "Я тебе кохаю",
    "Ég elska þig", "Rakastan sinua", "Jeg elsker deg", "Jeg elsker dig",
    "Szeretlek", "Te iubesc", "Miluji tě", "Ľúbim ťa", "Volim te",
    "Obožujem te", "Mīlu tevi", "Aš tave myliu", "Armastan sind",
    "Ma wuxuu ahay jacayl", "Mahal kita", "Saya cinta awak",
    "Ani ohev otach", "أنا أحبك", "دوستت دارم", "আমি তোমাকে ভালোবাসি",
    "நான் உன்னை காதலிக்கிறேன்", "Nakupenda", "Ngiyakuthanda",
    "Σε αγαπώ", "Mi amas vin", "Es mīl tevi", "Te quiero", "Ti voglio bene",
    "Ik hou van je", "Ich hab dich lieb", "Love you", "Amor", "Amour",
    "Liebe", "愛", "爱", "사랑", "Любовь", "Αγάπη",
]

REDS = ["#ff3b3b", "#e8312f", "#ff5a5a", "#d62828", "#ff7070", "#c1121f"]

s = t.Screen()
s.setup(900, 820)
s.bgcolor("black")
s.title("love heart")
t.tracer(0)
t.hideturtle()
cv = s.getcanvas()
rng = r.Random(11)         # fixed seed -> same layout every run

_fonts = {}


def font_for(size):
    if size not in _fonts:
        _fonts[size] = tkf.Font(root=cv, family=FONT, size=size, weight="bold")
    return _fonts[size]


def heart(a):
    """Classic parametric heart, returned in canvas coordinates."""
    x = 16 * m.sin(a) ** 3
    y = (13 * m.cos(a)
         - 5 * m.cos(2 * a)
         - 2 * m.cos(3 * a)
         - m.cos(4 * a))
    return x * SCALE + CX, y * SCALE + CY


OUTLINE = [heart(i * 2 * m.pi / 400) for i in range(400)]


ROW = 2                                     # scanline height in px
YMIN = min(y for _, y in OUTLINE)


def _scanlines():
    """For every row, work out once which x-ranges are inside the heart."""
    rows = []
    n = len(OUTLINE)
    ymax = max(y for _, y in OUTLINE)
    for k in range(int((ymax - YMIN) / ROW) + 2):
        py = YMIN + k * ROW + ROW / 2
        xs = []
        for i in range(n):
            x1, y1 = OUTLINE[i]
            x2, y2 = OUTLINE[(i + 1) % n]
            if (y1 > py) != (y2 > py):
                xs.append((x2 - x1) * (py - y1) / (y2 - y1) + x1)
        xs.sort()
        rows.append(list(zip(xs[0::2], xs[1::2])))
    return rows


SCAN = _scanlines()


def inside(px, py):
    k = int((py - YMIN) / ROW)
    if k < 0 or k >= len(SCAN):
        return False
    for a, b in SCAN[k]:
        if a <= px <= b:
            return True
    return False


CELL = 32
_info = {}


def size_info(size):
    """(font, line height, {phrase: width}) for a text size, cached."""
    if size not in _info:
        f = font_for(size)
        _info[size] = (f, f.metrics("linespace"), {p: f.measure(p) for p in PHRASES})
    return _info[size]


def cells(x1, y1, x2, y2):
    for gx in range(int(x1 // CELL), int(x2 // CELL) + 1):
        for gy in range(int(y1 // CELL), int(y2 // CELL) + 1):
            yield gx, gy


def try_place(grid, items, px, py, text, size):
    """Place `text` centred at (px, py) if it fits inside the heart and
    doesn't touch another phrase. Returns True when placed."""
    _, h, widths = size_info(size)
    w = widths[text]
    x1, y1, x2, y2 = px - w / 2, py - h / 2, px + w / 2, py + h / 2
    if not (inside(px, py) and inside(x1, y1) and inside(x2, y1)
            and inside(x1, y2) and inside(x2, y2)):
        return False
    box = (x1 - PAD, y1 - PAD, x2 + PAD, y2 + PAD)
    for c in cells(*box):
        for bx1, by1, bx2, by2 in grid.get(c, ()):
            if box[0] < bx2 and box[2] > bx1 and box[1] < by2 and box[3] > by1:
                return False
    for c in cells(*box):
        grid.setdefault(c, []).append(box)
    color = "#ffffff" if rng.random() < 0.05 else rng.choice(REDS)
    items.append((px, py, text, size, color))
    return True


def layout_outline(grid):
    """Walk round the heart outline starting at the top-middle notch and going
    clockwise, dropping a phrase wherever one fits just inside the edge."""
    items = []
    gx = sum(x for x, _ in OUTLINE) / len(OUTLINE)
    gy = sum(y for _, y in OUTLINE) / len(OUTLINE)
    steps = 1800
    for k in range(steps):
        ox, oy = heart(2 * m.pi * k / steps)   # a=0 is the top notch; a grows clockwise
        dx, dy = gx - ox, gy - oy
        d = m.hypot(dx, dy) or 1
        nx, ny = dx / d, dy / d                # unit vector pointing inwards
        for _ in range(4):                     # a few attempts per spot
            size = rng.choice(OUTLINE_SIZES)
            text = rng.choice(PHRASES)
            _, h, widths = size_info(size)
            reach = abs(nx) * widths[text] / 2 + abs(ny) * h / 2 + 2
            if try_place(grid, items, ox + nx * reach, oy + ny * reach, text, size):
                break
    return items


def layout_fill(grid):
    """Pack the inside with phrases, big first so small ones fill the gaps."""
    items = []
    for size in SIZES:
        misses = 0
        for _ in range(TRIES_PER_SIZE):
            if misses > FAIL_LIMIT:
                break
            misses += 1
            text = rng.choice(PHRASES)
            px = rng.uniform(-17 * SCALE, 17 * SCALE) + CX
            py = rng.uniform(-14 * SCALE, 14 * SCALE) + CY
            if try_place(grid, items, px, py, text, size):
                misses = 0
    rng.shuffle(items)
    return items


_grid = {}
OUTLINE_ITEMS = layout_outline(_grid)
ITEMS = OUTLINE_ITEMS + layout_fill(_grid)
N_OUTLINE = len(OUTLINE_ITEMS)
i = 0


def mix(color, k):
    """Colour `color` at brightness k (0 = black, 1 = full)."""
    return "#%02x%02x%02x" % tuple(int(int(color[j:j + 2], 16) * k) for j in (1, 3, 5))


def fade_in(item, color, step=1):
    cv.itemconfigure(item, fill=mix(color, step / FADE_STEPS))
    if step < FADE_STEPS:
        s.ontimer(lambda: fade_in(item, color, step + 1), FADE_MS)


def show(entry):
    px, py, text, size, color = entry
    # turtle's canvas has its origin at the centre with y pointing up
    item = cv.create_text(px, -py, text=text, fill="#000000", font=font_for(size))
    fade_in(item, color)


def spawn():
    global i
    n = 1 if i < N_OUTLINE else FILL_BATCH     # outline: strictly one by one
    for _ in range(n):
        if i >= len(ITEMS):
            return
        show(ITEMS[i])
        i += 1
    s.ontimer(spawn, OUTLINE_MS if i <= N_OUTLINE else FILL_MS)


s.ontimer(spawn, START_DELAY_MS)
s.mainloop()