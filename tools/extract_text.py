#!/usr/bin/env python3
"""Extract the English column of WER 92(17) page by page.

The WER is bilingual: English in the left column, French in the right. Pages 1-23 of the PDF
are journal pages 205-227. Output is one block per journal page, headed `=== p.NNN ===`, and is
the text that tools/build_l1.py checks every verbatim quote against.

    python3 tools/extract_text.py l1/source/WER9217.pdf > l1/source/WER9217.en.txt
"""
import re
import sys

import pdfplumber

FIRST_JOURNAL_PAGE = 205
SPLIT_X = 290  # English column ends before x=290 on a 595pt page
# p.205 has a contents sidebar; its English column sits at x=165-350
FIRST_PAGE_BOX = (160, 0, 352)


def clean(text):
    # Line-break hyphens are left as printed; build_l1.py normalises whitespace and hyphens
    text = text.replace("­", "")
    return text


def main(path):
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages[:23]):
            box = (*FIRST_PAGE_BOX, page.height) if i == 0 else (0, 0, SPLIT_X, page.height)
            col = page.crop(box)
            print(f"=== p.{FIRST_JOURNAL_PAGE + i} ===")
            print(clean(col.extract_text() or ""))


if __name__ == "__main__":
    main(sys.argv[1])
