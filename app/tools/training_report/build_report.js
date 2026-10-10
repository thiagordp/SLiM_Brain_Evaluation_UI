// Render the Training-phase calibration report (.docx) from the JSON written by
// extract.py. Every count, percentage and distribution is computed here from that
// JSON; the interpretive text refers to items by id and is checked against the
// data before each release (see README.md).
//
//   NODE_PATH=<dir with node_modules/docx> node build_report.js DATA.json OUT.docx
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, HeadingLevel,
  AlignmentType, WidthType, ShadingType, BorderStyle, LevelFormat, Footer, PageNumber, PageOrientation,
  Bookmark, InternalHyperlink,
} = require("docx");

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const R = D.raters;
const SNAPSHOT_DATE = (([y, m, d]) => `${+d} ${["January", "February", "March", "April", "May", "June", "July", "August",
  "September", "October", "November", "December"][m - 1]} ${y}`)(D.snapshot.slice(0, 10).split("-").map(Number));
const PAPERS = ["SRC-0006", "SRC-0009"];
const FONT = "Calibri";
const W = 9638;                                   // A4 text width, 2 cm margins

// ------------------------------------------------------------- data helpers
const P = s => D.papers[s];
const items = s => P(s).items;
const contested = s => items(s).filter(i => !i.unanimous);
const pct = (a, b) => (100 * a / b).toFixed(1);
const qrow = (s, key) => P(s).per_question.find(q => q.key === key);
const unan = (s, key) => { const q = qrow(s, key); return q ? `${q.unanimous}/${q.n}` : "—"; };
const LABEL = { "All are represented": "All", "Most are represented": "Most", "Some are represented": "Some",
  "None are represented": "None" };
const dist = i => Object.entries(i.distribution).map(([v, n]) => `${LABEL[v] || v} ${n}`).join(" / ");
const splitText = i => i.values > 2 ? "multi-valued" : i.split;
function find(s, claim, key, obj) {
  const hit = items(s).filter(i => i.claim === claim && i.key === key &&
    (!obj || JSON.stringify(i.object).includes(obj) || i.object_id.includes(obj)));
  if (hit.length !== 1) throw new Error(`find ${s} ${claim} ${key} ${obj}: ${hit.length}`);
  return hit[0];
}
const F = (s, claim, key, obj) => dist(find(s, claim, key, obj));
const splitCount = (s, label) => contested(s).filter(i => i.split === label).length;
const unanimousCount = s => items(s).filter(i => i.unanimous).length;

// evaluator statistics, both papers
const ev = Object.fromEntries(R.map(r => [r, { n: 0, flag: 0, com: 0, lone: 0, lonePass: 0, minority: 0, dom: {} }]));
for (const s of PAPERS) for (const i of items(s)) {
  const top = Math.max(...Object.values(i.distribution));
  for (const r of R) {
    const v = i.answers[r], e = ev[r];
    e.n++; if (i.flags[r]) e.flag++; if (i.comments[r]) e.com++;
    if (i.distribution[v] < top) { e.minority++; e.dom[i.section] = (e.dom[i.section] || 0) + 1; }
    if (i.split === "6–1" && i.distribution[v] === 1) { e.lone++; if (!i.flags[r]) e.lonePass++; }
  }
}
const loneTotal = R.reduce((t, r) => t + ev[r].lone, 0);
const byFlag = [...R].sort((a, b) => ev[a].flag - ev[b].flag);

// ------------------------------------------------------------- docx helpers
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: o.size || 21, ...o });
const para = (parts, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, ...o,
  children: (Array.isArray(parts) ? parts : [parts]).map(t => typeof t === "string" ? run(t) : t) });
const b = t => run(t, { bold: true });
const it = t => run(t, { italics: true });
// h1/h2 carry a bookmark and are listed in the Contents (built at the end, see toc)
const toc = [];
const marked = (level, t, runOpts, o = {}) => {
  const id = `sec_${toc.length + 1}`;
  toc.push({ level, t, id });
  return new Paragraph({ heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, keepNext: true, keepLines: true,
    ...o, children: [new Bookmark({ id, children: [run(t, runOpts)] })] });
};
const h1 = (t, o = {}) => marked(1, t, { size: 28, bold: true, color: "1F3864" }, { spacing: { before: 300, after: 120 }, ...o });
const h2 = t => marked(2, t, { size: 23, bold: true, color: "2E5395" }, { spacing: { before: 200, after: 80 } });
const h3 = (t, o = {}) => new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, keepLines: true,
  spacing: { before: 220, after: 60 }, ...o, children: [run(t, { size: 21, bold: true, color: "2E5395" })] });
const bullet = parts => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 264 },
  children: (Array.isArray(parts) ? parts : [parts]).map(t => typeof t === "string" ? run(t) : t) });
const note = t => para([it(t)], { spacing: { before: 60, after: 140 } });
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(head, rows, widths, o = {}) {
  const size = o.size || 18;
  const cell = (t, w, h) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders, margins: { top: 40, bottom: 40, left: 80, right: 80 },
    shading: h ? { fill: "DCE3EE", type: ShadingType.CLEAR, color: "auto" } : undefined,
    children: String(t).split("\n").map(line => new Paragraph({ keepNext: !!o.keep, keepLines: true,
      children: [run(line, { size, bold: h })] })) });
  return new Table({ width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, cantSplit: true, children: head.map((t, k) => cell(t, widths[k], true)) }),
      ...rows.map(row => new TableRow({ cantSplit: true, children: row.map((t, k) => cell(t, widths[k], false)) }))] });
}
const spacer = () => new Paragraph({ spacing: { after: 80 }, children: [] });
const body = [];
const add = (...x) => body.push(...x);

// ================================================================== title
add(new Paragraph({ spacing: { after: 60 }, children: [run("Training-phase calibration report", { size: 36, bold: true, color: "1F3864" })] }));
add(para([it(`SLiM Brain human evaluation, round ROUND-2026-01, instrument 4.1. Training papers SRC-0006 and SRC-0009, seven evaluators. Data snapshot: ${SNAPSHOT_DATE}.`)]));
const TOC_AT = body.length;

const a6 = P("SRC-0006"), a9 = P("SRC-0009");
const pr = s => P(s).pairs.map(p => p.pct);
const f1 = x => x.toFixed(1);
const iq = (s, c, k, o) => find(s, c, k, o);
const cmt = (s, c, k, o, r) => { const v = iq(s, c, k, o).comments[r]; if (!v) throw new Error(`no comment ${c} ${k} ${r}`); return v; };

// ================================================================== 1
add(h1("1. Summary", { pageBreakBefore: true }));
add(bullet(`Pairwise percentage agreement is ${f1(Math.min(...pr("SRC-0006")))}–${f1(Math.max(...pr("SRC-0006")))}% on SRC-0006 and ${f1(Math.min(...pr("SRC-0009")))}–${f1(Math.max(...pr("SRC-0009")))}% on SRC-0009. All seven evaluators give the same answer on ${pct(unanimousCount("SRC-0006"), items("SRC-0006").length)}% and ${pct(unanimousCount("SRC-0009"), items("SRC-0009").length)}% of the items.`));
add(bullet(`Agreement is agreement on “Yes”. On defects it is low: when one evaluator records a defect, another records the same defect in ${(a6.pos_agreement * 100).toFixed(0)}% (SRC-0006) and ${(a9.pos_agreement * 100).toFixed(0)}% (SRC-0009) of comparisons; Krippendorff's α is ${a6.alpha_defect.toFixed(2)} and ${a9.alpha_defect.toFixed(2)}.`));
add(bullet("Stable: central thesis, understood on its own, legal and temporal reference, relation grounding, Dataset questions. Unstable: Relation type and Direction, candidate Concepts, Textual grounding, Basis, Claim object, Claim jurisdiction."));
add(bullet("Recurring causes: unclear category boundaries (law/other, literature/abstract/factual, descriptive/interpretative); different evidential standards (anchors only versus the paper as context); different readings of the question (relation existence versus type; Concept family versus fit); categories the schema lacks (a “compatible” relation, a mixed basis)."));
add(bullet("Calibration needs: a rule for mixed Claim objects and mixed bases; one evidential standard for fields (anchors or source); an option for “relation should not exist”; a decision on parallel-evidence relations; clearer scope for candidate Concepts."));

