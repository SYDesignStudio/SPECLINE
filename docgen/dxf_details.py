#!/usr/bin/env python3
"""Construction details as DXF, converted from the drawn sheets in
reference/details/extension-junctions.html.

    python docgen/dxf_details.py                every detail on the sheet
    python docgen/dxf_details.py D-201 D-203    only the ones named
    python docgen/dxf_details.py --paper a4     A4 landscape instead of A3
    python docgen/dxf_details.py --png          also render a PNG of each, to look at
    python docgen/dxf_details.py --check        run the checks and write nothing

Writes output/dxf/details/D-2xx.dxf, one file per detail.

WHERE THE GEOMETRY COMES FROM, and why not from the schedule.

  The six SVG sheets already have the junctions worked out — in real millimetres, with
  the wall at the same coordinates on every sheet, the coursing set out from the damp
  proof course, and every decision about where the insulation laps the membrane already
  taken. That is the expensive part of a detail and it is done. This script converts it.
  build-up-schedule.json says what each build-up is MADE OF; it does not know where any
  of it goes, and a stack of rectangles is not a junction.

  So: geometry from the sheets, materials and thicknesses from the schedule, and where
  the two disagree the script says so rather than picking one (see CHECKS below).

HOW IT IS SET OUT.

  Model space is 1:1 in millimetres, exactly as drawn. The geometry is never scaled —
  that is what lets the sheet measure true and lets anyone dimension off it in CAD and
  get the real number. SVG y increases downwards and DXF y increases upwards, so the
  only transform applied anywhere is y -> -y.

  One DXF layer per material, named S-MAT-<hatch> for the hatch names the schedule
  uses, plus S-CUT (cut through structure), S-THIN, S-DIM, S-TEXT, S-LEAD, S-REF and
  S-KEY. Lineweight and colour are set on the layer and every entity is BYLAYER, so the
  whole drawing can be re-penned by editing layers and nothing has to be selected.

  Paper space is an A3 landscape layout with one viewport at a true 1:10. The layout
  itself plots 1:1 — paper is paper — and the 1:10 lives on the viewport, which is
  locked so it cannot be scrolled off scale. Plotting model space direct at 1:10 gives
  the same sheet if you prefer to work that way; the title block says so.

  Brick and block are drawn with their real bed joints — 75mm and 225mm centres, phased
  so a joint lands on the DPC, as they are set out on site — not with a bond pattern.
  AR-B816 is a running-bond elevation pattern with perpends in it, and a perpend on a
  section is a lie about where the cut is. Everything else takes a standard ACAD
  pattern from the table dxf_buildups.py already uses, so the two scripts agree.

CHECKS (printed every run; nothing is silently corrected).

  1. Every dimension on the sheet is rebuilt as a real DXF DIMENSION measuring the
     geometry, and the written value is compared with what the geometry measures. A
     mismatch means the sheet says one thing and draws another, and is reported.
  2. Each material drawn on a sheet is compared with the layer thicknesses of the
     build-ups the sheet references (EW1, GF1, RF1 -> BUILDUPS below). A material drawn
     at a thickness the clause does not give is reported. The clause wins: fix the
     drawing, or fix the clause, but do not issue them disagreeing.

Nothing here touches the network.
"""
import json, math, os, re, sys
import xml.etree.ElementTree as ET

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    from ezdxf.math import ConstructionArc
except ImportError:
    sys.exit("ezdxf is not installed.  python -m pip install ezdxf matplotlib")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
try:
    from dxf_buildups import MAT           # one material table for both scripts
except ImportError:
    sys.exit("docgen/dxf_buildups.py is missing — it holds the material table.")

SVG_SRC = os.path.join(ROOT, "reference", "details", "extension-junctions.html")
JSON_SRC = os.path.join(ROOT, "reference", "details", "build-up-schedule.json")
OUT = os.path.join(ROOT, "output", "dxf", "details")

SCALE = 10.0                       # the viewport scale, and the scale on the title block
PAPER = {"a3": (420.0, 297.0), "a4": (297.0, 210.0)}
MARGIN = 9.0
TITLE_H = 26.0                     # title block strip across the foot of the sheet

# The sheets' own ink. Colour carries meaning on them, so it carries layer here.
INK, GREY, GOLD, RED, PETROL = "#10191F", "#5C6871", "#C9A94E", "#B3352B", "#0E6E85"
CUT_MIN = 2.0                      # stroke width at or above which a line is a cut line

