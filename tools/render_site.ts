#!/usr/bin/env bun
/**
 * Render the measles L1 site (REQ-04) into _site/, which is gitignored and never committed.
 *
 *   bun tools/render_site.ts [build/measles.l1.kg.json] [_site]
 *
 * Run it after tools/build.sh. It needs smart-base's needs closure mounted (`bun run mount:remote`)
 * and the platform's node_modules at ./node_modules, from a folio-assistant checkout at the SAME
 * pin as test.json. The mount brings code without a dependency manifest, so those packages come
 * from that checkout (see the remote-mount findings on PR #4).
 *
 * Two renderers, and which is which:
 *
 * - THE L1 DOCUMENT KIND (document-kinds/index.html) is drawn by folio-assistant's own
 *   document-kinds viewer: `readDocumentKinds` and `pageHtml` from the MOUNTED
 *   cat-harness/scripts/gen-document-kinds-viz.ts, imported through the mount path. This script
 *   only computes the `document-kind-coverage/1.0.0` report that says how this paper realises
 *   smart-base's `l1-guideline` kind. The rule is the kind's own data: a node of smart-kg class C
 *   goes in every section whose `modelledBy` names `sgkg-l1#C`. Whatever no section models is
 *   listed as unplaced, never dropped. The report is validated with the platform's
 *   DocumentKindCoverageSchema before it is drawn.
 * - THE READING PAGES (index, one page per publication section, coverage) are drawn here. The
 *   platform viewer lists at most 12 labels per section and has no page links, so it cannot show
 *   every recommendation verbatim with its PDF page. Those pages read the built graph and nothing
 *   else, so they show what the graph says.
 */
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

import { remark } from "remark";
import remarkGfm from "remark-gfm";
import remarkHtml from "remark-html";

import { DocumentKindCoverageSchema, type DocumentKindCoverage } from "../cat-harness/schemas/document-kind.ts";
import { pageHtml, readDocumentKinds } from "../cat-harness/scripts/gen-document-kinds-viz.ts";
import { withRenders } from "../cat-harness/scripts/viewer-declarations.ts";

const ROOT = resolve(import.meta.dir, "..");
const GRAPH = resolve(ROOT, process.argv[2] ?? "build/measles.l1.kg.json");
const OUT = resolve(ROOT, process.argv[3] ?? "_site");
const COVERAGE_MD = join(dirname(GRAPH), "coverage-report.md");
const KIND = "l1-guideline";
const KIND_OWNER = "smart-base";

type Node = {
  id: string;
  type: string;
  label: string;
  properties: Record<string, unknown>;
  derivation?: string;
  note?: string;
  evidence?: { location?: string; quote?: string };
};
type Edge = { predicate: string; source: string; target: string };
type Graph = { nodes: Node[]; edges: Edge[]; wasDerivedFrom?: { path: string; sha256: string }[] };

const esc = (s: unknown): string =>
  String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
const tail = (iri: string): string => iri.slice(iri.lastIndexOf("/") + 1);

/** `library/wer-92-17/WER9217.pdf#page=16 (journal p.220)` → its parts; undefined if it does not say. */
function locate(n: Node): { pdf: string; pdfPage: number; journal: string } | undefined {
  const m = /^(\S+\.pdf)#page=(\d+)\s+\(journal p\.([^)]+)\)$/.exec(n.evidence?.location ?? "");
  return m ? { pdf: m[1]!, pdfPage: Number(m[2]), journal: m[3]! } : undefined;
}

const graph = JSON.parse(readFileSync(GRAPH, "utf-8")) as Graph;
const decl = JSON.parse(readFileSync(join(ROOT, "test.json"), "utf-8")) as { name: string; title: string; description: string };
const byId = new Map(graph.nodes.map((n) => [n.id, n]));
const out = (n: Node, pred: string, type?: string): Node[] =>
  graph.edges
    .filter((e) => e.source === n.id && e.predicate === pred)
    .map((e) => byId.get(e.target)!)
    .filter((t) => t && (type === undefined || t.type === type));

const publication = graph.nodes.find((n) => n.type === "publication" && out(n, "contains", "publication-section").length > 0);
if (!publication) throw new Error(`${GRAPH}: no publication contains a section`);
const sections = out(publication, "contains", "publication-section");
const pdfPath = (() => {
  const l = graph.nodes.map(locate).find(Boolean);
  if (!l) throw new Error("no node records a PDF location");
  return l.pdf;
})();

// ── the coverage report against the L1 document kind ─────────────────────────────────────────

const { kinds } = readDocumentKinds(ROOT);
const entry = kinds.find((k) => k.instance === KIND_OWNER && k.kind.id === KIND);
if (!entry) throw new Error(`the mounted ${KIND_OWNER} declares no document kind "${KIND}" — is smart-base mounted?`);

function label(n: Node): string {
  if (n.type === "recommendation") return String(n.label);
  if (n.type === "remark") return `${n.label}: ${String(n.properties.text ?? "").slice(0, 120)}`;
  return String(n.label);
}

