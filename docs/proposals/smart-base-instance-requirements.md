---
id: reqset:test-smart-base-instance
title: Instantiate smart-base on litlfred/test, and publish its site
methodology: crdm
stage: proposed
issue: https://github.com/litlfred/test/issues/3
document: docs/proposals/smart-base-instance-requirements.md
---

# Instantiate smart-base on litlfred/test, and publish its site

**Stage: proposed.** Nothing in this document is implemented until the owner signs it off on
[#3](https://github.com/litlfred/test/issues/3).

## 1. Needs statement

The owner asked, 2026-10-07: *"where is https://litlfred.github.io/test? — wouldn't it be a part
of instantiating litlfred/smart-base on litlfred/test?"*

`litlfred/test` holds a finished L1 source for the 2017 WHO measles position paper. Today its
outputs (the L1 graph and the coverage report) exist only as CI artifacts. The repo should become
a **folio-assistant instance that stands on the smart-base harness**, so that the L1 content is
rendered and published the way the rest of the SMART estate is. A reviewer would then read it at
`https://litlfred.github.io/test/` instead of downloading artifacts.

This is the **overlay** case in folio-assistant's
[`getting-started`](https://github.com/litlfred/folio-assistant/blob/9541dbcd10ea1aaaee30b6dc19bf50111ce75c6d/cat-harness/skills/conduct/conduct-core/getting-started.md)
skill: folio-assistant laid over a repository that already has work in it. It follows
[`repo-conversion`](https://github.com/litlfred/folio-assistant/blob/9541dbcd10ea1aaaee30b6dc19bf50111ce75c6d/cat-harness/skills/conduct/conduct-core/repo-conversion.md):
scan, show, ask, then move.

**Out of scope:** the L2 DAK and the L3 FHIR IG. This is L1 only, as before.

## 2. What the read-only scan found

Output of `scan-repo-content.ts /home/user/test`, at `fbce319`. It wrote nothing.

| bucket | files | proposed disposition |
|---|---|---|
| library | `l1/source/WER9217.pdf` | becomes a smart-base **library entry** (`manifest.jsonld`, sha256), following the pattern of bean `8pzh` |
| folio (prose) | `README.md`, `docs/proposals/*.md` | stay where they are |
| folio (prose) | `l1/source/WER9217.en.txt` | **reclassified as derived**: it is the text extracted from the PDF, so it goes with the library entry, not with prose |
| unclassified | `l1/*.yaml` | the authored L1 source; stays in place as the input to the L1 document kind |
| unclassified | `tools/*.py`, `tools/build.sh` | stay. The verbatim and coverage checks keep running in CI |

## 3. Requirements

Each statement has at least one success criterion and a verification method.

### REQ-01 Overlay without loss (M) · `req:test-instance#no-loss`
The conversion SHALL NOT move, rename or delete any existing file except as approved in §2.
- **SC-01.1** (inspection): the conversion PR's diff shows only additions, plus the moves listed in
  §2. A file list is attached to the PR.
- **SC-01.2** (test): `tools/build.sh` with `REQUIRE_SIGNOFF=1` still passes. That means 129
  verbatim checks with 0 failing, 100% coverage, and smart-kg conforms.

### REQ-02 A declared instance on smart-base (M) · `req:test-instance#declared`
The repository SHALL declare itself a folio-assistant instance (`test.json`, `test.config.json`,
`contentType: document`) whose `needs` includes **smart-base**.
- **SC-02.1** (test): folio-assistant's declaration checks run in this repo's CI and pass. These
  include the harness-directory and declaration-schema gates that `folio_init` wires up.
- **SC-02.2** (inspection): the folio-assistant platform is linked in the way decided by D2, and it
  resolves in a fresh clone.

### REQ-03 The PDF is a library entry (M) · `req:test-instance#library`
The L1 PDF SHALL be held as a smart-base library entry with a `manifest.jsonld` that records its
title, identifier (WER 92(17), ISSN 0049-8114), source URL and sha256.
- **SC-03.1** (test): the manifest's sha256 equals the PDF's sha256 and the L1 graph's
  `publication.sha256`.
- **SC-03.2** (test): smart-base's library checks pass on the entry.

### REQ-04 The L1 content is rendered (M) · `req:test-instance#rendered`
The site SHALL render the measles L1 through smart-base's **L1 document kind** (`l1.json`). It
SHALL include:
- a page per section listing every recommendation verbatim, with its key, page and remarks;
- a link from each recommendation to its page in the PDF;
- the coverage report;
- a download of the L1 graph.
- **SC-04.1** (test): the built site contains all 80 recommendations and all 21 remarks, counted
  from the HTML, and each one has a working PDF page link.
- **SC-04.2** (test): the coverage page shows 85 normative sentences, 100% accounted for, and 13
  signed-off exclusions.
- **SC-04.3** (inspection): a person opens the site and confirms it is readable. Screenshots go on
  the PR.

### REQ-05 Published at the expected URL (M) · `req:test-instance#published`
The site SHALL be published at `https://litlfred.github.io/test/` from `main`.
- **SC-05.1** (test): after a merge to `main`, the URL returns 200 and shows the instance's own
  description from `test.json`.
- *Blocked by D1:* the repository is **private**. GitHub Pages for a private repository needs a
  paid plan, and Pages must be enabled in Settings.

### REQ-06 Nothing derived is committed (S) · `req:test-instance#derived`
The generated graph and the site build SHOULD stay out of git, following smart-kg STORAGE.md and
the REQ-07 decision of the measles L1 requirements.
- **SC-06.1** (inspection): `build/` and the site output are gitignored. Pages publishes from the
  Actions artifact, not from a committed branch, unless D1 forces a `gh-pages` branch.

## 4. Decisions needed from the owner

- **D1, how to publish while the repo is private.** Options:
  - make the repo public;
  - keep it private and enable Pages, which needs a paid plan;
  - publish only as a staging preview inside folio-assistant's site.
- **D2, how to link folio-assistant.** `folio_init` offers `--link submodule` (the default) or
  `--link sibling`.
- **D3, the §2 disposition** (SC-03 of repo-conversion): accept the table as is, or change any row.

## 5. Work plan

One bean per requirement. Each bean's `## Done when` copies that requirement's success criteria.
Beans live on this instance's `cat/test/beans` branch, which `folio_init` declares.

| # | Work | Requirement | Depends on |
|---|---|---|---|
| 1 | Owner decisions D1–D3 | n/a | none |
| 2 | `folio_init` overlay (`--dir . --type document`, needs smart-base, link per D2), without overwriting anything | 01, 02 | 1 |
| 3 | Library entry for WER9217 (manifest, sha256, extracted text moved beside it) | 03 | 2 |
| 4 | L1 document-kind rendering, PDF page links, coverage page, graph download | 04 | 3 |
| 5 | Pages publishing per D1; check the URL | 05, 06 | 4 |
| 6 | Owner review of the rendered site (SC-04.3) | 04 | 5 |

## 6. Overlap with existing work

| Existing | Relation |
|---|---|
| folio-assistant `getting-started` / `repo-conversion` skills, `getting-started.bpmn` | The process this follows (overlay intent) |
| bean `8pzh`, smart-base `scripts/extract-smart-kg-l1.ts` | Library-entry layout for the PDF (REQ-03) |
| bean `qvxh`, smart-base `document-kinds/l1.json` | The L1 document kind and its viewer (REQ-04) |
| bean `piw1`, skill `dak-l1-library` | The DAK library pattern. Not needed here, because there is no DAK |
| folio-assistant#2405, `RequirementSet` (bootstrap-tools#11) | The front matter of this document is shaped as a `RequirementSet` (`reqset:`, stage, issue) |
