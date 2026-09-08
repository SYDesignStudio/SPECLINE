#!/usr/bin/env python3
"""Build-up sections as DXF, from reference/details/build-up-schedule.json.

    python docgen/dxf_buildups.py                  every build-up
    python docgen/dxf_buildups.py extension        one project type
    python docgen/dxf_buildups.py extension EW     one type, one reference group
    python docgen/dxf_buildups.py --no-pdf         DXF only, skip the check prints

Writes output/dxf/<type>/<GROUP>_<title>.dxf and a matching .pdf to look at.

HOW IT IS SET OUT, and why it matters more than how it looks.

  Model space is 1:1 in millimetres. Never scale the geometry — a detail is only useful if
  someone can dimension off it in CAD and get the real number. Scale belongs to the paper
  space viewport, which is set to 1:10, matching the drawn sheets in reference/details/.

  One DXF layer per material, named S-MAT-<hatch>, plus S-CUT, S-DIM, S-TEXT, S-LEAD and
  S-BREAK. Lineweight is set on the layer, not the entity, so a CAD user can re-pen the whole
  drawing by editing layers.

  Masonry coursing is drawn as real lines at real centres — brick at 75, blockwork at 225 —
  rather than as a hatch pattern. A hatch would be an approximation of the bond; lines at
  centres ARE the coursing, they land where the courses land, and they read correctly in
  section where a bond pattern does not.

WHAT IT CANNOT DO. It draws the build-up: the layers, in order, to thickness. It does not
draw a junction. A junction is where two build-ups meet and the insulation, the damp proof
course and the fire separation have to be resolved, and that is a decision, not a stack of
rectangles — see reference/details/detail-register.md for which ones are worth drawing.

The layer data comes from clause prose, so check any output against the clause printed in
build-up-schedule.md before it goes near a submission. Where a build-up names a verified
table, that table wins and the DXF says so on the sheet.
"""
import glob, json, os, re, sys

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    sys.exit("ezdxf is not installed.  python -m pip install ezdxf matplotlib")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "reference", "details", "build-up-schedule.json")
OUT  = os.path.join(ROOT, "output", "dxf")

SECTION = 900.0          # how much of the element to show across the layers, mm
TXT     = 25.0           # 2.5mm on paper at 1:10
TXT_S   = 18.0
SCALE   = 10.0           # paper space viewport scale

# Walls are cut through their thickness and read left (outside) to right (inside).
# Floors and roofs are cut vertically and read bottom to top, which is the order the
# clauses state them in: hardcore, slab, insulation, screed.
HORIZONTAL = {"EW", "IW", "SW", "BW"}
VERTICAL   = {"GF", "IF", "SF", "RF", "BF"}

# material -> (aci colour, hatch pattern or None, pattern scale, coursing pitch in mm)
# A coursing pitch means the material is drawn with real bed joints instead of a hatch.
MAT = {
    "brick":    (31,  None,       1.0,  75.0),   # 65 brick + 10 bed joint
    "block":    (254, None,       1.0, 225.0),   # 215 block + 10 bed joint
    "dense":    (253, None,       1.0, 225.0),
    "ins":      (51,  "ANSI37",  12.0, None),    # rigid board: cross hatch
    "wool":     (41,  "INSUL",   14.0, None),    # quilt: the batt symbol
    "timber":   (42,  "ANSI31",  24.0, None),
    "metal":    (5,   "ANSI32",  18.0, None),    # a steel member, not a timber one
    "conc":     (8,   "AR-CONC",  0.6, None),
    "lean":     (9,   "AR-CONC",  1.0, None),
    "screed":   (254, "AR-SAND",  0.5, None),
    "hard":     (8,   "GRAVEL",   4.0, None),
    "earth":    (33,  "EARTH",    8.0, None),
    "pboard":   (254, None,       1.0, None),    # drawn plain, as it is on paper
    "membrane": (1,   None,       1.0, None),    # a line, not a thickness
    "void":     (7,   None,       1.0, None),    # a cavity is empty; leave it empty
}

LAYERS = [
    ("S-CUT",   7,   35),   # cut through structure, heaviest
    ("S-THIN",  8,   18),
    ("S-DIM",   4,   13),
    ("S-TEXT",  7,   13),
    ("S-LEAD",  8,   13),
    ("S-BREAK", 8,   13),
    ("S-TITLE", 7,   25),
]


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:60]


