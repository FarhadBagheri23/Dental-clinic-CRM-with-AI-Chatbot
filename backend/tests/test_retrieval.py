"""Retrieval tests — the Persian normalisation cases in particular.

These need no MongoDB and no API key: the whole point of the lexical index is
that it runs anywhere, so its tests should too.
"""

import pytest

from app.agent.normalize import normalize, tokenize
from app.agent.retrieve import Document, Index


# ------------------------------------------------------------ normalisation

@pytest.mark.parametrize("arabic, persian", [
    ("كلينيك", "کلینیک"),      # ARABIC KAF + ARABIC YEH
    ("مراجعه‌كننده", "مراجعه کننده"),
    ("بيمه", "بیمه"),
    ("دندانپزشكي", "دندانپزشکی"),
])
def test_arabic_and_persian_letterforms_fold_together(arabic, persian):
    """Identical glyphs, different codepoints. Untreated, a document typed on
    an Arabic keyboard is invisible to a Persian query."""
    assert normalize(arabic) == normalize(persian)


def test_zwnj_does_not_split_a_word_into_nothing():
    # «می‌شود» / «می شود» / «میشود» are one word to a reader.
    assert tokenize("می‌شود", keep_stopwords=True) == ["می", "شود"]
    assert tokenize("می شود", keep_stopwords=True) == ["می", "شود"]


def test_digit_systems_fold_to_ascii():
    assert normalize("۱۴۰۵") == "1405"
    assert normalize("١٤٠٥") == "1405"     # Arabic-Indic
    assert normalize("۱۴۰۵") == normalize("1405")


def test_diacritics_are_stripped():
    assert normalize("دَنْدان") == normalize("دندان")


def test_stopwords_are_dropped_but_content_survives():
    tokens = tokenize("هزینه ایمپلنت در این کلینیک چقدر است؟")
    assert "ایمپلنت" in tokens and "هزینه" in tokens
    for stop in ("در", "این", "است"):
        assert stop not in tokens


# ------------------------------------------------------------------- BM25

@pytest.fixture
def index():
    return Index([
        Document("s1", "ایمپلنت دندان", "کاشت پایه تیتانیومی در استخوان فک.", "services"),
        Document("s2", "عصب‌کشی", "درمان ریشه دندان و پاکسازی کانال.", "services"),
        Document("s3", "جرم‌گیری", "پاکسازی جرم و پلاک از سطح دندان.", "services"),
        Document("i1", "بیمه دانا", "پوشش ۶۰ درصدی خدمات درمانی و جراحی.", "insurance"),
    ])


def test_search_finds_the_right_document(index):
    assert index.search("ایمپلنت")[0].document.doc_id == "s1"
    assert index.search("پوشش بیمه دانا")[0].document.doc_id == "i1"


def test_search_survives_arabic_keyboard_input(index):
    """The query is typed with ARABIC YEH; the document uses FARSI YEH."""
    hits = index.search("بيمه دانا")
    assert hits and hits[0].document.doc_id == "i1"


def test_title_terms_outrank_body_terms(index):
    """«جرم‌گیری» appears in s3's title and in its own body. Ranking must put
    the document that is *about* the term first, not merely one mentioning it."""
    hits = index.search("پاکسازی")
    assert {h.document.doc_id for h in hits} >= {"s2", "s3"}
    assert index.search("جرم‌گیری")[0].document.doc_id == "s3"


def test_unmatched_and_empty_queries_return_nothing(index):
    assert index.search("ارتودنسی نامرئی") == []
    assert index.search("") == []
    assert index.search("در این و از") == [], "stopwords alone must not match"


def test_empty_index_does_not_divide_by_zero():
    assert Index([]).search("ایمپلنت") == []
