# Contributing

```bash
pip install -e ".[dev]"
pytest -q
python scripts/gen_style_docs.py   # refresh docs/STYLES.md after changing a style
```

## How a style works

A `Style` (see `wordcite/styles.py`) is plain data:

| field | meaning |
|---|---|
| `kind` | `numeric`, `author-date` or `author-page` |
| `names` | a `NameConfig`: name format (`family_initials` → *Smith JA*, `family_comma_initials` → *Smith, J. A.*, `initials_family` → *J. A. Smith*, `family_comma_given`, `given_family`), separators, et al. rules |
| `cite_*` | in-text rules: brackets, separators, et al. threshold, superscript |
| `bib_sort` | `citation` (order of first citation) or `author` (alphabetical) |
| `bib_label` | numeric label, e.g. `"[{n}]"`, `"{n}."` |
| `templates` | one template per reference type |

Types: `article-journal`, `book`, `chapter`, `paper-conference`, `thesis`, `report`, `webpage`
(missing types fall back: conference → chapter → book, thesis/report → book).

## Template syntax

```
{var}       variable            {var|i} italic   {var|b} bold
{a+b}       non-empty values joined with ", "
{t:term}    localised term ({t:Term} = capitalised)
<...>       group, printed only when every variable directly inside has a value
```

Punctuation is cleaned automatically afterwards (`..`, `, .`, double spaces, empty brackets),
so templates can be written generously.

Variables: `authors editors ed_short Ed_short ed_long title container container_short volume issue
pages page_first pages_label year year_raw month month_abbr day publisher place place_publisher
publisher_place edition doi doi_raw doi_url url link accessed isbn genre institution event number`.

## Adding a style

1. Add it in `wordcite/styles.py` (start from the closest existing style with `.derive(...)`).
2. Add at least one exact-output test in `tests/test_styles.py`. The parametrised test already checks
   that every style renders every sample reference without leftovers.
3. Run `python scripts/gen_style_docs.py` and commit `docs/STYLES.md`.

## Adding a language

Add a term dictionary to `wordcite/locales.py` (copy `EN`), register it in `LOCALES`, and extend
`CitationEngine.ref_locale` with a detection rule.
