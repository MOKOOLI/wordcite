<div dir="rtl">

# wordcite · استناددهی خودکار در فایل‌های Word

فایل Word خودت رو بده، فهرست منابع (BibTeX / Zotero / EndNote) رو بده، اسم سبک رو بگو؛ wordcite همه‌ی ارجاع‌های داخل متن رو با فرمت درست جایگزین می‌کنه و فهرست منابع رو با شماره‌گذاری، ترتیب، ایتالیک و تورفتگی صحیح می‌سازه.

- **۲۷ سبک استناد**: ونکوور، هاروارد، APA 7 و 6، IEEE، MLA، شیکاگو، AMA، Nature، Science، ACS، ISO 690 و …
- **پشتیبانی کامل از فارسی**: منابع فارسی به‌طور خودکار تشخیص داده می‌شن («و همکاران»، «بی‌تا»، «ویرایش سوم»، ویرگول فارسی، گیومه « »، راست‌به‌چپ) و حتی ارقام فارسی
- ورودی منابع: **BibTeX** (`.bib`)، **CSL-JSON** (خروجی Zotero/Mendeley)، **RIS** (EndNote، Scopus، Web of Science)
- دریافت خودکار اطلاعات مقاله از روی **DOI**
- فرمت متن (فونت، اندازه، رنگ) حفظ می‌شه، حتی وقتی Word یک نشانه رو بین چند run شکسته
- بدون وابستگی سنگین: فقط `python-docx`

## نصب

```bash
git clone https://github.com/<your-user>/wordcite.git
cd wordcite
pip install -e .
```

## استفاده در ۳ قدم

**۱. توی Word، جای هر ارجاع یک نشانه بذار** (همون سینتکس Pandoc):

| می‌نویسی | APA | Vancouver |
|---|---|---|
| `[@smith2020]` | (Smith & Jones, 2020) | [1] |
| `[@smith2020, p. 33]` | (Smith & Jones, 2020, p. 33) | [1, p. 33] |
| `[@smith2020; @lee2022]` | (Lee & Park, 2022; Smith & Jones, 2020) (الفبایی) | [1,2] |
| `[see @smith2020]` | (see Smith & Jones, 2020) | [see 1] |
| `[-@smith2020]` | (2020) | [1] |
| `@smith2020` (روایی) | Smith and Jones (2020) | Smith and Jones [1] |
| `\cite{smith2020,lee2022}` | مثل بالا (سبک LaTeX) | |
| `[@10.1038/nature12373]` | با `--fetch-dois` از اینترنت گرفته می‌شه | |

جایی که فهرست منابع باید بیاد یک پاراگراف با `[[BIBLIOGRAPHY]]` (یا `[[منابع]]`) بنویس. اگه ننویسی، آخر سند اضافه می‌شه.

**۲. فایل منابع** رو آماده کن (مثلاً از Zotero: Export → BibTeX یا CSL JSON).

**۳. اجرا کن:**

```bash
wordcite process thesis.docx -b refs.bib -s vancouver -o thesis-vancouver.docx
wordcite process thesis.docx -b refs.bib -s apa          # خروجی: thesis.apa.docx
wordcite styles                                          # فهرست سبک‌ها
wordcite preview -b refs.bib -s harvard                  # پیش‌نمایش فهرست منابع در ترمینال
wordcite fetch-doi 10.1038/nature12373 --append refs.json
```

گزینه‌های مهم `process`:

| گزینه | کار |
|---|---|
| `-s / --style` | شناسه‌ی سبک (پیش‌فرض `apa`) |
| `-b / --bib` | یک یا چند فایل `.bib` / `.json` / `.ris` |
| `--locale auto\|en\|fa` | زبان اصطلاحات؛ `auto` = فارسی برای منابع فارسی |
| `--persian-digits` | ارقام فارسی (۱۳۹۹) در منابع فارسی |
| `--include-uncited` | منابعی که ارجاع نخورده‌اند هم در فهرست بیایند |
| `--bib-title "منابع"` | عنوان فهرست منابع (`""` = بدون عنوان) |
| `--title-case sentence` | تبدیل عنوان‌ها به sentence case (مثلاً برای APA) |
| `--fetch-dois` | کلیدهایی که DOI هستند از doi.org گرفته شوند |
| `--strict` | اگر کلیدی پیدا نشد با کد خطا خارج شود (برای CI) |

> نکته: فایل اصلی (با نشانه‌ها) رو نگه دار و هر بار از روی اون خروجی بگیر؛ این‌طوری با یک فرمان سبک رو عوض می‌کنی.

## استفاده در پایتون

```python
from wordcite import process_docx

report = process_docx("thesis.docx", "out.docx", "refs.bib", style="harvard", persian_digits=True)
print(report.summary())
print(report.missing)   # کلیدهایی که در فایل منابع نبودند
```

## سبک‌ها

