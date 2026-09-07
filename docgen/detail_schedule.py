#!/usr/bin/env python3
"""Detail schedule — the layer data behind every build-up, for drawing details.

    python docgen/detail_schedule.py

Writes three files into reference/details/:

    build-up-schedule.md    every build-up in the library, layer by layer, with the clause
    build-up-schedule.json  the same, machine-readable, for generating DXF or PDF
    detail-register.md      the junctions worth drawing, and which are drawn

WHY THIS IS GENERATED AND NOT WRITTEN. data/ is the single source of truth. A schedule typed
out by hand drifts from the library the first time a clause changes, and a detail drawn from a
drifted schedule is worse than no detail at all. Re-run this whenever data/ changes.

WHAT IT CAN AND CANNOT PROMISE. The library states its layers in prose — "a 103mm facing brick
outer leaf, a 100mm cavity fully filled with 90mm Kingspan Kooltherm K106" — so the thicknesses
here are EXTRACTED, not stored. That is reliable enough to set a drawing out with and not
reliable enough to submit unchecked, so every build-up carries the sentence the layers came from
and every layer carries the phrase it was read from. Check the layers against the clause before
drawing. Where the extractor is unsure it says so rather than guessing: the whole point of this
repository is that a figure nobody verified never reaches a building control document.
"""
import io, json, os, re, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist", "specdata.js")
OUT  = os.path.join(ROOT, "reference", "details")

GROUPS = {"FD": "Foundations", "SW": "Separating walls", "SF": "Separating floors",
          "EW": "External walls", "IW": "Internal walls", "GF": "Ground floors",
          "IF": "Floors", "RF": "Roofs", "BW": "Basement walls", "BF": "Basement floors"}
GORDER = ["FD", "SW", "SF", "EW", "IW", "GF", "IF", "RF", "BW", "BF"]

# Three build-ups have a hand-verified layer table in buildup-layer-schedule.md, checked layer
# by layer against the clause and the U-value calculation. Where one exists it is the authority:
# the extractor can only report what the clause states, and a clause does not always state
# everything. The cavity wall is the example — it says "12.5mm plasterboard on dabs" and never
# gives the dabs a thickness, so the extracted total is 10 short of the verified 325.5.
VERIFIED = {
    ("extension", "Full Fill Cavity Wall"): "EW1",
    ("extension", "Solid Floor — Insulation Over Slab (Screed Finish)"): "GF1",
    ("extension", "Warm Deck Flat Roof"): "RF1",
}

TYPE_NAMES = {"extension": "House Extension", "loft": "Loft Conversion",
              "flat": "Flat Conversion", "garage": "Garage Conversion",
              "newbuild": "New Build", "nbflats": "New Build Flats",
              "basement": "Basement Conversion", "garagebld": "Garage Build"}

# A number followed by one of these is a SPACING, a LEVEL, a LAP or a clearance — never the
# thickness of a layer — and the veto is UNCONDITIONAL.
#
# It used to be cancelled whenever hatch_for() recognised any word later in the phrase. That was
# wrong, because hatch_for() answers "what would I draw this with", not "is this a material", and
# its patterns match single common nouns that turn up in ordinary prose: "at 450mm vertical
# centres and at every stud horizontally" matched *stud* and became 450mm of timber; "an air-gap
# correction of 0.01" matched *gap*; "600mm below finished ground level" matched *ground*.
# On 7 September 2026 that had put an invented band into 45% of the drawn build-ups — EW5 timber
# frame was drawn 764.5mm thick against a real 314.5mm, with the phantom inboard of the
# plasterboard. If a phrase reads like a dimension of position rather than of substance, no word
# anywhere else in it may rescue the number.
NEVER_A_LAYER = re.compile(
    r"^(?:[a-z]+\s+)?centres?\b"                       # "centres", "rafter centres", "joist centres"
    r"|^(?:vertical|horizontal|apart|intervals?|upstands?|above|below|beyond|into|onto|"
    r"studs? at|either side|each side|in every|at\s|from\b|of the\b|"
    r"overlap|laps?|bearing|cover|diameter|gauge|square|wide|deep|long|high|"
    r"and over\b|and in no case|is to be used|for both|to a minimum|where necessary|"
    r"openings along|over \d|gap at|gap along|gap on|and free of|so that|stud height)", re.I)

# These may legitimately precede a material — "150mm minimum well-compacted hardcore" is a layer,
# and so is "50mm clear ventilated and drained cavity". They veto only when nothing follows that
# can be identified as a material, which is the test the old single list was trying to make.
QUALIFIER = re.compile(r"^(minimum|maximum|min|max|clear|not less than|thick at)\b", re.I)

# Working, not construction: "100mm over the rafters calculates at 0.15 W/m²K" is a sentence about
# the U-value that happens to contain a thickness. Never a layer.
ARITHMETIC = re.compile(r"calculates|correction of|\bachieves\b", re.I)

# "47mm x 150mm C24 rafters" and "140mm x 38mm C16 studs" — the library writes the pair in both
# orders, so neither position can be trusted. A section cuts the member's DEPTH, which is always
# the larger of the two: 47 x 150 rafters are a 150 zone, 140 x 38 studs a 140 zone. Reading the
# first number gave a 38mm timber frame wall, the second a 47mm rafter zone.
MEMBER = re.compile(r"^x\s*(\d+(?:\.\d+)?)\s*mm\s+(.+)$", re.I)

# That zone is the same thickness of construction the insulation between the members fills, so the
# two are one band and not two: drawing both counted a single 150mm rafter zone as 300mm and a
# 220mm joist zone as 420mm. A partial fill still leaves the zone at the member's depth.
FILLS_THE_ZONE = re.compile(
    r"between (?:and under )?(?:the )?(?:joists|rafters|studs)|fitted tightly between|"
    r"fully filling|full (?:stud|rafter|joist) depth", re.I)

