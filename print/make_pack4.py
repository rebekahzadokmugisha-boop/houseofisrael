#!/usr/bin/env python3
"""House of Israel children's printing pack, four files (colouring 0-7, Little Learners 4-6,
Juniors 7-10, Seniors 11-14), each with a teacher's key. Usage: pack4.py content.json OUT_DIR"""
import json, os, sys, random, unicodedata
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white, black

FD = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
for n, f in (('Serif', 'DejaVuSerif'), ('SerifB', 'DejaVuSerif-Bold'), ('Sans', 'DejaVuSans'), ('SansB', 'DejaVuSans-Bold')):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FD, f + '.ttf')))
DEEP, GREEN, GOLD, INK, MUTE = HexColor('#123d30'), HexColor('#1d5a46'), HexColor('#b9862a'), HexColor('#16241e'), HexColor('#6b7a72')
W, H = A4
C = json.load(open(sys.argv[1])); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
DATE, PORTION, TORAH, DATE_LONG = C['date'], C['portion'], C['torah'], C['date_long']

# ------------------------------------------------------------ furniture
def header(c, title, sub):
    c.setFillColor(DEEP); c.rect(0, H - 78, W, 78, stroke=0, fill=1)
    c.setFillColor(GOLD); c.rect(0, H - 82, W, 4, stroke=0, fill=1)
    c.setFillColor(white); c.setFont('Sans', 7.5)
    c.drawString(36, H - 20, f"HOUSE OF ISRAEL · SHABBAT SCHOOL · {PORTION.upper()} · {TORAH.upper()}")
    c.drawRightString(W - 36, H - 20, f"Shabbat {DATE_LONG}")
    c.setFont('SerifB', 19); c.drawString(36, H - 46, title)
    c.setFillColor(HexColor('#f3e6c6')); c.setFont('Serif', 9.5); c.drawString(36, H - 63, sub)

def name_line(c, y=None):
    y = y or H - 112
    c.setFillColor(INK); c.setFont('Sans', 10); c.drawString(44, y, 'Name: ______________________________          Age: ______')

def footer(c):
    c.setFillColor(MUTE); c.setFont('Sans', 7.5); c.drawCentredString(W / 2, 22, 'Shabbat shalom · House of Israel'); c.showPage()

def wrap(text, font, size, width):
    out, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= width: cur = t
        else: out.append(cur); cur = w
    return out + ([cur] if cur else [])

def clean(w):
    return ''.join(ch for ch in unicodedata.normalize('NFD', w.upper()) if 'A' <= ch <= 'Z')

# ------------------------------------------------------------ line art
def P(c, pts, close=False, fill=0):
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]:
        p.curveTo(*q) if len(q) == 6 else p.lineTo(*q)
    if close: p.close()
    c.drawPath(p, stroke=1, fill=fill)

