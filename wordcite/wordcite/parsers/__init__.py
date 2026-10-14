"""Readers for reference libraries: BibTeX (.bib), CSL-JSON (.json) and RIS (.ris)."""
from __future__ import annotations

import os
from typing import Dict, Iterable, List, Union

from ..models import Reference
from .bibtex import parse_bibtex
from .csljson import parse_csl_json
from .ris import parse_ris

__all__ = ["load_references", "parse_bibtex", "parse_csl_json", "parse_ris"]

PathLike = Union[str, "os.PathLike[str]"]


def _parse_file(path: str) -> List[Reference]:
    ext = os.path.splitext(path)[1].lower()
    with open(path, encoding="utf-8-sig") as fh:
        text = fh.read()
    if ext in (".bib", ".bibtex"):
        return parse_bibtex(text)
    if ext in (".json", ".csljson"):
        return parse_csl_json(text)
    if ext in (".ris", ".txt"):
        return parse_ris(text)
    raise ValueError(f"Unsupported reference file: {path} (use .bib, .json or .ris)")


def load_references(sources: Union[PathLike, Iterable, Dict[str, Reference]]) -> Dict[str, Reference]:
    """Load one or more reference files (or pass through Reference objects) into a dict by key."""
    if isinstance(sources, dict):
        return dict(sources)
    if isinstance(sources, (str, os.PathLike)):
        sources = [sources]
    library: Dict[str, Reference] = {}
    for src in sources:
        refs = [src] if isinstance(src, Reference) else _parse_file(os.fspath(src))
        for ref in refs:
            library[ref.id] = ref
    return library
