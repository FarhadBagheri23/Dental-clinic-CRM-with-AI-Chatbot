"""Persian text normalisation for retrieval.

Persian is where naive retrieval quietly fails, and none of the reasons are
visible when reading the text back:

* «کلینیک» typed on an Arabic keyboard uses ARABIC KAF (U+0643), not PERSIAN
  KEHEH (U+06A9). Different codepoints, identical glyph.
* Likewise ARABIC YEH (U+064A) vs FARSI YEH (U+06CC).
* «می‌شود» carries a ZERO WIDTH NON-JOINER; «می شود» and «میشود» are the same
  word to a reader and three different tokens to a tokeniser.
* Persian digits ۰-۹, Arabic-Indic ٠-٩ and ASCII 0-9 all mean the same number.
* Diacritics (ـَـِـُ) are usually absent but occasionally typed.

Every one of these turns a document the user asked for into a document the
retriever cannot find. Normalising both sides of the comparison fixes it.
"""

import re
import unicodedata

# Characters that differ by codepoint but not by meaning.
_CHAR_MAP = str.maketrans({
    "ك": "ک",  # ARABIC KAF      -> KEHEH
    "ي": "ی",  # ARABIC YEH      -> FARSI YEH
    "ى": "ی",  # ALEF MAKSURA    -> FARSI YEH
    "ة": "ه",  # TEH MARBUTA     -> HEH
    "أ": "ا",  # ALEF WITH HAMZA ABOVE -> ALEF
    "إ": "ا",  # ALEF WITH HAMZA BELOW -> ALEF
    "آ": "ا",  # ALEF WITH MADDA -> ALEF
    "ؤ": "و",  # WAW WITH HAMZA  -> WAW
    "ئ": "ی",  # YEH WITH HAMZA  -> FARSI YEH
    "‌": " ",       # ZWNJ            -> space (splits می‌شود into می شود)
    "‏": "",        # RTL mark
    "‎": "",        # LTR mark
})

# Harakat and tatweel carry no lexical meaning here.
_STRIP = re.compile(r"[ً-ْٰـ]")

# Persian ۰-۹ (U+06F0) and Arabic-Indic ٠-٩ (U+0660) both fold to ASCII.
_DIGITS = {**{chr(0x06F0 + i): str(i) for i in range(10)},
           **{chr(0x0660 + i): str(i) for i in range(10)}}
_DIGIT_MAP = str.maketrans(_DIGITS)

_TOKEN = re.compile(r"[0-9a-z؀-ۿ]+")

# Function words that match everything and therefore discriminate nothing.
STOPWORDS = frozenset("""
از به با در بر که را این آن های ها یک و یا هم تا بی برای می نمی است بود شد
شده کرد کردن می‌شود چه چند چطور چگونه کدام کجا کی آیا هر همه بعضی خیلی
دارد دارند داشت باشد باشند شود شوند ما شما آنها او وی من تو نیز اما ولی
اگر پس چون زیرا یعنی مثل مانند روی زیر بالا پایین بین طی هنگام وقتی
""".split())


def normalize(text: str) -> str:
    """Fold the variations above into one canonical form."""
    if not text:
        return ""
    # NFKC first: it already collapses presentation forms and compatibility
    # ligatures, so the explicit map below only handles what it leaves alone.
    text = unicodedata.normalize("NFKC", str(text))
    text = text.translate(_CHAR_MAP).translate(_DIGIT_MAP)
    text = _STRIP.sub("", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    """Normalised tokens, stopwords dropped unless asked otherwise."""
    tokens = _TOKEN.findall(normalize(text))
    if keep_stopwords:
        return tokens
    return [t for t in tokens if t not in STOPWORDS]
