from wordcite.models import Name
from wordcite.parsers import parse_bibtex, parse_csl_json, parse_ris


def test_bibtex_strings_accents_and_literals():
    refs = parse_bibtex(r'''
@string{nm = "Nature"}
@article{k1, author = {M\"{u}ller, J{\"o}rg and {World Health Organization}},
  title = {On {DNA}}, journal = nm # " Medicine", year = 2020, month = mar, pages = {1--9}}
''')
    r = refs[0]
    assert r.authors[0].family == "Müller" and r.authors[0].given == "Jörg"
    assert r.authors[1].literal == "World Health Organization"
    assert r.container == "Nature Medicine" and r.month == "3" and r.pages == "1-9"
    assert r.title == "On DNA"


def test_name_parsing():
    assert Name.parse("Ludwig van Beethoven").particle == "van"
    n = Name.parse("King, Jr, Martin Luther")
    assert (n.family, n.suffix, n.given) == ("King", "Jr", "Martin Luther")
    assert Name.parse("Jane Doe").family == "Doe"


def test_csl_json():
    refs = parse_csl_json('''[{"id": "a", "type": "article-journal", "title": "T",
        "author": [{"family": "Doe", "given": "Jane"}], "container-title": "J",
        "issued": {"date-parts": [[2019, 4]]}, "DOI": "10.1/x", "page": "3-4"}]''')
    r = refs[0]
    assert (r.year, r.month, r.doi, r.authors[0].family) == ("2019", "4", "10.1/x", "Doe")


def test_ris():
    refs = parse_ris("""TY  - JOUR
AU  - Doe, Jane
AU  - Roe, Rick
TI  - A title
JO  - Journal
PY  - 2018/05/01
SP  - 10
EP  - 20
ER  -
""")
    r = refs[0]
    assert r.id == "doe2018" and r.pages == "10-20" and len(r.authors) == 2
