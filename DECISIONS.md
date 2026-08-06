# Decisions log

One entry per non-trivial decision. Keep entries short — this is a log to
defend decisions in an interview, not a design essay. Newest at the top.

---

## Template

**Date:**
**Decision:**
**Options considered:**
**Chosen because:**
**Rejected because:**

---

<!-- Add entries below as you build. Example: -->

## Example — Kafka partition key

**Date:** 2026-07-29
**Decision:** Partition Kafka topics by `user_id`
**Options considered:** partition by `order_id`, partition by `user_id`, no explicit key (round-robin)
**Chosen because:** guarantees per-user event ordering, which matters for the stateful running-total and pattern-detection operators in Flink
**Rejected because:** `order_id` partitioning spreads load more evenly but loses per-user ordering, which the stateful operators depend on
