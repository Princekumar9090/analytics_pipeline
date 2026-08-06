# KPI Glossary

Single source of truth for what each metric means. Fill in "Precise
definition" only after the matching sanity checks (see DATA_QUALITY.md)
are done — a definition written before you've seen the data's edge cases
is a guess, not a definition.

Status: 🟡 candidate (not yet defined) → 🟢 defined (checks done, definition locked)

---

## North star

**Orders per active user per week** 🟡
- Why: captures engagement and volume in one number; a pure revenue or
  order-count north star can rise while user health quietly declines.
- Precise definition: _(fill in after checking `orders`/`user_id` grain
  and defining "active")_

- Note: User will be regarded as 'active' if atleast one order is being placed in the trailing 30 days (Using order_number + days_since_prior_order fields)

## Guardrails

**Reorder rate** 🟡
- Why: north star can go up from binge-then-churn behavior; this catches it.
- Precise definition: _(fill in — see DATA_QUALITY.md note on first-order nulls)_

**Payment failure rate** 🟡
- Why: catches operational/reliability regressions the volume metrics won't show.
- Precise definition: _(fill in once `payment_processed`/`payment_failed`
  synthesis logic is finalized in the producer)_

## Revenue / order health

**Revenue per minute/hour/day (tumbling window)** 🟡
- Precise definition: _(depends on synthetic price-per-product decision —
  log that decision in DECISIONS.md first, then define this)_

**Average order value (AOV)** 🟡
- Precise definition: _(numerator: ?, denominator: ? — orders or users?)_

**Items per basket** 🟡
- Precise definition: _(watch the grain issue — aggregate order_products
  to order level first, don't average the fanned-out join)_

## Growth / momentum

**Order volume trend (sliding window)** 🟡
- Precise definition: _(window size, update frequency)_

## Customer behavior

**Session conversion rate (item_viewed → order_placed)** 🟡
- Precise definition: _(session boundary = ? inactivity gap; see session-window design in ARCHITECTURE.md)_

## Retention

**Cohort reorder curves** 🟡
- Precise definition: _(cohort = signup week? first-order week?)_

---

## Template for new entries

**Metric name** 🟡/🟢
- Why it matters / what decision it informs:
- Precise definition (numerator, denominator, window, edge cases):
- Known caveats:
