<?php
/* The marketing home page. It is PHP only so that the sign-up button can follow the
   before-launch lock in Settings rather than needing an edit at launch. Everything else
   on it is static. */
require __DIR__ . '/app/bootstrap.php';
/* This one is public and cacheable, unlike the account pages bootstrap.php assumes. Kept to a
   minute on purpose: the sign-up button follows the before-launch lock, and a switch whose job
   is to shut the door now must not sit behind a quarter of an hour of stale cache. */
header('Cache-Control: public, max-age=60');
?><!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Building Regulations specification software for architects — Specline</title>
<meta name="description" content="Write a Building Regulations specification for a house extension, loft conversion, garage conversion or new build in England. Eight project types, written to the Approved Documents, with U-value calculations to BS EN ISO 6946 attached. Issued under your own practice's name. For architects and architectural technologists.">
<!-- TODO before launch: set the real domain on the canonical and og:url tags below. -->
<link rel="canonical" href="https://specline.co.uk/">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#0E6E85">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Specline">
<meta property="og:title" content="Building Regulations specification software for architects — Specline">
<meta property="og:description" content="Building Regulations specifications for extensions, lofts, conversions and new build in England, written to the Approved Documents with the U-value working attached. Issued under your own name.">
<meta property="og:url" content="https://specline.co.uk/">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://specline.co.uk/static/img/spec-cover.png">
<meta property="og:image" content="https://specline.co.uk/static/img/spec-cover.png">
<meta property="og:image:alt" content="The cover page of a Building Regulations specification produced in Specline, carrying the practice's own name and address.">
<meta name="twitter:title" content="Building Regulations specification software for architects — Specline">
<meta name="twitter:description" content="Specifications written to the Approved Documents, with the U-value working attached. Issued under your practice's name.">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230E6E85'/%3E%3Cpath d='M13.5 7.5H8V24.5H13.5M18.5 7.5H24V24.5H18.5' fill='none' stroke='%23FBFAF8' stroke-width='3'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
 {"@type":"Organization","@id":"https://specline.co.uk/#org","name":"Specline","legalName":"SY Design Studio Ltd","url":"https://specline.co.uk/","email":"info@specline.co.uk",
  "address":{"@type":"PostalAddress","streetAddress":"49 Durham Avenue","addressLocality":"Hounslow","postalCode":"TW5 0HG","addressCountry":"GB"}},
 {"@type":"SoftwareApplication","name":"Specline","applicationCategory":"BusinessApplication","operatingSystem":"Web","url":"https://specline.co.uk/",
  "description":"Drafts Building Regulations specifications for building control across eight residential project types in England, written to the Approved Documents, with U-value calculations to BS EN ISO 6946 and BS EN ISO 13370 attached.",
  "publisher":{"@id":"https://specline.co.uk/#org"},
  "screenshot":["https://specline.co.uk/static/img/spec-cover.png","https://specline.co.uk/static/img/spec-clauses.png","https://specline.co.uk/static/img/uvalue-working.png","https://specline.co.uk/static/img/detail-sheet.png"],
  "offers":[
   {"@type":"Offer","name":"Solo","price":"39","priceCurrency":"GBP","availability":"https://schema.org/PreOrder","description":"1 user, all 8 project types, unlimited specifications. £39 a month or £390 a year, ex VAT."},
   {"@type":"Offer","name":"Practice","price":"89","priceCurrency":"GBP","availability":"https://schema.org/PreOrder","description":"Up to 5 users, shared job library, the practice's own added clauses. £89 a month or £890 a year, ex VAT."},
   {"@type":"Offer","name":"Per spec","price":"25","priceCurrency":"GBP","availability":"https://schema.org/PreOrder","description":"£25 per issued specification, no subscription, ex VAT."}]},
 {"@type":"FAQPage","mainEntity":[
  {"@type":"Question","name":"Does Specline certify Building Regulations compliance?","acceptedAnswer":{"@type":"Answer","text":"No. Specline drafts the specification. The named designer at the practice remains responsible for its suitability for the project, and compliance of the work is determined by the building control body. Nothing Specline produces is a certificate, an approval or a plan check."}},
  {"@type":"Question","name":"Which regions and project types does Specline cover?","acceptedAnswer":{"@type":"Answer","text":"England, across eight residential project types: house extension, loft conversion, flat conversion, garage conversion, new build house, new build flats, basement conversion and new garage. Wales is planned as a second region."}},
  {"@type":"Question","name":"Whose name goes on the specification?","acceptedAnswer":{"@type":"Answer","text":"The practice's own. The logo, address, named designer and running header come from the practice profile on every plan, including per-specification purchases. Specline's mark never appears on a generated document."}},
  {"@type":"Question","name":"What is a Building Regulations specification?","acceptedAnswer":{"@type":"Answer","text":"A written description of how a building will be constructed, clause by clause, submitted to building control alongside the drawings. It states the construction of each element layer by layer, the U-values achieved, fire and sound performance, ventilation rates, drainage and services. Building control reads it with the plans; the drawings show where things are and the specification says what they are."}},
  {"@type":"Question","name":"Do I need a specification for a house extension?","acceptedAnswer":{"@type":"Answer","text":"A full plans application is assessed on the drawings and the written information submitted with them. Generic notes on a drawing sheet are usually where queries come from, because they are rarely project-specific. A separate specification answers the questions before they are asked, and it is the document Specline produces."}},
  {"@type":"Question","name":"Does it include U-value calculations?","acceptedAnswer":{"@type":"Answer","text":"Yes. Cavity walls, framed walls, floors, basements and roofs are calculated to BS EN ISO 6946 by the combined method with the Annex F corrections for air gaps and wall ties, and to BS EN ISO 13370 for ground floors and heated basements. The working prints in the specification as its own section, so a plan checker can follow the arithmetic rather than take the figure on trust."}},
  {"@type":"Question","name":"Is Specline a specification template?","acceptedAnswer":{"@type":"Answer","text":"No. A template is a document you edit. Specline assembles the specification from a maintained clause library for the project type you choose, numbers the build-up references per job, calculates the U-values for the construction you specify, and produces a PDF and an editable Word file under your own practice identity."}},
  {"@type":"Question","name":"What happens when the Approved Documents change?","acceptedAnswer":{"@type":"Answer","text":"The 2026 editions of Approved Documents L1 and F1 were published on 24 March 2026 and come into force on 24 March 2027. Every specification carries that flag, and the library is maintained against the editions in force. That is why Specline is a subscription rather than a one-off licence."}}]}
]}
</script>
<style>
:root{
  --paper:#F7F8F6; --paper-warm:#FBFAF8; --well:#EEF0EC; --surface:#FFFFFF;
  --ink:#16281F; --ink-2:#4C5C52; --ink-3:#6E7C74; --rule:#C7CDC5; --rule-soft:#DEE2DB;
  --petrol:#0E6E85; --petrol-hi:#0B586B; --petrol-soft:#E0EEF2; --on-petrol:#FBFAF8; --bracket:#0E6E85;
  --pass:#2E7D4F; --pass-soft:#E3F0E8; --hold:#8A6108; --hold-soft:#F6EEDB;
  --wordmark:"Archivo","IBM Plex Sans",Inter,system-ui,sans-serif;
  --sans:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --r-input:2px; --r-ctl:4px; --r-card:6px; --r-modal:10px;
  --shadow-2:0 4px 14px rgba(22,40,31,.10),0 24px 60px rgba(22,40,31,.12);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#10191F; --paper-warm:#17222A; --well:#0B1319; --surface:#17222A;
  --ink:#EDEAE4; --ink-2:#A8B4BC; --ink-3:#78868F; --rule:#263239; --rule-soft:#1F2A31;
  --petrol:#2E9EB8; --petrol-hi:#63BDD1; --petrol-soft:#0F323C; --on-petrol:#08141A; --bracket:#2E9EB8;
  --pass:#5CB981; --pass-soft:#142A1E; --hold:#D7A54A; --hold-soft:#2B2113;
  --shadow-2:0 4px 16px rgba(0,0,0,.5),0 24px 70px rgba(0,0,0,.55);}}