# Bed joints, and where the coursing is phased from, straight off the SVG patterns:
# brick 50 + 75k and block 125 + 225k both land a joint on the DPC at 350.
COURSE = {"brick": (75.0, 50.0), "block": (225.0, 125.0), "dense": (225.0, 125.0)}
JOINT = 10.0                       # bed joint thickness, drawn as two lines

# Which build-up each reference on the sheets stands for, so the schedule can be printed
# against the drawing and checked against it. Keys are the petrol references on the sheet.
BUILDUPS = {
    "EW1": ("extension", "Full Fill Cavity Wall"),
    "GF1": ("extension", "Solid Floor — Insulation Over Slab (Screed Finish)"),
    "RF1": ("extension", "Warm Deck Flat Roof"),
    "RF2": ("extension", "Pitched Roof — Insulation at Rafter Level"),
    "RF3": ("extension", "Pitched Roof — Insulation at Rafter Level"),
    "IF1": ("extension", "Intermediate Floor — Solid Timber Joists"),
    "FD1": ("extension", "Trench Fill Foundation"),
}

LAYERS = [
    # name,      aci, lineweight (1/100 mm)
    ("S-CUT",    7,   35),
    ("S-THIN",   8,   18),
    ("S-DIM",    4,   13),
    ("S-TEXT",   7,   13),
    ("S-LEAD",   8,   13),
    ("S-REF",  134,   18),
    ("S-KEY",    8,   13),
    ("S-TITLE",  7,   25),
    ("S-FRAME",  8,   25),
]

# ---------------------------------------------------------------- SVG reading

SHEET = re.compile(
    r'<span class="sheet-ref">([^<]+)</span>\s*<h2>(.*?)</h2>\s*'
    r'<span class="sc">([^<]*)</span>(.*?)</section>', re.S)
DRAWING = re.compile(r'(<svg viewBox="[^"]*"[^>]*--pw.*?</svg>)', re.S)
NUM = re.compile(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')
CMD = re.compile(r'[MmLlHhVvCcSsQqTtAaZz]')
INHERIT = ("fill", "stroke", "stroke-width", "stroke-dasharray", "font-family",
           "font-size", "text-anchor", "marker-start", "marker-end")


def nums(s):
    return [float(x) for x in NUM.findall(s or "")]


def read_sheets(path, wanted=None):
    """Pull each detail off the HTML page: its reference, title, viewBox and its SVG."""
    html = open(path, encoding="utf-8").read()
    out = []
    for ref, title, sub, body in SHEET.findall(html):
        ref = ref.strip()
        if wanted and ref not in wanted:
            continue
        m = DRAWING.search(body)
        if not m:
            continue
        svg = ET.fromstring(m.group(1))
        out.append({
            "ref": ref,
            "title": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title)).strip(),
            "sub": sub.strip(),
            "view": nums(svg.get("viewBox")),
            "svg": svg,
        })
    return out


def flatten(elem, style=None, out=None):
    """Walk the SVG, carrying the style down, and return the drawable elements."""
    out = [] if out is None else out
    style = dict(style or {})
    for k in INHERIT:
        v = elem.get(k)
        if v is not None:
            style[k] = v
    tag = elem.tag.split("}")[-1]
    if tag in ("svg", "g"):
        for child in elem:
            flatten(child, style, out)
    elif tag in ("rect", "path", "text", "circle"):
        out.append((tag, elem, style))
    return out


# ---------------------------------------------------------------- path parsing