# material phrase -> the hatch to draw it with. Names match the patterns in the detail sheets.
HATCH = [
    (r"facing brick|brick outer|brickwork outer|facing brickwork|brick-on-edge|engineering brick|"
     r"solid brick|brick wall|brickwork", "brick"),
    (r"aircrete|thermalite|celcon|blockwork inner|block inner|aerated block", "block"),
    (r"dense concrete block|dense block|concrete block|block wall|blockwork|\bblock\b", "dense"),
    (r"mineral wool|rockwool|dritherm|knauf|glass wool|quilt|cavity barrier|acoustic (?:roll|quilt)", "wool"),
    (r"kooltherm|celotex|sopratherm|xtratherm|unilin|ecotherm|thermaroof|thermafloor|thermawall|"
     r"pir\b|phenolic|rigid (?:urethane )?insulation|insulation board|insulated plasterboard|"
     r"polystyrene|eps\b|xps\b|foam board|k1\d\d|t[rf]\d\d|cw4000|ga4000|xt/|upstand|insulation", "ins"),
    # Steel before timber: the timber rule matches "stud", so a galvanised steel C-stud was being
    # drawn with a wood grain. A metal stud partition is a different thing to build and to fire
    # stop, and the drawing should say so.
    (r"metal (?:c[- ])?studs?|steel c-?studs?|light gauge steel|metal furring|steel frame|"
     r"galvanised steel|metal channels?|resilient bar", "metal"),
    (r"joist|rafter|stud|batten|counter-batten|timber|softwood|plywood|osb|sole plate|wall plate|"
     r"noggin|firring|deck|fascia|soffit|chipboard|t&g|tongued and grooved|plank flooring|"
     r"flooring grade|floorboard", "timber"),
    (r"screed", "screed"),
    (r"hardcore|sub-base|compacted fill", "hard"),
    (r"lean mix|lean-mix", "lean"),
    (r"concrete|slab|raft|beam and block", "conc"),
    (r"plasterboard|gypsum board|fireline|wallboard|plaster|skim|dab|lining board|render", "pboard"),
    (r"subsoil|ground|earth|topsoil", "earth"),
    (r"sand blinding|blinding|\bsand\b", "screed"),
    (r"membrane|dpm|dpc|vapour control|vcl|breather|underlay|radon", "membrane"),
    (r"cavity|\bgap\b|void|air space|ventilated", "void"),
]


def hatch_for(phrase):
    p = phrase.lower()
    for pat, name in HATCH:
        if re.search(pat, p):
            return name
    return None


def load():
    js = ('const fs=require("fs");const s=fs.readFileSync(%r,"utf8");'
          'process.stdout.write(JSON.stringify(new Function(s+";return SPECS;")()))'
          % DIST.replace("\\", "/"))
    return json.loads(subprocess.check_output(["node", "-e", js]).decode("utf-8"))


# A thickness named INSIDE another match's window. See _rescue().
# The lookbehind matters. The rescue pass searches a window that can begin part-way through a
# figure, so without it "12.5mm plasterboard each side" was read a second time as "5mm
# plasterboard each side" and a basement partition grew a 5mm board that no clause mentions.
INNER = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*mm\s+([A-Za-z][^,;.()—]{2,60})")

# "Masonry partitions of 100mm blockwork may be used where the slab is designed for them" offers
# another way of building the wall, not another layer of this one.
ANOTHER_WAY = re.compile(r"may be used|may be substituted|as an alternative|"
                         r"achieves? the same", re.I)

# The insulation that fills a stud, rafter or joist zone is that zone, not a band beside it —
# even when it is thinner than the member, which a partial fill usually is. The tell has to be
# the words immediately around the fill itself: a clause can say "the full stud depth insulated"
# about the studs and then name a separate lining board inboard of them, and merging that would
# swallow a real layer.
INFILLING = re.compile(r"(?:stud|rafter|joist)s?\s+depth\s+(?:filled|infilled|insulated)|"
                       r"filled with|infilled with|\binfill\b|between the (?:studs|joists|rafters)",
                       re.I)


def _consider(t, phrase, raw, after, layers, notes, before=""):
    """One <thickness, phrase> pair against every veto; appends a layer if it survives.

    Shared by the top-level scan and the rescue pass below, so the two cannot drift apart.
    """
    if NEVER_A_LAYER.match(phrase) or ARITHMETIC.search(phrase) or ANOTHER_WAY.search(phrase):
        notes.append("not a layer — %gmm reads as a spacing, a level, working or an alternative "
                     "construction: '%s'" % (t, phrase[:52]))
        return
    if QUALIFIER.match(phrase) and hatch_for(phrase) is None:
        return
    if t > 600:                      # no single layer in this library is thicker
        notes.append("skipped %gmm %s — too thick to be a layer" % (t, phrase[:40]))
        return
    if hatch_for(phrase) is None:
        # A layer with no identifiable material is prose the pattern happened to catch, not a
        # layer. Recorded rather than guessed, so `layers` stays safe to draw from.
        notes.append("not treated as a layer: '%s'" % phrase[:56])
        return
    # The label stops at the next thickness, which is a layer of its own and is about to be read
    # as one: "well-compacted hardcore blinded with 50mm sand" labels the hardcore, not the sand.
    cut = INNER.search(phrase)
    label = phrase[:cut.start()] if cut and cut.start() >= 3 else phrase
    label = TAIL.sub("", label.strip(" ,;")).strip(" ,;")
    if len(label) < 3:
        notes.append("not treated as a layer: '%s'" % phrase[:56])
        return
    # The hatch follows the LABEL, not the phrase it was cut from. Reading it from the whole
    # phrase drew "12.5mm plasterboard on a metal furring system with 100mm mineral wool in the
    # void" as mineral wool, a 50mm clear cavity as brickwork and 150mm of joists as insulation —
    # 20 layers across the set were drawn as the wrong material. Where the trimmed label names no
    # material, keep the fuller phrase so the two still agree with each other.
    h = hatch_for(label)
    if h is None:
        if QUALIFIER.match(phrase):
            # A qualifier-led phrase has to name its material in its own label. "25mm minimum
            # where the stud depth is shallower" reached a hatch only through the word *stud*
            # five words later — the same mistake the unconditional veto was written to stop.
            notes.append("not treated as a layer: '%s'" % phrase[:56])
            return
        label, h = phrase, hatch_for(phrase)
    layers.append({"t": int(t) if t == int(t) else t, "material": label[:70],
                   "hatch": h, "read_from": raw, "_after": after, "_before": before})