:root[data-theme="dark"]{
  --paper:#10191F; --paper-warm:#17222A; --well:#0B1319; --surface:#17222A;
  --ink:#EDEAE4; --ink-2:#A8B4BC; --ink-3:#78868F; --rule:#263239; --rule-soft:#1F2A31;
  --petrol:#2E9EB8; --petrol-hi:#63BDD1; --petrol-soft:#0F323C; --on-petrol:#08141A; --bracket:#2E9EB8;
  --pass:#5CB981; --pass-soft:#142A1E; --hold:#D7A54A; --hold-soft:#2B2113;
  --shadow-2:0 4px 16px rgba(0,0,0,.5),0 24px 70px rgba(0,0,0,.55);}

*{box-sizing:border-box}
html{color-scheme:light dark;scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--petrol);text-decoration:none}
a:hover{color:var(--petrol-hi);text-decoration:underline}
button{font:inherit;color:inherit;cursor:pointer}
:focus-visible{outline:2px solid var(--petrol);outline-offset:2px}
::selection{background:var(--petrol-soft)}
h1,h2,h3{font-family:var(--wordmark);font-weight:700;letter-spacing:-.025em;line-height:1.08;margin:0;text-wrap:balance}
h2{font-size:clamp(26px,3.2vw,36px);margin-bottom:12px}
h3{font-size:19px;letter-spacing:-.015em;line-height:1.3}
p{margin:0 0 14px}
.lede{color:var(--ink-2);font-size:17.5px;max-width:60ch}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-3);margin:0 0 14px;display:flex;gap:12px;align-items:center}
.eyebrow::after{content:"";flex:0 0 36px;height:1px;background:var(--rule)}
.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
.wrap{max-width:1140px;margin:0 auto;padding:0 28px}
@media(max-width:640px){.wrap{padding:0 18px}}
section{padding:88px 0;border-top:1px solid var(--rule-soft)}
section.tight{padding:64px 0}
@media(max-width:760px){section{padding:60px 0}}

/* buttons */
.btn{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--rule);background:var(--surface);color:var(--ink);border-radius:var(--r-ctl);padding:11px 18px;font-size:15px;font-weight:500;line-height:1.2;white-space:nowrap;text-decoration:none}
.btn:hover{border-color:var(--ink-2);text-decoration:none;color:var(--ink)}
.btn-primary{background:var(--petrol);border-color:var(--petrol);color:var(--on-petrol)}
.btn-primary:hover{background:var(--petrol-hi);border-color:var(--petrol-hi);color:var(--on-petrol)}
.btn-quiet{background:transparent;border-color:transparent;color:var(--ink-2)}
.btn-quiet:hover{background:var(--well);border-color:transparent}