// ================================================================== 2
add(h1("2. Data and method"));
const c6 = a6.counts, c9 = a9.counts;
const rel = c => Object.entries(c.relations).map(([t, n]) => `${n} ${t}`).join(", ");
add(para(`Seven evaluators (${R.join(", ")}) answered every item of both Training papers; there are no missing answers. Answers were read from the round workbook; nothing was written.`));
add(table(["", "SRC-0006", "SRC-0009"], [
  ["Claims", c6.claims, c9.claims],
  ["Assigned Concepts (Q12) / candidate Concepts (Q13)", `${c6.assigned_concepts} / ${c6.candidate_concepts}`, `${c9.assigned_concepts} / ${c9.candidate_concepts}`],
  ["Relations (Grounding, Direction, Type each)", rel(c6), rel(c9)],
  ["Datasets (six questions each)", c6.datasets, c9.datasets],
  ["Single-label items per evaluator", items("SRC-0006").length, items("SRC-0009").length],
], [5038, 2300, 2300], { size: 19 }));
add(spacer());
add(para([b("Definitions. "), run("An item is one question about one object: a Claim (Q2–Q11), an assigned or candidate Concept, one relation judgment, a Dataset field, or Claim recall. Percentages use single-label items only. Missing Concepts (Q14), restatement groups and the Missing Claims text are set-valued or free text and are reported separately. Items the instrument does not show are “not asked” (Missing Claims when recall is “All”; Direction for SAME_AS, absent here). Pairwise agreement: identical answers ÷ items both evaluators answered. Unanimous: all seven answers identical; contested otherwise. Split: answer counts from largest to smallest (4–3, 5–2, 6–1; three or more values: multi-valued); a 4–3 split is stronger evidence of a calibration problem than a 6–1. Lone dissent: the minority evaluator in a 6–1 split. Flag rate: share of an evaluator's answers recording a defect (No, In part, recall below “All”).")]));
add(para([b("Chance-corrected agreement. "), run(`α and κ compare observed agreement with the agreement expected from the answer distribution. With almost all answers “Yes”, expected agreement is high and the coefficients are low even when raw agreement is high. Specific agreement shows the two components: ${(a6.neg_agreement * 100).toFixed(0)}% and ${(a9.neg_agreement * 100).toFixed(0)}% on outputs judged correct, ${(a6.pos_agreement * 100).toFixed(0)}% and ${(a9.pos_agreement * 100).toFixed(0)}% on defects.`)]));

// ================================================================== 3
add(h1("3. Agreement"));
add(h2("3.1 Pairwise agreement"));
const pairKey = p => [p.a, p.b].sort().join("|");
const p9 = Object.fromEntries(a9.pairs.map(p => [pairKey(p), p]));
const merged = a6.pairs.map(p => ({ pair: `${p.a} – ${p.b}`, x: p.pct, y: p9[pairKey(p)].pct }))
  .sort((u, v) => (u.x + u.y) - (v.x + v.y));
add(table(["Evaluator pair", "SRC-0006 agreement (%)", "SRC-0009 agreement (%)"],
  merged.map(m => [m.pair, f1(m.x), f1(m.y)]), [4238, 2700, 2700], { size: 18 }));
add(note(`Comparable items per pair: ${items("SRC-0006").length} (SRC-0006) and ${items("SRC-0009").length} (SRC-0009). Rows sorted by mean agreement across the two papers.`));
const ext = s => { const ps = [...P(s).pairs].sort((x, y) => x.pct - y.pct); return { lo: ps.slice(0, 2), hi: ps.slice(-2).reverse(), min: ps[0].pct, max: ps[ps.length - 1].pct }; };
const e6 = ext("SRC-0006"), e9 = ext("SRC-0009");
const fmtp = ps => ps.map(p => `${p.a}–${p.b} (${f1(p.pct)}%)`).join(", ");
const ys = [...a6.pairs, ...a9.pairs].map(p => p.both_yes_share * 100);
add(para(`SRC-0006: ${f1(e6.min)}–${f1(e6.max)}%; lowest ${fmtp(e6.lo)}; highest ${fmtp(e6.hi)}. SRC-0009: ${f1(e9.min)}–${f1(e9.max)}%; lowest ${fmtp(e9.lo)}; highest ${fmtp(e9.hi)}. Between ${Math.min(...ys).toFixed(0)}% and 100% of each pair's identical answers are “Yes”, so the highest pairs are those that flag least.`));

add(h2("3.2 Unanimity per question"));
const QORDER = ["CLAIM_Q02_CENTRAL_THESIS", "CLAIM_Q03_MODALITY", "CLAIM_Q04_STANDALONE", "CLAIM_Q05_GROUNDING",
  "CLAIM_Q06_CLAIM_OBJECT", "CLAIM_Q07_CLAIM_TYPE", "CLAIM_Q08_BASIS", "CLAIM_Q09_CLAIM_JURISDICTION",
  "CLAIM_Q10_LEGAL_REFERENCE", "CLAIM_Q11_TEMPORAL_REFERENCE", "CLAIM_Q12_CONCEPT", "CLAIM_Q13_CANDIDATE",
  "REL_GROUNDING", "REL_DIRECTION", "REL_TYPE"];
const QNAME = { CLAIM_Q12_CONCEPT: "Concept assignment (Q12)", CLAIM_Q13_CANDIDATE: "Candidate Concept necessary (Q13)",
  REL_GROUNDING: "Relation grounding", REL_DIRECTION: "Relation direction", REL_TYPE: "Relation type" };
const title = k => QNAME[k] || (qrow("SRC-0006", k) || qrow("SRC-0009", k)).title;
const share = (s, k) => { const q = qrow(s, k); return q ? `${q.unanimous}/${q.n} (${Math.round(100 * q.unanimous / q.n)}%)` : "—"; };
const dsKeys = a9.per_question.filter(q => q.key.startsWith("DATASET")).map(q => q.key);
const dsUnan = dsKeys.reduce((t, k) => t + qrow("SRC-0009", k).unanimous, 0);
add(table(["Question", "SRC-0006 unanimous", "SRC-0009 unanimous"],
  [...QORDER.map(k => [title(k), share("SRC-0006", k), share("SRC-0009", k)]),
   ["Dataset questions (six)", "—", `${dsUnan}/${dsKeys.length} (${Math.round(100 * dsUnan / dsKeys.length)}%)`]],
  [4238, 2700, 2700], { size: 18 }));
add(spacer());
const sl = s => P(s).source_level;
const cnt = (s, f) => { const c = {}; R.forEach(r => { const v = f(sl(s)[r]); c[v] = (c[v] || 0) + 1; }); return Object.entries(c).map(([v, n]) => `${v} ${n}`).join(" / "); };
const q14same = s => Object.values(P(s).q14).filter(ev2 => new Set(R.map(r => JSON.stringify([ev2[r].state,
  ev2[r].selected.map(x => x.id).sort(), ev2[r].proposed.map(x => x.name.toLowerCase()).sort()]))).size === 1).length;
add(table(["Paper-level and set-valued", "SRC-0006", "SRC-0009"], [
  ["Claim recall", cnt("SRC-0006", x => LABEL[x.recall]), cnt("SRC-0009", x => LABEL[x.recall])],
  ["Restatements present", cnt("SRC-0006", x => x.restatements), cnt("SRC-0009", x => x.restatements)],
  ["Missing Concepts identical across all seven (Claims)", `${q14same("SRC-0006")}/${c6.claims}`, `${q14same("SRC-0009")}/${c9.claims}`],
], [4238, 2700, 2700], { size: 18 }));
add(spacer());
add(para(`Questions that compare the Claim with its own wording are near-unanimous; questions that require a category decision or an evidential threshold are not (lowest: Relation type ${unan("SRC-0006", "REL_TYPE")} and ${unan("SRC-0009", "REL_TYPE")}; candidate Concepts on SRC-0009 ${unan("SRC-0009", "CLAIM_Q13_CANDIDATE")}; Direction on SRC-0009 ${unan("SRC-0009", "REL_DIRECTION")}). The paper-level questions are holistic and are not mixed with Claim-level results: Francesca and Thibault answered recall “Most” on both papers, the others “All”; on SRC-0006 the four evaluators who report restatements formed different groups (Appendix B); Missing Concepts coincide only where all evaluators recorded none missing.`));

