#!/usr/bin/env python3
"""L1 coverage QA report: is every normative sentence in the paper accounted for?

    python3 tools/coverage.py l1/measles-position-paper-2017.l1.yaml l1/coverage-exclusions.yaml \
        build/coverage-report.md

REQ-03 (docs/proposals/measles-l1-requirements.md). A sentence is NORMATIVE when it contains one of
the phrases in NORMATIVE below. It is ACCOUNTED FOR when it is captured -- at least COVERED of its
text appears in recommendation statements or remarks of the authored L1 YAML -- or when it is
listed in the exclusions file with a reason from REASONS. The build fails below 100% accounted for.

Exclusions count as SIGNED OFF only once a person signs them (SC-03.3). The report gives both
figures. By default the build fails only on an unaccounted sentence; `--require-signoff` (for a
release) also fails while any exclusion is pending.
"""
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_l1 import FOOTNOTE, load_pages, norm  # noqa: E402

NORMATIVE = re.compile(
    r"\b(should|shall|must|recommend\w*|is not a reason|are not a contraindication|"
    r"may (?:be |even be |also be )?(?:given|administered|offered|considered|used|"
    r"co-administered|implemented))\b", re.I)
REASONS = {"background-fact", "manufacturer-statement", "duplicate-of", "editorial",
           "research-question"}
COVERED = 0.9

# Running heads, page numbers and footnote lines are not body text.
NOT_BODY = re.compile(r"^(\d{1,3}|RELEVE EPIDEMIOLOGIQUE.*|WEEKLY EPIDEMIOLOGICAL RECORD.*)$")
FOOTNOTE_LINE = re.compile(r"^\d{1,2} [A-Z]")
# The subscription box at the foot of the last page is masthead, not position paper.
END_OF_PAPER = "How to obtain the WER through the Internet"


def is_heading(prev, line, nxt):
    """A sub-heading: follows the end of a sentence, carries no terminal punctuation itself, and
    is followed by a line starting a new sentence. Headings are dropped so that they are not
    glued to the first sentence of their section."""
    line = line.strip()
    return (bool(line) and line[0].isupper() and not re.search(r"[.,;:?!–-]$", line)
            and (not prev or re.search(r"[.:?!]\d*$", prev.strip()))
            and bool(nxt) and nxt.strip()[:1].isupper() and len(line) < 60)


def body_sentences(pages):
    """(page, sentence) for the body text, in reading order; a sentence belongs to the page it
    starts on, so one running across a page break is counted once."""
    stream, starts = [], []
    for p in sorted(pages, key=int):
        raw = pages[p].split(END_OF_PAPER)[0].splitlines()
        body = []
        for line in raw:
            if FOOTNOTE_LINE.match(line):
                break
            if not NOT_BODY.match(line.strip()):
                body.append(line)
        lines = [ln for i, ln in enumerate(body)
                 if not is_heading(body[i - 1] if i else "", ln,
                                   body[i + 1] if i + 1 < len(body) else "")]
        starts.append((sum(len(s) for s in stream), p))
        stream.append(" ".join(lines) + " ")
    text = "".join(stream)
    out, pos = [], 0
    for m in re.finditer(r"(?<=[.?!])(?:\d{1,2}(?:,\s?\d{1,2})*)?\s+(?=[A-Z0-9“(])", text):
        out.append((pos, text[pos:m.start()].strip()))
        pos = m.end()
    out.append((pos, text[pos:].strip()))

    def page_at(offset):
        page = starts[0][1]
        for s, p in starts:
            if s <= offset:
                page = p
        return page
    return [(page_at(o), s) for o, s in out if s]


def key(s):
    return norm(FOOTNOTE.sub("", s)).lower()


def coverage(sentence, captured):
    s = key(sentence)
    if not s:
        return 1.0
    hit = [False] * len(s)
    for c in captured:
        if s in c:
            return 1.0
        i = s.find(c)
        while c and i != -1:
            hit[i:i + len(c)] = [True] * len(c)
            i = s.find(c, i + 1)
    return sum(hit) / len(s)