/* header */
.top{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--paper) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--rule-soft)}
.top .wrap{display:flex;align-items:center;gap:22px;height:64px}
.lockup{display:inline-flex;align-items:stretch;gap:7px;height:28px;text-decoration:none}
.lockup svg{width:6.7px;height:28px;display:block;overflow:visible}
.lockup b{align-self:center;font-family:var(--wordmark);font-weight:700;font-size:19.6px;letter-spacing:-.035em;line-height:.95;color:var(--ink)}
.lockup:hover{text-decoration:none}
.nav{display:flex;gap:4px;margin-left:8px}
.nav a{color:var(--ink-2);padding:8px 11px;border-radius:var(--r-ctl);font-size:14.5px}
.nav a:hover{background:var(--well);color:var(--ink);text-decoration:none}
.top .spacer{flex:1}
@media(max-width:820px){.nav{display:none}.top .wrap{height:58px}}
@media(max-width:640px){.top .btn-primary{display:none}.top .wrap{gap:12px}.eyebrow::after{display:none}}

/* hero */
.hero{padding:76px 0 72px;border-top:0}
.hero .wrap{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);gap:56px;align-items:center}
@media(max-width:900px){.hero .wrap{grid-template-columns:1fr;gap:40px}}
.hero h1{font-size:clamp(36px,5.2vw,62px)}
.hero h1 em{font-style:normal;color:var(--petrol)}
.hero .lede{margin:22px 0 28px}
.hero .actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.hero .note{font-family:var(--mono);font-size:12px;color:var(--ink-3);margin:16px 0 0}

/* the signature: a wall drawn to scale, settling on its U-value */
.spec{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-card);padding:22px 24px 20px;position:relative}
.spec .shead{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px}
.spec .shead .eyebrow{margin:0}.spec .shead .eyebrow::after{display:none}
.pill{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;padding:3px 10px;border-radius:100px;white-space:nowrap}
.pill.pass{color:var(--pass);background:var(--pass-soft)}
.pill.hold{color:var(--hold);background:var(--hold-soft)}
.ubig{display:flex;align-items:baseline;gap:10px;margin:2px 0 16px}
.ubig b{font-family:var(--wordmark);font-weight:700;font-size:64px;line-height:1;letter-spacing:-.035em;font-variant-numeric:tabular-nums;min-width:3.2ch}
.ubig .unit{display:flex;flex-direction:column;line-height:1.25;font-size:13px;color:var(--ink-2)}
.ubig .unit small{color:var(--ink-3);font-family:var(--mono);font-size:11px}
.lbar{display:flex;height:40px;border-radius:var(--r-input);overflow:hidden;border:1px solid var(--rule)}
.lbar span{display:block;height:100%;transform-origin:left center;border-right:1px solid rgba(22,40,31,.18);animation:draw .6s cubic-bezier(.2,.7,.2,1) both;animation-delay:calc(var(--i)*160ms + 200ms)}
.lbar span:last-child{border-right:0}
.lbar span.air{background-image:repeating-linear-gradient(135deg,transparent 0 4px,rgba(22,40,31,.14) 4px 5px)}
.lkey{font-family:var(--mono);font-size:11px;color:var(--ink-2);line-height:1.6;margin:10px 0 0}
.clause{margin:18px 0 0;padding-top:16px;border-top:1px solid var(--rule-soft)}
.clause h4{font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;margin:0 0 6px;display:flex;gap:9px;align-items:baseline}
.clause h4 i{font-style:normal;font-family:var(--mono);color:var(--petrol);font-weight:500}
.clause p{font-size:12.5px;color:var(--ink-2);margin:0;line-height:1.55;max-width:none}
.clause .tl{color:var(--petrol);font-weight:500;font-size:12px;margin:0 0 5px}
.reveal{animation:rise .5s ease both}
.clause .tl{animation-delay:1.35s}.clause p{animation-delay:1.55s}
@keyframes draw{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.corner{position:absolute;width:18px;height:18px;border:2px solid var(--bracket);pointer-events:none}
.corner.tl{top:-7px;left:-7px;border-right:0;border-bottom:0}
.corner.br{bottom:-7px;right:-7px;border-left:0;border-top:0}

/* three columns */
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0;border:1px solid var(--rule);border-radius:var(--r-card);background:var(--surface);overflow:hidden}
.col{padding:26px 26px 24px;border-left:1px solid var(--rule)}
.col:first-child{border-left:0}
@media(max-width:820px){.col{border-left:0;border-top:1px solid var(--rule)}.col:first-child{border-top:0}}
.col .eyebrow{margin-bottom:10px}
.col p{color:var(--ink-2);font-size:15px;margin:8px 0 0}
.col .ref{font-family:var(--mono);color:var(--petrol);background:var(--petrol-soft);border-radius:var(--r-input);padding:1px 6px;font-size:13px}

/* types */
.types{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.type{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-card);padding:16px 17px 14px;display:flex;flex-direction:column;gap:5px;min-height:112px}
.type .tk{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3)}
.type .tk b{color:var(--petrol);font-weight:500}
.type .tn{font-weight:600;font-size:16px;margin-top:4px}
.type .td{color:var(--ink-2);font-size:13.5px;line-height:1.4}
.total{font-family:var(--mono);font-size:12px;color:var(--ink-3);margin:14px 0 0}