def parse_path(d):
    """SVG path -> list of subpaths, each a list of segments in SVG coordinates.

    A segment is ("l", p0, p1) for a straight run or ("a", p0, pmid, p1) for a circular
    arc; curves are flattened into short straight runs. Points stay in SVG space and are
    flipped once, on the way into the drawing.
    """
    toks, i = [], 0
    while i < len(d):
        c = d[i]
        if CMD.match(c):
            toks.append(c)
            i += 1
        elif c in " ,\t\r\n":
            i += 1
        else:
            m = NUM.match(d, i)
            if not m:
                i += 1
                continue
            toks.append(float(m.group()))
            i = m.end()

    subs, seg, cur, start, prev_c2, prev_q, cmd = [], [], (0.0, 0.0), (0.0, 0.0), None, None, None
    k = 0

    def push():
        if seg:
            subs.append(list(seg))
        seg.clear()

    def take(n):
        nonlocal k
        vals = toks[k:k + n]
        k += n
        return vals

    while k < len(toks):
        t = toks[k]
        if isinstance(t, str):
            cmd = t
            k += 1
            if cmd in "Mm":
                x, y = take(2)
                if cmd == "m":
                    x, y = cur[0] + x, cur[1] + y
                push()
                cur = start = (x, y)
                cmd = "L" if cmd == "M" else "l"     # further pairs are implicit lines
                continue
            if cmd in "Zz":
                if cur != start:
                    seg.append(("l", cur, start))
                cur = start
                push()
                continue
        if cmd is None:
            k += 1
            continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "L":
            x, y = take(2)
        elif c == "H":
            x, y = take(1)[0], (0.0 if rel else cur[1])
        elif c == "V":
            x, y = (0.0 if rel else cur[0]), take(1)[0]
        elif c in "CSQTA":
            pass
        else:
            k += 1
            continue

        if c in "LHV":
            if rel:
                x, y = cur[0] + x, cur[1] + y
            seg.append(("l", cur, (x, y)))
            cur = (x, y)
            prev_c2 = prev_q = None
            continue

        if c == "C":
            x1, y1, x2, y2, x, y = take(6)
        elif c == "S":
            x2, y2, x, y = take(4)
            x1, y1 = (0.0, 0.0) if rel else cur
            if prev_c2:
                r = (2 * cur[0] - prev_c2[0], 2 * cur[1] - prev_c2[1])
                x1, y1 = (r[0] - cur[0], r[1] - cur[1]) if rel else r
        elif c == "Q":
            qx, qy, x, y = take(4)
        elif c == "T":
            x, y = take(2)
            if prev_q:
                r = (2 * cur[0] - prev_q[0], 2 * cur[1] - prev_q[1])
                qx, qy = (r[0] - cur[0], r[1] - cur[1]) if rel else r
            else:
                qx, qy = (0.0, 0.0) if rel else cur
        elif c == "A":
            rx, ry, rot, laf, sf, x, y = take(7)

        if rel:
            ax, ay = cur[0] + x, cur[1] + y
        else:
            ax, ay = x, y

        if c in "CS":
            p1 = (cur[0] + x1, cur[1] + y1) if rel else (x1, y1)
            p2 = (cur[0] + x2, cur[1] + y2) if rel else (x2, y2)
            seg += bezier(cur, p1, p2, (ax, ay))
            prev_c2, prev_q = p2, None
        elif c in "QT":
            q = (cur[0] + qx, cur[1] + qy) if rel else (qx, qy)
            p1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
            p2 = (ax + 2 / 3 * (q[0] - ax), ay + 2 / 3 * (q[1] - ay))
            seg += bezier(cur, p1, p2, (ax, ay))
            prev_q, prev_c2 = q, None
        elif c == "A":
            seg += arc(cur, rx, ry, rot, laf, sf, (ax, ay))
            prev_c2 = prev_q = None
        cur = (ax, ay)

    push()
    return subs