# The rescue pass is a salvage operation, not the primary reading, so it is deliberately meaner
# than the top-level scan. Three tells separate a swallowed layer from swallowed prose:
WORKING = re.compile(r"calculat|W/m|achiev|U-value", re.I)   # the whole sentence is arithmetic
# "...board or a 90mm lining", "215mm dense blockwork or two leaves of 100mm blockwork" — an "or"
# anywhere between the two figures makes the second a choice, not an extra band.
ALTERNATIVE = re.compile(r"\bor\b", re.I)
# Only the verb marks a sentence as arithmetic. W/mK appears in perfectly good layer phrases
# ("100mm aircrete inner leaf of 0.11 W/mK"), so it cannot be the test.
WORKING_SENTENCE = re.compile(r"calculat|achiev", re.I)
# A phrase that names a cavity and nothing else — the restatement of one already read.
BARE_CAVITY = re.compile(r"^(?:clear\s+|residual\s+|nominal\s+|minimum\s+){0,3}"
                         r"(?:residual\s+)?cavit(?:y|ies)\b(?:\s+\w+){0,3}$", re.I)
# The same test one level up, reading the words that come BEFORE the figure: "...to a solid wall,
# or 62.5mm to an uninsulated cavity wall" offers a choice of construction, not a second band.
OR_BEFORE = re.compile(r"\bor(?:\s+(?:an?|one|two|three|either))?"
                       r"(?:\s+(?:layers?|leaves|leaf|sheets?))?(?:\s+of)?\s*$", re.I)
CONNECTIVE = re.compile(r"^(or|and|with|by|in|on|so|of|at|to|from|as|is|are|both|leaves|remains|"
                        r"filling|between|above|below|over|under|that|which|where)\b", re.I)
# and the label is trimmed where the noun phrase stops, so "cavity at 0" cannot masquerade
# as a layer called "cavity".
TAIL = re.compile(r"\s+(?:in|at|of|on|so|which|where|leaves|remains|is|are|both|tied|by|and|or|"
                  r"with)\b.*$", re.I)


def _rescue(window, layers, notes, context="", outer=None, limit=None):
    """Thicknesses named inside another match's window.

    That window is greedy to 70 characters because the cavity split and the member rule both have
    to see two thicknesses in one phrase. The cost, until 7 September 2026, was that a second
    layer named close behind the first vanished inside it and was never read: "150mm minimum
    well-compacted hardcore blinded with 50mm sand" lost the sand blinding, and a cold-roof
    ceiling lost the 300mm quilt that is its entire insulation. About 25 real layers across 30
    build-ups. Whatever the caller has already consumed is passed in already removed, so nothing
    is counted twice.
    """
    if WORKING.search(window + " " + context):
        return          # the sentence is about the U-value, so every figure in it is working
    for im in INNER.finditer(window):
        # A match must START inside the caller's window; the window is allowed to run on a little
        # so a phrase clipped by the 70-character cut can finish. Without that, "...both faces of
        # 50mm minimum galvanised" lost the studs — the words naming them fell the wrong side of
        # the cut and what was left matched no material at all.
        if limit is not None and im.start() >= limit:
            break
        inner = re.sub(r"\s+", " ", im.group(2)).strip()
        t = float(im.group(1))
        # A member is only recognised at the top level, where the merge that stops a rafter zone
        # and its insulation being counted twice lives. Rescuing one from inside another phrase
        # has no such context, and the ones that turn up here are alternatives — "70mm metal C
        # studs or 89mm x 38mm treated timber studs" — or a member that is not a layer at all,
        # like a wall plate. Both would add a band that is not there.
        if MEMBER.match(inner):
            notes.append("not a layer — %gmm is a member named inside another phrase: '%s'"
                         % (t, inner[:52]))
            continue
        if ALTERNATIVE.search(window[:im.start()]) or CONNECTIVE.match(inner):
            notes.append("not a layer — %gmm is an alternative or a continuation: '%s'"
                         % (t, inner[:52]))
            continue
        if outer is not None and abs(t - outer) < 0.01:
            # The same figure restated — "115mm K106 in a 115mm cavity", "100mm K107 filling
            # existing 100mm rafters". One band, named twice.
            continue
        label = TAIL.sub("", inner).strip(" ,;")
        if len(label) < 3 or hatch_for(label) is None:
            notes.append("not treated as a layer: '%s'" % inner[:56])
            continue
        _consider(t, label, re.sub(r"\s+", " ", im.group(0))[:90],
                  re.sub(r"\s+", " ", window[im.end():im.end() + 90]), layers, notes)


# The ceiling finish of a roof is on the INSIDE. Clauses are written in whichever order reads
# best — "roof covering on battens over an underlay, on 47 x 150 rafters" runs outside in, while
# "12.5mm plasterboard, 100mm quilt between the joists" runs inside out — and the extractor keeps
# the clause's order, so four roofs came out with the ceiling as the outermost band. Nothing in
# the drawing said so, and a roof drawn inside-out is the same class of mistake as a wall with
# its plasterboard on the weather side. Reversing the list orders what the clause already states
# and invents nothing; it is recorded in extraction_notes so it can be checked.
INSIDE_FACE = ("pboard",)


MEMBER_WORD = re.compile(r"\brafters?|joists?|studs?\b", re.I)

# "line both faces with 12.5mm plasterboard" is two boards. The extractor reads the figure once,
# so every stud partition in the library was drawn with plasterboard on one side only — which is
# not a partition. The phrase has to sit in the same sentence as the board, or "damp proof courses
# in both leaves" would mirror a lining that is only ever on one face.
BOTH_FACES = re.compile(r"both faces|both sides|each side|each face|either side", re.I)
LINING = re.compile(r"plasterboard|lining board|wallboard", re.I)

