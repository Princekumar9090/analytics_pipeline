# CLAUDE.md — Order Events Analytics Pipeline

This file is auto-loaded by Claude Code at the start of every session in
this repo. It is the primer — don't re-explain project context in chat;
update this file instead when something changes.

## Project

Real-time order-events analytics pipeline. Built as a 20-day interview
prep project for a backend/data-engineering role. Full design rationale
lives in `ARCHITECTURE.md` — read it before touching unfamiliar parts of
the codebase. Every major "why" decision belongs in `DECISIONS.md`, not
scattered in code comments or chat history.

**Dataset:** Instacart Market Basket Analysis (Kaggle) — `orders`,
`order_products`, `products`, `aisles`, `departments`. ~3.4M orders,
~32M order-product rows. Event types (`order_placed`, `payment_processed`,
`order_cancelled`, `item_viewed`) are synthesized from these rows by the
replay producer — see `ARCHITECTURE.md` §3 and §7.

## Scope tiers — respect these, do not silently violate them

- **Tier 1 (build for real, protect this time above all else):** Kafka/Redpanda
  producer+consumer, PyFlink windowing/stateful/join operations, Postgres
  schema + advanced SQL, FastAPI REST, docker-compose, DSA practice.
- **Tier 2 (one real working slice, not a full build):** GraphQL resolvers
  w/ DataLoader, one PySpark batch job, one partitioned/clustered BigQuery
  table + load job, Cloud Run deploy of the API.
- **Tier 2b (optional practice, never blocks Tier 1):** C++ producer
  (`librdkafka`, multithreaded) — alternative implementation of the Python
  replay producer, for systems-level practice + a throughput comparison
  story. Salesforce Developer Edition as a second event source (polled
  Opportunity/Lead REST API → canonical event schema → second Kafka
  topic) — multi-source ingestion story. SAP explicitly rejected: no
  free-forever dev org, disproportionate time cost. Both Tier 2b items
  are first dropped if Tier 1 time is tight.
- **Tier 3 (conceptual only — do not implement):** Kubernetes,
  exactly-once semantics, multi-region, full IAM policy design, Pub/Sub
  and Dataflow migration.

Full tier definitions: `ARCHITECTURE.md` §0. If a task doesn't clearly map
to a tier, ask before building — don't default to building it fully.

## Repo structure

```
producer/       # event generator + replay producer, Kafka publish
producer_cpp/   # optional (Tier 2b): C++/librdkafka producer, practice + perf comparison
producer_sf/    # optional (Tier 2b): Salesforce polling job, second event source
consumer/       # idempotent Python consumer, DLQ handling
flink_job/      # PyFlink windowed/stateful/join jobs
spark_job/      # PySpark batch ETL (Tier 2, single job)
api/            # FastAPI REST + Strawberry GraphQL
db/             # Postgres schema, migrations, materialized views
docker-compose.yml
.github/workflows/ci-cd.yml
ARCHITECTURE.md
DECISIONS.md
LEARNING_LOG.md
ARCHITECT_REVIEWER.md
KPI_GLOSSARY.md
DATA_QUALITY.md
STANDARDS.md
```

## Working conventions

1. **Architect review before moving to the next phase.** Use the persona
   and checklist in `ARCHITECT_REVIEWER.md`. Don't rubber-stamp — surface
   the weakest point of a design first, ask the critical questions, only
   then suggest fixes if asked.
2. **Update `DECISIONS.md`** after any non-trivial choice (schema shape,
   partition key, window type, join strategy, etc.) — what was chosen,
   what was rejected, why.
3. **Write `LEARNING_LOG.md` entries yourself, in your own words**, after
   each component works — this is interview prep material, not something
   to generate for you.
4. **Don't expand scope** without updating the tier list in this file and
   `ARCHITECTURE.md` first. If asked to add something not in a tier,
   flag that explicitly rather than just building it.
5. **One phase per session** where practical — Kafka/ingestion, stream
   processing, SQL/storage, API layer, containerization, cloud deploy.
   Current phase: **Kafka/ingestion (producer + Redpanda setup)**.
6. **KPI/data-quality workflow order:** rough KPI candidates
   (`KPI_GLOSSARY.md`, 🟡 status) → sanity checks (`DATA_QUALITY.md`) →
   precise KPI definitions (upgrade to 🟢 in `KPI_GLOSSARY.md`). Don't
   write a precise metric definition before the matching sanity check is
   done — that's writing a guess, not a definition.
7. **Standards compliance is part of "done."** Before marking any
   component complete, check it against `STANDARDS.md` — naming,
   schema/versioning, logging, and its tier's testing bar. This is part
   of the architect review in convention 1, not a separate step to skip.
8. **Automated review gate.** `scripts/ai_review.py` runs the same
   `ARCHITECT_REVIEWER.md` persona programmatically against every PR's
   diff (CI: `ai-review` job) and, optionally, locally before each commit
   (`git config core.hooksPath .githooks`). It reviews the diff plus
   `ARCHITECTURE.md`/`STANDARDS.md` as context — not the whole repo from
   scratch each time. Requires `ANTHROPIC_API_KEY` (repo secret in CI,
   local env var for the pre-commit hook). Bypass with `git commit
   --no-verify` only when you can explain why in the commit message.

## Current status

Phase: not yet started — this is session 1. First task: docker-compose
with Redpanda + Postgres running locally, then the replay producer
reading Instacart data and publishing synthesized events.