def bezier(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return [("l", pts[i], pts[i + 1]) for i in range(n)]


def arc(p0, rx, ry, rot, laf, sf, p1):
    """SVG elliptical arc. Circular ones are kept as arcs; anything else is flattened."""
    if rx == 0 or ry == 0 or p0 == p1:
        return [("l", p0, p1)]
    # endpoint -> centre parameterisation (F.6.5 of the SVG spec), rotation ignored for
    # circles because it has no effect on them.
    phi = math.radians(rot)
    dx2, dy2 = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1 = math.cos(phi) * dx2 + math.sin(phi) * dy2
    y1 = -math.sin(phi) * dx2 + math.cos(phi) * dy2
    rx, ry = abs(rx), abs(ry)
    lam = x1 * x1 / (rx * rx) + y1 * y1 / (ry * ry)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    co = math.sqrt(max(num / den, 0.0)) * (-1 if laf == sf else 1)
    cx1, cy1 = co * rx * y1 / ry, -co * ry * x1 / rx
    cx = math.cos(phi) * cx1 - math.sin(phi) * cy1 + (p0[0] + p1[0]) / 2
    cy = math.sin(phi) * cx1 + math.cos(phi) * cy1 + (p0[1] + p1[1]) / 2

    def ang(px, py):
        return math.atan2((py - cy1) / ry, (px - cx1) / rx)

    a0, a1 = ang(x1, y1), ang(-x1, -y1)
    sweep = a1 - a0
    if sf == 0 and sweep > 0:
        sweep -= 2 * math.pi
    elif sf == 1 and sweep < 0:
        sweep += 2 * math.pi
    mid = a0 + sweep / 2
    pm = (cx + rx * math.cos(mid) * math.cos(phi) - ry * math.sin(mid) * math.sin(phi),
          cy + rx * math.cos(mid) * math.sin(phi) + ry * math.sin(mid) * math.cos(phi))
    if abs(rx - ry) < 1e-6:
        return [("a", p0, pm, p1)]
    return [("l", p0, pm), ("l", pm, p1)]


# ---------------------------------------------------------------- drawing

def flip(p):
    return (p[0], -p[1])


def material(style):
    """The hatch name behind fill="url(#ins)", or None."""
    m = re.match(r"url\(#([a-z]+)\)", (style.get("fill") or "").strip())
    return m.group(1) if m and m.group(1) in MAT else None


def line_layer(style):
    """Which layer a stroked line belongs on: colour first, then weight."""
    stroke = (style.get("stroke") or "").upper()
    width = float(style.get("stroke-width") or 1.0)
    if stroke == RED.upper():
        return "S-MAT-MEMBRANE"
    if stroke == GOLD.upper():
        return "S-MAT-INS"
    if "tick" in (style.get("marker-start", "") + style.get("marker-end", "")):
        return "S-DIM"
    if "dot" in style.get("marker-start", ""):
        return "S-LEAD"
    return "S-CUT" if width >= CUT_MIN else "S-THIN"


def fill_material(msp, pts, mat):
    """Hatch or course a closed shape, on its own material layer."""
    lay = "S-MAT-" + mat.upper()
    colour, pattern, pscale, _pitch = MAT[mat]
    if pattern:
        h = msp.add_hatch(color=colour, dxfattribs={"layer": lay})
        h.set_pattern_fill(pattern, scale=pscale)
        h.paths.add_polyline_path(pts, is_closed=True)
    elif mat == "membrane":
        h = msp.add_hatch(color=colour, dxfattribs={"layer": lay})
        h.set_solid_fill(color=colour)
        h.paths.add_polyline_path(pts, is_closed=True)
    if mat in COURSE:
        course(msp, pts, mat, lay)


def course(msp, pts, mat, lay):
    """Real bed joints at real centres, phased so one lands on the damp proof course."""
    pitch, phase = COURSE[mat]
    xs = [p[0] for p in pts]
    ys = [-p[1] for p in pts]                       # back into SVG y to use the phase
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    k = math.ceil((y0 - phase) / pitch)
    y = phase + k * pitch
    while y < y1:
        for yy in (y, y + JOINT):
            if y0 < yy < y1:
                msp.add_line((x0, -yy), (x1, -yy), dxfattribs={"layer": lay})
        y += pitch


def stroke_path(msp, segs, layer, dash=None):
    """Draw a run of segments: arcs as arcs, everything else as a polyline."""
    attribs = {"layer": layer}
    if dash:
        attribs["linetype"] = dash
    run = []
    for kind, a, b_or_m, *rest in [(s[0], s[1], s[2], *s[3:]) for s in segs]:
        if kind == "l":
            if not run:
                run = [flip(a)]
            run.append(flip(b_or_m))
        else:
            if run:
                msp.add_lwpolyline(run, dxfattribs=attribs)
                run = []
            p0, pm, p1 = flip(a), flip(b_or_m), flip(rest[0])
            try:
                ConstructionArc.from_3p(p0, p1, pm).add_to_layout(msp, dxfattribs=attribs)
            except Exception:
                msp.add_lwpolyline([p0, pm, p1], dxfattribs=attribs)
    if run:
        msp.add_lwpolyline(run, dxfattribs=attribs)


def dash_name(style):
    d = style.get("stroke-dasharray")
    if not d:
        return None
    a, b = (nums(d) + [0, 0])[:2]
    return "SY-DASH%g" % a


# ---------------------------------------------------------------- the sheet

def build(sheet, schedule, paper):
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4          # millimetres
    doc.header["$MEASUREMENT"] = 1       # metric
    doc.header["$LTSCALE"] = 1.0         # linetype patterns are already in millimetres
    doc.header["$PSLTSCALE"] = 0
    for name, colour, lw in LAYERS:
        doc.layers.add(name, color=colour, lineweight=lw)
    for mat, (colour, _p, _s, _c) in MAT.items():
        doc.layers.add("S-MAT-" + mat.upper(), color=colour, lineweight=18)
    vp_layer = doc.layers.add("S-VPORT", color=8)
    vp_layer.dxf.plot = 0
    for total, on in ((32.0, 20.0), (34.0, 22.0)):
        doc.linetypes.add("SY-DASH%g" % on, pattern=[total, on, -(total - on)],
                          description="Dashed %g-%g" % (on, total - on))
    ds = doc.dimstyles.duplicate_entry("Standard", "SY-1-10")
    ds.dxf.dimtxt = 24.0                 # 2.4mm on paper at 1:10, as drawn
    ds.dxf.dimtsz = 8.0                  # oblique ticks, not arrows
    ds.dxf.dimexe = 10.0
    ds.dxf.dimexo = 6.0
    ds.dxf.dimgap = 8.0
    ds.dxf.dimdec = 0
    ds.dxf.dimlunit = 2
    ds.dxf.dimclrd = 256                 # dimension line, extension lines and text
    ds.dxf.dimclre = 256                 # all BYLAYER, so S-DIM decides
    ds.dxf.dimclrt = 256

    msp = doc.modelspace()
    items = flatten(sheet["svg"])
    used, dims, dimtexts, notes = set(), [], [], []

    for tag, el, st in items:
        if tag == "rect":
            x, y = float(el.get("x", 0)), float(el.get("y", 0))
            w, h = float(el.get("width", 0)), float(el.get("height", 0))
            pts = [flip(p) for p in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]
            mat = material(st)
            if mat:
                used.add(mat)
                fill_material(msp, pts, mat)
                notes.append((mat, min(w, h)))
            if (st.get("stroke") or "none") != "none":
                msp.add_lwpolyline(pts, close=True,
                                   dxfattribs={"layer": line_layer(st)})

        elif tag == "path":
            subs = parse_path(el.get("d", ""))
            mat = material(st)
            layer = line_layer(st)
            dash = dash_name(st)
            if mat:
                used.add(mat)
                for sub in subs:
                    pts = [flip(sub[0][1])] + [flip(s[2] if s[0] == "l" else s[3]) for s in sub]
                    fill_material(msp, pts, mat)
                    q = list(pts)
                    if len(q) > 1 and math.hypot(q[-1][0] - q[0][0],
                                                 q[-1][1] - q[0][1]) < 0.01:
                        q.pop()
                    if len(q) == 4:          # a band: its thickness is its short edge
                        notes.append((mat, min(
                            math.hypot(q[(i + 1) % 4][0] - q[i][0],
                                       q[(i + 1) % 4][1] - q[i][1]) for i in range(4))))
            ticked = ("tick" in st.get("marker-start", "")
                      and "tick" in st.get("marker-end", ""))
            if layer == "S-DIM" and ticked and len(subs) == 1:
                pts = [subs[0][0][1], subs[0][-1][2] if subs[0][-1][0] == "l" else subs[0][-1][3]]
                dims.append((flip(pts[0]), flip(pts[1])))
                continue
            if (st.get("stroke") or "none") != "none":
                for sub in subs:
                    stroke_path(msp, sub, layer, dash)

        elif tag == "circle":
            c = flip((float(el.get("cx", 0)), float(el.get("cy", 0))))
            msp.add_circle(c, float(el.get("r", 1)),
                           dxfattribs={"layer": line_layer(st)})

        elif tag == "text":
            txt = (el.text or "").strip()
            if not txt:
                continue
            p = flip((float(el.get("x", 0)), float(el.get("y", 0))))
            height = float(st.get("font-size") or 24)
            anchor = st.get("text-anchor", "start")
            mono = "Mono" in (st.get("font-family") or "")
            petrol = (st.get("fill") or "").upper() == PETROL.upper()
            if mono and not petrol:
                dimtexts.append((p, txt, height, anchor))     # a dimension value
                continue
            layer = "S-REF" if petrol else "S-TEXT"
            place(msp, txt, p, height, anchor, layer)

    problems = dimension(msp, dims, dimtexts)
    refs = set()
    for tag, el, st in items:
        if tag == "text" and (st.get("fill") or "").upper() == PETROL.upper():
            t = (el.text or "").strip()
            if t in BUILDUPS:
                refs.add(t)
    refs = sorted(refs)
    problems += check_schedule(sheet, refs, notes, schedule)
    if sheet["sub"].lower().startswith("horizontal") and any(
            m in COURSE for m, _t in notes):
        problems.append("horizontal section, but the masonry carries bed joints — a "
                        "plan cut through stretcher bond shows perpends, not beds "
                        "(fix the hatch on the SVG sheet, not here)")
    layout(doc, sheet, sorted(used), refs, schedule, paper)
    return doc, problems


def place(msp, txt, p, height, anchor, layer):
    align = {"middle": TextEntityAlignment.CENTER,
             "end": TextEntityAlignment.RIGHT}.get(anchor, TextEntityAlignment.LEFT)
    t = msp.add_text(txt, height=height, dxfattribs={"layer": layer})
    if align is TextEntityAlignment.LEFT:
        t.set_placement(p)
    else:
        t.set_placement(p, align=align)
    return t


def dimension(msp, dims, texts):
    """Rebuild each drawn dimension as a real DIMENSION, and check what it says.

    The dimension measures the geometry, so if the number written on the sheet and the
    number the line spans disagree, the sheet is wrong somewhere and says so here.
    """
    problems, free = [], list(texts)
    for p1, p2 in dims:
        mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        best, bi = None, None
        for i, (tp, txt, _h, _a) in enumerate(free):
            d = math.hypot(tp[0] - mid[0], tp[1] - mid[1])
            if d < 160 and (best is None or d < best):
                best, bi = d, i
        label = free.pop(bi)[1] if bi is not None else None
        measured = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        angle = 0.0 if abs(p2[1] - p1[1]) < abs(p2[0] - p1[0]) else 90.0
        override = "<>"
        if label:
            want = nums(label)
            low = "min" in label.lower()
            high = "max" in label.lower()
            exact = len(want) == 1 and not low and not high
            if not exact or abs(want[0] - measured) > 1.0:
                override = label            # keep what the sheet says, and report it
            if len(want) == 1:
                if exact and abs(want[0] - measured) > 1.0:
                    problems.append("dimension reads %s but spans %.0f"
                                    % (label, measured))
                elif low and measured < want[0] - 1.0:
                    problems.append("dimension reads %s but spans only %.0f"
                                    % (label, measured))
                elif high and measured > want[0] + 1.0:
                    problems.append("dimension reads %s but spans %.0f"
                                    % (label, measured))
        msp.add_linear_dim(base=mid, p1=p1, p2=p2, angle=angle, text=override,
                           dimstyle="SY-1-10", dxfattribs={"layer": "S-DIM"}).render()
    for tp, txt, h, a in free:                # any label that paired with nothing
        place(msp, txt, tp, h, a, "S-DIM")
    return problems


def matches(t, drawn, tol=1.0):
    """Is a clause thickness on the sheet — as one board, or two or three built up?"""
    for i, a in enumerate(drawn):
        if abs(t - a) <= tol:
            return True
        for j, b in enumerate(drawn[i + 1:], i + 1):
            if abs(t - (a + b)) <= tol:
                return True
            for c in drawn[j + 1:]:
                if abs(t - (a + b + c)) <= tol:
                    return True
    return False


def check_schedule(sheet, refs, drawn, schedule):
    """Compare what the sheet draws with what the clause says the build-up is made of."""
    problems = []
    by_mat = {}
    for mat, t in drawn:
        by_mat.setdefault(mat, []).append(round(t, 1))
    for ref in refs:
        rec = schedule.get(ref)
        if not rec:
            continue
        for lay in rec["layers"]:
            mat, t = lay["hatch"], float(lay["t"])
            if mat in ("void", "membrane") or mat not in by_mat:
                continue
            if not matches(t, by_mat[mat]):
                problems.append(
                    "%s %s: clause gives %g %s (%s); the sheet draws it at %s"
                    % (ref, rec["title"][:34], t, mat, lay["material"][:34],
                       ", ".join("%g" % d for d in sorted(set(by_mat[mat])))))
    return problems


# ---------------------------------------------------------------- paper space

def layout(doc, sheet, used, refs, schedule, paper):
    w, h = PAPER[paper]
    lay = doc.layouts.new("1-10 @ %s" % paper.upper())
    lay.page_setup(size=(w, h), margins=(MARGIN,) * 4, units="mm", scale=(1, 1))
    psp = lay
    fx0, fy0, fx1, fy1 = MARGIN, MARGIN, w - MARGIN, h - MARGIN
    psp.add_lwpolyline([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)], close=True,
                       dxfattribs={"layer": "S-FRAME"})
    psp.add_line((fx0, fy0 + TITLE_H), (fx1, fy0 + TITLE_H), dxfattribs={"layer": "S-FRAME"})

    vx, vy, vw, vh = sheet["view"]
    pw, ph = vw / SCALE, vh / SCALE                  # what the drawing takes on paper
    area_h = (fy1 - fy0) - TITLE_H
    cx, cy = fx0 + 4 + pw / 2, fy0 + TITLE_H + area_h / 2
    vp = psp.add_viewport(
        center=(cx, cy), size=(pw, ph),
        view_center_point=(vx + vw / 2, -(vy + vh / 2)),
        view_height=vh, dxfattribs={"layer": "S-VPORT"})
    vp.dxf.flags = vp.dxf.flags | 16384              # display locked: the scale stays 1:10

    # title block
    def line(txt, x, y, size=2.2, layer="S-TITLE", anchor="start"):
        place(psp, txt, (x, y), size, anchor, layer)

    line("%s   %s" % (sheet["ref"], sheet["title"]), fx0 + 4, fy0 + TITLE_H - 8.5, 3.4)
    line("%s @ %s   ·   model space 1:1 in millimetres   ·   plot the layout 1:1, the "
         "viewport carries the 1:10" % (sheet["sub"].split("·")[0].strip(), paper.upper()),
         fx0 + 4, fy0 + TITLE_H - 14.5, 2.0, "S-TEXT")
    line("STATUS: FOR BUILDING CONTROL APPROVAL   ·   DIMENSIONS IN MILLIMETRES   ·   "
         "DO NOT SCALE FROM THIS DRAWING", fx0 + 4, fy0 + 8.5, 2.0, "S-TEXT")
    line("Library detail, not a project detail. Foundations, beams and lintels are "
         "indicative and to the structural engineer's design.",
         fx0 + 4, fy0 + 4.0, 2.0, "S-TEXT")
    line("Specline detail library · P01", fx1 - 4, fy0 + TITLE_H - 8.5, 2.4, "S-TITLE", "end")

    # right-hand column: the hatch key, then the build-ups the sheet references
    kx = fx0 + pw + 14
    ky = fy1 - 6
    if kx + 60 < fx1:
        line("MATERIALS", kx, ky, 2.4, "S-KEY")
        ky -= 6
        for mat in used:
            colour, pattern, pscale, _c = MAT[mat]
            box = [(kx, ky - 5), (kx + 14, ky - 5), (kx + 14, ky + 1), (kx, ky + 1)]
            psp.add_lwpolyline(box, close=True, dxfattribs={"layer": "S-KEY"})
            if pattern:
                hh = psp.add_hatch(color=colour, dxfattribs={"layer": "S-KEY"})
                hh.set_pattern_fill(pattern, scale=pscale / SCALE)
                hh.paths.add_polyline_path(box, is_closed=True)
            elif mat in COURSE:
                pitch = COURSE[mat][0] / SCALE
                yy = ky - 5 + pitch
                while yy < ky + 1:
                    psp.add_line((kx, yy), (kx + 14, yy), dxfattribs={"layer": "S-KEY"})
                    yy += pitch
            line(MATERIAL_NAMES.get(mat, mat), kx + 17, ky - 3.6, 2.0, "S-KEY")
            ky -= 8
        ky -= 4
        for ref in refs:
            rec = schedule.get(ref)
            if not rec:
                continue
            line("%s   %s" % (ref, rec["title"]), kx, ky, 2.4, "S-REF")
            ky -= 4.6
            if rec.get("u_achieved"):
                line("U-value achieved %s W/m2K against a target of %s"
                     % (rec["u_achieved"], rec.get("u_target") or "-"), kx, ky, 2.0, "S-KEY")
                ky -= 4.6
            for l in rec["layers"]:
                line("%-7s %s" % ("%g" % l["t"], l["material"][:52]), kx, ky, 2.0, "S-KEY")
                ky -= 3.6
            line("Layers read from the clause — check against build-up-schedule.md.",
                 kx, ky, 1.8, "S-KEY")
            ky -= 7