def person(c, x, y, s, arms='down', face=1, staff=False, beard=False):
    """Standing figure, feet at (x,y), height ~ s*2.2. arms: down | out | hug_r | hug_l"""
    u = s / 50.0
    hx, hy = x, y + 92 * u
    c.circle(hx, hy, 11 * u, stroke=1, fill=0)                             # head
    P(c, [(hx - 13 * u, hy - 2 * u), (hx - 14 * u, hy + 16 * u, hx + 14 * u, hy + 16 * u, hx + 13 * u, hy - 2 * u)])   # head cloth
    P(c, [(hx - 13 * u, hy - 2 * u), (hx - 15 * u, hy - 16 * u)]); P(c, [(hx + 13 * u, hy - 2 * u), (hx + 15 * u, hy - 16 * u)])
    c.circle(hx - 4 * u, hy + 1 * u, 1.2 * u, stroke=1, fill=1); c.circle(hx + 4 * u, hy + 1 * u, 1.2 * u, stroke=1, fill=1)
    P(c, [(hx - 4 * u, hy - 5 * u), (hx - 2 * u, hy - 8 * u, hx + 2 * u, hy - 8 * u, hx + 4 * u, hy - 5 * u)])
    if beard: P(c, [(hx - 9 * u, hy - 5 * u), (hx - 6 * u, hy - 18 * u, hx + 6 * u, hy - 18 * u, hx + 9 * u, hy - 5 * u)])
    P(c, [(x - 14 * u, y + 78 * u), (x - 22 * u, y + 4 * u), (x + 22 * u, y + 4 * u), (x + 14 * u, y + 78 * u)], close=True)   # robe
    P(c, [(x - 17 * u, y + 44 * u), (x + 17 * u, y + 44 * u)])           # belt
    for fx in (-9, 9): c.ellipse(x + (fx - 6) * u, y, x + (fx + 6) * u, y + 6 * u, stroke=1, fill=0)
    sh = y + 74 * u
    def arm(side, ex, ey):
        P(c, [(x + side * 13 * u, sh), (ex, ey)]); c.circle(ex, ey, 3.5 * u, stroke=1, fill=0)
    if arms == 'down': arm(-1, x - 26 * u, y + 40 * u); arm(1, x + 26 * u, y + 40 * u)
    elif arms == 'out': arm(-1, x - 36 * u, y + 66 * u); arm(1, x + 36 * u, y + 66 * u)
    elif arms == 'hug_r': arm(-1, x + 8 * u, y + 62 * u); arm(1, x + 40 * u, y + 70 * u)
    elif arms == 'hug_l': arm(-1, x - 40 * u, y + 70 * u); arm(1, x - 8 * u, y + 62 * u)
    if staff: P(c, [(x + 30 * u, y), (x + 30 * u, y + 110 * u), (x + 30 * u, y + 122 * u, x + 42 * u, y + 122 * u, x + 42 * u, y + 112 * u)])

def goat(c, x, y, s):
    u = s / 50.0
    c.ellipse(x, y + 22 * u, x + 50 * u, y + 46 * u, stroke=1, fill=0)
    for lx in (6, 14, 36, 44): P(c, [(x + lx * u, y + 26 * u), (x + lx * u, y)])
    P(c, [(x + 46 * u, y + 40 * u), (x + 54 * u, y + 56 * u)]); c.ellipse(x + 48 * u, y + 50 * u, x + 66 * u, y + 64 * u, stroke=1, fill=0)
    P(c, [(x + 54 * u, y + 63 * u), (x + 50 * u, y + 74 * u, x + 44 * u, y + 76 * u, x + 42 * u, y + 72 * u)])   # horn
    P(c, [(x + 60 * u, y + 52 * u), (x + 62 * u, y + 44 * u)])          # beard
    c.circle(x + 60 * u, y + 59 * u, 1 * u, stroke=1, fill=1); P(c, [(x, y + 40 * u), (x - 6 * u, y + 46 * u)])

def cow(c, x, y, s):
    u = s / 50.0
    c.roundRect(x, y + 22 * u, 58 * u, 28 * u, 10 * u, stroke=1, fill=0)
    for lx in (6, 16, 42, 52): P(c, [(x + lx * u, y + 24 * u), (x + lx * u, y)])
    c.roundRect(x + 56 * u, y + 34 * u, 20 * u, 22 * u, 7 * u, stroke=1, fill=0)
    P(c, [(x + 58 * u, y + 56 * u), (x + 54 * u, y + 62 * u)]); P(c, [(x + 74 * u, y + 56 * u), (x + 78 * u, y + 62 * u)])
    c.circle(x + 66 * u, y + 49 * u, 1 * u, stroke=1, fill=1)
    c.ellipse(x + 14 * u, y + 30 * u, x + 28 * u, y + 42 * u, stroke=1, fill=0)  # patch
    P(c, [(x, y + 46 * u), (x - 6 * u, y + 30 * u)])

