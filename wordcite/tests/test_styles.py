from pathlib import Path

import pytest

from wordcite import CitationEngine, CiteItem, Cluster, list_styles, load_references

LIB = load_references(Path(__file__).resolve().parents[1] / "examples" / "references.bib")


def engine(style, keys=None):
    e = CitationEngine(LIB, style)
    for k in keys or list(LIB):
        e.register(Cluster([CiteItem(k)]))
    e.finalize()
    return e


def entry(style, key):
    e = engine(style)
    return next(b for b in e.bibliography() if b.key == key)


def test_at_least_20_styles():
    assert len(list_styles()) >= 20


@pytest.mark.parametrize("style", [s.id for s in list_styles()])
def test_every_style_renders_every_reference(style):
    e = engine(style)
    entries = e.bibliography()
    assert len(entries) == len(LIB)
    for b in entries:
        text = b.text.plain
        assert text, f"{style}/{b.key} is empty"
        assert "{" not in text and "}" not in text
        assert ".." not in text.replace("…", ""), text
        assert " ," not in text and "( )" not in text and "()" not in text, text
    assert e.format_cluster(Cluster([CiteItem("smith2020"), CiteItem("garcia2021")])).plain


def test_apa_article():
    assert entry("apa", "smith2020").text.plain == (
        "Smith, J. A., & Jones, B. (2020b). Machine learning for early sepsis detection. "
        "Journal of Medical Informatics, 12(3), 123–129. https://doi.org/10.1000/jmi.2020.123")


def test_apa_italics():
    segs = entry("apa", "smith2020").text.segs
    italic = [s.text for s in segs if "i" in s.fmt]
    assert italic == ["Journal of Medical Informatics", "12"]


def test_vancouver_article():
    assert entry("vancouver", "smith2020").text.plain == (
        "Smith JA, Jones B. Machine learning for early sepsis detection. J Med Inform. "
        "2020 Mar;12(3):123-9. doi:10.1000/jmi.2020.123")


def test_ieee_article():
    assert entry("ieee", "garcia2021").text.plain == (
        "M. García, W. Chen, N. Okafor, and P. Novak, “Transformer models in clinical text mining: "
        "a systematic review,” Nature Medicine, vol. 27, pp. 1043–1051, 2021, doi: 10.1038/s41591-021-0001.")


def test_harvard_book():
    assert entry("harvard", "kahneman2011").text.plain == (
        "Kahneman, D. (2011) Thinking, Fast and Slow. 2nd edn. New York: Farrar, Straus and Giroux.")


def test_chicago_chapter():
    assert entry("chicago", "brown2019").text.plain == (
        "Brown, Alice. 2019. “Ethics of artificial intelligence in medicine.” In Handbook of Digital Health, "
        "edited by Robert White and Sara Green, 45–67. Cham: Springer.")


def test_numeric_compression():
    e = engine("vancouver")
    c = Cluster([CiteItem(k) for k in ["smith2020", "smith2020b", "garcia2021", "brown2019"]])
    assert e.format_cluster(c).plain == "[1–3,5]"


def test_author_date_disambiguation_and_collapse():
    e = engine("apa", ["smith2020", "smith2020b"])
    c = Cluster([CiteItem("smith2020"), CiteItem("smith2020b")])
    assert e.format_cluster(c).plain == "(Smith & Jones, 2020a, 2020b)" or \
        e.format_cluster(c).plain == "(Smith & Jones, 2020b, 2020a)"


def test_narrative_and_locator():
    e = engine("apa", ["garcia2021"])
    assert e.format_cluster(Cluster([CiteItem("garcia2021", locator="p. 5")], narrative=True)).plain == \
        "García et al. (2021, p. 5)"
    assert e.format_cluster(Cluster([CiteItem("garcia2021", locator="12")])).plain == \
        "(García et al., 2021, p. 12)"


def test_chicago_locator_strip():
    e = engine("chicago", ["kahneman2011"])
    assert e.format_cluster(Cluster([CiteItem("kahneman2011", locator="p. 33")])).plain == "(Kahneman 2011, 33)"


def test_superscript_style():
    e = engine("nature", ["smith2020"])
    r = e.format_cluster(Cluster([CiteItem("smith2020")]))
    assert r.plain == "1" and "sup" in r.segs[0].fmt


def test_missing_key_is_reported():
    e = CitationEngine(LIB, "apa")
    e.register(Cluster([CiteItem("nope")]))
    e.finalize()
    assert e.missing == ["nope"]
    assert "nope?" in e.format_cluster(Cluster([CiteItem("nope")])).plain


def test_persian_reference_uses_persian_terms():
    e = engine("apa", ["rezaei1399"])
    assert e.format_cluster(Cluster([CiteItem("rezaei1399")])).plain == "(رضایی و محمدی، 1399)"
    b = e.bibliography()[0]
    assert b.rtl and "ع." in b.text.plain


def test_persian_digits():
    e = CitationEngine(LIB, "apa", persian_digits=True)
    e.register(Cluster([CiteItem("rezaei1399")]))
    e.finalize()
    assert "۱۳۹۹" in e.format_cluster(Cluster([CiteItem("rezaei1399")])).plain


def test_author_date_cluster_sorted_alphabetically():
    e = engine("apa", ["smith2020", "kahneman2011"])
    c = Cluster([CiteItem("smith2020"), CiteItem("kahneman2011")])
    assert e.format_cluster(c).plain == "(Kahneman, 2011; Smith & Jones, 2020)"