def main(yaml_path, excl_path, out_path, require_signoff=False):
    spec = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    pages = load_pages(spec["graph"]["source"]["text"])
    captured = [key(r["statement"]) for r in spec["recommendations"]]
    captured += [key(m["text"]) for r in spec["recommendations"] for m in r.get("remarks", [])]
    excl = yaml.safe_load(Path(excl_path).read_text(encoding="utf-8")) or {}
    exclusions = excl.get("exclusions", [])
    problems = []
    for e in exclusions:
        if e["reason"].split(":")[0] not in REASONS:
            problems.append(f"exclusion on p.{e['page']} has unknown reason {e['reason']!r}")

    rows, used = [], set()
    for page, s in body_sentences(pages):
        if not NORMATIVE.search(s):
            continue
        cov = coverage(s, captured)
        status, why = ("captured", "") if cov >= COVERED else ("unaccounted", "")
        if status == "unaccounted":
            for i, e in enumerate(exclusions):
                if key(e["text"]) and key(e["text"]) in key(s):
                    status, why = "excluded", e["reason"]
                    used.add(i)
                    if not e.get("signedOffBy"):
                        status = "excluded (pending sign-off)"
                    break
        rows.append((page, status, why, cov, s))
    for i, e in enumerate(exclusions):
        if i not in used:
            problems.append(f"exclusion on p.{e['page']} matches no normative sentence: "
                            f"{e['text'][:60]}…")

    total = len(rows)
    n_cap = sum(r[1] == "captured" for r in rows)
    n_exc = sum(r[1].startswith("excluded") for r in rows)
    n_pending = sum(r[1] == "excluded (pending sign-off)" for r in rows)
    n_un = total - n_cap - n_exc
    pct = lambda n: f"{100 * n / total:.1f}%" if total else "n/a"

    md = ["# L1 coverage report — WER 92(17) measles position paper", "",
          "Generated by `tools/coverage.py` (REQ-03). Target: **100% accounted for**.", "",
          "| | sentences | share |", "|---|---:|---:|",
          f"| normative sentences | {total} | |",
          f"| captured (recommendation or remark) | {n_cap} | {pct(n_cap)} |",
          f"| excluded with a reason | {n_exc} | {pct(n_exc)} |",
          f"| of which pending human sign-off (SC-03.3) | {n_pending} | |",
          f"| **unaccounted** | **{n_un}** | |",
          f"| **accounted for** | **{n_cap + n_exc}** | **{pct(n_cap + n_exc)}** |",
          f"| accounted for, counting signed-off exclusions only | {n_cap + n_exc - n_pending} "
          f"| {pct(n_cap + n_exc - n_pending)} |", "",
          "## By page", "", "| page | normative | captured | excluded | unaccounted |",
          "|---|---:|---:|---:|---:|"]
    for p in sorted({r[0] for r in rows}, key=int):
        rs = [r for r in rows if r[0] == p]
        md.append(f"| {p} | {len(rs)} | {sum(r[1] == 'captured' for r in rs)} | "
                  f"{sum(r[1].startswith('excluded') for r in rs)} | "
                  f"{sum(r[1] == 'unaccounted' for r in rs)} |")
    md += ["", "## Every normative sentence", "", "| page | status | reason | sentence |",
           "|---|---|---|---|"]
    for p, status, why, cov, s in rows:
        md.append(f"| {p} | {status} | {why} | {s.replace('|', '/')[:220]} |")
    if problems:
        md += ["", "## Problems", ""] + [f"- {x}" for x in problems]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"coverage: {total} normative sentences; captured {n_cap} ({pct(n_cap)}), "
          f"excluded {n_exc} ({n_pending} pending sign-off), unaccounted {n_un}; "
          f"accounted for {pct(n_cap + n_exc)} "
          f"({pct(n_cap + n_exc - n_pending)} counting signed-off exclusions only) -> {out_path}")
    for p, status, _, _, s in rows:
        if status == "unaccounted":
            print(f"  UNACCOUNTED p.{p}: {s[:150]}", file=sys.stderr)
    for x in problems:
        print(f"  PROBLEM: {x}", file=sys.stderr)
    if n_un or problems or (require_signoff and n_pending):
        sys.exit(1)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--require-signoff"]
    main(*args[:3], require_signoff="--require-signoff" in sys.argv)
