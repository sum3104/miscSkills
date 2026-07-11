---
name: knowledge-backfill
description: Seed the project's knowledge vault (docs/knowledge) retroactively by extracting domain terms and business rules from existing specs, plans, and ADRs. Use once when introducing the vault to a project that already has superpowers-generated documents, or to catch up after the vault has fallen behind the documents.
---

# Knowledge-Backfill

Read the project's existing design documents — superpowers-generated specs
and plans, and ADRs — and populate the Obsidian vault with the same kind of
notes that `knowledge-capture` produces from live sessions. Source documents
are **never modified**: they remain immutable point-in-time artifacts that
the vault links back to.

This skill is installed alongside `knowledge-capture` and reuses its
references (paths below assume the two skill folders sit side by side):

- What to extract, what to skip, dedup rules:
  [../knowledge-capture/references/extraction-guide.md](../knowledge-capture/references/extraction-guide.md)
- Note formats and conventions:
  [../knowledge-capture/references/note-templates.md](../knowledge-capture/references/note-templates.md)

Notes are written in the language of the source documents (Japanese specs →
Japanese notes), regardless of this skill being English.

## Step 1 — Inventory the documents

List the files under the spec/plan directories — current superpowers
writes to `docs/superpowers/specs/` and `docs/superpowers/plans/`, older
layouts use `docs/specs/` and `docs/plans/`; both generations may coexist,
so inventory whichever exist — and the ADR directory (commonly `docs/adr/`;
ask if it is elsewhere). Record path and date (from the filename or
frontmatter; fall back to `git log --follow --format=%as -1 -- <file>` for
the first commit date). Source wiki-links in notes must use the real
vault-root-relative path (e.g. `[[superpowers/plans/...]]` vs
`[[plans/...]]`). If `docs/knowledge/` does not exist, offer to scaffold
it from the bundled `vault-template/` first.

Confirm the inventory and intended scope with the user before extracting —
they may want to exclude abandoned plans or superseded specs.

## Step 2 — Extract in chronological order

Process documents **oldest first**, so that when a later document changes a
rule, the note is updated and the earlier statement lands in `## History`
naturally — the same flow a live vault would have had.

Per document:

1. Read it and list candidates per the extraction guide. For backfill the
   emphasis is: term definitions and glossary-like passages, condition →
   outcome rules, exceptions, thresholds, permissions, and — especially in
   ADRs and plan "Alternatives considered" sections — the domain reasons
   behind rejected options.
2. Apply the dedup rules against notes created so far (and any pre-existing
   ones): update rather than duplicate; changed content goes to `## History`
   with the document's date.
3. Every note's `source` must cite the document as a vault-root-relative
   wiki-link (e.g. `"[[plans/2026-07-01-shipping]]"`). A backfilled note with
   no source is a bug.
4. Knowledge that comes verbatim from an approved spec or accepted ADR may be
   `status: confirmed`; anything inferred or found only in a plan's
   exploratory prose stays `draft` with `[ASSUMPTION]` on the guessed lines.

Contradictions between documents that chronology cannot resolve: record both
statements in the note's `## History`, set `status: draft`, and add it to the
questions batch (Step 3). Do not pick a winner yourself.

## Step 3 — Ask questions in one batch

Collect every ambiguity — unresolvable conflicts, rules that look superseded
but were never explicitly retired, terms used inconsistently across
documents — and ask the user about them **in one numbered batch**: what is
ambiguous → the candidate interpretations → your proposed default. If the
user defers, apply the stated defaults and leave the affected notes `draft`
with `[ASSUMPTION]` tags.

## Step 4 — Finish the vault and report

- Add all new notes to the topic lists in `knowledge/Home.md`.
- Report: number of documents processed, notes created/updated (grouped by
  `domain` / `rules`), the open-questions list, and a reminder that from now
  on `knowledge-capture` maintains the vault incrementally.

## Quality checklist (before reporting)

- [ ] No file under `specs/`, `plans/`, or the ADR directory was modified.
- [ ] Every note cites at least one source document.
- [ ] Documents were processed oldest-first; superseded values sit in `## History`.
- [ ] Conflicts are recorded as `draft` + question, not silently resolved.
- [ ] Home.md lists every created note.
