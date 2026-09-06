from playwright.sync_api import sync_playwright
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL="file://"+os.path.join(ROOT,"dist","preview.html").replace("\\","/")
os.makedirs(os.path.join(ROOT,"dist","dl"),exist_ok=True)
R=[]
def ok(n,c,x=""): R.append((("PASS" if c else "FAIL"),n,x))
with sync_playwright() as p:
    b=p.chromium.launch(); c=b.new_context(viewport={'width':1500,'height':1000},accept_downloads=True)
    pg=c.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(800); pg.click('.tile[data-k="extension"]'); pg.wait_for_timeout(500)
    # floor
    pg.locator('button.step:has-text("Ground Floors")').click(); pg.wait_for_timeout(300)
    ok("F1 floor configurator present", pg.locator("#addFloor").count()==1)
    ok("F1 wall configurator absent here", pg.locator("#addWall").count()==0)
    u=pg.inner_text(".uval b").strip(); ok("F2 default 100 TF70 P/A 0.5 clay = 0.16", u=="0.16", u)
    pg.select_option('select[data-cf="pa"]',"1"); pg.wait_for_timeout(250)
    u2=pg.inner_text(".uval b").strip(); ok("F3 P/A 1.0 raises U", float(u2)>float(u), f"{u}->{u2}")
    pg.select_option('select[data-cf="kind"]',"timber"); pg.wait_for_timeout(300)
    ok("F4 timber shows joist controls", pg.locator('select[data-cf="joistDepth"]').count()==1 and pg.locator('select[data-cf="edge"]').count()==0)
    u3=pg.inner_text(".uval b").strip(); ok("F4 suspended timber 100 TF70 fails 0.18", pg.locator(".uval.bad").count()==1, u3)
    pg.select_option('select[data-cf="kind"]',"solid"); pg.select_option('select[data-cf="pa"]',"0.5"); pg.wait_for_timeout(250)
    pg.click("#addFloor"); pg.wait_for_timeout(400)
    ok("F5 floor added and numbered GF", any(t.strip().startswith("GF") for t in pg.locator('#stage .card.on .tag').all_inner_texts()))
    ok("F5 ISO 13370 steps in preview", "Characteristic dimension" in pg.inner_text("#paper"))
    # roof
    pg.locator('button.step:has-text("Roofs")').click(); pg.wait_for_timeout(300)
    ok("R1 roof configurator present", pg.locator("#addRoof").count()==1)
    u=pg.inner_text(".uval b").strip(); ok("R2 default warm deck 150 TR27 = 0.15", u=="0.15", u)
    pg.select_option('select[data-cf="kind"]',"rafter"); pg.wait_for_timeout(300)
    u=pg.inner_text(".uval b").strip(); ok("R3 default rafter 150 K107 + 62.5 K118 = 0.14 (lambda 0.019 verified)", u=="0.14", u)
    pg.select_option('select[data-cf="rThick"]',"100"); pg.select_option('select[data-cf="under"]',"k118_375"); pg.wait_for_timeout(300)
    u=pg.inner_text(".uval b").strip(); ok("R4 old loft spec 100 + 37.5 = 0.21 and FAILS", u=="0.21" and pg.locator(".uval.bad").count()==1, u)
    warn=pg.locator(".cfgwarn").count()
    pg.select_option('select[data-cf="rThick"]',"200"); pg.wait_for_timeout(250)
    ok("R5 over-depth warning shown", pg.locator(".cfgwarn").count()==1 and "exceeds rafter depth" in pg.inner_text(".cfgwarn"))
    pg.select_option('select[data-cf="kind"]',"ceiling"); pg.wait_for_timeout(300)
    u=pg.inner_text(".uval b").strip(); ok("R6 cold roof 100+300 = 0.11", u=="0.11", u)
    pg.click("#addRoof"); pg.wait_for_timeout(400)
    ok("R7 roof added and numbered RF", any(t.strip().startswith("RF") for t in pg.locator('#stage .card.on .tag').all_inner_texts()))
    # both customs coexist, refs distinct
    paper=pg.inner_text("#paper")
    ok("X1 both customs in schedule", "Solid Ground Floor" in paper and "Ceiling Level" in paper)
    ok("X1 working section lists both", paper.upper().count("COMBINED METHOD")>=1 and "Characteristic dimension" in paper)
    with pg.expect_download(timeout=40000) as d: pg.click("#btnPdf")
    dd=d.value; path="dl/fr.pdf"; dd.save_as(path)
    ok("X2 PDF with floor+roof working", os.path.getsize(path)>40000, f"{os.path.getsize(path)} bytes")
    # wall configurator still works alongside
    pg.locator('button.step:has-text("External Walls")').click(); pg.wait_for_timeout(300)
    pg.select_option('select[data-cf="gapLevel"]',"0"); pg.wait_for_timeout(250)
    ok("X3 wall configurator unaffected", pg.inner_text(".uval b").strip()=="0.17")

    # ---- foundations: the configurator appears, and the projection rule bites ----
    pg.locator('button.step:has-text("Foundations")').first.click(); pg.wait_for_timeout(300)
    ok("FD1 foundation configurator present under Foundations",
       pg.locator("#addFound").count()==1 and "foundation" in pg.inner_text(".cfgcard h3").lower(),
       pg.inner_text(".cfgcard h3") if pg.locator(".cfgcard h3").count() else "none")
    ok("FD1 wall configurator absent here", pg.locator("#addWall").count()==0)

    # 600 wide on a 300 wall gives a 150 projection; a 100 thickness must fail
    pg.select_option('select[data-cf="type"]',"strip"); pg.wait_for_timeout(150)
    pg.select_option('select[data-cf="wall"]',"300"); pg.wait_for_timeout(150)
    pg.select_option('select[data-cf="width"]',"600"); pg.wait_for_timeout(150)
    res = pg.evaluate("(()=>{const c={...cfgFD(),wall:300,width:600,thickness:100};"
                      "const r=foundationResult(c);"
                      "return {proj:r.proj, ok:r.ok, failed:r.checks.filter(x=>!x.pass).map(x=>x.n)};})()")
    ok("FD2 projection is 150 on a 600 foundation and a 300 wall", res["proj"]==150, str(res["proj"]))
    ok("FD2 a 100 thickness fails the projection rule", res["ok"] is False, str(res))
    ok("FD2 the failing check names the projection",
       any("projection" in n.lower() for n in res["failed"]), "; ".join(res["failed"]))
    # and 225 passes the same geometry
    okres = pg.evaluate("foundationResult({...cfgFD(),wall:300,width:600,thickness:225,depth:1000,"
                        "ground:'clay_firm',trees:'none',profile:'level',type:'strip'}).ok")
    ok("FD3 a 225 thickness passes the same geometry", okres is True, str(okres))

    # ---- framed walls: the configurator, and stud bridging biting on a dormer cheek ----
    pg.goto(URL); pg.wait_for_timeout(500)
    pg.evaluate("try{localStorage.clear()}catch(e){}"); pg.goto(URL); pg.wait_for_timeout(700)
    pg.click('.tile[data-k="loft"]'); pg.wait_for_timeout(600)
    pg.locator('button.step:has-text("Dormer Construction (Walls)")').first.click(); pg.wait_for_timeout(400)
    ok("FR1 framed wall configurator present on a dormer cheek category",
       pg.locator("#addFrame").count()==1 and "framed wall" in pg.inner_text(".cfgcard h3").lower(),
       pg.inner_text(".cfgcard h3") if pg.locator(".cfgcard h3").count() else "none")
    ok("FR1 it defaults to a dormer cheek at 400mm centres",
       pg.evaluate("cfgFR().use")=="cheek" and pg.evaluate("cfgFR().spacing")==400,
       str(pg.evaluate("[cfgFR().use, cfgFR().spacing]")))

    # 140mm K112 between 38x140 studs: the stated library figure is 0.18, but the studs bridge
    fr = pg.evaluate("""(()=>{const b={insulation:'k112',thickness:140,studWidth:38,studDepth:140,
        sheathing:'ply18',lining:'none',void:0,gapLevel:1};
        const at=(o)=>UC.frame({...b,...o});
        return {c400:at({spacing:400}).U, c600:at({spacing:600}).U,
                lined:at({spacing:400,lining:'k118_375'}).U,
                nogap:at({spacing:400,gapLevel:0}).U,
                f400:at({spacing:400}).f};})()""")
    ok("FR2 timber fraction is 9.5% at 400mm centres", abs(fr["f400"]-0.095)<0.001, str(fr["f400"]))
    ok("FR2 the cheek as the library states it does NOT meet 0.18", fr["c400"] > 0.18,
       f"{fr['c400']:.3f}")
    ok("FR2 the library figure is reproduced only without the air-gap correction",
       abs(fr["nogap"]-0.185) < 0.005, f"{fr['nogap']:.3f}")
    ok("FR3 a 37.5mm K118 lining brings it back inside 0.18", fr["lined"] <= 0.18, f"{fr['lined']:.3f}")
    ok("FR3 600mm centres alone is not enough", fr["c600"] > 0.18, f"{fr['c600']:.3f}")

    # the cladding is outside a ventilated cavity, so it must not change the U-value
    same = pg.evaluate("""(()=>{const b={insulation:'k112',thickness:140,studWidth:38,studDepth:140,
        spacing:600,sheathing:'osb9',lining:'none',void:0,gapLevel:1};
        return [UC.frame({...b,outer:'brick'}).U, UC.frame({...b,outer:'timber'}).U];})()""")
    ok("FR4 the external finish does not change the U-value", abs(same[0]-same[1]) < 1e-9, str(same))

    pg.click("#addFrame"); pg.wait_for_timeout(500)
    ok("FR5 the framed wall is added and numbered EW",
       "EW1" in pg.inner_text("#paper .sched"), pg.inner_text("#paper .sched").replace("\n"," ")[:90])
    ok("FR5 the entry carries the timber-fraction note",
       "Noggins, head and sole plates" in pg.inner_text("#paper"))

    print(json.dumps([{"r":a,"t":b,"x":c} for a,b,c in R])); print("PAGE ERRORS:",errs[:4]); b.close()
