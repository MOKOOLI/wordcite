"""Resolve DOIs to references through doi.org content negotiation (needs internet)."""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Optional

from .models import Reference
from .parsers.csljson import item_to_reference

_DOI_RE = re.compile(r"^(doi:)?10\.\d{4,9}/\S+$", re.I)


def looks_like_doi(key: str) -> bool:
    return bool(_DOI_RE.match(key.strip()))


def normalise_doi(doi: str) -> str:
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi.strip(), flags=re.I)


@lru_cache(maxsize=512)
def fetch_doi(doi: str, timeout: float = 20.0) -> Reference:
    doi = normalise_doi(doi)
    url = "https://doi.org/" + urllib.parse.quote(doi, safe="/:;()._-")
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.citationstyles.csl+json",
        "User-Agent": "wordcite (https://github.com/)",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    ref = item_to_reference(data)
    ref.id = doi
    return ref


def resolve_doi(key: str) -> Optional[Reference]:
    try:
        return fetch_doi(normalise_doi(key))
    except Exception:   # network errors, 404s: leave the citation unresolved
        return None
