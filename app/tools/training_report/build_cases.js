// Render docs/CALIBRATION_CASES.md as a .docx in the style of the Training report
// (Calibri, the report's heading colours, Claim statement box, ruled anchors).
//
//   NODE_PATH=<dir with node_modules/docx> node build_cases.js CASES.md OUT.docx
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, HeadingLevel,
  AlignmentType, WidthType, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber,
} = require("docx");

const MD = fs.readFileSync(process.argv[2], "utf8");
const OUT = process.argv[3];
const FONT = "Calibri";
const W = 9638;                                   // A4 text width, 2 cm margins

// ------------------------------------------------------------- docx helpers (as in build_report.js)
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: o.size || 21, ...o });
// inline **bold** and `code` -> runs
const inline = (t, o = {}) => t.split(/(\*\*[^*]+\*\*|`[^`]+`)/).filter(Boolean).map(s =>
  s.startsWith("**") ? run(s.slice(2, -2), { ...o, bold: true }) : s.startsWith("`") ? run(s.slice(1, -1), o) : run(s, o));
const para = (t, o = {}) => new Paragraph({ spacing: { after: 60, line: 260 }, ...o, children: inline(t) });
const h1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, keepLines: true,
  spacing: { after: 80 }, children: [run(t, { size: 36, bold: true, color: "1F3864" })] });
const h2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, keepLines: true,
  spacing: { before: 220, after: 40 }, children: [run(t, { size: 23, bold: true, color: "2E5395" })] });
const label = t => new Paragraph({ keepNext: true, spacing: { before: 70, after: 30 },
  children: [run(t, { bold: true, size: 17, color: "2E5395", allCaps: true })] });
const bullet = (t, keep) => new Paragraph({ numbering: { reference: "bul", level: 0 }, keepNext: !!keep,
  spacing: { after: 20, line: 252 }, children: inline(t) });
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const statementBox = t => new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W],
  rows: [new TableRow({ cantSplit: true, children: [new TableCell({ width: { size: W, type: WidthType.DXA },
    borders: { top: border, bottom: border, left: { style: BorderStyle.SINGLE, size: 18, color: "2E5395" }, right: border },
    shading: { fill: "EEF2F8", type: ShadingType.CLEAR, color: "auto" }, margins: { top: 60, bottom: 60, left: 140, right: 140 },
    children: [new Paragraph({ keepNext: true, children: [run(t, { size: 20 })] })] })] })] });
const anchor = (n, loc, quote) => new Paragraph({ keepNext: true, keepLines: true, spacing: { before: 20, after: 40 },
  indent: { left: 360, right: 240 }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: "A6A6A6", space: 8 } },
  children: [run(`Anchor ${n}, ${loc}`, { bold: true, size: 17, color: "595959" }), run("", { break: 1 }),
    run(`“${quote}”`, { size: 19, italics: true })] });

// ------------------------------------------------------------- parse the Markdown
const body = [];
const add = (...x) => body.push(...x);
const field = (block, name) => { const m = block.match(new RegExp(`^\\*\\*${name}:\\*\\* ?(.*)$`, "m")); return m ? m[1] : null; };
const [head, ...cases] = MD.split(/^## /m);

const title = head.match(/^# (.*)$/m)[1];
add(h1(title));
const intro = head.replace(/^# .*$/m, "").trim();
add(para(intro, { spacing: { after: 80 } }));

for (const raw of cases) {
  const block = "## " + raw;
  const heading = block.match(/^## (.*)$/m)[1];
  add(h2(heading));

  const claim = field(block, "Claim");
  if (claim) { add(label("Claim statement")); add(statementBox(claim)); }
  const anchors = field(block, "Anchors") || field(block, "Anchor");
  if (anchors) {
    const list = [...anchors.matchAll(/\((\d+)\) (p\. \d+) "(.*?)"(?=;\s*\(\d+\)|\s*$)/g)];
    if (!list.length) throw new Error("no anchors parsed in " + heading);
    add(label(list.length === 1 ? "Anchor in the source" : "Anchors in the source"));
    list.forEach(m => add(anchor(m[1], m[2], m[3])));
  }

  // Issue: optional lead text on the same line, then "- " bullets
  const issueAt = block.indexOf("**Issue:**");
  if (issueAt >= 0) {
    const rest = block.slice(issueAt + "**Issue:**".length);
    const lead = rest.split("\n")[0].trim();
    const bullets = rest.split("\n").slice(1).filter(l => l.startsWith("- ")).map(l => l.slice(2));
    add(label("Issue"));
    if (lead) add(para((lead.charAt(0).toUpperCase() + lead.slice(1)).replace(/:$/, "."), { keepNext: true, spacing: { after: 40 } }));
    bullets.forEach((t, k) => add(bullet(t.replace(/;$/, ""), k < bullets.length - 1)));
  }
  const discuss = field(block, "Discuss");
  if (discuss) {
    add(label("What to discuss"));
    add(para(discuss));
  }
  const why = field(block, "Why");
  if (why) { add(label("Why it matters")); add(para(why.charAt(0).toUpperCase() + why.slice(1))); }

  // any other bold-led paragraph (e.g. the spare case) after the case
  const spare = block.match(/^\*\*Spare case:\*\*.*$/m);
  if (spare) add(para(spare[0], { spacing: { before: 160, after: 60 } }));
}

const doc = new Document({
  creator: "SLiM Brain evaluation", title,
  styles: { default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 36, bold: true, color: "1F3864" }, paragraph: { outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 23, bold: true, color: "2E5395" }, paragraph: { outlineLevel: 1, keepNext: true } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT, buf.length); });
