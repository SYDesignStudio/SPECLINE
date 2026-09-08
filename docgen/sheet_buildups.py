#!/usr/bin/env python3
"""Build-up sheets: one A4 drawing per build-up, laid out to be issued.

    python docgen/sheet_buildups.py                 every build-up
    python docgen/sheet_buildups.py extension       one project type
    python docgen/sheet_buildups.py extension EW    one type, one reference group
    python docgen/sheet_buildups.py --practice p.json   whose name goes in the title block
    python docgen/sheet_buildups.py --practice brand    this installation's own practice
    python docgen/sheet_buildups.py --html          write the HTML and stop, no PDF

Writes output/sheets/<type>/<REF>_<title>.pdf, and the HTML each was printed from.

WHAT A SHEET CARRIES. The section on the left with its annotations, the thermal performance
and the specification on the right, the scale note, and a title block. The annotations are not
labels invented for the drawing — each one is the sentence from the clause that describes that
layer, so the drawing and the specification cannot drift apart. Same for the numbers: the
thicknesses are the ones in build-up-schedule.json and the U-values are the ones in the
library.

WHY HTML AND NOT CAD. This is the issue sheet, and typography is most of what makes it
readable. The DXF is the other half of the job — docgen/dxf_buildups.py — and that one is for
someone who needs the geometry in CAD. Neither replaces the other.

DRAWING CONVENTIONS. Real millimetres throughout, printed at 1:10. Masonry shows bed joints at
real centres, brick 75 and blockwork 225. Wall ties are drawn where the clause specifies them,
at the centres it specifies, set with the fall to the outer leaf that the clause requires —
a tie drawn level, or falling inwards, is a drawing that teaches the wrong thing.
"""
import html as H
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "reference", "details", "build-up-schedule.json")
OUT  = os.path.join(ROOT, "output", "sheets")

HORIZONTAL = {"EW", "IW", "SW", "BW"}          # cut through the thickness, drawn upright
VERTICAL   = {"GF", "IF", "SF", "RF", "BF"}    # cut vertically, layers stacked

WALL_H  = 1800.0     # how much wall height to show, mm
FLOOR_W = 1000.0     # how much floor or roof run to show, mm
TXT     = 27.0       # annotation text, model mm (about 7.7pt at 1:10)
TXT_S   = 23.0

COURSE = {"brick": 75.0, "block": 225.0, "dense": 225.0}


def esc(s):
    return H.escape(str(s), quote=True)


def practice(source=None):
    """The practice whose name goes on the sheet — THE ONE USING THE TOOL.

    This is the commercial rule in CLAUDE.md and it is not a preference: a specification or a
    detail carries the subscribing practice's own identity, never the vendor's. No technologist
    will issue a drawing to building control under another company's name. So this generator
    hard-codes NO practice at all. It reads one, and if it is given none it prints placeholders
    for a practice to fill in, which is the safe failure: an obviously blank title block gets
    corrected, someone else's name on your drawing might not.

    Where it looks, in order:
      --practice <file.json>          an explicit profile
      SPECLINE_PRACTICE               the same, as an environment variable
      ../specline-practice.json       beside the other per-installation data, above the repo
      --practice brand                docgen/brand_inhouse.py, SY Design Studio's own profile,
                                      for its in-house documents only

    In the hosted app the equivalent profile is the `practices` row for the signed-in account,
    which is where a sheet generated server-side would take it from.

    The lookup itself is docgen/practice.py, shared with the Word and PDF generators so the
    specification and the details cannot disagree about who drew the job. This used to hold its
    own copy of it, reading `docgen/brand.py` for --practice brand; when brand.py stopped owning
    a practice that path quietly returned the installed profile instead of the in-house one.

    Project, client and the job number are NOT filled from anywhere. They belong to a job, and
    these are library details, so a value there would be an invented job.
    """
    sys.path.insert(0, os.path.join(ROOT, "docgen"))
    import practice as _pr
    p = _pr.load(source)
    p["date"] = __import__("datetime").date.today().strftime("%m.%y")
    p["resp"] = ("All dimensions to be checked on site. Read in conjunction with the structural "
                 "engineer's drawings and the insulation manufacturer's current certificate. "
                 "%s %s responsible for the suitability of this detail; compliance of the work "
                 "is determined by the building control body."
                 % (p["who"], "is the named designer and remains" if p["designer"] else "remains"))
    return p


PRACTICE_ = None


def sentences(clause):
    out = []
    for para in clause:
        for s in re.split(r"(?<=[.;])\s+(?=[A-Z0-9])", para):
            s = re.sub(r"\s+", " ", s).strip()
            if len(s) > 25:
                out.append(s)
    return out


def note_for(layer, clause_text, used):
    """What the clause says about THIS layer.

    Taken as the fragment starting at the layer's own thickness in the clause and running to
    the end of that thought, so each leader quotes the part of the specification that describes
    the thing it points at. Matching on whole sentences instead put the same opening sentence
    against every layer, because the opening sentence describes the whole build-up.
    """
    probe = (layer.get("read_from") or "").strip()
    frag = ""
    if probe:
        i = clause_text.find(probe[:30])
        if i >= 0:
            window = clause_text[i:i + 300]
            cut = window.find(". ")
            if cut < 30:                       # no sentence end nearby: stop at a comma instead
                c = [window.find(", ", 60), window.find("; ", 60)]
                c = [x for x in c if x > 0]
                cut = min(c) if c else -1
            if cut > 0:
                frag = window[:cut + 1].strip().rstrip(",;")
            else:
                # Nothing to break on inside the window. Stop at a word, not in the middle of
                # one, and say so: a note that ends "where the underlay is not br." reads as a
                # specification, and it is a truncation.
                frag = window[:window.rfind(" ", 0, 230)].strip().rstrip(",;") + " …"
    if not frag or frag[:26].lower() in used:
        frag = "%g mm %s" % (layer["t"], layer["material"].rstrip(" of").rstrip())
    used.add(frag[:26].lower())
    frag = frag[0].upper() + frag[1:]
    return frag if frag.endswith((".", "…")) else frag + "."


