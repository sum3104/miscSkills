---
name: adr-capture
description: Distill ADR-worthy technical and implementation decisions from the current conversation into draft ADRs (status: proposed) under docs/adr. Use right after a design document (spec / plan) has been written — run this BEFORE knowledge-capture so knowledge notes can link the fresh ADRs — when a plan or implementation deviates significantly from the agreed design, before ending a session that contained substantial technical decision discussion, or when the user asks to record an architecture or technology decision.
---

# ADR-Capture

Turn the technical decisions made in this session — technology choices,
architecture shapes, cross-cutting policies, deviations from an agreed
design — into draft Architecture Decision Records. The conversation itself
is the source: extract while the context is still live, never by parsing
session logs later.

Two principles govern everything below:

1. **Signal over noise.** Only decisions that meet the worthiness criteria
   in [references/adr-criteria.md](references/adr-criteria.md) become ADRs:
   significant impact, hard to reverse, cross-cutting, consciously chosen
   among alternatives, or deviating from an earlier design. Everything
   below that bar is dropped silently. An ADR log where everything is
   recorded is one where nothing can be found.
2. **Record, don't duplicate.** An ADR captures the decision, the options
   that were on the table, and the *why* — especially why the losing
   options lost. The what/how details live in the spec; link to it with a
   wiki-link, never restate it.

Every new ADR is written automatically as `status: proposed` — a human
never has to remember to ask for it — and is promoted to `accepted` only
when the user confirms it in the Step 5 report. This mirrors
knowledge-capture's `draft → confirmed` flow.

## Step 1 — Locate the ADR directory and its conventions

- Default location is `docs/adr/` (the project's `docs/` is an Obsidian
  vault root shared with specs, plans, and knowledge notes). Also check
  common alternatives: `docs/decisions/`, `adr/`, `doc/adr/`.
- If a directory with existing ADRs is found, **follow its conventions** —
  file naming, numbering, template shape — even if they differ from the
  defaults below.
- If no ADR directory exists anywhere, tell the user and offer to create
  `docs/adr/` before continuing.
- Default naming (greenfield): `NNNN-title-with-dashes.md` — a 4-digit
  sequential number plus a short lowercase-English dashed title (e.g.
  `0001-use-meilisearch.md`), per the MADR convention. Determine the next
  number as max existing + 1, re-checking immediately before writing each
  file. Filenames stay ASCII even when the ADR body is not.

## Step 2 — Collect candidate decisions from the conversation

Re-read the session and list every decision candidate, applying
[references/adr-criteria.md](references/adr-criteria.md). In short, a
decision is ADR-worthy when it is at least one of:

- **Significant** — shapes the system beyond one file or one task
  (framework/library/protocol choice, schema or architecture shape).
- **Hard to reverse** — migrations, external contracts, data formats.
- **Cross-cutting** — policies that many parts must follow (error
  handling, auth strategy, logging, versioning).
- **Chosen among alternatives** — options were weighed and one won for
  stated reasons (superpowers brainstorming's approach comparison is a
  prime source; the rejected options' "why not" is the highest-value
  content, because the spec usually keeps only the winner).
- **A deviation** — plan-writing or implementation departed from an
  agreed spec or an accepted ADR in a way that future readers must know.

Do NOT capture domain terms or business rules — those belong to the
`knowledge-capture` skill, which runs after this one. Rejected-alternative
reasons split by the *kind* of reason: technical reasons stay here in the
ADR; business-fact reasons belong in the knowledge vault.

## Step 3 — Check existing ADRs

For each candidate, grep the ADR directory for the topic and its key terms
before writing anything. Classify:

- **Already covered** — an existing ADR records the same decision with
  nothing new: drop the candidate silently.
- **Supersedes** — the session decided something that replaces an existing
  ADR: write a new ADR linking the old one (`Supersedes: [[adr/NNNN-...]]`).
  Flip the old ADR's `status` to `superseded by ADR-NNNN` **only after the
  user confirms in Step 5** — this status flip is the single permitted
  edit to an existing ADR.
- **New** — no ADR covers it: write one.

## Step 4 — Write draft ADRs

Follow the format in
[references/adr-template.md](references/adr-template.md) exactly (MADR
required sections; greenfield default — Step 1 conventions win if the
project already has ADRs). Key rules:

- `status: proposed`, `date` = today, `source` = wiki-link to the design
  doc just written and/or a session marker.
- Link the spec with a vault-root-relative wiki-link, using the path that
  actually exists: current superpowers writes to `docs/superpowers/specs/`
  and `docs/superpowers/plans/` (so `[[superpowers/specs/...]]`), older
  layouts use `docs/specs/` and `docs/plans/` (so `[[specs/...]]`).
- Every considered option gets its rejection reason. A bare option list
  without the "why not" is the failure mode this skill exists to prevent.
- One decision per ADR. A session that made three independent decisions
  produces three ADRs.
- Write the ADR title and body in the language of the conversation
  (Japanese discussion → Japanese ADR); section headings and frontmatter
  keys stay in English per the template.
- Never modify anything under `specs/` or `plans/` (either path
  generation), and never edit existing ADRs except the confirmed status
  flip from Step 3.

## Step 5 — Report to the user

Finish with a short summary the user can review at a glance:

- ADRs created: path + one-line decision statement each.
- Numbered confirmation questions: one per `proposed` ADR ("accept as
  recorded?") and one per pending `superseded` flip. On approval, flip
  `proposed → accepted` (and apply confirmed supersede flips); on
  correction, amend the ADR first.
- Candidates you deliberately dropped as below the bar, in one line, if
  the user might expect them.
- If this run was triggered by a finished design doc, note that
  `knowledge-capture` should run next and can wiki-link the fresh ADRs.

## Quality checklist (before reporting)

- [ ] Every ADR traces to a decision actually made in this conversation or a cited document.
- [ ] No ADR restates spec content — it links instead.
- [ ] Every considered option has its rejection reason recorded.
- [ ] No ADR was written for a below-threshold choice (naming, trivially reversible defaults).
- [ ] Numbering follows the directory's convention with no collisions.
- [ ] Nothing under `specs/` or `plans/` was modified; existing ADRs untouched except confirmed status flips.
- [ ] All new ADRs are `status: proposed` and surfaced as confirmation questions.
