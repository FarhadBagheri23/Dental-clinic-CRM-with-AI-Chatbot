# Business Intelligence Dashboard With AI Chatbot

**Farhad Bagheri Taheri — Sharif University of Technology, International Campus**

A management dashboard for a dental clinic: seven analytical pages in Persian
and RTL, on MongoDB, with an AI assistant that reads its numbers from the same
reports the dashboard renders.

> The data is **synthetic** — generated with `Faker("fa_IR")` and a fixed
> seed of 42.

---

## What the dashboard shows

| Page | The question it answers |
|---|---|
| **Overview** | Revenue, collections, receivables, appointments, and the 12-month trend |
| **Revenue & Services** | Which service actually makes money — revenue per chair-hour, not gross revenue |
| **Dentist Performance** | Revenue, commission, the clinic's net share, revenue per chair-hour, cancellation and no-show rates |
| **Operations** | Cancellation and no-show rates, weekday × hour heatmap, chair utilisation, the cost of a lost slot in tomans |
| **Treatment Plans & Recall** | Case acceptance, treatment accepted but never delivered, the call list for lapsed patients |
| **Finance & Inventory** | The billed → insurance → collected chain, payment methods, material cost, stock levels |
| **Profitability & Receivables** | Gross margin per service, cost structure, hidden discount, A/R ageing and DSO |

Three record pages as well — patients, appointments and invoices — with search
and pagination.

---

## Metrics computed unconventionally, on purpose

- **Revenue per chair-hour** — ranking by gross revenue makes a cheap,
  high-volume service look like the star. Dividing by the chair time it
  consumes shows what actually earns from the clinic's capacity.

- **Gross margin per service** — revenue minus materials and commission. The
  table is sorted from worst margin to best, because the busiest service sits
  at the top of every revenue report and may well be the least profitable one.

- **Cohort collection rate** — payments are matched to the invoices issued in
  *the same window*. Dividing cash received by what was billed that month
  compares two different populations and produces collection rates above 100%.

- **Chair utilisation** — the denominator comes from `clinic_capacity`, not
  from "chairs × opening hours". The chairs are not staffed identical shifts.

- **DSO and A/R ageing** — a single outstanding total looks exactly the same
  whether every invoice is current or half of them are uncollectable.

---

## Filters

Five global filters: date range, dentist specialty, service category and
insurance company.

Some combinations are structurally impossible, and rather than approximate
them the affected chart says so beneath itself. A cancelled appointment never
produced a session, so it has no service and no category — applying the
category filter to a cancellation chart would delete exactly the rows the
chart exists to count.

---

## AI assistant

**It is a RAG system, but a hybrid one, and the split is the point.**

- **Retrieval (BM25)** answers prose questions — what a service is, what an
  insurer covers, how a front-desk procedure runs. The index is lexical, built
  in memory over service descriptions, insurance terms and the flow specs. No
  vector store and no embedding API: the corpus is a few hundred short Persian
  documents, nothing needs re-embedding when a price changes, and clinic
  questions lean on exact nouns — «بیمه دانا», «ایمپلنت» — which is where
  lexical matching beats semantic similarity.

- **Tool calls answer everything countable.** No figure is ever retrieved or
  computed by the model. Each one comes from the same repository function the
  dashboard renders, so any answer can be checked against the page it came
  from. Retrieving an invoice row by keyword similarity and letting a language
  model add it up is how a chatbot reports ۴۲ میلیون for a ۱٫۲ میلیارد month.

The assistant's scope is limited to the clinic and it declines anything else.
Without `AVALAI_API_KEY` the rest of the panel runs normally and only the chat
tab is disabled.

---

## Stack

| Layer | Technology |
|---|---|
| Data model | DBML (13 entities) |
| Data generation | Python 3.12 + Faker (fa_IR), fixed seed |
| Database | MongoDB 7 |
| API | FastAPI + Motor (async) |
| Panel | React 18 + Vite + Tailwind CSS + Vazirmatn |
| Assistant | BM25 retrieval + tool-calling over the same repositories (AvalAI gateway) |
| Public site | Next.js 14 |
| Deployment | Docker Compose + nginx |

```
├── data/                      13 CSV files (11,380 records)
├── scripts/generate_data.py   data generator
├── seeder/seed.py             CSV → MongoDB
├── backend/app/
│   ├── api/routers/           HTTP layer
│   ├── repositories/          aggregation pipelines — the source of every number
│   ├── agent/                 assistant: retrieval, tools, tool-calling loop
│   └── core/                  config, security, roles, rate limiting
├── frontend/src/pages/        7 dashboard pages + 3 record pages
└── website/                   public clinic site
```

---

## Running it

```bash
cp .env.example .env      # then change every value
docker compose up -d --build
```

Panel on http://localhost:8080, public site on http://localhost:3000.
