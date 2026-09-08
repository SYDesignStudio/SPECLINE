"""Suite 8 — insulation manufacturer substitution and the Part M category (8 September 2026).

The library is written with Kingspan. A job carries a default manufacturer and a build-up can
override it; the substituted build-up is recalculated through UC, its clause rewritten, and the
working carried into section 4.0. A new-build job carries an M4 category that decides which
Access (Part M) note is on."""
from playwright.sync_api import sync_playwright
import json, os, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL="file://"+os.path.join(ROOT,"dist","preview.html").replace("\\","/")
R=[]
def ok(n,c,extra=""): R.append((("PASS" if c else "FAIL"),n,extra))

with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':1500,'height':980},accept_downloads=True)
    pg=ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(900)
    pg.evaluate("try{localStorage.clear()}catch(e){}")
    pg.goto(URL); pg.wait_for_timeout(700)
    pg.click('.tile[data-k="newbuild"]'); pg.wait_for_timeout(600)

    # M1 job record carries the two selects, defaulting to Kingspan and M4(1)
    ok("M1 manufacturer select on the job record", pg.locator('#fields select[data-k="mfr"]').count()==1)
    ok("M1 Part M select on a new build job", pg.locator('#fields select[data-k="m4"]').count()==1)
    ok("M1 defaults are Kingspan and M4(1)", pg.evaluate("S.data.mfr")=="kingspan" and pg.evaluate("S.data.m4")=="1")
    # M2 only the M4(1) note is on; the cover says so
    st=pg.evaluate("(()=>{const r={on:[],off:[]}; spec().notes.forEach((n,i)=>{ if(n.m4) (S.notes[i]?r.on:r.off).push(n.m4); }); return r;})()")
    ok("M2 M4(1) note on, M4(2) and M4(3) off", st["on"]==["1"] and sorted(st["off"])==["2","3"], json.dumps(st))
    paper=pg.inner_text("#paper")
    ok("M2 cover carries the access category", "M4(1) Visitable dwelling" in paper)
    ok("M2 Part B carries M4(1) and not M4(3)", "CATEGORY M4(1) VISITABLE DWELLING" in paper.upper() and "WHEELCHAIR USER DWELLING" not in paper.upper())
    # M3 switching to M4(3) swaps the note
    pg.select_option('#fields select[data-k="m4"]', "3"); pg.wait_for_timeout(300)
    paper=pg.inner_text("#paper")
    ok("M3 M4(3) note on after the switch", "CATEGORY M4(3) WHEELCHAIR USER DWELLING" in paper.upper() and "CATEGORY M4(1) VISITABLE DWELLING" not in paper.upper())
    ok("M3 cover updates", "M4(3) Wheelchair user dwelling" in paper)
    ok("M3 M4(3) note carries the wheelchair storage space", "1100mm deep × 1700mm wide" in paper)
    pg.select_option('#fields select[data-k="m4"]', "1"); pg.wait_for_timeout(200)

    # M4 the library is unchanged with Kingspan: no build-up carries a calc, none is rewritten
    n_calc=pg.evaluate("spec().buildups.map(mfrApply).filter(b=>b.calc).length")
    ok("M4 Kingspan leaves every library build-up as written", n_calc==0, str(n_calc))
    ok("M4 65 build-ups carry a descriptor across the library", pg.evaluate("Object.keys(SPECS).reduce((n,k)=>n+SPECS[k].buildups.filter(b=>b.mf).length,0)")==65)

    # M5 Celotex as the job default: the full fill wall is recalculated and rewritten
    base=pg.evaluate("(()=>{const i=spec().buildups.findIndex(b=>b.t==='Full Fill Cavity Wall'); const b=allBU()[i]; return {i, u:b.u, tgt:b.tgt, n:b.p.length};})()")
    pg.select_option('#fields select[data-k="mfr"]', "celotex"); pg.wait_for_timeout(300)
    sub=pg.evaluate("(()=>{const i=%d; const b=allBU()[i]; return {u:b.u, tgt:b.tgt, n:b.p.length, calc:!!b.calc, U:b.calc&&b.calc.result.U, last:b.p[b.p.length-1], txt:b.p.join(' '), info:b.mfrInfo};})()" % base["i"])
    ok("M5 Celotex build-up carries a calc", sub["calc"])
    ok("M5 schedule figure is the calculated one", sub["u"]==("%.2f W/m²K" % sub["U"]), sub["u"])
    ok("M5 the Kingspan product is gone from the clause", "Kingspan Kooltherm K106" not in sub["txt"].replace(sub["last"],""))
    ok("M5 Thermaclass named in the clause", "Thermaclass Cavity Wall 21" in sub["txt"])
    ok("M5 closing paragraph names the manufacturer", sub["last"].startswith("Insulation manufacturer: Celotex"))
    ok("M5 thickness stepped up to meet 0.18", sub["info"]["ok"] and "increased from 100mm to 115mm" in sub["last"], sub["last"][:160])
    ok("M5 cavity widened with it", "cavity widened from 100mm to 115mm" in sub["last"] and "115mm cavity" in sub["txt"])
    ok("M5 calculates-at sentence rewritten", ("calculates at %.2f W/m²K" % sub["U"]) in sub["txt"])
    ok("M5 U meets the target", sub["U"]<=0.18+1e-9, str(sub["U"]))
    # card shows the chip and the override select
    pg.evaluate("setStep(cats().findIndex(isWallCat))"); pg.wait_for_timeout(300)
    card=pg.locator('#stage .card:has-text("Full Fill Cavity Wall")').first
    ok("M5 card shows the manufacturer row", card.locator("select[data-mo]").count()==1)
    ok("M5 card chip says recalculated", "RECALCULATED" in card.inner_text().upper())
    ok("M5 no Remove button on a library build-up", card.locator(".rm").count()==0)
    ok("M5 layer bar drawn on the card", card.locator(".cfgbar").count()==1)

    # M6 per-build-up override back to Kingspan
    card.locator("select[data-mo]").select_option("kingspan"); pg.wait_for_timeout(300)
    back=pg.evaluate("(()=>{const b=allBU()[%d]; return {u:b.u, calc:!!b.calc};})()" % base["i"])
    ok("M6 override restores the library build-up", back["u"]==base["u"] and not back["calc"], json.dumps(back))
    ok("M6 override is in the snapshot", pg.evaluate("snapshot().ovr[%d]" % base["i"])=="kingspan")
    card=pg.locator('#stage .card:has-text("Full Fill Cavity Wall")').first
    card.locator("select[data-mo]").select_option(""); pg.wait_for_timeout(300)
    ok("M6 clearing the override returns to the job default", pg.evaluate("!!allBU()[%d].calc" % base["i"]))

    # M7 the working section appears in the preview and the review passes the build-up
    pg.evaluate("S.sel=[%d]; renderSteps(); renderStage(); renderPaper();" % base["i"]); pg.wait_for_timeout(300)
    paper=pg.inner_text("#paper")
    ok("M7 section 4.0 carries the substituted wall", "U-value calculations" in paper and "Thermaclass" in paper)
    pg.evaluate("setStep('review')"); pg.wait_for_timeout(300)
    rev=pg.inner_text("#stage")
    ok("M7 review names the manufacturer", "Celotex" in rev and "Substituted and recalculated" in rev)
    ok("M7 review passes the recalculated wall", re.search(r"0\.\d\d against 0\.18", rev) is not None)

    # M8 a manufacturer with no product for the role keeps Kingspan and says so
    pg.evaluate("S.data.mfr='rockwool'; renderPaper();"); pg.wait_for_timeout(200)
    r=pg.evaluate("(()=>{const i=spec().buildups.findIndex(b=>/Warm Deck Flat Roof/.test(b.t)); const b=allBU()[i]; return {calc:!!b.calc, last:b.p[b.p.length-1]};})()")
    ok("M8 ROCKWOOL keeps the flat roof board", not r["calc"] and "no verified ROCKWOOL product" in r["last"], r["last"][:120])
    # M9 a product that cannot reach the target is flagged, not hidden
    # no library build-up falls short any more, so drive the NOTE path with an unreachable target
    f=pg.evaluate("(()=>{const b=SPECS.loft.buildups.find(b=>b.t==='Hip to Gable — New Gable Wall'); const c={...b, mf:{...b.mf, lim:0.10}}; const r=mfrSubstitute(c,'knauf'); return {ok:r.info.ok, last:r.b.p[r.b.p.length-1]};})()")
    ok("M9 a shortfall is a NOTE that says so", f["ok"] is False and f["last"].startswith("NOTE — Insulation manufacturer") and "does not meet the target" in f["last"])

    # M10 every manufacturer runs across every descriptor without error
    tot=pg.evaluate("""(()=>{let n=0,e=[]; Object.keys(SPECS).forEach(k=>SPECS[k].buildups.forEach(b=>{ if(!b.mf) return;
        MFRS.forEach(m=>{ try{ const r=mfrSubstitute(b,m.id); if(r&&r.changed){ n++; if(!(r.b.calc.result.U>0)) e.push(k+'/'+b.t+'/'+m.id); if(!/W\\/m²K/.test(r.b.u)) e.push('u:'+b.t); } }catch(x){ e.push(k+'/'+b.t+'/'+m.id+': '+x.message); } }); })); return {n,e};})()""")
    ok("M10 every substitution runs", not tot["e"] and tot["n"]>200, json.dumps(tot["e"][:5])+" n=%d" % tot["n"])

    # M11 a saved job reloads with its manufacturer, category and overrides
    pg.evaluate("S.type='newbuild'; S.data.mfr='unilin'; S.data.m4='2'; applyM4(); S.ovr={3:'recticel'}; save();"); pg.wait_for_timeout(900)
    pg.goto(URL); pg.wait_for_timeout(900)
    got=pg.evaluate("({mfr:S.data.mfr, m4:S.data.m4, ovr:S.ovr, on:spec().notes.filter((n,i)=>n.m4&&S.notes[i]).map(n=>n.m4)})")
    ok("M11 reload keeps manufacturer, category and override", got["mfr"]=="unilin" and got["m4"]=="2" and got["ovr"]=={"3":"recticel"} and got["on"]==["2"], json.dumps(got))

    ok("M12 no page errors", not errs, "; ".join(errs)[:300])
    b.close()

print(json.dumps([{"r":a,"t":b,"x":c} for a,b,c in R],indent=0))
print("PAGE ERRORS:", errs[:5])
