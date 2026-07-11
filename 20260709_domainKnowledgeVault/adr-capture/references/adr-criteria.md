# ADR-worthiness criteria — what earns an ADR, what does not

Used by `adr-capture` to filter decision candidates. The bar exists on
purpose: an ADR directory that records every choice is unreadable, and an
unreadable ADR directory protects nothing.

## Earns an ADR

A decision earns an ADR when at least one signal applies:

| Signal | Example |
|---|---|
| Technology selection | Framework, library, database, protocol, external service ("検索は Meilisearch を使う") |
| Architecture shape | Module boundaries, sync vs async, monolith vs services, data flow topology |
| Schema / data format | Table design choices, event payload shape, file formats — anything persisted or shared |
| Irreversible or costly to reverse | Migrations, published API contracts, ID schemes |
| Cross-cutting policy | Error-handling strategy, auth model, logging/telemetry rules, versioning scheme |
| Chosen among alternatives | Options were explicitly compared and one won for stated reasons — superpowers brainstorming's approach comparison is the prime source |
| Deviation | Plan-writing or implementation departed from an agreed spec or an accepted ADR ("spec では REST だったが実装で gRPC に変更した") |

The single highest-value content is the **rejected options and why they
lost**. Specs keep the winner; the "why not" usually survives only in the
conversation. If a decision has stated alternatives with reasons, that
alone is a strong signal it is ADR-worthy.

## Does NOT earn an ADR

- **Naming** — variables, functions, files, branch names.
- **Single-file or local choices** — a refactor pattern inside one module,
  a helper's signature.
- **Trivially reversible defaults** — a config value nobody argued about,
  a formatting rule the linter owns.
- **Tooling and logistics chatter** — editor setup, task ordering, CI
  retry counts (unless a cross-cutting policy was decided).
- **Restatements** — the decision is already recorded in an existing ADR
  with nothing new. Drop silently.
- **Undecided discussions** — options were explored but nothing was
  chosen. Not an ADR yet; mention it in the Step 5 report only if the user
  is likely to think it was decided.

## Boundary with knowledge-capture

`adr-capture` and `knowledge-capture` split the session's content by kind,
not by importance:

- **Technical / implementation decisions** → ADR (this skill). Never into
  the knowledge vault.
- **Domain terms and business rules** → knowledge vault
  (`knowledge-capture`). Never into an ADR.
- **Rejected-alternative reasons** split by the kind of reason:
  - Technical reason ("Elasticsearch は運用人員が足りない") → stays in the
    ADR's option list.
  - Business fact ("後払いを外したのは与信コストが単価に見合わないため") →
    the cost structure is domain knowledge; it belongs in a vault note.
    The ADR may still cite it in one line and link the note.

When both skills fire on the same finished design doc, `adr-capture` runs
first so knowledge notes can wiki-link the fresh ADRs.

## Deduplication and superseding

1. Grep the ADR directory for the candidate's topic and key terms before
   writing anything.
2. Same decision, nothing new → drop silently.
3. Same topic, decision changed → new ADR with
   `Supersedes: [[adr/NNNN-...]]` under More Information. The old ADR's
   `status` becomes `superseded by ADR-NNNN` **only after user
   confirmation** — that flip is the only permitted edit to an existing
   ADR. Never rewrite an old ADR's body: ADRs are point-in-time records,
   and the chain of superseded records *is* the history.
4. Same decision recorded under a different title → do not duplicate;
   report the near-miss so the user can decide.

## Status lifecycle

- `proposed` — written automatically by this skill; not yet human-ratified.
- `accepted` — the user confirmed it in the Step 5 report (or it was
  accepted before this skill existed).
- `deprecated` — no longer applies and nothing replaced it (user-driven).
- `superseded by ADR-NNNN` — replaced by a newer ADR; flipped by this
  skill only with user confirmation.

Who flips what: `adr-capture` writes `proposed`, flips `proposed →
accepted` on user approval, and flips `accepted → superseded by ADR-NNNN`
on confirmed supersede. All other transitions are the user's.
