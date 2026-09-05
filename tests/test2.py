from playwright.sync_api import sync_playwright
import json, os, glob
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL="file://"+os.path.join(ROOT,"dist","preview.html").replace("\\","/")
R=[]
def ok(n,c,extra=""): R.append((("PASS" if c else "FAIL"),n,extra))
os.makedirs("dl",exist_ok=True)
for f in glob.glob("dl/*"): os.remove(f)

with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':1500,'height':980},accept_downloads=True)
    pg=ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(800)
    pg.click('.tile[data-k="loft"]'); pg.wait_for_timeout(600)

    ok("L1 21 loft categories", pg.locator("button.step").count()==21, str(pg.locator("button.step").count()))
    ok("L1 chip says Loft Conversion", pg.inner_text("#typename")=="Loft Conversion")
    names=[n.strip() for n in pg.locator("button.step .st").all_inner_texts()]
    for want in ["Hip to Gable","Dormer Construction (Walls)","Dormer Construction (Roof)",
                 "Dwarf / Ashlar Walls","Upgrading Existing External Wall","Upgrading Existing Party Wall",
                 "Upgrading Existing Roof","Loft Floor","Sound Insulation"]:
        ok("L2 category present: "+want, want in names)

    empty=[]
    for i in range(21):
        pg.locator("button.step").nth(i).click(); pg.wait_for_timeout(90)
        if pg.locator("#stage .card").count()==0: empty.append(pg.inner_text(".stagehead h2"))
    ok("L3 no empty loft categories", len(empty)==0, "empty: "+", ".join(empty))

    # every buildup and note reachable exactly once
    counts=pg.evaluate("""(()=>{
      const bs=SPECS.loft.buildups.map(b=>buCat(b)), ns=SPECS.loft.notes.map(n=>ntCat(n));
      const cs=SPECS.loft.cats;
      return {orphanB:bs.filter(c=>!cs.includes(c)), orphanN:ns.filter(c=>!cs.includes(c))};
    })()""")
    ok("L4 no orphan build-ups", len(counts["orphanB"])==0, str(counts["orphanB"]))
    ok("L4 no orphan notes", len(counts["orphanN"])==0, str(counts["orphanN"]))

    # PDF from loft
    pg.click("#stepJob"); pg.wait_for_timeout(200)
    pg.fill('#fields input[data-k="job"]',"1141")
    pg.fill('#fields input[data-k="project"]',"Rear dormer loft conversion")
    pg.wait_for_timeout(250)
    with pg.expect_download(timeout=25000) as di:
        pg.click("#btnPdf")
    d=di.value; path=os.path.join(ROOT,"dist","dl")+"/"+d.suggested_filename; d.save_as(path)
    ok("P1 loft PDF downloads", os.path.exists(path) and os.path.getsize(path)>20000, f"{os.path.getsize(path)} bytes, {d.suggested_filename}")

    # switch to extension, all notes off, no build-ups -> still generates
    pg.click("#btnType"); pg.wait_for_timeout(300)
    pg.click('.tile[data-k="extension"]'); pg.wait_for_timeout(500)
    pg.evaluate("S.sel=[]; Object.keys(S.notes).forEach(k=>S.notes[k]=false); renderStage(); renderSteps(); renderPaper();")
    pg.wait_for_timeout(300)
    with pg.expect_download(timeout=25000) as di2:
        pg.click("#btnPdf")
    d2=di2.value; p2="dl/empty.pdf"; d2.save_as(p2)
    ok("P2 empty spec still generates", os.path.exists(p2) and os.path.getsize(p2)>5000, f"{os.path.getsize(p2)} bytes")

    # full extension spec
    pg.evaluate("defaults(); S.sel=SPECS.extension.buildups.map((b,i)=>i); renderStage(); renderSteps(); renderPaper();")
    pg.wait_for_timeout(400)
    with pg.expect_download(timeout=30000) as di3:
        pg.click("#btnPdf")
    d3=di3.value; p3="dl/full.pdf"; d3.save_as(p3)
    ok("P3 full extension PDF", os.path.exists(p3) and os.path.getsize(p3)>30000, f"{os.path.getsize(p3)} bytes")

    # narrow viewport
    pg.set_viewport_size({"width":900,"height":900}); pg.wait_for_timeout(400)
    ok("V1 preview hidden when narrow", not pg.is_visible(".viewer"))
    pg.click("#btnPrev"); pg.wait_for_timeout(400)
    ok("V1 preview toggle shows it", pg.is_visible(".viewer"))
    pg.click("#btnPrev"); pg.set_viewport_size({"width":1500,"height":980})

    print(json.dumps([{"r":a,"t":b,"x":c} for a,b,c in R]))
    print("PAGE ERRORS:", errs[:5])
    b.close()
