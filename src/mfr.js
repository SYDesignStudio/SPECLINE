/* ===== Insulation manufacturer substitution (8 September 2026) =====

   The library is written with Kingspan products. A practice may prefer another manufacturer,
   so a job carries a default manufacturer (S.data.mfr) and any build-up may override it
   (S.ovr[i]). A library build-up that carries an `mf` descriptor — the UC calculation that
   reproduces its stated figure, and the phrases in its clause that name the product — is
   re-run with the chosen manufacturer's product for the same role:

   - the product swaps at the same thickness; where that misses the target the thickness is
     stepped up through the product's OWN published thicknesses until it meets, and the cavity,
     stud or rafter depth that has to grow with it grows, and the clause says so;
   - the U-value in the clause, the schedule figure and the target line are rewritten from the
     calculation, and the working is carried into section 4.0 exactly as a configured
     build-up's is — never a figure typed in;
   - a manufacturer with no verified product for a role keeps the Kingspan product and says so.

   Every product here has a verified conductivity and thickness list (reference/FACTS.md).
   Kingspan itself never substitutes: the library figure stands as written. */

const MFRS = [
 {id:"kingspan", n:"Kingspan", short:"Kingspan"},
 {id:"celotex",  n:"Celotex (Soprema SOPRATHERM)", short:"Celotex", cavfull:"tc21", cavpart:"cw4000", floor:"ga4000", rafter:"ga4000r", flat:"xr4000f", frame:"ga4000f", lining:"pl4000"},
 {id:"unilin",   n:"Unilin (formerly Xtratherm)", short:"Unilin", cavfull:"ctpir", cavpart:"xtcw", floor:"xtuf", rafter:"xtpr", flat:"xtfr", frame:"xtprf"},
 {id:"ecotherm", n:"EcoTherm", short:"EcoTherm", cavfull:"ecoff", cavpart:"ecopf", floor:"ecov", rafter:"ecovr", frame:"ecovf"},
 {id:"recticel", n:"Recticel", short:"Recticel", cavfull:"ewplus", floor:"egp", rafter:"egpr", frame:"egpf"},
 {id:"knauf",    n:"Knauf Insulation (glass mineral wool, cavity walls only)", short:"Knauf", cavfull:"dt32"},
 {id:"rockwool", n:"ROCKWOOL (stone wool, cavity walls only)", short:"ROCKWOOL", cavfull:"rwff"}
];
const MFR_ROLES = {cavfull:"cavity wall full fill", cavpart:"cavity wall partial fill", floor:"floor board", rafter:"pitched roof board",
                   flat:"flat roof board", frame:"framing board", lining:"insulated plasterboard"};

/* Insulated plasterboard comes as a family of fixed total thicknesses, each its own UC id. */
const LINING_FAM = {
 k118:  {n:"Kingspan Kooltherm K118 insulated plasterboard", k:0.019, ids:{"25":"k118_25","37.5":"k118_375","52.5":"k118_525","57.5":"k118_575","62.5":"k118_625","72.5":"k118_725"}},
 pl4000:{n:"Celotex (Soprema SOPRATHERM) PL4000 insulated plasterboard", k:0.022, ids:{"37.5":"pl4000_375","52.5":"pl4000_525","62.5":"pl4000_625","72.5":"pl4000_725"}}
};
function liningFamOf(id){ for(const f in LINING_FAM){ for(const t in LINING_FAM[f].ids) if(LINING_FAM[f].ids[t]===id) return {fam:f, t:+t}; } return null; }

