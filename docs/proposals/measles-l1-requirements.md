---
status: approved (owner, 2026-10-07: "implement as recommended")
methodology: crdm
issue: https://github.com/litlfred/test/issues/1
pr: https://github.com/litlfred/test/pull/2
scope: L1 only (no L2 DAK)
---

# Measles L1: requirements and work plan

**Status: approved** by the owner on 2026-10-07 (*"implement as recommended"*,
[recorded on #1](https://github.com/litlfred/test/issues/1#issuecomment-6035163009)). The decisions
below marked *Decided* are the agent's recommendations, which the owner accepted as a set.

PR #2 has already done some of this work (the L1 YAML, the build and validation). That was done
before this document existed, which is the wrong order. Its status against each requirement is
listed below and stays unaccepted until it is reviewed.

## 1. Needs statement

WHO needs the 2017 measles vaccines position paper (WER 92(17):205–228) as a computable L1 source:
every normative statement in it addressable, quoted verbatim, and traceable to its page. Later work
can then cite a recommendation rather than a document. A reviewer must be able to see what fraction
of the paper is captured, and why anything is not.

**Out of scope:** the L2 DAK (personas, BPMN, DMN, data dictionary) and the L3 FHIR IG.

## 2. What counts as a requirement here

Each requirement below follows the existing base schema, `bootstrap-tools/schemas/requirement.ts`
([source](https://github.com/litlfred/bootstrap-tools/blob/ca85e1dbe641e5710b142bd063be775ff62f8c6d/schemas/requirement.ts)):
an id, and statements with a `conformance` (SHALL / SHOULD / MAY / SHALL NOT) and one sentence.

That schema has **no success-criteria field yet**. This document adds what it is missing:

- every statement has at least one **success criterion**: checkable and pass/fail, written as
  Given/When/Then or as a threshold;
- each criterion has a **verification method**: `test` (automated), `inspection` (a person looks)
  or `review` (a named person signs off).

A statement with no success criterion is not a requirement. It is recorded as an open question
instead.

## 3. Requirements

Priority is M (must have), S (should have) or N (nice to have).

### REQ-01 Source pinned (M) · `req:measles-l1#source`
The L1 publication SHALL be held in the repository and pinned by its sha256 in every graph built
from it.
- **SC-01.1** (test): Given the build, when the graph is produced, then `publication.sha256` equals
  the sha256 of `l1/source/WER9217.pdf`.
- **SC-01.2** (test): Given the PDF, when the text extraction is re-run, then it is byte-identical
  to the committed `WER9217.en.txt` (CI fails otherwise).
- *PR #2 status:* both met.

### REQ-02 Verbatim (M) · `req:measles-l1#verbatim`
Every recommendation statement, remark, conditionality and quote SHALL appear verbatim on the page
it cites.
- **SC-02.1** (test): 0 failed verbatim checks. Whitespace, line-break hyphens and footnote
  markers are ignored, and every footnote-only match is listed by name.
- **SC-02.2** (test): Given one changed word in any statement (for example "9 months" changed to
  "8 months"), the build fails.
- *PR #2 status:* met. 118 checks, 0 failed, 3 footnote-only matches.

### REQ-03 L1 coverage is 100% (M) · `req:measles-l1#coverage`
A QA report SHALL account for every normative sentence in the paper.
- *Normative sentence:* any sentence containing *should, shall, must, recommend\*, should not, is
  not a reason, are not a contraindication*, or *may be given / administered / offered / considered
  / used / co-administered / implemented*.
- *Accounted for:* captured as a recommendation or remark, or listed in a committed exclusions file
  with a reason chosen from a fixed list: `background-fact`, `manufacturer-statement`,
  `duplicate-of:<id>`, `editorial`, `research-question`.

Success criteria:
- **SC-03.1** (test): The QA report shows **accounted-for = 100%** of normative sentences. Below
  100%, the build fails.
- **SC-03.2** (test): The report also shows **captured %** (excluding exclusions), page by page,
  and lists every exclusion with its reason.
- **SC-03.3** (review): The owner signs off the exclusions list. No exclusion counts until it is
  signed off.
- **SC-03.4** (test): Given a sentence deleted from the YAML, the coverage report shows it as
  unaccounted and the build fails.
- *PR #2 status:* **all met.** 85 normative sentences: 72 captured (84.7%) and 13 excluded, so 100%
  accounted for. All 13 exclusions were signed off by the owner on 2026-10-07
  ([evidence](https://github.com/litlfred/test/issues/1#issuecomment-6035371270)). Two proposed
  exclusions (pp. 216 and 218) were captured as remarks instead. CI runs with `REQUIRE_SIGNOFF=1`.

### REQ-04 Ontology conformance (M) · `req:measles-l1#conforms`
The graph SHALL conform to smart-kg L1 at a pinned commit.
- **SC-04.1** (test): smart-kg `tools/validate.mjs` reports "conforms to the ontology".
- **SC-04.2** (test): ajv validation against `shapes/recommendation-graph.schema.json` passes.
- *PR #2 status:* both met, at `66a9b13`.

### REQ-05 Nothing invented (M) · `req:measles-l1#no-invention`
GRADE strength and certainty, indicator numerators and denominators, and anything else the paper
does not state SHALL NOT be set.
- **SC-05.1** (test): No `recommendation` node carries `strength` or `certainty`.
- **SC-05.2** (test): Every node or edge marked `inferred` or `decided` carries a note and a
  page-located quote (smart-kg `validate.mjs` enforces this).
- *PR #2 status:* met.

### REQ-06 Same pipeline as the rest of the estate (S) · `req:measles-l1#pipeline`
The paper SHOULD be ingested as a library entry and extracted the way bean `8pzh` extracts other
guidelines (`smart-base/scripts/extract-smart-kg-l1.ts`), not by a one-off script.
- **SC-06.1** (inspection): The paper is a library entry with a `manifest.jsonld`, under the library
  agreed with the owner.
- **SC-06.2** (test): That extractor, given this entry, produces the same recommendations as the
  authored YAML. Any difference is reported.
- *Known gap:* that extractor finds a recommendation only by a printed label ("Recommendation 8:").
  Position papers have no labels, so it would find **0** here.
- *Decided:* position papers keep the authored YAML. The gap is logged on bean `8pzh`, and
  SC-06.1 and SC-06.2 are deferred.

### REQ-07 Where the generated graph lives (M, decision) · `req:measles-l1#storage`
The location of the generated graph SHALL be decided by the owner, not by default.
- **SC-07.1** (review): The owner picks one of:
  - (a) smart-kg STORAGE.md: not committed, published with the build;
  - (b) the folio-assistant `8pzh` default: committed beside the library entry, with a staleness
    check.
- *Decided:* (a). Not committed; CI uploads the graph and the coverage report as artifacts.

### REQ-08 Human review of segmentation (M) · `req:measles-l1#fidelity`
Deciding which sentences are recommendations, and how each one is divided up, SHALL be confirmed
by a person (the T3 fidelity check from `8pzh`).
- **SC-08.1** (review): The owner, or a named WHO reviewer, signs off on the recommendation list,
  including R13.1–13.6 as separate entries and R41 as one entry spanning two sentences.
  *Signed off* by the owner on 2026-10-07: 75 recommendations (count corrected from 80 to 75 on 2026-10-07; the segmentation is unchanged), 21 remarks and nine judgement
  calls, approved as is ([evidence](https://github.com/litlfred/test/issues/1#issuecomment-6035423832)).
- **SC-08.2** (review): The owner decides whether case management (pp. 210–211) belongs in the L1
  graph. *Decided:* it stays. Vaccine storage and safety guidance (pp. 213 and 217, V01–V05) was
  added on the same basis, so that coverage is reached by capturing sentences rather than
  excluding them.

## 4. Work plan

One bean per requirement. Each bean's `## Done when` is copied from that requirement's success
criteria. A bean starts only after this document is signed off.

| # | Bean | Requirement | Depends on | PR |
|---|---|---|---|---|
| 1 | Owner decisions: storage (REQ-07), pipeline (REQ-06), case management (SC-08.2) | 06, 07, 08 | n/a | none |
| 2 | Coverage QA report and committed exclusions file | 03 | 1 | #2 |
| 3 | Close the coverage gap (pp. 212–219, 227) to 100% accounted for | 03 | 2 | #2 |
| 4 | Library entry for WER9217 + extractor parity (if REQ-06 is kept) | 06 | 1 | new |
| 5 | Owner review of segmentation and exclusions (**done 2026-10-07**) | 08, SC-03.3 | 3 | none |

## 5. Overlap with existing work

| Existing | Relation |
|---|---|
| folio-assistant bean `8pzh`: extract L1 from ingested PDFs | Same goal, label-only extractor. REQ-06 and REQ-07 depend on it |
| bean `piw1`, skill `dak-l1-library` | The DAK library pattern. Applies once a measles DAK exists, which is out of scope here |
| bean `ioa4` / `5uyl`: immunizations L1 from DAK Component 1 | Sibling L1 for immunizations. The measles paper may already be cited there |
| issue [litlfred/folio-assistant#1164](https://github.com/litlfred/folio-assistant/issues/1164) | The requirement schema this document follows |
