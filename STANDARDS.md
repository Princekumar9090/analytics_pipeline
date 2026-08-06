# Engineering standards

Cross-cutting conventions that apply to every component in this project.
Component-specific READMEs should say "see STANDARDS.md" for anything
covered here, and only document what's genuinely unique to that component.
If you find yourself repeating a rule from here in a README, delete it
from the README — one source of truth, not N copies drifting apart.

---

## 1. Naming conventions

**Kafka topics** — kebab-case, domain-prefixed, purpose-suffixed:
- `order-events` — raw events from the Python/C++ producer
- `order-aggregates` — PyFlink's windowed output
- `order-events-dlq` — dead-letter queue for malformed/failed events
- `crm-events` — Salesforce-sourced events (Tier 2b)

**Consumer groups** — `{purpose}-{component}`:
- `flink-agg` (PyFlink), `pg-writer` (Python consumer)

**Postgres** — snake_case, plural table nouns, `mv_` prefix for materialized views:
- Tables: `orders`, `order_items`, `users`
- Views: `mv_revenue_by_minute`

**REST/GraphQL** — plural nouns, versioned REST paths:
- `/api/v1/orders`, GraphQL fields in camelCase per spec convention

**Environment variables** — `SCREAMING_SNAKE_CASE`, service-prefixed:
- `KAFKA_BOOTSTRAP_SERVERS`, `PG_DSN`, `SF_CLIENT_ID`

**Docker Compose services** — kebab-case, matching the directory it runs:
- `redpanda`, `postgres`, `api`, `flink-jobmanager`

---

## 2. Event schema standards

- Every event carries: `event_id` (UUID, used for idempotency/dedup),
  `event_type`, `event_time` (ISO 8601, UTC), `schema_version`.
- Schema defined **once**, as a Pydantic model, imported by both producer
  and consumer — never redefined/duplicated in each service.
- Backward-compatible changes (new optional field) stay within the same
  `schema_version`. Breaking changes bump the version **and** get a
  `DECISIONS.md` entry explaining why.

---

## 3. Error handling & logging

- Structured logging only (JSON) — no bare `print()`.
- Every log line includes: timestamp, level, service name, and the
  relevant correlation/event ID.
- Consumer errors are never silently dropped: route to DLQ, or log with
  full context + increment an error metric. Silence is a bug.
- No bare `except:` — catch specific exceptions, log with context on
  what was being processed when it failed.

---

## 4. Testing expectations by tier

- **Tier 1 components**: at least one unit test per core function, plus
  one integration test proving the happy path end-to-end.
- **Tier 2/2b components**: at least one smoke test proving it runs;
  full coverage isn't required given the scope tier.
- A component isn't "done" without its test(s) — this pairs with the
  `LEARNING_LOG.md` entry, not a replacement for it.

---

## 5. Code style

- Python: `black` + `ruff`, type hints on all function signatures.
- One module = one responsibility, matching the repo structure in
  `CLAUDE.md` — don't let unrelated logic accumulate in one file.

---

## 6. Documentation per component

- Each top-level directory (`producer/`, `consumer/`, `flink_job/`, etc.)
  gets a short `README.md`: what it does, how to run it locally, what it
  depends on. Naming/logging/testing rules are **not** repeated there —
  link back here instead.

---

## 7. Commit conventions

- Conventional Commits style: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
- Enforced in spirit by the CI/CD lint/test gate in `.github/workflows/ci-cd.yml`.
