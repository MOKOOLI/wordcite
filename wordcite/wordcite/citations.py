"""Finding citation markers in plain text.

Supported markers (Pandoc-compatible):
    [@smith2020]                    parenthetical      -> (Smith, 2020)  / [1]
    [@smith2020, p. 33; @lee2019]   several works, with locator
    [see @smith2020]                prefix text
    [-@smith2020]                   suppress author   -> (2020)
    @smith2020                      narrative          -> Smith (2020)  / Smith [1]
    @smith2020 [p. 33]              narrative + locator
    \\cite{smith2020,lee2019}        LaTeX style (also \\citep, \\citet = narrative)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Container, List

from .engine import CiteItem, Cluster

KEY = r"[\w][\w:.#$%&\-+?<>~/()]*[\w)]|[\w]"
CLUSTER_RE = re.compile(r"\[(?P<body>[^\[\]]*?-?@(?:" + KEY + r")[^\[\]]*)\]")
NARRATIVE_RE = re.compile(r"(?<![\w@.\-\[/])@(?P<key>" + KEY + r")(?:\s\[(?P<loc>[^\[\]@]+)\])?")
LATEX_RE = re.compile(r"\\cite(?P<kind>[pt]?)\{(?P<keys>[^{}]+)\}")
BIBLIOGRAPHY_RE = re.compile(
    r"^\s*(\[\[\s*(bibliography|references|منابع)\s*\]\]|\{\{\s*(bibliography|references|منابع)\s*\}\})\s*$",
    re.I)
ITEM_RE = re.compile(r"^(?P<prefix>.*?)(?P<suppress>-?)@(?P<key>" + KEY + r")(?P<rest>.*)$", re.S)


@dataclass
class Match:
    start: int
    end: int
    cluster: Cluster


def parse_cluster_body(body: str) -> Cluster:
    items = []
    for part in body.split(";"):
        m = ITEM_RE.match(part.strip())
        if not m:
            continue
        items.append(CiteItem(key=m.group("key"), locator=m.group("rest").strip().lstrip(",").strip(),
                              prefix=m.group("prefix").strip(), suppress_author=bool(m.group("suppress"))))
    return Cluster(items)


def find_citations(text: str, known_keys: Container[str]) -> List[Match]:
    matches: List[Match] = []
    taken = []

    def free(s, e):
        return all(e <= a or s >= b for a, b in taken)

    for m in CLUSTER_RE.finditer(text):
        cluster = parse_cluster_body(m.group("body"))
        if cluster.items:
            matches.append(Match(m.start(), m.end(), cluster))
            taken.append((m.start(), m.end()))
    for m in LATEX_RE.finditer(text):
        if not free(m.start(), m.end()):
            continue
        keys = [k.strip() for k in m.group("keys").split(",") if k.strip()]
        cluster = Cluster([CiteItem(k) for k in keys], narrative=m.group("kind") == "t")
        matches.append(Match(m.start(), m.end(), cluster))
        taken.append((m.start(), m.end()))
    for m in NARRATIVE_RE.finditer(text):
        key = m.group("key")
        while key and key not in known_keys and key[-1] in ".,:;?)":
            key = key[:-1]
        if key not in known_keys:
            continue
        end = m.start() + 1 + len(key)
        if m.group("loc") and key == m.group("key"):
            end = m.end()
        if not free(m.start(), end):
            continue
        loc = m.group("loc") if end == m.end() else ""
        matches.append(Match(m.start(), end, Cluster([CiteItem(key, locator=loc or "")], narrative=True)))
        taken.append((m.start(), end))
    matches.sort(key=lambda x: x.start)
    return matches