const placed = new Set<string>();
const kindSections = entry.kind.sections.map((s) => {
  const classes = (s.modelledBy ?? []).filter((t) => t.startsWith("sgkg-l1#")).map((t) => t.slice("sgkg-l1#".length));
  const members = graph.nodes.filter((n) => classes.includes(n.type));
  for (const m of members) placed.add(m.id);
  return { id: s.id, members: members.map((n) => ({ key: tail(n.id), label: label(n) })) };
});
const unplacedBy = new Map<string, number>();
for (const n of graph.nodes) if (!placed.has(n.id)) unplacedBy.set(n.type, (unplacedBy.get(n.type) ?? 0) + 1);

const coverage: DocumentKindCoverage = DocumentKindCoverageSchema.parse({
  $schema: "document-kind-coverage/1.0.0",
  kind: KIND,
  subject: decl.name,
  from: "build/measles.l1.kg.json",
  method:
    `Each node of the measles L1 graph is placed in every section of smart-base's ${KIND} kind whose modelledBy names its smart-kg class ` +
    `(sgkg-l1#<class>). The rule is the kind's own data; nodes of a class no section models are listed as unplaced.`,
  total: graph.nodes.length,
  sections: kindSections,
  unplaced: [...unplacedBy].sort(([a], [b]) => a.localeCompare(b)).map(([group, count]) => ({ group, count })),
  generatedBy: "tools/render_site.ts",
});
entry.coverage.push(coverage);

// ── the pages ────────────────────────────────────────────────────────────────────────────────

const CSS = `
:root { --bg:#fff; --fg:#17191c; --muted:#5b6168; --line:#d9dde2; --panel:#f6f7f9; --accent:#0b5cad; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --bg:#14171a; --fg:#e8eaed; --muted:#9aa2ab; --line:#2e343b; --panel:#1b1f24; --accent:#7db4ec; }
}
:root[data-theme="dark"] { --bg:#14171a; --fg:#e8eaed; --muted:#9aa2ab; --line:#2e343b; --panel:#1b1f24; --accent:#7db4ec; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 ui-sans-serif, system-ui, sans-serif; }
main { max-width:52rem; margin:0 auto; padding:16px; overflow-wrap:anywhere; }
nav.crumbs { font-size:.9rem; color:var(--muted); margin:8px 0 16px; }
a { color:var(--accent); }
h1 { font-size:1.4rem; line-height:1.3; margin:8px 0; } h2 { font-size:1.15rem; margin:28px 0 8px; } h3 { font-size:1rem; margin:0; }
.m { color:var(--muted); font-size:.9rem; }
.rec { border-top:1px solid var(--line); padding:14px 0; }
.rec .statement { font-size:1.05rem; margin:6px 0; }
.remark { background:var(--panel); border-left:3px solid var(--line); padding:8px 12px; margin:8px 0 0; }
.remark p { margin:4px 0; }
table { width:100%; border-collapse:collapse; font-size:.92rem; }
th, td { text-align:left; vertical-align:top; padding:6px 8px; border-bottom:1px solid var(--line); }
th { background:var(--panel); }
td.n, th.n { text-align:right; white-space:nowrap; }
.clip { width:100%; overflow-x:auto; }
code { font-size:.88em; }
`;

function page(title: string, body: string, crumbs: string): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<style>${CSS}</style>
</head>
<body>
<main>
<nav class="crumbs">${crumbs}</nav>
${body}
</main>
</body>
</html>
`;
}

function pdfLink(n: Node, up: string): string {
  const l = locate(n);
  if (!l) throw new Error(`${n.id} records no PDF page`);
  return `journal p.${esc(l.journal)} · <a class="pdf" href="${up}${esc(l.pdf)}#page=${l.pdfPage}">PDF page ${l.pdfPage}</a>`;
}

function recHtml(r: Node): string {
  const key = tail(r.id);
  const l = locate(r)!;
  const refines = out(r, "refines", "recommendation").map((t) => `<a href="#${esc(tail(t.id))}">${esc(tail(t.id))}</a>`);
  const remarks = out(r, "hasRemark", "remark");
  return `<article class="rec" id="${esc(key)}" data-key="${esc(key)}" data-journal-page="${esc(l.journal)}" data-pdf-page="${l.pdfPage}">
<h3>${esc(key)}</h3>
<p class="statement">${esc(r.properties.statement)}</p>
${r.properties.conditionality ? `<p class="m">Condition: ${esc(r.properties.conditionality)}</p>` : ""}
<p class="m">${pdfLink(r, "../")}${refines.length ? ` · refines ${refines.join(", ")}` : ""} · <code>${esc(r.properties.identifier)}</code></p>
${remarks
  .map(
    (k) => `<div class="remark" id="${esc(tail(k.id))}" data-key="${esc(tail(k.id))}">
<p class="m"><b>Remark</b> ${esc(tail(k.id))} · ${pdfLink(k, "../")}</p>
<p class="text">${esc(k.properties.text)}</p>
</div>`,
  )
  .join("\n")}
