"""Localised terms. English and Persian (fa) are built in."""
from __future__ import annotations

from typing import Dict

EN: Dict[str, str] = {
    "and": "and", "amp": "&", "et_al": "et al.",
    "editor": "editor", "editors": "editors",
    "editor_short": "ed.", "editors_short": "eds.",
    "edition": "ed.", "in": "in", "vol": "vol.", "no": "no.",
    "page": "p.", "pages": "pp.",
    "available_at": "available at:", "available_from": "available from:", "available": "available",
    "accessed": "accessed", "cited": "cited", "retrieved": "retrieved", "retrieved_from": "Retrieved from ",
    "nd": "n.d.", "references": "References", "works_cited": "Works Cited", "bibliography": "Bibliography",
    "online": "online", "internet": "[Internet]", "thesis": "PhD thesis", "edited_by": "edited by",
    "report": "report",
}

FA: Dict[str, str] = {
    "and": "و", "amp": "و", "et_al": "و همکاران",
    "editor": "ویراستار", "editors": "ویراستاران",
    "editor_short": "ویراستار", "editors_short": "ویراستاران",
    "edition": "ویرایش", "in": "در", "vol": "ج.", "no": "ش.",
    "page": "ص.", "pages": "صص.",
    "available_at": "قابل دسترس در:", "available_from": "قابل دسترس از:", "available": "قابل دسترس",
    "accessed": "تاریخ دسترسی", "cited": "تاریخ دسترسی", "retrieved": "بازیابی‌شده در",
    "retrieved_from": "بازیابی‌شده از ",
    "nd": "بی‌تا", "references": "منابع", "works_cited": "منابع", "bibliography": "کتابنامه",
    "online": "برخط", "internet": "[اینترنت]", "thesis": "رساله دکتری", "edited_by": "به کوشش",
    "report": "گزارش",
}

LOCALES = {"en": EN, "fa": FA}

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "fa": ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن", "ژوئیه",
           "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"],
}
MONTHS_ABBR_DOT = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.",
                   "Aug.", "Sep.", "Oct.", "Nov.", "Dec."]
MONTHS_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
               "Aug", "Sep", "Oct", "Nov", "Dec"]

FA_ORDINALS = {2: "دوم", 3: "سوم", 4: "چهارم", 5: "پنجم", 6: "ششم", 7: "هفتم",
               8: "هشتم", 9: "نهم", 10: "دهم"}

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_persian_digits(text: str) -> str:
    return text.translate(_FA_DIGITS)


def get_terms(locale: str) -> Dict[str, str]:
    return dict(LOCALES.get(locale, EN))
