"""Word export from the app.

Drives the browser to build a .docx, saves it, then opens it with python-docx —
the same library the practice generator uses — so a file Word would reject fails
here rather than in front of a building control officer.
"""
from playwright.sync_api import sync_playwright
import json, os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys as _sys
_sys.path.insert(0, os.path.join(ROOT, "docgen"))
import practice as _pr
PRACTICE_NAME = _pr.load()["name"]
URL = "file://" + os.path.join(ROOT, "dist", "preview.html").replace("\\", "/")
DL = os.path.join(ROOT, "dist", "dl")
os.makedirs(DL, exist_ok=True)
R = []
def ok(n, c, x=""): R.append((("PASS" if c else "FAIL"), n, x))

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1500, 'height': 980}, accept_downloads=True)
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(700)
    pg.evaluate("try{localStorage.clear()}catch(e){}")
    pg.goto(URL); pg.wait_for_timeout(700)

    # a full extension job, everything selected, so every section is exercised
    pg.click('.tile[data-k="extension"]'); pg.wait_for_timeout(600)
    ok("W1 Word button present", pg.locator("#btnDocx").count() == 1)
    pg.evaluate("""S.data.job='1150'; S.data.project='Single-storey rear extension';
        S.data.address='42 Hollybank Road, Hounslow'; S.data.client='Mr & Mrs Ahmed';
        S.sel=allBU().map((_,i)=>i); renderSteps(); renderStage(); renderPaper(); save();""")
    pg.wait_for_timeout(400)

    # add a calculated wall so section 4.0 has working in it
    pg.locator('button.step:has-text("External Walls")').click(); pg.wait_for_timeout(300)
    if pg.locator("#addWall").count():
        pg.click("#addWall"); pg.wait_for_timeout(400)
    ok("W2 a calculated build-up is on the job", pg.evaluate("calcsOnJob().length") >= 1,
       str(pg.evaluate("calcsOnJob().length")))

    with pg.expect_download(timeout=40000) as di:
        pg.click("#btnDocx")
    d = di.value
    path = os.path.join(DL, d.suggested_filename)
    d.save_as(path)
    ok("W3 downloads with a .docx name", d.suggested_filename.endswith(".docx"), d.suggested_filename)
    size = os.path.getsize(path)
    ok("W4 file is a plausible size", size > 20000, f"{size} bytes")

    # a .docx is a zip: check the parts Word requires are all present
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        bad = z.testzip()
    ok("W5 zip is not corrupt", bad is None, str(bad))
    for part in ["[Content_Types].xml", "_rels/.rels", "word/document.xml",
                 "word/styles.xml", "word/_rels/document.xml.rels",
                 "word/header1.xml", "word/footer1.xml"]:
        ok(f"W6 part present: {part}", part in names, ", ".join(names[:9]))
    ok("W7 practice logo embedded", any(n.startswith("word/media/logo.") for n in names), ", ".join(names))

    # python-docx is the real test: it parses the XML the way Word does
    try:
        from docx import Document
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
        ok("W8 python-docx opens the file", True)
        # Assert the practice from the profile, not a literal: a test that names one firm
        # is the same hard-coding a layer up, and would go green on a document carrying the
        # wrong practice as long as that practice happened to be this one.
        ok("W9 cover carries the practice, not Specline",
           PRACTICE_NAME in text and "Specline" not in text,
           "Specline present" if "Specline" in text else ("missing " + PRACTICE_NAME))
        ok("W10 responsibility statement present",
           "is the named designer and remains responsible" in text)
        ok("W11 compliance wording exact",
           "not an approval of it" in text and "building control body" in text)
        ok("W12 Part A and Part B headings present",
           "PART A — CONSTRUCTION BUILD-UPS" in text.upper() and "PART B" in text.upper())
        ok("W13 U-value working section present", "U-VALUE CALCULATIONS" in text.upper())
        ok("W14 a clause paragraph came through",
           "cavity" in text.lower() and len(text) > 20000, f"{len(text)} chars")
        # tables: schedule + cover + at least one working table
        ok("W15 tables present", len(doc.tables) >= 3, str(len(doc.tables)))
        sched = "\n".join(c.text for c in doc.tables[1].rows[0].cells) if len(doc.tables) > 1 else ""
        ok("W16 schedule table has the expected columns",
           "REF" in sched.upper() and "BUILD-UP" in sched.upper(), sched.replace("\n", " ")[:60])
        refs = "\n".join(c.text for r in doc.tables[1].rows for c in r.cells)
        ok("W17 build-up references numbered per job", "EW1" in refs and "GF1" in refs,
           refs.replace("\n", " ")[:80])
    except ImportError:
        ok("W8 python-docx opens the file", False, "python-docx not installed")

    # the superscript characters must survive; Word handles them, unlike the PDF fonts
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    ok("W18 m²K survives into the XML", "m²K" in xml or "W/m²K" in xml)
    ok("W19 no unescaped ampersands", "& " not in xml.replace("&amp; ", ""))

    ok("W20 no page errors", len(errs) == 0, "; ".join(errs[:2]))
    print(json.dumps([{"r": a, "t": b_, "x": c} for a, b_, c in R]))
    print("PAGE ERRORS:", errs[:4])
    b.close()
