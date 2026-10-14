"""CSL-JSON reader (the format exported by Zotero, Mendeley and doi.org)."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Union

from ..models import Name, Reference

TYPE_MAP = {
    "article-journal": "article-journal", "article": "article-journal", "article-magazine": "article-magazine",
    "article-newspaper": "article-newspaper", "book": "book", "chapter": "chapter",
    "paper-conference": "paper-conference", "thesis": "thesis", "report": "report",
    "webpage": "webpage", "post-weblog": "webpage", "post": "webpage", "dataset": "webpage",
    "journal-article": "article-journal", "book-chapter": "chapter", "proceedings-article": "paper-conference",
    "dissertation": "thesis", "edited-book": "book", "monograph": "book",
}


def _names(items) -> List[Name]:
    out = []
    for it in items or []:
        if "literal" in it:
            out.append(Name(literal=it["literal"]))
        else:
            out.append(Name(family=it.get("family", ""), given=it.get("given", ""),
                            particle=it.get("non-dropping-particle", ""), suffix=it.get("suffix", "")))
    return out


def _date(d) -> List[str]:
    if not d:
        return ["", "", ""]
    parts = (d.get("date-parts") or [[]])[0] if isinstance(d, dict) else []
    if not parts and isinstance(d, dict):
        raw = str(d.get("raw") or d.get("literal") or "")
        parts = [p for p in raw.replace("/", "-").split("-") if p.isdigit()]
    parts = [str(p) for p in parts] + ["", "", ""]
    return parts[:3]


def _s(v: Any) -> str:
    if isinstance(v, list):
        v = v[0] if v else ""
    return "" if v is None else str(v)


def item_to_reference(item: Dict[str, Any]) -> Reference:
    y, m, d = _date(item.get("issued"))
    ay, am, ad = _date(item.get("accessed"))
    ref = Reference(
        id=str(item.get("id") or item.get("citation-key") or item.get("DOI") or ""),
        type=TYPE_MAP.get(item.get("type", ""), item.get("type") or "article-journal"),
        authors=_names(item.get("author")),
        editors=_names(item.get("editor")),
        title=_s(item.get("title")),
        container=_s(item.get("container-title")),
        container_short=_s(item.get("container-title-short") or item.get("journalAbbreviation")
                           or item.get("short-container-title")),
        volume=_s(item.get("volume")), issue=_s(item.get("issue")), pages=_s(item.get("page")),
        year=y, month=m, day=d,
        publisher=_s(item.get("publisher")), place=_s(item.get("publisher-place")),
        edition=_s(item.get("edition")), doi=_s(item.get("DOI")), url=_s(item.get("URL")),
        accessed="-".join(x.zfill(2) if i else x for i, x in enumerate([ay, am, ad]) if x),
        isbn=_s(item.get("ISBN")), genre=_s(item.get("genre")),
        event=_s(item.get("event-title") or item.get("event")), number=_s(item.get("number")),
        language=_s(item.get("language")), note=_s(item.get("note")),
    )
    if ref.type in ("thesis", "report") and not ref.publisher:
        ref.institution = _s(item.get("authority"))
    return ref


def parse_csl_json(text: Union[str, list, dict]) -> List[Reference]:
    data = json.loads(text) if isinstance(text, str) else text
    if isinstance(data, dict):
        data = data.get("items", [data])
    return [item_to_reference(it) for it in data]