MATERIAL_NAMES = {
    "brick": "Facing brickwork", "block": "Aircrete blockwork",
    "dense": "Dense concrete block", "ins": "Rigid insulation board",
    "wool": "Mineral wool", "timber": "Sawn timber", "conc": "Concrete",
    "lean": "Lean mix concrete", "screed": "Screed / sand", "hard": "Hardcore",
    "earth": "Subsoil", "pboard": "Plasterboard", "membrane": "DPC / DPM / VCL",
    "void": "Cavity",
}


# ---------------------------------------------------------------- schedule

def load_schedule():
    """The build-ups the sheets reference, keyed by their reference on the drawing."""
    data = json.load(open(JSON_SRC, encoding="utf-8"))
    out = {}
    for ref, (type_key, title) in BUILDUPS.items():
        for rec in data["types"][type_key]["buildups"]:
            if rec["title"] == title:
                out[ref] = rec
                break
        else:
            print("  ! %s: no build-up called %r in %s" % (ref, title, type_key))
    return out


def to_png(path_dxf, path_png):
    """A picture of the drawing, to look at before it is issued.

    Two things are done to the copy that is rendered and to nothing else: ACI 7 is
    remapped to near-black, because the renderer treats 7 as white on white paper, and
    pattern hatches are exploded into their lines, because the renderer resolves a
    pattern by name only in CAD. The DXF on disk is untouched.
    """
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.render import hatching
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    doc = ezdxf.readfile(path_dxf)
    for lay in doc.layers:
        if lay.dxf.color == 7:
            lay.dxf.color = 250
    msp = doc.modelspace()
    for h in msp.query("HATCH"):
        if h.dxf.solid_fill:
            continue
        try:
            for a, b in hatching.hatch_entity(h):
                msp.add_line(a, b, dxfattribs={"layer": h.dxf.layer})
        except Exception:
            pass
        msp.delete_entity(h)

    fig = plt.figure(figsize=(16.5, 11.7))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(msp, finalize=True)
    fig.savefig(path_png, dpi=150, facecolor="white")
    plt.close(fig)


