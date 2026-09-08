from playwright.sync_api import sync_playwright
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL="file://"+os.path.join(ROOT,"dist","preview.html").replace("\\","/")
R=[]
def ok(n,c,x=""): R.append((("PASS" if c else "FAIL"),n,x))
def calc(pg,label):
    """open a calculator tab in the current category — the calculators sit behind tabs"""
    t=pg.locator('.stab:has-text("%s")' % label)
    if t.count(): t.first.click(); pg.wait_for_timeout(250)
    return t.count()
os.makedirs("dl",exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(); c=b.new_context(viewport={'width':1500,'height':1000},accept_downloads=True)
    pg=c.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(800); pg.click('.tile[data-k="extension"]'); pg.wait_for_timeout(500)
    pg.locator('button.step:has-text("External Walls")').click(); pg.wait_for_timeout(300)
    # External Walls carries two calculators, a cavity wall and a framed wall, each behind its own
    # tab. Their selects are namespaced (data-cf="cavity" vs data-cf="fr_*") so neither suite can
    # pick up the other's, and only one renders at a time.
    tabs=[t.strip().split("\n")[0] for t in pg.locator(".stab").all_inner_texts()]
    ok("C1 the category offers the library and both calculators as tabs",
       tabs==["Library","Cavity wall calculator","Framed wall calculator"], str(tabs))
    ok("C1 the library list is what opens first",
       pg.locator("#addWall").count()==0 and pg.locator('#stage .card input[data-t="b"]').count()>0)
    calc(pg,"Cavity wall")
    ok("C1 the cavity tab opens the cavity calculator alone",
       pg.locator("#addWall").count()==1 and pg.locator("#addFrame").count()==0 and pg.locator(".cfgcard").count()==1,
       str(pg.locator(".cfgcard").count()))
    ok("C1 no library cards behind a calculator",
       pg.locator('#stage .card input[data-t="b"]').count()==0)
    ok("C1 the two do not share select names",
       pg.locator('select[data-cf="insulation"]').count()==1 and pg.locator('select[data-cf="fr_insulation"]').count()==0)
    calc(pg,"Framed wall")
    ok("C1 the framed tab opens the framed calculator alone",
       pg.locator("#addFrame").count()==1 and pg.locator("#addWall").count()==0 and
       pg.locator('select[data-cf="fr_insulation"]').count()==1)
    ok("C1 no calculator tab in Roofs for a wall", (pg.locator('button.step:has-text("Roofs")').click(), pg.wait_for_timeout(200),
       pg.locator('.stab:has-text("Cavity wall")').count()==0)[2])
    pg.locator('button.step:has-text("External Walls")').click(); pg.wait_for_timeout(300)
    calc(pg,"Cavity wall")
    CAV = ".cfgcard:has(#addWall) "
    u=pg.inner_text(CAV+".uval b").strip()
    ok("C2 default (90 K106 / 0.15 block, level 1) reads 0.18", u=="0.18", u)
    ok("C2 default status = pass at 0.18 limit", pg.locator(CAV+".uval.ok").count()==1)
    # change gap level to 0 -> 0.17
    pg.select_option('select[data-cf="gapLevel"]',"0"); pg.wait_for_timeout(250)
    u0=pg.inner_text(CAV+".uval b").strip(); ok("C3 level 0 -> 0.17 (matches Kingspan)", u0=="0.17", u0)
    # switch to Dritherm 37 -> fails limit
    pg.select_option('select[data-cf="insulation"]',"dt37"); pg.wait_for_timeout(250)
    ok("C4 Dritherm 37 @100mm fails 0.18", pg.locator(CAV+".uval.bad").count()==1, pg.inner_text(CAV+".uval b"))
    # thickness options follow product
    ths=[o.get_attribute("value") for o in pg.locator('select[data-cf="thickness"] option').all()]
    ok("C4 thickness list follows product", ths==["50","65","75","85","100","125","150"], str(ths))
    # partial fill switches product list and computes residual
    pg.select_option('select[data-cf="fill"]',"partial"); pg.wait_for_timeout(250)
    prods=[o.get_attribute("value") for o in pg.locator('select[data-cf="insulation"] option').all()]
    ok("C5 partial fill shows partial products only", all(x in ["k108","cw4000","xtcw","ecopf"] for x in prods), str(prods))
    pg.select_option('select[data-cf="cavity"]',"125"); pg.select_option('select[data-cf="thickness"]',"75"); pg.wait_for_timeout(250)
    ok("C5 residual cavity 50mm shown in working", "Residual cavity 50mm" in pg.inner_html("table.wk"))
    # working table present and consistent
    pg.click(".working summary"); pg.wait_for_timeout(150)
    wk=pg.inner_text("table.wk")
    ok("C6 working shows combined method", "combined method" in wk and "upper / lower" in wk)
    # add as build-up -> back to K106 default first
    pg.select_option('select[data-cf="fill"]',"full"); pg.wait_for_timeout(200)
    pg.select_option('select[data-cf="insulation"]',"k106"); pg.select_option('select[data-cf="thickness"]',"90"); pg.select_option('select[data-cf="cavity"]',"100"); pg.wait_for_timeout(250)
    before=pg.evaluate("allBU().length")
    pg.click("#addWall"); pg.wait_for_timeout(400)
    ok("C7 adding returns to the library so the new card is visible", pg.evaluate("S.tab")=="lib")
    after=pg.evaluate("allBU().length")
    ok("C7 add creates a new build-up card", after==before+1, f"{before}->{after}")
    ok("C7 new build-up is selected and numbered", pg.locator('#stage .card.on .tag:not(.off)').count()>=1)
    tags=[t.strip() for t in pg.locator('#stage .card.on .tag').all_inner_texts()]
    ok("C7 sequential EW numbering", "EW1" in tags and "EW2" in tags, str(tags))
    ok("C7 custom card has Remove", pg.locator("#stage .card .rm").count()==1)
    paper=pg.inner_text("#paper")
    ok("C8 U-value working appears in preview", "U-VALUE CALCULATIONS" in paper.upper() and "upper / lower" in paper)
    ok("C8 spec text uses our wording", "built up as" in paper and "comprise of" not in paper.lower())
    # persistence of custom
    pg.reload(); pg.wait_for_timeout(800)
    ok("C9 custom build-up survives reload", pg.locator("#stage .card .rm").count()==1 or "U-VALUE CALCULATIONS" in pg.inner_text("#paper").upper())
    # PDF with working
    with pg.expect_download(timeout=40000) as d: pg.click("#btnPdf")
    dd=d.value; path="dl/cfg.pdf"; dd.save_as(path)
    ok("C10 PDF generates with custom build-up", os.path.getsize(path)>40000, f"{os.path.getsize(path)} bytes")
    # remove
    pg.locator('button.step:has-text("External Walls")').click(); pg.wait_for_timeout(300)
    pg.click("#stage .card .rm"); pg.wait_for_timeout(300)
    ok("C11 remove deletes custom build-up", pg.locator("#stage .card .rm").count()==0)
    print(json.dumps([{"r":a,"t":b,"x":c} for a,b,c in R])); print("PAGE ERRORS:",errs[:4]); b.close()