def ascii_(s):
    """DXF text with the standard fonts, so nothing lands on a drawing as an empty box.

    The library is written with typographic characters — a squared sign, an em dash, a middle
    dot — and CAD's default SHX fonts have none of them. Spelled out, they survive.
    """
    return (str(s)
            .replace("²", "2").replace("³", "3")
            .replace("·", "-").replace("—", "-").replace("–", "-")
            .replace("‘", "'").replace("’", "'")
            .replace("“", '"').replace("”", '"')
            .replace("°", "deg").replace(" ", " ")
            .encode("ascii", "replace").decode("ascii"))


def setup(doc):
    for name, colour, lw in LAYERS:
        doc.layers.add(name, color=colour, lineweight=lw)
    for mat, (colour, _p, _s, _c) in MAT.items():
        doc.layers.add("S-MAT-" + mat.upper(), color=colour, lineweight=13)
    ds = doc.dimstyles.get("Standard")
    ds.dxf.dimtxt = TXT          # text height
    ds.dxf.dimasz = TXT * 0.5    # arrow size
    ds.dxf.dimexe = TXT * 0.4    # extension beyond the dimension line
    ds.dxf.dimexo = TXT * 0.4    # offset from the object
    ds.dxf.dimgap = TXT * 0.3
    ds.dxf.dimdec = 0            # millimetres, whole numbers
    ds.dxf.dimlunit = 2


# A zone that merge_member_fill() folded a member into: "mineral wool between 47 x 220mm C24
# joists at 400mm centres". Drawn, because a CAD user dimensioning a floor needs the joists in it
# and not a solid band of quilt where the structure is. Only floors and roofs: a wall is cut
# through its thickness and its studs run out of the page, so a vertical section cannot show them.
MEMBER_ZONE = re.compile(r"between\s+(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm\s+(.{0,24})", re.I)
AT_CENTRES  = re.compile(r"\bat\s+(\d{3,4})\s*mm\s+(?:or\s+\d{3,4}\s*mm\s+)?"
                         r"(?:rafter\s+|joist\s+|stud\s+)?centres", re.I)


def zone_bands(layer, inner_first):
    """How a layer divides across its thickness: [(offset, thickness, hatch), ...].

    A partly filled zone is two things. 100mm of quilt in a 220mm joist zone is 100mm of quilt
    and 120mm of nothing, and a CAD user dimensioning a solid 220mm band of it would specify
    twice the insulation the clause states. The fill sits against the inner face — quilt rests
    on the ceiling below it, board between rafters is held to the warm side. The sheets use the
    same rule; see docgen/sheet_buildups.py.
    """
    t = float(layer["t"])
    f = float(layer.get("fill_t") or 0)
    mat = layer.get("hatch") or "void"
    if not f or f >= t:
        return [(0.0, t, mat)]
    return ([(0.0, f, mat), (f, t - f, "void")] if inner_first
            else [(0.0, t - f, "void"), (t - f, f, mat)])


def member_run(layer, clause):
    mat = layer.get("material") or ""
    m = MEMBER_ZONE.search(mat)
    if not m:
        return None
    c = AT_CENTRES.search(mat) or next((x for p in clause for x in [AT_CENTRES.search(p)] if x), None)
    if not c:
        return None
    metal = bool(re.match(r"\s*(?:metal|steel|galvanised|light gauge)", m.group(3), re.I))
    return {"breadth": float(m.group(1)), "centres": float(c.group(1)),
            "hatch": "metal" if metal else "timber"}


def members(msp, run, y0, y1, breadth, centres, hatch):
    """The members inside a zone, at their real centres along the run."""
    x = centres * 0.5
    while x < run - breadth:
        band(msp, x, y0, x + breadth, y1, hatch)
        x += centres


