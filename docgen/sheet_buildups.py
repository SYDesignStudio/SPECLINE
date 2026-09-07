#!/usr/bin/env python3
"""Build-up sheets: one A4 drawing per build-up, laid out to be issued.

    python docgen/sheet_buildups.py                 every build-up
    python docgen/sheet_buildups.py extension       one project type
    python docgen/sheet_buildups.py extension EW    one type, one reference group
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
import json, os, re, sys

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


def practice():
    """The practice whose name goes on the sheet, from docgen/brand.py.

    One source, shared with the Word and PDF specification generator, so a sheet and a
    specification issued on the same day cannot disagree about who drew them. Specline's own
    name never appears here: the commercial rule is that a generated document carries the
    subscribing practice's identity and nothing else.

    Project, client and the job number stay as placeholders on purpose. They belong to a job,
    and these are library details — filling them in would be inventing a job that does not
    exist.
    """
    try:
        sys.path.insert(0, os.path.join(ROOT, "docgen"))
        from brand import PRACTICE
        p = dict(PRACTICE)
    except Exception:
        p = {}
    p.setdefault("name", "[Practice name]")
    for k in ("designer", "addr", "email", "web"):
        p.setdefault(k, "")
    parts = [w for w in re.split(r"[\s-]+", p["designer"]) if w]
    p["initials"] = "".join(w[0] for w in parts[:3]).upper() or "[XX]"
    p["date"] = __import__("datetime").date.today().strftime("%m.%y")
    who = ("%s of %s" % (p["designer"], p["name"])) if p["designer"] else p["name"]
    p["resp"] = ("All dimensions to be checked on site. Read in conjunction with the structural "
                 "engineer's drawings and the insulation manufacturer's current certificate. "
                 "%s is the named designer and remains responsible for the suitability of this "
                 "detail; compliance of the work is determined by the building control body."
                 % who)
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
            window = clause_text[i:i + 230]
            cut = window.find(". ")
            if cut < 30:                       # no sentence end nearby: stop at a comma instead
                c = [window.find(", ", 60), window.find("; ", 60)]
                c = [x for x in c if x > 0]
                cut = min(c) if c else -1
            frag = (window[:cut + 1] if cut > 0 else window).strip().rstrip(",;")
    if not frag or frag[:26].lower() in used:
        frag = "%g mm %s" % (layer["t"], layer["material"].rstrip(" of").rstrip())
    used.add(frag[:26].lower())
    frag = frag[0].upper() + frag[1:]
    return frag if frag.endswith(".") else frag + "."


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
        "ins": "#F2E3BE", "wool": "url(#p-wool)", "timber": "url(#p-timber)",
        "conc": "url(#p-conc)", "lean": "url(#p-lean)", "screed": "url(#p-screed)",
        "hard": "url(#p-hard)", "earth": "url(#p-earth)", "pboard": "#E8E7E3",
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


def wall_svg(rec, sents):
    layers = rec["layers"]
    total = sum(l["t"] for l in layers)
    ties = tie_spec(rec["clause"])
    H_ = WALL_H
    parts = [DEFS]

    # the layers
    pos = 0.0
    for l in layers:
        t = float(l["t"])
        mat = l["hatch"] or "void"
        parts.append('<rect x="%.1f" y="0" width="%.1f" height="%.1f" fill="%s" stroke="#1B1B1B" stroke-width="2.6"/>'
                     % (pos, t, H_, FILL.get(mat, "#FFF")))
        if mat in COURSE:
            parts += courses(pos, 0, pos + t, H_, COURSE[mat], False)
        pos += t

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

    # overall dimension across the top
    dy = -96
    parts.append('<path d="M0 %.1f h%.1f" stroke="#1B1B1B" stroke-width="1.8"/>' % (dy, total))
    for x in (0, total):
        parts.append('<path d="M%.1f %.1f v%.1f" stroke="#1B1B1B" stroke-width="1.8"/>' % (x, dy - 20, 40))
    parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="%g" fill="#1B1B1B">%g</text>'
                 % (total / 2, dy - 26, TXT, total))

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
    notes = [(l, note_for(l, ctext, used)) for l in layers]
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
    for l in layers:                      # first layer at the bottom, as the clause reads
        t = float(l["t"])
        y = total - pos - t
        mat = l["hatch"] or "void"
        parts.append('<rect x="0" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#1B1B1B" stroke-width="2.6"/>'
                     % (y, W, t, FILL.get(mat, "#FFF")))
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
        ky += 116
    return parts, body, total, W, (-230, -140, W + 170, ky + 60)


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
header h1{margin:0;font-size:12.5pt;font-weight:600;letter-spacing:-0.01em;text-transform:uppercase}
header .sc{font-family:"IBM Plex Sans Condensed",Arial,sans-serif;font-size:7.6pt;font-weight:600;
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
    parts, body, total, other, vb = (wall_svg if horiz else floor_svg)(rec, sents)

    wrap = 30 if horiz else 46          # the key beneath a flat section has the full width
    for lx, ly, note in body:
        words, line, lines = note.split(), "", []
        for w in words:
            if len(line) + len(w) > wrap:
                lines.append(line); line = w
            else:
                line = (line + " " + w).strip()
        lines.append(line)
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
    PRACTICE_ = practice()
    print("  practice on the title block: %s%s"
          % (PRACTICE_["name"], " / " + PRACTICE_["designer"] if PRACTICE_["designer"] else ""))
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
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
