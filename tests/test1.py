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
    ok("T1 chooser visible on load", pg.is_visible("#chooser"))
    ok("T1 eight project types", pg.locator(".tile").count()==8, str(pg.locator(".tile").count()))
    ok("T1 built types enabled", pg.locator(".tile:not(.soon)").count()==8, str(pg.locator(".tile:not(.soon)").count()))
    ok("T1 app hidden behind chooser", not pg.is_visible("#stage"))

    # T2 pick extension
    pg.click('.tile[data-k="extension"]'); pg.wait_for_timeout(600)
    ok("T2 chooser closes", not pg.is_visible("#chooser"))
    ok("T2 18 categories", pg.locator("button.step").count()==18, str(pg.locator("button.step").count()))
    ok("T2 starts at step 1", "STEP 1 OF 18" in pg.inner_text(".crumb").upper())
    ok("T2 project fields on step 1", pg.locator("#fields input").count()==6)
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

    # T7 read full clause toggle
    pg.locator('button.step:has-text("External Walls")').click(); pg.wait_for_timeout(200)
    before=pg.locator("#stage .card .text").first.bounding_box()["height"]
    pg.locator("#stage .card .more").first.click(); pg.wait_for_timeout(200)
    after=pg.locator("#stage .card .text").first.bounding_box()["height"]
    ok("T7 read full clause expands", after>before, f"{before:.0f}->{after:.0f}")

    # T8 project details flow into preview
    pg.locator("button.step").first.click(); pg.wait_for_timeout(200)
    pg.fill('#fields input[data-k="job"]', "1140")
    pg.fill('#fields input[data-k="address"]', "28 Talbot Road, Isleworth TW7 7HH")
    pg.wait_for_timeout(300)
    ok("T8 job number in preview", "1140" in pg.inner_text("#paper"))
    ok("T8 address in preview", "Talbot Road" in pg.inner_text("#paper"))

    # T9 persistence across reload
    pg.reload(); pg.wait_for_timeout(900)
    ok("T9 no chooser after reload", not pg.is_visible("#chooser"))
    ok("T9 job number restored", "1140" in pg.inner_text("#paper"))
    ok("T9 EW numbering restored", "EW1" in pg.inner_text("#paper .sched"))

    print(json.dumps([{"r":a,"t":b,"x":c} for a,b,c in R],indent=0))
    print("PAGE ERRORS:", errs[:5])
    b.close()
