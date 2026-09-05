from playwright.sync_api import sync_playwright
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL="file://"+os.path.join(ROOT,"dist","preview.html").replace("\\","/")
R=[]
def ok(n,c,x=""): R.append((("PASS" if c else "FAIL"),n,x))
os.makedirs("dl",exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(); c=b.new_context(viewport={'width':1500,'height':950},accept_downloads=True)
    pg=c.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(800)
    ok("F1 eight types enabled", pg.locator(".tile:not(.soon)").count()==8, str(pg.locator(".tile:not(.soon)").count()))
    pg.click('.tile[data-k="flat"]'); pg.wait_for_timeout(600)
    ok("F1 chip", pg.inner_text("#typename")=="Flat Conversion")
    ok("F2 23 categories", pg.locator("button.step").count()==23, str(pg.locator("button.step").count()))
    names=[n.strip() for n in pg.locator("button.step .st").all_inner_texts()]
    for w in ["Applicability","Separating Walls","Separating Floors","Sound Insulation (Part E)",
              "Drainage & Waste","Water & Sanitary"]:
        ok("F3 category: "+w, w in names)
    empty=[]
    for i in range(23):
        pg.locator("button.step").nth(i).click(); pg.wait_for_timeout(90)
        if pg.locator("#stage .card").count()==0: empty.append(pg.inner_text(".stagehead h2"))
    ok("F4 no empty categories", len(empty)==0, "empty: "+", ".join(empty))
    orph=pg.evaluate("""(()=>{const cs=SPECS.flat.cats;
      return {b:SPECS.flat.buildups.map(x=>buCat(x)).filter(c=>!cs.includes(c)),
              n:SPECS.flat.notes.map(x=>ntCat(x)).filter(c=>!cs.includes(c))};})()""")
    ok("F5 no orphan build-ups", len(orph["b"])==0, str(orph["b"]))
    ok("F5 no orphan notes", len(orph["n"])==0, str(orph["n"]))
    # SW/SF numbering
    pg.locator('button.step:has-text("Separating Walls")').click(); pg.wait_for_timeout(200)
    pg.locator('#stage .card input[data-t="b"]').nth(1).check(); pg.wait_for_timeout(250)
    sched=pg.inner_text("#paper .sched")
    ok("F6 SW refs in schedule", "SW1" in sched and "SW2" in sched, sched.replace("\n"," ")[:80])
    pg.locator('button.step:has-text("Separating Floors")').click(); pg.wait_for_timeout(200)
    ok("F6 SF ref present", "SF1" in pg.inner_text("#paper .sched"))
    # Reg 6 content flows to preview
    ok("F7 Reg 6 applies list in preview", "H6 SOLID WASTE STORAGE" in pg.inner_text("#paper").upper())
    ok("F7 does-not-apply list in preview", "O1 OVERHEATING" in pg.inner_text("#paper").upper())
    ok("F7 43 dB standard in preview", "43 dB" in pg.inner_text("#paper"))
    # PDF
    pg.locator("button.step").nth(2).click(); pg.wait_for_timeout(200)
    pg.evaluate("S.data.job='1111'; S.data.project='Conversion of house into 2 self-contained flats'; renderPaper();")
    pg.wait_for_timeout(300)
    with pg.expect_download(timeout=40000) as d: pg.click("#btnPdf")
    dd=d.value; path=os.path.join(ROOT,"dist","dl")+"/"+dd.suggested_filename; dd.save_as(path)
    ok("F8 flat PDF downloads", os.path.getsize(path)>40000, f"{os.path.getsize(path)} bytes, {dd.suggested_filename}")
    print(json.dumps([{"r":a,"t":b,"x":c} for a,b,c in R])); print("PAGE ERRORS:",errs[:4]); b.close()
