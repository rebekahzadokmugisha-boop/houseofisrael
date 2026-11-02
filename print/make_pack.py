#!/usr/bin/env python3
"""House of Israel weekly printing pack.

Usage:  python3 make_pack.py quiz.json OUT_DIR
quiz.json holds: date (YYYY-MM-DD), portion, torah (reference), adult[], kids[], words[],
coloring (notes) and optionally scenes: [{"title": "...", "ref": "Gen 24:20", "motifs": ["well","camel",...]}].
Each question: {"q", "options"[], "answer" (index), "ref"}.

Makes three print-ready A4 PDFs:
  HOI-<date>-ages-0-7-colouring.pdf   two colouring pages + a colour-the-name page
  HOI-<date>-ages-8-14-puzzles.pdf    word search, questions with Scripture references, teacher's key
  HOI-<date>-adults-quiz.pdf          detail quiz with references, teacher's key
"""
import json, os, sys, random, math
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white, black

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, 'fonts')
pdfmetrics.registerFont(TTFont('Serif', os.path.join(F, 'DejaVuSerif.ttf')))
pdfmetrics.registerFont(TTFont('SerifB', os.path.join(F, 'DejaVuSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('Sans', os.path.join(F, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('SansB', os.path.join(F, 'DejaVuSans-Bold.ttf')))
GREEN, DEEP, GOLD, INK = HexColor('#1d5a46'), HexColor('#123d30'), HexColor('#b9862a'), HexColor('#16241e')
W, H = A4
LW = 3.2  # colouring line weight

# ---------------------------------------------------------------- motifs (line art, unit box 0..100)
def _p(c, pts, close=False):
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]:
        if len(q) == 6: p.curveTo(*q)
        else: p.lineTo(*q)
    if close: p.close()
    c.drawPath(p, stroke=1, fill=0)

def m_camel(c):
    _p(c, [(10, 40), (12, 55, 18, 62, 26, 60), (30, 70, 40, 74, 46, 64), (52, 74, 62, 72, 66, 60),
           (70, 62, 74, 70, 76, 80), (78, 88, 86, 90, 92, 86), (96, 84, 96, 80, 90, 80),
           (84, 80, 82, 70, 80, 58), (78, 48, 74, 42, 70, 40)], close=False)
    _p(c, [(10, 40), (70, 40)])
    for x in (16, 26, 58, 68):
        _p(c, [(x, 40), (x - 1, 8), (x + 4, 8), (x + 5, 40)])
    _p(c, [(10, 50), (4, 42, 4, 34, 6, 30)])           # tail
    c.circle(89, 85, 0.8, stroke=1, fill=0)             # eye
    _p(c, [(30, 64), (38, 62), (46, 64)])               # saddle blanket edge

def m_well(c):
    c.rect(20, 10, 60, 34, stroke=1, fill=0)
    for y in (21, 32):
        _p(c, [(20, y), (80, y)])
    for x, y in ((35, 10), (50, 21), (35, 32), (65, 10), (65, 32)):
        _p(c, [(x, y), (x, y + 11)])
    c.ellipse(16, 40, 84, 50, stroke=1, fill=0)
    _p(c, [(24, 45), (24, 82)]); _p(c, [(76, 45), (76, 82)]); _p(c, [(18, 82), (82, 82)])
    _p(c, [(50, 82), (50, 62)]); m_jar_at(c, 44, 50, 12)

def m_jar_at(c, x, y, s):
    c.saveState(); c.translate(x, y); c.scale(s / 20, s / 20)
    _p(c, [(6, 0), (0, 8, 0, 18, 6, 22), (8, 26), (12, 26), (14, 22), (20, 18, 20, 8, 14, 0)], close=True)
    _p(c, [(7, 26), (7, 29), (13, 29), (13, 26)])
    c.restoreState()

def m_jar(c): m_jar_at(c, 30, 10, 40)

def m_tent(c):
    _p(c, [(5, 10), (50, 85), (95, 10)], close=True)
    _p(c, [(38, 10), (50, 45), (62, 10)])
    _p(c, [(50, 85), (50, 95)]); _p(c, [(20, 10), (14, 2)]); _p(c, [(80, 10), (86, 2)])
    for y in (30, 50):
        _p(c, [(50 - (85 - y) * 45 / 75, y), (50 + (85 - y) * 45 / 75, y)])

def m_tree(c):
    _p(c, [(44, 5), (46, 40), (40, 52)]); _p(c, [(56, 5), (54, 40), (60, 52)])
    for cx, cy, r in ((50, 62, 22), (32, 56, 14), (68, 56, 14), (50, 80, 14), (38, 72, 12), (62, 72, 12)):
        c.circle(cx, cy, r, stroke=1, fill=0)

def m_palm(c):
    _p(c, [(48, 5), (46, 40, 50, 60, 52, 72)]); _p(c, [(56, 5), (54, 40, 56, 60, 56, 72)])
    for y in range(12, 70, 10):
        _p(c, [(47, y), (56, y + 2)])
    for a in (20, 55, 90, 125, 160):
        r = math.radians(a)
        _p(c, [(54, 72), (54 + 18 * math.cos(r), 72 + 14 * math.sin(r) + 10, 54 + 34 * math.cos(r), 72 + 6 * math.sin(r), 54 + 40 * math.cos(r), 66 + 4 * math.sin(r))])

def m_cave(c):
    _p(c, [(0, 10), (10, 50, 30, 80, 50, 82), (70, 84, 92, 52, 100, 10)])
    _p(c, [(32, 10), (34, 38, 46, 46, 54, 44), (64, 42, 68, 30, 68, 10)])
    for x, y in ((14, 40), (82, 46), (22, 62), (76, 66), (50, 68)):
        c.ellipse(x - 5, y - 3, x + 5, y + 3, stroke=1, fill=0)

def m_sheep(c):
    for cx, cy in ((30, 45), (42, 52), (55, 52), (66, 45), (55, 38), (42, 38)):
        c.circle(cx, cy, 10, stroke=1, fill=0)
    c.ellipse(70, 42, 88, 60, stroke=1, fill=0); c.circle(82, 54, 0.8, stroke=1, fill=0)
    for x in (34, 44, 56, 64):
        _p(c, [(x, 30), (x, 12)])

def m_person(c, robe=True):
    c.circle(50, 82, 9, stroke=1, fill=0)
    _p(c, [(41, 84), (40, 92, 60, 92, 59, 84)])           # head covering
    _p(c, [(36, 6), (40, 50, 42, 66, 44, 72), (56, 72), (58, 66, 60, 50, 64, 6)], close=True)
    _p(c, [(44, 66), (30, 48)]); _p(c, [(56, 66), (70, 48)])
    _p(c, [(40, 40), (60, 40)])

def m_woman_jar(c):
    m_person(c); m_jar_at(c, 60, 72, 14)

def m_sun(c):
    c.circle(50, 50, 16, stroke=1, fill=0)
    for a in range(0, 360, 30):
        r = math.radians(a); _p(c, [(50 + 22 * math.cos(r), 50 + 22 * math.sin(r)), (50 + 34 * math.cos(r), 50 + 34 * math.sin(r))])

def m_star_at(c, x, y, r):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    _p(c, pts, close=True)

def m_stars(c):
    for x, y, r in ((15, 70, 7), (40, 85, 9), (65, 72, 6), (88, 88, 8), (30, 45, 5), (78, 45, 6), (55, 55, 4)):
        m_star_at(c, x, y, r)

def m_menorah(c):
    _p(c, [(50, 10), (50, 80)]); _p(c, [(38, 4), (62, 4), (56, 10), (44, 10)], close=True)
    for d in (10, 20, 30):
        _p(c, [(50 - d, 80), (50 - d, 66), (50 - d, 50 + d * 0.2, 50 + d, 50 + d * 0.2, 50 + d, 66), (50 + d, 80)])
    for x in (20, 30, 40, 50, 60, 70, 80):
        _p(c, [(x, 84), (x - 3, 90, x, 96, x, 96), (x + 3, 90, x, 84, x, 84)])

def m_ring(c):
    c.circle(30, 50, 14, stroke=1, fill=0); c.circle(30, 50, 9, stroke=1, fill=0)
    c.ellipse(52, 30, 92, 70, stroke=1, fill=0); c.ellipse(58, 36, 86, 64, stroke=1, fill=0)

def m_hills(c):
    _p(c, [(0, 20), (20, 40, 40, 44, 55, 30), (70, 46, 90, 44, 100, 24)])
    for x in range(6, 100, 12):
        _p(c, [(x, 4), (x + 2, 12)]); _p(c, [(x + 4, 4), (x + 4, 13)])

def m_waves(c):
    for y in (20, 40, 60):
        _p(c, [(0, y), (12, y + 10, 25, y + 10, 25, y), (37, y - 10, 50, y - 10, 50, y), (62, y + 10, 75, y + 10, 75, y), (87, y - 10, 100, y - 10, 100, y)])

def m_ark(c):
    _p(c, [(5, 40), (20, 10), (80, 10), (95, 40)], close=True)
    c.rect(25, 40, 50, 25, stroke=1, fill=0); _p(c, [(20, 65), (50, 85), (80, 65)], close=True)
    c.rect(44, 46, 12, 12, stroke=1, fill=0)

def m_rainbow(c):
    for r in (40, 32, 24, 16):
        c.arc(50 - r, 10 - r, 50 + r, 10 + r, 0, 180)

def m_dove(c):
    _p(c, [(20, 50), (40, 40, 60, 40, 80, 52), (70, 56), (86, 64), (74, 64, 66, 60, 60, 56), (50, 80, 40, 84, 30, 82), (40, 70, 44, 60, 40, 54)], close=True)
    _p(c, [(80, 52), (90, 54)]); _p(c, [(88, 54), (96, 58), (92, 62)])

def m_ladder(c):
    _p(c, [(35, 0), (45, 100)]); _p(c, [(65, 0), (55, 100)])
    for i in range(1, 10):
        y = i * 10; _p(c, [(35 + y * 0.1, y), (65 - y * 0.1, y)])

def m_tablets(c):
    for x in (12, 52):
        _p(c, [(x, 10), (x, 70), (x + 1, 82, x + 35, 82, x + 36, 70), (x + 36, 10)], close=True)
        for y in (25, 40, 55):
            _p(c, [(x + 8, y), (x + 28, y)])

def m_altar(c):
    c.rect(20, 10, 60, 40, stroke=1, fill=0)
    for y in (23, 36):
        _p(c, [(20, y), (80, y)])
    _p(c, [(30, 50), (36, 74, 46, 62, 50, 86), (54, 62, 64, 74, 70, 50)])

def m_wheat(c):
    for x in (38, 50, 62):
        _p(c, [(x, 5), (x, 70)])
        for y in range(48, 90, 8):
            c.ellipse(x - 6, y, x, y + 8, stroke=1, fill=0); c.ellipse(x, y, x + 6, y + 8, stroke=1, fill=0)
    _p(c, [(32, 30), (68, 30)])

def m_mountain(c):
    _p(c, [(0, 5), (35, 80), (50, 60), (65, 90), (100, 5)], close=True)
    _p(c, [(28, 66), (35, 72), (42, 64)]); _p(c, [(58, 76), (65, 82), (72, 74)])

MOTIFS = {k[2:]: v for k, v in globals().items() if k.startswith('m_')}
KEYWORDS = {'camel': 'camel', 'well': 'well', 'fountain': 'well', 'jar': 'jar', 'tent': 'tent', 'tree': 'tree', 'palm': 'palm',
            'cave': 'cave', 'sheep': 'sheep', 'flock': 'sheep', 'lamb': 'sheep', 'ram': 'sheep', 'sun': 'sun', 'star': 'stars',
            'menorah': 'menorah', 'lampstand': 'menorah', 'ring': 'ring', 'bracelet': 'ring', 'field': 'hills', 'sea': 'waves',
            'water': 'waves', 'flood': 'waves', 'ark': 'ark', 'rainbow': 'rainbow', 'bow': 'rainbow', 'dove': 'dove', 'ladder': 'ladder',
            'tablet': 'tablets', 'commandment': 'tablets', 'altar': 'altar', 'offering': 'altar', 'wheat': 'wheat', 'grain': 'wheat',
            'harvest': 'wheat', 'mountain': 'mountain', 'sinai': 'mountain', 'woman': 'woman_jar', 'man': 'person', 'servant': 'person'}

LAYOUTS = [  # (x, y, size) slots on the drawing area, back-to-front
    [(0.08, 0.04, 0.84)],
    [(0.04, 0.10, 0.50), (0.50, 0.10, 0.46)],
    [(0.00, 0.30, 0.46), (0.30, 0.00, 0.50), (0.56, 0.32, 0.44)],
    [(0.00, 0.44, 0.42), (0.58, 0.44, 0.42), (0.00, 0.00, 0.50), (0.50, 0.00, 0.50)],
]

def draw_scene(c, motifs, x0, y0, w, h):
    motifs = [m for m in motifs if m in MOTIFS][:4] or ['menorah']
    c.saveState(); c.setLineWidth(LW / 1.0); c.setStrokeColor(black); c.setLineJoin(1); c.setLineCap(1)
    _p(c, [(x0, y0 + 4), (x0 + w * 0.3, y0 + 10, x0 + w * 0.7, y0 - 2, x0 + w, y0 + 6)])   # ground
    if 'sun' not in motifs and 'stars' not in motifs:                                   # sky
        c.saveState(); c.translate(x0 + w * 0.80, y0 + h * 0.86); c.scale(w * 0.0014, w * 0.0014); c.setLineWidth(LW / (w * 0.0014)); m_sun(c); c.restoreState()
        for fx, fy in ((0.12, 0.92), (0.30, 0.97), (0.50, 0.90)):
            _p(c, [(x0 + w * fx, y0 + h * fy), (x0 + w * fx + 18, y0 + h * fy + 8, x0 + w * fx + 36, y0 + h * fy + 8, x0 + w * fx + 54, y0 + h * fy)])
    for (fx, fy, fs), m in zip(LAYOUTS[len(motifs) - 1], motifs):
        s = fs * min(w, h)
        c.saveState(); c.translate(x0 + fx * w, y0 + fy * h); c.scale(s / 100, s / 100)
        c.setLineWidth(LW * 100 / s)
        MOTIFS[m](c); c.restoreState()
    c.restoreState()

# ---------------------------------------------------------------- page furniture
def header(c, title, sub, band=GREEN):
    c.setFillColor(band); c.rect(0, H - 70, W, 70, stroke=0, fill=1)
    c.setFillColor(GOLD); c.rect(0, H - 74, W, 4, stroke=0, fill=1)
    c.setFillColor(white); c.setFont('SerifB', 20); c.drawString(36, H - 38, 'House of Israel')
    c.setFont('Sans', 10); c.drawString(36, H - 56, sub)
    c.setFont('SerifB', 13); c.drawRightString(W - 36, H - 38, title)

def footer(c, txt):
    c.setFillColor(INK); c.setFont('Sans', 8.5); c.drawCentredString(W / 2, 22, txt)

def wrap(c, text, font, size, width):
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if pdfmetrics.stringWidth(t, font, size) <= width: cur = t
        else: lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines

def outline_text(c, text, x, y, size):
    c.saveState()
    t = c.beginText(); t.setTextRenderMode(1); t.setFont('SerifB', size); c.setLineWidth(1.6); c.setStrokeColor(black)
    tw = pdfmetrics.stringWidth(text, 'SerifB', size); t.setTextOrigin(x - tw / 2, y); t.textOut(text); t.setTextRenderMode(0); c.drawText(t)
    c.restoreState()

# ---------------------------------------------------------------- ages 0-7
def colouring(Q, path):
    c = canvas.Canvas(path, pagesize=A4); date = Q['date']; portion = Q['portion']
    scenes = Q.get('scenes') or auto_scenes(Q)
    for sc in scenes[:2]:
        header(c, portion, f"Colouring page · Ages 0–7 · Shabbat {date}")
        c.setFillColor(INK); c.setFont('SerifB', 17); c.drawCentredString(W / 2, H - 108, sc['title'])
        c.setStrokeColor(black); c.setLineWidth(2); c.roundRect(36, 92, W - 72, H - 220, 18, stroke=1, fill=0)
        draw_scene(c, sc['motifs'], 56, 112, W - 112, H - 262)
        c.setFont('Serif', 12); c.drawCentredString(W / 2, 70, f"Read it together: {sc['ref']} (YAH Scriptures)")
        c.setFont('Sans', 10); c.drawString(40, 46, 'My name: ________________________')
        footer(c, 'House of Israel · Shabbat school'); c.showPage()
    # colour-the-name page
    header(c, portion, f"Colour the name · Ages 0–7 · Shabbat {date}")
    size = 64 if len(portion) < 12 else 46
    outline_text(c, portion, W / 2, H / 2 + 120, size)
    c.setFont('Serif', 14); c.drawCentredString(W / 2, H / 2 + 70, f"This week’s Torah portion · {Q.get('torah', '')}")
    draw_scene(c, ['stars', 'menorah'], 120, 120, W - 240, H / 2 - 120)
    footer(c, 'House of Israel · Shabbat school'); c.showPage(); c.save()

def auto_scenes(Q):
    text = ' '.join([Q.get('coloring', '')] + [q['q'] + ' ' + ' '.join(q['options']) for q in Q.get('kids', [])]).lower()
    found = []
    for k, m in KEYWORDS.items():
        if k in text and m not in found: found.append(m)
    found = found or ['menorah', 'stars']
    notes = [s.strip() for s in Q.get('coloring', '').replace('Page 1:', '|').replace('Page 2:', '|').split('|') if s.strip()]
    refs = [q.get('ref', '') for q in Q.get('kids', []) if q.get('ref')] or [Q.get('torah', '')]
    return [{'title': (notes[0] if notes else Q['portion']).rstrip('.'), 'ref': refs[0], 'motifs': found[:3]},
            {'title': (notes[1] if len(notes) > 1 else Q['portion']).rstrip('.'), 'ref': refs[-1], 'motifs': found[3:6] or found[:2]}]

# ---------------------------------------------------------------- word search
def make_grid(words, size=13, seed=7):
    rnd = random.Random(seed); g = [['' for _ in range(size)] for _ in range(size)]; placed = []
    dirs = [(0, 1), (1, 0), (1, 1), (-1, 1)]
    for w in sorted(words, key=len, reverse=True):
        for _ in range(500):
            dr, dc = rnd.choice(dirs); r = rnd.randrange(size); cc = rnd.randrange(size)
            er, ec = r + dr * (len(w) - 1), cc + dc * (len(w) - 1)
            if not (0 <= er < size and 0 <= ec < size): continue
            if all(g[r + dr * i][cc + dc * i] in ('', w[i]) for i in range(len(w))):
                for i in range(len(w)): g[r + dr * i][cc + dc * i] = w[i]
                placed.append((w, r, cc, dr, dc)); break
    for r in range(size):
        for cc in range(size):
            if not g[r][cc]: g[r][cc] = rnd.choice('ABCDEFGHIJKLMNOPRSTUWY')
    return g, placed

def clean(w):
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFD', w.upper()) if 'A' <= ch <= 'Z')

def questions_pages(c, qs, title, sub, band, start_y=None, letters=True):
    y = start_y or H - 110
    for i, q in enumerate(qs, 1):
        lines = wrap(c, f"{i}. {q['q']}", 'SerifB', 12, W - 90)
        need = 18 * len(lines) + 18 * len(q['options']) + 30
        if y - need < 50:
            footer(c, 'House of Israel · answers are in the YAH Scriptures'); c.showPage(); header(c, title, sub, band); y = H - 110
        c.setFillColor(INK); c.setFont('SerifB', 12)
        for ln in lines: c.drawString(44, y, ln); y -= 17
        c.setFont('Serif', 11.5)
        for j, o in enumerate(q['options']):
            c.circle(60, y + 4, 4.5, stroke=1, fill=0); c.drawString(72, y, f"{'ABCD'[j]}.  {o}"); y -= 17
        c.setFillColor(GREEN); c.setFont('Sans', 9.5); c.drawString(72, y, f"Look it up: {q.get('ref', '')}"); c.setFillColor(INK); y -= 22
    return y

def key_page(c, qs, title, sub, band, words=None):
    header(c, title, sub + ' · TEACHER’S KEY', band)
    c.setFont('SerifB', 15); c.setFillColor(INK); c.drawString(44, H - 110, 'Answers (for the teacher)'); y = H - 136
    for i, q in enumerate(qs, 1):
        line = f"{i}. {'ABCD'[q['answer']]} – {q['options'][q['answer']]}   ({q.get('ref', '')})"
        for ln in wrap(c, line, 'Serif', 11, W - 90):
            c.setFont('Serif', 11); c.drawString(44, y, ln); y -= 16
        if y < 60: c.showPage(); header(c, title, sub + ' · TEACHER’S KEY', band); y = H - 110
    footer(c, 'House of Israel · Shabbat school'); c.showPage()

def puzzles(Q, path):
    c = canvas.Canvas(path, pagesize=A4); date, portion = Q['date'], Q['portion']
    sub = f"Ages 8–14 · Shabbat {date} · {Q.get('torah', '')}"
    words = [clean(w) for w in Q.get('words', []) if 3 <= len(clean(w)) <= 13]
    g, placed = make_grid(words, 13, int(date.replace('-', '')))
    header(c, portion, sub, DEEP)
    c.setFillColor(INK); c.setFont('SerifB', 17); c.drawString(44, H - 108, 'Word search')
    c.setFont('Serif', 10.5); c.drawString(44, H - 126, 'Find every word from this week’s portion. Words go across, down and diagonally.')
    cell = 30; gx = (W - cell * 13) / 2; gy = H - 150
    c.setStrokeColor(GREEN); c.setLineWidth(1.4); c.roundRect(gx - 8, gy - cell * 13 - 8, cell * 13 + 16, cell * 13 + 16, 10, stroke=1, fill=0)
    c.setFont('SansB', 15)
    for r in range(13):
        for cc in range(13):
            c.drawCentredString(gx + cc * cell + cell / 2, gy - r * cell - cell / 2 - 5, g[r][cc])
    y = gy - cell * 13 - 34; c.setFont('SansB', 11); c.drawString(44, y, 'Words to find:'); y -= 18
    c.setFont('Sans', 11); x = 44
    for w, *_ in sorted(placed):
        tw = pdfmetrics.stringWidth('☐ ' + w, 'Sans', 11) + 18
        if x + tw > W - 44: x = 44; y -= 18
        c.drawString(x, y, '☐ ' + w); x += tw
    footer(c, 'House of Israel · Shabbat school'); c.showPage()
    header(c, portion, sub, DEEP); c.setFont('SerifB', 17); c.setFillColor(INK); c.drawString(44, H - 108, 'What does the Scripture say?')
    c.setFont('Serif', 10.5); c.drawString(44, H - 126, 'Circle the right answer. Not sure? Look up the verse given under each question.')
    questions_pages(c, Q.get('kids', []), portion, sub, DEEP, start_y=H - 152)
    c.setFont('Sans', 10); c.drawString(44, 46, 'Name: ________________________   Score: ____ / ' + str(len(Q.get('kids', []))))
    footer(c, 'House of Israel · Shabbat school'); c.showPage()
    # key with word positions
    key_page(c, Q.get('kids', []), portion, sub, DEEP)
    c.save()

def adults(Q, path):
    c = canvas.Canvas(path, pagesize=A4); date, portion = Q['date'], Q['portion']
    sub = f"Adults · Shabbat {date} · {Q.get('torah', '')}"
    header(c, portion, sub, GREEN)
    c.setFont('SerifB', 18); c.setFillColor(INK); c.drawString(44, H - 108, f'{portion}: the details')
    c.setFont('Serif', 10.5); c.drawString(44, H - 126, 'Every answer is written in this week’s portion. The verse under each question is your guide.')
    questions_pages(c, Q.get('adult', []), portion, sub, GREEN, start_y=H - 152)
    c.setFont('Sans', 10); c.drawString(44, 46, 'Name: ________________________   Score: ____ / ' + str(len(Q.get('adult', []))))
    footer(c, 'House of Israel'); c.showPage()
    key_page(c, Q.get('adult', []), portion, sub, GREEN); c.save()

def main():
    Q = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    d = Q['date']; files = []
    for name, fn in ((f'HOI-{d}-ages-0-7-colouring.pdf', colouring), (f'HOI-{d}-ages-8-14-puzzles.pdf', puzzles), (f'HOI-{d}-adults-quiz.pdf', adults)):
        p = os.path.join(out, name); fn(Q, p); files.append(p)
    print('\n'.join(files))

if __name__ == '__main__':
    main()