def camel(c, x, y, s):
    u = s / 50.0
    P(c, [(x, y + 34 * u), (x + 4 * u, y + 50 * u, x + 14 * u, y + 52 * u, x + 20 * u, y + 46 * u),
          (x + 26 * u, y + 62 * u, x + 40 * u, y + 62 * u, x + 44 * u, y + 46 * u), (x + 50 * u, y + 40 * u, x + 58 * u, y + 44 * u, x + 60 * u, y + 56 * u),
          (x + 62 * u, y + 70 * u), (x + 74 * u, y + 72 * u), (x + 76 * u, y + 66 * u), (x + 66 * u, y + 62 * u), (x + 64 * u, y + 44 * u, x + 60 * u, y + 34 * u, x + 54 * u, y + 32 * u)])
    P(c, [(x, y + 34 * u), (x + 54 * u, y + 32 * u)])
    for lx in (6, 14, 42, 50): P(c, [(x + lx * u, y + 33 * u), (x + lx * u, y)])
    c.circle(x + 70 * u, y + 68 * u, 1 * u, stroke=1, fill=1)

def sun(c, x, y, r):
    c.circle(x, y, r, stroke=1, fill=0)
    import math
    for i in range(10):
        a = i * math.pi / 5; P(c, [(x + math.cos(a) * r * 1.4, y + math.sin(a) * r * 1.4), (x + math.cos(a) * r * 1.9, y + math.sin(a) * r * 1.9)])

def cloud(c, x, y, s):
    for dx, dy, r in ((0, 0, 12), (14, 6, 15), (30, 0, 12), (16, -6, 11)): c.circle(x + dx * s, y + dy * s, r * s, stroke=1, fill=0)

def hills(c, x0, y0, w):
    P(c, [(x0, y0 + 60), (x0 + w * .2, y0 + 120, x0 + w * .35, y0 + 120, x0 + w * .5, y0 + 70), (x0 + w * .7, y0 + 140, x0 + w * .85, y0 + 130, x0 + w, y0 + 80)])

def tent(c, x, y, s):
    P(c, [(x, y), (x + s * .5, y + s * .8), (x + s, y)], close=True); P(c, [(x + s * .5, y + s * .8), (x + s * .42, y), ]); P(c, [(x + s * .5, y + s * .8), (x + s * .58, y)])
    P(c, [(x + s * .5, y + s * .8), (x + s * .5, y + s * .98)]); P(c, [(x + s * .5, y + s * .98), (x + s * .62, y + s * .93), (x + s * .5, y + s * .88)], close=True)

def frame(c):
    c.setStrokeColor(INK); c.setLineWidth(2); c.roundRect(36, 70, W - 72, H - 210, 16, stroke=1, fill=0)