def band(msp, x0, y0, x1, y1, mat):
    """One layer of the build-up: its fill, its coursing or hatch, and its cut outline."""
    colour, pattern, pscale, pitch = MAT.get(mat, MAT["void"])
    lay = "S-MAT-" + (mat or "void").upper()
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    if pattern:
        h = msp.add_hatch(color=colour, dxfattribs={"layer": lay})
        h.set_pattern_fill(pattern, scale=pscale)
        h.paths.add_polyline_path(pts, is_closed=True)
    elif mat in ("brick", "block", "dense"):
        # No fill. Masonry in section is its bed joints and its outline — that is the
        # convention, and a solid fill turns the courses into a black bar the moment anyone
        # prints in monochrome, which is how a building control set is usually printed.
        pass
    elif mat == "membrane":
        h = msp.add_hatch(color=colour, dxfattribs={"layer": lay})
        h.set_solid_fill(color=colour)
        h.paths.add_polyline_path(pts, is_closed=True)

    # real coursing, at real centres, rather than a bond pattern that only looks like masonry
    if pitch:
        y = y0 + pitch
        while y < y1 - 1:
            msp.add_line((x0, y), (x1, y), dxfattribs={"layer": lay})
            y += pitch

    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "S-CUT"})


def dim(msp, a, b, base, horizontal, from_edge):
    """A dimension drawn as geometry: extension lines, dimension line, 45 degree ticks, text.

    Not a DXF DIMENSION entity, deliberately. These drawings are regenerated from the library
    whenever a clause changes, so nobody should be editing a dimension by hand — and an
    associative dimension buys nothing in return for the trouble it causes: the value is
    computed from the layer thickness, and it renders as extension lines alone in every viewer
    that does not implement dimension blocks in full.
    """
    tick = TXT * 0.45
    if horizontal:
        x0, x1 = a, b
        msp.add_line((x0, from_edge), (x0, base + tick), dxfattribs={"layer": "S-DIM"})
        msp.add_line((x1, from_edge), (x1, base + tick), dxfattribs={"layer": "S-DIM"})
        msp.add_line((x0, base), (x1, base), dxfattribs={"layer": "S-DIM"})
        for x in (x0, x1):
            msp.add_line((x - tick, base - tick), (x + tick, base + tick),
                         dxfattribs={"layer": "S-DIM"})
        v = x1 - x0
        t = msp.add_text(ascii_("%g" % v), height=TXT, dxfattribs={"layer": "S-DIM"})
        # a value that will not fit between its own ticks goes above them, off to one side
        if v * 0.9 < TXT * len("%g" % v) * 0.75:
            # too narrow to sit between its own ticks: raise it a line so it cannot collide
            # with the figure on either side, and let the tick mark it belongs to
            t.set_placement((x1 + tick, base + tick * 1.2 + TXT))
        else:
            t.set_placement(((x0 + x1) / 2, base + tick * 1.2), align=TextEntityAlignment.BOTTOM_CENTER)
    else:
        y0, y1 = a, b
        msp.add_line((from_edge, y0), (base + tick, y0), dxfattribs={"layer": "S-DIM"})
        msp.add_line((from_edge, y1), (base + tick, y1), dxfattribs={"layer": "S-DIM"})
        msp.add_line((base, y0), (base, y1), dxfattribs={"layer": "S-DIM"})
        for y in (y0, y1):
            msp.add_line((base - tick, y - tick), (base + tick, y + tick),
                         dxfattribs={"layer": "S-DIM"})
        v = y1 - y0
        t = msp.add_text(ascii_("%g" % v), height=TXT,
                         dxfattribs={"layer": "S-DIM", "rotation": 90})
        if v * 0.9 < TXT * len("%g" % v) * 0.75:
            t.set_placement((base + tick * 1.2 + TXT, y1 + tick))
        else:
            t.set_placement((base + tick * 1.2, (y0 + y1) / 2), align=TextEntityAlignment.BOTTOM_CENTER)


def break_line(msp, a, b, horizontal):
    """The conventional zig-zag saying the element carries on past the drawing."""
    (x0, y0), (x1, y1) = a, b
    n, pts = 9, []
    for i in range(n + 1):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        if 0 < i < n:
            off = (-1) ** i * TXT * 0.7
            if horizontal: y += off
            else:          x += off
        pts.append((x, y))
    msp.add_lwpolyline(pts, dxfattribs={"layer": "S-BREAK"})


