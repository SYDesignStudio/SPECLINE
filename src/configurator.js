
/* ================= Cavity wall configurator (parametric build-ups) ================= */
const allBU = () => spec().buildups.concat(S.custom||[]);
const CFG_DEFAULT = {outer:"brick",cavity:100,fill:"full",insulation:"k106",thickness:90,inner:"a015",
                     mortar:"gp",finish:"pbdabs",ties:"ss45x90",gapLevel:1,limit:0.18};
function cfg(){ if(!S.cfg) S.cfg={...CFG_DEFAULT}; return S.cfg; }
function isWallCat(cat){ return /external wall|hip to gable/i.test(cat||""); }

function cfgOptions(){
  const c=cfg();
  const insList=UC.insulation.filter(i=>i.fill===c.fill);
  if(!insList.find(i=>i.id===c.insulation)){ c.insulation=insList[0].id; }
  const ins=insList.find(i=>i.id===c.insulation);
  if(!ins.th.includes(c.thickness)) c.thickness=ins.th[Math.floor(ins.th.length/2)];
  return {insList,ins};
}
function sel(name,opts,val,label){
  return `<label class="cf"><span>${esc(label)}</span><select data-cf="${name}">`+
    opts.map(o=>`<option value="${esc(o.v)}" ${String(o.v)===String(val)?"selected":""}>${esc(o.n)}</option>`).join("")+
    `</select></label>`;
}
function renderConfigurator(){
  const c=cfg(); const {insList,ins}=cfgOptions();
  const r=UC.wall(c);
  const pass=r.U<=c.limit+1e-9;
  const cavities=c.fill==="full"?[75,90,100,115,125,140,150]:[100,125,150];
  if(!cavities.includes(c.cavity)) c.cavity=cavities[Math.min(2,cavities.length-1)];
  let h=`<div class="card cfgcard">
    <div class="cfghead"><h3>Build a cavity wall</h3>
      <span class="uval ${pass?"ok":"bad"}"><b>${r.U.toFixed(2)}</b> W/m²K <small>(${r.U.toFixed(3)})</small></span></div>
    <p class="lede" style="margin-bottom:12px">Choose the layers and the U-value is calculated live to BS EN ISO 6946. Add it and it becomes a numbered EW build-up with the working attached.</p>
    <div class="cfggrid">
      ${sel("outer",UC.outer.map(o=>({v:o.id,n:o.n})),c.outer,"Outer leaf")}
      ${sel("fill",[{v:"full",n:"Full fill"},{v:"partial",n:"Partial fill"}],c.fill,"Cavity fill")}
      ${sel("cavity",cavities.map(v=>({v,n:v+"mm"})),c.cavity,"Cavity width")}
      ${sel("insulation",insList.map(i=>({v:i.id,n:i.n+"  (λ "+i.k+")"})),c.insulation,"Insulation")}
      ${sel("thickness",ins.th.map(v=>({v,n:v+"mm"})),c.thickness,"Insulation thickness")}
      ${sel("inner",UC.inner.map(o=>({v:o.id,n:o.n})),c.inner,"Inner leaf")}
      ${sel("mortar",UC.mortar.map(o=>({v:o.id,n:o.n})),c.mortar,"Mortar")}
      ${sel("finish",UC.finish.map(o=>({v:o.id,n:o.n})),c.finish,"Internal finish")}
      ${sel("ties",UC.ties.map(o=>({v:o.id,n:o.n})),c.ties,"Wall ties")}
      ${sel("gapLevel",UC.gapLevel.map(o=>({v:o.id,n:o.n})),c.gapLevel,"Air-gap correction")}
      ${sel("limit",[{v:0.18,n:"0.18 — new element in extension"},{v:0.26,n:"0.26 — new dwelling notional"},{v:0.30,n:"0.30 — retained element threshold"}],c.limit,"Target")}
    </div>
    ${r.notes.length?`<p class="cfgwarn">${r.notes.map(esc).join(" ")}</p>`:""}
    <details class="working"><summary>U-value working</summary>${workingTable(r)}</details>
    <div class="cfgfoot">
      <span class="srcnote">Sources: ${[...new Set(r.src)].map(esc).join(" · ")}</span>
      <button class="btn btn-primary" id="addWall">Add as EW build-up</button>
    </div></div>`;
  return h;
}
function workingTable(r){
  let h=`<table class="wk"><tr><th>Layer</th><th>mm</th><th>R (m²K/W)</th></tr>`;
  r.layers.forEach(l=>{ h+=`<tr><td>${esc(l.n)}${l.bridged?` <i>(combined method: block R ${l.Rb.toFixed(3)} × ${(l.fb*100).toFixed(1)}%, mortar R ${l.Rm.toFixed(3)} × ${(l.fm*100).toFixed(1)}%)</i>`:""}</td><td>${l.d!=null?l.d:"—"}</td><td>${l.R.toFixed(3)}</td></tr>`; });
  h+=`<tr class="tot"><td>R<sub>T</sub> upper / lower limit</td><td></td><td>${r.RT_upper.toFixed(3)} / ${r.RT_lower.toFixed(3)}</td></tr>
      <tr class="tot"><td>R<sub>T</sub> (mean)</td><td></td><td>${r.RT.toFixed(3)}</td></tr>
      <tr class="tot"><td>U<sub>0</sub> = 1 / R<sub>T</sub></td><td></td><td>${r.U0.toFixed(3)}</td></tr>
      <tr><td>ΔU<sub>g</sub> air gaps (Annex F)</td><td></td><td>+${r.dUg.toFixed(3)}</td></tr>
      <tr><td>ΔU<sub>f</sub> wall ties (Annex F)</td><td></td><td>+${r.dUf.toFixed(3)}</td></tr>
      <tr class="tot"><td><b>U</b></td><td></td><td><b>${r.U.toFixed(3)} → ${r.U.toFixed(2)} W/m²K</b></td></tr></table>`;
  return h;
}
function wallSpecText(c,r){
  const outer=UC.outer.find(x=>x.id===c.outer), inner=UC.inner.find(x=>x.id===c.inner),
        ins=UC.insulation.find(x=>x.id===c.insulation), fin=UC.finish.find(x=>x.id===c.finish),
        mort=UC.mortar.find(x=>x.id===c.mortar), tie=UC.ties.find(x=>x.id===c.ties);
  const fillTxt = c.fill==="full"
    ? `a ${c.cavity}mm cavity fully filled with ${c.thickness}mm ${ins.n}${r.residual?` leaving a nominal ${r.residual}mm residual cavity against the outer leaf`:""}`
    : `a ${c.cavity}mm cavity with ${c.thickness}mm ${ins.n} retained against the inner leaf by proprietary clips and a ${r.residual}mm clear residual cavity`;
  const title = (c.fill==="full"?"Full Fill":"Partial Fill")+" Cavity Wall — "+ins.n.split(" ")[0]+" "+c.thickness+"mm";
  return {
    g:"EW", cat:"__wall__", t:title, u:r.U.toFixed(2)+" W/m²K",
    tgt:`To achieve a maximum U-value of ${c.limit.toFixed(2)} W/m²K (calculated ${r.U.toFixed(2)} W/m²K to BS EN ISO 6946 — see U-value working; obtain the manufacturer's certified calculation before submission)`,
    p:[
     `External cavity wall built up as ${outer.n} to the outer leaf, ${fillTxt}, and ${inner.n} to the inner leaf, finished internally with ${fin.n.toLowerCase()}. All masonry laid in ${mort.id==="thin"?"thin-joint mortar to the block manufacturer's system":"1:1:6 cement:lime:sand mortar"}. Outer leaf to match the existing dwelling in material, bond and pointing unless noted otherwise on the elevations.`,
     `Insulation installed strictly to the manufacturer's published instructions and current BBA certificate, boards tightly butted on every edge with vertical joints staggered course to course and no gaps at ties, reveals or junctions. Corner, reveal and junction details to follow the certificate. Where the manufacturer's certificate does not support the air-gap correction level assumed in the calculation, the U-value is to be recalculated.`,
     tie.nf?`${tie.n.replace(/\s*\(.*\)/,"")} to be provided, staggered, with additional ties at 225mm vertical centres within 225mm of all unbonded jambs, reveals and movement joints. Ties to be set with a slight fall to the outer leaf and kept free of mortar droppings.`:
            `Low-conductivity wall ties to be provided to the manufacturer's specification, with additional ties at 225mm vertical centres within 225mm of all unbonded jambs, reveals and movement joints.`,
     `The exposure of the site is to be assessed for the suitability of ${c.fill==="full"?"full fill":"the residual cavity width"} before boards are ordered.`],
    calc:{params:{...c}, result:{U:r.U,U0:r.U0,dUg:r.dUg,dUf:r.dUf,RT:r.RT,RT_upper:r.RT_upper,RT_lower:r.RT_lower,
          layers:r.layers.map(l=>({n:l.n,d:l.d,R:l.R})),src:[...new Set(r.src)]}}
  };
}
function bindConfigurator(){
  const card=document.querySelector(".cfgcard"); if(!card) return;
  card.querySelectorAll("select[data-cf]").forEach(s=>s.onchange=()=>{
    const k=s.dataset.cf; let v=s.value;
    if(["cavity","thickness","gapLevel"].includes(k)) v=+v; if(k==="limit") v=parseFloat(v);
    cfg()[k]=v; renderStage(); save();
  });
  const add=el("addWall"); if(add) add.onclick=()=>{
    const c=cfg(); const r=UC.wall(c);
    S.custom=S.custom||[]; S.custom.push(wallSpecText(c,r));
    const idx=allBU().length-1; S.sel.push(idx);
    renderStage(); renderSteps(); renderPaper(); save(); toast("Added "+refs()[idx]);
  };
}