def tie_spec(clause):
    """Wall ties, only if the clause actually specifies them, and only at its own centres."""
    txt = " ".join(clause)
    m = re.search(r"ties?[^.]{0,120}?(\d{3})mm vertical(?:\s+and\s+(\d{3})mm horizontal)?", txt, re.I)
    if not m:
        return None
    return {"vert": float(m.group(1)),
            "horiz": float(m.group(2)) if m.group(2) else None,
            "fall": bool(re.search(r"fall to the outer leaf", txt, re.I)),
            "note": next((s for s in sentences(clause) if re.search(r"\bties\b", s, re.I)), "")}


DEFS = """<defs>
  <pattern id="p-brick" width="60" height="75" patternUnits="userSpaceOnUse">
    <rect width="60" height="75" fill="#EFEAE3"/>
    <path d="M-8 8 L8 -8 M0 60 L60 0 M52 68 L68 52" stroke="#CFC5B6" stroke-width="2"/>
    <rect y="0" width="60" height="9" fill="#E2DACD"/>
    <path d="M0 0h60M0 9h60" stroke="#B9AE9C" stroke-width="1.6"/>
  </pattern>
  <pattern id="p-block" width="75" height="225" patternUnits="userSpaceOnUse">
    <rect width="75" height="225" fill="#F2F2EF"/>
    <path d="M0 0 L75 75 M0 75 L75 0 M0 75 L75 150 M0 150 L75 75 M0 150 L75 225 M0 225 L75 150"
          stroke="#D8D8D1" stroke-width="2"/>
    <rect y="0" width="75" height="9" fill="#E4E4DD"/>
    <path d="M0 0h75M0 9h75" stroke="#B4B4AA" stroke-width="1.6"/>
  </pattern>
  <pattern id="p-dense" width="75" height="225" patternUnits="userSpaceOnUse">
    <rect width="75" height="225" fill="#E3E2DC"/>
    <path d="M0 0 L75 75 M0 75 L75 0 M0 75 L75 150 M0 150 L75 75 M0 150 L75 225 M0 225 L75 150"
          stroke="#C4C3BA" stroke-width="2.4"/>
    <rect y="0" width="75" height="9" fill="#D2D1C8"/>
    <path d="M0 0h75M0 9h75" stroke="#A5A499" stroke-width="1.6"/>
  </pattern>
  <pattern id="p-wool" width="70" height="30" patternUnits="userSpaceOnUse">
    <rect width="70" height="30" fill="#F5EBE9"/>
    <path d="M0 21 q9 -18 18 0 t18 0 t18 0 t18 0" fill="none" stroke="#BE968F" stroke-width="2"/>
  </pattern>
  <!-- Rigid board insulation: the lobed chain a technologist expects, not a flat tint. Drawn
       as a column of pinched lobes so it reads the same way up a cavity as across a roof. -->
  <pattern id="p-ins" width="46" height="30" patternUnits="userSpaceOnUse">
    <rect width="46" height="30" fill="#FBF2D8"/>
    <ellipse cx="23" cy="15" rx="21" ry="13.5" fill="none" stroke="#D3AE59" stroke-width="2"/>
    <path d="M2 1.5 q20 13.5 0 27 M44 1.5 q-20 13.5 0 27" fill="none" stroke="#D3AE59" stroke-width="2"/>
  </pattern>
  <!-- Plasterboard: the fine stipple, so a lining reads as a board and not as a void. -->
  <pattern id="p-pboard" width="18" height="18" patternUnits="userSpaceOnUse">
    <rect width="18" height="18" fill="#ECEBE7"/>
    <circle cx="4" cy="5" r="1.1" fill="#A9A8A2"/><circle cx="13" cy="11" r="1.1" fill="#A9A8A2"/>
    <circle cx="8" cy="15" r="0.9" fill="#A9A8A2"/>
  </pattern>
  <pattern id="p-metal" width="34" height="34" patternUnits="userSpaceOnUse">
    <rect width="34" height="34" fill="#E7EAEC"/>
    <path d="M0 34 L34 0 M-8 8 L8 -8 M26 42 L42 26" stroke="#9BA6AD" stroke-width="1.9"/>
  </pattern>
  <pattern id="p-timber" width="110" height="110" patternUnits="userSpaceOnUse">
    <rect width="110" height="110" fill="#F0E4CE"/>
    <path d="M-12 96 q55 -34 122 0 M-12 70 q55 -34 122 0 M-12 44 q55 -34 122 0 M-12 18 q55 -34 122 0"
          fill="none" stroke="#CFAF7C" stroke-width="1.8"/>
  </pattern>
  <pattern id="p-conc" width="52" height="52" patternUnits="userSpaceOnUse">
    <rect width="52" height="52" fill="#EAE9E5"/>
    <path d="M22 15 l9 11 -18 0 z" fill="#C2C5C7"/>
    <circle cx="10" cy="13" r="3" fill="#C2C5C7"/><circle cx="38" cy="9" r="2.4" fill="#C2C5C7"/>
    <circle cx="8" cy="40" r="2.6" fill="#C2C5C7"/><circle cx="43" cy="36" r="2.2" fill="#C2C5C7"/>
  </pattern>
  <pattern id="p-lean" width="46" height="46" patternUnits="userSpaceOnUse">
    <rect width="46" height="46" fill="#E4E2DC"/>
    <circle cx="12" cy="12" r="3.6" fill="#BDBCB4"/><circle cx="33" cy="26" r="3" fill="#BDBCB4"/>
    <circle cx="20" cy="38" r="2.6" fill="#BDBCB4"/>
  </pattern>
  <pattern id="p-screed" width="26" height="26" patternUnits="userSpaceOnUse">
    <rect width="26" height="26" fill="#F3F2EF"/>
    <circle cx="5" cy="6" r="1.4" fill="#B5B8BA"/><circle cx="18" cy="15" r="1.4" fill="#B5B8BA"/>
    <circle cx="11" cy="22" r="1.2" fill="#B5B8BA"/>
  </pattern>
  <pattern id="p-hard" width="70" height="70" patternUnits="userSpaceOnUse">
    <rect width="70" height="70" fill="#E7E5DF"/>
    <path d="M6 19 l13 -9 9 12 -12 9 z M37 6 l15 5 -5 13 -13 -6 z M17 47 l13 -6 8 12 -13 7 z
             M47 40 l13 7 -7 13 -12 -9 z" fill="#D6D3CB" stroke="#ABA99F" stroke-width="1.6"/>
  </pattern>
  <pattern id="p-earth" width="36" height="36" patternUnits="userSpaceOnUse">
    <rect width="36" height="36" fill="#EFEDE7"/>
    <path d="M0 36 L36 0 M-9 9 L9 -9 M27 45 L45 27" stroke="#C2C7C9" stroke-width="1.7"/>
  </pattern>
</defs>"""

