"""Citation engine: numbering, disambiguation, in-text citations and bibliography."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from . import template as tpl
from .formatting import (NameConfig, apply_case, edition_phrase, first_page, format_date,
                         format_names, format_pages, is_page_range, month_name)
from .locales import get_terms, to_persian_digits
from .models import Reference
from .richtext import RichText
from .styles import Style, get_style

_FA_QUOTES = str.maketrans({"“": "«", "”": "»", "‘": "«", "’": "»"})

TYPE_FALLBACKS = {
    "article-journal": ["article-journal"],
    "article-magazine": ["article-magazine", "article-journal"],
    "article-newspaper": ["article-newspaper", "article-journal"],
    "paper-conference": ["paper-conference", "chapter", "article-journal"],
    "chapter": ["chapter", "book"],
    "book": ["book"],
    "thesis": ["thesis", "book"],
    "report": ["report", "book"],
    "webpage": ["webpage", "book"],
}


@dataclass
class CiteItem:
    key: str
    locator: str = ""
    prefix: str = ""
    suppress_author: bool = False


@dataclass
class Cluster:
    items: List[CiteItem]
    narrative: bool = False


@dataclass
class BibEntry:
    key: str
    label: str
    text: RichText
    rtl: bool = False


@dataclass
class _TermSet:
    terms: Dict[str, str]
    locale: str

    def __call__(self, key: str) -> str:
        if key in self.terms:
            return self.terms[key]
        low = key[:1].lower() + key[1:]
        if low in self.terms:
            val = self.terms[low]
            return val[:1].upper() + val[1:]
        return key


class CitationEngine:
    """Formats citations and the bibliography for one document.

    Usage: ``register()`` every cluster in document order, call ``finalize()``,
    then ``format_cluster()`` for each cluster and ``bibliography()`` once.
    """

    def __init__(self, library: Dict[str, Reference], style="apa", locale: str = "auto",
                 persian_digits: bool = False, title_case: Optional[str] = None,
                 resolver: Optional[Callable[[str], Optional[Reference]]] = None):
        self.library: Dict[str, Reference] = dict(library)
        self.style: Style = get_style(style)
        self.locale = locale
        self.persian_digits = persian_digits
        self.title_case = title_case or self.style.title_case
        self.resolver = resolver
        self.cited: List[str] = []
        self.missing: List[str] = []
        self._numbers: Dict[str, int] = {}
        self._suffix: Dict[str, str] = {}
        self._bib_refs: List[Reference] = []
        self._first_seen: set = set()
        self._templates: Dict[str, list] = {}
        self._finalized = False

    # ------------------------------------------------------------------ locale helpers
    def ref_locale(self, ref: Optional[Reference]) -> str:
        if self.locale in ("en", "fa"):
            return self.locale
        return "fa" if ref is not None and ref.is_persian else "en"

    def terms(self, locale: str) -> _TermSet:
        t = get_terms(locale)
        if locale == "en":
            t.update(self.style.terms)
        return _TermSet(t, locale)

    def _localise(self, rich: RichText, locale: str) -> RichText:
        if locale != "fa":
            return rich

        def fix(text: str) -> str:
            def tok(m):
                w = m.group(0)
                urlish = "://" in w or w.lower().startswith(("doi:", "10.", "www."))
                if not urlish and self.persian_digits:
                    w = to_persian_digits(w)
                return re.sub(r",([»”]?)$", r"،\1", re.sub(r";([»”]?)$", r"؛\1", w))
            text = text.translate(_FA_QUOTES)
            return re.sub(r"\S+", tok, text)
        return rich.map_text(fix)

    # ------------------------------------------------------------------ registration
    def register(self, cluster: Cluster) -> None:
        for item in cluster.items:
            key = item.key
            if key not in self.library and self.resolver is not None:
                ref = self.resolver(key)
                if ref is not None:
                    ref.id = key
                    self.library[key] = ref
            if key in self.library:
                if key not in self.cited:
                    self.cited.append(key)
            elif key not in self.missing:
                self.missing.append(key)

    @property
    def uncited(self) -> List[str]:
        return [k for k in self.library if k not in self.cited]

    def finalize(self, include_uncited: bool = False) -> None:
        keys = list(self.cited) + (self.uncited if include_uncited else [])
        refs = [self.library[k] for k in keys]
        st = self.style
        if st.bib_sort == "author":
            refs.sort(key=self._sort_key)
        self._bib_refs = refs
        if st.kind == "numeric":
            self._numbers = {r.id: i + 1 for i, r in enumerate(refs)}
        elif st.kind == "author-date":
            self._disambiguate(refs)
        self._finalized = True

    def _sort_key(self, ref: Reference):
        names = ref.authors or ref.editors
        who = " ".join(n.sort_key() for n in names) if names else ref.title.casefold()
        return (who, ref.year or "9999", ref.title.casefold())

    def _disambiguate(self, refs: List[Reference]) -> None:
        groups: Dict[tuple, List[Reference]] = {}
        for r in refs:
            terms = self.terms(self.ref_locale(r))
            groups.setdefault((self._cite_names(r, terms, False, False), r.year), []).append(r)
        self._suffix = {}
        for (_, year), members in groups.items():
            if len(members) < 2:
                continue
            members.sort(key=lambda r: r.title.casefold())
            for i, r in enumerate(members):
                letter = chr(ord("a") + i) if i < 26 else str(i + 1)
                self._suffix[r.id] = letter if year else f"-{letter}"

    # ------------------------------------------------------------------ in-text
    def _family(self, n) -> str:
        fam = n.full_family
        return fam.upper() if self.style.cite_upper and not n.literal else fam

    def _cite_names(self, ref: Reference, terms: _TermSet, narrative: bool, first_time: bool) -> str:
        st = self.style
        names = ref.authors or ref.editors
        if not names:
            words = ref.title.split()
            short = " ".join(words[:4]) + ("…" if len(words) > 4 else "")
            return f"“{short}”" if short else ref.id
        fams = [self._family(n) for n in names]
        threshold = st.cite_etal_first if (first_time and st.cite_etal_first) else st.cite_etal_min
        and_ = st.cite_and_narrative if (narrative and st.cite_and_narrative) else st.cite_and
        and_ = and_.replace("{and}", terms("and")).replace("{amp}", terms("amp"))
        if len(fams) >= threshold:
            return f"{fams[0]} {terms('et_al')}"
        if len(fams) == 1:
            return fams[0]
        if len(fams) == 2:
            return fams[0] + and_ + fams[1]
        if and_.strip() == ";":
            return and_.join(fams)
        serial = "," if st.cite_serial_comma else ""
        return ", ".join(fams[:-1]) + serial + and_ + fams[-1]

    def _cite_year(self, ref: Reference, terms: _TermSet) -> str:
        year = ref.year or (terms("nd") if self.style.use_nd else "")
        return year + self._suffix.get(ref.id, "")

    def _locator(self, loc: str, terms: _TermSet) -> str:
        loc = loc.strip().strip(",").strip()
        if not loc:
            return ""
        if self.style.locator_strip_label:
            return re.sub(r"^(pp?\.|pages?|ص+\.)\s*", "", loc, flags=re.I)
        if re.fullmatch(r"[\d\s\-–,]+", loc):
            return f"{terms('pages') if is_page_range(loc) else terms('page')} {loc.replace('-', '–')}"
        return loc

    def format_cluster(self, cluster: Cluster) -> RichText:
        if not self._finalized:
            self.finalize()
        if self.style.kind == "numeric":
            return self._format_numeric(cluster)
        return self._format_author_date(cluster)

    def _numeric_body(self, items: List[CiteItem]) -> str:
        st = self.style
        default_terms = self.terms("en")
        nums = [(self._numbers.get(it.key), self._locator(it.locator, default_terms)) for it in items]
        if any(loc for _, loc in nums):
            parts = [f"{n if n else '?'}{st.num_loc_sep + loc if loc else ''}" for n, loc in nums]
            return st.num_delim.join(parts)
        known = sorted({n for n, _ in nums if n})
        parts: List[str] = []
        i = 0
        while i < len(known):
            j = i
            while j + 1 < len(known) and known[j + 1] == known[j] + 1:
                j += 1
            if j - i >= 2:
                parts.append(f"{known[i]}{st.num_range}{known[j]}")
            else:
                parts.extend(str(n) for n in known[i:j + 1])
            i = j + 1
        parts += ["?" for n, _ in nums if not n]
        return st.num_delim.join(parts)

    def _format_numeric(self, cluster: Cluster) -> RichText:
        st = self.style
        fmt = set(st.cite_fmt) | ({"sup"} if st.superscript else set())
        prefix = " ".join(it.prefix for it in cluster.items if it.prefix)
        body = st.cite_open + (prefix + " " if prefix and not st.superscript else "") + \
            self._numeric_body(cluster.items) + st.cite_close
        out = RichText()
        if cluster.narrative:
            it = cluster.items[0]
            ref = self.library.get(it.key)
            if ref is not None:
                loc = self.ref_locale(ref)
                out.extend(self._localise(RichText().append(
                    self._cite_names(ref, self.terms(loc), True, False)), loc))
                out.append("" if st.superscript else " ")
        if st.cite_fmt and not st.superscript:
            out.append(st.cite_open)
            out.append(body[len(st.cite_open):len(body) - len(st.cite_close)], st.cite_fmt)
            out.append(st.cite_close)
        else:
            out.append(body, fmt)
        return out

    def _format_author_date(self, cluster: Cluster) -> RichText:
        st = self.style
        pieces: List[tuple] = []   # (author, RichText)
        items = list(cluster.items)
        if st.sort_cluster and not cluster.narrative and len(items) > 1:
            items.sort(key=lambda it: self._sort_key(self.library[it.key]) if it.key in self.library
                       else ("\uffff",))
        for it in items:
            ref = self.library.get(it.key)
            if ref is None:
                pieces.append((None, RichText().append(f"{it.key}?", {"b"})))
                continue
            loc = self.ref_locale(ref)
            terms = self.terms(loc)
            first = it.key not in self._first_seen
            self._first_seen.add(it.key)
            author = "" if it.suppress_author else self._cite_names(ref, terms, cluster.narrative, first)
            year = self._cite_year(ref, terms) if st.kind == "author-date" else ""
            locator = self._locator(it.locator, terms)
            if cluster.narrative:
                inner = ", ".join(x for x in [year] if x)
                if locator:
                    inner = (inner + st.cite_loc_sep + locator) if inner else locator
                text = author + (f" {st.cite_open}{inner}{st.cite_close}" if inner else "")
                pieces.append((None, self._localise(RichText().append(text), loc)))
                continue
            core = author
            if year:
                core = core + st.cite_year_sep + year if core else year
            if locator:
                core = core + st.cite_loc_sep + locator if core else locator
            if it.prefix:
                core = f"{it.prefix} {core}"
            prev = pieces[-1] if pieces else None
            if (st.collapse_same_author and prev and prev[0] == author and author and not locator
                    and not it.prefix and year and not prev[1].plain.endswith("?")):
                pieces[-1] = (author, prev[1].append(", " + year))
                continue
            pieces.append((author, self._localise(RichText().append(core), loc)))
        out = RichText()
        if cluster.narrative:
            for i, (_, r) in enumerate(pieces):
                if i:
                    out.append("; ")
                out.extend(r)
            return out
        all_fa = all(self.ref_locale(self.library.get(it.key)) == "fa" for it in cluster.items)
        delim = st.cite_delim.replace(";", "؛") if all_fa else st.cite_delim
        out.append(st.cite_open)
        for i, (_, r) in enumerate(pieces):
            if i:
                out.append(delim)
            out.extend(r)
        out.append(st.cite_close)
        return out

    # ------------------------------------------------------------------ bibliography
    def _template(self, ref: Reference) -> list:
        chain = TYPE_FALLBACKS.get(ref.type, ["article-journal" if ref.container else "book"])
        for t in chain:
            if t in self.style.templates:
                if t not in self._templates:
                    self._templates[t] = tpl.parse(self.style.templates[t])
                return self._templates[t]
        t = "article-journal" if ref.container and "article-journal" in self.style.templates else "book"
        if t not in self._templates:
            self._templates[t] = tpl.parse(self.style.templates[t])
        return self._templates[t]

    def variables(self, ref: Reference, terms: _TermSet) -> Dict[str, str]:
        st = self.style
        locale = terms.locale
        v: Dict[str, str] = {}
        v["authors"] = format_names(ref.authors, st.names, terms.terms)
        ed_cfg: NameConfig = st.editor_names or st.names
        v["editors"] = format_names(ref.editors, ed_cfg, terms.terms)
        ne = len(ref.editors)
        v["ed_short"] = (terms("editor_short") if ne == 1 else terms("editors_short")) if ne else ""
        v["Ed_short"] = v["ed_short"][:1].upper() + v["ed_short"][1:]
        v["ed_long"] = (terms("editor") if ne == 1 else terms("editors")) if ne else ""
        v["title"] = apply_case(ref.title, self.title_case)
        v["container"] = ref.container
        v["container_short"] = ref.container_short or ref.container
        v["volume"] = ref.volume
        v["issue"] = ref.issue
        v["pages"] = format_pages(ref.pages, st.page_range, st.page_delim)
        v["page_first"] = first_page(ref.pages)
        v["pages_label"] = (terms("pages") if is_page_range(ref.pages) else terms("page")) if ref.pages else ""
        nd = terms("nd") if (st.use_nd and st.kind != "numeric") else ""
        v["year"] = (ref.year or nd) + (self._suffix.get(ref.id, "") if st.kind == "author-date" else "")
        if not v["year"].strip("-"):
            v["year"] = ""
        v["year_raw"] = ref.year
        v["month"] = month_name(ref.month, locale) if ref.month else ""
        v["month_abbr"] = month_name(ref.month, locale, abbr=True, dots=st.month_abbr_dots) if ref.month else ""
        v["day"] = ref.day
        publisher = ref.publisher
        if not publisher and ref.type in ("thesis", "report"):
            publisher = ref.institution
        v["publisher"] = publisher
        v["place"] = ref.place
        v["place_publisher"] = ": ".join(x for x in [ref.place, publisher] if x)
        v["publisher_place"] = ": ".join(x for x in [publisher, ref.place] if x)
        v["edition"] = edition_phrase(ref.edition, terms.terms, locale)
        doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", ref.doi.strip(), flags=re.I)
        v["doi_raw"] = doi
        v["doi_url"] = f"https://doi.org/{doi}" if doi else ""
        v["doi"] = (f"doi:{doi}" if st.doi_format == "doi" else v["doi_url"]) if doi else ""
        v["url"] = ref.url
        prefix = terms(st.url_prefix_term) if st.url_prefix_term else ""
        v["link"] = v["doi"] or (prefix + ref.url if ref.url else "")
        v["accessed"] = format_date(ref.accessed, st.accessed_format, locale) if ref.accessed else ""
        v["isbn"] = ref.isbn
        v["genre"] = ref.genre or (terms("thesis") if ref.type == "thesis" else "")
        v["institution"] = ref.institution
        v["event"] = ref.event
        v["number"] = ref.number
        return v

    def format_reference(self, ref: Reference) -> RichText:
        locale = self.ref_locale(ref)
        terms = self.terms(locale)
        rich = tpl.render(self._template(ref), self.variables(ref, terms), terms).cleanup()
        return self._localise(rich, locale)

    def bibliography(self) -> List[BibEntry]:
        if not self._finalized:
            self.finalize()
        out = []
        for ref in self._bib_refs:
            locale = self.ref_locale(ref)
            label = ""
            if self.style.kind == "numeric" and self.style.bib_label:
                label = self.style.bib_label.format(n=self._numbers[ref.id])
                if locale == "fa" and self.persian_digits:
                    label = to_persian_digits(label)
            out.append(BibEntry(ref.id, label, self.format_reference(ref), rtl=(locale == "fa")))
        return out

    def bibliography_title(self, locale: str = "en") -> str:
        return self.terms(locale)(self.style.bib_title_term)
