#!/usr/bin/env python3
"""Build the L1 knowledge-graph document from the authored YAML.

    python3 tools/build_l1.py l1/measles-position-paper-2017.l1.yaml build/measles.l1.kg.json

Emits a smart-kg L1 graph document (ontology/l1/l1.json, schemaVersion 1.0) and FAILS if any
verbatim text in the YAML -- recommendation statements, remarks, conditionality, evidence quotes,
section headings -- cannot be found on the page(s) it cites in the extracted English text.

The output is derived data: it is gitignored and regenerated (smart-kg docs/STORAGE.md).
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

FIRST_JOURNAL_PAGE = 205
CONTEXT = "http://smart.who.int/kg/l1.context.jsonld"


# ---- verbatim checking ---------------------------------------------------------------------

def norm(s):
    """Whitespace- and hyphen-insensitive. Line breaks in a two-column PDF split words at
    arbitrary hyphens, so neither side's hyphens or spacing can be trusted."""
    return re.sub(r"[\s\-­]+", "", s)


# Footnote markers print as bare digits glued to the preceding word or punctuation
# ("study22", "HCWs71", "levels;70"). Never after a capital, so MCV1, B19 and CD4 survive.
FOOTNOTE = re.compile(r"(?<=[a-z.,;:)%])\d{1,2}(?:,\s?\d{1,2})*(?=[\s.,;:]|$)", re.M)


def load_pages(path):
    pages, cur = {}, None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^=== p\.(\d+) ===$", line)
        if m:
            cur = m.group(1)
            pages.setdefault(cur, [])
        elif cur:
            pages[cur].append(line)
    return {p: "\n".join(ls) for p, ls in pages.items()}


def page_list(page):
    parts = re.split(r"[–-]", str(page))
    if len(parts) == 1:
        return [parts[0]]
    lo, hi = int(parts[0]), int(parts[1])
    return [str(p) for p in range(lo, hi + 1)]


class Verifier:
    def __init__(self, pages):
        self.strict = {p: norm(t) for p, t in pages.items()}
        self.loose = {p: norm(FOOTNOTE.sub("", t)) for p, t in pages.items()}
        self.failures, self.footnoted, self.checked = [], [], 0

    def _found(self, q, texts):
        if len(texts) == 1:
            return q in texts[0]
        # Across a page break the running footer and footnotes sit between the halves, so the
        # quote must split into a suffix-free tail of one page and a head of the next.
        a, b = texts[0], texts[1]
        return any(q[:k] in a and b.find(q[k:]) != -1 and q[:k] and q[k:]
                   for k in range(1, len(q)))

    def check(self, what, page, text):
        self.checked += 1
        q = norm(text)
        pages = page_list(page)
        if any(p not in self.strict for p in pages):
            self.failures.append(f"{what}: page {page} not in extracted text")
            return
        if self._found(q, [self.strict[p] for p in pages]):
            return
        if self._found(q, [self.loose[p] for p in pages]):
            self.footnoted.append(what)
            return
        self.failures.append(f"{what}: not found verbatim on p.{page}: {text[:80]}…")


# ---- graph building ------------------------------------------------------------------------

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pdf_location(src, page):
    first = page_list(page)[0]
    return f"{src['pdf']}#page={int(first) - FIRST_JOURNAL_PAGE + 1} (journal p.{page})"