// ================================================================== 4
add(h1("4. Where the raters agree"));
add(para("Agreement is highest where the Claim statement reproduces its anchors and the field values can be read from the text. CLM-0006-001 and CLM-0006-002 are unanimous on every Claim-level question (Q2–Q11); nine further Claims have at most one 6–1 split there. No Claim is unanimous once Concepts and Relations are included."));
add(para("CLM-0006-002 joins three anchors almost verbatim (“it produces an illusion of meaning which users mistake for actual meaning”; “both phenomena succeed in replicating the form of their mimicked output, but not its substance”). CLM-0009-010 restates a single reported result (“LinearSVC's performance is not much inferior to state-of-the-art models, suggesting that lexical cues play a crucial role”), from which factual basis and technology object follow directly."));
add(para("The contrast case is CLM-0006-012: its statement adds content not in the anchors and its object combines legal practice and technology. It has four 4–3 splits (Section 6)."));

// ================================================================== 5
add(h1("5. Where the raters disagree"));
const block = (name, observed, interp) => { add(h2(name)); add(para([b("Observed. "), run(observed)])); add(para([b("Interpretation. "), run(interp)])); };
block("5.1 Claim object",
  `Unanimous for ${unan("SRC-0006", "CLAIM_Q06_CLAIM_OBJECT")} and ${unan("SRC-0009", "CLAIM_Q06_CLAIM_OBJECT")} Claims. Assigned law is split on CLM-0006-012 (${F("SRC-0006", "CLM-0006-012", "CLAIM_Q06_CLAIM_OBJECT")}) and CLM-0006-008 (${F("SRC-0006", "CLM-0006-008", "CLAIM_Q06_CLAIM_OBJECT")}); dissenters propose other. On SRC-0009 the split is other versus technology (CLM-0009-006, ${F("SRC-0009", "CLM-0009-006", "CLAIM_Q06_CLAIM_OBJECT")}).`,
  `Schema ambiguity. The definition does not say how to classify Claims about both law and technology, or about legal practice described as a social phenomenon (Francesca: “${cmt("SRC-0006", "CLM-0006-012", "CLAIM_Q06_CLAIM_OBJECT", "", "Francesca")}”). The Claim object calibration added during the phase addresses this boundary.`);
block("5.2 Basis",
  `Unanimous for ${unan("SRC-0006", "CLAIM_Q08_BASIS")} and ${unan("SRC-0009", "CLAIM_Q08_BASIS")} Claims. Closest splits: CLM-0009-004, literature versus abstract for an uncited statement (${F("SRC-0009", "CLM-0009-004", "CLAIM_Q08_BASIS")}); CLM-0006-012, factual versus literature for data reported in earlier work (${F("SRC-0006", "CLM-0006-012", "CLAIM_Q08_BASIS")}); legal versus literature on CLM-0006-004 and CLM-0009-003 (5–2 each).`,
  `Schema ambiguity and a missing category. Basis takes one value, while Claims often combine sources; the definition does not say whether literature requires a citation or whether data reported in the literature are factual (Vaclav on CLM-0006-012: “…the difficult case where the literature reports some data, and data are regarded as "factual" basis under our definition. I think we need a guideline here.”).`);
block("5.3 Claim jurisdiction",
  `Unanimous for ${unan("SRC-0006", "CLAIM_Q09_CLAIM_JURISDICTION")} and ${unan("SRC-0009", "CLAIM_Q09_CLAIM_JURISDICTION")} Claims. AU is contested on CLM-0006-012 (${F("SRC-0006", "CLM-0006-012", "CLAIM_Q09_CLAIM_JURISDICTION")}), CLM-0006-020 (${F("SRC-0006", "CLM-0006-020", "CLAIM_Q09_CLAIM_JURISDICTION")}) and CLM-0006-010 (${F("SRC-0006", "CLM-0006-010", "CLAIM_Q09_CLAIM_JURISDICTION")}); on SRC-0009 all EU dissents are Thiago's (three 6–1).`,
  "Conflicting texts. The definition includes “the jurisdiction(s) of the data the claim is based on” (supporting AU or EU from the source data); the Claim-level calibration asks to judge fields “from what the anchors support” (supporting Thiago's explicit-mention reading); the jurisdiction calibration defines General as “explicitly jurisdiction-independent or concerns law in general” (the reading of Francesca and Alessandro). Each reading is consistent with one text.");
block("5.4 Textual grounding",
  `Unanimous for ${unan("SRC-0006", "CLAIM_Q05_GROUNDING")} and ${unan("SRC-0009", "CLAIM_Q05_GROUNDING")} Claims; no evaluator answered No. Closest splits: CLM-0006-004 (${F("SRC-0006", "CLM-0006-004", "CLAIM_Q05_GROUNDING")}), CLM-0006-018 and CLM-0009-006 (4–3 each).`,
  `Different evidential standards. “In part” marks statement content absent from the quotes (Giuseppe on CLM-0009-006: “${cmt("SRC-0009", "CLM-0009-006", "CLAIM_Q05_GROUNDING", "", "Giuseppe")}”); others accept content recoverable from the paper. The question does not fix the threshold. A separate citation criterion (“missing refs”) is treated in Section 8.`);
block("5.5 Strength and modality",
  `Unanimous for ${unan("SRC-0006", "CLAIM_Q03_MODALITY")} and ${unan("SRC-0009", "CLAIM_Q03_MODALITY")} Claims. All No answers come from Thibault and Thiago; only CLM-0006-014 exceeds a 6–1 split (${F("SRC-0006", "CLM-0006-014", "CLAIM_Q03_MODALITY")}).`,
  `Different evidential standards. Two evaluators check hedges word by word (Thiago: “${cmt("SRC-0006", "CLM-0006-014", "CLAIM_Q03_MODALITY", "", "Thiago")}”); the others do not record such differences. The dissents cite verifiable source wording.`);
block("5.6 Claim type",
  `Unanimous for ${unan("SRC-0006", "CLAIM_Q07_CLAIM_TYPE")} and ${unan("SRC-0009", "CLAIM_Q07_CLAIM_TYPE")} Claims. Close splits on CLM-0009-002 (interpretative; ${F("SRC-0009", "CLM-0009-002", "CLAIM_Q07_CLAIM_TYPE")}) and CLM-0009-012 (descriptive; ${F("SRC-0009", "CLM-0009-012", "CLAIM_Q07_CLAIM_TYPE")}).`,
  "Schema ambiguity. Characterisations of a practice and generalisations from results sit between describing and proposing a view. On CLM-0009-012 the No answers propose different alternatives (interpretative, prescriptive), which the Yes/No format hides.");
block("5.7 Concepts",
  `Assignment unanimous for ${unan("SRC-0006", "CLAIM_Q12_CONCEPT")} and ${unan("SRC-0009", "CLAIM_Q12_CONCEPT")}; candidate necessity for ${unan("SRC-0006", "CLAIM_Q13_CANDIDATE")} and ${unan("SRC-0009", "CLAIM_Q13_CANDIDATE")}. Close splits concern candidate or emergent Concepts (Administration of justice, Annotation guidelines, Decision support); Judicial interpretative formulas is judged unnecessary by the same two evaluators on three Claims.`,
  "Scope ambiguity of Concepts created during extraction, combined with two readings of Q12: fit to the Claim versus correctness of the Concept's family (Section 8). Missing Concepts are rarely added, and additions by different evaluators rarely coincide.");
