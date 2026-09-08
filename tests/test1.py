from playwright.sync_api import sync_playwright
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL="file://"+os.path.join(ROOT,"dist","preview.html").replace("\\","/")
os.makedirs(os.path.join(ROOT,"dist","dl"),exist_ok=True)
R=[]
def ok(n,c,extra=""): R.append((("PASS" if c else "FAIL"),n,extra))

with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':1500,'height':980},accept_downloads=True)
    pg=ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(900)

    # T1 chooser shows first, 8 tiles, 2 enabled
    ok("T1 desk visible on load", pg.is_visible("#home") and not pg.is_visible("#chooser"))
    ok("T1 eight project types", pg.locator(".tile").count()==8, str(pg.locator(".tile").count()))
    ok("T1 built types enabled", pg.locator(".tile:not(.soon)").count()==8, str(pg.locator(".tile:not(.soon)").count()))
    ok("T1 workspace hidden on the desk", not pg.is_visible("#stage"))

    # T2 pick extension
    pg.click('.tile[data-k="extension"]'); pg.wait_for_timeout(600)
    ok("T2 desk closes", not pg.is_visible("#home") and pg.is_visible("#stage"))
    ok("T2 18 categories", pg.locator("button.step").count()==18, str(pg.locator("button.step").count()))
    ok("T2 starts at the job record", "JOB RECORD" in pg.inner_text(".crumb").upper())
    ok("T2 six job record fields", pg.locator("#fields input").count()==6)
    ok("T2 chip shows type", pg.inner_text("#typename")=="House Extension")

    # T3 every category reachable and populated
    empty=[]
    for i in range(18):
        pg.locator("button.step").nth(i).click(); pg.wait_for_timeout(120)
        name=pg.inner_text(".stagehead h2")
        cards=pg.locator("#stage .card").count()
        if cards==0: empty.append(name)
    ok("T3 no empty categories", len(empty)==0, "empty: "+", ".join(empty))

    # T4 selection-order numbering: clear EW, tick Partial first then Full
    pg.locator('button.step:has-text("External Walls")').click(); pg.wait_for_timeout(200)
    boxes=pg.locator('#stage .card input[data-t="b"]')
    for i in range(boxes.count()):
        if boxes.nth(i).is_checked(): boxes.nth(i).uncheck(); pg.wait_for_timeout(120)
    pg.locator('#stage .card:has-text("Partial Fill Cavity Wall") input').first.check(); pg.wait_for_timeout(200)
    pg.locator('#stage .card:has-text("Full Fill Cavity Wall") input').first.check(); pg.wait_for_timeout(250)
    tags=[t.strip() for t in pg.locator('#stage .card .tag:not(.off)').all_inner_texts()]
    sched=pg.inner_text("#paper .sched")
    ok("T4 partial fill becomes EW1", "EW1" in pg.locator('#stage .card:has-text("Partial Fill Cavity Wall") .tag').first.inner_text())
    ok("T4 full fill becomes EW2", "EW2" in pg.locator('#stage .card:has-text("Full Fill Cavity Wall") .tag').first.inner_text())
    ok("T4 schedule reflects order", sched.index("Partial Fill")<sched.index("Full Fill"))

    # T5 category counts update
    c=pg.locator('button.step:has-text("External Walls") .sc').inner_text().strip()
    tot=pg.locator('#stage .card input[data-t="b"]').count()
    ok("T5 count badge reflects selection", c==f"2/{tot}", f"{c} (cards {tot})")

    # T6 untick all notes in Ventilation -> disappears from preview
    pg.locator('button.step:has-text("Ventilation")').click(); pg.wait_for_timeout(200)
    nb=pg.locator('#stage .card input[data-t="n"]')
    for i in range(nb.count()):
        if nb.nth(i).is_checked(): nb.nth(i).uncheck(); pg.wait_for_timeout(150)
    ok("T6 ventilation removed from preview", "VENTILATION — APPROVED DOCUMENT F" not in pg.inner_text("#paper").upper())
    nb.first.check(); pg.wait_for_timeout(200)
    ok("T6 re-adding restores it", "VENTILATION — APPROVED DOCUMENT F" in pg.inner_text("#paper").upper())

    # T6b build-ups and notes are separate views where a category holds both
    found=None
    for i in range(pg.locator("button.step").count()):
        pg.locator("button.step").nth(i).click(); pg.wait_for_timeout(120)
        labs=[t.strip().splitlines()[0] for t in pg.locator(".stab").all_inner_texts()]
        if "Build-ups" in labs and "Notes" in labs: found=pg.inner_text(".stagehead h2"); break
    ok("T6b a category holding both shows them as separate tabs", found is not None, str(found))
    ok("T6b the build-ups open first, with no notes behind them",
       pg.locator('#stage .card input[data-t="b"]').count()>0 and pg.locator('#stage .card input[data-t="n"]').count()==0)
    n0=pg.locator('.stab:has-text("Notes") .stn').inner_text().strip()
    pg.locator('.stab:has-text("Notes")').click(); pg.wait_for_timeout(250)
    ok("T6b the notes tab shows the notes alone",
       pg.locator('#stage .card input[data-t="n"]').count()>0 and pg.locator('#stage .card input[data-t="b"]').count()==0)
    pg.locator('#stage .card input[data-t="n"]').first.uncheck(); pg.wait_for_timeout(250)
    n1=pg.locator('.stab:has-text("Notes") .stn').inner_text().strip()
    ok("T6b the tab count follows the ticks", n1!=n0, f"{n0} -> {n1}")
    pg.locator('#stage .card input[data-t="n"]').first.check(); pg.wait_for_timeout(200)
    ok("T6b a category of notes alone keeps its single page",
       (pg.locator('button.step:has-text("Ventilation")').first.click(), pg.wait_for_timeout(250),
        pg.locator(".stagetabs").count()==0 and pg.locator('#stage .card input[data-t="n"]').count()>0)[2])

    # T7 read full clause toggle
    pg.locator('button.step:has-text("External Walls")').click(); pg.wait_for_timeout(200)
    before=pg.locator("#stage .card .text").first.bounding_box()["height"]
    pg.locator("#stage .card .more").first.click(); pg.wait_for_timeout(200)
    after=pg.locator("#stage .card .text").first.bounding_box()["height"]
    ok("T7 read full clause expands", after>before, f"{before:.0f}->{after:.0f}")

    # T8 project details flow into preview
    pg.click("#stepJob"); pg.wait_for_timeout(200)
    pg.fill('#fields input[data-k="job"]', "1140")
    pg.fill('#fields input[data-k="address"]', "28 Talbot Road, Isleworth TW7 7HH")
    pg.wait_for_timeout(300)
    ok("T8 job number in preview", "1140" in pg.inner_text("#paper"))
    ok("T8 address in preview", "Talbot Road" in pg.inner_text("#paper"))

    # T9 persistence across reload
    pg.reload(); pg.wait_for_timeout(900)
    ok("T9 workspace restored after reload", pg.is_visible("#stage") and not pg.is_visible("#home"))
    ok("T9 job number restored", "1140" in pg.inner_text("#paper"))
    ok("T9 EW numbering restored", "EW1" in pg.inner_text("#paper .sched"))

    # T10 review and issue: the summary and the schedule are separate views; the actions are not
    pg.evaluate("S.sel=spec().buildups.map((_,i)=>i); renderSteps(); setStep('review');"); pg.wait_for_timeout(400)
    labs=[t.strip().splitlines()[0] for t in pg.locator(".stab").all_inner_texts()]
    ok("T10 review splits into summary and build-ups", labs==["Summary","Build-ups"], str(labs))
    stage=pg.inner_text("#stage")
    ok("T10 the summary opens first", "Cover page complete" in stage or "fields not set" in stage)
    ok("T10 the issue actions stay out of the tabs",
       pg.is_visible("#issue") and pg.is_visible("#finish") and pg.is_visible("#finishDocx"))
    nsum=pg.locator("#stage .rows .row").count()
    pg.locator('.stab:has-text("Build-ups")').click(); pg.wait_for_timeout(250)
    nbus=pg.locator("#stage .rows .row").count()
    ok("T10 the build-up rows are their own view",
       nbus==len(pg.evaluate("orderedSel()")) and nbus!=nsum, "%d summary, %d build-ups" % (nsum, nbus))
    ok("T10 the actions are still there behind the tab", pg.is_visible("#issue"))
    # a build-up over its target names itself on the tab rather than hiding behind it
    pg.evaluate("""S.custom=[{g:'EW',cat:'__wall__',t:'Over target for the test',u:'0.30 W/m2K',tgt:'x',p:['test'],
        calc:{params:{limit:0.18},result:{U:0.30,layers:[{n:'x',d:100,R:1}],src:[]}}}];
        S.sel.push(allBU().length-1); renderReview();"""); pg.wait_for_timeout(300)
    tabtext=pg.locator('.stab:has-text("Build-ups")').inner_text()
    ok("T10 a failing check is named on the tab", "over target" in tabtext, " ".join(tabtext.split()))
    ok("T10 and it is marked, not merely coloured",
       "bad" in (pg.locator('.stab:has-text("Build-ups") .stn').get_attribute("class") or ""))

    print(json.dumps([{"r":a,"t":b,"x":c} for a,b,c in R],indent=0))
    print("PAGE ERRORS:", errs[:5])
    b.close()
