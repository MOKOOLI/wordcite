"""Data model for references and author names."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

_ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def has_arabic_script(text: str) -> bool:
    return bool(_ARABIC_SCRIPT.search(text or ""))


def _split_particle(last: str):
    words = last.split()
    particle = []
    while len(words) > 1 and words[0][:1].islower():
        particle.append(words.pop(0))
    return " ".join(particle), " ".join(words)


@dataclass
class Name:
    family: str = ""
    given: str = ""
    particle: str = ""   # "van", "de la", ...
    suffix: str = ""     # "Jr.", "III"
    literal: str = ""    # organisations: "World Health Organization"

    @classmethod
    def parse(cls, raw: str) -> "Name":
        """Parse "Family, Given", "Given Family", "von Family, Jr, Given" or "{Literal}"."""
        raw = (raw or "").strip()
        if not raw:
            return cls()
        if raw.startswith("{") and raw.endswith("}"):
            return cls(literal=raw[1:-1].strip())
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) >= 2:
            if len(parts) == 3:
                last, suffix, given = parts
            else:
                last, suffix, given = parts[0], "", ", ".join(parts[1:])
            particle, family = _split_particle(last)
            return cls(family=family, given=given, particle=particle, suffix=suffix)
        words = raw.split()
        if len(words) == 1:
            return cls(family=words[0])
        idx = None
        for i, w in enumerate(words[:-1]):
            if i > 0 and w[:1].islower():
                idx = i
                break
        if idx is not None:
            particle, family = _split_particle(" ".join(words[idx:]))
            return cls(family=family, given=" ".join(words[:idx]), particle=particle)
        return cls(family=words[-1], given=" ".join(words[:-1]))

    @property
    def full_family(self) -> str:
        return (self.literal or f"{self.particle} {self.family}").strip()

    def sort_key(self) -> str:
        return (self.literal or f"{self.family} {self.particle} {self.given}").casefold()

    def __str__(self) -> str:
        if self.literal:
            return self.literal
        return f"{self.full_family}, {self.given}".strip(", ")


@dataclass
class Reference:
    id: str
    type: str = "article-journal"   # CSL-like type names
    authors: List[Name] = field(default_factory=list)
    editors: List[Name] = field(default_factory=list)
    title: str = ""
    container: str = ""             # journal / book / proceedings / website
    container_short: str = ""       # journal abbreviation
    volume: str = ""
    issue: str = ""
    pages: str = ""
    year: str = ""
    month: str = ""                 # 1-12 as string
    day: str = ""
    publisher: str = ""
    place: str = ""
    edition: str = ""
    doi: str = ""
    url: str = ""
    accessed: str = ""              # ISO date: YYYY-MM-DD
    isbn: str = ""
    institution: str = ""
    genre: str = ""                 # "PhD thesis", "Technical report", ...
    event: str = ""
    number: str = ""                # report number
    language: str = ""
    note: str = ""

    @property
    def is_persian(self) -> bool:
        if self.language.lower() in ("fa", "fas", "per", "persian", "farsi"):
            return True
        sample = " ".join([self.title, self.container] + [str(a) for a in self.authors])
        return has_arabic_script(sample)

    def first_family(self) -> str:
        names = self.authors or self.editors
        return names[0].full_family if names else ""
