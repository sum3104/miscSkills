# Test Perspective Catalog

Walk this catalog for every feature in the inventory. Not every perspective
applies to every feature — skip consciously, don't skip by omission. When a
perspective applies but the design document is silent, that is a question for
the user (SKILL.md Step 4), not a case to invent.

## A. Screens (UI)

1. **Initial display** — what is shown on first open: default values,
   focus, disabled/hidden elements, data loaded from where.
2. **Authorization / role-based display** — for each role: which elements are
   visible, enabled, or reachable. Cover every role × every gated element,
   including the denial side (general user does NOT see the admin menu).
3. **Input validation** — per field: required/optional, type, length,
   format (mail, date, phone), character classes (full/half width for
   Japanese systems), and the error message/behavior on violation.
4. **Boundary values** — min, max, min−1, max+1 for lengths, counts,
   amounts, dates. Zero items, one item, many items for lists/paging.
5. **Actions and navigation** — each button/link: destination, what is
   saved/sent, double-click or resubmit behavior, cancel/back behavior,
   unsaved-changes handling.
6. **State-dependent display** — same screen under different data states:
   empty result, partial data, locked/approved records, expired sessions.
7. **Messages** — confirmation dialogs, success notifications, error
   display location and wording (if the design specifies wording, test it).

## B. Web APIs

1. **Authentication** — valid credential/token succeeds; invalid, expired,
   missing, and malformed tokens fail with the specified status/error body.
2. **Authorization** — authenticated but insufficient role/scope is denied.
   Distinguish 401-type from 403-type behavior if the design does.
3. **Normal response** — for valid input: status code, response schema,
   key field values, side effects (record created, mail queued).
4. **Input validation** — each parameter: missing, wrong type, out of
   range, oversized, malformed. Expected status code and error format.
5. **Boundary values** — same as screens, applied to parameters and
   payload sizes.
6. **Error responses** — resource not found, conflict/duplicate,
   dependent-service failure if specified.
7. **Idempotency / repeat calls** — double submission, retry behavior,
   same request twice (only if the design addresses it; otherwise ask).

## C. Batch / background jobs

1. **Normal run** — expected inputs produce expected outputs/updates/logs.
2. **Empty input** — zero target records: completes cleanly, no side effects.
3. **Partial failure** — one bad record among many: skip/abort/rollback per
   the design.
4. **Re-run / duplicate run** — running twice, running after a failure.
5. **Schedule and preconditions** — required preceding jobs, lock behavior
   when the previous run is still active.

## D. Data maintenance (master edit, CRUD screens)

1. Create / read / update / delete each succeed with valid data.
2. Duplicate keys, referential constraints (delete a master in use).
3. Concurrent edit behavior (optimistic lock, last-write-wins) if specified.
4. Audit fields (updated-by, updated-at) if specified.

## E. Cross-cutting

1. **State transitions** — if the design has statuses (draft → approved →
   closed), test every allowed transition and at least the explicitly
   forbidden ones.
2. **Dates and time** — month/year boundaries, leap years, timezone or
   era (和暦) handling if the system is Japanese.
3. **Combinations** — when 2+ conditions jointly decide behavior
   (role × record state, plan × feature flag), build a small decision table
   and cover each distinct outcome at least once. Do not enumerate the full
   cartesian product unless the design demands it.
4. **Non-functional** — performance, capacity, security hardening: include
   only if the design states measurable requirements AND the user confirmed
   they are in scope.

## Techniques to keep the list small but sufficient

- **Equivalence partitioning**: one representative per input class, not
  every value.
- **Boundary value analysis**: test at and just outside each boundary; the
  interior is covered by the equivalence representative.
- **Decision tables**: for combination logic, one case per distinct rule
  outcome.
- **Positive/negative pairing**: every "can" statement in the design implies
  a "cannot" case for the complementary condition — but only write it if the
  design or the user defines what "cannot" looks like.
