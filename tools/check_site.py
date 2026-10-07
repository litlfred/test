#!/usr/bin/env python3
"""SC-04.1 and SC-04.2: count the rendered site from its HTML, not from the renderer.

    python3 tools/check_site.py [_site] [build/measles.l1.kg.json]

SC-04.1: counts every recommendation (<article class="rec">) and remark (<div class="remark">) in
the section pages. Each one must carry a PDF link `<path>.pdf#page=N` whose file exists in the site,
whose N is a page of that PDF, and whose N agrees with the journal page printed beside it. Each
statement and remark must equal the graph's text exactly. Every recommendation and remark in the
graph must appear exactly once.

SC-04.2: reads the coverage page's summary table and requires 85 normative sentences, 100.0%
accounted for, 13 excluded, 0 pending sign-off and 0 unaccounted.

Also requires the index to link the graph download and the coverage page, and the L1
document-kind page to exist. Exits 1 on any failure.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

FIRST_JOURNAL_PAGE = 205


class Collect(HTMLParser):
    """Recommendations and remarks, each with its key, PDF links, journal page and text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items, self.stack, self.capture = [], [], None
        self.links, self.tables, self.cell, self.row = [], [], None, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if tag == "article" and "rec" in cls:
            self.items.append({"kind": "recommendation", "key": a.get("data-key"), "links": [], "text": "", "meta": ""})
        elif tag == "div" and "remark" in cls:
            self.items.append({"kind": "remark", "key": a.get("data-key"), "links": [], "text": "", "meta": ""})
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.items and "pdf" in cls:
                self.items[-1]["links"].append(a["href"])
        if tag == "p" and self.items:
            self.capture = "text" if ({"statement", "text"} & set(cls)) else "meta" if "m" in cls else None
        if tag == "tr":
            self.row = []
        if tag in ("td", "th"):
            self.cell = ""

    def handle_endtag(self, tag):
        if tag == "p":
            self.capture = None
        if tag in ("td", "th") and self.row is not None:
            self.row.append(self.cell.strip())
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.tables.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.capture and self.items:
            self.items[-1][self.capture] += data
        if self.cell is not None:
            self.cell += data


def parse(path):
    p = Collect()
    p.feed(path.read_text(encoding="utf-8"))
    return p


def main(site="_site", graph_path="build/measles.l1.kg.json"):
    site, failures = Path(site), []
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    want = {}
    for n in graph["nodes"]:
        if n["type"] == "recommendation":
            want[("recommendation", n["id"].rsplit("/", 1)[1])] = n["properties"]["statement"]
        elif n["type"] == "remark":
            want[("remark", n["id"].rsplit("/", 1)[1])] = n["properties"]["text"]

    seen = {}
    for page in sorted((site / "sections").glob("*.html")):
        for it in parse(page).items:
            k = (it["kind"], it["key"])
            seen[k] = seen.get(k, 0) + 1
            where = f"{page.relative_to(site)} {it['kind']} {it['key']}"
            if want.get(k) is None:
                failures.append(f"{where}: not in the graph")
            elif " ".join(it["text"].split()) != " ".join(want[k].split()):
                failures.append(f"{where}: text differs from the graph")
            if len(it["links"]) != 1:
                failures.append(f"{where}: {len(it['links'])} PDF links, expected 1")
                continue
            m = re.fullmatch(r"(.+\.pdf)#page=(\d+)", it["links"][0])
            target = (page.parent / m.group(1)).resolve() if m else None
            if not m or not target.is_file():
                failures.append(f"{where}: PDF link {it['links'][0]} does not resolve to a file in the site")
                continue
            manifest = json.loads((target.parent / "manifest.jsonld").read_text(encoding="utf-8"))
            n, pages = int(m.group(2)), manifest["meta"]["pages"]
            j = re.search(r"journal p\.(\d+)", it["meta"])
            if not 1 <= n <= pages:
                failures.append(f"{where}: #page={n} is outside the PDF's {pages} pages")
            elif not j or int(j.group(1)) - FIRST_JOURNAL_PAGE + 1 != n:
                failures.append(f"{where}: #page={n} does not match the journal page shown ({j.group(0) if j else 'none'})")

    for k in want:
        if seen.get(k, 0) != 1:
            failures.append(f"{k[0]} {k[1]}: rendered {seen.get(k, 0)} times, expected once")
    recs = sum(v for (kind, _), v in seen.items() if kind == "recommendation")
    remarks = sum(v for (kind, _), v in seen.items() if kind == "remark")
    print(f"SC-04.1: {recs} recommendations and {remarks} remarks counted from {len(list((site / 'sections').glob('*.html')))} section pages; "
          f"graph holds {sum(1 for k in want if k[0] == 'recommendation')} and {sum(1 for k in want if k[0] == 'remark')}; "
          f"every one has exactly one PDF link that resolves, in range and matching its journal page: {'yes' if not failures else 'NO'}")

    rows = {r[0].strip("* "): r[1:] for r in parse(site / "coverage.html").tables if r}
    def cell(label, i=0):
        return rows.get(label, [None, None])[i].strip("* ") if label in rows else None
    got = {
        "normative sentences": cell("normative sentences"),
        "excluded with a reason": cell("excluded with a reason"),
        "pending sign-off": cell("of which pending human sign-off (SC-03.3)"),
        "unaccounted": cell("unaccounted"),
        "accounted for": cell("accounted for"),
        "accounted for, share": cell("accounted for", 1),
    }
    expect = {"normative sentences": "85", "excluded with a reason": "13", "pending sign-off": "0",
              "unaccounted": "0", "accounted for": "85", "accounted for, share": "100.0%"}
    for k, v in expect.items():
        if got[k] != v:
            failures.append(f"coverage page: {k} is {got[k]!r}, expected {v!r}")
    print("SC-04.2: coverage page shows " + ", ".join(f"{k} {got[k]}" for k in expect))

    index = parse(site / "index.html")
    for href in ("measles.l1.kg.json", "coverage.html", "document-kinds/"):
        if href not in index.links:
            failures.append(f"index.html: no link to {href}")
    for f in ("measles.l1.kg.json", "document-kinds/index.html"):
        if not (site / f).is_file():
            failures.append(f"{f}: missing")
    if failures:
        print("\n".join("  FAIL " + f for f in failures))
        sys.exit(1)
    print("site check passed")


if __name__ == "__main__":
    main(*sys.argv[1:])
