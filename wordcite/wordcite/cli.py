"""Command line interface:  wordcite process | styles | preview | fetch-doi"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .docx_processor import process_docx
from .engine import CitationEngine
from .parsers import load_references
from .styles import list_styles


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("-b", "--bib", nargs="+", required=True, help="reference file(s): .bib, .json (CSL) or .ris")
    p.add_argument("-s", "--style", default="apa", help="style id (see `wordcite styles`), default: apa")
    p.add_argument("--locale", default="auto", choices=["auto", "en", "fa"],
                   help="terms language; auto = Persian terms for Persian references")
    p.add_argument("--persian-digits", action="store_true", help="use ۰-۹ digits in Persian references")
    p.add_argument("--title-case", choices=["as-is", "sentence", "title"], help="rewrite title casing")


def cmd_process(a) -> int:
    report = process_docx(a.input, a.output or a.input.replace(".docx", f".{a.style}.docx"), a.bib,
                          style=a.style, locale=a.locale, include_uncited=a.include_uncited,
                          bib_title=a.bib_title, persian_digits=a.persian_digits,
                          fetch_dois=a.fetch_dois, title_case=a.title_case)
    print(report.summary())
    return 1 if (a.strict and report.missing) else 0


def cmd_styles(a) -> int:
    rows = [(s.id, s.kind, s.name, s.discipline) for s in list_styles()]
    if a.json:
        print(json.dumps([dict(zip(["id", "kind", "name", "discipline"], r)) for r in rows], indent=2))
        return 0
    w = max(len(r[0]) for r in rows)
    for r in rows:
        print(f"{r[0]:<{w}}  {r[1]:<11}  {r[2]}  ·  {r[3]}")
    print(f"\n{len(rows)} styles")
    return 0


def cmd_preview(a) -> int:
    lib = load_references(a.bib)
    eng = CitationEngine(lib, a.style, locale=a.locale, persian_digits=a.persian_digits, title_case=a.title_case)
    eng.cited = list(lib)
    eng.finalize()
    for e in eng.bibliography():
        body = e.text.to_html() if a.format == "html" else e.text.to_markdown() if a.format == "markdown" \
            else e.text.plain
        print(f"{e.label} {body}".strip())
    return 0


def cmd_fetch(a) -> int:
    from .doi import fetch_doi
    out = []
    for doi in a.doi:
        ref = fetch_doi(doi)
        out.append(ref)
        print(f"✓ {doi}: {ref.title}", file=sys.stderr)
    items = [{
        "id": r.id, "type": r.type, "title": r.title, "container-title": r.container,
        "author": [{"family": n.family, "given": n.given} if not n.literal else {"literal": n.literal}
                   for n in r.authors],
        "volume": r.volume, "issue": r.issue, "page": r.pages, "DOI": r.doi, "URL": r.url,
        "publisher": r.publisher, "issued": {"date-parts": [[int(x) for x in [r.year, r.month, r.day] if x]]},
    } for r in out]
    if a.append:
        try:
            existing = json.load(open(a.append, encoding="utf-8"))
        except FileNotFoundError:
            existing = []
        json.dump(existing + items, open(a.append, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"appended {len(items)} item(s) to {a.append}", file=sys.stderr)
    else:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wordcite", description="Automatic citations for Word documents.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("process", help="format citations + bibliography in a .docx")
    p.add_argument("input", help="input .docx with [@key] markers")
    p.add_argument("-o", "--output", help="output .docx (default: <input>.<style>.docx)")
    _common(p)
    p.add_argument("--include-uncited", action="store_true", help="also list references that are never cited")
    p.add_argument("--bib-title", help='bibliography heading ("" for none)')
    p.add_argument("--fetch-dois", action="store_true", help="resolve [@10.xxxx/yyy] keys online via doi.org")
    p.add_argument("--strict", action="store_true", help="exit with code 1 if any key is missing")
    p.set_defaults(func=cmd_process)

    p = sub.add_parser("styles", help="list available styles")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_styles)

    p = sub.add_parser("preview", help="print the bibliography of a reference file in a style")
    _common(p)
    p.add_argument("--format", choices=["text", "markdown", "html"], default="text")
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("fetch-doi", help="download reference data for DOIs (CSL-JSON)")
    p.add_argument("doi", nargs="+")
    p.add_argument("--append", help="append to this CSL-JSON file")
    p.set_defaults(func=cmd_fetch)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
