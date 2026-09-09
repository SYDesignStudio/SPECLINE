/* ===== Minimal .docx writer, no dependencies =====================================
   A .docx is a ZIP of XML parts. This writes one directly, so the app has no npm
   package and no CDN script to load, and it works offline in the Playwright tests.

   Entries are STORED (compression method 0). The files are a few hundred KB rather
   than a few tens, which does not matter for a specification, and it removes any
   need for a deflate implementation.

   Word needs, at minimum:
     [Content_Types].xml        what each part is
     _rels/.rels                points at the main document
     word/document.xml          the content
     word/styles.xml            named styles the content refers to
   plus, for the practice logo:
     word/_rels/document.xml.rels  relationship from the document to the image
     word/media/logo.<ext>         the image bytes

   Measurements: twips (1/20 pt) for spacing and table widths; half-points for font
   size; EMU (914400 per inch) for image extents.                                   */

const DOCX = (() => {

  /* ---------- CRC32, needed by the ZIP central directory ---------- */
  const CRC_TABLE = (() => {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[n] = c >>> 0;
    }
    return t;
  })();
  function crc32(bytes) {
    let c = 0xFFFFFFFF;
    for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }

  const utf8 = s => new TextEncoder().encode(s);

  /* ---------- ZIP (stored) ---------- */
  function zip(files) {
    // files: [{name, data:Uint8Array}]
    const chunks = [], central = [];
    let offset = 0;

    const dosTime = () => {
      const d = new Date();
      const time = (d.getHours() << 11) | (d.getMinutes() << 5) | (Math.floor(d.getSeconds() / 2));
      const date = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
      return { time, date };
    };
    const { time, date } = dosTime();

    for (const f of files) {
      const name = utf8(f.name), data = f.data, crc = crc32(data);
      const local = new DataView(new ArrayBuffer(30));
      local.setUint32(0, 0x04034b50, true);   // local file header signature
      local.setUint16(4, 20, true);           // version needed
      local.setUint16(6, 0x0800, true);       // flags: UTF-8 names
      local.setUint16(8, 0, true);            // method 0 = stored
      local.setUint16(10, time, true);
      local.setUint16(12, date, true);
      local.setUint32(14, crc, true);
      local.setUint32(18, data.length, true); // compressed size
      local.setUint32(22, data.length, true); // uncompressed size
      local.setUint16(26, name.length, true);
      local.setUint16(28, 0, true);           // extra length
      chunks.push(new Uint8Array(local.buffer), name, data);

      const cen = new DataView(new ArrayBuffer(46));
      cen.setUint32(0, 0x02014b50, true);     // central directory signature
      cen.setUint16(4, 20, true);             // version made by
      cen.setUint16(6, 20, true);             // version needed
      cen.setUint16(8, 0x0800, true);
      cen.setUint16(10, 0, true);
      cen.setUint16(12, time, true);
      cen.setUint16(14, date, true);
      cen.setUint32(16, crc, true);
      cen.setUint32(20, data.length, true);
      cen.setUint32(24, data.length, true);
      cen.setUint16(28, name.length, true);
      cen.setUint16(30, 0, true);             // extra
      cen.setUint16(32, 0, true);             // comment
      cen.setUint16(34, 0, true);             // disk number
      cen.setUint16(36, 0, true);             // internal attrs
      cen.setUint32(38, 0, true);             // external attrs
      cen.setUint32(42, offset, true);        // offset of local header
      central.push(new Uint8Array(cen.buffer), name);

      offset += 30 + name.length + data.length;
    }

    const centralBytes = central.reduce((a, c) => a + c.length, 0);
    const end = new DataView(new ArrayBuffer(22));
    end.setUint32(0, 0x06054b50, true);
    end.setUint16(4, 0, true);
    end.setUint16(6, 0, true);
    end.setUint16(8, files.length, true);
    end.setUint16(10, files.length, true);
    end.setUint32(12, centralBytes, true);
    end.setUint32(16, offset, true);
    end.setUint16(20, 0, true);

    const all = [...chunks, ...central, new Uint8Array(end.buffer)];
    const total = all.reduce((a, c) => a + c.length, 0);
    const out = new Uint8Array(total);
    let p = 0;
    for (const c of all) { out.set(c, p); p += c.length; }
    return out;
  }

  /* ---------- XML helpers ---------- */
  /* XML 1.0 forbids most control characters. Build the escaped string, then drop
     anything below 0x20 that is not tab, newline or carriage return. Done by code
     point rather than a regex, so no escape sequence can be mangled in transit. */
  const esc = s => {
    const t = String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&apos;");
    let out = "";
    for (let i = 0; i < t.length; i++) {
      const c = t.charCodeAt(i);
      if (c === 9 || c === 10 || c === 13 || c >= 32) out += t[i];
    }
    return out;
  };

  /* A run. opts: {b bold, i italic, sz half-points, color hex, font, caps} */
  function run(text, opts) {
    const o = opts || {};
    let rPr = "";
    if (o.font)  rPr += `<w:rFonts w:ascii="${esc(o.font)}" w:hAnsi="${esc(o.font)}" w:cs="${esc(o.font)}"/>`;
    if (o.b)     rPr += `<w:b/>`;
    if (o.i)     rPr += `<w:i/>`;
    if (o.caps)  rPr += `<w:caps/>`;
    if (o.color) rPr += `<w:color w:val="${esc(o.color)}"/>`;
    if (o.sz)    rPr += `<w:sz w:val="${o.sz}"/><w:szCs w:val="${o.sz}"/>`;
    if (o.spacing) rPr += `<w:spacing w:val="${o.spacing}"/>`;
    const body = esc(text).replace(/\n/g, "</w:t><w:br/><w:t xml:space=\"preserve\">");
    return `<w:r>${rPr ? `<w:rPr>${rPr}</w:rPr>` : ""}<w:t xml:space="preserve">${body}</w:t></w:r>`;
  }

  /* A paragraph. opts: {before, after, align, ind, border, shade, keepNext, style} */
  function para(runs, opts) {
    const o = opts || {};
    let pPr = "";
    if (o.style) pPr += `<w:pStyle w:val="${esc(o.style)}"/>`;
    if (o.keepNext) pPr += `<w:keepNext/>`;
    if (o.shade) pPr += `<w:shd w:val="clear" w:color="auto" w:fill="${esc(o.shade)}"/>`;
    if (o.border) pPr += `<w:pBdr><w:${o.border.side || "bottom"} w:val="single" w:sz="${o.border.sz || 6}" w:space="${o.border.space || 2}" w:color="${o.border.color || "DDDDDD"}"/></w:pBdr>`;
    if (o.ind) pPr += `<w:ind w:left="${o.ind}"/>`;
    const sp = [];
    if (o.before != null) sp.push(`w:before="${o.before}"`);
    if (o.after  != null) sp.push(`w:after="${o.after}"`);
    if (o.line) sp.push(`w:line="${o.line}" w:lineRule="auto"`);
    if (sp.length) pPr += `<w:spacing ${sp.join(" ")}/>`;
    if (o.align) pPr += `<w:jc w:val="${o.align}"/>`;
    return `<w:p>${pPr ? `<w:pPr>${pPr}</w:pPr>` : ""}${Array.isArray(runs) ? runs.join("") : runs}</w:p>`;
  }

  /* A table. rows: [[{text|runs, w, shade, b, color, sz}]] ; widths in twips */
  function table(rows, opts) {
    const o = opts || {};
    const border = `<w:top w:val="single" w:sz="4" w:color="${o.border || "D9DCDD"}"/>`
                 + `<w:left w:val="single" w:sz="4" w:color="${o.border || "D9DCDD"}"/>`
                 + `<w:bottom w:val="single" w:sz="4" w:color="${o.border || "D9DCDD"}"/>`
                 + `<w:right w:val="single" w:sz="4" w:color="${o.border || "D9DCDD"}"/>`
                 + `<w:insideH w:val="single" w:sz="4" w:color="${o.border || "D9DCDD"}"/>`
                 + `<w:insideV w:val="single" w:sz="4" w:color="${o.border || "D9DCDD"}"/>`;
    const body = rows.map(cells => `<w:tr>` + cells.map(c => {
      const w = c.w || 2000;
      const cellPr = `<w:tcPr><w:tcW w:w="${w}" w:type="dxa"/>`
        + (c.shade ? `<w:shd w:val="clear" w:color="auto" w:fill="${esc(c.shade)}"/>` : "")
        + `<w:vAlign w:val="top"/></w:tcPr>`;
      const content = c.runs ? c.runs
        : para(run(c.text == null ? "" : c.text, { b: c.b, color: c.color, sz: c.sz || 18, font: c.font }),
               { before: 20, after: 20, align: c.align });
      return `<w:tc>${cellPr}${content}</w:tc>`;
    }).join("") + `</w:tr>`).join("");
    return `<w:tbl><w:tblPr><w:tblW w:w="${o.width || 9360}" w:type="dxa"/>`
         + `<w:tblBorders>${border}</w:tblBorders>`
         + `<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>`
         + `<w:bottom w:w="60" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar>`
         + `</w:tblPr>${body}</w:tbl>`;
  }

  const pageBreak = () => `<w:p><w:r><w:br w:type="page"/></w:r></w:p>`;

  /* An inline image. w/h in EMU. rId must match a relationship. */
  function image(rId, wEmu, hEmu, name) {
    return `<w:p><w:pPr><w:spacing w:after="80"/></w:pPr><w:r><w:drawing>`
      + `<wp:inline distT="0" distB="0" distL="0" distR="0">`
      + `<wp:extent cx="${Math.round(wEmu)}" cy="${Math.round(hEmu)}"/>`
      + `<wp:docPr id="1" name="${esc(name || "Logo")}"/>`
      + `<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">`
      + `<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">`
      + `<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">`
      + `<pic:nvPicPr><pic:cNvPr id="1" name="${esc(name || "Logo")}"/><pic:cNvPicPr/></pic:nvPicPr>`
      + `<pic:blipFill><a:blip r:embed="${rId}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>`
      + `<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="${Math.round(wEmu)}" cy="${Math.round(hEmu)}"/></a:xfrm>`
      + `<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>`
      + `</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>`;
  }

  /* ---------- assemble ---------- */
  /* opts: {body, header:{left,right}, footer:{left}, image:{bytes,ext} } */
  function build(opts) {
    const o = opts || {};
    const hasImg = !!(o.image && o.image.bytes);
    const ext = hasImg ? (o.image.ext || "png") : null;
    const mime = ext === "jpg" || ext === "jpeg" ? "image/jpeg" : "image/png";

    const contentTypes = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
${hasImg ? `<Default Extension="${ext}" ContentType="${mime}"/>` : ""}
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>`;

    const rootRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`;

    const docRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rIdHeader" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
${hasImg ? `<Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo.${ext}"/>` : ""}
</Relationships>`;

    const styles = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="20"/><w:szCs w:val="20"/>
</w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
</w:styles>`;

    const NS = `xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" `
      + `xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" `
      + `xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" `
      + `xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"`;

    /* A mark that has to appear on EVERY page belongs in the header, not in the body. Word's own
       watermark is a VML shape in the header and this writer does not emit VML, so the mark is a
       centred line above the running header instead: it repeats on every page, it survives a
       monochrome print, and it cannot be scrolled past. */
    const hdrMark = o.header && o.header.mark
      ? para(run(o.header.mark, { b: true, sz: 26, color: "B45309" }), { align: "center", after: 40 })
      : "";

    const header = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr ${NS}>${hdrMark}${para(
  [run(o.header && o.header.left || "", { sz: 15, color: "6E7477" }),
   run("\t\t", { sz: 15 }),
   run(o.header && o.header.right || "", { sz: 15, color: "6E7477" })],
  { after: 60, border: { side: "bottom", sz: 4, color: "D9DCDD" } })}</w:hdr>`;

    /* PAGE / NUMPAGES as field codes, so Word renders live page numbers */
    const fld = code => `<w:r><w:fldChar w:fldCharType="begin"/></w:r>`
      + `<w:r><w:instrText xml:space="preserve"> ${code} </w:instrText></w:r>`
      + `<w:r><w:fldChar w:fldCharType="separate"/></w:r>`
      + `<w:r><w:rPr><w:sz w:val="15"/><w:color w:val="6E7477"/></w:rPr><w:t>1</w:t></w:r>`
      + `<w:r><w:fldChar w:fldCharType="end"/></w:r>`;
    const footer = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr ${NS}><w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="4" w:space="4" w:color="D9DCDD"/></w:pBdr>`
      + `<w:spacing w:before="60"/><w:tabs><w:tab w:val="right" w:pos="9360"/></w:tabs></w:pPr>`
      + run(o.footer && o.footer.left || "", { sz: 15, color: "6E7477" })
      + `<w:r><w:tab/></w:r>`
      + run("Page ", { sz: 15, color: "6E7477" }) + fld("PAGE")
      + run(" of ", { sz: 15, color: "6E7477" }) + fld("NUMPAGES")
      + `</w:p></w:ftr>`;

    const sectPr = `<w:sectPr>`
      + `<w:headerReference w:type="default" r:id="rIdHeader"/>`
      + `<w:footerReference w:type="default" r:id="rIdFooter"/>`
      + `<w:pgSz w:w="11906" w:h="16838"/>`                       /* A4 portrait */
      + `<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1247" w:header="567" w:footer="567" w:gutter="0"/>`
      + `<w:titlePg/>`
      + `</w:sectPr>`;

    const document = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document ${NS}><w:body>${o.body || ""}${sectPr}</w:body></w:document>`;

    const files = [
      { name: "[Content_Types].xml",       data: utf8(contentTypes) },
      { name: "_rels/.rels",               data: utf8(rootRels) },
      { name: "word/document.xml",         data: utf8(document) },
      { name: "word/_rels/document.xml.rels", data: utf8(docRels) },
      { name: "word/styles.xml",           data: utf8(styles) },
      { name: "word/header1.xml",          data: utf8(header) },
      { name: "word/footer1.xml",          data: utf8(footer) }
    ];
    if (hasImg) files.push({ name: `word/media/logo.${ext}`, data: o.image.bytes });

    return new Blob([zip(files)],
      { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
  }

  /* data: URI -> {bytes, ext} */
  function dataUriToImage(uri) {
    const m = /^data:image\/(png|jpe?g);base64,(.+)$/i.exec(uri || "");
    if (!m) return null;
    const ext = m[1].toLowerCase() === "png" ? "png" : "jpg";
    const bin = atob(m[2]);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return { bytes, ext };
  }

  return { build, run, para, table, image, pageBreak, dataUriToImage, esc, EMU_PER_MM: 36000 };
})();
if (typeof module !== "undefined") module.exports = DOCX;
