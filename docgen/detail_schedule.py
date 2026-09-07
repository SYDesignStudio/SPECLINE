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

# A number followed by one of these is a spacing, a lap or a clearance — never a layer.
NOT_A_LAYER = re.compile(
    r"^(centres|wide|deep|long|high|apart|above|below|clear|minimum|maximum|min|max|"
    r"bearing|overlap|lap|laps|cover|diameter|gauge|square|thick at|from|"
    r"either side|each side|beyond|into|onto|of the|in every|at |"
    # not layers: arithmetic, spacings, member sizes, prose carried over by the match
    r"calculates|and over\b|and in no case|is to be used|for both|to a minimum|"
    r"where necessary|openings along|over \d|x \d|vertical|horizontal|"
    r"gap at|gap along|gap on|and free of|so that)", re.I)

# material phrase -> the hatch to draw it with. Names match the patterns in the detail sheets.
HATCH = [
    (r"facing brick|brick outer|brickwork outer|facing brickwork|brick-on-edge|engineering brick|"
     r"solid brick|brick wall|brickwork", "brick"),
    (r"aircrete|thermalite|celcon|blockwork inner|block inner|aerated block", "block"),
    (r"dense concrete block|dense block|concrete block|block wall|blockwork|\bblock\b", "dense"),
    (r"kooltherm|celotex|sopratherm|xtratherm|unilin|ecotherm|thermaroof|thermafloor|thermawall|"
     r"pir\b|phenolic|rigid (?:urethane )?insulation|insulation board|insulated plasterboard|"
     r"polystyrene|eps\b|xps\b|foam board|k1\d\d|t[rf]\d\d|cw4000|ga4000|xt/|upstand|insulation", "ins"),
    (r"mineral wool|rockwool|dritherm|knauf|glass wool|quilt|cavity barrier|acoustic (?:roll|quilt)", "wool"),
    (r"joist|rafter|stud|batten|counter-batten|timber|softwood|plywood|osb|sole plate|wall plate|"
     r"noggin|firring|deck|fascia|soffit|chipboard|t&g|tongued and grooved|plank flooring|"
     r"flooring grade|floorboard", "timber"),
    (r"screed", "screed"),
    (r"hardcore|sub-base|compacted fill", "hard"),
    (r"lean mix|lean-mix", "lean"),
    (r"concrete|slab|raft|beam and block", "conc"),
    (r"plasterboard|plaster|skim|dab|lining board|render", "pboard"),
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


def layers_from(text):
    """Pull '103mm facing brick outer leaf' style layers out of a clause.

    Returns (layers, notes). Anything that looks like a spacing or a clearance rather than a
    layer is skipped, and the phrase each layer was read from is kept so it can be checked.
    """
    layers, notes = [], []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*mm\s+([A-Za-z][^,;.()—]{2,70})", text):
        t = float(m.group(1))
        phrase = re.sub(r"\s+", " ", m.group(2)).strip()
        raw = re.sub(r"\s+", " ", m.group(0))[:90]
        # The qualifier test runs only when no material is named. "150mm minimum well-compacted
        # hardcore" begins with a qualifier and is still a layer, because hardcore is a material.
        if NOT_A_LAYER.match(phrase) and hatch_for(phrase) is None:
            continue
        if t > 600:                      # no single layer in this library is thicker
            notes.append("skipped %gmm %s — too thick to be a layer" % (t, phrase[:40]))
            continue

        # "100mm cavity fully filled with 90mm Kooltherm K106" is TWO layers, and reading it as
        # one both loses the board and double counts the residual against the separate mention
        # of it later in the clause. Split it: the board, and what is left of the cavity.
        fill = re.match(r"cavit(?:y|ies)[^0-9]{0,40}?(\d+(?:\.\d+)?)\s*mm\s+(.{3,60})", phrase, re.I)
        if fill:
            board = float(fill.group(1))
            what = fill.group(2).strip()
            if board <= t:
                if t - board > 0:
                    layers.append({"t": round(t - board, 1), "material": "residual cavity",
                                   "hatch": "void", "read_from": raw})
                layers.append({"t": int(board) if board == int(board) else board,
                               "material": what[:70], "hatch": hatch_for(what) or "ins",
                               "read_from": raw})
                continue

        h = hatch_for(phrase)
        if h is None:
            # A layer with no identifiable material is prose the pattern happened to catch, not a
            # layer. Recorded rather than guessed, so `layers` stays safe to draw from.
            notes.append("not treated as a layer: '%s'" % phrase[:56])
            continue
        layers.append({"t": int(t) if t == int(t) else t,
                       "material": phrase[:70], "hatch": h,
                       "read_from": raw})
    return layers, notes


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
            layers, notes, seen = [], [], set()
            for para in b["p"]:
                ls, ns = layers_from(para)
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
    return S


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