/* what it produces — real output, not mock-ups */
.shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;margin-top:34px}
@media(max-width:820px){.shots{grid-template-columns:1fr}}
.shot{margin:0;background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-card);overflow:hidden;display:flex;flex-direction:column}
.shot img{display:block;width:100%;height:auto;border-bottom:1px solid var(--rule-soft);background:#fff}
.shot figcaption{padding:14px 18px 16px}
.shot .cap{font-weight:600;font-size:15px;margin:0 0 4px}
.shot .sub{color:var(--ink-2);font-size:14px;line-height:1.5;margin:0}
.shot .eyebrow{margin:0 0 8px}
.shotnote{font-family:var(--mono);font-size:12px;color:var(--ink-3);margin:18px 0 0}

/* practice section */
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:56px;align-items:start}
@media(max-width:820px){.two{grid-template-columns:1fr;gap:32px}}
.list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
.list li{padding:16px 0;border-top:1px solid var(--rule-soft);display:grid;grid-template-columns:34px minmax(0,1fr);gap:14px;align-items:start}
.list li:first-child{border-top:0}
.list li i{font-style:normal;font-family:var(--mono);color:var(--petrol);font-size:12px;line-height:1.7;letter-spacing:.06em}
.list li b{display:block;font-weight:600;margin-bottom:2px}
.list li span{color:var(--ink-2);font-size:15px}

/* the boundary */
.boundary{background:var(--well);border-top:1px solid var(--rule-soft)}
.boundary .wrap{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:48px;align-items:center}
@media(max-width:820px){.boundary .wrap{grid-template-columns:1fr}}
.boundary blockquote{margin:0;font-family:var(--wordmark);font-weight:600;font-size:clamp(24px,3vw,34px);letter-spacing:-.02em;line-height:1.15}
.boundary blockquote em{font-style:normal;color:var(--petrol)}
.boundary p{color:var(--ink-2);font-size:15.5px}

/* pricing */
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin-top:8px}
.plan{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-card);padding:24px 24px 22px;display:flex;flex-direction:column;gap:6px;position:relative}
.plan.mid{border-color:var(--petrol)}
.plan .eyebrow{margin-bottom:6px}.plan .eyebrow::after{display:none}
.plan .price{font-family:var(--wordmark);font-weight:700;font-size:40px;letter-spacing:-.03em;line-height:1;font-variant-numeric:tabular-nums;margin:4px 0 2px}
.plan .price small{font-family:var(--sans);font-weight:500;font-size:14px;letter-spacing:0;color:var(--ink-2)}
.plan .alt{font-family:var(--mono);font-size:12px;color:var(--ink-3);margin:0 0 12px}
.plan ul{margin:0 0 18px;padding:0;list-style:none;display:flex;flex-direction:column;gap:6px;font-size:14.5px;color:var(--ink-2);flex:1}
.plan li::before{content:"—";color:var(--petrol);margin-right:8px}
.plan .soon{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);text-align:center;padding:9px;border:1px dashed var(--rule);border-radius:var(--r-ctl)}
.founder{margin-top:22px;border:1px solid var(--rule);background:var(--hold-soft);border-radius:var(--r-card);padding:14px 18px;display:flex;gap:14px;align-items:center;flex-wrap:wrap;font-size:14.5px}
.founder .pill{flex:none}
.vat{font-family:var(--mono);font-size:12px;color:var(--ink-3);margin:12px 0 0}

/* waiting list */
.join{background:var(--surface);border:1px solid var(--rule);border-radius:var(--r-card);padding:24px;display:flex;flex-direction:column;gap:14px}
.join label{display:flex;flex-direction:column;gap:5px;font-size:13.5px;font-weight:500;color:var(--ink-2)}
.join label .req{position:absolute;left:-9999px}
.join input[type=text],.join input[type=email]{border:1px solid var(--rule);background:var(--paper);border-radius:var(--r-ctl);padding:11px 12px;font:inherit;font-size:15px;color:var(--ink);width:100%}
.join input:focus{border-color:var(--petrol);outline:none;background:var(--surface)}
.join input[aria-invalid="true"]{border-color:var(--hold)}
.join .pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:520px){.join .pair{grid-template-columns:1fr}}
.join .check{flex-direction:row;align-items:flex-start;gap:10px;font-weight:400;font-size:14px;line-height:1.5}
.join .check input{margin:3px 0 0;accent-color:var(--petrol);width:16px;height:16px;flex:none}
.join .hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.join button{justify-content:center;width:100%}
.join button:disabled{opacity:.5;cursor:not-allowed}
.jmsg{margin:0;font-size:14.5px;padding:11px 13px;border-radius:var(--r-ctl);border:1px solid var(--rule)}
.jmsg.ok{color:var(--pass);background:var(--pass-soft);border-color:transparent}
.jmsg.bad{color:var(--hold);background:var(--hold-soft);border-color:transparent}

/* faq */
.faq{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:0 40px}
.faq dt{font-weight:600;padding:18px 0 4px;border-top:1px solid var(--rule-soft)}
.faq dd{margin:0 0 14px;color:var(--ink-2);font-size:15px}

/* footer */
footer{border-top:1px solid var(--rule);padding:40px 0 48px;font-size:13.5px;color:var(--ink-2)}
footer .wrap{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap;align-items:flex-start}
footer p{margin:0 0 4px}
footer .links{display:flex;gap:16px;flex-wrap:wrap}
footer .links span{color:var(--ink-3)}

