# Measles vaccines: WHO position paper – April 2017

Ingested source material, attributed to its document. It is not folio content.

Held in the library [`library/`](../) as `wer-92-17`, a smart-base library entry.

| | |
|---|---|
| document id | `wer-92-17` |
| identifier | Weekly Epidemiological Record 92(17):205–228; ISSN 0049-8114 |
| source | <https://www.who.int/teams/immunization-vaccines-and-biologicals/policies/position-papers/measles> |
| source file | [`WER9217.pdf`](WER9217.pdf) (sha256 `ea04e936b5767ebcb4bac8c42d9459f12745d5a934a85baebbc3eeee3f077a8d`) |
| pages | 24 (journal pp. 205–228), English and French in two columns |
| extracted text | [`WER9217.en.txt`](WER9217.en.txt): the English column, one block per journal page (`tools/extract_text.py`) |
| structure | [`structure.json`](structure.json): `pdf-structure/v1`, written by folio-assistant's `cat-harness/scripts/pdf-structure.py --no-sections`, with the title recorded as an editorial correction (the PDF has no Title metadata) |
| provenance | ingested |
| licence | unknown: the issue prints no licence statement |

`manifest.jsonld` records the sha256. `tools/build.sh` fails unless that sha256 equals the PDF's
and the L1 graph's `publication.sha256`. Never edit these files to change the L1 graph; the
authored source is `l1/measles-position-paper-2017.l1.yaml`.