FILL = {"brick": "url(#p-brick)", "block": "url(#p-block)", "dense": "url(#p-dense)",
        "ins": "url(#p-ins)", "wool": "url(#p-wool)", "timber": "url(#p-timber)",
        "conc": "url(#p-conc)", "lean": "url(#p-lean)", "screed": "url(#p-screed)",
        "hard": "url(#p-hard)", "earth": "url(#p-earth)", "pboard": "url(#p-pboard)",
        "metal": "url(#p-metal)",
        "membrane": "#8A5A52", "void": "#FFFFFF"}


def courses(x0, y0, x1, y1, pitch, vertical_stack):
    """Bed joints at real centres, set out from the bottom of the leaf."""
    out = []
    if vertical_stack:
        return out
    y = y0 + pitch
    while y < y1 - 2:
        out.append('<path d="M%.1f %.1f h%.1f" stroke="#A79C8B" stroke-width="1.6"/>'
                   % (x0, y, x1 - x0))
        y += pitch
    return out


def ins_pattern(pid, t, across):
    """A lobe chain sized to the layer it fills.

    A fixed tile put two cramped columns of lobes across a 90mm board and a single squashed one
    across a 25mm upstand. Sizing the tile to the thickness gives one clean chain whatever the
    board is, which is how the symbol is drawn by hand. `across` is True for a band that runs
    horizontally — a floor or a roof — and False for an upright wall.
    """
    t = max(float(t), 8.0)
    w, h = (t * 0.62, t) if across else (t, t * 0.62)
    return ('<defs><pattern id="%s" width="%.2f" height="%.2f" patternUnits="userSpaceOnUse">'
            '<rect width="%.2f" height="%.2f" fill="#FBF2D8"/>'
            '<ellipse cx="%.2f" cy="%.2f" rx="%.2f" ry="%.2f" fill="none" stroke="#D3AE59" '
            'stroke-width="%.2f"/></pattern></defs>'
            % (pid, w, h, w, h, w / 2, h / 2, max(w / 2 - 1.5, 1.5), max(h / 2 - 1.5, 1.5),
               max(1.6, t * 0.03)))


def layer_fill(parts, i, mat, t, across):
    """The fill for one band, adding a sized pattern where the material needs one."""
    if mat == "ins":
        pid = "ins%d%s" % (i, "h" if across else "v")
        parts.append(ins_pattern(pid, t, across))
        return "url(#%s)" % pid
    return FILL.get(mat, "#FFF")


MEMBER_IN = re.compile(r"\bstuds?\b|\bjoists?\b|\brafters?\b", re.I)
AT_CENTRES = re.compile(r"\bat\s+(\d{3,4})\s*mm\s+centres", re.I)
CORE_W = 100.0          # drawing width for a stud zone the clause does not size. Never printed.


def stud_zone(rec):
    # Wall ties are specified at VERTICAL centres, so a wall that has them is a vertical section
    # and its studs cannot be shown at their spacing in that view. Partitions have no ties, and
    # they are the ones read in plan.
    if tie_spec(rec["clause"]):
        return None
    """Where the studs are, and at what centres — from a sized layer or from an unsized core.

    A partition is read in plan: the studs march along the wall at their centres, and that is
    what makes it a stud partition rather than a solid one. A vertical section cannot show them
    at all, which is why the metal stud partition sheet was two lines of plasterboard.
    """
    for i, l in enumerate(rec["layers"]):
        mat = l.get("material") or ""
        m = AT_CENTRES.search(mat)
        # the band may be hatched as whatever fills it — a stud zone merged with its insulation
        # is drawn as the insulation, and the studs are drawn over it
        if l.get("hatch") in ("timber", "metal") or MEMBER_IN.search(mat):
            # the centres come from the band where it states them, and from the clause where the
            # band is a merged zone whose label kept the material but not the spacing
            c = m or next((x for para in rec["clause"]
                           for x in [AT_CENTRES.search(para)] if x), None)
            if c:
                metal = re.search(r"metal|steel|galvanised", mat, re.I)
                return {"i": i, "centres": float(c.group(1)),
                        "hatch": "metal" if metal else "timber", "core": False}
    c = rec.get("stud_core")
    if c:
        return {"i": None, "centres": c["centres"], "hatch": c["hatch"], "core": True,
                "fill": c.get("fill"), "note": c["note"]}
    return None


def studs(x0, x1, H_, centres, hatch):
    """C-sections at their centres, drawn as they are cut in plan."""
    out, y = [], centres * 0.5
    w = x1 - x0
    while y < H_ - 10:
        if hatch == "metal":
            # A C-stud cut in plan: the web runs across the wall thickness with a flange at each
            # end, both turned the same way. Drawn the other way round it is not a C.
            out.append('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f" fill="none" '
                       'stroke="#1B1B1B" stroke-width="5" stroke-linejoin="miter" '
                       'stroke-linecap="square"/>'
                       % (x0, y + 22, x0, y, x1, y, x1, y + 22))
        else:
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="48" fill="url(#p-timber)" '
                       'stroke="#1B1B1B" stroke-width="3"/>' % (x0, y - 24, w))
        y += centres
    return out


