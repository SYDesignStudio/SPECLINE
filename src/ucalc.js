/* ===== U-value calculator — BS EN ISO 6946 (walls), with BR 443 conventions =====
   Surface resistances, unventilated air layers, combined (upper/lower limit) method for
   mortar-bridged blockwork, and Annex F corrections for air gaps (dUg) and wall ties (dUf).
   Every material carries a `src` so the app can show what was verified and what to confirm. */

const UC = {
  Rsi_wall:0.13, Rse_wall:0.04,
  // unventilated air layer, horizontal heat flow (ISO 6946 Table 7)
  airGap(mm){ if(mm<=0) return 0; if(mm<5) return 0.11*mm/5; if(mm<7) return 0.11; if(mm<10) return 0.13;
              if(mm<15) return 0.15; if(mm<25) return 0.17; return 0.18; },
  outer:[
   {id:"brick",  n:"103mm facing brickwork",              d:103, k:0.77, src:"BR 443 typical (brickwork outer leaf)"},
   {id:"render", n:"100mm dense block, rendered",         d:100, k:1.13, extra:{n:"20mm render",d:20,k:1.00}, src:"BR 443 typical"},
   {id:"stone",  n:"100mm reconstituted stone",           d:100, k:1.30, src:"BR 443 typical"}],
  inner:[
   {id:"a011", n:"100mm aircrete block 0.11 W/mK (Celcon Solar, Thermalite Turbo)", d:100, k:0.11, src:"H+H verified 04/09/2026"},
   {id:"a015", n:"100mm aircrete block 0.15 W/mK (Celcon Standard, Thermalite Shield)", d:100, k:0.15, src:"H+H verified 04/09/2026"},
   {id:"a019", n:"100mm high-strength aircrete block 7.3N 0.185 W/mK (Thermalite Hi-Strength 7; Celcon High Strength 0.18)", d:100, k:0.185, src:"Forterra datasheet 06/2026 (0.185 design, 3%) / H+H 2025 datasheet (0.18) verified 05/09/2026"},
   {id:"m051", n:"100mm medium-dense block 0.51 W/mK", d:100, k:0.51, src:"BR 443 typical"},
   {id:"d113", n:"100mm dense concrete block 1.13 W/mK (7.3N)", d:100, k:1.13, src:"BR 443 typical"}],
  mortar:[
   {id:"gp",   n:"General purpose mortar, 10mm joints", k:0.88, frac:0.067, src:"BR 443 (440×215 block)"},
   {id:"thin", n:"Thin-joint mortar, 2–3mm joints",     k:0.88, frac:0.014, src:"BR 443"}],
  finish:[
   {id:"pbdabs", n:"12.5mm plasterboard on dabs", layers:[{n:"dab air gap",gap:10},{n:"12.5mm plasterboard",d:12.5,k:0.21}], src:"BR 443"},
   {id:"pbbatt", n:"12.5mm plasterboard on 25mm battens", layers:[{n:"batten void",gap:25},{n:"12.5mm plasterboard",d:12.5,k:0.21}], src:"BR 443"},
   {id:"plaster",n:"13mm lightweight plaster",        layers:[{n:"13mm lightweight plaster",d:13,k:0.18}], src:"BR 443"}],
  insulation:[
   // full fill
   {id:"k106", n:"Kingspan Kooltherm K106 Cavity Board", k:0.019, fill:"full", th:[75,90,100,115,125,140], residual:10, src:"Kingspan/NBS verified 04/09/2026"},
   {id:"tc21", n:"Celotex (Soprema) Thermaclass Cavity Wall 21", k:0.021, fill:"full", th:[90,115,140], residual:0, src:"Celotex verified 04/09/2026"},
   {id:"ctpir",n:"Unilin (Xtratherm) CavityTherm CT/PIR", k:0.021, fill:"full", th:[100,110,125,150], residual:0, src:"Unilin handbook 09/2025 + BBA 23/7059 verified 05/09/2026"},
   {id:"ecoff",n:"EcoTherm Eco-Cavity Full Fill", k:0.022, fill:"full", th:[90,115,140], residual:0, src:"EcoTherm datasheet 14th issue 02/2026 + BBA 24/7114 verified 05/09/2026"},
   {id:"dt32", n:"Knauf DriTherm Cavity Slab 32 Ultimate", k:0.032, fill:"full", th:[75,85,100,125,150], residual:0, src:"Knauf datasheet 03/2024 + BBA 95/3212 verified 05/09/2026"},
   {id:"dt37", n:"Knauf DriTherm Cavity Slab 37 Standard", k:0.037, fill:"full", th:[50,65,75,85,100,125,150], residual:0, src:"Knauf datasheet 03/2024 + BBA 95/3212 verified 05/09/2026"},
   {id:"rwff", n:"ROCKWOOL Full Fill Cavity Batt", k:0.037, fill:"full", th:[75,100,125,150,175,200], residual:0, src:"ROCKWOOL datasheet 08/2026 + BBA 94/3079 (50–250mm range) verified 05/09/2026"},
   // partial fill
   {id:"k108", n:"Kingspan Kooltherm K108 Cavity Board", k:0.019, fill:"partial", th:[40,50,60,70,75,80,90,100], src:"Kingspan K108 brochure 10th issue 04/2026 verified 05/09/2026"},
   {id:"cw4000",n:"Celotex CW4000 (now Soprema SOPRATHERM CW4000)", k:0.022, fill:"partial", th:[40,50,60,70,75,80,85,100], src:"Soprema product page + BBA 25/7312 verified 05/09/2026"},
   {id:"xtcw", n:"Unilin Thin-R XT/CW (was Xtratherm CW/PIR)", k:0.022, fill:"partial", th:[60,70,75,80,90,100], src:"Unilin handbook 09/2025 + BBA 23/6997 verified 05/09/2026"},
   {id:"ecopf",n:"EcoTherm Eco-Cavity (partial fill)", k:0.022, fill:"partial", th:[50,60,70,75,80,100], src:"EcoTherm datasheet 15th issue 02/2026 + BBA 24/7114 verified 05/09/2026"}],
  ties:[
   {id:"ss45x90", n:"Stainless steel wire ties, 450 × 900mm (2.5/m²)", nf:2.47, Af:1.26e-5, lam:17, src:"BR 443 / ISO 6946 Annex F"},
   {id:"ss45x45", n:"Stainless steel wire ties, 450 × 450mm (4.9/m²)", nf:4.94, Af:1.26e-5, lam:17, src:"BR 443 / ISO 6946 Annex F"},
   {id:"none",    n:"Ignore ties (basalt / low-conductivity)", nf:0, Af:0, lam:0, src:"—"}],
  gapLevel:[
   {id:0, n:"Level 0 — no air gaps through the insulation (dU'' = 0.00)", dU:0.00},
   {id:1, n:"Level 1 — small gaps, boards butted to inner leaf (dU'' = 0.01)", dU:0.01},
   {id:2, n:"Level 2 — gaps allow air circulation (dU'' = 0.04)", dU:0.04}],

  /* returns {U, U0, dUg, dUf, RT, RT_upper, RT_lower, layers:[{n,d,R}], notes:[]} */
  wall(p){
    const outer=this.outer.find(x=>x.id===p.outer), inner=this.inner.find(x=>x.id===p.inner),
          mort=this.mortar.find(x=>x.id===p.mortar), fin=this.finish.find(x=>x.id===p.finish),
          ins=this.insulation.find(x=>x.id===p.insulation), tie=this.ties.find(x=>x.id===p.ties),
          lvl=this.gapLevel.find(x=>x.id===p.gapLevel);
    const t=p.thickness, cav=p.cavity;
    const layers=[{n:"External surface (Rse)",R:this.Rse_wall}];
    if(outer.extra) layers.push({n:outer.extra.n,d:outer.extra.d,R:outer.extra.d/1000/outer.extra.k});
    layers.push({n:outer.n,d:outer.d,R:outer.d/1000/outer.k});
    // residual cavity
    let residual = ins.fill==="full" ? (ins.residual||0) : Math.max(cav - t, 0);
    const notes=[];
    if(ins.fill==="partial" && residual<50) notes.push("Residual cavity is less than 50mm — check the manufacturer's certificate permits this.");
    if(ins.fill==="full" && t>cav) notes.push("Insulation thicker than the cavity — increase cavity width.");
    if(residual>0) layers.push({n:`Residual cavity ${residual}mm (unventilated air layer)`,d:residual,R:this.airGap(residual)});
    const Rins=t/1000/ins.k;
    layers.push({n:`${t}mm ${ins.n} (λ ${ins.k})`,d:t,R:Rins,ins:true});
    // inner leaf: combined method for mortar bridging
    const Rb=inner.d/1000/inner.k, Rm=inner.d/1000/mort.k, fb=1-mort.frac, fm=mort.frac;
    const RbLower=1/(fb/Rb+fm/Rm);
    layers.push({n:`${inner.n} + ${mort.n}`,d:inner.d,R:RbLower,bridged:true,Rb,Rm,fb,fm});
    fin.layers.forEach(l=>layers.push(l.gap?{n:`${l.n} ${l.gap}mm`,d:l.gap,R:this.airGap(l.gap)}:{n:l.n,d:l.d,R:l.d/1000/l.k}));
    layers.push({n:"Internal surface (Rsi)",R:this.Rsi_wall});
    const others=layers.filter(l=>!l.bridged).reduce((s,l)=>s+l.R,0);
    const RT_lower=others+RbLower;
    const RT_upper=1/(fb/(others+Rb)+fm/(others+Rm));
    const RT=(RT_upper+RT_lower)/2;
    const U0=1/RT;
    const dUg=lvl.dU*Math.pow(Rins/RT,2);
    const dUf= tie.nf? 0.8*tie.lam*tie.nf*tie.Af/(t/1000)*Math.pow(Rins/RT,2) : 0;
    const U=U0+dUg+dUf;
    return {U,U0,dUg,dUf,RT,RT_upper,RT_lower,layers,notes,residual,
            src:[outer.src,inner.src,mort.src,fin.src,ins.src,tie.src]};
  }
};
if(typeof module!=="undefined") module.exports=UC;
