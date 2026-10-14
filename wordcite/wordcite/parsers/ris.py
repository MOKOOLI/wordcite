"""RIS reader (EndNote, Scopus, Web of Science, Google Scholar exports)."""
from __future__ import annotations

import re
from typing import Dict, List

from ..models import Name, Reference

TYPE_MAP = {
    "JOUR": "article-journal", "JFULL": "article-journal", "MGZN": "article-magazine",
    "NEWS": "article-newspaper", "BOOK": "book", "EBOOK": "book", "EDBOOK": "book",
    "CHAP": "chapter", "ECHAP": "chapter", "CONF": "paper-conference", "CPAPER": "paper-conference",
    "THES": "thesis", "RPRT": "report", "ELEC": "webpage", "WEB": "webpage", "BLOG": "webpage",
    "GEN": "book",
}
_LINE = re.compile(r"^([A-Z][A-Z0-9])  - ?(.*)$")


def _make_key(ref: Reference, used: Dict[str, int]) -> str:
    base = re.sub(r"\W+", "", (ref.first_family() or "ref").lower()) + (ref.year or "")
    used[base] = used.get(base, 0) + 1
    return base if used[base] == 1 else f"{base}{chr(ord('a') + used[base] - 2)}"


def parse_ris(text: str) -> List[Reference]:
    records: List[Dict[str, List[str]]] = []
    cur: Dict[str, List[str]] = {}
    for line in text.splitlines():
        m = _LINE.match(line.rstrip())
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "ER":
            if cur:
                records.append(cur)
            cur = {}
            continue
        cur.setdefault(tag, []).append(val)
    if cur:
        records.append(cur)

    refs, used = [], {}
    for r in records:
        g = lambda *tags: next((r[t][0] for t in tags if r.get(t)), "")
        ref = Reference(id=g("ID"), type=TYPE_MAP.get(g("TY"), "article-journal"))
        ref.authors = [Name.parse(a) for t in ("AU", "A1") for a in r.get(t, [])]
        ref.editors = [Name.parse(a) for t in ("ED", "A2") for a in r.get(t, [])] \
            if ref.type in ("chapter", "paper-conference", "book") else []
        ref.title = g("TI", "T1", "CT")
        ref.container = g("T2", "JO", "JF", "BT") if ref.type != "book" else g("T2")
        ref.container_short = g("J2", "JA")
        ref.volume, ref.issue = g("VL"), g("IS")
        sp, ep = g("SP"), g("EP")
        ref.pages = f"{sp}-{ep}" if sp and ep else sp
        date = g("PY", "Y1", "DA")
        ym = re.match(r"(\d{4})(?:[/-](\d{1,2}))?(?:[/-](\d{1,2}))?", date)
        if ym:
            ref.year = ym.group(1)
            ref.month = (ym.group(2) or "").lstrip("0")
            ref.day = (ym.group(3) or "").lstrip("0")
        ref.publisher, ref.place, ref.edition = g("PB"), g("CY"), g("ET")
        ref.doi, ref.url = g("DO"), g("UR", "L2")
        ref.accessed = g("Y2").replace("/", "-")
        ref.isbn = g("SN")
        ref.genre = g("M3")
        if ref.type in ("thesis", "report") and not ref.publisher:
            ref.institution = g("PB")
        ref.language = g("LA")
        if not ref.id:
            ref.id = _make_key(ref, used)
        refs.append(ref)
    return refs