/* sign-in */
.overlay{position:fixed;inset:0;z-index:80;background:rgba(10,18,14,.5);display:flex;align-items:center;justify-content:center;padding:24px;backdrop-filter:blur(3px)}
.overlay[hidden]{display:none}
.dialog{background:var(--surface);border-radius:var(--r-modal);max-width:460px;width:100%;box-shadow:var(--shadow-2);padding:30px 32px 28px;position:relative}
.dialog h2{font-size:26px;margin-bottom:8px}
.dialog p{color:var(--ink-2);font-size:15px}
.closeX{position:absolute;top:12px;right:14px;border:0;background:none;font-size:22px;color:var(--ink-3);line-height:1;padding:6px 10px;border-radius:var(--r-ctl)}
.closeX:hover{background:var(--well);color:var(--ink)}
.dialog .field{border:1px dashed var(--rule);border-radius:var(--r-input);padding:10px 12px;font-family:var(--mono);font-size:12px;color:var(--ink-3);margin:14px 0 18px}

@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.lbar span{transform:none}.reveal{opacity:1}}
</style>
</head>
<body>

<header class="top">
  <div class="wrap">
    <a class="lockup" href="#top" aria-label="Specline"><svg viewBox="0 0 6.7 28" aria-hidden="true"><path d="M5.7 1H1V27H5.7" fill="none" stroke="var(--bracket)" stroke-width="2" stroke-linejoin="miter"/></svg><b aria-hidden="true">Specline</b><svg viewBox="0 0 6.7 28" aria-hidden="true"><path d="M1 1H5.7V27H1" fill="none" stroke="var(--bracket)" stroke-width="2" stroke-linejoin="miter"/></svg></a>
    <nav class="nav" aria-label="Sections">
      <a href="#what">What you issue</a>
      <a href="#output">The document</a>
      <a href="#types">Project types</a>
      <a href="#practices">For practices</a>
      <a href="#pricing">Pricing</a>
    </nav>
    <span class="spacer"></span>
    <a class="btn btn-quiet" href="/account/login.php">Sign in</a>
<?php if (site_locked()): ?>
    <a class="btn btn-primary" href="#join">Join the waiting list</a>
<?php else: ?>
    <a class="btn btn-primary" href="/account/signup.php">Create an account</a>
<?php endif; ?>
  </div>
</header>

<main id="top">
<section class="hero">
  <div class="wrap">
    <div>
      <p class="eyebrow">Building Regulations · England · for building control</p>
      <h1>The specification, written to the Approved Documents. <em>Issued under your name.</em></h1>
      <p class="lede">Specline drafts Building Regulations specifications for extensions, lofts, conversions and new build, with the U-value working attached. You check it, put your practice's name on it, and issue it to building control.</p>
      <div class="actions">
        <a class="btn btn-primary" href="#join">Join the waiting list</a>
        <a class="btn" href="#what">See what you issue</a>
      </div>
      <p class="note">Not open for sign-up yet. Founding-member pricing for the first 30 practices.</p>
    </div>

    <div class="spec" aria-label="Example: a full fill cavity wall, calculated live">
      <span class="corner tl" aria-hidden="true"></span><span class="corner br" aria-hidden="true"></span>
      <div class="shead"><p class="eyebrow">EW1 · Full fill cavity wall</p><span class="pill pass" id="pill">Calculating</span></div>
      <div class="ubig"><b id="uval" aria-live="polite">0.35</b><span class="unit">W/m²K<small>target 0.18 · new element</small></span></div>
      <div class="lbar" role="img" aria-label="103 mm facing brickwork, 10 mm residual cavity, 90 mm Kooltherm K106, 100 mm aircrete block, 10 mm dab gap, 12.5 mm plasterboard">
        <span style="flex:103;background:#A8705A;--i:0"></span>
        <span class="air" style="flex:10;background:#F1F0EC;--i:1"></span>
        <span style="flex:90;background:#E4CF8A;--i:2"></span>
        <span style="flex:100;background:#C3C7CB;--i:3"></span>
        <span class="air" style="flex:10;background:#F1F0EC;--i:4"></span>
        <span style="flex:12.5;background:#EDE6DA;--i:5"></span>
      </div>
      <p class="lkey">103 mm facing brickwork · 10 mm residual cavity · 90 mm Kingspan Kooltherm K106 (λ 0.019) · 100 mm aircrete block 0.15 W/mK · 12.5 mm plasterboard on dabs</p>
      <div class="clause">
        <h4 class="reveal" style="animation-delay:1.2s"><i>EW1</i>Full fill cavity wall</h4>
        <p class="tl reveal">To achieve minimum U-value of 0.18 W/m²K (actual U-value achieved 0.17 W/m²K)</p>
        <p class="reveal">External cavity wall to be built up as a 103mm facing brick outer leaf matched to the existing dwelling, a 100mm cavity fully filled with 90mm Kingspan Kooltherm K106, and a 100mm aircrete blockwork inner leaf… calculated to BS EN ISO 6946 allowing for mortar joints, wall ties and an air-gap correction.</p>
      </div>
    </div>
  </div>
</section>

<section id="what">
  <div class="wrap">
    <p class="eyebrow">What you issue</p>
    <h2>One document, three parts, all from the same library</h2>
    <p class="lede" style="margin-bottom:34px">Every specification is assembled from a library written from the Approved Documents in plain, confident prose. Not numbered legal clauses: the construction, layer by layer, with named products and their alternatives.</p>
    <div class="cols">
      <div class="col"><p class="eyebrow">Part A</p><h3>Construction build-ups</h3>
        <p>Numbered per job, in the order you pick them: <span class="ref">EW1</span> <span class="ref">GF1</span> <span class="ref">RF1</span>. The same references go on your plans and sections. Cavity walls, floors, basements and roofs are configurable layer by layer; the rest are written build-ups you tick.</p></div>
      <div class="col"><p class="eyebrow">Part B</p><h3>General notes by topic</h3>
        <p>Structure, fire, ventilation, drainage, services and the rest, arranged in the order a building control officer reads a pack. One subject, one note: no repeated or contradicting clauses.</p></div>
      <div class="col"><p class="eyebrow">Section 4</p><h3>U-value working</h3>
        <p>Every calculated build-up carries its working to BS EN ISO 6946 with the Annex F corrections, or BS EN ISO 13370 for ground floors and heated basements, with manufacturer-verified conductivities. It is what makes the figure defensible to a plan checker.</p></div>
    </div>
  </div>