block("5.8 Relations",
  `Relation type unanimous for ${unan("SRC-0006", "REL_TYPE")} and ${unan("SRC-0009", "REL_TYPE")} relations; Direction for ${unan("SRC-0006", "REL_DIRECTION")} and ${unan("SRC-0009", "REL_DIRECTION")}; Grounding nearly unanimous. ${PAPERS.reduce((t, s) => t + contested(s).filter(i => i.split === "4–3" && i.section === "Relations").length, 0)} relation judgments are split 4–3 (Section 6).`,
  "Divergent reading of the question and a missing category. Comments show three readings: whether the relation should exist (“unrelated”, “vague”), a type the schema lacks (“Compatible/same as”), and whether direction is meaningful for symmetric relations. The instrument has no answer for “this relation should not exist”, so rejection is expressed as No on type, direction or both.");

// ================================================================== 6
add(h1("6. Most problematic data points"));
add(para(`All items with the closest possible split (4–3): ${splitCount("SRC-0006", "4–3")} on SRC-0006 and ${splitCount("SRC-0009", "4–3")} on SRC-0009. No single-label item has more than two distinct answers. There are ${splitCount("SRC-0006", "5–2") + splitCount("SRC-0009", "5–2")} 5–2 and ${splitCount("SRC-0006", "6–1") + splitCount("SRC-0009", "6–1")} 6–1 splits in total.`));
add(h2("6.1 Items with a 4–3 split"));
const ISSUE = {
  "CLM-0006-002|REL_DIRECTION": "Which Claim supports which; weak inferred link",
  "CLM-0006-004|CLAIM_Q05_GROUNDING": "Quoted court wording not in anchors",
  "CLM-0006-008|CLAIM_Q06_CLAIM_OBJECT": "Law vs other for a typology of arguments",
  "CLM-0006-012|CLAIM_Q06_CLAIM_OBJECT": "Law vs other for law + technology",
  "CLM-0006-012|CLAIM_Q08_BASIS": "Factual vs literature for reported data",
  "CLM-0006-012|CLAIM_Q09_CLAIM_JURISDICTION": "Data jurisdiction vs explicit mention vs general",
  "CLM-0006-012|CLAIM_Q13_CANDIDATE": "Scope of candidate Concept",
  "CLM-0006-013|REL_TYPE": "Counter-position or unrelated; no fitting type",
  "CLM-0006-015|REL_TYPE": "Relation between Claims on different objects",
  "CLM-0006-018|CLAIM_Q05_GROUNDING": "Recommendation not stated in anchors",
  "CLM-0006-018|CLAIM_Q12_CONCEPT": "Scope of candidate Concept",
  "CLM-0006-018|CLAIM_Q13_CANDIDATE": "Scope of candidate Concept",
  "CLM-0009-002|CLAIM_Q07_CLAIM_TYPE": "Descriptive vs interpretative",
  "CLM-0009-004|CLAIM_Q08_BASIS": "Literature vs abstract without citation",
  "CLM-0009-006|CLAIM_Q05_GROUNDING": "Details absent from anchors",
  "CLM-0009-006|REL_TYPE": "Qualified counter-example; no fitting type",
  "CLM-0009-011|CLAIM_Q12_CONCEPT": "Practitioner relevance vs legal task",
  "CLM-0009-012|CLAIM_Q07_CLAIM_TYPE": "Dissenters disagree on the alternative",
  "CLM-0009-012|REL_TYPE": "Relevance of the link",
  "CLM-0009-014|CLAIM_Q12_CONCEPT": "Candidate Concept for a corpus description",
  "CLM-0009-014|CLAIM_Q13_CANDIDATE": "Candidate Concept for a corpus description",
};
const objLabel = i => i.object.concept ? i.object.concept : i.object.type ? `${i.object.type} → ${i.object.target}` : "";
const close = PAPERS.flatMap(s => contested(s).filter(x => x.split === "4–3").map(i => ({ s, i })));
add(table(["Item", "Question", "Distribution", "Calibration issue"],
  close.map(({ i }) => { const k = `${i.claim}|${i.key}`; if (!ISSUE[k]) throw new Error("issue " + k);
    return [i.claim + (objLabel(i) ? `\n${objLabel(i)}` : ""), i.title, dist(i), ISSUE[k]]; }),
  [2500, 1900, 1650, 3588], { size: 17 }));
add(spacer());
add(h2("6.2 Cases"));
add(para([b("CLM-0006-012. "), run("Four of the SRC-0006 4–3 splits fall on one Claim (object, basis, jurisdiction, candidate Concept). It combines court practice, a technology and the author's earlier empirical work; each field requires one value where the content supports several.")]));
add(para([b("CLM-0009-006 → CLM-0008-009 (ATTACKS). "), run("Near-perfect annotation agreement on one task is linked to a Claim that annotation is difficult on another. Four evaluators reject the type for three different reasons: no fitting type, unrelatable contexts, unrelated.")]));
add(para([b("CLM-0009-012, Claim type. "), run("The four No answers name different alternatives, so a 4–3 on a Yes/No question can conceal a multi-valued disagreement.")]));
add(para([b("Candidate Concepts. "), run("Administration of justice (CLM-0006-018, Q12 and Q13) and Annotation guidelines (CLM-0009-014, Q12 and Q13) are split 4–3 on both questions: evaluators disagree on whether the Concept fits and, consistently, on whether it is needed.")]));

// ================================================================== 7
add(h1("7. Annotation patterns per evaluator"));
add(h2("7.1 Overview"));
const domText = r => Object.entries(ev[r].dom).sort((x, y) => y[1] - x[1]).slice(0, 2).map(([k, n]) => `${k} (${n})`).join("; ") || "—";
add(table(["Evaluator", "Flag rate", "Comments (rate)", "Lone dissents", "Minority answers", "Main disagreement domains"],
  R.map(r => [r, `${pct(ev[r].flag, ev[r].n)}%`, `${ev[r].com} (${pct(ev[r].com, ev[r].n)}%)`, ev[r].lone, ev[r].minority, domText(r)]),
  [1300, 1000, 1400, 1100, 1250, 3588], { size: 18 }));
add(note(`${ev[R[0]].n} items per evaluator (both papers). Minority answers: answers outside the largest group of the item. Domains: sections with most minority answers.`));
const lonePass = R.reduce((t, r) => t + ev[r].lonePass, 0);
add(para(`Flag rates range from ${pct(ev[byFlag[0]].flag, ev[byFlag[0]].n)}% (${byFlag[0]}) to ${pct(ev[byFlag[R.length - 1]].flag, ev[byFlag[R.length - 1]].n)}% (${byFlag[R.length - 1]}). Of ${loneTotal} lone dissents, ${loneTotal - lonePass} record a defect; a single evaluator almost never accepts what the other six reject. Disagreement is therefore driven by which defects each evaluator records, not by disagreement about acceptable outputs.`));
add(para("Minority answers concentrate in different domains: Concepts for Giuseppe and Alessandro, Claim evaluation for Thibault (grounding, modality), Schema fields for Francesca, Thiago and Vaclav. Stricter checks in one domain therefore do not predict strictness in another. These are response patterns; they do not measure accuracy, care or competence."));

