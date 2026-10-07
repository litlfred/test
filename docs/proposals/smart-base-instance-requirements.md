---
id: reqset:test-smart-base-instance
title: Instantiate smart-base on litlfred/test, and publish its site
methodology: crdm
stage: approved
signOffs:
  - kind: human
    id: litlfred
    at: "2026-10-07"
    scope: reqset:test-smart-base-instance
    outcome: approve
    stage: approved
    reason: "Approve, start now"
    evidence: https://github.com/litlfred/test/issues/3#issuecomment-6036960506
issue: https://github.com/litlfred/test/issues/3
document: docs/proposals/smart-base-instance-requirements.md
---

# Instantiate smart-base on litlfred/test, and publish its site

**Stage: approved** by the owner on 2026-10-07 (*"Approve, start now"*). Pages publishing waits until
the owner has made the repo public.

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
- **SC-02.2** (test): **no git submodule and no `.deps/`.** smart-base and its `needs` closure
  arrive through a declared **remote mount**: `remoteMounts` in `test.json`, pinned to a full
  40-character SHA of `litlfred/folio-assistant`, where smart-base `livesAt` today. Code imported
  from folio-assistant comes in as a pinned package, per bean `w0at`. `bun run mount:remote` resolves
  the closure in a fresh clone, and `bun run mount:remote:check` passes in CI
  ([`remote-mount`](https://github.com/litlfred/folio-assistant/blob/9541dbcd10ea1aaaee30b6dc19bf50111ce75c6d/cat-harness/skills/kg/kg-core/remote-mount.md),
  bean `0mpw`).
- *Risk:* this would be the **first live downstream** of remote mount. The smart-ra pilot (bean
  `0mpw`) still uses a submodule. Any gap found is filed against `0mpw`, not worked around with a
  submodule.

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
- **SC-04.1** (test): the built site contains all 75 recommendations and all 21 remarks, counted
  from the HTML, and each one has a working PDF page link.
- **SC-04.2** (test): the coverage page shows 85 normative sentences, 100% accounted for, and 13
  signed-off exclusions.
- **SC-04.3** (inspection): a person opens the site and confirms it is readable. Screenshots go on
  the PR.

### REQ-05 Published at the expected URL (M) · `req:test-instance#published`
The site SHALL be published at `https://litlfred.github.io/test/` from `main`.
- **SC-05.1** (test): after a merge to `main`, the URL returns 200 and shows the instance's own
  description from `test.json`.
- *D1 decided:* the repo will be made **public**. The owner flips the visibility in Settings,
  because the agent cannot. Pages is then enabled with source "GitHub Actions".

### REQ-06 Nothing derived is committed (S) · `req:test-instance#derived`
The generated graph and the site build SHOULD stay out of git, following smart-kg STORAGE.md and
the REQ-07 decision of the measles L1 requirements.
- **SC-06.1** (inspection): `build/` and the site output are gitignored. Pages publishes from the
  Actions artifact, not from a committed branch, unless D1 forces a `gh-pages` branch.

## 4. Decisions (owner, 2026-10-07)

- **D1:** **make the repo public.** The content is a public WHO paper. The owner changes the
  visibility and enables Pages; the agent cannot do either.
- **D2:** **remote KG mounting** (`remoteMounts`, bean `0mpw`), with no submodule and no sibling
  checkout.
- **D3:** **accept the §2 disposition as proposed.** Only the PDF and its extracted `.txt` move,
  into the library entry.

## 5. Work plan

One bean per requirement. Each bean's `## Done when` copies that requirement's success criteria.
Beans live on this instance's `cat/test/beans` branch, which `folio_init` declares.

| # | Work | Requirement | Depends on | Status |
|---|---|---|---|---|
| 1 | Owner decisions D1–D3 (**decided 2026-10-07**). Owner makes the repo public and enables Pages | n/a | none | D1–D3 decided. Making the repo public and enabling Pages: **owner, open** |
| 2 | Overlay: declare `test.json` / `test.config.json` (needs smart-base, `remoteMounts` pinned to a folio-assistant SHA), without overwriting anything. `folio_init` offers only submodule or sibling linking, so the declaration is written by hand following `remote-mount`, and that gap is filed on `0mpw` | 01, 02 | 1 | **Done** ([`2b425eb`](https://github.com/litlfred/test/commit/2b425ebb5cc7965b76298c2b240a2c2df6d0b312), [`e7a0a0c`](https://github.com/litlfred/test/commit/e7a0a0c4cd7530a5baf31067ae441586a2f6a50c)). The pin is `8b22cc61a789c1f24c6d11a6a8f6990a1930face`, the lock lists 7 instances, and CI runs `mount:remote:check`. Remote-mount findings are reported on PR #4 |
| 3 | Library entry for WER9217 (manifest, sha256, extracted text moved beside it) | 03 | 2 | **Done** ([`72e59ea`](https://github.com/litlfred/test/commit/72e59ea6a0cb809ce0b5a93415be0d039c485344)): `library/wer-92-17/`. The three sha256 values agree, and `check:library-qa` passes |
| 4 | L1 document-kind rendering, PDF page links, coverage page, graph download | 04 | 3 | **Done** ([`078131d`](https://github.com/litlfred/test/commit/078131d3839d4abe843a317d5bb1df4932f1219a)): `_site/` is built in CI and uploaded as the `measles-l1-site` artifact, not deployed. 75 recommendations and 21 remarks are counted from the HTML (see the note below) |
| 5 | Pages publishing per D1; check the URL | 05, 06 | 4 | Open: waits on item 1 (repo public) |
| 6 | Owner review of the rendered site (SC-04.3) | 04 | 5 | Open: waits on item 5 |

*Count corrected 2026-10-07:* SC-04.1 said 80 recommendations. The graph and the built site hold **75**: R01–R52 (52), R13.1–R13.6 (6), V01–V05 (5) and C01–C12 (12). The segmentation is unchanged; only the arithmetic in the sign-off note was wrong.

## 6. Overlap with existing work

| Existing | Relation |
|---|---|
| folio-assistant `getting-started` / `repo-conversion` skills, `getting-started.bpmn` | The process this follows (overlay intent) |
| bean `8pzh`, smart-base `scripts/extract-smart-kg-l1.ts` | Library-entry layout for the PDF (REQ-03) |
| bean `qvxh`, smart-base `document-kinds/l1.json` | The L1 document kind and its viewer (REQ-04) |
| bean `piw1`, skill `dak-l1-library` | The DAK library pattern. Not needed here, because there is no DAK |
| bean `0mpw` (remote mount, PR #2326), bean `w0at` (code as a pinned package) | How smart-base reaches this repo (REQ-02) |
| folio-assistant#2405, `RequirementSet` (bootstrap-tools#11) | The front matter of this document is shaped as a `RequirementSet` (`reqset:`, stage, issue) |