</section>

<section id="output">
  <div class="wrap">
    <p class="eyebrow">What comes out of it</p>
    <h2>The document, and the working behind it</h2>
    <p class="lede">A specimen house extension, produced in Specline and shown exactly as it prints. The practice name, address and accent on it are the practice's own — Specline's mark never appears on a specification.</p>
    <div class="shots">
      <figure class="shot">
        <img src="/static/img/spec-cover.png" width="1640" height="1706" loading="lazy" decoding="async"
             alt="Cover page of a Building Regulations specification for a house extension, showing the practice name and address, the project, site address, job number, local authority, application type and revision, above the construction build-up schedule.">
        <figcaption><p class="eyebrow">Cover and schedule</p><p class="cap">Your identity, and the build-up schedule</p>
          <p class="sub">The cover carries the practice's logo or name, the job record and the responsibility statement. Underneath it, every build-up on the job with its reference and the standard it meets.</p></figcaption>
      </figure>
      <figure class="shot">
        <img src="/static/img/spec-clauses.png" width="1640" height="1720" loading="lazy" decoding="async"
             alt="Part A of the specification: trench fill foundation and full fill cavity wall clauses written out layer by layer, with target U-values and designer notes.">
        <figcaption><p class="eyebrow">Part A</p><p class="cap">Construction, layer by layer</p>
          <p class="sub">Flowing prose rather than numbered legal clauses: the construction described as it is built, with named products, their alternatives, the standards cited inline, and notes to the designer set apart in grey.</p></figcaption>
      </figure>
      <figure class="shot">
        <img src="/static/img/uvalue-working.png" width="2808" height="1800" loading="lazy" decoding="async"
             alt="U-value working for a full fill cavity wall: layer by layer thermal resistances, upper and lower resistance limits, the Annex F air gap and wall tie corrections, and the resulting U-value of 0.18 W/m²K against a target of 0.18.">
        <figcaption><p class="eyebrow">Section 4</p><p class="cap">U-value working you can hand over</p>
          <p class="sub">Every calculated build-up prints its arithmetic: layer resistances, the upper and lower limits of the combined method, the Annex F corrections for air gaps and wall ties, and the conductivity source for each material.</p></figcaption>
      </figure>
      <figure class="shot">
        <img src="/static/img/detail-sheet.png" width="2384" height="1440" loading="lazy" decoding="async"
             alt="A typical vertical section through a full fill cavity wall at 1:10, dimensioned and annotated, with each annotation quoted from the specification clause beside it.">
        <figcaption><p class="eyebrow">Detail sheets</p><p class="cap">The section, drawn from the same clause</p>
          <p class="sub">Each build-up draws as a dimensioned section at 1:10, and every annotation on it is quoted from the clause, so the drawing cannot drift away from the specification.</p></figcaption>
      </figure>
    </div>
    <p class="shotnote">Specimen project. No client, address or job of anyone's appears on this page.</p>
  </div>
</section>

<section id="types">
  <div class="wrap">
    <p class="eyebrow">Project types · England</p>
    <h2>Eight residential project types</h2>
    <p class="lede" style="margin-bottom:30px">Each carries its own categories, build-ups and notes. Pick the type, work through the categories, and the document builds as you go.</p>
    <div class="types">
      <div class="type"><span class="tk"><b>EXT</b><span>21 build-ups · 53 notes</span></span><span class="tn">House extension</span><span class="td">Single and two storey, rear and side</span></div>
      <div class="type"><span class="tk"><b>LFT</b><span>15 build-ups · 36 notes</span></span><span class="tn">Loft conversion</span><span class="td">Dormer, hip to gable, room in roof</span></div>
      <div class="type"><span class="tk"><b>FLT</b><span>14 build-ups · 37 notes</span></span><span class="tn">Flat conversion</span><span class="td">Material change of use, Part E</span></div>
      <div class="type"><span class="tk"><b>GAR</b><span>20 build-ups · 36 notes</span></span><span class="tn">Garage conversion</span><span class="td">Integral and detached</span></div>
      <div class="type"><span class="tk"><b>NBH</b><span>16 build-ups · 58 notes</span></span><span class="tn">New build house</span><span class="td">Full notional dwelling assessment</span></div>
      <div class="type"><span class="tk"><b>NBF</b><span>16 build-ups · 55 notes</span></span><span class="tn">New build flats</span><span class="td">Separating construction, common parts</span></div>
      <div class="type"><span class="tk"><b>BSM</b><span>10 build-ups · 32 notes</span></span><span class="tn">Basement conversion</span><span class="td">Underpinning, tanking, BS 8102</span></div>
      <div class="type"><span class="tk"><b>GBD</b><span>12 build-ups · 23 notes</span></span><span class="tn">New garage</span><span class="td">Detached and attached, unheated</span></div>
    </div>
    <p class="total">124 build-ups · 330 notes · conductivities verified against manufacturer and BBA data · Wales planned as a second region</p>
  </div>