# A partition whose studs the clause places but does not size. "proprietary galvanised steel
# C-studs at 600mm centres ... to the system manufacturer's specification" gives the centres and
# defers the depth, which is right — the depth belongs to the system, not to us. The drawing may
# not invent one, so the core is recorded WITHOUT a thickness and the sheet draws it as an
# undimensioned zone with the studs at the centres the clause does give. Left alone, the sheet
# was two sheets of plasterboard with nothing between them.
STUD_CENTRES = re.compile(r"\b(?:C-?)?studs?\b[^.]{0,60}?\bat\s+(\d{3,4})\s*mm\s+centres", re.I)
METAL_STUD = re.compile(r"metal|steel|galvanised", re.I)


def stud_core(group, layers, clause, notes):
    """The stud zone of a partition whose depth the clause leaves to the system."""
    if group not in ("IW", "SW"):
        return None
    if any(l.get("hatch") in ("timber", "metal") or MEMBER_WORD.search(l.get("material") or "")
           for l in layers):
        return None          # the studs are already in a band, merged or drawn
    for para in clause:
        for s in re.split(r"(?<=[.;])\s+", para):
            m = STUD_CENTRES.search(s)
            if m:
                notes.append("stud zone drawn undimensioned — the clause gives the centres and "
                             "leaves the depth to the system manufacturer")
                # what fills between the studs, if the clause says: the zone is drawn as the
                # infill with the studs over it, which is what the wall actually is.
                fill = None
                for p2 in clause:
                    if re.search(r"infill[^.]{0,80}(mineral wool|quilt|insulation)", p2, re.I):
                        fill = "wool"
                        break
                return {"centres": float(m.group(1)),
                        "hatch": "metal" if METAL_STUD.search(s) else "timber",
                        "fill": fill,
                        "note": re.sub(r"\s+", " ", s).strip()}
    return None


def line_both_faces(group, layers, clause, notes):
    if group not in ("IW", "SW", "EW", "BW") or not layers:
        return layers
    said = any(BOTH_FACES.search(s) and LINING.search(s)
               for para in clause for s in re.split(r"(?<=[.;])\s+", para))
    if not said:
        return layers
    boards = [i for i, l in enumerate(layers) if l.get("hatch") == "pboard"]
    # Two identical boards sitting together at one end are the two faces, read from a clause that
    # names the lining once and then again for a fire variant. One belongs on the other face.
    if (len(boards) == 2 and boards[1] == boards[0] + 1 and len(layers) > 2
            and boards[1] == len(layers) - 1
            and abs(float(layers[boards[0]]["t"]) - float(layers[boards[1]]["t"])) < 0.01):
        notes.append("one of two identical linings moved to the other face - a partition is "
                     "lined on both sides")
        return [layers[boards[1]]] + layers[:boards[0]] + [layers[boards[0]]]
    if len(boards) != 1 or boards[0] not in (0, len(layers) - 1):
        return layers            # already two, or in the middle: leave it alone
    if all(l.get("hatch") == "pboard" for l in layers):
        return layers            # nothing between the faces to line — see STUD_CENTRES
    b = layers[boards[0]]
    notes.append("lining mirrored to the other face - the clause lines both faces with it")
    twin = dict(b, material=b["material"])
    return ([twin] + layers) if boards[0] == len(layers) - 1 else (layers + [twin])


def merge_member_fill(layers, notes):
    """A member zone and the insulation filling it are one band, across paragraph boundaries.

    layers_from() merges them inside a paragraph, but a clause often names the rafters in the
    paragraph about structure and the board that fills them in the paragraph about insulation —
    "47mm x 150mm C24 rafters at 400mm centres" and then, two sentences later, "150mm K107 fully
    filling the rafter depth". Both then survive and the roof is drawn 150mm too thick, which the
    sloping drawing made obvious.
    """
    out = []
    for l in layers:
        if out:
            prev = out[-1]
            same_t = abs(float(prev["t"]) - float(l["t"])) < 0.51
            pair = {prev.get("hatch"), l.get("hatch")}
            member_fill = pair in ({"timber", "ins"}, {"timber", "wool"},
                                   {"metal", "ins"}, {"metal", "wool"})
            # A partial fill is thinner than the zone it fills, so equal thicknesses cannot be the
            # only test. The words immediately around the fill have to say it fills the members —
            # "the stud depth filled with 50mm mineral wool", "mineral wool infill" — or a lining
            # board inboard of the studs would be swallowed into the frame.
            fills = l if prev.get("hatch") in ("timber", "metal") else prev
            deep = prev if fills is l else l
            partial = (member_fill and not same_t
                       and float(fills["t"]) <= float(deep["t"])
                       and (INFILLING.search(fills.get("_before", "") + " "
                                             + (fills.get("material") or ""))))
            if member_fill and (same_t or partial):
                member = prev if prev.get("hatch") in ("timber", "metal") else l
                fill = l if member is prev else prev
                if MEMBER_WORD.search(member.get("material") or ""):
                    notes.append("merged %gmm '%s' into the zone it fills — one band, not two"
                                 % (float(member["t"]), (member["material"] or "")[:44]))
                    # the band is the MEMBER's depth: a 50mm quilt in a 70mm stud is 70mm of wall
                    out[-1] = dict(fill, t=member["t"],
                                   material=("%s between %s"
                                             % (fill["material"], member["material"]))[:90])
                    continue
        out.append(l)
    return out


def face_order(group, layers, notes):
    if group not in ("RF", "SF", "IF") or len(layers) < 2:
        return layers
    first, last = (layers[0].get("hatch") or ""), (layers[-1].get("hatch") or "")
    if first in INSIDE_FACE and last not in INSIDE_FACE:
        notes.append("layers reversed so the ceiling finish reads as the inside face — the clause "
                     "states this build-up from the inside out")
        return list(reversed(layers))
    return layers