def wall_svg(rec, sents):
    layers = list(rec["layers"])
    zone = stud_zone(rec)
    core_at = None
    if zone and zone["core"]:
        # an undimensioned zone between the two linings: the clause gives the centres and leaves
        # the depth to the system, so the drawing shows the studs and states no thickness
        core_at = 1 if len(layers) > 1 else len(layers)
        layers = layers[:core_at] + [{"t": CORE_W, "material": "", "_core": True,
                                      "hatch": zone.get("fill") or zone["hatch"]}] + layers[core_at:]
        zone["i"] = core_at
    total = sum(float(l["t"]) for l in layers)
    ties = tie_spec(rec["clause"])
    H_ = WALL_H
    parts = [DEFS]

    # the layers
    pos = 0.0
    bands = []
    for i, l in enumerate(layers):
        t = float(l["t"])
        mat = l["hatch"] or "void"
        parts.append('<rect x="%.1f" y="0" width="%.1f" height="%.1f" fill="%s" stroke="#1B1B1B" stroke-width="2.6"/>'
                     % (pos, t, H_, layer_fill(parts, i, mat, t, False)))
        if mat in COURSE:
            parts += courses(pos, 0, pos + t, H_, COURSE[mat], False)
        bands.append((pos, pos + t))
        pos += t
    if zone and zone["i"] is not None:
        x0, x1 = bands[zone["i"]]
        parts += studs(x0, x1, H_, zone["centres"], zone["hatch"])

    # wall ties, only where the clause asks for them, at its centres, falling to the outer leaf
    if ties:
        cav = None
        pos = 0.0
        for l in layers:
            if (l["hatch"] or "") in ("void", "ins", "wool") and cav is None:
                cav = [pos, pos + float(l["t"])]
            elif cav and (l["hatch"] or "") in ("void", "ins", "wool"):
                cav[1] = pos + float(l["t"])
            pos += float(l["t"])
        if cav:
            x_in, x_out = cav[1] + 18, cav[0] - 18
            y = ties["vert"] * 0.5
            while y < H_ - 10:
                drop = 14 if ties["fall"] else 0
                parts.append('<path d="M%.1f %.1f L%.1f %.1f" stroke="#1B1B1B" stroke-width="4.4" stroke-linecap="round"/>'
                             % (x_in, y - drop / 2, x_out, y + drop / 2))
                y += ties["vert"]

    # break lines
    for y in (0, H_):
        parts.append('<path d="M%.1f %.1f h%.1f" stroke="#1B1B1B" stroke-width="2.2" stroke-dasharray="26 16"/>'
                     % (-26, y, total + 52))

    # Overall dimension across the top — but only when the whole thickness is stated. Where the
    # clause leaves the stud depth to the system there is no overall figure to give, and printing
    # one drawn off a nominal band would be inventing the very number the clause declines to fix.
    dy = -96
    if not (zone and zone["core"]):
        parts.append('<path d="M0 %.1f h%.1f" stroke="#1B1B1B" stroke-width="1.8"/>' % (dy, total))
        for x in (0, total):
            parts.append('<path d="M%.1f %.1f v%.1f" stroke="#1B1B1B" stroke-width="1.8"/>' % (x, dy - 20, 40))
        parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" fill="#1B1B1B">%g</text>'
                     % (total / 2, dy - 26, TXT, total))
    else:
        parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" '
                     'fill="#1B1B1B">STUD DEPTH TO THE SYSTEM SPECIFICATION</text>'
                     % (total / 2, dy - 26, TXT_S))

    # the tie spacing chain down the left
    if ties:
        cx = -150
        n = int(H_ // ties["vert"])
        parts.append('<path d="M%.1f %.1f v%.1f" stroke="#1B1B1B" stroke-width="1.6"/>'
                     % (cx, ties["vert"] * 0.5, ties["vert"] * n))
        for i in range(n + 1):
            y = ties["vert"] * (0.5 + i)
            parts.append('<path d="M%.1f %.1f h34" stroke="#1B1B1B" stroke-width="1.6"/>' % (cx - 17, y))
            if i < n:
                parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" fill="#1B1B1B" '
                             'transform="rotate(-90 %.1f %.1f)">%g</text>'
                             % (cx - 12, y + ties["vert"] / 2, TXT, cx - 12, y + ties["vert"] / 2, ties["vert"]))

    # leaders and the sentence from the clause for each layer
    used = set()
    ctext = " ".join(rec["clause"])
    notes = [(l, (zone["note"] if l.get("_core") else note_for(l, ctext, used))) for l in layers]
    if ties and ties["note"]:
        notes.append((None, ties["note"]))
    lx = total + 250
    step = H_ / max(len(notes), 1)
    body = []
    pos = 0.0
    mids = []
    for l in layers:
        mids.append(pos + float(l["t"]) / 2)
        pos += float(l["t"])
    for i, (l, note) in enumerate(notes):
        ly = step * (i + 0.42)
        if l is not None:
            sx = mids[layers.index(l)]
            parts.append('<circle cx="%.1f" cy="%.1f" r="7" fill="#1B1B1B"/>' % (sx, ly))
            parts.append('<path d="M%.1f %.1f H%.1f" stroke="#1B1B1B" stroke-width="1.8" fill="none"/>'
                         % (sx, ly, lx - 12))
        body.append((lx, ly, note))
    return parts, body, total, H_, (-330, -170, total + 1180, H_ + 150)


