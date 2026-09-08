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
NEW=[("garage","Garage Conversion",18),("newbuild","New Build",28),("nbflats","New Build Flats",30),("basement","Basement Conversion",21),("garagebld","Garage Build",16)]
with sync_playwright() as p:
    b=p.chromium.launch(); c=b.new_context(viewport={'width':1500,'height':950},accept_downloads=True)
    pg=c.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    for k,name,ncat in NEW:
        pg.goto(URL); pg.wait_for_timeout(700)
        pg.evaluate("try{localStorage.clear()}catch(e){}"); pg.goto(URL); pg.wait_for_timeout(700)
        pg.click(f'.tile[data-k="{k}"]'); pg.wait_for_timeout(600)
        ok(f"{k}: chip", pg.inner_text("#typename")==name, pg.inner_text("#typename"))
        n=pg.locator("button.step").count(); ok(f"{k}: {ncat} categories", n==ncat, str(n))
        empty=[]
        for i in range(n):
            pg.locator("button.step").nth(i).click(); pg.wait_for_timeout(80)
            if pg.locator("#stage .card").count()==0: empty.append(pg.inner_text(".stagehead h2"))
        ok(f"{k}: no empty categories", len(empty)==0, ", ".join(empty))
        orph=pg.evaluate(f"""(()=>{{const cs=SPECS.{k}.cats;
          return {{b:SPECS.{k}.buildups.map(x=>buCat(x)).filter(c=>!cs.includes(c)),
                  n:SPECS.{k}.notes.map(x=>ntCat(x)).filter(c=>!cs.includes(c))}};}})()""")
        ok(f"{k}: no orphans", len(orph["b"])+len(orph["n"])==0, str(orph))
        # select everything then PDF
        pg.evaluate("S.sel=allBU().map((_,i)=>i); S.notes={}; spec().notes.forEach((_,i)=>S.notes[i]=true); S.data.job='9'+String(S.type.length); renderSteps(); renderStage(); renderPaper(); save();")
        pg.wait_for_timeout(400)
        sched=pg.inner_text("#paper .sched")
        ok(f"{k}: schedule numbered per group", all(x in sched for x in {"garage":["GF1","GF3","EW1","EW4","IW1","RF1","RF3"],"newbuild":["EW1","EW3","SW1","IW1","IW2","GF1","GF2","IF1","RF1","RF3"],"nbflats":["EW1","EW2","SW1","SW2","SF1","SF2","IW1","GF1","RF1","RF2"],"basement":["BW1","BW2","BF1","BF2","IF1"],"garagebld":["GF1","GF2","EW1","EW3","SW1","RF1","RF3"]}[k]), sched.replace("\n"," ")[:120])
        paper=pg.inner_text("#paper")
        key={"garage":"Regulation 23","newbuild":"Dwelling Emission Rate","nbflats":"Regulation 38","basement":"BS 8102","garagebld":"Class 6"}[k]
        ok(f"{k}: key content in preview", key in paper, key)
        r=pg.evaluate("(()=>{try{const d=buildPdf(); return 'ok '+d.getNumberOfPages()}catch(e){return 'ERR '+e.message+' @ '+(e.stack||'').split('\\n')[1]}})()")
        print(k, r, errs[-2:])
        try:
            with pg.expect_download(timeout=30000) as d: pg.click("#btnPdf")
            dd=d.value; path=os.path.join(ROOT,"dist","dl")+"/"+dd.suggested_filename; dd.save_as(path)
            ok(f"{k}: PDF downloads", os.path.getsize(path)>60000, f"{os.path.getsize(path)} bytes, {dd.suggested_filename}")
        except Exception as e: ok(f"{k}: PDF downloads", False, r+" / "+str(e)[:80])
    # basement configurator
    pg.goto(URL); pg.wait_for_timeout(500); pg.evaluate("try{localStorage.clear()}catch(e){}"); pg.goto(URL); pg.wait_for_timeout(700)
    pg.click('.tile[data-k="basement"]'); pg.wait_for_timeout(500)
    pg.locator('button.step:has-text("Basement Floors")').click(); pg.wait_for_timeout(300)
    ok("B1 the basement calculator is offered as a tab", calc(pg,"Basement calculator")==1)
    ok("B1 basement configurator present", pg.locator("#addFloor").count()==1 and "heated basement" in pg.inner_text(".cfgcard h3").lower(), pg.inner_text(".cfgcard h3") if pg.locator(".cfgcard h3").count() else "none")
    u=pg.inner_text(".uval b").strip(); ok("B2 default 100 K103 floor + 100 wall, 2.7m, P/A 0.5 ≈ 0.13", u in ("0.13","0.12"), u)
    pg.select_option('select[data-cf="depth"]',"1.5"); pg.wait_for_timeout(300)
    u2=pg.inner_text(".uval b").strip(); ok("B3 shallower basement raises U", float(u2)>float(u), f"{u}->{u2}")
    pg.click("#addFloor"); pg.wait_for_timeout(400)
    ok("B4 BF build-up added", "Heated Basement" in pg.inner_text("#paper .sched"), pg.inner_text("#paper .sched").replace("\n"," ")[:200])
    ok("B5 ISO 13370 basement steps in preview", "Below-ground wall U_bw" in pg.inner_text("#paper"))
    with pg.expect_download(timeout=60000) as d: pg.click("#btnPdf")
    dd=d.value; path=os.path.join(ROOT,"dist","dl")+"/"+dd.suggested_filename; dd.save_as(path)
    ok("B6 PDF with basement working", os.path.getsize(path)>60000, f"{os.path.getsize(path)} bytes")
    # roofs configurator should not appear under "Additional Notes for Walls & Roofs" (new build)
    pg.goto(URL); pg.wait_for_timeout(500); pg.evaluate("try{localStorage.clear()}catch(e){}"); pg.goto(URL); pg.wait_for_timeout(700)
    pg.click('.tile[data-k="newbuild"]'); pg.wait_for_timeout(500)
    pg.locator('button.step:has-text("Additional Notes for Walls")').click(); pg.wait_for_timeout(300)
    ok("N1 no roof calculator under Additional Notes",
       pg.locator('.stab:has-text("Roof calculator")').count()==0 and pg.locator("#addRoof").count()==0)
    pg.locator('button.step:has-text("Roofs")').first.click(); pg.wait_for_timeout(300)
    calc(pg,"Roof calculator")
    ok("N2 roof configurator under Roofs", pg.locator("#addRoof").count()==1)
    pg.locator('button.step:has-text("Ground Floors")').click(); pg.wait_for_timeout(300)
    calc(pg,"Ground floor calculator")
    ok("N3 ground floor configurator is solid kind (not basement)", "ground floor" in pg.inner_text(".cfgcard h3").lower(), pg.inner_text(".cfgcard h3"))
    print(json.dumps([{"r":a,"t":b,"x":c} for a,b,c in R])); print("PAGE ERRORS:",errs[:4]); b.close()