def draw(doc, rec, type_name):
    msp = doc.modelspace()
    horiz = rec["group"] in HORIZONTAL
    layers = rec["layers"]
    total = sum(l["t"] for l in layers)
    # How much of the element to show across the layers. Fixed at 900 a 168mm roof came out as
    # a strip five times longer than it is thick, which reads as a line rather than a section.
    global SECTION
    SECTION = min(900.0, max(300.0, total * 3.0))

    pos = 0.0
    for l in layers:
        t = float(l["t"])
        if horiz:
            # a wall reads left to right, outside first
            for off, wd, hm in zone_bands(l, False):
                band(msp, pos + off, 0, pos + off + wd, SECTION, hm)
        else:
            # a floor or roof reads bottom to top, and the bottom is the ceiling
            for off, ht, hm in zone_bands(l, True):
                band(msp, 0, pos + off, SECTION, pos + off + ht, hm)
            run = member_run(l, rec["clause"])
            if run:
                members(msp, SECTION, pos, pos + t, run["breadth"], run["centres"], run["hatch"])
        pos += t

    # the element continues past the cut
    if horiz:
        break_line(msp, (0, SECTION), (total, SECTION), True)
        break_line(msp, (0, 0), (total, 0), True)
    else:
        break_line(msp, (SECTION, 0), (SECTION, total), False)
        break_line(msp, (0, 0), (0, total), False)

    # a dimension per layer, and the overall above it
    off = SECTION + TXT * 3
    pos = 0.0
    for l in layers:
        t = float(l["t"])
        if horiz: dim(msp, pos, pos + t, off, True, SECTION)
        else:     dim(msp, pos, pos + t, off, False, SECTION)
        pos += t
    off2 = off + TXT * 3.5
    if horiz: dim(msp, 0, total, off2, True, off)
    else:     dim(msp, 0, total, off2, False, off)

    # a leader and a label per layer, stacked clear of the section
    lx = total + TXT * 12 if horiz else SECTION + TXT * 12
    pos, i = 0.0, 0
    for l in layers:
        t = float(l["t"])
        mid = pos + t / 2
        ly = SECTION - (i + 1) * TXT * 2.2 if horiz else mid
        if horiz:
            start, knee = (mid, SECTION * 0.5), (lx - TXT * 2, ly)
        else:
            start, knee = (SECTION * 0.5, mid), (lx - TXT * 2, ly)
        msp.add_lwpolyline([start, knee, (lx, ly)], dxfattribs={"layer": "S-LEAD"})
        msp.add_text(ascii_("%g  %s" % (t, l["material"])),
                     height=TXT_S, dxfattribs={"layer": "S-TEXT"}
                     ).set_placement((lx + TXT * 0.6, ly - TXT_S * 0.4))
        pos += t
        i += 1

    # title block, under the section
    y = -TXT * 3
    def line(txt, h=TXT, gap=2.0):
        nonlocal y
        msp.add_text(ascii_(txt), height=h, dxfattribs={"layer": "S-TITLE"}).set_placement((0, y))
        y -= h * gap
    line("%s  -  %s" % (rec["group"], rec["title"]), TXT * 1.3)
    line("%s  -  %s" % (type_name, rec["category"]), TXT_S)
    if rec.get("u_target") or rec.get("u_achieved"):
        line("Target %s W/m2K   -   Achieved %s" %
             (rec.get("u_target") or "-", rec.get("standard") or "-"), TXT_S)
    line("Overall %g mm  -  drawn 1:1 in millimetres, plot at 1:10" % total, TXT_S)
    line("STATUS: FOR BUILDING CONTROL APPROVAL.  DO NOT SCALE FROM THIS DRAWING.", TXT_S)
    if rec.get("verified_table"):
        line("Layers: use the verified table, buildup-layer-schedule.md section %s"
             % rec["verified_table"], TXT_S)
    else:
        line("Layers read from the clause - check against build-up-schedule.md before issue.", TXT_S)
    return total


def paperspace(doc, rec, total):
    """An A3 layout with the section at a true 1:10, so the sheet measures what it says."""
    try:
        lay = doc.layouts.new("1-10 @ A3")
    except Exception:
        return
    lay.page_setup(size=(420, 297), margins=(10, 10, 10, 10), units="mm")
    w = (total + SECTION) / 2
    cx = total / 2 if rec["group"] in HORIZONTAL else SECTION / 2
    cy = SECTION / 2 if rec["group"] in HORIZONTAL else total / 2
    lay.add_viewport(center=(210, 150), size=(380, 250),
                     view_center_point=(cx + SECTION * 0.6, cy),
                     view_height=250 * SCALE)


