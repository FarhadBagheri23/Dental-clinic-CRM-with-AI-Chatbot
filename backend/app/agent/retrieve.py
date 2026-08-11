"""Lexical retrieval (BM25) over the clinic's unstructured text.

ponytail: no vector store, no embedding API, no numpy. The corpus is a few
hundred short Persian documents — service descriptions, insurance terms and
the flow specs. At that size BM25 is not a compromise:

* it runs with no API key and no network, so retrieval works before the LLM
  gateway is even configured, and costs nothing per query;
* nothing has to be re-embedded when a service price or description changes;
* clinic questions lean on exact nouns — «بیمه دانا», «ایمپلنت», «عصب‌کشی» —
  which is precisely where lexical matching beats semantic similarity.

Embeddings are the upgrade path if evaluation shows recall failing on
paraphrases; `search()` is the only seam that would change.
"""

import math
from dataclasses import dataclass, field

from app.agent.normalize import tokenize

# BM25 constants. k1 damps the payoff from repeating a term, b controls how
# hard long documents are penalised. These are the standard defaults and
# there is no tuning signal here that would justify moving them.
K1 = 1.5
B = 0.75


@dataclass
class Document:
    """One retrievable chunk, with the metadata an answer must cite."""
    doc_id: str
    title: str
    text: str
    source: str
    tokens: list[str] = field(default_factory=list, repr=False)

    def __post_init__(self):
        if not self.tokens:
            # Title terms carry more signal than body terms in short documents,
            # so they are counted twice rather than given a separate field.
            self.tokens = tokenize(self.title) * 2 + tokenize(self.text)


@dataclass
class Hit:
    document: Document
    score: float


class Index:
    """In-memory BM25 index. Rebuilt at startup; the corpus is small enough
    that incremental updates would be more machinery than they save."""

    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.avg_len = (
            sum(len(d.tokens) for d in documents) / len(documents) if documents else 0.0
        )
        # term -> {doc index: term frequency}
        self.postings: dict[str, dict[int, int]] = {}
        for i, doc in enumerate(documents):
            for token in doc.tokens:
                self.postings.setdefault(token, {}).setdefault(i, 0)
                self.postings[token][i] += 1

    def _idf(self, term: str) -> float:
        n = len(self.documents)
        df = len(self.postings.get(term, ()))
        if not df:
            return 0.0
        # BM25's probabilistic IDF, +1 inside the log so a term appearing in
        # every document scores ~0 instead of going negative.
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def search(self, query: str, limit: int = 5) -> list[Hit]:
        terms = tokenize(query)
        if not terms or not self.documents:
            return []

        scores: dict[int, float] = {}
        for term in terms:
            idf = self._idf(term)
            if not idf:
                continue
            for i, tf in self.postings[term].items():
                length_norm = 1 - B + B * (len(self.documents[i].tokens) / (self.avg_len or 1))
                scores[i] = scores.get(i, 0.0) + idf * (tf * (K1 + 1)) / (tf + K1 * length_norm)

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return [Hit(document=self.documents[i], score=round(s, 3)) for i, s in ranked]