def layers_from(text, state=None):
    """Pull '103mm facing brick outer leaf' style layers out of a clause.

    Returns (layers, notes). Anything that looks like a spacing or a clearance rather than a
    layer is skipped, and the phrase each layer was read from is kept so it can be checked.
    """
    layers, notes, members = [], [], []
    last_end = None                  # where the previous accepted figure finished
    # Cavity figures already split into board + residual. Carried across the paragraphs of one
    # build-up by the caller, because the clause states the cavity in the build-up paragraph and
    # mentions it again several paragraphs later — "wall ties of the length specified for a 150mm
    # cavity in BS EN 845-1" — and a set that reset each paragraph could not see the first.
    cavities = state.setdefault("cavities", set()) if state is not None else set()
    # The lookbehind is the same guard INNER carries: the 70-character window can cut a figure in
    # half, and finditer then resumes on the fragment — "...infill and 12" left ".5mm plasterboard
    # each side" behind it, and a 5mm board no clause mentions appeared on two partitions. The
    # rescue pass reads the whole figure back, because its run-on spans the cut.
    for m in re.finditer(r"(?<![\d.])(\d+(?:\.\d+)?)\s*mm\s+([A-Za-z][^,;.()—]{2,70})", text):
        t = float(m.group(1))
        phrase = re.sub(r"\s+", " ", m.group(2)).strip()
        raw = re.sub(r"\s+", " ", m.group(0))[:90]
        after = re.sub(r"\s+", " ", text[m.end():m.end() + 90])   # for FILLS_THE_ZONE
        before = re.sub(r"\s+", " ", text[max(0, m.start() - 46):m.start()])  # for INFILLING

        # A sentence that works out a U-value is not a description of the construction, however
        # many thicknesses it contains: "72.5mm board on a 215mm solid brick wall calculates at
        # 0.28 and 62.5mm board on an uninsulated cavity wall at 0.28". Only the verb gives it
        # away — W/mK appears in perfectly good layer phrases, so it cannot be the test.
        s0 = text.rfind(". ", 0, m.start()) + 1
        s1 = text.find(". ", m.end())
        sentence = text[s0:s1 if s1 > 0 else len(text)]
        if ANOTHER_WAY.search(sentence):
            notes.append("not a layer - %gmm is in a sentence offering another way to build it: "
                         "'%s'" % (t, phrase[:44]))
            continue
        verb = WORKING_SENTENCE.search(sentence)
        # Everything BEFORE the verb is still specification — "72.5mm K118 insulated
        # plasterboard ... calculates at 0.28" names a real board. Only what follows it is
        # working: "...and 62.5mm board on an uninsulated cavity wall at 0.28". Refusing the
        # whole sentence emptied five retained-element build-ups that state the two together.
        if verb and m.start() - s0 > verb.start():
            notes.append("not a layer — %gmm follows the working in its sentence: '%s'"
                         % (t, phrase[:48]))
            continue

        # ...and only where the option before it was itself recorded as a layer. "an independent
        # stud lining or 72.5mm insulated plasterboard" offers a choice whose first half carries
        # no figure, and dropping the second left that build-up with nothing to draw at all.
        if OR_BEFORE.search(text[max(0, m.start() - 44):m.start()]) and \
                last_end is not None and m.start() - last_end < 120:
            notes.append("not a layer — %gmm is the alternative to the figure before it: '%s'"
                         % (t, phrase[:48]))
            continue

        # A member's cross-section. Held back and resolved after the loop, so that a member and
        # whatever fills it merge whichever order the clause names them in.
        mem = MEMBER.match(phrase)
        if mem:
            if MEMBER.match(mem.group(2).strip()):
                # "500 x 500mm x 700mm minimum set into the slab" — three dimensions makes it a
                # sump or a pad, an object sitting in the construction rather than a thickness
                # of it. A section through the floor does not cut it.
                notes.append("not a layer — %gmm is a component, not a section: '%s'"
                             % (t, phrase[:48]))
                continue
            pair = sorted([float(m.group(1)), float(mem.group(1))])
            members.append({"breadth": pair[0], "depth": pair[1],
                            "what": mem.group(2).strip(), "at": len(layers), "raw": raw})
            _rescue(mem.group(2), layers, notes, after)     # the depth is consumed; the rest is not
            continue

        # "100mm cavity fully filled with 90mm Kooltherm K106" is TWO layers, and reading it as
        # one both loses the board and double counts the residual against the separate mention
        # of it later in the clause. Split it: the board, and what is left of the cavity.
        fill = re.match(r"cavit(?:y|ies)[^0-9]{0,40}?(\d+(?:\.\d+)?)\s*mm\s+(.{3,60})", phrase, re.I)
        if fill and float(fill.group(1)) <= t:
            board = float(fill.group(1))
            what = fill.group(2).strip()
            # The vetoes apply to what the split produces as much as to anything else. A
            # sentence of working — "a 150mm cavity with 150mm of the 0.032 slab calculates
            # at 0.18" — reaches here looking exactly like a filled cavity, and left
            # unchecked it became a 150mm layer called "of the 0".
            if NEVER_A_LAYER.match(what) or ARITHMETIC.search(what):
                notes.append("not a layer — %gmm reads as a spacing, a level or working: '%s'"
                             % (board, what[:52]))
                continue
            if t - board > 0:
                layers.append({"t": round(t - board, 1), "material": "residual cavity",
                               "hatch": "void", "read_from": raw, "_after": after,
                               "_split": True})
            cut = INNER.search(what)
            lbl = what[:cut.start()].strip(" ,;") if cut and cut.start() >= 3 else what
            lbl = TAIL.sub("", lbl.strip(" ,;")).strip(" ,;") or what
            layers.append({"t": int(board) if board == int(board) else board,
                           "material": lbl[:70],
                           "hatch": hatch_for(lbl) or hatch_for(what) or "ins",
                           "read_from": raw, "_after": after})
            cavities.update({t, round(t - board, 1)})
            _rescue(what, layers, notes, after)
            continue

        # A cavity already split into board and residual does not get counted again when the
        # clause restates it: "a 150mm cavity with 100mm K108 ... and a 50mm clear residual
        # cavity maintained" is one cavity described twice, and was drawn as 350mm of it.
        if t in cavities and BARE_CAVITY.match(phrase):
            notes.append("not a layer — %gmm restates a cavity already read: '%s'"
                         % (t, phrase[:48]))
            continue

        # "18mm or 22mm moisture resistant chipboard" is one layer offered in two thicknesses,
        # not two layers. Keep the first — the base specification — and take its material from
        # after the alternative, whose own number is then consumed rather than rescued. Dropping
        # the first instead left a stud partition with no studs.
        alt = re.match(r"^(?:or|and)\s+(\d+(?:\.\d+)?)\s*mm\s+(.*)$", phrase, re.I)
        window = phrase
        if alt and len(alt.group(2).strip()) >= 3:
            phrase = window = alt.group(2).strip()

        _consider(t, phrase, raw, after, layers, notes, before)
        last_end = m.end()
        # Anything swallowed by this window, with a short run-on so a phrase clipped by the
        # 70-character cut can finish. The run-on is rebuilt from the ORIGINAL text and then
        # normalised, because gluing two separately-normalised pieces either splits a word or
        # welds two together — both recorded a phrase that appears in no clause.
        if alt:
            _rescue(window, layers, notes, after, t)
        else:
            run_on = re.sub(r"\s+", " ", m.group(2) + text[m.end():m.end() + 44])
            _rescue(run_on, layers, notes, after, t,
                    limit=len(re.sub(r"\s+", " ", m.group(2))))

    # Members last. A rafter zone and the insulation between the rafters are one thickness of
    # roof, not two, so a member is folded into the layer that fills it — by an equal thickness
    # where the fill is full depth, or by the clause saying so where it is not.
    for mb in members:
        same = next((L for L in layers if abs(float(L["t"]) - mb["depth"]) < 0.51), None)
        if same is None:
            same = next((L for L in layers if float(L["t"]) <= mb["depth"]
                         and FILLS_THE_ZONE.search(L.get("_after", ""))), None)
            if same is not None:      # a partial fill: the zone is still the member's depth
                same["t"] = int(mb["depth"]) if mb["depth"] == int(mb["depth"]) else mb["depth"]
        if same:
            if " between " not in same["material"]:
                same["material"] = ("%s between %g x %gmm %s"
                                    % (same["material"], mb["breadth"], mb["depth"], mb["what"]))[:90]
            continue
        if NEVER_A_LAYER.match(mb["what"]) or ARITHMETIC.search(mb["what"]) or mb["depth"] > 600:
            continue
        h = hatch_for(mb["what"])
        if h is None:
            notes.append("not treated as a layer: '%s'" % mb["what"][:56])
            continue
        d = mb["depth"]
        layers.insert(min(mb["at"], len(layers)),
                      {"t": int(d) if d == int(d) else d,
                       "material": ("%g x %gmm %s" % (mb["breadth"], d, mb["what"]))[:70],
                       "hatch": h, "read_from": mb["raw"]})
    # A cavity restated anywhere later in the clause is not a second cavity, whichever pass read
    # it. "a 150mm cavity with 100mm K108 ... and a 50mm clear residual cavity maintained" had
    # been drawn as 350mm of cavity in a 365mm wall.
    #
    # (Layer ORDER is settled by the caller, which knows the group — see face_order().)
    keep = []
    for L in layers:
        split = L.pop("_split", False)
        if (not split and L.get("hatch") == "void"
                and BARE_CAVITY.match((L.get("material") or "").strip())
                and round(float(L["t"]), 1) in cavities):
            notes.append("not a layer — %gmm restates a cavity already read: '%s'"
                         % (float(L["t"]), (L.get("material") or "")[:48]))
            continue
        L.pop("_after", None)
        keep.append(L)
    return keep, notes