add(h2("7.2 Evaluator profiles"));
add(para("Each profile reports counts only, computed from the answers in the workbook."));
const QSHORT = k => (title(k) || k).replace(/ \(Q\d+\)$/, "");
const top = (obj, n) => Object.entries(obj).sort((x, y) => y[1] - x[1] || x[0].localeCompare(y[0])).slice(0, n);
const ofQ = (obj, n) => top(obj, n).map(([k, c]) => `${QSHORT(k)} (${c})`).join(", ");
const SHORT_RECALL = v => LABEL[v] || v || "not answered";
for (const r of R) {
  const per = {}, flagQ = {}, comQ = {}, loneQ = {}, secMin = {};
  let no = 0, inpart = 0, lone = 0, loneFlag = 0;
  for (const s of PAPERS) {
    per[s] = { n: 0, flag: 0, com: 0 };
    for (const i of items(s)) {
      const v = i.answers[r], topN = Math.max(...Object.values(i.distribution));
      per[s].n++;
      if (i.flags[r]) { per[s].flag++; flagQ[i.key] = (flagQ[i.key] || 0) + 1; }
      if (v === "No") no++; if (v === "In part") inpart++;
      if (i.comments[r]) { per[s].com++; comQ[i.key] = (comQ[i.key] || 0) + 1; }
      if (i.distribution[v] < topN) secMin[i.section] = (secMin[i.section] || 0) + 1;
      if (i.split === "6–1" && i.distribution[v] === 1) { lone++; if (i.flags[r]) loneFlag++; loneQ[i.key] = (loneQ[i.key] || 0) + 1; }
    }
  }
  const meanAgr = s => { const ps = P(s).pairs.filter(p => p.a === r || p.b === r); return f1(ps.reduce((t, p) => t + p.pct, 0) / ps.length); };
  const q14 = s => { const v = Object.values(P(s).q14).map(c => c[r]);
    return [v.filter(x => x.state === "missing").length, v.reduce((t, x) => t + x.selected.length, 0), v.reduce((t, x) => t + x.proposed.length, 0)]; };
  const restate = s => { const x = sl(s)[r]; return x.restatements === "Yes" ? `Yes (${x.groups.length} group${x.groups.length === 1 ? "" : "s"})` : (x.restatements || "not answered"); };
  const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
  const mc = s => sl(s)[r].recall === "All are represented" ? "" : (sl(s)[r].missing_claims.trim() ? ", Missing Claims listed" : ", no Missing Claims listed");
  const both = PAPERS.map(s => per[s]);
  const tot = { n: both[0].n + both[1].n, flag: both[0].flag + both[1].flag, com: both[0].com + both[1].com };
  add(h3(r));
  add(bullet([b("Defects recorded: "), run(`${tot.flag} of ${tot.n} answers (${pct(tot.flag, tot.n)}%); SRC-0006 ${pct(per["SRC-0006"].flag, per["SRC-0006"].n)}%, SRC-0009 ${pct(per["SRC-0009"].flag, per["SRC-0009"].n)}%. No: ${no}; In part: ${inpart}.` + (tot.flag ? ` Most frequent questions: ${ofQ(flagQ, 3)}.` : ""))]));
  add(bullet([b("Comments: "), run(`${tot.com} items (${pct(tot.com, tot.n)}%)` + (tot.com ? `; most frequent questions: ${ofQ(comQ, 2)}.` : "."))]));
  add(bullet([b("Minority answers: "), run(`${ev[r].minority}` + (ev[r].minority ? ` (${top(secMin, 4).map(([k, c]) => `${k} ${c}`).join(", ")}).` : "."))]));
  add(bullet([b("Lone dissents (6–1): "), run(`${lone}, of which ${loneFlag} record a defect` + (lone ? `; most frequent questions: ${ofQ(loneQ, 2)}.` : "."))]));
  add(bullet([b("Mean pairwise agreement with the other six: "), run(`SRC-0006 ${meanAgr("SRC-0006")}%, SRC-0009 ${meanAgr("SRC-0009")}%.`)]));
  add(bullet([b("Missing Concepts (Q14): "), run(PAPERS.map(s => { const [m, sel, pro] = q14(s); return m ? `${s}: ${plural(m, "Claim")} with missing Concepts (${sel} existing selected, ${pro} new proposed)` : `${s}: none recorded`; }).join("; ") + ".")]));
  add(bullet([b("Source-level answers: "), run(PAPERS.map(s => `${s}: recall ${SHORT_RECALL(sl(s)[r].recall)}${mc(s)}, restatements ${restate(s)}`).join("; ") + ".")]));
}

// ================================================================== 8
add(h1("8. Potential evaluator–schema mismatches"));
add(para("Responses that appear inconsistent with the schema definition, the question wording or a calibration rule. The majority is not used as a criterion; similar cases are grouped."));
add(table(["Pattern / evaluator(s)", "Example(s)", "Relevant rule", "Why this matters"], [
  ["Concept family instead of fit (Giuseppe)", "Annotation cost (CLM-0009-004, -012), Inter annotator agreement (CLM-0009-006): “no normative concern”",
   "Q12: “Is this Concept correctly assigned to the Claim?”", "Rejections may reflect the vocabulary's family structure, not the Claim–Concept fit."],
  ["Citation required for grounding (Giuseppe)", "Textual grounding “In part — missing refs” (e.g. CLM-0006-009, -013)",
   "Anchor: verbatim passage “where the claim and its basis are put forward”", "The anchor definition does not require a citation; “In part” then mixes two criteria."],
  ["Relation existence instead of type (Alessandro, Giuseppe)", "“VAGUE, GENERAL” (CLM-0006-013 relations); “unrelated” (CLM-0009-004 → CLM-0018-011)",
   "“Is the Relation type correct for the relationship…?”", "The instrument offers no answer for an unwanted relation; No on type then carries two meanings."],
  ["Category not in the schema (Francesca)", "“Compatible/same as” on four SUPPORTS relations of CLM-0009-001 and -004",
   "SUPPORTS: “one claim gives reasons or evidence for another claim”", "Parallel findings may fit SUPPORTS as defined; the comments point to a category the schema does not provide."],
  ["Temporal value from a cited source (Vaclav)", "CLM-0006-008 (also CLM-0006-012): “recently, as of 2024 (publication year of the source in fn 3)”",
   "“date or period … when stated; otherwise as_of_publication”", "The Claims state no date; the definition does not use the dates of cited sources."],
  ["Central thesis read as main thesis (Thiago)", "CLM-0006-006, -007: “It's a claim that suports the main claim.”",
   "Q2: a thesis “that the paper advances as part of its contribution”", "The question includes supporting theses; the narrower reading lowers Q2 for multi-claim papers."],
  ["Concept fit by explicit mention (Thiago)", "Precedent on CLM-0009-002: “There is no mention of precedent.”",
   "Precedent: “grounds interpretation in prior decisions and their authority”", "The Claim describes interpretation developed through self-citation of earlier decisions."],
], [1900, 2700, 2400, 2638], { size: 16 }));
add(spacer());
add(para("Not listed: Claim jurisdiction and Claim object for mixed Claims, where the applicable texts conflict (Sections 5.1, 5.3) and responses on both sides follow one of them."));

// ================================================================== 9
add(h1("9. Limitations"));
[
  "Two papers; several questions have few observations (13 and 8 relations; 7 candidate Concepts on SRC-0009; one Dataset).",
  "Strong imbalance towards “Yes”: percentage agreement overstates agreement on defects; chance-corrected coefficients are low and unstable.",
  "Calibration texts (Basis, Claim jurisdiction, Claim object) were revised during the phase; evaluators may have seen different guidance.",
  "Set-valued answers (Missing Concepts, restatements, Missing Claims) are not covered by the percentages.",
  "The analysis locates disagreement; it does not establish gold-standard answers. Section 8 applies the schema as read by the author and is input for calibration, not adjudication.",
].forEach(t => add(bullet(t)));

// ================================================================== Appendix A
const SECTIONS = ["Claim evaluation", "Schema fields", "Concepts", "Relations"];
const sevOrder = { "4–3": 0, "multi-valued": 0, "5–2": 1, "6–1": 2 };
const strongest = list => list.length ? list.map(splitText).sort((x, y) => sevOrder[x] - sevOrder[y])[0] : "none contested";
add(h1("Appendix A. Contested items per Claim", { pageBreakBefore: true, spacing: { after: 100 } }));
add(note("Contested single-label items by section; strongest disagreement among them (4–3 strongest, 6–1 weakest). Missing Concepts are set-valued and not counted."));
for (const s of PAPERS) {
  add(h2(`A.${PAPERS.indexOf(s) + 1} ${s}`));
  const rows = P(s).claims.map(c => {
    const its = contested(s).filter(i => i.claim === c.id);
    return [c.id, ...SECTIONS.map(sec => its.filter(i => i.section === sec).length || ""), its.length || "", strongest(its)];
  });
  if (P(s).counts.datasets) rows.push(["Dataset", "", "", "", "", contested(s).filter(i => i.section === "Dataset").length || "", strongest(contested(s).filter(i => i.section === "Dataset"))]);
  const slc = contested(s).filter(i => i.section === "Source-level");
  rows.push(["Claim recall (Source)", "", "", "", "", slc.length || "", strongest(slc)]);
  const tot = contested(s);
  rows.push(["Total", ...SECTIONS.map(sec => tot.filter(i => i.section === sec).length), tot.length, ""]);
  add(table(["Claim", "Claim eval.", "Fields", "Concepts", "Relations", "Total", "Strongest"], rows,
    [2000, 1100, 1000, 1100, 1100, 900, 2438], { size: 16 }));
}