function mfrTable(role){
  if(role==="cavfull") return UC.insulation.filter(x=>x.fill==="full");
  if(role==="cavpart") return UC.insulation.filter(x=>x.fill==="partial");
  if(role==="floor")   return UC.floorIns;
  if(role==="rafter")  return UC.rafterIns;
  if(role==="flat")    return UC.flatIns;
  if(role==="frame")   return UC.frameIns;
  return [];
}
/* which parameter carries the product, and which the thickness, for each calculation */
const MFR_KEYS = {
  wall:{insulation:"insulation", thickness:"thickness"}, floorSolid:{insulation:"insulation", thickness:"thickness"},
  floorSusp:{insulation:"insulation", thickness:"thickness"}, rafter:{insulation:"insulation", thickness:"thickness", lining:"under"},
  overRafter:{insulation:"insulation", thickness:"over"}, flat:{insulation:"insulation", thickness:"thickness"},
  frame:{insulation:"insulation", thickness:"thickness", lining:"lining"}, lined:{insulation:"insulation", thickness:"thickness", lining:"lining"},
  basementWall:{insulation:"wallIns", thickness:"wallThk"}, basementFloor:{insulation:"floorIns", thickness:"floorThk"}
};

function mfrRun(k, p){
  let r, U;
  switch(k){
    case "wall":        r=UC.wall(p); break;
    case "floorSolid":  r=UC.floorSolid(p); break;
    case "floorSusp":   r=UC.floorSuspended(p); break;
    case "rafter":      r=UC.roofRafter(p); break;
    case "overRafter":  r=UC.roofOverRafter(p); break;
    case "flat":        r=UC.roofFlat(p); break;
    case "frame":       r=UC.frame(p); break;
    case "lined":       r=UC.lined(p); break;
    case "basementWall": r=UC.basement(p); r={...r, U:r.Ubw}; break;
    case "basementFloor": r=UC.basement(p); r={...r, U:r.Ubf}; break;
    default: throw new Error("unknown calculation "+k);
  }
  U=r.U;
  return {U, res:{kind:r.kind, U:r.U, U0:r.U0, dUg:r.dUg||0, dUf:r.dUf||0, RT:r.RT, RT_upper:r.RT_upper, RT_lower:r.RT_lower,
                  layers:r.layers.map(l=>({n:l.n,d:l.d,R:l.R})), steps:r.steps, notes:r.notes||[], src:[...new Set((r.src||[]).filter(Boolean))]}};
}

/* Basement descriptors name a product outside floorIns by role; resolve it to a product object. */
function mfrBasementProduct(p, role, id){
  const prod = mfrTable(role).find(x=>x.id===id);
  return prod ? {n:prod.n, k:prod.k, src:prod.src} : null;
}
function mfrPrepare(k, p, s0){
  const q={...p};
  if(k==="basementWall" && String(q.wallIns).startsWith("__")) { q.wallProduct=mfrBasementProduct(q, s0.r, s0.id); q.wallIns="k103"; }
  return q;
}