# ------------------------------------------------------------ 1. colouring 0-7
def colouring(path):
    c = canvas.Canvas(path, pagesize=A4); c.setLineJoin(1); c.setLineCap(1)
    for pg in C['colouring']:
        header(c, pg['title'], pg['sub']); name_line(c); frame(c)
        c.setStrokeColor(black); c.setLineWidth(3)
        ground = 200
        if pg['scene'] == 'embrace':
            hills(c, 40, ground, W - 80); sun(c, W - 130, H - 230, 26); cloud(c, 100, H - 230, 1.6); cloud(c, 260, H - 270, 1.2)
            P(c, [(40, ground), (W - 40, ground)])
            person(c, 232, ground, 92, arms='hug_r', beard=True)       # Ĕsaw
            person(c, 336, ground, 92, arms='hug_l', staff=False)       # Ya'aqoḇ
            tent(c, 440, ground, 90); goat(c, 58, ground, 34); goat(c, 110, ground, 30)
            c.setFillColor(INK); c.setFont('SerifB', 12)
            c.drawCentredString(225, ground - 22, 'Ĕsaw'); c.drawCentredString(345, ground - 22, 'Ya’aqoḇ')
        elif pg['scene'] == 'present':
            hills(c, 40, ground + 10, W - 80); sun(c, W - 120, H - 230, 24); cloud(c, 90, H - 240, 1.4)
            P(c, [(40, ground), (W - 40, ground)])
            camel(c, 60, ground, 70); cow(c, 210, ground, 46); goat(c, 330, ground, 40); goat(c, 385, ground, 30)
            person(c, 470, ground, 58, arms='down', staff=True)
            c.setFillColor(INK); c.setFont('SerifB', 11)
            for tx, t in ((115, 'camels'), (245, 'cows'), (360, 'goats'), (470, 'servant')): c.drawCentredString(tx, ground - 20, t)
        elif pg['scene'] == 'name':
            c.saveState(); c.setFillColor(white); c.setStrokeColor(black)
            for txt, sz, yy, font in ((PORTION.upper(), 54, H - 300, 'SerifB'), (C['hebrew'], 60, H - 400, 'SansB')):
                t = c.beginText(); t.setTextRenderMode(1); t.setFont(font, sz); c.setLineWidth(1.6)
                tw = pdfmetrics.stringWidth(txt, font, sz); t.setTextOrigin(W / 2 - tw / 2, yy); t.textOut(txt); t.setTextRenderMode(0); c.drawText(t)
            c.restoreState(); c.setFillColor(INK); c.setFont('SerifB', 22); c.drawCentredString(W / 2, H - 460, '“And he sent”')
            c.setLineWidth(3); c.setStrokeColor(black)
            person(c, 130, 180, 46, arms='out', beard=True); person(c, W - 130, 180, 46, arms='out')
            for k in range(3): person(c, 230 + k * 65, 180, 30, arms='down')
            c.setFont('SerifB', 11); c.drawCentredString(130, 160, 'Ya’aqoḇ'); c.drawCentredString(295, 160, 'messengers'); c.drawCentredString(W - 130, 160, 'Ĕsaw')
            P(c, [(190, 260), (W - 190, 260)]); P(c, [(W - 200, 266), (W - 190, 260), (W - 200, 254)])
        c.setFillColor(MUTE); c.setFont('Serif', 9.5)
        for i, ln in enumerate(wrap(pg['verse'], 'Serif', 9.5, W - 120)): c.drawCentredString(W / 2, 108 - i * 13, ln)
        footer(c)
    c.save()

# ------------------------------------------------------------ word search
def grid(words, size, dirs, seed):
    rnd = random.Random(seed)
    for attempt in range(200):
        g = [[''] * size for _ in range(size)]; placed = []
        for w in sorted(words, key=len, reverse=True):
            for _ in range(800):
                dr, dc = rnd.choice(dirs); r, cc = rnd.randrange(size), rnd.randrange(size)
                er, ec = r + dr * (len(w) - 1), cc + dc * (len(w) - 1)
                if not (0 <= er < size and 0 <= ec < size): continue
                if all(g[r + dr * i][cc + dc * i] in ('', w[i]) for i in range(len(w))):
                    for i in range(len(w)): g[r + dr * i][cc + dc * i] = w[i]
                    placed.append((w, r, cc, dr, dc)); break
        if len(placed) == len(words): break
    for r in range(size):
        for cc in range(size):
            if not g[r][cc]: g[r][cc] = rnd.choice('ABCDEFGHIKLMNOPRSTUWY')
    return g, placed