</article>`;
}

rmSync(OUT, { recursive: true, force: true });
mkdirSync(join(OUT, "sections"), { recursive: true });
const write = (rel: string, s: string): void => {
  mkdirSync(dirname(join(OUT, rel)), { recursive: true });
  writeFileSync(join(OUT, rel), s);
};

const home = `<a href="../">${esc(decl.title)}</a>`;
let recTotal = 0;
let remarkTotal = 0;
const rows: string[] = [];
for (const s of sections) {
  const key = tail(s.id);
  const recs = out(s, "contains", "recommendation");
  const nRemarks = recs.reduce((n, r) => n + out(r, "hasRemark", "remark").length, 0);
  recTotal += recs.length;
  remarkTotal += nRemarks;
  rows.push(
    `<tr><td><a href="sections/${esc(key)}.html">${esc(s.properties.heading)}</a></td><td class="n">${esc(s.properties.pageRange)}</td><td class="n">${recs.length}</td><td class="n">${nRemarks}</td></tr>`,
  );
  write(
    `sections/${key}.html`,
    page(
      `${s.properties.heading} — ${decl.title}`,
      `<h1>${esc(s.properties.heading)}</h1>
<p class="m">${esc(publication.label)}, journal pp. ${esc(s.properties.pageRange)} · ${recs.length} recommendation(s), ${nRemarks} remark(s). Every statement and remark is verbatim from the English column of the PDF; the build fails if it is not found on the page it cites.</p>
${recs.map(recHtml).join("\n")}`,
      `${home} › sections › ${esc(s.properties.heading)}`,
    ),
  );
}

// The coverage report, as the build wrote it.
const covHtml = String(await remark().use(remarkGfm).use(remarkHtml).process(readFileSync(COVERAGE_MD, "utf-8")));
write("coverage.html", page(`Coverage — ${decl.title}`, `<div class="clip">${covHtml}</div>`, `<a href="./">${esc(decl.title)}</a> › coverage`));

// The L1 document kind, drawn by the platform's viewer.
write(
  "document-kinds/index.html",
  withRenders(pageHtml([entry], `${KIND_OWNER}: ${entry.kind.title}, as realised by ${decl.name}`), ["build/measles.l1.kg.json"], "document-kinds-viewer"),
);
write("document-kinds/l1-guideline.coverage.test.json", JSON.stringify(coverage, null, 2) + "\n");

// Downloads, and the PDF the links point at.
copyFileSync(GRAPH, join(OUT, "measles.l1.kg.json"));
copyFileSync(COVERAGE_MD, join(OUT, "coverage-report.md"));
for (const f of [pdfPath, join(dirname(pdfPath), "manifest.jsonld")]) {
  mkdirSync(dirname(join(OUT, f)), { recursive: true });
  copyFileSync(join(ROOT, f), join(OUT, f));
}
const pdfSha = graph.wasDerivedFrom?.find((w) => w.path === pdfPath)?.sha256 ?? "";

write(
  "index.html",
  page(
    decl.title,
    `<h1>${esc(decl.title)}</h1>
<p>${esc(decl.description)}</p>
<p class="m">Source: <a href="${esc(pdfPath)}">${esc(publication.properties.title)}</a> (${esc(publication.properties.identifier)}), <a href="${esc(publication.properties.url)}">WHO</a>. PDF sha256 <code>${esc(pdfSha)}</code>; the library entry's <a href="${esc(join(dirname(pdfPath), "manifest.jsonld"))}">manifest</a> records the same.</p>
<p><b>${recTotal}</b> recommendations and <b>${remarkTotal}</b> remarks, in ${sections.length} sections. <a href="coverage.html">Coverage report</a> · <a href="document-kinds/">As a WHO guideline (smart-base L1 document kind)</a> · <a href="measles.l1.kg.json" download>Download the L1 graph (JSON-LD)</a></p>
<h2>Sections</h2>
<div class="clip"><table>
<thead><tr><th>Section</th><th class="n">Journal pages</th><th class="n">Recommendations</th><th class="n">Remarks</th></tr></thead>
<tbody>
${rows.join("\n")}
</tbody></table></div>
<p class="m">Built from the authored source <code>l1/measles-position-paper-2017.l1.yaml</code> by <code>tools/build.sh</code>, and rendered by <code>tools/render_site.ts</code>. Ontology: smart-kg L1. The site is derived data and is not committed.</p>`,
    `${esc(decl.name)}`,
  ),
);
if (!existsSync(join(OUT, pdfPath))) throw new Error(`${pdfPath} was not copied`);
console.log(`wrote ${OUT}: ${sections.length} section page(s), ${recTotal} recommendation(s), ${remarkTotal} remark(s); ${KIND} coverage: ${placed.size} of ${graph.nodes.length} node(s) placed`);
