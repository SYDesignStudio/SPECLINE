/* ===== Floors (BS EN ISO 13370) and roofs (BS EN ISO 6946) ===== */
Object.assign(UC, {
  Rsi_floor:0.17, Rse_floor:0.04, Rsi_roof:0.10, Rse_roof:0.04,
  airGapUp(mm){ if(mm<=0) return 0; if(mm<5) return 0.11*mm/5; if(mm<7) return 0.11; if(mm<10) return 0.13; if(mm<15) return 0.15; return 0.16; },
  timber:0.13,
  ground:[
   {id:"clay", n:"Clay or silt (λg 1.5)", k:1.5, src:"BS EN ISO 13370 Table"},
   {id:"sand", n:"Sand or gravel (λg 2.0)", k:2.0, src:"BS EN ISO 13370 Table"},
   {id:"rock", n:"Homogeneous rock (λg 3.5)", k:3.5, src:"BS EN ISO 13370 Table"}],
  floorIns:[
   {id:"tf70", n:"Kingspan Thermafloor TF70", k:0.022, th:[50,60,70,75,80,90,100,110,120,125,130,140,150], src:"retailer datasheet verified 05/09/2026"},
   {id:"k103", n:"Kingspan Kooltherm K103 Floorboard", k:0.019, th:[50,60,70,75,80,90,100,120,130,140,150], src:"Kingspan K103 brochure 12th issue 03/2026 verified 05/09/2026"},
   {id:"ga4000",n:"Celotex GA4000 / XR4000 (now Soprema SOPRATHERM)", k:0.022, th:[50,60,70,75,80,90,100,110,120,125,130,140,150,165,200], src:"Soprema product pages verified 05/09/2026"},
   {id:"xtuf", n:"Unilin Thin-R XT/PR-UF (was Xtratherm XT/UF)", k:0.022, th:[50,60,70,90,100,110,125,140,150], src:"Unilin handbook 09/2025 + BBA 23/6997 verified 05/09/2026"},
   {id:"ecov", n:"EcoTherm Eco-Versal", k:0.022, th:[50,60,70,75,80,90,100,110,120,125,130,140,150], src:"EcoTherm datasheet 02/2026 + BBA 24/7114 verified 05/09/2026"},
   {id:"eps100",n:"EPS 100 (expanded polystyrene)", k:0.036, th:[50,75,100,125,150,200], src:"BR 443 typical"},
   {id:"xps", n:"XPS (extruded polystyrene)", k:0.033, th:[50,75,100,125,150], src:"BR 443 typical"}],
  floorFinish:[
   {id:"screed65", n:"65mm sand/cement screed", layers:[{n:"65mm sand/cement screed",d:65,k:1.41}], src:"BR 443"},
   {id:"screed75", n:"75mm sand/cement screed", layers:[{n:"75mm sand/cement screed",d:75,k:1.41}], src:"BR 443"},
   {id:"chip22", n:"22mm chipboard floating floor", layers:[{n:"22mm chipboard",d:22,k:0.14}], src:"BR 443"},
   {id:"none", n:"Power-floated slab, no finish", layers:[], src:"—"}],
  slabs:[
   {id:"c100", n:"100mm concrete slab", d:100, k:1.35, src:"BR 443 (dense concrete)"},
   {id:"c125", n:"125mm concrete slab", d:125, k:1.35, src:"BR 443 (dense concrete)"},
   {id:"c150", n:"150mm concrete slab", d:150, k:1.35, src:"BR 443 (dense concrete)"},
   {id:"bb150", n:"150mm beam and block deck", d:150, k:1.35, src:"BR 443 — treat as dense concrete; confirm with beam manufacturer"}],
  edgeIns:[
   {id:"none", n:"No perimeter upstand", D:0, R:0},
   {id:"e25x150", n:"25mm PIR upstand, 150mm deep", D:0.15, R:0.025/0.022},
   {id:"e25x300", n:"25mm PIR upstand, 300mm deep", D:0.30, R:0.025/0.022},
   {id:"e50x300", n:"50mm PIR upstand, 300mm deep", D:0.30, R:0.050/0.022}],

  /* Slab-on-ground with all-over insulation (ISO 13370 §9.1) + vertical edge insulation (Annex B) */
  floorSolid(p){
    const g=this.ground.find(x=>x.id===p.ground), ins=this.floorIns.find(x=>x.id===p.insulation),
          slab=this.slabs.find(x=>x.id===p.slab), fin=this.floorFinish.find(x=>x.id===p.finish),
          edge=this.edgeIns.find(x=>x.id===p.edge);
    const PA=+p.pa, B=2/PA, w=(p.wall||300)/1000;
    const layers=[];
    layers.push({n:slab.n,d:slab.d,R:slab.d/1000/slab.k});
    layers.push({n:"Damp proof membrane",d:0,R:0});
    layers.push({n:`${p.thickness}mm ${ins.n} (λ ${ins.k})`,d:p.thickness,R:p.thickness/1000/ins.k,ins:true});
    fin.layers.forEach(l=>layers.push({n:l.n,d:l.d,R:l.d/1000/l.k}));
    const Rf=layers.reduce((s,l)=>s+l.R,0);
    const dt=w+g.k*(this.Rsi_floor+Rf+this.Rse_floor);
    const U0 = dt<B ? (2*g.k/(Math.PI*B+dt))*Math.log(Math.PI*B/dt+1) : g.k/(0.457*B+dt);
    let psi=0;
    if(edge.D>0){ const dp=edge.R*g.k; psi=-(g.k/Math.PI)*(Math.log(edge.D/dt+1)-Math.log(edge.D/(dt+dp)+1)); }
    const dUe=2*psi/B;
    const U=Math.max(U0+dUe,0.01);
    const notes=[];
    if(p.insulation==="none") notes.push("No insulation selected.");
    return {kind:"floor-solid",U,U0,dUe,psi,B,dt,Rf,layers,notes,
      steps:[["Perimeter/area ratio P/A",PA.toFixed(2)],["Characteristic dimension B' = 2/(P/A)",B.toFixed(2)+" m"],
             ["Floor construction R_f",Rf.toFixed(3)+" m²K/W"],["Ground conductivity λg",g.k+" W/mK"],
             ["Equivalent thickness d_t = w + λg(Rsi+Rf+Rse)",dt.toFixed(2)+" m"],
             [dt<B?"U₀ = 2λg/(πB'+d_t) · ln(πB'/d_t + 1)":"U₀ = λg/(0.457B' + d_t)  (well insulated, d_t ≥ B')",U0.toFixed(3)],
             ["Edge insulation ψ (Annex B)",psi.toFixed(4)+" W/mK"],["ΔU_edge = 2ψ/B'",dUe.toFixed(3)],["U",U.toFixed(3)+" → "+U.toFixed(2)]],
      src:[g.src,ins.src,slab.src,fin.src]};
  },

  /* Suspended floor over ventilated void (ISO 13370 §9.3) */
  /* Heated basement — BS EN ISO 13370 (basement floor and below-ground wall) */
  basement(p){
    const g=this.ground.find(x=>x.id===p.ground), fi=this.floorIns.find(x=>x.id===p.floorIns), wi=this.floorIns.find(x=>x.id===p.wallIns);
    const PA=+p.pa, B=2/PA, z=+p.depth, w=(p.wall||300)/1000;
    const fl=[{n:`${p.slab||200}mm reinforced concrete slab`,d:p.slab||200,R:(p.slab||200)/1000/1.35},{n:"Waterproofing / cavity drain membrane",d:0,R:0},
      {n:`${p.floorThk}mm ${fi.n} (λ ${fi.k})`,d:p.floorThk,R:p.floorThk/1000/fi.k,ins:true},{n:"75mm screed",d:75,R:0.075/1.41}];
    const wl=[{n:`${Math.round(w*1000)}mm reinforced concrete / masonry retaining wall`,d:w*1000,R:w/1.35},{n:"Waterproofing / cavity drain membrane",d:0,R:0},
      {n:`${p.wallThk}mm ${wi.n} (λ ${wi.k})`,d:p.wallThk,R:p.wallThk/1000/wi.k,ins:true},{n:"12.5mm plasterboard",d:12.5,R:0.0125/0.21}];
    const Rf=fl.reduce((s,l)=>s+l.R,0), Rw=wl.reduce((s,l)=>s+l.R,0);
    const dt=w+g.k*(this.Rsi_floor+Rf+this.Rse_floor), dw=g.k*(this.Rsi_wall+Rw+this.Rse_wall);
    const Ubf = (dt+0.5*z)<B ? (2*g.k/(Math.PI*B+dt+0.5*z))*Math.log(Math.PI*B/(dt+0.5*z)+1) : g.k/(0.457*B+dt+0.5*z);
    const dd = dw<dt ? dw : dt;
    const Ubw = (2*g.k/(Math.PI*z))*(1+0.5*dd/(dd+z))*Math.log(z/dw+1);
    const U=(Ubf + z*PA*Ubw)/(1+z*PA); // area-weighted per unit floor area (A=1, P=PA)
    return {kind:"basement",U,Ubf,Ubw,B,dt,dw,z,layers:fl.concat(wl),notes:[],
      steps:[["Perimeter/area ratio P/A",PA.toFixed(2)],["Characteristic dimension B'",B.toFixed(2)+" m"],["Basement depth z",z.toFixed(2)+" m"],
        ["Floor construction R_f",Rf.toFixed(3)+" m²K/W"],["Wall construction R_w",Rw.toFixed(3)+" m²K/W"],["λg",g.k+" W/mK"],
        ["d_t = w + λg(Rsi+Rf+Rse)",dt.toFixed(2)+" m"],["d_w = λg(Rsi+Rw+Rse)",dw.toFixed(2)+" m"],
        ["Basement floor U_bf",Ubf.toFixed(3)],["Below-ground wall U_bw",Ubw.toFixed(3)],["Combined (area-weighted) U",U.toFixed(3)+" → "+U.toFixed(2)]],
      src:[g.src,fi.src,wi.src,"BS EN ISO 13370 heated basement"]};
  },

  floorSuspended(p){
    const g=this.ground.find(x=>x.id===p.ground), ins=this.floorIns.find(x=>x.id===p.insulation);
    const PA=+p.pa, B=2/PA, w=(p.wall||300)/1000;
    const deck = p.deck==="bb" ? {n:"150mm beam and block deck",d:150,k:1.35} : {n:"22mm T&G chipboard/board deck",d:22,k:0.14};
    const layers=[];
    if(p.deck==="bb"){
      layers.push({n:`${p.thickness}mm ${ins.n} over deck (λ ${ins.k})`,d:p.thickness,R:p.thickness/1000/ins.k,ins:true});
      layers.push({n:"65mm sand/cement screed",d:65,R:0.065/1.41});
      layers.push({n:deck.n,d:deck.d,R:deck.d/1000/deck.k});
    } else {
      // timber joists with insulation between: bridged layer
      const jd=p.joistDepth||150, f=47/(p.spacing||400), tb=Math.min(p.thickness,jd);
      const Rins=tb/1000/ins.k, Rtim=tb/1000/this.timber;
      const Rbr=1/((1-f)/Rins+f/Rtim);
      layers.push({n:deck.n,d:deck.d,R:deck.d/1000/deck.k});
      layers.push({n:`${tb}mm ${ins.n} between 47×${jd} joists at ${p.spacing||400} (λ ${ins.k}; bridging ${(f*100).toFixed(1)}%)`,d:tb,R:Rbr,ins:true,bridged:true,Rb:Rins,Rm:Rtim,fb:1-f,fm:f});
      if(p.thickness>jd) layers.push({n:`${p.thickness-jd}mm ${ins.n} below joists`,d:p.thickness-jd,R:(p.thickness-jd)/1000/ins.k});
    }
    const Rf=layers.reduce((s,l)=>s+l.R,0);
    const Uf=1/(this.Rsi_floor+Rf+this.Rse_floor);
    const dg=w+g.k*(this.Rsi_floor+0+this.Rse_floor);
    const Ug=(2*g.k/(Math.PI*B+dg))*Math.log(Math.PI*B/dg+1);
    const h=0.3, Uw=1.5, eps=(p.vent||1500)/1e6, v=5, fw=0.05;
    const Ux=2*h*Uw/B + 1450*eps*v*fw/B;
    const U=1/(1/Uf+1/(Ug+Ux));
    return {kind:"floor-susp",U,U0:Uf,Uf,Ug,Ux,B,Rf,layers,notes:[],
      steps:[["P/A",PA.toFixed(2)],["B' = 2/(P/A)",B.toFixed(2)+" m"],["Floor deck R_f",Rf.toFixed(3)],["U_f = 1/(Rsi+Rf+Rse)",Uf.toFixed(3)],
             ["Ground U_g (bare oversite, λg "+g.k+")",Ug.toFixed(3)],["Void ventilation U_x (ε "+(p.vent||1500)+" mm²/m, h 0.3m, v 5 m/s, f_w 0.05)",Ux.toFixed(3)],
             ["U = 1/(1/U_f + 1/(U_g+U_x))",U.toFixed(3)+" → "+U.toFixed(2)]],
      src:[g.src,ins.src,"ISO 13370 §9.3 defaults: h 0.3m, U_w 1.5, v 5 m/s, f_w 0.05"]};
  },

  rafterIns:[
   {id:"k107", n:"Kingspan Kooltherm K107 Pitched Roof Board", k:0.019, src:"Kingspan K107 brochure 4th issue 06/2024 verified 05/09/2026"},
   {id:"ga4000r",n:"Celotex GA4000 / XR4000 (now Soprema SOPRATHERM)", k:0.022, src:"Soprema product pages verified 05/09/2026"},
   {id:"xtpr", n:"Unilin Thin-R XT/PR-UF (was Xtratherm XT/PR)", k:0.022, src:"Unilin handbook 09/2025 + BBA 23/6997 verified 05/09/2026"},
   {id:"ecovr",n:"EcoTherm Eco-Versal", k:0.022, src:"EcoTherm datasheet 02/2026 + BBA 24/7114 verified 05/09/2026"},
   {id:"rr32", n:"Knauf Rafter Roll 32", k:0.032, src:"product designation (λ×1000)"},
   {id:"mw35", n:"Mineral wool slab 0.035", k:0.035, src:"BR 443 typical"}],
  underIns:[
   {id:"none", n:"12.5mm plasterboard only", t:0, k:0, pb:12.5},
   {id:"k118_25", n:"Kingspan Kooltherm K118 25mm (12.5 + 12.5 pb)", t:12.5, k:0.019, pb:12.5, src:"Kingspan K118 datasheet verified 05/09/2026"},
   {id:"k118_375",n:"Kingspan Kooltherm K118 37.5mm (25 + 12.5 pb)", t:25, k:0.019, pb:12.5, src:"Kingspan K118 datasheet verified 05/09/2026"},
   {id:"k118_525",n:"Kingspan Kooltherm K118 52.5mm (40 + 12.5 pb)", t:40, k:0.019, pb:12.5, src:"Kingspan K118 datasheet verified 05/09/2026"},
   {id:"k118_575",n:"Kingspan Kooltherm K118 57.5mm (45 + 12.5 pb)", t:45, k:0.019, pb:12.5, src:"Kingspan K118 datasheet verified 05/09/2026"},
   {id:"k118_625",n:"Kingspan Kooltherm K118 62.5mm (50 + 12.5 pb)", t:50, k:0.019, pb:12.5, src:"Kingspan K118 datasheet verified 05/09/2026"},
   {id:"k118_725",n:"Kingspan Kooltherm K118 72.5mm (60 + 12.5 pb)", t:60, k:0.019, pb:12.5, src:"Kingspan K118 datasheet verified 05/09/2026"},
   {id:"pl4000_375",n:"Celotex PL4000 37.5mm (25 + 12.5 pb)", t:25, k:0.022, pb:12.5, src:"Soprema (SOPRATHERM PL4000) + BBA 25/7366 verified 05/09/2026"},
   {id:"pl4000_525",n:"Celotex PL4000 52.5mm (40 + 12.5 pb)", t:40, k:0.022, pb:12.5, src:"Soprema (SOPRATHERM PL4000) + BBA 25/7366 verified 05/09/2026"},
   {id:"pl4000_625",n:"Celotex PL4000 62.5mm (50 + 12.5 pb)", t:50, k:0.022, pb:12.5, src:"Soprema (SOPRATHERM PL4000) + BBA 25/7366 verified 05/09/2026"},
   {id:"pl4000_725",n:"Celotex PL4000 72.5mm (60 + 12.5 pb)", t:60, k:0.022, pb:12.5, src:"Soprema (SOPRATHERM PL4000) + BBA 25/7366 verified 05/09/2026"}],
  flatIns:[
   {id:"tr27", n:"Kingspan Thermaroof TR27 LPC/FM", k:0.024, kl:"0.024 at 120mm+, 0.025 at 80–119mm", kt:t=>t<80?0.027:t<120?0.025:0.024, th:[100,110,120,130,140,150,160], src:"Kingspan TR27 brochure 19th issue 03/2026 + BBA 16/5332 (lambda banded by thickness) verified 05/09/2026"},
   {id:"tr26", n:"Kingspan Thermaroof TR26 LPC/FM", k:0.022, th:[100,110,120,130,140,150,160], src:"Kingspan TR26 brochure 16th issue 03/2026 + BBA 16/5332 verified 05/09/2026"},
   {id:"xr4000f",n:"Celotex XR4000 (now Soprema SOPRATHERM XR4000)", k:0.022, th:[110,120,125,130,140,150,165,200], src:"Soprema product page verified 05/09/2026"},
   {id:"xtfr", n:"Unilin Thin-R FR/ALU", k:0.022, th:[100,110,120,125,130,140,150], src:"Unilin handbook 09/2025 verified 05/09/2026"},
   {id:"ecodeck",n:"EcoTherm Eco-Deck (legacy — not in current EcoTherm range; confirm availability)", k:0.022, th:[100,120,130,140,150], src:"EcoTherm datasheet 07/2015 (BBA 07/4487) — product not listed on current range 05/09/2026"}],
  quilt:[
   {id:"lr44", n:"Mineral wool loft roll 0.044 (e.g. Knauf Loft Roll 44)", k:0.044, src:"product designation"},
   {id:"lr40", n:"Mineral wool loft roll 0.040 (e.g. Knauf Loft Roll 40)", k:0.040, src:"product designation"},
   {id:"lr37", n:"Mineral wool 0.037", k:0.037, src:"BR 443 typical"}],

  /* Pitched roof, insulation between and under rafters, ventilated batten space above */
  roofRafter(p){
    const ins=this.rafterIns.find(x=>x.id===p.insulation), und=this.underIns.find(x=>x.id===p.under);
    const rd=p.rafterDepth||150, sp=p.spacing||400, f=47/sp, tb=Math.min(p.thickness,rd);
    const layers=[{n:"External surface — ventilated batten space above (Rse taken as 0.10)",R:0.10}];
    if(tb<rd) layers.push({n:`Ventilated air gap ${rd-tb}mm above insulation (disregarded)`,d:rd-tb,R:0});
    const Rins=tb/1000/ins.k, Rtim=tb/1000/this.timber, Rbr=1/((1-f)/Rins+f/Rtim);
    layers.push({n:`${tb}mm ${ins.n} between 47×${rd} rafters at ${sp} (λ ${ins.k}; bridging ${(f*100).toFixed(1)}%)`,d:tb,R:Rbr,ins:true,bridged:true,Rb:Rins,Rm:Rtim,fb:1-f,fm:f});
    if(und.t>0) layers.push({n:`${und.t}mm insulation under rafters (${und.n.split(" (")[0]}, λ ${und.k})`,d:und.t,R:und.t/1000/und.k,ins2:true});
    layers.push({n:`${und.pb}mm plasterboard`,d:und.pb,R:und.pb/1000/0.21});
    layers.push({n:"Internal surface (Rsi, upward)",R:this.Rsi_roof});
    // combined method across the bridged layer
    const others=layers.filter(l=>!l.bridged).reduce((s,l)=>s+l.R,0);
    const RT_lower=others+Rbr, RT_upper=1/((1-f)/(others+Rins)+f/(others+Rtim)), RT=(RT_upper+RT_lower)/2;
    const U0=1/RT, lvl=this.gapLevel.find(x=>x.id===(p.gapLevel==null?1:p.gapLevel));
    const Rall=Rins+(und.t?und.t/1000/und.k:0);
    const dUg=lvl.dU*Math.pow(Rall/RT,2);
    const U=U0+dUg;
    const notes=[]; if(p.thickness>rd) notes.push(`Insulation ${p.thickness}mm exceeds rafter depth ${rd}mm — only ${rd}mm fits between; increase rafter depth or use under-rafter board.`);
    if(tb===rd) notes.push("Insulation fills the full rafter depth: a breathable underlay is required as no ventilated gap remains.");
    return {kind:"roof-rafter",U,U0,dUg,dUf:0,RT,RT_upper,RT_lower,layers,notes,src:[ins.src,und.src||"BR 443",lvl.n]};
  },

  /* Warm deck flat roof */
  roofFlat(p){
    const ins=Object.assign({},this.flatIns.find(x=>x.id===p.insulation));
    if(ins.kt) ins.k=ins.kt(p.thickness);
    const jd=p.joistDepth||200, sp=p.spacing||400, f=47/sp;
    const layers=[{n:"External surface (Rse)",R:this.Rse_roof},{n:"Waterproof membrane",d:0,R:0.02},
      {n:`${p.thickness}mm ${ins.n} (λ ${ins.k}${ins.kt?" at this thickness":""})`,d:p.thickness,R:p.thickness/1000/ins.k,ins:true},
      {n:"Vapour control layer",d:0,R:0},{n:"18mm plywood/OSB deck",d:18,R:0.018/0.13}];
    const Rair=this.airGapUp(jd), Rtim=jd/1000/this.timber, Rbr=1/((1-f)/Rair+f/Rtim);
    layers.push({n:`Unventilated joist void 47×${jd} at ${sp} (air R ${Rair.toFixed(2)} bridged ${(f*100).toFixed(1)}% by joists)`,d:jd,R:Rbr,bridged:true,Rb:Rair,Rm:Rtim,fb:1-f,fm:f});
    layers.push({n:"12.5mm plasterboard",d:12.5,R:0.0125/0.21},{n:"Internal surface (Rsi, upward)",R:this.Rsi_roof});
    const others=layers.filter(l=>!l.bridged).reduce((s,l)=>s+l.R,0);
    const RT_lower=others+Rbr, RT_upper=1/((1-f)/(others+Rair)+f/(others+Rtim)), RT=(RT_upper+RT_lower)/2;
    const U0=1/RT, Rins=p.thickness/1000/ins.k;
    const dUf = p.fixing==="mech" ? 0.8*50*5*1.13e-5/(p.thickness/1000)*Math.pow(Rins/RT,2) : 0;
    const U=U0+dUf;
    return {kind:"roof-flat",U,U0,dUg:0,dUf,RT,RT_upper,RT_lower,layers,notes:[],src:[ins.src,"BR 443 (deck, void, timber)",p.fixing==="mech"?"ISO 6946 Annex F fasteners (steel, 5/m²)":"fully adhered — no fastener correction"]};
  },

  /* Cold roof — insulation at ceiling level, ventilated loft above */
  roofCeiling(p){
    const q=this.quilt.find(x=>x.id===p.quilt);
    const jd=p.joistDepth||100, sp=p.spacing||400, f=47/sp, tb=Math.min(p.between,jd), to=p.over||0;
    const layers=[{n:"External surface — ventilated loft above (Rse taken as 0.10)",R:0.10}];
    if(to>0) layers.push({n:`${to}mm ${q.n.split(" (")[0]} laid over joists (λ ${q.k})`,d:to,R:to/1000/q.k,ins:true});
    const Rins=tb/1000/q.k, Rtim=tb/1000/this.timber, Rbr=1/((1-f)/Rins+f/Rtim);
    layers.push({n:`${tb}mm quilt between 47×${jd} joists at ${sp} (λ ${q.k}; bridging ${(f*100).toFixed(1)}%)`,d:tb,R:Rbr,bridged:true,Rb:Rins,Rm:Rtim,fb:1-f,fm:f});
    layers.push({n:"12.5mm plasterboard",d:12.5,R:0.0125/0.21},{n:"Internal surface (Rsi, upward)",R:this.Rsi_roof});
    const others=layers.filter(l=>!l.bridged).reduce((s,l)=>s+l.R,0);
    const RT_lower=others+Rbr, RT_upper=1/((1-f)/(others+Rins)+f/(others+Rtim)), RT=(RT_upper+RT_lower)/2;
    const U=1/RT;
    return {kind:"roof-ceiling",U,U0:U,dUg:0,dUf:0,RT,RT_upper,RT_lower,layers,notes:[],src:[q.src,"BR 443 (timber, plasterboard)"]};
  }
});
