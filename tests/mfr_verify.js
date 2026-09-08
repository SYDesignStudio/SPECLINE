/* Every build-up with an mf descriptor must reproduce its own stated U-value through UC, every
   product phrase it names must exist in its clause, and every manufacturer must run across it
   without error. build.py runs this after the structural check; it exits non-zero on a problem.

     node tests/mfr_verify.js          summary and problems only
     node tests/mfr_verify.js all      every substitution, one line each */
const fs=require("fs"), path=require("path");
const ROOT=path.dirname(__dirname);
const rd=f=>fs.readFileSync(path.join(ROOT,f),"utf8");
const UC=require(path.join(ROOT,"src/ucalc.js"));
["src/ucalc2.js","src/ucalc3.js","src/ucalc4.js"].forEach(f=>new Function("UC", rd(f))(UC));
global.UC=UC; global.S={type:null,data:{},ovr:{}};
const M=new Function("UC","S","module", rd("src/mfr.js")+";return module.exports;")(UC,S,{exports:{}});
const SPECS=new Function(rd("dist/specdata.js")+";return SPECS;")();
const all=process.argv[2]==="all";
let bad=0, n=0; const summary={};
for(const k in SPECS) for(const b of SPECS[k].buildups){
  if(!b.mf) continue; n++;
  const txt=b.p.join("\n"), d=b.mf;
  d.s.forEach(s=>{ if(!txt.includes(s.f)){ console.log("PHRASE NOT FOUND", k, b.t, "::", s.f); bad++; } if(s.over&&!txt.includes(s.over)){ console.log("OVER NOT FOUND",k,b.t); bad++; } });
  const stated=parseFloat((b.u||"").match(/\d\.\d\d/)||[NaN]);
  let p={...d.p};
  if(d.k==="basementWall" && String(p.wallIns).startsWith("__")){ const prod=M.mfrTable(d.s[0].r).find(x=>x.id===d.s[0].id); p.wallProduct={n:prod.n,k:prod.k}; p.wallIns="k103"; }
  const r=M.mfrRun(d.k, p);
  const ok=Math.abs(r.U-stated)<0.0051;
  if(!ok){ console.log(`DIFF  ${k.padEnd(9)} ${b.t.slice(0,60).padEnd(60)} stated ${stated} calc ${r.U.toFixed(3)}`); bad++; }
  else if(all) console.log(`ok    ${k.padEnd(9)} ${b.t.slice(0,60).padEnd(60)} stated ${stated} calc ${r.U.toFixed(3)} lim ${d.lim}`);
  for(const m of M.MFRS){
    if(m.id==="kingspan") continue;
    summary[m.id]=summary[m.id]||{kept:0,ok:0,short:0,up:0};
    let s; try{ s=M.mfrSubstitute(b, m.id); }catch(e){ console.log("ERROR", k, b.t, m.id, e.message); bad++; continue; }
    if(!s||!s.changed){ summary[m.id].kept++; if(all) console.log("      "+m.id.padEnd(9)+" kept"); continue; }
    if(s.info.ok) summary[m.id].ok++; else summary[m.id].short++;
    if(s.info.swaps.some(x=>/increased/.test(x))) summary[m.id].up++;
    if(!/\d\.\d\d W\/m²K/.test(s.b.u)||!(s.b.calc.result.U>0)){ console.log("BAD RESULT", k, b.t, m.id); bad++; }
    if(all) console.log("      "+m.id.padEnd(9)+(s.info.ok?" ok    ":" SHORT ")+s.info.U.toFixed(3)+"  "+s.info.swaps.join("; ").slice(0,150));
    const left=s.b.p.slice(0,-1).join("\n"); d.s.forEach(x=>{ if(left.includes(x.f) && !s.info.kept.length){ console.log("PHRASE SURVIVED", k, b.t, m.id, x.f); bad++; } });
  }
}
console.log(`mfr: ${n} descriptors reproduce their clause; ${bad} problems; `+Object.keys(summary).map(k=>`${k} ok ${summary[k].ok}/short ${summary[k].short}/kept ${summary[k].kept}`).join(", "));
if(bad) process.exit(1);