def wordsearch_page(c, title, sub, words, size, dirs, seed, key=False, g=None, placed=None):
    words = [clean(w) for w in words]
    if g is None: g, placed = grid(words, size, dirs, seed)
    header(c, title, sub)
    if not key: name_line(c)
    cell = min(34, (W - 120) / size); gx = (W - cell * size) / 2; gy = H - 140
    hit = {(r + dr * i, cc + dc * i) for (w, r, cc, dr, dc) in placed for i in range(len(w))}
    c.setStrokeColor(GREEN); c.setLineWidth(1.4); c.roundRect(gx - 8, gy - cell * size - 8, cell * size + 16, cell * size + 16, 10, stroke=1, fill=0)
    fs = 18 if size <= 8 else (15 if size <= 11 else 13)
    for r in range(size):
        for cc in range(size):
            cx, cy = gx + cc * cell + cell / 2, gy - r * cell - cell / 2
            if key and (r, cc) in hit:
                c.setFillColor(HexColor('#f3e6c6')); c.circle(cx, cy, cell * .42, stroke=0, fill=1)
            c.setFillColor(INK); c.setFont('SansB', fs); c.drawCentredString(cx, cy - fs * .35, g[r][cc])
    y = gy - cell * size - 36; c.setFont('SansB', 11); c.drawString(44, y, 'Find these words:'); y -= 20
    c.setFont('Sans', 12 if size <= 8 else 11); x = 44
    for w in [p[0] for p in placed]:
        tw = pdfmetrics.stringWidth('☐ ' + w, 'Sans', 12) + 22
        if x + tw > W - 44: x = 44; y -= 20
        c.drawString(x, y, '☐ ' + w); x += tw
    footer(c)
    return g, placed

def quiz_page(c, title, sub, qs, big=False, read_aloud=False):
    header(c, title, sub); name_line(c); y = H - 145
    qf, of = ('SerifB', 15 if big else 12), ('Serif', 14 if big else 11)
    for i, q in enumerate(qs, 1):
        c.setFillColor(GREEN); c.setFont('SansB', qf[1]); c.drawString(44, y, f"{i}.")
        c.setFillColor(INK); c.setFont(*qf)
        for ln in wrap(q['q'], qf[0], qf[1], W - 110): c.drawString(68, y, ln); y -= qf[1] + 4
        x = 74; c.setFont(*of)
        for j, o in enumerate(q['options']):
            c.circle(x, y + of[1] * .35, of[1] * .55 if big else 5, stroke=1, fill=0)
            if not big: c.setFont('SansB', 7); c.drawCentredString(x, y + 1.5, 'abc'[j]); c.setFont(*of)
            c.drawString(x + 12, y, o); x += pdfmetrics.stringWidth(o, *of) + (60 if big else 40)
        y -= of[1] + 2; c.setFillColor(MUTE); c.setFont('Sans', 7.5); c.drawString(68, y, q['ref']); c.setFillColor(INK)
        y -= 24 if big else 18
    footer(c)

def key_page(c, title, items, extra=None):
    header(c, 'Teacher’s answer key', title); y = H - 120
    c.setFillColor(INK)
    for line in items:
        for ln in wrap(line, 'Serif', 11, W - 100): c.setFont('Serif', 11); c.drawString(48, y, ln); y -= 16
        y -= 3
        if y < 70: footer(c); header(c, 'Teacher’s answer key (continued)', title); y = H - 120
    if extra:
        y -= 8; c.setFont('SerifB', 12); c.drawString(48, y, extra[0]); y -= 18
        for line in extra[1]:
            c.setFont('Serif', 11); c.drawString(48, y, line); y -= 16
    footer(c)

def qkey(qs): return [f"{i}. {q['options'][q['answer']]}  ({q['ref']})" for i, q in enumerate(qs, 1)]