| شناسه | سبک | نوع | حوزه |
|---|---|---|---|
| `vancouver` | Vancouver (ICMJE) | شماره‌ای | پزشکی، علوم سلامت |
| `nlm` | NLM / Citing Medicine | شماره‌ای | پزشکی |
| `ama` | AMA 11 | شماره‌ای | پزشکی (JAMA) |
| `bmj` | BMJ | شماره‌ای | پزشکی |
| `lancet` | The Lancet | شماره‌ای | پزشکی |
| `plos` | PLOS | شماره‌ای | علوم زیستی |
| `cse-cs` | CSE citation-sequence | شماره‌ای | زیست‌شناسی |
| `ieee` | IEEE | شماره‌ای | مهندسی، کامپیوتر |
| `acs` | ACS | شماره‌ای | شیمی |
| `rsc` | RSC | شماره‌ای | شیمی |
| `nature` | Nature | شماره‌ای | علوم |
| `science` | Science | شماره‌ای | علوم |
| `aip` | AIP | شماره‌ای | فیزیک |
| `aps` | APS (Physical Review) | شماره‌ای | فیزیک |
| `springer` | Springer Basic | شماره‌ای | چندرشته‌ای |
| `iso690-numeric` | ISO 690 (عددی) | شماره‌ای | استاندارد بین‌المللی |
| `harvard` | Harvard (Cite Them Right) | نویسنده-سال | عمومی |
| `harvard-elsevier` | Elsevier Harvard | نویسنده-سال | مجلات الزویر |
| `apa` | APA 7 | نویسنده-سال | روان‌شناسی، علوم تربیتی، علوم اجتماعی |
| `apa6` | APA 6 | نویسنده-سال | (برای دانشگاه‌هایی که هنوز ۶ می‌خواهند) |
| `chicago` | Chicago 17 author-date | نویسنده-سال | تاریخ، علوم اجتماعی |
| `turabian` | Turabian 9 | نویسنده-سال | پایان‌نامه‌ها |
| `asa` | ASA | نویسنده-سال | جامعه‌شناسی |
| `cse-ny` | CSE name-year | نویسنده-سال | زیست‌شناسی |
| `iso690-author-date` | ISO 690 (نویسنده-سال) | نویسنده-سال | استاندارد بین‌المللی |
| `abnt` | ABNT NBR 6023 | نویسنده-سال | برزیل/پرتغال |
| `mla` | MLA 9 | نویسنده-صفحه | ادبیات، علوم انسانی |

نمونه‌ی خروجی همه‌ی سبک‌ها: [docs/STYLES.md](docs/STYLES.md)

## ساختار پروژه

```
wordcite/
  models.py          Reference و Name
  parsers/           خواندن BibTeX، CSL-JSON، RIS
  styles.py          تعریف ۲۷ سبک (فقط داده + قالب)
  template.py        زبان قالب کوچک برای مدخل‌های فهرست منابع
  engine.py          شماره‌گذاری، ab/2020a، et al.، قالب‌بندی ارجاع و فهرست
  citations.py       پیدا کردن نشانه‌ها ([@key]، @key، \cite{})
  docx_processor.py  جراحی run های Word، درج فهرست، RTL
  formatting.py      نام‌ها، حروف اول، صفحات، تاریخ، ویرایش
  locales.py         اصطلاحات انگلیسی و فارسی
  doi.py             دریافت اطلاعات از doi.org
  cli.py             خط فرمان
tests/               تست‌ها (pytest)
examples/            references.bib نمونه، make_sample.py و خروجی‌های نمونه در output/
```

## اضافه کردن سبک جدید

سبک‌ها فقط داده‌اند. در `styles.py`:

```python
register(STYLES["vancouver"].derive(
    id="tums", name="دانشگاه علوم پزشکی تهران", superscript=True,
    cite_open="", cite_close="", bib_label="{n}-"))
```

یا یک `Style` کامل با قالب‌ها بساز. سینتکس قالب: `{var}` متغیر، `{var|i}` ایتالیک، `{var|b}` پررنگ، `{t:term}` اصطلاح محلی، و `<...>` گروهی که فقط وقتی همه‌ی متغیرهای داخلش مقدار دارند چاپ می‌شه. جزئیات در [CONTRIBUTING.md](CONTRIBUTING.md).

## محدودیت‌ها و نقشه‌ی راه

- [ ] ارجاع در پانویس‌ها (footnotes) و text box ها (فعلاً فقط بدنه و جدول‌ها)
- [ ] سبک‌های پانویسی (Chicago notes، OSCOLA، Bluebook)
- [ ] پشتیبانی از فایل‌های CSL (۱۰٬۰۰۰+ سبک) از طریق `citeproc-py`
- [ ] تبدیل فیلدهای Zotero/Mendeley داخل Word به نشانه
- [ ] تشخیص و بازنویسی فهرست منابعی که دستی تایپ شده
- [ ] رابط وب (Streamlit/FastAPI) برای کسانی که با خط فرمان راحت نیستند
- [ ] تاریخ شمسی برای تاریخ دسترسی منابع فارسی

</div>

---

## English

**wordcite** turns a Word draft with Pandoc-style markers (`[@key]`, `@key`, `\cite{key}`) into a finished document with formatted in-text citations and a bibliography, in any of 27 styles (Vancouver, Harvard, APA 7/6, IEEE, MLA, Chicago, AMA, Nature, Science, ACS, ISO 690, …). References come from BibTeX, CSL-JSON or RIS, and can be fetched by DOI. Persian references are detected automatically and get Persian terms, punctuation, quotes and right-to-left paragraphs.

```bash
pip install -e .
wordcite process draft.docx -b refs.bib -s ieee -o final.docx
pytest
```

MIT licensed. Contributions welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).