def uvals(b):
    got = re.search(r"([0-9]\.[0-9]{2})\s*W/m", b.get("u") or "")
    tgt = re.search(r"maximum U-value of ([0-9]\.[0-9]{2})", b.get("tgt") or "")
    return (got.group(1) if got else None), (tgt.group(1) if tgt else None)


def build():
    S = load()
    doc = {"generated": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
           "source": "data/specdata_*.js, merged to dist/specdata.js",
           "warning": ("Layer thicknesses are EXTRACTED from the clause prose, not stored as data. "
                       "Check every layer against `clause` before drawing. Where a figure is not "
                       "in the clause it is not here either."),
           "hatches": sorted({h for _, h in HATCH}),
           "types": {}}
    md = []
    total_bu = 0
    unmatched = 0

    md.append("# Build-up schedule — layer data for drawing details\n")
    md.append("Generated by `docgen/detail_schedule.py` from `data/`. **Do not edit by hand**;\n"
              "re-run the script. Every build-up in the library is here, in reference-group order,\n"
              "with the layers read out of its clause and the clause itself underneath.\n")
    md.append("> **Read this before drawing.** The library states its layers in prose, so the\n"
              "> thicknesses below are extracted rather than stored. They are good enough to set a\n"
              "> drawing out with and not good enough to submit unchecked. The clause is printed\n"
              "> under each build-up so every layer can be checked against it in one glance.\n")

    for key in ["extension", "loft", "flat", "garage", "newbuild", "nbflats", "basement", "garagebld"]:
        spec = S[key]
        doc["types"][key] = {"name": TYPE_NAMES[key], "buildups": []}
        md.append("\n---\n\n## %s\n" % TYPE_NAMES[key])
        bus = sorted(spec["buildups"],
                     key=lambda b: (GORDER.index(b["g"]) if b["g"] in GORDER else 99, b["t"]))
        for b in bus:
            total_bu += 1
            text = "\n".join(b["p"])
            # Every paragraph, not just the first: a floor states its hardcore, slab and screed
            # across several sentences and the first alone gives a third of the build-up.
            layers, notes, seen, state = [], [], set(), {}
            for para in b["p"]:
                ls, ns = layers_from(para, state)
                notes += ns
                for l in ls:
                    # the clause names the same layer more than once — the residual cavity is
                    # mentioned inside the cavity phrase and again on its own
                    # deliberately not keyed on the hatch: the clause names the residual cavity
                    # twice and the second mention sits inside a sentence about the insulation,
                    # so the two mentions resolve to different hatches for the same layer
                    k = (l["t"], " ".join(l["material"].lower().split()[:2]))
                    if k in seen:
                        continue
                    seen.add(k)
                    layers.append(l)
            layers = face_order(b["g"], merge_member_fill(layers, notes), notes)
            layers = line_both_faces(b["g"], layers, b["p"], notes)
            for l in layers:                     # context kept only for the merges above
                l.pop("_before", None)
            got, tgt = uvals(b)
            unmatched += sum(1 for l in layers if l["hatch"] is None)
            rec = {"group": b["g"], "group_name": GROUPS.get(b["g"], b["g"]),
                   "category": b["c"], "title": b["t"],
                   "u_achieved": got, "u_target": tgt,
                   "standard": (b.get("u") or "").strip(),
                   "layers": layers,
                   "total_mm": round(sum(l["t"] for l in layers), 1) if layers else None,
                   "extraction_notes": notes,
                   "verified_table": VERIFIED.get((key, b["t"])),
                   "stud_core": stud_core(b["g"], layers, b["p"], notes),
                   "clause": b["p"]}
            doc["types"][key]["buildups"].append(rec)

            md.append("\n### %s · %s\n" % (b["g"], b["t"]))
            md.append("*%s · %s*\n" % (GROUPS.get(b["g"], b["g"]), b["c"]))
            if rec["verified_table"]:
                md.append("\n> **Use the verified table instead.** `buildup-layer-schedule.md` "
                          "§%s holds a hand-checked layer table for this build-up. It is the "
                          "authority; the extraction below is only what the clause happens to "
                          "state.\n" % rec["verified_table"])
            if got or tgt:
                md.append("\n**Target** %s · **Achieved** %s\n"
                          % (tgt + " W/m²K" if tgt else "—", got + " W/m²K" if got else (b.get("u") or "—")))
            if layers:
                md.append("\n| # | Layer | mm | Hatch |\n|---|---|---|---|")
                for i, l in enumerate(layers, 1):
                    md.append("| %d | %s | **%g** | `%s` |"
                              % (i, l["material"], l["t"], l["hatch"] or "— unmatched —"))
                md.append("| | **Extracted total** | **%g** | |" % rec["total_mm"])
            else:
                md.append("\n*No layer thicknesses stated in the clause — this build-up is described "
                          "by performance or by reference to another. Draw it from the clause.*")
            if notes:
                md.append("\n" + "\n".join("- ⚠ %s" % n for n in notes))
            md.append("\n<details><summary>Clause</summary>\n")
            for para in b["p"]:
                md.append("\n%s\n" % para)
            md.append("\n</details>\n")

    md.append("\n---\n\n*%d build-ups · %d layers with no hatch matched · generated %s*\n"
              % (total_bu, unmatched, doc["generated"]))

    os.makedirs(OUT, exist_ok=True)
    with io.open(os.path.join(OUT, "build-up-schedule.md"), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(md))
    with io.open(os.path.join(OUT, "build-up-schedule.json"), "w", encoding="utf-8", newline="") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    print("  build-up-schedule.md   %d build-ups" % total_bu)
    print("  build-up-schedule.json %d types" % len(doc["types"]))
    if unmatched:
        print("  %d layers had no hatch match — listed in the schedule as unmatched" % unmatched)
    verify(doc)
    return S


