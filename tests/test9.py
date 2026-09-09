# -*- coding: utf-8 -*-
"""Suite 9 — a whole specification, per project type, read back as a document.

The other suites drive the app; this one reads what comes out of it. It builds a specification for
every project type with every build-up on it, for two manufacturers, and asserts on the rendered
document text rather than on the source — which is where a reader finds a fault and where the
source can look perfectly reasonable.

It exists because of a review of an issued specification on 9 September 2026. Everything it checks
is something that review found, or something the fixes for it must not undo:

  - flat roof falls state the BS 6229 rule (design 1:40 to a finished 1:80), never the reverse;
  - "VERIFY BEFORE ISSUE" is an instruction to the author and never prints on an issued document;
  - the application is named in current terms;
  - the specification says it takes precedence over generic notes in the drawing pack;
  - notes about a feature the project may not have are OFF until the designer turns them on, so a
    rear extension does not go to building control with septic tanks and wind turbines in it;
  - nothing states a U-value worse than the target printed beside it, for any manufacturer.
"""
import json, pathlib, re, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
URL = (ROOT / "dist" / "preview.html").as_uri()
TYPES = ["extension", "loft", "flat", "garage", "newbuild", "nbflats", "basement", "garagebld"]
MFRS = ["kingspan", "celotex"]

BANNED = [
    ("VERIFY BEFORE ISSUE", "an internal quality-control heading"),
    ("minimum finished 1:40", "the reversed flat roof falls"),
    ("finished falls of not less than 1:40", "a finished fall where a design fall is meant"),
    ("falls of not less than 1:40 finished", "a finished fall where a design fall is meant"),
    ("Full Plans Application", "the superseded application name"),
]
# A new dwelling's Part L compliance normally leans on low-carbon technology, so those notes
# belong on a new build. The complaint was about an extension, and these are the retrofit types.
OPTIONAL_MARKERS = [("septic tank", "off-mains drainage"), ("wind turbine", "wind"),
                    ("ground source heat pump", "ground source heat pumps"), ("greywater", "water reuse")]

out = []
def ok(t, cond, x=""):
    out.append({"r": "PASS" if cond else "FAIL", "t": t, "x": str(x)[:150]})

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 1000})
    pg.goto(URL); pg.wait_for_timeout(700)
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(700)

    for mfr in MFRS:
        for t in TYPES:
            pg.evaluate("localStorage.clear()")
            pg.reload(); pg.wait_for_timeout(420)
            pg.click('.tile[data-k="%s"]' % t); pg.wait_for_timeout(520)
            pg.evaluate("""
                P.name='Marchmont Ridley Architects'; P.designer='J Marchmont';
                P.addr='14 Bellhouse Yard, Leeds LS2 7QR'; P.email='studio@example.test';
                S.data.job='9001'; S.data.project='Suite specimen';
                S.data.address='Specimen address'; S.data.client='Specimen client';
                S.data.mfr='%s';
                S.sel = allBU().map((_,i)=>i);
                renderSteps(); renderStage(); renderPaper(); save(); go('spec');""" % mfr)
            pg.wait_for_timeout(750)
            txt = pg.evaluate("document.getElementById('paper').innerText")
            tag = "S9 %s/%s" % (t, mfr)

            for phrase, why in BANNED:
                ok("%s: no %s" % (tag, why), phrase not in txt, phrase)
            ok("%s: transitional provisions note present" % tag, "TRANSITIONAL PROVISIONS" in txt)
            ok("%s: application named in current terms" % tag,
               "Building Control Approval Application with Full Plans" in txt)
            ok("%s: takes precedence over the drawing pack" % tag,
               "takes precedence over any conflicting generic" in txt)

            falls = re.findall(r"[Ff]alls?[^.]{0,200}?1:\d+[^.]{0,200}", txt)
            for f in falls:
                low = f.lower()
                if any(k in low for k in ("drain", "gradient", "sewer", "ramp")):
                    continue
                ok("%s: a roof falls sentence cites BS 6229" % tag,
                   "1:40" not in f or "BS 6229" in f, f[:110])

            # Every note marked optional is off on a new job, and none of their headings print.
            # Asserting on the note titles rather than on keywords matters: "greywater" appears in
            # a conditional sentence inside a general note on the flat conversion, which is honest
            # prose and not an irrelevant section, and a keyword check called that a failure.
            offs = pg.evaluate("optOff()")
            marked = pg.evaluate("spec().notes.filter(n=>n.opt).map(n=>n.t)")
            ok("%s: every optional note starts off" % tag, sorted(offs) == sorted(marked),
               "off=%d of %d marked" % (len(offs), len(marked)))
            # Check the HEADINGS, not the whole text: a note may legitimately name an optional
            # note in a designer NOTE — the loft alarm clause tells you to turn the Houses in
            # Multiple Occupation note on — and that is a cross-reference, not the section itself.
            heads = [h.strip().upper() for h in
                     pg.evaluate("[...document.querySelectorAll('#paper h3,#paper h4')].map(e=>e.textContent)")]
            for title in marked:
                ok("%s: '%s' is not a section by default" % (tag, title[:38]),
                   title.upper() not in heads, title)

            bad = pg.evaluate("""(()=>{const o=[];allBU().forEach(b=>{
                if(!b.u||!b.tgt) return;
                const a=parseFloat((b.u.match(/[\\d.]+/)||[])[0]);
                const m=b.tgt.match(/maximum U-value of ([\\d.]+)/);
                if(a&&m&&a>parseFloat(m[1])+1e-9) o.push(b.t+' '+a+' > '+m[1]);});return o;})()""")
            ok("%s: no build-up worse than its own target" % tag, not bad, "; ".join(bad))
            ok("%s: no manufacturer shortfall note" % tag, "not to be issued as it stands" not in txt)

    errs = pg.evaluate("window.__errs||[]")
    ok("S9 no page errors", not errs, str(errs)[:150])
    b.close()

print(json.dumps(out))
sys.exit(1 if any(o["r"] == "FAIL" for o in out) else 0)
