"""Builds the retrievable corpus.

Only *unstructured* text goes in here. Numbers stay out: an invoice row
retrieved by keyword similarity and then summed by a language model is how a
chatbot reports ۴۲ میلیون for a ۱٫۲ میلیارد month. Anything countable is
answered by a tool in `app.agent.tools`, which runs the same aggregation the
dashboard runs.

So the corpus is: what a service *is*, what an insurer *covers*, and how a
front-desk procedure is meant to go.
"""

import logging
from pathlib import Path

from app.agent.retrieve import Document, Index

log = logging.getLogger(__name__)

# chatbot-flows/ lives at the repo root, beside backend/.
FLOWS_DIR = Path(__file__).resolve().parents[3] / "chatbot-flows"

# Markdown headings split the flow docs into chunks small enough that a
# retrieved passage is mostly relevant, without a sentence splitter.
_HEADING = "\n## "


async def build_corpus(db) -> list[Document]:
    services, insurers = await _load_reference(db)
    return [*services, *insurers, *_load_flows()]


async def _load_reference(db) -> tuple[list[Document], list[Document]]:
    services = [
        Document(
            doc_id=f"service:{s['service_id']}",
            title=s["name"],
            # Price and duration are included as prose because they answer
            # "how much is X" directly. Aggregates over them still go to tools.
            text=(f"دسته: {s.get('category', '')}. "
                  f"{s.get('description') or ''} "
                  f"مدت انجام: {s.get('duration_minutes', '')} دقیقه. "
                  f"تعرفه پایه: {s.get('base_price', '')} تومان."),
            source="services",
        )
        for s in await db.services.find({}, {"_id": 0}).to_list(None)
    ]
    insurers = [
        Document(
            doc_id=f"insurance:{i['insurance_id']}",
            title=i["company_name"],
            text=(f"شرکت بیمه طرف قرارداد کلینیک. "
                  f"درصد پوشش: {i.get('coverage_percentage', '')} درصد. "
                  f"شماره قرارداد: {i.get('policy_number', '')}."),
            source="insurance",
        )
        for i in await db.insurance.find({}, {"_id": 0}).to_list(None)
    ]
    return services, insurers


def _load_flows() -> list[Document]:
    """The five flow specs, chunked on their markdown headings."""
    if not FLOWS_DIR.is_dir():
        log.warning("chatbot-flows not found at %s — flow answers disabled", FLOWS_DIR)
        return []

    docs = []
    for path in sorted(FLOWS_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        head, *sections = raw.split(_HEADING)
        flow = path.stem
        title = head.lstrip("# ").splitlines()[0].strip() if head.strip() else flow
        docs.append(Document(f"flow:{flow}:0", title, head, "chatbot-flows"))
        for n, section in enumerate(sections, start=1):
            heading, _, body = section.partition("\n")
            docs.append(Document(
                doc_id=f"flow:{flow}:{n}",
                title=f"{title} — {heading.strip()}",
                text=body.strip(),
                source="chatbot-flows",
            ))
    return docs


async def build_index(db) -> Index:
    corpus = await build_corpus(db)
    log.info("retrieval corpus: %d documents", len(corpus))
    return Index(corpus)