def verify(doc):
    """Refuse to leave an invented band in the schedule.

    Everything downstream draws from this file, so a bad layer here becomes a bad sheet and a bad
    DXF. On 7 September 2026 a third of the drawn build-ups carried a band read out of a spacing
    or a line of U-value working, and nothing noticed: the phrase each layer was read from was
    recorded exactly so it could be checked, and never was. This is that check, and it exits
    non-zero, because a drawing that states a wrong thickness is worse than no drawing.
    """
    bad = []
    for tk, t in doc["types"].items():
        for b in t["buildups"]:
            for L in b.get("layers", []):
                m = (L.get("material") or "").strip()
                why = ("a spacing or a level" if NEVER_A_LAYER.match(m) else
                       "a member's cross-section" if MEMBER.match(m) else
                       "U-value working" if ARITHMETIC.search(m) else None)
                if why:
                    bad.append("  %s / %s: %gmm reads as %s — '%s'"
                               % (tk, b["title"][:40], L["t"], why, m[:52]))
    if bad:
        print("\n  REFUSING THE SCHEDULE — %d layer(s) are not layers:" % len(bad))
        print("\n".join(bad))
        raise SystemExit(1)
    print("  checked: no layer reads as a spacing, a member breadth or U-value working")

    # A warning, not a refusal. Reading two thicknesses out of one sentence cannot always tell an
    # extra layer from an alternative — "215mm dense blockwork or two leaves of 100mm blockwork"
    # is one wall, and a restatement in a later paragraph looks exactly like a second band. What
    # it can do is notice when the answer has come out implausibly thick and say so, so the ones
    # worth reading get read. These are the numbers to check against the clause before issuing.
    FAT = {"EW": 500, "IW": 350, "SW": 500, "GF": 600, "IF": 500, "SF": 500,
           "RF": 600, "BW": 600, "BF": 700, "FD": 1200}
    fat = []
    for tk, t in doc["types"].items():
        for b in t["buildups"]:
            tot = sum(float(L["t"]) for L in b.get("layers", []))
            lim = FAT.get(b.get("group") or b.get("g") or "", 600)
            if tot > lim:
                fat.append("  %s / %s: %gmm — thicker than a %s is usually built"
                           % (tk, b["title"][:44], tot, b.get("group") or b.get("g") or "build-up"))
    if fat:
        print("  %d build-up(s) came out thick enough to be worth checking against the clause:"
              % len(fat))
        print("\n".join(fat))