def build(spec, verifier, yaml_path):
    g, src = spec["graph"], spec["graph"]["source"]
    ns = g["namespace"].rstrip("/")
    iri = lambda kind, key: f"{ns}/l1/{kind}/{key}"
    nodes, edges = [], []

    def node(id_, type_, label, props, derivation="derived", note=None, evidence=None):
        n = {"id": id_, "type": type_, "label": label,
             "properties": {k: v for k, v in props.items() if v not in (None, "", [])},
             "derivation": derivation}
        if note:
            n["note"] = note
        if evidence:
            n["evidence"] = evidence
        nodes.append(n)
        return id_

    def edge(pred, s, t, derivation="derived", note=None, evidence=None, qualifier=None):
        e = {"type": "Statement", "predicate": pred, "source": s, "target": t,
             "derivation": derivation}
        if qualifier:
            e["qualifier"] = qualifier
        if note:
            e["note"] = note
        if evidence:
            e["evidence"] = evidence
        edges.append(e)

    # publication
    pub = spec["publication"]
    pub_id = node(iri("publication", pub["key"]), "publication", pub["title"], {
        "title": pub["title"], "creator": pub["creator"], "publisher": pub["publisher"],
        "date": pub["date"], "identifier": pub["identifier"], "language": pub["language"],
        "url": pub["url"], "sha256": sha256(src["pdf"]), "publicationType": pub["publicationType"],
    })
    for old in pub.get("supersedes", []):
        ev = old["evidence"]
        verifier.check(f"supersedes {old['key']}", ev["page"], ev["quote"])
        evd = {"location": pdf_location(src, ev["page"]), "quote": ev["quote"]}
        old_id = node(iri("publication", old["key"]), "publication", old["title"], {
            "title": old["title"], "identifier": old["identifier"], "date": old["date"],
            "publicationType": "position-paper"}, "inferred",
            "Known only from the superseding paper's statement; not itself ingested.", evd)
        edge("supersedes", pub_id, old_id, "derived", evidence=evd)

    # sections
    sec_ids, sec_head = {}, {}
    for s in spec["sections"]:
        verifier.check(f"section heading {s['key']}", s["pageRange"], s["heading"])
        sec_ids[s["key"]] = node(iri("section", s["key"]), "publication-section", s["heading"],
                                 {"heading": s["heading"], "pageRange": s["pageRange"]})
        sec_head[s["key"]] = s["heading"]
        edge("contains", pub_id, sec_ids[s["key"]])

    recs = {r["key"]: r for r in spec["recommendations"]}
    rec_id = lambda k: iri("recommendation", k)
    rec_ev = lambda k: {"location": pdf_location(src, recs[k]["page"]),
                        "quote": recs[k]["statement"]}

    def first_user(field, key):
        for r in spec["recommendations"]:
            if key in r.get(field, []):
                return r["key"]
        raise SystemExit(f"{field} {key} is used by no recommendation")

    # health interventions: the grouping is a decision, evidenced by the first rec using it
    hi_ids = {}
    for h in spec["health_interventions"]:
        k = first_user("recommends", h["key"])
        hi_ids[h["key"]] = node(iri("health-intervention", h["key"]), "health-intervention",
                                h["name"], {"identifier": h["key"], "name": h["name"],
                                            "description": h["description"]}, "decided",
                                "The position paper does not enumerate health interventions; this "
                                "grouping was chosen as the hinge to the DAK healthInterventions "
                                "component.", rec_ev(k))

    pop_ids, int_ids = {}, {}
    for p in spec["populations"]:
        k = first_user("population", p["key"])
        pop_ids[p["key"]] = node(iri("population", p["key"]), "population", p["description"], {
            "description": p["description"], "ageRange": p.get("ageRange"),
            "qualifier": p.get("qualifier")}, "inferred",
            "PICO population read from the recommendation text.", rec_ev(k))
    for i in spec["interventions"]:
        k = first_user("intervention", i["key"])
        int_ids[i["key"]] = node(iri("intervention", i["key"]), "intervention", i["description"],
                                 {"description": i["description"]}, "inferred",
                                 "PICO intervention read from the recommendation text.", rec_ev(k))

    ev_ids = {}
    for e in spec["evidence"]:
        loc = e["location"]
        verifier.check(f"evidence {e['key']}", loc["page"], loc["quote"])
        ev_ids[e["key"]] = node(iri("evidence", e["key"]), "evidence", e["summary"], {
            "summary": e["summary"], "citation": e["citation"]}, "derived",
            "Certainty is not stated in the position paper; it is in the cited table.",
            {"location": pdf_location(src, loc["page"]), "quote": loc["quote"]})

    # recommendations
    for r in spec["recommendations"]:
        k = r["key"]
        verifier.check(f"recommendation {k}", r["page"], r["statement"])
        if r.get("conditionality"):
            verifier.check(f"recommendation {k} conditionality", r["page"], r["conditionality"])
        ev = rec_ev(k)
        rid = node(rec_id(k), "recommendation", f"{k}: {r['statement'][:90]}", {
            "identifier": f"WER9217-{k}", "statement": r["statement"],
            "conditionality": r.get("conditionality"), "status": "active"}, "inferred",
            f"Segmented as one normative statement under '{sec_head[r['section']]}'. "
            "GRADE strength and certainty are not stated in the paper and are left absent.", ev)
        edge("contains", sec_ids[r["section"]], rid, "inferred",
             "Placed under the heading it is printed beneath.", ev)
        for p in r.get("population", []):
            edge("hasPopulation", rid, pop_ids[p], "inferred", "PICO reading.", ev)
        for i in r.get("intervention", []):
            edge("hasIntervention", rid, int_ids[i], "inferred", "PICO reading.", ev)
        for h in r.get("recommends", []):
            edge("recommends", rid, hi_ids[h], "decided",
                 "Assignment to a DAK health intervention.", ev)
        for t in r.get("refines", []):
            if t not in recs:
                raise SystemExit(f"{k} refines unknown {t}")
            edge("refines", rid, rec_id(t), "inferred",
                 f"Narrows or conditions {t} (same setting, population or dose).", ev)
        for e in r.get("supportedBy", []):
            edge("supportedBy", rid, ev_ids[e], "derived",
                 evidence={"location": ev["location"], "quote": "footnote marker on the statement"})
        for n_, rm in enumerate(r.get("remarks", []), 1):
            verifier.check(f"remark {k}/{n_}", rm["page"], rm["text"])
            rev = {"location": pdf_location(src, rm["page"]), "quote": rm["text"]}
            mid = node(iri("remark", f"{k}-{n_}"), "remark", f"{k} remark {n_}",
                       {"text": rm["text"]}, "derived", evidence=rev)
            edge("hasRemark", rid, mid, "inferred",
                 "Implementation consideration printed with this recommendation.", rev)

    # schedule
    sch = spec["schedule"]
    sch_id = node(iri("schedule", sch["key"]), "schedule", sch["name"], {
        "identifier": sch["key"], "name": sch["name"], "scope": sch["scope"]}, "inferred",
        "Assembled from the dose-timing recommendations; the paper has no schedule table.",
        rec_ev(sch["entries"][0]["derivedFrom"][0]))
    edge("definedIn", sch_id, pub_id)
    for se in sch["entries"]:
        ev = rec_ev(se["derivedFrom"][0])
        sid = node(iri("schedule-entry", se["key"]), "schedule-entry", se["key"], {
            k: se.get(k) for k in
            ("antigen", "doseNumber", "series", "targetAge", "minimumInterval", "note")},
            "inferred", "Dose timing read from the recommendations it derives from.", ev)
        edge("contains", sch_id, sid)
        for h in se["schedules"]:
            edge("schedules", sid, hi_ids[h], "inferred", "Dose belongs to this intervention.", ev)
        for k in se["derivedFrom"]:
            edge("derivedFrom", sid, rec_id(k), "inferred", "Restates this recommendation.",
                 rec_ev(k))

    for ind in spec["indicators"]:
        ev = rec_ev(ind["derivedFrom"][0])
        iid = node(iri("indicator", ind["key"]), "indicator", ind["name"], {
            "identifier": ind["key"], "name": ind["name"], "definition": ind["definition"],
            "disaggregation": ind.get("disaggregation")}, "inferred",
            "Target stated in the recommendation; numerator and denominator are not defined in "
            "the paper and are left absent.", ev)
        edge("definedIn", iid, pub_id)
        for h in ind["measures"]:
            edge("measures", iid, hi_ids[h], "inferred", "Measures delivery of this intervention.",
                 ev)
        for k in ind["derivedFrom"]:
            edge("derivedFrom", iid, rec_id(k), "inferred", "Operationalises this target.",
                 rec_ev(k))

    return {
        "@context": CONTEXT,
        "id": f"{ns}/kg/l1",
        "type": "Entity",
        "ontologyVersion": g["ontologyVersion"],
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        .replace("+00:00", "Z"),
        "wasDerivedFrom": [
            {"path": src["pdf"], "sha256": sha256(src["pdf"])},
            {"path": src["text"], "sha256": sha256(src["text"]),
             "note": "English column extracted by tools/extract_text.py; quotes are checked here."},
            {"path": str(yaml_path), "sha256": sha256(yaml_path)},
        ],
        "nodes": nodes,
        "edges": edges,
    }


def main(yaml_path, out_path):
    spec = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    verifier = Verifier(load_pages(spec["graph"]["source"]["text"]))
    doc = build(spec, verifier, yaml_path)

    print(f"verbatim checks: {verifier.checked}, failed: {len(verifier.failures)}, "
          f"matched only after removing footnote markers: {len(verifier.footnoted)}")
    for w in verifier.footnoted:
        print(f"  note: {w}")
    for f in verifier.failures:
        print(f"  FAIL: {f}", file=sys.stderr)
    if verifier.failures:
        sys.exit(1)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    counts = {}
    for n in doc["nodes"]:
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    print(f"wrote {out_path}: {len(doc['nodes'])} nodes, {len(doc['edges'])} edges")
    for t, c in sorted(counts.items()):
        print(f"  {t:22} {c}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