def main():
    argv = sys.argv[1:]
    paper = "a3"
    if "--paper" in argv:
        paper = argv[argv.index("--paper") + 1].lower()
    want_png = "--png" in argv
    check_only = "--check" in argv
    wanted = [a.upper() for a in argv if re.fullmatch(r"[Dd]-?\d{3}", a)]
    wanted = [a if "-" in a else a[0] + "-" + a[1:] for a in wanted]

    if paper not in PAPER:
        sys.exit("paper must be a3 or a4")
    if not os.path.exists(SVG_SRC):
        sys.exit("missing %s" % SVG_SRC)
    schedule = load_schedule()
    sheets = read_sheets(SVG_SRC, wanted or None)
    if not sheets:
        sys.exit("no details found — check the reference or the source page")

    os.makedirs(OUT, exist_ok=True)
    trouble = 0
    for sheet in sheets:
        doc, problems = build(sheet, schedule, paper)
        if not check_only:
            path = os.path.join(OUT, sheet["ref"] + ".dxf")
            doc.saveas(path)
            if want_png:
                try:
                    to_png(path, path[:-4] + ".png")
                except Exception as e:
                    print("     (no png for %s: %s)" % (sheet["ref"], e))
        print("  %s  %-52s %s" % (sheet["ref"], sheet["title"][:52],
                                  "%d to check" % len(problems) if problems else "ok"))
        for p in problems:
            print("        - %s" % p)
        trouble += len(problems)

    where = "checked" if check_only else "written to output/dxf/details/"
    print("\n  %d detail%s %s  ·  %d thing%s to check against the clause"
          % (len(sheets), "" if len(sheets) == 1 else "s", where,
             trouble, "" if trouble == 1 else "s"))


if __name__ == "__main__":
    main()