/* The substitution itself. Returns null when nothing changes (Kingspan, or no descriptor). */
function mfrSubstitute(b, mfrId){
  const mf=b.mf; if(!mf || !mfrId || mfrId==="kingspan") return null;
  const M=MFRS.find(m=>m.id===mfrId); if(!M) return null;
  const keys=MFR_KEYS[mf.k];
  let p=mfrPrepare(mf.k, mf.p, mf.s[0]);
  const done=[], kept=[];
  /* 1. swap every role at the clause's own thickness */
  mf.s.forEach(s=>{
    if(s.r==="lining"){
      const fam=M.lining, cur=liningFamOf(p[keys.lining]);
      if(!fam || !cur){ kept.push(s); return; }
      const F=LINING_FAM[fam], ts=Object.keys(F.ids).map(Number).sort((a,b)=>a-b);
      const t0=ts.find(t=>t>=cur.t); if(t0==null){ kept.push(s); return; }
      p[keys.lining]=F.ids[String(t0)];
      done.push({s, role:"lining", fam, from:cur.t, t:t0, ts, name:F.n, k:F.k});
      return;
    }
    const pid=M[s.r]; const prod=pid && mfrTable(s.r).find(x=>x.id===pid);
    if(!prod || !prod.th){ kept.push(s); return; }
    const t0raw = mf.k==="basementWall" ? p.wallThk : mf.k==="basementFloor" ? p.floorThk : p[keys.thickness];
    /* boards on a floor, a flat roof or between rafters are laid in two layers where one will
       not reach: the candidates are the single thicknesses and every pair of them */
    let ts=prod.th.slice();
    if(s.r==="floor"||s.r==="flat"||s.r==="rafter") prod.th.forEach(a=>prod.th.forEach(c=>{ if(a<=c) ts.push(a+c); }));
    ts=[...new Set(ts)].sort((a,b)=>a-b);
    let t0=ts.find(t=>t>=t0raw); if(t0==null) t0=ts[ts.length-1];
    if(mf.k==="basementWall"){ p.wallProduct={n:prod.n,k:prod.k,src:prod.src}; p.wallThk=t0; }
    else if(mf.k==="basementFloor"){ p.floorProduct={n:prod.n,k:prod.k,src:prod.src}; p.floorThk=t0; }
    else { p[keys.insulation]=prod.id; p[keys.thickness]=t0; }
    done.push({s, role:s.r, prod, from:t0raw, t:t0, ts});
  });
  if(!done.length){
    return {b:{...b, p:b.p.concat([`Insulation manufacturer: ${M.n} is selected for this job, but the library holds no verified ${M.short} product for the role this build-up needs (${mf.s.map(s=>MFR_ROLES[s.r]).join(", ")}), so the product named above is retained. Any substitution is to be supported by the manufacturer's certified U-value calculation before submission.`])}, changed:false};
  }
  /* geometry that follows the thickness */
  const fit=()=>{
    if(mf.k==="wall"){
      const ins=UC.insulation.find(x=>x.id===p.insulation);
      if(ins.fill==="full") p.cavity=Math.max(mf.p.cavity, p.thickness+(ins.residual||0));
      else p.cavity=Math.max(mf.p.cavity, p.thickness+50);
    }
    if(mf.k==="frame"||mf.k==="lined"){ if(p.insulation) p.studDepth=Math.max(mf.p.studDepth||0, p.thickness); }
    if(mf.k==="rafter"){ p.rafterDepth=Math.max(mf.p.rafterDepth, p.thickness); }
  };
  /* 2. step the thickness up until the target is met: the main product first, then the lining */
  fit();
  let run=mfrRun(mf.k, p);
  const order=done.filter(d=>d.role!=="lining").concat(done.filter(d=>d.role==="lining"));
  let ok = run.U<=mf.lim+1e-9;
  for(const d of order){
    while(!ok){
      const i=d.ts.indexOf(d.t); if(i<0||i>=d.ts.length-1) break;
      d.t=d.ts[i+1];
      if(d.role==="lining") p[keys.lining]=LINING_FAM[d.fam].ids[String(d.t)];
      else if(mf.k==="basementWall") p.wallThk=d.t; else if(mf.k==="basementFloor") p.floorThk=d.t; else p[keys.thickness]=d.t;
      fit(); run=mfrRun(mf.k, p); ok=run.U<=mf.lim+1e-9;
    }
    if(ok) break;
  }
  /* 3. rewrite the clause */
  const lambda = d => d.role==="lining" ? d.k : d.prod.k;
  const phrase = d => d.role==="lining" ? `${d.t}mm ${d.name} (thermal conductivity ${d.k} W/mK)` : `${d.t}mm ${d.prod.n} (thermal conductivity ${d.prod.k} W/mK)`;
  let ps=b.p.slice(), tgt=b.tgt||"";
  done.forEach(d=>{ ps=ps.map(x=>x.split(d.s.f).join(phrase(d)));
    if(d.s.over) ps=ps.map(x=>x.split(d.s.over).join(`${p.over}mm ${d.prod.n}`)); });
  const geo=[];
  if(mf.k==="wall" && p.cavity!==mf.p.cavity){ ps=ps.map(x=>x.replace(`${mf.p.cavity}mm cavity`, `${p.cavity}mm cavity`)); geo.push(`the cavity widened from ${mf.p.cavity}mm to ${p.cavity}mm`); }
  if((mf.k==="frame"||mf.k==="lined") && p.studDepth!==mf.p.studDepth){ ps=ps.map(x=>x.split(`${mf.p.studDepth}mm x `).join(`${p.studDepth}mm x `).split(`${mf.p.studDepth}mm studs`).join(`${p.studDepth}mm studs`)); geo.push(`the studs deepened from ${mf.p.studDepth}mm to ${p.studDepth}mm`); }
  if(mf.k==="rafter" && p.rafterDepth!==mf.p.rafterDepth){ ps=ps.map(x=>x.split(`x ${mf.p.rafterDepth}mm`).join(`x ${p.rafterDepth}mm`).split(`${mf.p.rafterDepth}mm rafters`).join(`${p.rafterDepth}mm rafters`).split(`${mf.p.rafterDepth}mm joists`).join(`${p.rafterDepth}mm joists`)); geo.push(`the rafters deepened from ${mf.p.rafterDepth}mm to ${p.rafterDepth}mm`); }
  const Ut=run.U.toFixed(2);
  let hit=false;
  ps=ps.map(x=>{ if(hit) return x; const y=x.replace(/calculates at \d\.\d\d W\/m²K/, m=>{hit=true; return `calculates at ${Ut} W/m²K`;}); return y; });
  tgt=tgt.replace(/achieved \d\.\d\d W\/m²K/, `achieved ${Ut} W/m²K`);
  const u=(b.u||"").replace(/\d\.\d\d W\/m²K/, `${Ut} W/m²K`) || `${Ut} W/m²K`;
  const swaps=done.map(d=>{ const from=d.s.f.replace(/\s*\(thermal.*$/,""); const to=phrase(d).replace(/\s*\(thermal.*$/,"");
    const two = d.role!=="lining" && !d.prod.th.includes(d.t) ? " laid in two layers" : "";
    return `${to}${two} in place of ${from}${d.t!==d.from?` (thickness increased from ${d.from}mm to ${d.t}mm to meet the target${geo.length?", with "+geo.join(" and "):""})`:""}`; });
  const std = mf.k==="floorSolid"||mf.k==="floorSusp"||mf.k.startsWith("basement") ? "BS EN ISO 13370" : "BS EN ISO 6946";
  const tail = ok
    ? `Insulation manufacturer: ${M.n} is selected for this job. ${swaps.join("; ")}. The U-value stated in this clause, in the schedule and in the target line is recalculated for the substituted product to ${std} by the same method as the library figure and is carried into the U-value working; figures quoted in the clause for other thicknesses of the original product no longer apply. The substituted product is to be installed to its own BBA certificate and the manufacturer's certified U-value calculation obtained before submission.`
    : `NOTE — Insulation manufacturer: ${M.n} is selected for this job. ${swaps.join("; ")}. At its greatest published thickness the substituted product calculates at ${run.U.toFixed(3)} W/m²K to ${std} (${Ut} to two places) and does not meet the target of ${mf.lim.toFixed(2)}; the build-up is shown with it for information and is not to be issued until the construction is changed or the original product reinstated.`;
  const info={mfr:M.id, ok, U:run.U, swaps, kept:kept.map(s=>MFR_ROLES[s.r])};
  const keptTail = kept.length ? ` The ${kept.map(s=>MFR_ROLES[s.r]).join(" and ")} named in the clause is retained: the library holds no verified ${M.short} product for that role.` : "";
  return {changed:true, info, b:{...b, u, tgt, p:ps.concat([tail+keptTail]),
          calc:{params:{...p, limit:mf.lim, mfr:M.id, kind:mf.k}, result:run.res}}};
}

/* ---- the job side: which manufacturer applies to build-up i, and the memoised result ---- */
const MFR_CACHE = {};
function mfrFor(i){ return (S.ovr && S.ovr[i]) || S.data.mfr || "kingspan"; }
function mfrApply(b, i){
  if(!b.mf) return b;
  const id=mfrFor(i), key=S.type+"|"+i+"|"+id;
  if(!(key in MFR_CACHE)){ const r=mfrSubstitute(b, id); MFR_CACHE[key]= r ? {...r.b, mfrInfo:r.info||null, lib:i} : b; }
  return MFR_CACHE[key];
}
if(typeof module!=="undefined") module.exports={MFRS, MFR_ROLES, LINING_FAM, mfrSubstitute, mfrRun, mfrTable};
