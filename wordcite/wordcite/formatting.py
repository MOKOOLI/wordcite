"""Low-level formatting helpers: names, initials, pages, dates, title case."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .locales import FA_ORDINALS, MONTHS, MONTHS_ABBR, MONTHS_ABBR_DOT
from .models import Name


@dataclass
class NameConfig:
    """How a list of names is written in the bibliography.

    Formats: family_initials ("Smith JA"), family_comma_initials ("Smith, J. A."),
    initials_family ("J. A. Smith"), family_comma_given ("Smith, John A."),
    given_family ("John A. Smith").
    """
    first: str = "family_comma_initials"
    rest: Optional[str] = None           # format for 2nd+ names (MLA/Chicago invert only the first)
    initial_dot: str = "."
    initial_space: str = " "
    upper: bool = False                  # SMITH (ISO 690, ABNT)
    delim: str = ", "
    and_two: str = " {and} "
    and_last: str = ", {and} "
    etal_max: Optional[int] = None       # truncate when there are more than etal_max names
    etal_show: int = 1
    etal_delim: str = ", "
    ellipsis_last: bool = False          # APA 7: first 19, …, last author


def initials(given: str, dot: str = ".", space: str = " ") -> str:
    out: List[str] = []
    for tok in re.split(r"[\s.]+", given.strip()):
        if not tok:
            continue
        if tok.isalpha() and tok.isupper() and len(tok) <= 3 and len(tok) > 1:
            out.extend(ch + dot for ch in tok)   # already initials, e.g. "JA"
            continue
        parts = [p for p in tok.split("-") if p]
        if not parts:
            continue
        out.append("-".join(p[0] + dot for p in parts))
    return space.join(out)


def format_name(n: Name, fmt: str, cfg: NameConfig) -> str:
    if n.literal:
        return n.literal
    fam = n.full_family
    if cfg.upper:
        fam = fam.upper()
    giv = n.given.strip()
    ini = initials(giv, cfg.initial_dot, cfg.initial_space) if giv else ""
    if fmt == "family_initials":
        s = f"{fam} {ini}".strip()
    elif fmt == "family_comma_initials":
        s = f"{fam}, {ini}" if ini else fam
    elif fmt == "initials_family":
        s = f"{ini} {fam}".strip()
    elif fmt == "family_comma_given":
        s = f"{fam}, {giv}" if giv else fam
    elif fmt == "given_family":
        s = f"{giv} {fam}".strip()
    else:
        raise ValueError(f"unknown name format: {fmt}")
    if n.suffix:
        s += (" " if fmt == "family_initials" else ", ") + n.suffix
    return s


def format_names(names: List[Name], cfg: NameConfig, terms: Dict[str, str]) -> str:
    if not names:
        return ""

    def fmt(i: int, n: Name) -> str:
        style = cfg.first if i == 0 or not cfg.rest else cfg.rest
        return format_name(n, style, cfg)

    def term(s: str) -> str:
        return s.replace("{and}", terms["and"]).replace("{amp}", terms["amp"])

    total = len(names)
    if cfg.etal_max and total > cfg.etal_max:
        shown = [fmt(i, n) for i, n in enumerate(names[: cfg.etal_show])]
        if cfg.ellipsis_last:
            return cfg.delim.join(shown) + ", … " + fmt(total - 1, names[-1])
        return cfg.delim.join(shown) + cfg.etal_delim + terms["et_al"]
    parts = [fmt(i, n) for i, n in enumerate(names)]
    if total == 1:
        return parts[0]
    if total == 2:
        return parts[0] + term(cfg.and_two) + parts[1]
    return cfg.delim.join(parts[:-1]) + term(cfg.and_last) + parts[-1]


# --------------------------------------------------------------------------- pages
def format_pages(pages: str, mode: str = "full", delim: str = "–") -> str:
    p = re.sub(r"\s*(--|—|–|-)\s*", "-", (pages or "").strip())
    if not p:
        return ""
    m = re.match(r"^([A-Za-z]*)(\d+)-([A-Za-z]*)(\d+)$", p)
    if not m:
        return p.replace("-", delim)
    pre1, a, pre2, b = m.groups()
    if mode == "first":
        return pre1 + a
    if mode == "minimal" and len(a) == len(b):
        i = 0
        while i < len(b) - 1 and a[i] == b[i]:
            i += 1
        b = b[i:]
    return f"{pre1}{a}{delim}{pre2}{b}"


def first_page(pages: str) -> str:
    return format_pages(pages, "first")


def is_page_range(pages: str) -> bool:
    return bool(re.search(r"\d\s*(--|—|–|-|,)\s*\w", pages or ""))


# --------------------------------------------------------------------------- dates
def parse_date(value: str):
    m = re.match(r"^\s*(\d{3,4})(?:[-/](\d{1,2}))?(?:[-/](\d{1,2}))?", value or "")
    if not m:
        return None
    y, mo, d = m.groups()
    return int(y), int(mo) if mo else None, int(d) if d else None


def month_name(month: str, locale: str = "en", abbr: bool = False, dots: bool = True) -> str:
    try:
        i = int(month) - 1
    except (TypeError, ValueError):
        return month or ""
    if not 0 <= i < 12:
        return ""
    if locale == "fa":
        return MONTHS["fa"][i]
    if abbr:
        return (MONTHS_ABBR_DOT if dots else MONTHS_ABBR)[i]
    return MONTHS["en"][i]


def format_date(value: str, fmt: str, locale: str = "en") -> str:
    parsed = parse_date(value)
    if not parsed:
        return value or ""
    y, mo, d = parsed
    if locale == "fa":
        bits = [str(d) if d else "", month_name(str(mo), "fa") if mo else "", str(y)]
        return " ".join(b for b in bits if b)
    full = month_name(str(mo)) if mo else ""
    ab_dot = month_name(str(mo), abbr=True, dots=True) if mo else ""
    ab = month_name(str(mo), abbr=True, dots=False) if mo else ""
    if fmt == "iso":
        return "-".join(x for x in [f"{y:04d}", f"{mo:02d}" if mo else "", f"{d:02d}" if d else ""] if x)
    if fmt == "dmy":
        return " ".join(str(x) for x in [d, full, y] if x)
    if fmt == "dmy_abbr":
        return " ".join(str(x) for x in [d, ab_dot, y] if x)
    if fmt == "mdy":
        return f"{full} {d}, {y}" if d else " ".join(str(x) for x in [full, y] if x)
    if fmt == "mdy_abbr":
        return f"{ab_dot} {d}, {y}" if d else " ".join(str(x) for x in [ab_dot, y] if x)
    if fmt == "ymd_abbr":
        return " ".join(str(x) for x in [y, ab, d] if x)
    raise ValueError(f"unknown date format: {fmt}")


# --------------------------------------------------------------------------- editions
def ordinal_en(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def edition_phrase(edition: str, terms: Dict[str, str], locale: str) -> str:
    ed = (edition or "").strip()
    if not ed:
        return ""
    m = re.match(r"^(\d+)", ed)
    if m:
        n = int(m.group(1))
        if n <= 1:
            return ""
        if locale == "fa":
            return f"{terms['edition']} {FA_ORDINALS.get(n, str(n) + 'م')}"
        return f"{ordinal_en(n)} {terms['edition']}"
    return f"{ed} {terms['edition']}" if locale != "fa" else f"{terms['edition']} {ed}"


# --------------------------------------------------------------------------- title case
_SMALL = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "by",
          "of", "in", "with", "as", "via", "vs", "from", "into", "over"}


def _protected(word: str) -> bool:
    core = re.sub(r"^\W+|\W+$", "", word)
    return any(c.isdigit() for c in core) or any(c.isupper() for c in core[1:])


def sentence_case(title: str) -> str:
    words = title.split(" ")
    out = []
    cap_next = True
    for w in words:
        if not w:
            out.append(w)
            continue
        if _protected(w):
            out.append(w)
        elif cap_next:
            out.append(w[:1].upper() + w[1:].lower())
        else:
            out.append(w.lower())
        cap_next = w.endswith((":", "?", "!", "."))
    return " ".join(out)


def title_case(title: str) -> str:
    words = title.split(" ")
    out = []
    for i, w in enumerate(words):
        if not w or _protected(w):
            out.append(w)
            continue
        first_or_last = i == 0 or i == len(words) - 1 or words[i - 1].endswith(":")
        if w.lower() in _SMALL and not first_or_last:
            out.append(w.lower())
        else:
            out.append("-".join(p[:1].upper() + p[1:] for p in w.split("-")))
    return " ".join(out)


def apply_case(title: str, mode: str) -> str:
    if not title or mode in (None, "", "as-is"):
        return title or ""
    if mode == "sentence":
        return sentence_case(title)
    if mode == "title":
        return title_case(title)
    raise ValueError(f"unknown title case mode: {mode}")