def band_pack(path, band):
    B = C[band]; c = canvas.Canvas(path, pagesize=A4); c.setLineJoin(1); c.setLineCap(1)
    lbl, ages = B['label'], B['ages']
    dirs = {'easy': [(0, 1), (1, 0)], 'mid': [(0, 1), (1, 0), (1, 1)], 'hard': [(0, 1), (1, 0), (1, 1), (-1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1)]}[B['dirs']]
    note = {'easy': 'Words go across → and down ↓', 'mid': 'Words go across, down and diagonally', 'hard': 'Words go in every direction – even backwards!'}[B['dirs']]
    g, placed = wordsearch_page(c, f"Word search · {lbl}", f"Ages {ages} · {note}", B['words'], B['size'], dirs, int(DATE.replace('-', '')) + B['size'])
    quiz_page(c, f"{PORTION} quiz · {lbl}", f"Ages {ages} · " + ('Teacher reads aloud – colour the circle by the right answer' if B['dirs'] == 'easy' else 'Circle the right answer. Look up the verse to check!'), B['quiz'], big=B['dirs'] == 'easy')
    if 'match' in B:   # Who is it?
        header(c, f"Who is it? · {lbl}", 'Draw a line from each clue to the right person'); name_line(c)
        people = B['match_order']; y = H - 160
        for i, (clue, who, ref) in enumerate(B['match']):
            c.setFillColor(INK); c.setFont('Serif', 11)
            ls = wrap(f"{i + 1}. {clue}", 'Serif', 11, 300)
            for k, ln in enumerate(ls): c.drawString(48, y - k * 14, ln)
            c.setFillColor(MUTE); c.setFont('Sans', 7.5); c.drawString(60, y - len(ls) * 14, ref)
            c.setFillColor(INK); c.circle(360, y - 4, 3, stroke=1, fill=1)
            c.circle(400, y - 4, 3, stroke=1, fill=1); c.setFont('SerifB', 13); c.drawString(412, y - 8, people[i])
            y -= 62
        footer(c)
        extra = ('Who is it?', [f"{i + 1}. {who}" for i, (cl, who, r) in enumerate(B['match'])])
    elif 'fill' in B:
        header(c, f"Fill in & unscramble · {lbl}", 'Use your Bible to fill each gap, then unscramble the words'); name_line(c); y = H - 150
        c.setFillColor(INK); c.setFont('SerifB', 12); c.drawString(48, y, 'A. Fill in the missing word'); y -= 22
        for i, (sent, ans, ref) in enumerate(B['fill'], 1):
            for k, ln in enumerate(wrap(f"{i}. {sent}", 'Serif', 11, W - 110)): c.setFont('Serif', 11); c.drawString(56, y, ln); y -= 15
            c.setFillColor(MUTE); c.setFont('Sans', 7.5); c.drawString(70, y + 2, ref); c.setFillColor(INK); y -= 14
        y -= 10; c.setFont('SerifB', 12); c.drawString(48, y, 'B. Unscramble the names and places'); y -= 24
        rnd = random.Random(int(DATE.replace('-', '')))
        for i, (word, hint) in enumerate(B['unscramble'], 1):
            w = clean(word); s = list(w)
            while ''.join(s) == w: rnd.shuffle(s)
            c.setFont('SansB', 13); c.drawString(56, y, f"{i}.  {' '.join(s)}"); c.setFont('Serif', 10); c.drawString(250, y, hint)
            c.drawString(420, y, '____________'); y -= 24
        footer(c)
        extra = ('Fill in & unscramble', [f"A{i}. {a}" for i, (s, a, r) in enumerate(B['fill'], 1)] + [f"B{i}. {clean(w)}" for i, (w, h) in enumerate(B['unscramble'], 1)])
    else: extra = None
    key = qkey(B['quiz'])
    wordsearch_page(c, 'Teacher’s key · word search', f"{lbl} · ages {ages} · found words shaded", B['words'], B['size'], dirs, 0, key=True, g=g, placed=placed)
    key_page(c, f"{lbl} · ages {ages}", ['Quiz:'] + key, extra)
    c.save()

d = DATE
colouring(os.path.join(OUT, f'HOI-{d}-1-colouring-ages-0-7.pdf'))
band_pack(os.path.join(OUT, f'HOI-{d}-2-little-learners-ages-4-6.pdf'), 'little')
band_pack(os.path.join(OUT, f'HOI-{d}-3-juniors-ages-7-10.pdf'), 'juniors')
band_pack(os.path.join(OUT, f'HOI-{d}-4-seniors-ages-11-14.pdf'), 'seniors')
print('ok')