# ─────────────────────────────────────────────────────────────────────────────────────────
# The junctions worth drawing. A detail earns its place where two build-ups meet and the
# insulation, the damp proof course or the fire separation has to be resolved. A mid-wall
# section restates the specification in a picture and is never queried.
JUNCTIONS = [
    ("D-201", "External wall to ground floor and DPC",      ["EW", "GF"],
     "Ground floor perimeter thermal bridge; DPC to DPM continuity", "drawn"),
    ("D-202", "Warm deck flat roof at the eaves",           ["EW", "RF"],
     "Wall head thermal bridge; cavity barrier at the head of the cavity", "drawn"),
    ("D-203", "Flat roof abutment to the existing dwelling",["RF"],
     "Weather-tightness and insulation continuity at the existing wall", "drawn"),
    ("D-204", "Window head — lintel and cavity tray",       ["EW"],
     "Head thermal bridge; cavity tray and weep holes over the opening", "drawn"),
    ("D-205", "Window jamb — closer and vertical DPC",      ["EW"],
     "Reveal thermal bridge; vertical DPC where the cavity is closed", "drawn"),
    ("D-206", "Window cill — sub-cill, DPC and closer",     ["EW"],
     "Cill thermal bridge; water thrown clear; guarding and glazing thresholds", "drawn"),
    ("D-207", "Eaves at a pitched roof",                    ["EW", "RF"],
     "Insulation continuity over the wall plate; ventilation path kept clear", "next"),
    ("D-208", "Verge and gable ladder",                     ["EW", "RF"],
     "Insulation continuity at the gable; cavity closed at the verge", "not drawn"),
    ("D-209", "Separating wall to roof",                    ["SW", "RF"],
     "Fire stopping at the head; sound flanking at the junction", "not drawn"),
    ("D-210", "Separating wall to intermediate floor",      ["SW", "IF"],
     "Sound flanking; fire separation between dwellings", "not drawn"),
    ("D-211", "Separating floor edge at the external wall", ["SF", "EW"],
     "Sound flanking at the perimeter; compartment continuity", "not drawn"),
    ("D-212", "Intermediate floor into the external wall",  ["IF", "EW"],
     "Joist bearing; air barrier continuity at the floor zone", "not drawn"),
    ("D-213", "Wall to foundation",                         ["FD", "EW"],
     "Cavity fill below DPC; substructure to superstructure change", "not drawn"),
    ("D-214", "Party wall at the ground floor",             ["SW", "GF"],
     "Party wall thermal bypass; sound flanking at the floor", "not drawn"),
    ("D-215", "Basement wall to basement floor",            ["BW", "BF"],
     "Waterproofing continuity at the corner; drainage to the sump", "not drawn"),
    ("D-216", "Basement wall to the ground floor over",     ["BW", "GF"],
     "Waterproofing termination; thermal bridge at the head", "not drawn"),
    ("D-217", "Dormer cheek to main roof",                  ["EW", "RF"],
     "Insulation continuity around the dormer; weathering at the abutment", "not drawn"),
    ("D-218", "Door threshold, level access",               ["EW", "GF"],
     "Thermal bridge at the threshold; water and accessibility together", "not drawn"),
]


def register(S):
    md = ["# Detail register — the junctions worth drawing\n",
          "Generated by `docgen/detail_schedule.py`. A detail earns its place where two build-ups\n"
          "meet and the insulation, the damp proof course or the fire separation has to be\n"
          "resolved. A mid-wall section restates the specification in a picture and is never\n"
          "queried, so it is not on this list.\n",
          "Layer data for every build-up named here is in `build-up-schedule.md`, and the same\n"
          "data in machine-readable form is in `build-up-schedule.json`.\n",
          "\n## The register\n",
          "| Ref | Detail | Joins | Substantiates | Status |",
          "|---|---|---|---|---|"]
    for ref, name, groups, why, status in JUNCTIONS:
        mark = {"drawn": "**drawn**", "next": "next", "not drawn": "—"}[status]
        md.append("| `%s` | %s | %s | %s | %s |"
                  % (ref, name, " + ".join(groups), why, mark))

    md.append("\n## Which project types need which\n")
    md.append("A detail is relevant to a type when that type has build-ups in both of the groups it\n"
              "joins. This is worked out from the library, so it follows the library.\n")
    md.append("\n| Ref | " + " | ".join(TYPE_NAMES[k] for k in TYPE_NAMES) + " |")
    md.append("|---" * (len(TYPE_NAMES) + 1) + "|")
    for ref, name, groups, why, status in JUNCTIONS:
        cells = []
        for k in TYPE_NAMES:
            have = {b["g"] for b in S[k]["buildups"]}
            cells.append("•" if all(g in have for g in groups) else "")
        md.append("| `%s` | %s |" % (ref, " | ".join(cells)))

    md.append("\n## Build-ups available in each type, by group\n")
    for k in TYPE_NAMES:
        by = {}
        for b in S[k]["buildups"]:
            by.setdefault(b["g"], []).append(b["t"])
        md.append("\n**%s** — %d build-ups\n" % (TYPE_NAMES[k], len(S[k]["buildups"])))
        for g in GORDER:
            if g in by:
                md.append("- `%s` %s: %s" % (g, GROUPS[g], "; ".join(sorted(by[g]))))

    md.append("\n---\n\n*Re-run `python docgen/detail_schedule.py` after any change to `data/`.*\n")
    with io.open(os.path.join(OUT, "detail-register.md"), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(md))
    drawn = sum(1 for j in JUNCTIONS if j[4] == "drawn")
    print("  detail-register.md     %d junctions, %d drawn" % (len(JUNCTIONS), drawn))


if __name__ == "__main__":
    if not os.path.exists(DIST):
        sys.exit("dist/specdata.js is missing — run python build.py first")
    register(build())
