# Measles SMART Guidelines DAK

A WHO SMART Guidelines Digital Adaptation Kit for measles immunization, starting from its L1
source:

> **Measles vaccines: WHO position paper – April 2017.** *Weekly Epidemiological Record*
> 92(17):205–228. ISSN 0049-8114.
> <https://www.who.int/teams/immunization-vaccines-and-biologicals/policies/position-papers/measles>

The knowledge graph uses the type graph in
[litlfred/smart-kg](https://github.com/litlfred/smart-kg), `main` @ `66a9b13`, L1 ontology
`schemaVersion 1.0`.

## Status

Scope is **L1 only**: there is no L2 DAK in this repository. Requirements, success criteria
and the work plan are in
[`docs/proposals/measles-l1-requirements.md`](docs/proposals/measles-l1-requirements.md), status
*approved* 2026-10-07.
The L1 coverage QA report (`build/coverage-report.md`, a CI artifact) accounts for 100% of the
paper's normative sentences. 15 exclusions are awaiting owner sign-off.

## Layout

| Path | What | Committed |
|---|---|---|
| `l1/source/WER9217.pdf` | The L1 publication, pinned by sha256 in the graph | yes |
| `l1/source/WER9217.en.txt` | English column, one block per journal page (`tools/extract_text.py`) | yes, checked against the PDF |
| `l1/measles-position-paper-2017.l1.yaml` | **The authored L1 source**: what to review | yes |
| `tools/build_l1.py` | YAML to smart-kg L1 graph document, with the verbatim check | yes |
| `tools/coverage.py`, `l1/coverage-exclusions.yaml` | L1 coverage QA report (REQ-03); exclusions with reasons and sign-off | yes |
| `tools/build.sh` | Extract check, build, coverage, tier-2 and tier-1 validation | yes |
| `build/measles.l1.kg.json` | The generated graph | **no**: derived, gitignored ([smart-kg STORAGE.md](https://github.com/litlfred/smart-kg/blob/main/docs/STORAGE.md)); CI uploads it as an artifact |

## What the L1 graph holds

| Class | Count | Notes |
|---|---|---|
| `recommendation` | 75 | 58 from *WHO position* (pp. 220–227). From *Background*: 12 on case management and post-exposure prophylaxis (pp. 210–211), and 5 on vaccine storage and safety (pp. 213, 217) |
| `remark` | 19 | Implementation considerations printed with a recommendation |
| `publication-section` | 16 | Each sub-heading the recommendations sit under |
| `population` · `intervention` | 31 · 12 | PICO |
| `health-intervention` | 13 | The hinge to the L2 `healthInterventions` component |
| `schedule` · `schedule-entry` | 1 · 6 | MCV0; MCV1/MCV2 for high and low transmission; the HIV additional dose |
| `indicator` | 4 | MCV1 and MCV2 district coverage, campaign coverage, zero-dose children in campaigns |
| `evidence` | 2 | The two evidence-to-recommendation tables the paper cites (footnotes 67, 73) |
| `publication` | 2 | This paper, and the 2009 paper it supersedes |

## Rules the build enforces

- **Verbatim.** Every statement, remark, conditionality, heading and evidence quote must be found
  on the page it cites (ignoring whitespace and hyphens, since the PDF breaks lines mid-word). A
  quote that matches only once footnote markers are removed is reported, not hidden. A single
  changed word (for example "9 months" to "8 months") fails the build.
- **Derivation is labelled.** Verbatim text is `derived`. Deciding that a sentence is a
  recommendation, and the PICO, refinement and schedule readings, are `inferred`. Assigning
  recommendations to health interventions is `decided`. Every node or edge that is not `derived`
  carries a note and a page-located quote.
- **Nothing is invented.**
  - GRADE strength and certainty are left absent: the paper does not state them per
    recommendation.
  - Indicator numerators and denominators are left absent: the paper gives targets only.
  - Background figures (incidence, case-fatality, return on investment) are not turned into nodes.

## Run it

```bash
reset; cd ~/space_cats && (test -d smart-kg || git clone https://github.com/litlfred/smart-kg) && cd test && git fetch && git switch claude/epic-maxwell-we88h8 && git pull && pip install pyyaml pdfplumber && SMART_KG=../smart-kg tools/build.sh
```

## Open questions for review

1. **Case management in L1.** The vitamin A, supportive care and post-exposure statements come
   from the *Background* section, not *WHO position*. They are kept, and their section edge shows
   where they come from. Should they instead cite the WHO vitamin A guidance directly (footnote 23)?
2. **Recommendation granularity.** The six MCV0 situations are separate recommendations that
   refine the lead-in sentence (R13.1–R13.6). The HIV early-dose recommendation (R41) keeps two
   sentences together because the second only makes sense with the first.
3. **Namespace.** `https://smart.who.int/measles` is a placeholder canonical for the DAK.