def to_pdf(path_dxf, path_pdf):
    """A check print, not the deliverable. The DXF is the deliverable.

    The renderer needs telling what to do with hatches and text, or it quietly drops both:
    the default hatch policy leaves pattern fills out, and text is skipped rather than drawn.
    Black on white, absolute lineweights, so the print shows the pen weights the layers carry.
    """
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing.config import (
        Configuration, HatchPolicy, TextPolicy, ColorPolicy, LineweightPolicy)
    import matplotlib.pyplot as plt

    doc = ezdxf.readfile(path_dxf)
    cfg = Configuration(
        hatch_policy=HatchPolicy.SHOW_APPROXIMATE_PATTERN,
        text_policy=TextPolicy.FILLING,
        color_policy=ColorPolicy.BLACK,
        # RELATIVE, not ABSOLUTE: an absolute 0.35mm pen against a drawing 900mm tall renders
        # as a black bar, because the backend measures the pen in paper units and the model in
        # millimetres. Relative keeps the pen proportional to the view.
        lineweight_policy=LineweightPolicy.RELATIVE,
        lineweight_scaling=0.7,
    )
    fig = plt.figure(figsize=(16.5, 11.7))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_axis_off()
    fig.patch.set_facecolor("white")
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg
             ).draw_layout(doc.modelspace(), finalize=True)
    fig.savefig(path_pdf, dpi=200, facecolor="white")
    plt.close(fig)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    # The issue PDF now comes from docgen/sheet_buildups.py, which lays out a proper A4
    # sheet. This one is only a check print of the CAD geometry, so it is opt-in.
    want_pdf = "--pdf" in sys.argv
    if not os.path.exists(SRC):
        sys.exit("run python docgen/detail_schedule.py first")
    data = json.load(open(SRC, encoding="utf-8"))

    made, skipped, written = 0, 0, set()
    for key, t in data["types"].items():
        if args and key != args[0]:
            continue
        for rec in t["buildups"]:
            if len(args) > 1 and rec["group"] != args[1].upper():
                continue
            if not rec["layers"]:
                print("  skipped %-10s %-46s no layer thicknesses in the clause"
                      % (key, rec["title"][:46]))
                skipped += 1
                continue
            if rec["group"] not in HORIZONTAL and rec["group"] not in VERTICAL:
                print("  skipped %-10s %-46s %s is not a layered build-up"
                      % (key, rec["title"][:46], rec["group"]))
                skipped += 1
                continue

            doc = ezdxf.new("R2010", setup=True)
            doc.header["$INSUNITS"] = 4          # millimetres
            doc.header["$MEASUREMENT"] = 1       # metric
            setup(doc)
            total = draw(doc, rec, t["name"])
            paperspace(doc, rec, total)

            d = os.path.join(OUT, key)
            os.makedirs(d, exist_ok=True)
            base = os.path.join(d, "%s_%s" % (rec["group"], slug(rec["title"])))
            doc.saveas(base + ".dxf")
            written.add(base)
            if want_pdf:
                try:
                    to_pdf(base + ".dxf", base + ".pdf")
                except Exception as e:
                    print("     (no pdf for %s: %s)" % (rec["title"][:40], e))
            made += 1
    print("\n  %d drawings written to output/dxf/  ·  %d skipped" % (made, skipped))

    # A build-up that stops drawing leaves its last DXF behind, and that file is wrong by
    # definition - worse than a stale sheet, because someone opens it in CAD and dimensions
    # off it. Only a full run may clear them: a filtered run knows nothing about the drawings
    # it was not asked for. The sheet generator carries the same rule.
    if not args:
        keep = {b + ext for b in written for ext in ('.dxf', '.pdf')}
        orphans = [f for f in glob.glob(os.path.join(OUT, '*', '*.*')) if f not in keep]
        for f in orphans:
            os.remove(f)
        if orphans:
            print('  %d drawing(s) removed for build-ups that no longer draw:' % len(orphans))
            for f in sorted({os.path.basename(f).rsplit('.', 1)[0] for f in orphans}):
                print('      %s' % f)


if __name__ == "__main__":
    main()