// ================================================================== Appendix B
// Landscape section: every contested item, one table per Claim, Claim statement
// and anchors above it; one column per evaluator (answer and verbatim comment).
const LW = 16838 - 2 * 1134;                       // A4 landscape text width
const bodyB = [];
const addB = (...x) => bodyB.push(...x);
const ORANGE = "FCE4D6", YELLOW = "FFF2CC", HEAD = "DCE3EE";
const label = t => new Paragraph({ keepNext: true, spacing: { before: 60, after: 40 },
  children: [run(t, { bold: true, size: 17, color: "2E5395", allCaps: true })] });
const statementBox = t => new Table({ width: { size: LW, type: WidthType.DXA }, columnWidths: [LW],
  rows: [new TableRow({ cantSplit: true, children: [new TableCell({ width: { size: LW, type: WidthType.DXA },
    borders: { top: border, bottom: border, left: { style: BorderStyle.SINGLE, size: 18, color: "2E5395" }, right: border },
    shading: { fill: "EEF2F8", type: ShadingType.CLEAR, color: "auto" }, margins: { top: 80, bottom: 80, left: 140, right: 140 },
    children: [new Paragraph({ keepNext: true, children: [run(t, { size: 20 })] })] })] })] });
const anchor = (a, k) => new Paragraph({ keepNext: true, keepLines: true, spacing: { before: 40, after: 60 }, indent: { left: 360, right: 240 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: "A6A6A6", space: 8 } },
  children: [run(`Anchor ${k + 1}${a.location ? `, ${a.location}` : ""}`, { bold: true, size: 17, color: "595959" }), run("", { break: 1 }),
    run(`“${a.quote}”`, { size: 19, italics: true })] });

const COLS = [1150, 1500, 1750];
const EVW = Math.floor((LW - COLS.reduce((a, c) => a + c, 0)) / R.length);
const WIDTHS = [...COLS, ...R.map(() => EVW)];
const cellMargins = { top: 30, bottom: 30, left: 60, right: 60 };
const xcell = (paras, w, fill) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders, margins: cellMargins,
  shading: fill ? { fill, type: ShadingType.CLEAR, color: "auto" } : undefined, children: paras });
const p16 = (t, o = {}) => new Paragraph({ keepLines: true, children: [run(t, { size: 16, ...o })] });
const headRow = () => new TableRow({ tableHeader: true, cantSplit: true,
  children: ["Claim", "Question", "Assigned", ...R].map((t, k) => xcell([p16(t, { bold: true })], WIDTHS[k], HEAD)) });
// row: {id, section, question, assigned, values: {rater: shown value}, comments: {rater: text}}
function matrixRow(x) {
  const n = {}; R.forEach(r => { n[x.values[r]] = (n[x.values[r]] || 0) + 1; });
  const topN = Math.max(...Object.values(n));
  const tie = Object.values(n).filter(c => c === topN).length > 1;
  return new TableRow({ cantSplit: true, children: [
    xcell([p16(x.id, { bold: true }), p16(x.section, { color: "666666" })], WIDTHS[0]),
    xcell([p16(x.question)], WIDTHS[1]),
    xcell(String(x.assigned || "").split("\n").map(t => p16(t)), WIDTHS[2]),
    ...R.map((r, k) => xcell([p16(x.values[r] || "–", { bold: true }),
      ...(x.comments[r] ? x.comments[r].split(/\s*\n\s*/).filter(Boolean).map(t => p16(t, { size: 15 })) : [])],
      WIDTHS[3 + k], tie ? YELLOW : (n[x.values[r]] < topN ? ORANGE : undefined))),
  ] });
}
const matrix = rows => new Table({ width: { size: LW, type: WidthType.DXA }, columnWidths: WIDTHS,
  rows: [headRow(), ...rows.map(matrixRow)] });
const assignedOf = i => { const o = i.object;
  if (o.kind === "relation") return `${o.type} → ${o.target} (${o.grounding})`;
  if (o.concept) return o.concept;
  if (o.dataset) return `${o.dataset}` + (o.assigned != null ? `\n${Array.isArray(o.assigned) ? o.assigned.join(", ") : o.assigned}` : "");
  if (i.section === "Claim evaluation") return "";
  return Array.isArray(o.assigned) ? o.assigned.join(", ") : (o.assigned || "(empty)"); };
const itemRow = i => ({ id: i.claim || i.object_id, section: i.section, question: i.title, assigned: assignedOf(i),
  values: Object.fromEntries(R.map(r => [r, LABEL[i.answers[r]] || i.answers[r]])), comments: i.comments });
const q14Row = (s, c) => { const e = P(s).q14[c];
  const shown = r => { const x = e[r]; const v = [...x.selected.map(y => y.name), ...x.proposed.map(y => `NEW: ${y.name}`)];
    return v.length ? v.join("\n") : (x.state ? "none" : ""); };
  const values = Object.fromEntries(R.map(r => [r, shown(r)]));
  if (new Set(Object.values(values)).size === 1) return null;
  return { id: c, section: "Concepts", question: "Missing Concepts (Q14)", assigned: "selected / proposed", values, comments: {} }; };

addB(h1("Appendix B. Every contested item: each evaluator's answer and comment", { spacing: { after: 100 } }));
addB(para("One table per Claim. Above each table, the Claim statement is given in a box and the anchors, the verbatim passages of the source on which the statement is based, are listed below it. Each row of the table is one contested question. Each evaluator's cell gives the answer (bold) and, below it, the evaluator's comment if one was written, quoted exactly. Orange: the answer differs from the majority of the row. Yellow: no single majority (a tie). “not asked”: the question was not shown because recall was “All”. Restatements: Yes with the groups formed (last three digits of each Claim id). Missing Concepts: the Concepts selected (“NEW:” for a proposed Concept), or “none”. Uncontested items are not listed; the complete item-level data remain available in the round workbook."));
PAPERS.forEach((s, k) => {
  addB(h2(`B.${k + 1} ${s}`));
  for (const c of P(s).claims) {
    const rows = contested(s).filter(i => i.claim === c.id).map(itemRow);
    const q = q14Row(s, c.id); if (q) rows.push(q);
    if (!rows.length) continue;
    addB(h3(c.id, { spacing: { before: 280, after: 40 } }));
    addB(label("Claim statement"));
    addB(statementBox(c.statement));
    addB(label(c.anchors.length === 1 ? "Anchor in the source" : "Anchors in the source"));
    c.anchors.forEach((a, n) => addB(anchor(a, n)));
    addB(new Paragraph({ keepNext: true, spacing: { after: 40 }, children: [] }));
    addB(matrix(rows));
  }
  const ds = contested(s).filter(i => i.section === "Dataset");
  if (ds.length) { addB(h3(`${s} · Dataset`, { spacing: { before: 280, after: 60 } })); addB(matrix(ds.map(itemRow))); }
  const x = sl(s);
  const recall = contested(s).find(i => i.section === "Source-level") || items(s).find(i => i.section === "Source-level");
  addB(h3(`${s} · Claim recall`, { spacing: { before: 280, after: 60 } }));
  addB(matrix([
    { id: s, section: "Claim recall", question: "Claim recall", assigned: "", values: Object.fromEntries(R.map(r => [r, LABEL[x[r].recall] || x[r].recall])), comments: recall ? recall.comments : {} },
    { id: s, section: "Claim recall", question: "Restatements", assigned: "", comments: {},
      values: Object.fromEntries(R.map(r => [r, x[r].restatements === "Yes" ? "Yes; " + x[r].groups.map(g => "{" + g.map(y => y.slice(-3)).join(", ") + "}").join(" ") : x[r].restatements])) },
    { id: s, section: "Claim recall", question: "Missing Claims (text)", assigned: "", values: Object.fromEntries(R.map(r => [r,
      x[r].recall === "All are represented" ? "not asked" : (x[r].missing_claims.trim() ? "listed" : "none")])),
      comments: Object.fromEntries(R.filter(r => x[r].recall !== "All are represented").map(r => [r, x[r].missing_claims.trim()])) },
  ]));
});
addB(spacer());

