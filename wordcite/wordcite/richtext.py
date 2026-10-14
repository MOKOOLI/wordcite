"""Tiny rich-text model: a list of text segments with simple formatting flags.

Formatting flags: "i" (italic), "b" (bold), "sup" (superscript).
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Callable, FrozenSet, Iterable, List, Optional

ITALIC = "i"
BOLD = "b"
SUP = "sup"


@dataclass(frozen=True)
class Seg:
    text: str
    fmt: FrozenSet[str] = frozenset()


# Each rule deletes the span of capture group 1. Rules run until nothing changes.
_CLEANUP_RULES = [
    re.compile(r" ( +)"),                  # collapse runs of spaces
    re.compile(r"( )[,.;:]"),              # no space before punctuation
    re.compile(r"[.?!](\.)"),              # "..", "?." -> single mark
    re.compile(r"([,;:]\s*)\."),           # ", ." -> "."
    re.compile(r"(,\s*),"),                # ", ," -> ","
    re.compile(r"(\(\s*\))"),              # empty parentheses
    re.compile(r"(“\s*”)"),                # empty quotes
    re.compile(r"^(\s+)"),
    re.compile(r"(\s+)$"),
    re.compile(r"^([,.;:]\s*)"),
]


class RichText:
    def __init__(self, segs: Optional[Iterable[Seg]] = None):
        self.segs: List[Seg] = []
        for s in segs or []:
            self.append(s.text, s.fmt)

    # -- building ---------------------------------------------------------
    def append(self, text: str, fmt: Iterable[str] = ()) -> "RichText":
        if not text:
            return self
        fmt = frozenset(fmt)
        if self.segs and self.segs[-1].fmt == fmt:
            self.segs[-1] = Seg(self.segs[-1].text + text, fmt)
        else:
            self.segs.append(Seg(text, fmt))
        return self

    def extend(self, other: "RichText") -> "RichText":
        for s in other.segs:
            self.append(s.text, s.fmt)
        return self

    def copy(self) -> "RichText":
        return RichText(self.segs)

    def with_fmt(self, extra: Iterable[str]) -> "RichText":
        extra = frozenset(extra)
        return RichText(Seg(s.text, s.fmt | extra) for s in self.segs)

    def map_text(self, fn: Callable[[str], str]) -> "RichText":
        return RichText(Seg(fn(s.text), s.fmt) for s in self.segs)

    # -- inspection -------------------------------------------------------
    @property
    def plain(self) -> str:
        return "".join(s.text for s in self.segs)

    def __bool__(self) -> bool:
        return bool(self.plain)

    def __str__(self) -> str:
        return self.plain

    def __repr__(self) -> str:
        return f"RichText({self.to_markdown()!r})"

    # -- cleanup ----------------------------------------------------------
    def cleanup(self) -> "RichText":
        chars = [(c, s.fmt) for s in self.segs for c in s.text]
        while True:
            text = "".join(c for c, _ in chars)
            for rx in _CLEANUP_RULES:
                m = rx.search(text)
                if m and m.end(1) > m.start(1):
                    del chars[m.start(1):m.end(1)]
                    break
            else:
                break
        out = RichText()
        for c, f in chars:
            out.append(c, f)
        return out

    # -- export -----------------------------------------------------------
    def to_markdown(self) -> str:
        parts = []
        for s in self.segs:
            t = s.text
            if SUP in s.fmt:
                t = f"^{t}^"
            if BOLD in s.fmt:
                t = f"**{t}**"
            if ITALIC in s.fmt:
                t = f"*{t}*"
            parts.append(t)
        return "".join(parts)

    def to_html(self) -> str:
        parts = []
        for s in self.segs:
            t = html.escape(s.text)
            if SUP in s.fmt:
                t = f"<sup>{t}</sup>"
            if BOLD in s.fmt:
                t = f"<b>{t}</b>"
            if ITALIC in s.fmt:
                t = f"<i>{t}</i>"
            parts.append(t)
        return "".join(parts)
