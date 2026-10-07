#!/usr/bin/env python3
"""SC-03.1: the library entry, the PDF and the L1 graph agree on one sha256.

    python3 tools/check_library.py l1/measles-position-paper-2017.l1.yaml build/measles.l1.kg.json

Reads the PDF named by the YAML's `graph.source.pdf`, the `manifest.jsonld` beside it, and the
built graph's `publication` node for this paper. Fails unless all three sha256 values are equal,
and unless the manifest names the PDF and the text file the build reads.
"""
import hashlib
import json
import sys
from pathlib import Path

import yaml


def main(yaml_path, graph_path):
    spec = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    src = spec["graph"]["source"]
    pdf, text = Path(src["pdf"]), Path(src["text"])
    manifest_path = pdf.parent / "manifest.jsonld"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    meta = manifest["meta"]
    key = spec["publication"]["key"]
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    pubs = [n for n in graph["nodes"] if n["type"] == "publication" and n["id"].endswith(f"/{key}")]
    if len(pubs) != 1:
        sys.exit(f"{graph_path}: expected one publication node for {key}, found {len(pubs)}")

    file_sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    shas = {
        f"sha256({pdf})": file_sha,
        f"{manifest_path} meta.source_sha256": meta["source_sha256"],
        f"{graph_path} publication.sha256": pubs[0]["properties"].get("sha256"),
    }
    problems = []
    if len(set(shas.values())) != 1:
        problems.append("sha256 values differ")
    if meta.get("source_file") != pdf.name:
        problems.append(f"manifest source_file {meta.get('source_file')!r} is not {pdf.name!r}")
    if meta.get("text_file") != text.name or text.parent != pdf.parent:
        problems.append(f"manifest text_file {meta.get('text_file')!r} is not {text} beside the PDF")
    for k, v in shas.items():
        print(f"  {v}  {k}")
    if problems:
        sys.exit("library entry check FAILED: " + "; ".join(problems))
    print(f"library entry {pdf.parent}: manifest, PDF and graph agree on sha256 {file_sha}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