// ================================================================== Appendix C
// Chance-corrected agreement coefficients, computed by coefficients.py.
const K = D.coefficients;
if (!K) throw new Error("no coefficients block: run coefficients.py on the JSON first");
const bodyC = [];
const addC = (...x) => bodyC.push(...x);
const fx = v => v == null ? "n.d." : (Math.abs(v) < 0.005 ? 0 : v).toFixed(2).replace("-", "−");
const ci = c => c ? `[${fx(c[0])}, ${fx(c[1])}]` : "";
const withCi = (v, c) => v == null ? "n.d." : `${fx(v)} ${ci(c)}`.trim();
const def = (name, rows) => { addC(h3(name, { spacing: { before: 200, after: 40 } }));
  rows.forEach(([k, t], n) => addC(para([b(`${k}. `), run(t)], { keepNext: n < rows.length - 1, spacing: { after: 40, line: 264 } }))); };

addC(h1("Appendix C. Agreement coefficients (To check)", { spacing: { after: 100 } }));
addC(para("This appendix reports the agreement coefficients commonly used in annotation studies, computed on the same data as the report. C.1 describes each coefficient, C.2 how they were applied to this instrument, C.3 gives the results and C.4 how to read them."));

addC(h2("C.1 Coefficients"));
def("Percentage agreement (Po)", [
  ["What", "The proportion of rater pairs that give the same answer to an item, averaged over items."],
  ["What for", "A direct measure of how often evaluators give the same answer."],
  ["Why here", "It is the measure used in Section 3 and the starting point of the chance-corrected coefficients."],
  ["How", "For an item answered by m raters, with n_k answers in category k: Po = Σ n_k(n_k − 1) / (m(m − 1)), averaged over items. Without missing answers this equals the mean of the 21 pairwise agreements. It does not account for agreement expected by chance."]]);
def("Cohen's κ and Light's κ", [
  ["What", "Agreement between two raters, corrected for the agreement expected from each rater's own answer distribution."],
  ["What for", "Comparing pairs of raters. Light's κ is the mean of Cohen's κ over all pairs."],
  ["Why here", "It is the most frequently reported coefficient; the pairwise values show the spread between pairs."],
  ["How", "κ = (Po − Pe) / (1 − Pe), with Pe = Σ_k pA(k) · pB(k), where pA(k) is the share of rater A's answers in category k. κ = 1: perfect agreement; κ = 0: agreement at chance level; κ < 0: below chance."]]);
def("Fleiss' κ", [
  ["What", "Chance-corrected agreement for more than two raters, with the same number of raters per item."],
  ["What for", "One value for the whole group of evaluators."],
  ["Why here", "All seven evaluators answered every item."],
  ["How", "κ = (Po − Pe) / (1 − Pe), with Po as above and Pe = Σ_k p_k², where p_k is the share of all answers in category k."]]);
def("Krippendorff's α", [
  ["What", "A reliability coefficient: one minus the ratio of observed to expected disagreement."],
  ["What for", "Any number of raters, missing answers, and different kinds of data (nominal, ordinal, interval, sets) through a distance function."],
  ["Why here", "It is the standard coefficient in content analysis and computational linguistics (Artstein and Poesio 2008), and its thresholds are the most widely used criterion."],
  ["How", "α = 1 − Do / De. Do is the mean disagreement between answers to the same item; De is the mean disagreement between any two answers in the data. For nominal data the disagreement is 1 if two answers differ and 0 otherwise. Krippendorff (2018): α ≥ 0.800 reliable; 0.667 ≤ α < 0.800 only tentative conclusions; below 0.667 not reliable. With many items, nominal α is almost equal to Fleiss' κ."]]);
def("Gwet's AC1", [
  ["What", "Chance-corrected agreement with a different estimate of chance agreement."],
  ["What for", "Data in which one category is very frequent. κ and α are then low even when agreement is high (the kappa paradox; Feinstein and Cicchetti 1990)."],
  ["Why here", `${(100 * (1 - K.overall.both.defect_share)).toFixed(1)}% of all answers record no defect.`],
  ["How", "AC1 = (Po − Pe) / (1 − Pe), with Pe = Σ_k π_k(1 − π_k) / (q − 1), where π_k is the share of answers in category k and q is the number of categories of the scale. Pe is small when one category dominates, so AC1 stays close to Po."]]);
def("Positive and negative specific agreement (PA+, PA−)", [
  ["What", "Agreement computed separately for each category of a binary judgement."],
  ["What for", "Showing which category the agreement comes from (Cicchetti and Feinstein 1990)."],
  ["Why here", "It separates agreement on defects from agreement on correct outputs."],
  ["How", "Over all rater pairs and items: a = both record a defect; d = neither records a defect; b + c = only one records a defect. PA+ = 2a / (2a + b + c); PA− = 2d / (2d + b + c)."]]);
def("Krippendorff's α with MASI distance", [
  ["What", "Krippendorff's α for answers that are sets of values."],
  ["What for", "Annotations that select several values, where partial overlap should count as partial agreement."],
  ["Why here", "Missing Concepts (Q14) is a set of Concepts per Claim and evaluator."],
  ["How", "MASI = J × M, where J = |A ∩ B| / |A ∪ B| (Jaccard) and M = 1 if the sets are identical, 2/3 if one contains the other, 1/3 if they overlap otherwise, 0 if they are disjoint (Passonneau 2006). The distance 1 − MASI is used in α. The mean pairwise Jaccard index is reported as the uncorrected agreement."]]);

addC(h2("C.2 Application to this evaluation"));
[
  "Unit: one single-label item (one question about one Claim, Concept, relation or Dataset), as in Section 2. Every item has seven answers; there are no missing answers.",
  "Defect coding: each answer is coded as defect (No, In part, recall below “All”) or no defect. All questions share this scale, so items can be pooled across questions and papers. Tables C1 and C2.",
  "Original categories: Yes / No, or Yes / In part / No for Textual grounding (Q5). Computed per question and pooled over the two papers (Table C3). For two-category questions the two codings give the same values.",
  "Missing Concepts (Q14): one set per Claim and evaluator (Concepts selected and Concepts proposed; “none missing” is the empty set). Table C4.",
  "Not computed: Claim recall and restatements (one answer per paper and evaluator, so one unit per paper); Missing Claims (free text); Dataset questions individually (one item each; they are pooled in the Dataset row of Table C2).",
  "n.d. (not defined): when all answers are in one category, expected disagreement is zero and κ and α cannot be computed.",
  `Confidence intervals: 95% percentile bootstrap over items (${K.reps.toLocaleString("en")} resamples, fixed seed); evaluators are fixed.`,
  "Landis and Koch's (1977) labels for κ (0.21–0.40 fair, 0.41–0.60 moderate, 0.61–0.80 substantial) are often cited but are not derived from data; Krippendorff's thresholds are used here.",
].forEach(t => addC(bullet(t)));

addC(h2("C.3 Results"));
const o = K.overall, fam = K.families;
addC(para([b("Table C1. "), run("All single-label items, defect coding.")], { keepNext: true, spacing: { after: 60 } }));
addC(table(["", "Items", "Po", "Light's κ (range)", "Fleiss' κ", "α [95% CI]", "AC1 [95% CI]", "PA+", "PA−"],
  [["SRC-0006", "SRC-0006"], ["SRC-0009", "SRC-0009"], ["both", "Both papers"]].map(([k, l]) => [l, o[k].n, fx(o[k].po),
    `${fx(o[k].light.mean)} (${fx(o[k].light.min)} to ${fx(o[k].light.max)})`, fx(o[k].fleiss), withCi(o[k].alpha, o[k].alpha_ci),
    withCi(o[k].ac1, o[k].ac1_ci), fx(o[k].pos), fx(o[k].neg)]),
  [1250, 650, 650, 1650, 900, 1450, 1450, 800, 838], { size: 17, keep: true }));
