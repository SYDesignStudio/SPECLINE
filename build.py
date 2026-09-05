#!/usr/bin/env python3
"""SY Spec Builder — build entry point.

  python build.py              merge the library and assemble the app
  python build.py --test       ... then run the Playwright test suite
  python build.py --docs       ... then regenerate every Word/PDF specification
  python build.py --docs loft  ... regenerate only the named type(s)
  python build.py --all        merge, assemble, test and regenerate the documents

Outputs go to dist/ (app) and output/ (Word and PDF). Both are git-ignored.
Nothing here touches the network or any third-party website.
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, "src")
DATA = os.path.join(ROOT, "data")
DIST = os.path.join(ROOT, "dist")
OUT  = os.path.join(ROOT, "output")

# Order matters only for readability of the merged file; the app keys off SPECS.<type>.
PARTS = ["specdata_core.js",      # extension, loft, flat  (declares `const SPECS = {...}`)
         "specdata_garage.js", "specdata_newbuild.js", "specdata_nbflats.js",
         "specdata_basement.js", "specdata_garagebld.js"]

TYPES = ["extension", "loft", "flat", "garage", "newbuild", "nbflats", "basement", "garagebld"]


def rd(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def wr(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def merge():
    """data/specdata_*.js  ->  dist/specdata.js"""
    out = []
    for p in PARTS:
        out.append("/* ===== %s ===== */\n%s\n" % (p, rd(os.path.join(DATA, p)).rstrip()))
    wr(os.path.join(DIST, "specdata.js"), "\n".join(out))
    print("merged %d library files -> dist/specdata.js" % len(PARTS))


def assemble():
    """src/* + dist/specdata.js  ->  dist/syds-spec-builder.html and dist/preview.html

    syds-spec-builder.html is the file published as the Claude artifact: it pulls jsPDF
    from cdnjs (the only host an artifact may load a script from) and has no doctype or
    <head> wrapper, because the artifact runtime supplies those.
    preview.html is the same page wrapped as a standalone document with a local jsPDF,
    so it opens from the filesystem and the Playwright tests can drive it offline.
    """
    head = rd(os.path.join(SRC, "app_head.html"))
    body = rd(os.path.join(SRC, "app_body.html"))
    spec = rd(os.path.join(DIST, "specdata.js"))
    uc   = rd(os.path.join(SRC, "ucalc.js")).replace('if(typeof module!=="undefined") module.exports=UC;', '')
    uc2  = rd(os.path.join(SRC, "ucalc2.js"))
    cfg  = rd(os.path.join(SRC, "configurator.js"))
    cfg2 = rd(os.path.join(SRC, "configurator2.js"))
    app  = rd(os.path.join(SRC, "app_js.js"))
    logos = rd(os.path.join(SRC, "logos.js"))
    assert logos.count("const LOGO") == 3, "src/logos.js must declare LOGO, LOGO_DARK and LOGO_PDF"

    marker = "/* ---------------- type chooser ---------------- */"
    assert marker in app, "anchor comment missing from src/app_js.js"
    app = app.replace(marker, cfg + "\n" + cfg2 + "\n" + marker, 1)

    js = "\n".join([spec, uc, uc2, logos, app])
    html = (head + "\n" + body +
            '\n<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>\n'
            '<script>\n' + js + '\n</script>\n')
    wr(os.path.join(DIST, "syds-spec-builder.html"), html)

    local = html.replace("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
                         "../src/vendor/jspdf.local.js")
    wr(os.path.join(DIST, "preview.html"),
       '<!doctype html><html><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'
       + local + '</body></html>')
    print("assembled dist/syds-spec-builder.html (%d bytes) and dist/preview.html" % len(html))


def check():
    """Structural checks on the merged library. Cheap, and catches the mistakes that matter."""
    js = ('const fs=require("fs");const s=fs.readFileSync(%r,"utf8");'
          'process.stdout.write(JSON.stringify(new Function(s+";return SPECS;")()))'
          % os.path.join(DIST, "specdata.js").replace("\\", "/"))
    import json
    S = json.loads(subprocess.check_output(["node", "-e", js]).decode())
    bad = 0
    tb = tn = 0
    for k in TYPES:
        v = S[k]
        tb += len(v["buildups"]); tn += len(v["notes"])
        orphan_n = [n["t"] for n in v["notes"] if n["c"] not in v["cats"]]
        orphan_b = [b["t"] for b in v["buildups"] if b["c"] not in v["cats"]]
        empty = [c for c in v["cats"]
                 if not any(n["c"] == c for n in v["notes"])
                 and not any(b["c"] == c for b in v["buildups"])]
        flags = []
        if orphan_n: flags.append("notes outside cats: %s" % orphan_n)
        if orphan_b: flags.append("build-ups outside cats: %s" % orphan_b)
        if empty:    flags.append("empty categories: %s" % empty)
        bad += len(flags)
        print("  %-10s %2d cats  %2d build-ups  %2d notes%s"
              % (k, len(v["cats"]), len(v["buildups"]), len(v["notes"]),
                 "   ** " + "; ".join(flags) if flags else ""))
    print("  TOTAL %d build-ups, %d notes" % (tb, tn))
    if bad:
        sys.exit("library check FAILED (%d problems)" % bad)
    print("library check passed")


def test():
    fails = 0
    for n in range(1, 7):
        t = os.path.join(ROOT, "tests", "test%d.py" % n)
        r = subprocess.run([sys.executable, t], capture_output=True, text=True, cwd=ROOT)
        passes = r.stdout.count('"r": "PASS"')
        f = r.stdout.count('"r": "FAIL"')
        fails += f
        print("  test%d: %d passed, %d failed" % (n, passes, f))
        if f:
            for line in r.stdout.splitlines():
                if '"FAIL"' in line or ('"t":' in line and False):
                    print("     ", line.strip())
            print(r.stdout[-1500:])
    if fails:
        sys.exit("%d test failures" % fails)
    print("all tests passed")


def docs(types):
    subprocess.run([sys.executable, os.path.join(ROOT, "docgen", "spec_from_data.py")] + list(types),
                   check=True, cwd=ROOT)


if __name__ == "__main__":
    args = sys.argv[1:]
    flags = [a for a in args if a.startswith("--")]
    rest  = [a for a in args if not a.startswith("--")]
    merge(); assemble(); check()
    if "--test" in flags or "--all" in flags:
        test()
    if "--docs" in flags or "--all" in flags:
        docs(rest or TYPES)
