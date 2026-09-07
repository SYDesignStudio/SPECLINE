#!/usr/bin/env python3
"""Review every extracted build-up against its own clause, and say what is wrong.

    python docgen/detail_review.py            every build-up
    python docgen/detail_review.py extension  one project type
    python docgen/detail_review.py --quiet    counts only

WHY THIS EXISTS. detail_schedule.py reads layers out of prose and verify() refuses the errors it
can name with certainty — a spacing read as a thickness, a member's breadth, a line of U-value
working. Those are the ones a regular expression can be sure about. This file is for everything
else: the defects that need the layers and the clause read side by side, which nobody was doing.
Two rounds of that reading on 7 September 2026 found an invented band in 45% of the drawn set and
about 25 layers missing from the rest, both of which had been shipping silently for weeks.

It reports; it never edits. A finding here is a prompt to read the clause, not a licence to change
a figure — non-negotiable 1 in CLAUDE.md applies to this file as much as to the library.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "reference", "details", "build-up-schedule.json")
sys.path.insert(0, os.path.join(ROOT, "docgen"))
from detail_schedule import hatch_for, NEVER_A_LAYER, MEMBER, ARITHMETIC   # noqa: E402

# What a build-up of each group is expected to finish with on the inside face, and what it needs
# on the outside. Absence is a question, not a failure: a clause states what it states.
INSIDE  = {"EW": ("pboard", "ins"), "IW": ("pboard",), "SW": ("pboard",), "BW": ("pboard", "ins"),
           "RF": ("pboard", "timber"), "GF": ("timber", "screed", "conc"),
           "IF": ("pboard",), "SF": ("pboard",), "BF": ("screed", "conc", "timber")}
OUTSIDE = {"EW": ("brick", "block", "dense", "pboard", "timber"),
           "SW": ("brick", "block", "dense"), "BW": ("conc", "block", "dense", "membrane")}
# A wall is read from the outside in. Plasterboard on the outer face is the tell that the clause
# was written inside-out or that a later sentence was picked up as if it came first.
FINISH_LAST = {"EW", "SW", "BW"}

THIN, THICK = 3.0, 400.0


def review(doc, only=None):
    findings = []

    def add(sev, tk, b, msg):
        findings.append((sev, tk, b["title"], msg))

    for tk, t in doc["types"].items():
        if only and tk != only:
            continue
        for b in t["buildups"]:
            ls = b.get("layers", [])
            g = b.get("group") or ""
            clause = " ".join(b.get("clause", []))
            tot = sum(float(L["t"]) for L in ls)

            if not ls:
                add("note", tk, b, "no layers — the clause states no thicknesses; nothing is drawn")
                continue

            # 1. the hatch still follows from the material it was chosen for
            for L in ls:
                h = hatch_for(L.get("material") or "")
                if h and L.get("hatch") and h != L["hatch"]:
                    add("FAIL", tk, b, "hatch drift: %gmm '%s' is drawn as %s, reads as %s"
                        % (L["t"], (L["material"] or "")[:34], L["hatch"], h))

            # 2. nothing that verify() would refuse (belt and braces — this file can be run alone)
            for L in ls:
                m = (L.get("material") or "").strip()
                if NEVER_A_LAYER.match(m) or MEMBER.match(m) or ARITHMETIC.search(m):
                    add("FAIL", tk, b, "not a layer: %gmm '%s'" % (L["t"], m[:44]))

            # 3. the phrase each layer was read from is still in the clause
            flat = re.sub(r"\s+", " ", clause)
            for L in ls:
                probe = (L.get("read_from") or "")[:28]
                if probe and probe not in flat:
                    add("warn", tk, b, "provenance lost: '%s' is not in the clause" % probe)

            # 4. two identical bands touching is a layer counted twice
            for a, c in zip(ls, ls[1:]):
                if abs(float(a["t"]) - float(c["t"])) < 0.01 and a.get("hatch") == c.get("hatch"):
                    add("warn", tk, b, "possible double count: two touching %gmm %s bands"
                        % (float(a["t"]), a.get("hatch")))

            # 5. a wall read inside-out
            if g in FINISH_LAST and len(ls) > 2:
                hs = [L.get("hatch") for L in ls]
                lined_both = hs[0] == "pboard" and hs[-1] == "pboard"
                if not lined_both and hs[0] == "pboard" and                         any(h in ("brick", "block", "dense") for h in hs[1:]):
                    add("FAIL", tk, b, "drawn inside-out: the internal finish is the outer layer")

            # 6. does it finish anywhere sensible
            if g in INSIDE and not any(L.get("hatch") in INSIDE[g] for L in ls):
                add("note", tk, b, "no internal finish among the layers (%s)"
                    % ", ".join(sorted({str(L.get("hatch")) for L in ls})))
            if g in OUTSIDE and not any(L.get("hatch") in OUTSIDE[g] for L in ls):
                add("note", tk, b, "no outer leaf among the layers")

            # 7. outliers worth an eye
            for L in ls:
                if float(L["t"]) < THIN:
                    add("warn", tk, b, "%gmm '%s' is thinner than anything usually drawn"
                        % (L["t"], (L["material"] or "")[:34]))
                elif float(L["t"]) > THICK:
                    add("warn", tk, b, "%gmm '%s' is thicker than a single layer usually is"
                        % (L["t"], (L["material"] or "")[:34]))

            # 8. a hand-checked table is the authority where one exists
            if b.get("verified_table") and b.get("total_mm"):
                add("note", tk, b, "hand-checked table %s exists — extracted total %gmm, that "
                                   "table wins" % (b["verified_table"], b["total_mm"]))

            # 9. the target has to be there to be met. A retained element states its standard in
            # the `standard` line rather than as "a maximum U-value of X", so both count.
            if b.get("u_achieved") and not (b.get("u_target") or b.get("standard")):
                add("warn", tk, b, "U-value %s stated with no target to measure it against"
                    % b["u_achieved"])
    return findings


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    doc = json.load(open(SRC, encoding="utf-8"))
    f = review(doc, args[0] if args else None)
    order = {"FAIL": 0, "warn": 1, "note": 2}
    f.sort(key=lambda x: (order[x[0]], x[1], x[2]))
    counts = {k: sum(1 for x in f if x[0] == k) for k in order}
    if not quiet:
        cur = None
        for sev, tk, title, msg in f:
            key = (tk, title)
            if key != cur:
                print("\n  %s / %s" % (tk, title))
                cur = key
            print("      %-5s %s" % (sev, msg))
    print("\n  %d FAIL   %d warn   %d note   across %d build-ups"
          % (counts["FAIL"], counts["warn"], counts["note"],
             len({(x[1], x[2]) for x in f})))
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