def floor_svg(rec, sents):
    """A floor or roof is wide and flat, so it does not fill an upright column the way a wall
    does. Drawn across the top at the column width with a numbered key beneath it, which is
    how a flat build-up is normally read: the section shows the order, the key does the words.
    """
    layers = rec["layers"]
    total = sum(l["t"] for l in layers)
    W = 1040.0
    parts = [DEFS]

    pos = 0.0
    tops = []
    for i, l in enumerate(layers):        # first layer at the bottom, as the clause reads
        t = float(l["t"])
        y = total - pos - t
        mat = l["hatch"] or "void"
        parts.append('<rect x="0" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#1B1B1B" stroke-width="2.6"/>'
                     % (y, W, t, layer_fill(parts, i, mat, t, True)))
        tops.append(y + t / 2)
        pos += t
    for x in (0, W):
        parts.append('<path d="M%.1f %.1f v%.1f" stroke="#1B1B1B" stroke-width="2.2" stroke-dasharray="26 16"/>'
                     % (x, -26, total + 52))

    # overall thickness down the left
    dx = -120
    parts.append('<path d="M%.1f 0 v%.1f" stroke="#1B1B1B" stroke-width="1.8"/>' % (dx, total))
    for y in (0, total):
        parts.append('<path d="M%.1f %.1f h44" stroke="#1B1B1B" stroke-width="1.8"/>' % (dx - 22, y))
    parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" fill="#1B1B1B" '
                 'transform="rotate(-90 %.1f %.1f)">%g</text>'
                 % (dx - 34, total / 2, TXT, dx - 34, total / 2, total))

    # a numbered callout sitting on each layer, staggered so they never collide
    used = set()
    ctext = " ".join(rec["clause"])
    notes = []
    for i, l in enumerate(layers):
        cx = 150 + (i % 4) * 200
        parts.append('<circle cx="%.1f" cy="%.1f" r="30" fill="#FFFFFF" stroke="#1B1B1B" stroke-width="2.4"/>'
                     % (cx, tops[i]))
        parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" fill="#1B1B1B">%d</text>'
                     % (cx, tops[i] + 11, TXT, i + 1))
        notes.append((i + 1, "%g mm" % l["t"], note_for(l, ctext, used)))

    # the key beneath the section
    body = []
    ky = total + 150
    for n, thick, note in notes:
        parts.append('<circle cx="18" cy="%.1f" r="26" fill="#FFFFFF" stroke="#1B1B1B" stroke-width="2.2"/>'
                     % (ky - 8))
        parts.append('<text x="18" y="%.1f" text-anchor="middle" font-size="%g" fill="#1B1B1B">%d</text>'
                     % (ky + 2, TXT_S, n))
        parts.append('<text x="60" y="%.1f" font-size="%g" font-weight="600" fill="#1B1B1B">%s</text>'
                     % (ky + 2, TXT_S, esc(thick)))
        body.append((170, ky, note))
        ky += max(116, (len(note) // 46 + 1) * TXT_S * 1.34 + 34)
    return parts, body, total, W, (-230, -140, W + 170, ky + 60)


# An indicative pitch. It is never dimensioned and never stated as a specified pitch, because the
# library does not give one: a typical section is drawn at a plausible slope so the construction
# reads as a roof, and the pitch for a job comes off the drawings. Same convention as the
# reference details — they show the slope and dimension nothing about it.
PITCH  = 30.0
TILE   = 12.0        # tile thickness, drawn
BATTEN = 38.0        # 25 x 38 battens laid flat on the underlay
GAUGE  = 325.0       # batten gauge along the slope, indicative

# The covering, in the order it is worth quoting. A tile or a slate IS the covering; an underlay
# sits directly under it and names it by implication. Battens and sarking are deliberately absent:
# a clause says "continuous sarking layer" about a board of insulation and "counter-battens" about
# deepening an existing rafter, and matching on those put the insulation sentence against the tiles
# on three of the fourteen pitched roofs.
COVERING = [re.compile(r"\btiles?\b|\bslates?\b|roof covering", re.I),
            re.compile(r"\bunderlay\b|\bfelt\b", re.I)]
CONDITIONAL = re.compile(r"^(where|when|unless|if|although)\b", re.I)


def is_pitched(rec):
    """A roof drawn on the slope rather than as flat bands.

    Flat roofs and warm decks stay flat — they are flat. Everything else in the RF group that
    talks about a pitch, rafters or trusses is a sloping roof and was being drawn as a horizontal
    sandwich, which is why none of them read as roofs.
    """
    if rec["group"] != "RF":
        return False
    t = rec["title"].lower()
    if "flat roof" in t or "warm deck" in t:
        return False
    # Insulation at ceiling level is a horizontal build-up under a pitched roof, not a build-up
    # on the slope. Drawn on the slope it read as 400mm of quilt following the rafters, which is
    # not where any of it goes: the quilt lies on the ceiling ties with a cold void above it.
    if "ceiling level" in t:
        return False
    return any(w in t for w in ("pitched", "rafter", "trussed", "eaves"))


def covering_sentence(clause):
    """The sentence naming the roof covering, or None.

    The covering is drawn ONLY where the clause names one — the same rule that governs wall ties.
    Six of the twenty-five roof clauses specify the build-up from the rafters inwards and say
    nothing about tiles; those get no tiles, because a drawing may not state what the
    specification does not.
    """
    for pat in COVERING:
        for s in sentences(clause):
            m = pat.search(s)
            if not m:
                continue
            # A conditional says what to do IF something else happens - "where the roof covering
            # is renewed at the same time" - and quoting it without its condition states a
            # covering the specification has not specified. The build-up sentences are also
            # conditional ("where the rafters are exposed internally, insulate over and
            # between:") but they carry a colon and the build-up follows it.
            if CONDITIONAL.match(s) and ":" not in s:
                continue
            # the fragment from where the covering is named, not the whole sentence: the covering
            # is usually named inside the sentence that describes the build-up, and quoting all of
            # it puts the same words against the tiles as against the first layer.
            frag = s[max(0, s.rfind(",", 0, m.start()) + 1):].strip()
            cut = frag.find(", ", 70)
            if cut > 0:
                frag = frag[:cut]
            frag = re.sub(r"^(?:and|with|on)\s+", "", frag.strip(), flags=re.I).rstrip(",;")
            # The covering has to be the subject of what is quoted. Where the word turns up
            # further in - carried through to the roof covering, ventilate unless the underlay is
            # breathable - the clause is talking about something else and the roof gets no tiles.
            if not frag or (pat.search(frag) or m).start() > 25:
                continue
            return frag[0].upper() + frag[1:] + "."
    return None


def pitched_svg(rec, sents):
    """A pitched roof, drawn on the slope with its covering.

    Local coordinates run along the slope in x and through the thickness in y, with y=0 the
    OUTSIDE face — which is why face_order() in detail_schedule.py had to come first. The whole
    section is then rotated; the callouts are placed at the rotated points so their text stays
    upright, and the key sits beneath, unrotated, as it does for a flat build-up.
    """
    import math
    layers = rec["layers"]
    total = sum(float(l["t"]) for l in layers)
    RUN = 1350.0
    a = math.radians(PITCH)
    ca, sa = math.cos(a), math.sin(a)

    def R(x, y):                       # matches transform="rotate(-PITCH)"
        return (x * ca + y * sa, -x * sa + y * ca)

    cover = covering_sentence(rec["clause"])
    top = -(BATTEN + TILE) if cover else 0.0
    parts, g = [DEFS], []

    pos, mids = 0.0, []
    for i, l in enumerate(layers):
        t = float(l["t"])
        mat = l["hatch"] or "void"
        g.append('<rect x="0" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#1B1B1B" '
                 'stroke-width="2.6"/>' % (pos, RUN, t, layer_fill(parts, i, mat, t, True)))
        mids.append(pos + t / 2)
        pos += t

    if cover:
        # underlay on the rafters, battens on the underlay, tiles on the battens — the order a
        # roof is built in, and the order the clause states it.
        g.append('<path d="M0 0 H%.1f" stroke="#8A5A52" stroke-width="4.5"/>' % RUN)
        x = 30.0
        while x < RUN - 40:
            g.append('<rect x="%.1f" y="%.1f" width="25" height="%.1f" fill="url(#p-timber)" '
                     'stroke="#1B1B1B" stroke-width="2"/>' % (x, -BATTEN, BATTEN))
            x += GAUGE
        g.append('<rect x="-70" y="%.1f" width="%.1f" height="%.1f" fill="#D9D3CB" '
                 'stroke="#1B1B1B" stroke-width="2.4"/>' % (top, RUN + 70, TILE))
        x = -70 + GAUGE                       # the tail of each course, so it reads as tiles
        while x < RUN:
            g.append('<path d="M%.1f %.1f v%.1f" stroke="#1B1B1B" stroke-width="2.2"/>'
                     % (x, top, TILE))
            x += GAUGE

    # break line across the whole section at the lower end
    zig = ["M%.1f %.1f" % (-34, top)]
    y = top
    while y < total:
        zig.append("l 26 %.1f l -26 %.1f" % (min(34, total - y) / 2, min(34, total - y) / 2))
        y += 34
    g.append('<path d="%s" fill="none" stroke="#1B1B1B" stroke-width="2.4"/>' % " ".join(zig))

    parts.append('<g transform="rotate(%.3f)">%s</g>' % (-PITCH, "".join(g)))

    # thickness dimension, square to the slope at the upper end
    p0, p1 = R(RUN + 60, top), R(RUN + 60, total)
    parts.append('<path d="M%.1f %.1f L%.1f %.1f" stroke="#1B1B1B" stroke-width="1.8"/>'
                 % (p0[0], p0[1], p1[0], p1[1]))
    mid = R(RUN + 110, (top + total) / 2)
    parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" fill="#1B1B1B" '
                 'transform="rotate(%.3f %.1f %.1f)">%g</text>'
                 % (mid[0], mid[1], TXT, -PITCH, mid[0], mid[1], round(total - top, 1)))

    # numbered callouts at the rotated layer midpoints, staggered along the slope
    used = set()
    ctext = " ".join(rec["clause"])
    notes = []
    items = list(layers) + ([None] if cover else [])
    for i, l in enumerate(items):
        cx = 190 + (i % 4) * 270
        cy = (top + TILE / 2) if l is None else mids[i]
        px, py = R(cx, cy)
        parts.append('<circle cx="%.1f" cy="%.1f" r="30" fill="#FFFFFF" stroke="#1B1B1B" '
                     'stroke-width="2.4"/>' % (px, py))
        parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" '
                     'fill="#1B1B1B">%d</text>' % (px, py + 11, TXT, i + 1))
        notes.append((i + 1, "covering" if l is None else "%g mm" % l["t"],
                      cover if l is None else note_for(l, ctext, used)))

    xs, ys = [], []
    for cx, cy in ((0, top), (RUN + 170, top), (0, total), (RUN + 170, total)):
        px, py = R(cx, cy)
        xs.append(px); ys.append(py)
    x0, x1, y0, y1 = min(xs) - 90, max(xs) + 60, min(ys) - 70, max(ys) + 60

    body = []
    ky = y1 + 120
    for n, thick, note in notes:
        parts.append('<circle cx="%.1f" cy="%.1f" r="26" fill="#FFFFFF" stroke="#1B1B1B" '
                     'stroke-width="2.2"/>' % (x0 + 40, ky - 8))
        parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" '
                     'fill="#1B1B1B">%d</text>' % (x0 + 40, ky + 2, TXT_S, n))
        parts.append('<text x="%.1f" y="%.1f" font-size="%g" font-weight="600" '
                     'fill="#1B1B1B">%s</text>' % (x0 + 82, ky + 2, TXT_S, esc(thick)))
        body.append((x0 + 200, ky, note))
        ky += max(116, (len(note) // 46 + 1) * TXT_S * 1.34 + 34)
    return parts, body, total, RUN, (x0, y0, x1 - x0, ky - y0 + 60)


SHEET = """<!doctype html><html lang="en-GB"><head><meta charset="utf-8">
<title>%(ref)s %(title)s</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
@page { size: A4 portrait; margin: 0; }
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{width:210mm;height:297mm;font-family:"IBM Plex Sans",Arial,sans-serif;color:#1B1B1B;
  font-size:8.2pt;line-height:1.42;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.sheet{width:210mm;height:297mm;padding:12mm 12mm 8mm;display:flex;flex-direction:column}
header{display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:1.1pt solid #1B1B1B;padding-bottom:2.6mm}
/* The long titles run to two lines. Without a track of its own the heading grows past the
   scale label and prints over it, which is how RF2 in the flat set was reading. */
header h1{margin:0;flex:1;min-width:0;padding-right:8mm;
  font-size:12.5pt;font-weight:600;letter-spacing:-0.01em;text-transform:uppercase}
header .sc{flex:none;white-space:nowrap;font-family:"IBM Plex Sans Condensed",Arial,sans-serif;
  font-size:7.6pt;font-weight:600;
  letter-spacing:.1em;text-transform:uppercase;color:#6A6A66}
main{flex:1;display:grid;grid-template-columns:104mm 1fr;gap:6mm;padding-top:5mm;min-height:0;overflow:hidden}
.dwg{overflow:hidden}
.dwg svg{width:100%%;height:auto;display:block}
.notes{border-left:.5pt solid #C9C7C1;padding-left:6mm;overflow:hidden}
.perf{border:.8pt solid #1B1B1B;padding:2.6mm 3mm;margin-bottom:4mm}
.perf h2{margin:0 0 1.8mm;font-family:"IBM Plex Sans Condensed",Arial,sans-serif;font-size:7.4pt;
  font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#6A6A66}
.perf .row{display:flex;justify-content:space-between;align-items:baseline;
  border-top:.4pt solid #DDDBD5;padding:1.4mm 0}
.perf .row:first-of-type{border-top:0}
.perf .v{font-family:"IBM Plex Mono",monospace;font-size:12pt;font-weight:500}
.perf .u{font-family:"IBM Plex Sans Condensed",Arial,sans-serif;font-size:6.8pt;letter-spacing:.08em;
  text-transform:uppercase;color:#6A6A66;padding-top:.8mm}
.notes h3{margin:0 0 2mm;font-size:8.6pt;font-weight:600}
/* a long clause is set smaller rather than being quietly cut off at the footer */
.notes.d1{font-size:7.5pt;line-height:1.38}
.notes.d2{font-size:6.9pt;line-height:1.34}
.notes.d3{font-size:6.3pt;line-height:1.3}
.notes p{margin:0 0 2.4mm;text-align:justify;hyphens:auto}
.flag{margin-top:3mm;border-left:2pt solid #8A6108;background:#FBF4E2;padding:2mm 2.6mm;font-size:7.6pt}
.scalenote{font-family:"IBM Plex Sans Condensed",Arial,sans-serif;font-size:7pt;font-weight:600;
  letter-spacing:.09em;text-transform:uppercase;color:#6A6A66;padding:3mm 0 2mm}
footer{border-top:1.1pt solid #1B1B1B;padding-top:2.4mm;display:grid;
  grid-template-columns:1fr 1fr 1fr 1fr 44mm;gap:3mm}
footer .cell{border-right:.4pt solid #DDDBD5;padding-right:3mm}
footer .cell:nth-child(4){border-right:0}
footer dt{font-family:"IBM Plex Sans Condensed",Arial,sans-serif;font-size:6.4pt;font-weight:600;
  letter-spacing:.1em;text-transform:uppercase;color:#6A6A66;margin:0 0 .6mm}
footer dd{margin:0 0 1.8mm;font-size:7.6pt}
footer .practice{font-size:6.9pt;color:#4A4A46;line-height:1.35}
footer .practice b{display:block;font-size:8pt;color:#1B1B1B;margin-bottom:.4mm}
footer .practice .addr{display:block;font-size:6.4pt;color:#6A6A66;margin-bottom:1.2mm}
svg text{font-family:"IBM Plex Sans",Arial,sans-serif}
</style></head><body><div class="sheet">
<header><h1>%(ref)s &mdash; %(title)s</h1><span class="sc">%(section)s &middot; 1:10 @ A4</span></header>
<main>
  <div class="dwg">%(svg)s</div>
  <div class="notes %(dense)s">
    <div class="perf">
      <h2>Thermal performance</h2>
      %(perf)s
      <div class="u">%(perfnote)s</div>
    </div>
    <h3>Specification</h3>
    %(spec)s
    %(flag)s
  </div>
</main>
<p class="scalenote">Dimensions in millimetres. Do not scale from this drawing.</p>
<footer>
  <div class="cell"><dt>Project</dt><dd>[Project name and address]</dd>
    <dt>Drawing No</dt><dd>[XX-XXX]-%(ref)s</dd></div>
  <div class="cell"><dt>Drawing title</dt><dd>%(ref)s %(title_lc)s &mdash; %(section_lc)s</dd>
    <dt>Scale</dt><dd>1:10 @ A4</dd></div>
  <div class="cell"><dt>Client</dt><dd>[Client]</dd>
    <dt>Date / drawn</dt><dd>%(date)s / %(initials)s</dd></div>
  <div class="cell"><dt>Status</dt><dd>For building control approval</dd>
    <dt>Rev</dt><dd>P01</dd></div>
  <div class="practice"><b>%(pname)s</b><span class="addr">%(paddr)s</span>%(resp)s</div>
</footer>
</div></body></html>"""


def build_sheet(rec, type_name):
    sents = sentences(rec["clause"])
    horiz = rec["group"] in HORIZONTAL
    draw = wall_svg if horiz else (pitched_svg if is_pitched(rec) else floor_svg)
    parts, body, total, other, vb = draw(rec, sents)

    wrap = 30 if horiz else 46          # the key beneath a flat section has the full width

    def fold(note):
        words, line, lines = note.split(), "", []
        for w in words:
            if len(line) + len(w) > wrap:
                lines.append(line); line = w
            else:
                line = (line + " " + w).strip()
        lines.append(line)
        return lines

    for lx, ly, note in body:
        # Six lines is what fits between one leader and the next. A note longer than that used
        # to lose its tail without saying so, and a leader reading "continuous vapour control
        # layer on the" is a drawing that states half a clause. Trim to whole words and mark it:
        # the specification column on this sheet carries the sentence in full.
        lines = fold(note)
        if len(lines) > 6:
            words = note.split()
            while len(words) > 1 and len(fold(" ".join(words) + " …")) > 6:
                words.pop()
            lines = fold(" ".join(words) + " …")
        for j, ln in enumerate(lines[:6]):
            parts.append('<text x="%.1f" y="%.1f" font-size="%g" fill="#1B1B1B">%s</text>'
                         % (lx, ly + j * (TXT_S * 1.32) - 6, TXT_S, esc(ln)))

    # Pad the viewBox to the shape of the column it sits in, centring the content, so the
    # section fills the sheet instead of sitting in the top corner with the page half empty.
    x0, y0, w, h = vb
    target = 104.0 / 205.0                      # the drawing column, width over height
    if w / h > target:
        # extra height goes below, so a flat build-up sits at the top of the column and reads
        # as a drawing of that size rather than as something floating in the middle of a page
        h = w / target
    else:
        nw = h * target; x0 -= (nw - w) / 2; w = nw
    svg = ('<svg viewBox="%.0f %.0f %.0f %.0f" xmlns="http://www.w3.org/2000/svg">%s</svg>'
           % (x0, y0, w, h, "".join(parts)))

    tgt, got = rec.get("u_target"), rec.get("u_achieved")
    perf = ""
    if tgt:
        perf += '<div class="row"><span>Maximum permitted</span><span class="v">%s</span></div>' % esc(tgt)
    if got:
        perf += '<div class="row"><span>Achieved</span><span class="v">%s</span></div>' % esc(got)
    if not perf:
        perf = '<div class="row"><span>Standard</span><span class="v">%s</span></div>' % esc(rec.get("standard") or "—")
    perfnote = ("W/m&sup2;K &middot; calculated to BS EN ISO 6946" if (tgt or got)
                else "As the specification")

    flag = ""
    if rec.get("verified_table"):
        flag = ('<div class="flag"><b>Layer table:</b> use buildup-layer-schedule.md section %s. '
                'It is hand-checked against the clause and the U-value calculation; the layers '
                'drawn here are read from the clause and a clause does not always state every '
                'thickness.</div>' % esc(rec["verified_table"]))

    section = "Typical vertical section" if horiz else "Typical section"
    if horiz and stud_zone(rec):
        # studs march along the wall, so the view that shows them is a plan
        section = "Typical plan section"
    # How much room the specification needs, not just how many characters it has. Each
    # paragraph costs a blank line, and the layer-table flag costs a box; the longest clause in
    # the library is only 2149 characters, so a threshold set on characters alone never fired
    # and the last line was quietly cut off at the footer.
    cost = (sum(len(p) for p in rec["clause"])
            + 90 * len(rec["clause"])
            + (260 if rec.get("verified_table") else 0))
    dense = "d3" if cost > 2800 else "d2" if cost > 2200 else "d1" if cost > 1500 else ""
    pr = PRACTICE_
    return SHEET % {
        "dense": dense,
        "pname": esc(pr["name"]),
        "paddr": esc(" · ".join(x for x in (pr["addr"], pr["email"]) if x)),
        "resp": esc(pr["resp"]),
        "date": esc(pr["date"]), "initials": esc(pr["initials"]),
        "ref": esc(rec["ref"]), "title": esc(rec["title"]), "title_lc": esc(rec["title"].lower()),
        "section": esc(section.upper()), "section_lc": esc(section.lower()),
        "svg": svg, "perf": perf, "perfnote": perfnote, "flag": flag,
        "spec": "".join("<p>%s</p>" % esc(p) for p in rec["clause"]),
    }


def main():
    global PRACTICE_
    src = None
    if "--practice" in sys.argv:
        i = sys.argv.index("--practice")
        if i + 1 < len(sys.argv):
            src = sys.argv[i + 1]
    PRACTICE_ = practice(src)
    print("  practice on the title block: %s%s   (from %s)"
          % (PRACTICE_["name"], " / " + PRACTICE_["designer"] if PRACTICE_["designer"] else "",
             PRACTICE_["source"]))
    if PRACTICE_["source"] == "placeholders":
        print("  no practice profile found - the title block will print [Practice name] for the")
        print("  practice to fill in. Pass --practice <file.json>, or see practice.example.json.")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if src in args:
        args.remove(src)
    html_only = "--html" in sys.argv
    data = json.load(open(SRC, encoding="utf-8"))

    jobs = []
    for key, t in data["types"].items():
        if args and key != args[0]:
            continue
        seen = {}
        for rec in t["buildups"]:
            seen[rec["group"]] = seen.get(rec["group"], 0) + 1
            rec["ref"] = "%s%d" % (rec["group"], seen[rec["group"]])
            if len(args) > 1 and rec["group"] != args[1].upper():
                continue
            if not rec["layers"] or rec["group"] not in HORIZONTAL | VERTICAL:
                continue
            d = os.path.join(OUT, key)
            os.makedirs(d, exist_ok=True)
            base = os.path.join(d, "%s_%s" % (rec["ref"], re.sub(r"[^A-Za-z0-9]+", "_", rec["title"])[:52].strip("_")))
            open(base + ".html", "w", encoding="utf-8").write(build_sheet(rec, t["name"]))
            jobs.append(base)

    print("  %d sheets written" % len(jobs))

    # A build-up that stops drawing leaves its last sheet behind, and that sheet is wrong — the
    # external wall insulation one still showed the phantom 150mm band read out of "150mm above
    # finished ground level", and the basement party wall showed one of two conditional options
    # as though it were the specification. Both sat in the issue folder for a day. Only a full
    # run may clear them: a filtered run knows nothing about the sheets it did not ask for.
    if not args:
        wanted = {j + ".pdf" for j in jobs} | {j + ".html" for j in jobs}
        orphans = [p for p in glob.glob(os.path.join(OUT, "*", "*.*")) if p not in wanted]
        for p in orphans:
            os.remove(p)
        if orphans:
            print("  %d sheet(s) removed for build-ups that no longer draw:" % len(orphans))
            for p in sorted({os.path.basename(p).rsplit(".", 1)[0] for p in orphans}):
                print("      %s" % p)

    if html_only or not jobs:
        return
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright is needed for the PDFs:  python -m pip install playwright")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for i, base in enumerate(jobs, 1):
            pg.goto("file:///" + base.replace("\\", "/") + ".html")
            pg.wait_for_timeout(220)
            pg.pdf(path=base + ".pdf", format="A4", print_background=True,
                   margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            if i % 20 == 0:
                print("    %d/%d" % (i, len(jobs)))
        b.close()
    print("  %d PDFs written to output/sheets/" % len(jobs))


if __name__ == "__main__":
    main()