addC(spacer());
addC(para([b("Table C2. "), run("By question family, both papers, defect coding.")], { keepNext: true, spacing: { after: 60 } }));
addC(table(["Family", "Items", "Defect answers", "Po", "Fleiss' κ", "α [95% CI]", "AC1 [95% CI]", "PA+", "PA−"],
  Object.entries(fam).map(([k, v]) => [k, v.n, `${(100 * v.defect_share).toFixed(1)}%`, fx(v.po), fx(v.fleiss),
    withCi(v.alpha, v.alpha_ci), withCi(v.ac1, v.ac1_ci), fx(v.pos), fx(v.neg)]),
  [1500, 650, 950, 650, 900, 1600, 1600, 800, 988], { size: 17, keep: true }));
addC(spacer());
addC(para([b("Table C3. "), run("By question, both papers, original categories (q = number of categories).")], { keepNext: true, spacing: { after: 60 } }));
addC(table(["Question", "Family", "Items", "q", "Po", "Fleiss' κ", "α", "AC1"],
  K.per_question.map(q => [title(q.key), q.section, q.n + (q.small ? " *" : ""), q.q, fx(q.po), fx(q.fleiss), fx(q.alpha), fx(q.ac1)]),
  [2900, 1500, 750, 500, 900, 1000, 1000, 1088], { size: 17 }));
addC(note(`Values below 0 mean agreement below chance level. This occurs when almost all answers are “Yes” and the few defects are mostly recorded by one evaluator only.${K.per_question.some(q => q.small) ? ` * fewer than ${K.small_n} items.` : ""}`));
addC(para([b("Table C4. "), run("Missing Concepts (Q14), one set per Claim and evaluator.")], { keepNext: true, spacing: { after: 60 } }));
const q4 = K.q14;
addC(table(["", "Claims", "Claims with identical sets", "Mean pairwise Jaccard", "α (MASI)"],
  [["SRC-0006", "SRC-0006"], ["SRC-0009", "SRC-0009"], ["both", "Both papers"]].map(([k, l]) => [l, q4[k].n, q4[k].identical, fx(q4[k].jaccard), fx(q4[k].alpha_masi)]),
  [2000, 1300, 2400, 2100, 1838], { size: 17, keep: true }));
addC(spacer());

addC(h2("C.4 How to read the results"));
const famDefined = Object.entries(fam).filter(([, v]) => v.alpha != null).sort((x, y) => y[1].alpha - x[1].alpha);
const pq = K.per_question.filter(q => q.alpha != null).sort((x, y) => y.alpha - x.alpha);
const nearUnan = K.per_question.filter(q => q.po >= 0.97).map(q => title(q.key));
[
  `Po and AC1 are high (both papers: ${fx(o.both.po)} and ${fx(o.both.ac1)}); κ and α are low (α ${fx(o.both.alpha)}, ${ci(o.both.alpha_ci)}). This is the prevalence effect: ${(100 * o.both.defect_share).toFixed(1)}% of answers record a defect, so chance agreement on “no defect” is high and κ and α depend almost only on agreement about defects.`,
  `PA− is ${fx(o.both.neg)} and PA+ is ${fx(o.both.pos)}: evaluators agree on what is correct; when one evaluator records a defect, the others seldom record the same defect.`,
  `No family reaches α = 0.667 (highest: ${famDefined[0][0]}, ${fx(famDefined[0][1].alpha)}). By Krippendorff's criterion, the defect judgements are not yet reliable in any family.${fam.Dataset && fam.Dataset.alpha == null ? " For the Dataset no defect was recorded, so α is not defined." : ""}`,
  `By question, α is highest for ${title(pq[0].key)} (${fx(pq[0].alpha)}) and ${title(pq[1].key)} (${fx(pq[1].alpha)}). Near-unanimous questions (Po ≥ 0.97: ${nearUnan.join(", ")}) have α close to 0: the few defects recorded there come mostly from single evaluators (6–1 splits, Appendix B), not from disagreement about correct outputs.`,
  `Missing Concepts: the mean Jaccard index is ${fx(q4.both.jaccard)} but α (MASI) is ${fx(q4.both.alpha_masi)}. Agreement comes from Claims where all evaluators recorded none missing; when Concepts are added, they rarely coincide.`,
  "Report α with its confidence interval as the reliability measure, together with Po, AC1 and PA+/PA−, so that the prevalence effect is visible. Neither α nor AC1 alone describes the data.",
  "The confidence intervals of the families overlap; differences within them should not be interpreted. The values describe the instrument before calibration (the calibration texts were revised during the phase) and serve as a baseline for the main phase, not as its reliability.",
].forEach(t => addC(bullet(t)));

addC(h2("References"));
[
  "Artstein, R., and Poesio, M. (2008). Inter-coder agreement for computational linguistics. Computational Linguistics, 34(4), 555–596.",
  "Cicchetti, D. V., and Feinstein, A. R. (1990). High agreement but low kappa: II. Resolving the paradoxes. Journal of Clinical Epidemiology, 43(6), 551–558.",
  "Cohen, J. (1960). A coefficient of agreement for nominal scales. Educational and Psychological Measurement, 20(1), 37–46.",
  "Feinstein, A. R., and Cicchetti, D. V. (1990). High agreement but low kappa: I. The problems of two paradoxes. Journal of Clinical Epidemiology, 43(6), 543–549.",
  "Fleiss, J. L. (1971). Measuring nominal scale agreement among many raters. Psychological Bulletin, 76(5), 378–382.",
  "Gwet, K. L. (2008). Computing inter-rater reliability and its variance in the presence of high agreement. British Journal of Mathematical and Statistical Psychology, 61(1), 29–48.",
  "Krippendorff, K. (2018). Content Analysis: An Introduction to Its Methodology (4th ed.). Sage.",
  "Landis, J. R., and Koch, G. G. (1977). The measurement of observer agreement for categorical data. Biometrics, 33(1), 159–174.",
  "Light, R. J. (1971). Measures of response agreement for qualitative data: Some generalizations and alternatives. Psychological Bulletin, 76(5), 365–377.",
  "Passonneau, R. (2006). Measuring agreement on set-valued items (MASI) for semantic and pragmatic annotation. Proceedings of the Fifth International Conference on Language Resources and Evaluation (LREC 2006).",
].forEach(t => addC(para(t, { spacing: { after: 60 }, indent: { left: 360, hanging: 360 } })));

// ------------------------------------------------------------- contents (links to the bookmarked headings)
body.splice(TOC_AT, 0,
  new Paragraph({ spacing: { before: 240, after: 100 }, children: [run("Contents", { size: 26, bold: true, color: "1F3864" })] }),
  ...toc.map(e => new Paragraph({ spacing: { before: e.level === 1 ? 80 : 0, after: 20 }, indent: { left: e.level === 1 ? 0 : 400 },
    children: [new InternalHyperlink({ anchor: e.id, children: [run(e.t, e.level === 1
      ? { size: 20, bold: true, color: "1F3864" } : { size: 19, color: "404040" })] })] })));

const headingStyle = (id, name, level, size, color) => ({ id, name, basedOn: "Normal", next: "Normal", quickFormat: true,
  run: { font: FONT, size, bold: true, color }, paragraph: { outlineLevel: level, keepNext: true } });
const doc = new Document({
  creator: "SLiM Brain evaluation", title: "Training-phase calibration report",
  styles: { default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [headingStyle("Heading1", "Heading 1", 0, 28, "1F3864"), headingStyle("Heading2", "Heading 2", 1, 23, "2E5395"),
      headingStyle("Heading3", "Heading 3", 2, 21, "2E5395")] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" })] })] }) },
    children: body,
  }, {
    properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" })] })] }) },
    children: bodyB,
  }, {
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" })] })] }) },
    children: bodyC,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT, buf.length); });
