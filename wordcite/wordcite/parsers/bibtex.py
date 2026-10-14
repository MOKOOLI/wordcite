"""A small, dependency-free BibTeX / BibLaTeX parser."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from ..models import Name, Reference

_MONTHS = {m: str(i + 1) for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

_ACCENTS = {
    "'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303",
    "=": "\u0304", ".": "\u0307", "u": "\u0306", "v": "\u030C", "H": "\u030B", "c": "\u0327",
}
_SPECIAL = {r"\ss": "ß", r"\o": "ø", r"\O": "Ø", r"\ae": "æ", r"\AE": "Æ", r"\aa": "å",
            r"\AA": "Å", r"\l": "ł", r"\L": "Ł", r"\i": "ı", r"\&": "&", r"\%": "%",
            r"\$": "$", r"\_": "_", r"\#": "#", "~": "\u00a0"}

TYPE_MAP = {
    "article": "article-journal", "book": "book", "booklet": "book", "inbook": "chapter",
    "incollection": "chapter", "inproceedings": "paper-conference", "conference": "paper-conference",
    "proceedings": "book", "phdthesis": "thesis", "mastersthesis": "thesis", "thesis": "thesis",
    "techreport": "report", "report": "report", "manual": "report", "online": "webpage",
    "electronic": "webpage", "www": "webpage", "misc": "webpage", "unpublished": "report",
}


def latex_to_unicode(text: str) -> str:
    import unicodedata

    def accent(m):
        cmd, letter = m.group(1), m.group(2)
        if letter == "\\i":
            letter = "i"
        return unicodedata.normalize("NFC", letter + _ACCENTS[cmd])

    text = re.sub(r"\\([\'`^\"~=.uvHc])\s*\{?(\\i|[A-Za-z])\}?", accent, text)
    for k, v in _SPECIAL.items():
        text = re.sub(re.escape(k) + r"(?![A-Za-z])\s*", v, text) if k[0] == "\\" and k[1:].isalpha() \
            else text.replace(k, v)
    text = re.sub(r"\\(textit|emph|textbf|textrm|texttt|mathrm|textsc)\s*\{([^{}]*)\}", r"\2", text)
    text = text.replace("---", "—").replace("``", "“").replace("''", "”")
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def _read_braced(s: str, i: int) -> Tuple[str, int]:
    depth = 0
    start = i
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1:i], i + 1
        i += 1
    raise ValueError("unbalanced braces in BibTeX value")


def _read_quoted(s: str, i: int) -> Tuple[str, int]:
    depth = 0
    j = i + 1
    while j < len(s):
        c = s[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == '"' and depth == 0 and s[j - 1] != "\\":
            return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unterminated quoted BibTeX value")


def _parse_fields(body: str, strings: Dict[str, str]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    i = 0
    n = len(body)
    while i < n:
        m = re.compile(r"[\s,]*([A-Za-z][\w\-:.+]*)\s*=\s*").match(body, i)
        if not m:
            break
        name = m.group(1).lower()
        i = m.end()
        pieces = []
        while i < n:
            c = body[i]
            if c == "{":
                val, i = _read_braced(body, i)
                pieces.append(val)
            elif c == '"':
                val, i = _read_quoted(body, i)
                pieces.append(val)
            else:
                tm = re.compile(r"[^\s,#}]+").match(body, i)
                if not tm:
                    break
                tok = tm.group(0)
                pieces.append(strings.get(tok.lower(), tok))
                i = tm.end()
            ws = re.compile(r"\s*#\s*").match(body, i)
            if ws and ws.end() > i and "#" in ws.group(0):
                i = ws.end()
                continue
            break
        fields[name] = "".join(pieces)
    return fields


def _split_names(value: str) -> List[str]:
    out, depth, buf = [], 0, []
    tokens = re.split(r"(\s+and\s+|[{}])", value)
    for tok in tokens:
        if tok == "{":
            depth += 1
        elif tok == "}":
            depth -= 1
        if depth == 0 and re.fullmatch(r"\s+and\s+", tok or ""):
            out.append("".join(buf))
            buf = []
        else:
            buf.append(tok or "")
    out.append("".join(buf))
    return [x.strip() for x in out if x.strip()]


def _names(value: str) -> List[Name]:
    names = []
    for raw in _split_names(value):
        if raw.lower() == "others":
            continue
        if raw.startswith("{") and raw.endswith("}") and raw.count("{") == 1:
            names.append(Name(literal=latex_to_unicode(raw)))
        else:
            n = Name.parse(latex_to_unicode(raw))
            names.append(n)
    return names


def _entry_to_reference(etype: str, key: str, f: Dict[str, str]) -> Reference:
    g = lambda *names: next((latex_to_unicode(f[n]) for n in names if f.get(n)), "")
    rtype = TYPE_MAP.get(etype, "book")
    ref = Reference(id=key, type=rtype)
    ref.authors = _names(f.get("author", ""))
    ref.editors = _names(f.get("editor", ""))
    ref.title = g("title")
    if rtype in ("chapter", "paper-conference"):
        ref.container = g("booktitle", "journal", "journaltitle")
        if etype == "inbook" and not ref.container:
            ref.container, ref.title = ref.title, g("chapter")
    else:
        ref.container = g("journal", "journaltitle", "booktitle", "howpublished", "organization")
    ref.container_short = g("shortjournal", "journal_abbr", "journalabbr", "journal-abbreviation", "abbr")
    ref.volume = g("volume")
    ref.issue = g("number", "issue") if rtype != "report" else g("issue")
    ref.number = g("number") if rtype == "report" else ""
    ref.pages = g("pages").replace("--", "-")
    date = g("date")
    ref.year = g("year") or (date[:4] if date else "")
    month = g("month")
    if date and len(date) >= 7 and not month:
        month = date[5:7]
    ref.month = _MONTHS.get(month[:3].lower(), month) if month else ""
    if date and len(date) >= 10:
        ref.day = date[8:10].lstrip("0")
    ref.publisher = g("publisher")
    ref.place = g("address", "location")
    ref.edition = g("edition")
    ref.doi = g("doi")
    ref.url = g("url")
    ref.accessed = g("urldate", "accessed", "lastchecked")
    ref.isbn = g("isbn")
    ref.institution = g("school", "institution", "organization") if rtype in ("thesis", "report") else ""
    ref.genre = g("type")
    if rtype == "thesis" and not ref.genre:
        ref.genre = "Master's thesis" if etype == "mastersthesis" else ""
    ref.event = g("eventtitle", "venue")
    ref.language = g("langid", "language")
    ref.note = g("note")
    return ref


def parse_bibtex(text: str) -> List[Reference]:
    strings = dict(_MONTHS)
    refs: List[Reference] = []
    i = 0
    n = len(text)
    while True:
        at = text.find("@", i)
        if at < 0:
            break
        m = re.compile(r"@\s*(\w+)\s*([{(])").match(text, at)
        if not m:
            i = at + 1
            continue
        etype = m.group(1).lower()
        close = "}" if m.group(2) == "{" else ")"
        j = m.end()
        depth = 0
        while j < n:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                if depth == 0 and close == "}":
                    break
                depth -= 1
            elif c == ")" and close == ")" and depth == 0:
                break
            j += 1
        body = text[m.end():j]
        i = j + 1
        if etype in ("comment", "preamble"):
            continue
        if etype == "string":
            for k, v in _parse_fields(body, strings).items():
                strings[k] = v
            continue
        key, _, rest = body.partition(",")
        refs.append(_entry_to_reference(etype, key.strip(), _parse_fields(rest, strings)))
    return refs