</section>

<section id="practices">
  <div class="wrap two">
    <div>
      <p class="eyebrow">For practices</p>
      <h2>Written for the desk of an architectural technologist</h2>
      <p class="lede">Built in a practice that issues these documents every week, for architects, technologists and small practices that would rather spend the afternoon on the drawings.</p>
    </div>
    <ul class="list">
      <li><i>01</i><div><b>Your name on the document, on every plan</b><span>Logo, address, named designer and running header come from your practice profile. Specline's mark never appears on a specification.</span></div></li>
      <li><i>02</i><div><b>References that match the drawings</b><span>Build-ups number themselves per job in the order you choose them, so EW1 on the specification is EW1 on the section.</span></div></li>
      <li><i>03</i><div><b>Practice standards stated the same way every time</b><span>FD30S doorsets, BS 5839-6 Grade D1 LD2 alarms, the escape window figures, hot water to Approved Document G3. Where the standard exceeds the Approved Document minimum, the document says so.</span></div></li>
      <li><i>04</i><div><b>Current, and flagged when it is about to change</b><span>Approved Documents L1 and F1 2026 come into force on 24 March 2027. Every specification carries the flag, and the library is maintained against the editions in force.</span></div></li>
      <li><i>05</i><div><b>Saved jobs, revisions, issue history</b><span>P01 to P02 with a record of what went out and when. Reopen any job and carry on.</span></div></li>
    </ul>
  </div>
</section>

<section class="boundary tight">
  <div class="wrap">
    <blockquote>Specline drafts the specification. <em>Building control approves the work.</em></blockquote>
    <div>
      <p>Nothing Specline produces is a certificate, an approval or a plan check. The named designer at your practice remains responsible for the suitability of the specification for the project, and every clause and table reference is to be confirmed against the Approved Documents in force at the date of submission.</p>
      <p>That sentence prints on the cover of every document, in your practice's voice, so the responsibility is exactly where it has always been.</p>
    </div>
  </div>
</section>

<section id="pricing">
  <div class="wrap">
    <p class="eyebrow">Pricing · ex VAT</p>
    <h2>A subscription, because the regulations change</h2>
    <p class="lede">A perpetual licence would leave you with a library that stops being current. Specline is maintained against the Approved Documents in force, and that is what the subscription pays for.</p>
    <div class="plans">
      <div class="plan"><p class="eyebrow">Solo</p><p class="price">£39<small> / month</small></p><p class="alt">or £390 a year · ten months' money</p>
        <ul><li>1 user</li><li>All 8 project types</li><li>Unlimited specifications</li><li>Your practice's identity on every document</li></ul>
        <p class="soon">Coming soon</p></div>
      <div class="plan mid"><p class="eyebrow">Practice</p><p class="price">£89<small> / month</small></p><p class="alt">or £890 a year · ten months' money</p>
        <ul><li>Up to 5 users</li><li>Shared job library</li><li>Your practice's own added clauses</li><li>Your practice's identity on every document</li></ul>
        <p class="soon">Coming soon</p></div>
      <div class="plan"><p class="eyebrow">Per spec</p><p class="price">£25<small> / issued spec</small></p><p class="alt">no subscription</p>
        <ul><li>Pay when you issue</li><li>All 8 project types</li><li>Your practice's identity on every document</li></ul>
        <p class="soon">Coming soon</p></div>
    </div>
    <div class="founder"><span class="pill hold">Founding members</span><span>The first 30 subscribing practices keep their joining price for as long as they stay subscribed.</span></div>
    <p class="vat">All prices exclude VAT. No payments are being taken yet. Join the waiting list and you will hear first.</p>
  </div>
</section>

