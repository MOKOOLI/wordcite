"""Citation style definitions.

Every style is plain data: name formatting rules, in-text citation rules and one
template per reference type (see ``wordcite.template`` for the template syntax).
Add a new style by creating a ``Style`` and calling ``register(style)``.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional

from .formatting import NameConfig


@dataclass
class Style:
    id: str
    name: str
    kind: str                                   # "numeric" | "author-date" | "author-page"
    templates: Dict[str, str]
    discipline: str = ""
    names: NameConfig = field(default_factory=NameConfig)
    editor_names: Optional[NameConfig] = None
    # ---- in-text citations
    cite_open: str = "("
    cite_close: str = ")"
    cite_fmt: frozenset = frozenset()           # e.g. {"i"} for Science's (*1*)
    superscript: bool = False
    cite_delim: str = "; "                      # between works (author-date)
    cite_year_sep: str = ", "
    cite_loc_sep: str = ", "
    cite_and: str = " {and} "
    cite_and_narrative: Optional[str] = None
    cite_serial_comma: bool = False
    cite_etal_min: int = 3
    cite_etal_first: Optional[int] = None       # APA 6: list up to 5 authors on first cite
    cite_upper: bool = False
    collapse_same_author: bool = True
    sort_cluster: bool = True                   # author-date: order works in (A; B) alphabetically
    num_delim: str = ","
    num_range: str = "–"
    num_loc_sep: str = ", "
    locator_strip_label: bool = False
    # ---- bibliography
    bib_sort: str = "citation"                  # "citation" | "author"
    bib_label: str = "{n}."
    bib_title_term: str = "references"
    hanging_indent: bool = True
    title_case: str = "as-is"
    page_range: str = "full"                    # "full" | "minimal" | "first"
    page_delim: str = "–"
    accessed_format: str = "dmy"
    month_abbr_dots: bool = True
    doi_format: str = "url"                     # "url" -> https://doi.org/x, "doi" -> doi:x
    url_prefix_term: str = ""                   # e.g. "retrieved_from" for APA 6
    use_nd: bool = True
    terms: Dict[str, str] = field(default_factory=dict)  # English term overrides
    aliases: List[str] = field(default_factory=list)

    def derive(self, **changes) -> "Style":
        """Copy this style with some fields changed (aliases are not inherited)."""
        changes.setdefault("aliases", [])
        return replace(self, **changes)


STYLES: Dict[str, Style] = {}
_ALIASES: Dict[str, str] = {}


def register(style: Style) -> Style:
    STYLES[style.id] = style
    for a in style.aliases:
        _ALIASES[a.lower()] = style.id
    return style


def get_style(style_id) -> Style:
    if isinstance(style_id, Style):
        return style_id
    key = str(style_id).strip().lower()
    key = _ALIASES.get(key, key)
    if key not in STYLES:
        raise KeyError(f"Unknown style '{style_id}'. Available: {', '.join(sorted(STYLES))}")
    return STYLES[key]


def list_styles() -> List[Style]:
    return [STYLES[k] for k in STYLES]


# ============================================================================ name presets
VANC_NAMES = NameConfig(first="family_initials", initial_dot="", initial_space="", delim=", ",
                        and_two=", ", and_last=", ", etal_max=6, etal_show=6, etal_delim=", ")
INITIALS_FIRST = NameConfig(first="initials_family", delim=", ", and_two=" {and} ",
                            and_last=", {and} ")
CHICAGO_NAMES = NameConfig(first="family_comma_given", rest="given_family", delim=", ",
                           and_two=", {and} ", and_last=", {and} ", etal_max=10, etal_show=7)
GIVEN_FIRST_EDITORS = NameConfig(first="given_family", delim=", ", and_two=" {and} ",
                                 and_last=", {and} ")

# ============================================================================ numeric family
VANCOUVER_T = {
    "article-journal": "<{authors}. ><{title}. ><{container_short}. ><{year}>< {month_abbr}>"
                       "<;{volume}><({issue})><:{pages}>.< doi:{doi_raw}>",
    "book": "<{authors}. ><{title}. ><{edition}. ><{place_publisher}; ><{year}>.",
    "chapter": "<{authors}. ><{title}. >{t:In}: <{editors}, {ed_long}. ><{container}. ><{place_publisher}; ><{year}>.< {t:page} {pages}.>",
    "paper-conference": "<{authors}. ><{title}. >{t:In}: <{editors}, {ed_long}. ><{container}; >"
                        "<{event}; ><{place_publisher}; ><{year}>.< {t:page} {pages}.>",
    "thesis": "<{authors}. ><{title} [{genre}]. ><{place_publisher}; ><{year}>.",
    "report": "<{authors}. ><{title}. ><{place_publisher}; ><{year}>.< Report No.: {number}.>",
    "webpage": "<{authors}. ><{title} {t:internet}. ><{place_publisher}; ><{container}; ><{year}>"
               "< [{t:cited} {accessed}]>.< {t:Available_from} {url}>",
}

register(Style(
    id="vancouver", name="Vancouver (ICMJE)", kind="numeric", discipline="Medicine, health sciences",
    templates=VANCOUVER_T, names=VANC_NAMES, cite_open="[", cite_close="]", bib_label="{n}.",
    page_range="minimal", page_delim="-", accessed_format="ymd_abbr", month_abbr_dots=False,
    aliases=["icmje", "vancouver-brackets"]))

register(STYLES["vancouver"].derive(
    id="nlm", name="NLM / Citing Medicine", discipline="Medicine (US National Library of Medicine)",
    names=replace(VANC_NAMES, etal_max=None), superscript=True, cite_open="", cite_close="",
    aliases=["citing-medicine"]))

register(Style(
    id="ama", name="AMA (11th edition)", kind="numeric", discipline="Medicine (JAMA)",
    templates={
        "article-journal": "<{authors}. ><{title}. ><{container_short|i}. ><{year}><;{volume}>"
                           "<({issue})><:{pages}>.< doi:{doi_raw}>",
        "book": "<{authors}. ><{title|i}. ><{edition}. ><{publisher}; ><{year}>.",
        "chapter": "<{authors}. ><{title}. >{t:In}: <{editors}, {ed_short}. ><{container|i}. >"
                   "<{publisher}; ><{year}><:{pages}>.",
        "webpage": "<{authors}. ><{title}. ><{container}. ><{t:Accessed} {accessed}. ><{url}>",
    },
    names=replace(VANC_NAMES, etal_max=6, etal_show=3),
    superscript=True, cite_open="", cite_close="", bib_label="{n}.", page_delim="-",
    accessed_format="mdy", aliases=["ama11", "jama"]))

register(Style(
    id="ieee", name="IEEE", kind="numeric", discipline="Engineering, computer science",
    templates={
        "article-journal": "<{authors}, ><“{title},” ><{container|i}, ><{t:vol} {volume}, >"
                           "<{t:no} {issue}, ><{pages_label} {pages}, ><{month_abbr} ><{year}>"
                           "<, doi: {doi_raw}>.",
        "book": "<{authors}, ><{title|i}, ><{edition}. ><{place_publisher}, ><{year}>.",
        "chapter": "<{authors}, ><“{title},” >{t:in} <{container|i}, ><{editors}, {Ed_short} >"
                   "<{place_publisher}, ><{year}, ><{pages_label} {pages}>.",
        "paper-conference": "<{authors}, ><“{title},” >{t:in} <{container|i}, ><{place}, ><{year}, >"
                            "<{pages_label} {pages}><, doi: {doi_raw}>.",
        "thesis": "<{authors}, ><“{title},” ><{genre}, ><{publisher}, ><{place}, ><{year}>.",
        "report": "<{authors}, ><“{title},” ><{publisher}, ><{place}, ><Rep. {number}, ><{year}>.",
        "webpage": "<{authors}. ><“{title}.” ><{container}. >[{t:Online}]. <{t:Available}: {url}>"
                   "< ({t:accessed} {accessed})>.",
    },
    names=replace(INITIALS_FIRST, etal_max=6, etal_show=1, etal_delim=" "),
    editor_names=INITIALS_FIRST,
    cite_open="[", cite_close="]", num_delim=", ", bib_label="[{n}]", accessed_format="mdy_abbr"))

register(Style(
    id="acs", name="ACS (American Chemical Society)", kind="numeric", discipline="Chemistry",
    templates={
        "article-journal": "<{authors}. ><{title}. ><{container_short|i} ><{year|b}><, {volume|i}>"
                           "< ({issue})><, {pages}>.< DOI: {doi_raw}.>",
        "book": "<{authors}. ><{title|i}, ><{edition}; ><{publisher_place}, ><{year}>.",
        "chapter": "<{authors}. ><{title}. >{t:In} <{container|i}; ><{editors}, {Ed_short}; >"
                   "<{publisher_place}, ><{year}><; pp {pages}>.",
        "webpage": "<{authors}. ><{title}. ><{container}. ><{url} >< ({t:accessed} {accessed})>.",
    },
    names=NameConfig(first="family_comma_initials", delim="; ", and_two="; ", and_last="; "),
    superscript=True, cite_open="", cite_close="", bib_label="({n})", accessed_format="mdy_abbr"))

register(Style(
    id="nature", name="Nature", kind="numeric", discipline="Multidisciplinary science",
    templates={
        "article-journal": "<{authors}. ><{title}. ><{container_short|i} ><{volume|b}, ><{pages} ><({year})>.",
        "book": "<{authors}. ><{title|i} ><({publisher+year})>.",
        "chapter": "<{authors}. ><{title}. >{t:in} <{container|i} ><({ed_short} {editors}) ><{pages} >"
                   "<({publisher+year})>.",
        "webpage": "<{authors}. ><{title}. ><{container|i} ><{url} ><({year})>.",
    },
    names=NameConfig(first="family_comma_initials", delim=", ", and_two=" {amp} ", and_last=" {amp} ",
                     etal_max=5, etal_show=1, etal_delim=" "),
    superscript=True, cite_open="", cite_close="", bib_label="{n}.", terms={"editors_short": "eds"}))

register(Style(
    id="science", name="Science", kind="numeric", discipline="Multidisciplinary science",
    templates={
        "article-journal": "<{authors}, ><{title}. ><{container_short|i} ><{volume|b}, ><{pages} ><({year})>.",
        "book": "<{authors}, ><{title|i} ><({publisher+year})>.",
        "chapter": "<{authors}, ><{title}, >{t:in} <{container|i}, ><{editors}, {Ed_short} >"
                   "<({publisher+year}), ><{pages_label} {pages}>.",
        "webpage": "<{authors}, ><{title} ><({container+year}); ><{url}>.",
    },
    names=NameConfig(first="initials_family", delim=", ", and_two=", ", and_last=", ",
                     etal_max=10, etal_show=1, etal_delim=", "),
    cite_open="(", cite_close=")", cite_fmt=frozenset({"i"}), num_delim=", ", bib_label="{n}."))

_AIP_T = {
    "article-journal": "<{authors}, ><{container_short} ><{volume|b}, ><{page_first} ><({year})>.",
    "book": "<{authors}, ><{title|i}, ><{edition} ><({publisher+place+year})>.",
    "chapter": "<{authors}, ><{t:in} {container|i}, ><{editors}, {ed_short} ><({publisher+place+year}), >"
               "<{pages_label} {pages}>.",
    "webpage": "<{authors}, ><“{title},” ><{url} ><({year})>.",
}
register(Style(
    id="aip", name="AIP (American Institute of Physics)", kind="numeric", discipline="Physics",
    templates=_AIP_T, names=replace(INITIALS_FIRST, etal_max=10, etal_show=1, etal_delim=" "),
    superscript=True, cite_open="", cite_close="", bib_label="{n}"))

register(STYLES["aip"].derive(
    id="aps", name="APS (Physical Review)", discipline="Physics",
    templates={**_AIP_T, "article-journal": "<{authors}, ><{title}, ><{container_short} ><{volume|b}, >"
                                            "<{page_first} ><({year})>."},
    superscript=False, cite_open="[", cite_close="]", bib_label="[{n}]", aliases=["physical-review"]))

register(Style(
    id="rsc", name="RSC (Royal Society of Chemistry)", kind="numeric", discipline="Chemistry",
    templates={
        "article-journal": "<{authors}, ><{container_short|i}, ><{year}, ><{volume|b}, ><{pages}>.",
        "book": "<{authors}, ><{title|i}, ><{publisher}, ><{place}, ><{edition}, ><{year}>.",
        "chapter": "<{authors}, ><{t:in} {container|i}, ><{ed_short} {editors}, ><{publisher}, >"
                   "<{place}, ><{year}, ><{pages_label} {pages}>.",
        "webpage": "<{authors}, ><{title}, ><{url}, ><({t:accessed} {accessed})>.",
    },
    names=NameConfig(first="initials_family", delim=", ", and_two=" {and} ", and_last=" {and} ",
                     etal_max=10, etal_show=1, etal_delim=" "),
    superscript=True, cite_open="", cite_close="", bib_label="{n}"))

register(STYLES["vancouver"].derive(
    id="bmj", name="BMJ", discipline="Medicine (British Medical Journal)",
    names=replace(VANC_NAMES, etal_max=6, etal_show=3), superscript=True, cite_open="", cite_close="",
    bib_label="{n}"))

register(STYLES["vancouver"].derive(
    id="lancet", name="The Lancet", discipline="Medicine",
    templates={**VANCOUVER_T,
               "article-journal": "<{authors}. ><{title}. ><{container_short|i} ><{year}; ><{volume}: >"
                                  "<{pages}>."},
    names=replace(VANC_NAMES, etal_max=6, etal_show=3), superscript=True, cite_open="", cite_close="",
    bib_label="{n}", page_range="full", page_delim="–"))

register(STYLES["vancouver"].derive(
    id="plos", name="PLOS", discipline="Life sciences (PLOS journals)", bib_label="{n}.",
    page_range="full", page_delim="–", aliases=["plos-one"]))

register(Style(
    id="springer", name="Springer Basic (numbered)", kind="numeric", discipline="Multidisciplinary",
    templates={
        "article-journal": "<{authors} ><({year}) ><{title}. ><{container_short} ><{volume}><:{pages}>."
                           "< {doi_url}>",
        "book": "<{authors} ><({year}) ><{title|i}, ><{edition}. ><{publisher}, ><{place}>.",
        "chapter": "<{authors} ><({year}) ><{title}. >{t:In}: <{editors} ({ed_short}) ><{container|i}. >"
                   "<{publisher}, ><{place}, ><pp {pages}>.",
        "webpage": "<{authors} ><({year}) ><{title}. ><{url}. ><{t:Accessed} {accessed}>",
    },
    names=replace(VANC_NAMES, etal_max=None),
    cite_open="[", cite_close="]", bib_label="{n}.", aliases=["springer-basic"]))

_ISO_T = {
    "article-journal": "<{authors}. ><{title}. ><{container|i}. ><{year}, ><{t:vol} {volume}, >"
                       "<{t:no} {issue}, ><{pages_label} {pages}>.< DOI {doi_raw}.>",
    "book": "<{authors}. ><{title|i}. ><{edition}. ><{place_publisher}, ><{year}>.< ISBN {isbn}.>",
    "chapter": "<{authors}. ><{title}. >{t:In}: <{editors}, {ed_short}. ><{container|i}. ><{place_publisher}, ><{year}, ><{pages_label} {pages}>.",
    "webpage": "<{authors}. ><{title|i} [{t:online}]. ><{container}, ><{year}. ><[{t:Accessed} {accessed}]. >"
               "<{t:Available_from} {url}>",
}
_ISO_NAMES = NameConfig(first="family_comma_given", upper=True, delim=", ", and_two=" {and} ",
                        and_last=" {and} ", etal_max=3, etal_show=1, etal_delim=" ")
register(Style(
    id="iso690-numeric", name="ISO 690 (numeric)", kind="numeric", discipline="International standard",
    templates=_ISO_T, names=_ISO_NAMES, cite_open="[", cite_close="]", bib_label="[{n}]",
    accessed_format="iso", aliases=["iso690"]))

register(STYLES["vancouver"].derive(
    id="cse-cs", name="CSE (citation-sequence)", discipline="Biology, life sciences",
    names=replace(VANC_NAMES, etal_max=10, etal_show=10), page_range="full", page_delim="–",
    aliases=["cse"]))

# ============================================================================ author-date family
register(Style(
    id="harvard", name="Harvard (Cite Them Right)", kind="author-date", discipline="General, UK/AU universities",
    templates={
        "article-journal": "<{authors} ><({year}) ><‘{title}’, ><{container|i}, ><{volume}><({issue})>"
                           "<, {pages_label} {pages}>.< {t:Available_at} {link}>< ({t:Accessed}: {accessed})>.",
        "book": "<{authors} ><({year}) ><{title|i}. ><{edition}. ><{place_publisher}>."
                "< {t:Available_at} {link}>< ({t:Accessed}: {accessed})>.",
        "chapter": "<{authors} ><({year}) ><‘{title}’, >{t:in} <{editors} ({ed_short}) ><{container|i}. >"
                   "<{place_publisher}, ><{pages_label} {pages}>.",
        "paper-conference": "<{authors} ><({year}) ><‘{title}’, >{t:in} <{container|i}. ><{place_publisher}, ><{pages_label} {pages}>.< {t:Available_at} {link}>.",
        "thesis": "<{authors} ><({year}) ><{title|i}. ><{genre}. ><{publisher}>.< {t:Available_at} {link}>"
                  "< ({t:Accessed}: {accessed})>.",
        "webpage": "<{authors} ><({year}) ><{title|i}. ><{t:Available_at} {url} ><({t:Accessed}: {accessed})>.",
    },
    names=NameConfig(first="family_comma_initials", initial_space="", delim=", ", and_two=" {and} ",
                     and_last=" {and} "),
    cite_etal_min=4, bib_sort="author", bib_label="", accessed_format="dmy",
    terms={"edition": "edn", "editors_short": "eds"},
    aliases=["harvard-cite-them-right", "cite-them-right"]))

register(Style(
    id="harvard-elsevier", name="Elsevier Harvard", kind="author-date", discipline="Elsevier journals",
    templates={
        "article-journal": "<{authors}, ><{year}. ><{title}. ><{container_short} ><{volume}><, {pages}>."
                           "< {doi_url}>",
        "book": "<{authors}, ><{year}. ><{title}, ><{edition}. ><{publisher}, ><{place}>.",
        "chapter": "<{authors}, ><{year}. ><{title}, >{t:in}: <{editors} ({Ed_short}), ><{container}. >"
                   "<{publisher}, ><{place}, ><pp. {pages}>.",
        "webpage": "<{authors}, ><{year}. ><{title}. ><{url} ><({t:accessed} {accessed})>.",
    },
    names=NameConfig(first="family_comma_initials", initial_space="", delim=", ", and_two=", ",
                     and_last=", "),
    bib_sort="author", bib_label="", accessed_format="dmy", aliases=["elsevier-harvard"]))

_APA_NAMES = NameConfig(first="family_comma_initials", delim=", ", and_two=", {amp} ",
                        and_last=", {amp} ", etal_max=20, etal_show=19, ellipsis_last=True)
_APA_EDITORS = NameConfig(first="initials_family", delim=", ", and_two=" {amp} ", and_last=", {amp} ")
register(Style(
    id="apa", name="APA (7th edition)", kind="author-date", discipline="Psychology, education, social sciences",
    templates={
        "article-journal": "<{authors}. ><({year}). ><{title}. ><{container|i}><, {volume|i}><({issue})>"
                           "<, {pages}>.< {link}>",
        "book": "<{authors}. ><({year}). ><{title|i}>< ({edition})>. <{publisher}.>< {link}>",
        "chapter": "<{authors}. ><({year}). ><{title}. >{t:In} <{editors} ({Ed_short}), ><{container|i}>"
                   "< ({pages_label} {pages})>. <{publisher}.>< {link}>",
        "thesis": "<{authors}. ><({year}). ><{title|i}>< [{genre}, {publisher}]>. <{link}>",
        "report": "<{authors}. ><({year}). ><{title|i}>< ({t:Report} No. {number})>. <{publisher}.>< {link}>",
        "webpage": "<{authors}. ><({year}). ><{title|i}>. <{container}. ><{url}>",
    },
    names=_APA_NAMES, editor_names=_APA_EDITORS,
    cite_and=" {amp} ", cite_and_narrative=" {and} ", cite_serial_comma=True,
    bib_sort="author", bib_label="", accessed_format="mdy", aliases=["apa7", "apa-7"]))

register(STYLES["apa"].derive(
    id="apa6", name="APA (6th edition)",
    templates={
        "article-journal": "<{authors}. ><({year}). ><{title}. ><{container|i}><, {volume|i}><({issue})>"
                           "<, {pages}>.< {link}>",
        "book": "<{authors}. ><({year}). ><{title|i}>< ({edition})>. <{place_publisher}.>< {link}>",
        "chapter": "<{authors}. ><({year}). ><{title}. >{t:In} <{editors} ({Ed_short}), ><{container|i}>"
                   "< ({pages_label} {pages})>. <{place_publisher}.>",
        "webpage": "<{authors}. ><({year}). ><{title|i}>. <{link}>",
    },
    names=replace(_APA_NAMES, etal_max=7, etal_show=6),
    # APA 6: 3-5 authors are listed in full on the first citation, then "et al."
    doi_format="doi", url_prefix_term="retrieved_from", cite_etal_min=3, cite_etal_first=6,
    aliases=["apa-6"]))

_CHICAGO_T = {
    "article-journal": "<{authors}. ><{year}. ><“{title}.” ><{container|i}>< {volume}>< ({issue})>"
                       "<: {pages}>.< {link}.>",
    "book": "<{authors}. ><{year}. ><{title|i}. ><{edition}. ><{place_publisher}>.< {link}.>",
    "chapter": "<{authors}. ><{year}. ><“{title}.” >{t:In} <{container|i}><, {t:edited_by} {editors}>"
               "<, {pages}>. <{place_publisher}>.",
    "thesis": "<{authors}. ><{year}. ><“{title}.” ><{genre}, ><{publisher}>.",
    "webpage": "<{authors}. ><{year}. ><“{title}.” ><{container}. ><{t:Accessed} {accessed}. ><{url}.>",
}
register(Style(
    id="chicago", name="Chicago (17th, author-date)", kind="author-date", discipline="History, sciences, social sciences",
    templates=_CHICAGO_T, names=CHICAGO_NAMES, editor_names=GIVEN_FIRST_EDITORS,
    cite_year_sep=" ", cite_loc_sep=", ", locator_strip_label=True, cite_etal_min=4,
    cite_serial_comma=True, bib_sort="author", bib_label="", accessed_format="mdy",
    aliases=["chicago-author-date", "chicago17"]))

register(STYLES["chicago"].derive(
    id="turabian", name="Turabian (9th, author-date)", discipline="Student papers and theses",
    aliases=["turabian-author-date"]))

register(Style(
    id="mla", name="MLA (9th edition)", kind="author-page", discipline="Humanities, literature, languages",
    templates={
        "article-journal": "<{authors}. ><“{title}.” ><{container|i}, ><{t:vol} {volume}, ><{t:no} {issue}, >"
                           "<{year}, ><{pages_label} {pages}, ><{link}>.",
        "book": "<{authors}. ><{title|i}. ><{edition}, ><{publisher}, ><{year}>.",
        "chapter": "<{authors}. ><“{title}.” ><{container|i}, ><{t:edited_by} {editors}, ><{publisher}, >"
                   "<{year}, ><{pages_label} {pages}>.",
        "webpage": "<{authors}. ><“{title}.” ><{container|i}, ><{year}, ><{url}>. <{t:Accessed} {accessed}.>",
    },
    names=NameConfig(first="family_comma_given", rest="given_family", and_two=", {and} ",
                     and_last=", {and} ", etal_max=2, etal_show=1, etal_delim=", "),
    editor_names=GIVEN_FIRST_EDITORS,
    cite_year_sep=" ", cite_loc_sep=" ", locator_strip_label=True, cite_etal_min=3,
    bib_sort="author", bib_label="", bib_title_term="works_cited", accessed_format="dmy_abbr",
    aliases=["mla9"]))

register(Style(
    id="asa", name="ASA (American Sociological Association)", kind="author-date", discipline="Sociology",
    templates={
        "article-journal": "<{authors}. ><{year}. ><“{title}.” ><{container|i}>< {volume}><({issue})>"
                           "<:{pages}>.< {link}.>",
        "book": "<{authors}. ><{year}. ><{title|i}. ><{edition}. ><{place_publisher}>.",
        "chapter": "<{authors}. ><{year}. ><“{title}.” ><Pp. {pages} >{t:in} <{container|i}>"
                   "<, {t:edited_by} {editors}>. <{place_publisher}>.",
        "webpage": "<{authors}. ><{year}. ><“{title}.” ><{container}. ><{t:Retrieved} {accessed} ><({url})>.",
    },
    names=CHICAGO_NAMES, editor_names=GIVEN_FIRST_EDITORS,
    cite_year_sep=" ", cite_loc_sep=":", locator_strip_label=True, cite_etal_min=3,
    bib_sort="author", bib_label="", accessed_format="mdy"))

register(STYLES["vancouver"].derive(
    id="cse-ny", name="CSE (name-year)", kind="author-date", discipline="Biology, life sciences",
    templates={
        "article-journal": "<{authors}. ><{year}. ><{title}. ><{container_short}. ><{volume}><({issue})>"
                           "<:{pages}>.< doi:{doi_raw}.>",
        "book": "<{authors}. ><{year}. ><{title}. ><{edition}. ><{place_publisher}>.",
        "chapter": "<{authors}. ><{year}. ><{title}. >{t:In}: <{editors}, {ed_long}. ><{container}. >"
                   "<{place_publisher}>.< {t:page} {pages}.>",
        "webpage": "<{authors}. ><{year}. ><{title} {t:internet}. ><{container}; ><[{t:cited} {accessed}]. >"
                   "<{url}>",
    },
    names=replace(VANC_NAMES, etal_max=10, etal_show=10), page_range="full", page_delim="–",
    cite_open="(", cite_close=")", cite_year_sep=" ", bib_sort="author", bib_label=""))

register(Style(
    id="abnt", name="ABNT NBR 6023", kind="author-date", discipline="Brazilian/Portuguese academia",
    templates={
        "article-journal": "<{authors}. ><{title}. ><{container|b}, ><{place}, ><v. {volume}, ><n. {issue}, >"
                           "<p. {pages}, ><{year}>.< DOI: {doi_raw}.>",
        "book": "<{authors}. ><{title|b}. ><{edition}. ><{place_publisher}, ><{year}>.",
        "chapter": "<{authors}. ><{title}. >{t:In}: <{editors} ({ed_short}). ><{container|b}. ><{place_publisher}, ><{year}. ><p. {pages}>.",
        "webpage": "<{authors}. ><{title}. ><{container}, ><{year}. ><{t:Available_at} {url}. >"
                   "<{t:Accessed} {accessed}.>",
    },
    names=NameConfig(first="family_comma_initials", upper=True, delim="; ", and_two="; ", and_last="; ",
                     etal_max=3, etal_show=1, etal_delim=" "),
    cite_upper=True, cite_and="; ", cite_etal_min=4, page_delim="-", bib_sort="author", bib_label="",
    hanging_indent=False, accessed_format="dmy_abbr"))

register(STYLES["iso690-numeric"].derive(
    id="iso690-author-date", name="ISO 690 (author-date)", kind="author-date",
    templates={
        "article-journal": "<{authors}, ><{year}. ><{title}. ><{container|i}. ><{t:vol} {volume}, >"
                           "<{t:no} {issue}, ><{pages_label} {pages}>.< DOI {doi_raw}.>",
        "book": "<{authors}, ><{year}. ><{title|i}. ><{edition}. ><{place_publisher}>.< ISBN {isbn}.>",
        "chapter": "<{authors}, ><{year}. ><{title}. >{t:In}: <{editors}, {ed_short}. ><{container|i}. >"
                   "<{place_publisher}, ><{pages_label} {pages}>.",
        "webpage": "<{authors}, ><{year}. ><{title|i} [{t:online}]. ><{container}. ><[{t:Accessed} {accessed}]. >"
                   "<{t:Available_from} {url}>",
    },
    cite_open="(", cite_close=")", cite_year_sep=" ", bib_sort="author", bib_label="", aliases=[]))