<section id="join">
  <div class="wrap two">
    <div>
      <p class="eyebrow">Waiting list</p>
      <h2>Be told when it opens</h2>
      <p class="lede">Specline is not open for sign-up yet. Leave your email and you will hear first, with founding-member pricing held for the first 30 practices.</p>
      <p style="color:var(--ink-2);font-size:15px">We will only email you about Specline, we will not pass your address to anyone, and every message has a one-click way off the list. What we keep and for how long is set out in the <a href="/privacy.html">privacy notice</a>.</p>
    </div>
    <form class="join" id="joinForm" method="post" action="/waitlist.php" novalidate>
      <label>Email address<span class="req">required</span>
        <input type="email" name="email" id="jEmail" autocomplete="email" required placeholder="you@practice.co.uk"></label>
      <div class="pair">
        <label>Your name<input type="text" name="name" autocomplete="name" placeholder="Optional"></label>
        <label>Practice<input type="text" name="practice" autocomplete="organization" placeholder="Optional"></label>
      </div>
      <p class="hp" aria-hidden="true"><label>Website<input type="text" name="website" tabindex="-1" autocomplete="off"></label></p>
      <label class="check"><input type="checkbox" name="consent" value="yes" id="jConsent" required>
        <span>Yes, email me when Specline opens. I can ask to be removed at any time.</span></label>
      <button class="btn btn-primary" type="submit" id="jSubmit">Join the waiting list</button>
      <p class="jmsg" id="jMsg" role="status" aria-live="polite" hidden></p>
    </form>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Questions</p>
    <h2>Straight answers</h2>
    <dl class="faq" style="margin-top:22px">
      <div><dt>What is a Building Regulations specification?</dt><dd>A written description of how a building will be constructed, clause by clause, submitted to building control alongside the drawings. It states the construction of each element layer by layer, the U-values achieved, fire and sound performance, ventilation rates, drainage and services. The drawings show where things are; the specification says what they are.</dd></div>
      <div><dt>Do I need one for a house extension?</dt><dd>A full plans application is assessed on the drawings and the written information sent with them. Generic notes on a drawing sheet are where most queries come from, because they are rarely project-specific. A separate specification answers those questions before they are asked.</dd></div>
      <div><dt>Does it include U-value calculations?</dt><dd>Yes, and it shows the working. Cavity walls, framed walls, floors, basements and roofs are calculated to BS EN ISO 6946 by the combined method with the Annex F corrections for air gaps and wall ties, and to BS EN ISO 13370 for ground floors and heated basements. The arithmetic prints as its own section so a plan checker can follow it rather than take the figure on trust.</dd></div>
      <div><dt>Is this a specification template?</dt><dd>No. A template is a document you edit and hope you edited everywhere. Specline assembles the specification from a maintained library for the project type, numbers the build-up references per job, calculates the U-values for the construction you specify, and produces the PDF and the Word file under your own identity.</dd></div>
      <div><dt>Does Specline certify Building Regulations compliance?</dt><dd>No. Specline drafts the specification. The named designer at the practice remains responsible for its suitability for the project, and compliance of the work is determined by the building control body. Nothing Specline produces is a certificate, an approval or a plan check.</dd></div>
      <div><dt>Which regions and project types does it cover?</dt><dd>England, across eight residential project types: house extension, loft conversion, flat conversion, garage conversion, new build house, new build flats, basement conversion and new garage. Wales is planned as a second region.</dd></div>
      <div><dt>Whose name goes on the specification?</dt><dd>Yours. The logo, address, named designer and running header come from your practice profile on every plan, including per-specification purchases. Specline's mark never appears on a generated document.</dd></div>
      <div><dt>What happens when the Approved Documents change?</dt><dd>The 2026 editions of Approved Documents L1 and F1 were published on 24 March 2026 and come into force on 24 March 2027. Every specification carries that flag, and the library is maintained against the editions in force. That is why Specline is a subscription rather than a one-off licence.</dd></div>
      <div><dt>Where does the wording come from?</dt><dd>It is written from the Approved Documents and the British Standards they cite, in our own words. Nothing is copied from a commercial specification library. Every figure in it has been checked against the source, with the date recorded.</dd></div>
      <div><dt>Can I export to Word?</dt><dd>Yes. Every specification downloads as a PDF and as an editable .docx, both carrying the U-value working as their own section. The Word file is the one to edit if you want to add a project-specific clause of your own before issue.</dd></div>
    </dl>
  </div>
</section>
</main>

<footer>
  <div class="wrap">
    <div>
      <p><b>Specline</b> is a trading name of SY Design Studio Ltd.</p>
      <p>49 Durham Avenue, Hounslow TW5 0HG · <a href="mailto:info@specline.co.uk">info@specline.co.uk</a></p>
      <p>© 2026 SY Design Studio Ltd. All rights reserved.</p>
    </div>
    <div class="links"><a href="/terms.html">Terms of supply</a><a href="/privacy.html">Privacy notice</a></div>
  </div>
</footer>

<script>
/* The hero: the wall draws in layer by layer, and the U-value settles from the uninsulated
   figure to the calculated one. Static at the final state when motion is reduced. */
(function(){
  const u=document.getElementById('uval'), pill=document.getElementById('pill');
  const from=0.35, to=0.17;
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const done=()=>{ u.textContent=to.toFixed(2); pill.textContent='Within target'; };
  if(still){ done(); return; }
  const t0=performance.now()+700, dur=1300;
  (function step(now){
    const k=Math.min(1,Math.max(0,(now-t0)/dur)), e=1-Math.pow(1-k,3);
    u.textContent=(from+(to-from)*e).toFixed(2);
    if(k<1) requestAnimationFrame(step); else done();
  })(performance.now());
})();
/* Waiting list: submit without leaving the page, and say plainly what happened. */
(function(){
  const f=document.getElementById('joinForm'), msg=document.getElementById('jMsg'),
        btn=document.getElementById('jSubmit'), email=document.getElementById('jEmail'),
        consent=document.getElementById('jConsent');
  const say=(text,ok)=>{ msg.hidden=false; msg.className='jmsg '+(ok?'ok':'bad'); msg.textContent=text; };
  f.addEventListener('submit', async e=>{
    e.preventDefault();
    email.setAttribute('aria-invalid','false');
    if(!email.value.trim() || !email.checkValidity()){ email.setAttribute('aria-invalid','true'); email.focus(); return say('Please enter a valid email address.',false); }
    if(!consent.checked){ consent.focus(); return say('Please tick the box so we know we may email you.',false); }
    btn.disabled=true; const was=btn.textContent; btn.textContent='Adding you…';
    try{
      const r=await fetch(f.action,{method:'POST',body:new FormData(f),headers:{'Accept':'application/json'}});
      let d={}; try{ d=await r.json(); }catch(_){}
      if(r.ok && d.ok){ say(d.message||'Thank you. You are on the list.',true); f.reset(); btn.textContent='On the list'; return; }
      say(d.message||'That did not go through. Please email info@specline.co.uk and we will add you.',false);
    }catch(_){
      say('We could not reach the server. Please email info@specline.co.uk and we will add you.',false);
    }
    btn.disabled=false; btn.textContent=was;
  });
})();
</script>
</body>
</html>
