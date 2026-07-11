---
name: knowledge-capture
description: Distill domain knowledge and business rules from the current conversation into a git-managed Obsidian vault (docs/knowledge). Use right after finishing a brainstorming or design session (once the design doc / spec / plan has been written), before ending a session that contained substantial domain discussion, or when the user asks to record domain terms, business rules, or domain knowledge. When both this skill and adr-capture fire on a finished design doc, adr-capture runs first so notes can link the fresh ADRs.
---

# Knowledge-Capture

Turn the domain knowledge that surfaced in this session — term definitions,
business rules, constraints, assumptions — into small, linked Markdown notes
inside the project's Obsidian vault. The conversation itself is the source:
extract while the context is still live, never by parsing session logs later.

Two principles govern everything below:

1. **Accuracy over invention.** Every note must be traceable to something
   actually said in this conversation (or written in a referenced document).
   If a rule was implied but never stated, that is a question for the user,
   not a note. Unconfirmed knowledge is marked `status: draft` and tagged
   `[ASSUMPTION]`.
2. **Update over duplicate.** The vault is a living body of knowledge, not a
   session log. Before creating any note, search for an existing one covering
   the same concept and update it instead. One concept or rule per note.

## Vault layout (expected)

The vault root is the project's `docs/` directory (so specs, plans, and ADRs
are linkable with `[[wiki-links]]`). Notes go here:

```
docs/
├── knowledge/
│   ├── Home.md          # map of content
│   ├── domain/          # one note per domain term / concept
│   └── rules/           # one note per business rule
├── adr/                 # ADRs (adr-capture output) — only adr-capture edits these
├── superpowers/
│   └── specs/  plans/   # current superpowers output — never modified by this skill
├── specs/  plans/       # older superpowers layout — same rule; either generation may exist
└── .obsidian/
```

Specs and plans may live under `docs/superpowers/` (current superpowers)
or directly under `docs/` (older layout) — detect which paths actually
exist and address wiki-links accordingly.

If `docs/knowledge/` does not exist, tell the user and offer to scaffold it
from the bundled `vault-template/` before continuing.

## Step 1 — Collect candidates from the conversation

Re-read the session and list every candidate item, applying the criteria in
[references/extraction-guide.md](references/extraction-guide.md). In short,
you are looking for:

- **Domain terms** that were defined, clarified, corrected, or disambiguated
  (corrections the user made to *your* usage are the highest-value items).
- **Business rules**: condition → outcome statements, exceptions, thresholds,
  actor permissions, calculation formulas, temporal rules, external or
  regulatory constraints.
- **Domain reasons behind rejected alternatives** (the "why not" that a spec
  usually drops).
- **Assumptions** stated but not confirmed.

Do NOT capture technical/implementation decisions — those belong in an
ADR. If you notice an ADR-worthy decision that is not yet recorded and the
`adr-capture` skill has not already run this session, invoke `adr-capture`
now (before Step 3, so new notes can wiki-link the fresh ADRs). If
`adr-capture` is not installed, list the decision in the Step 5 report
instead of writing it into the vault.

## Step 2 — Check the vault for existing notes

For each candidate, search `docs/knowledge/` before writing anything:

- Match against note file names, headings, and frontmatter `aliases`.
- Search for the term itself and its synonyms (grep is enough; no plugins or
  MCP required).

Classify each candidate as: **new** (no note exists), **update** (a note
exists and this session refined, extended, or changed it), or **already
covered** (nothing new — drop it silently).

## Step 3 — Write or update notes

Follow the formats in
[references/note-templates.md](references/note-templates.md) exactly.
Key rules:

- One concept per note. A rule with several independent sub-rules becomes
  several notes linked to a parent.
- New notes: fill the frontmatter (`type`, `status`, `aliases`, `source`,
  `created`, `updated`). `source` names where the knowledge came from — the
  design doc just written (as a wiki-link) and/or the session date.
- Updates: change the body, bump `updated`, append the new source. If the
  *content* of a rule changed (not just grew), record the superseded value in
  the note's `## History` section with the date — do not silently overwrite.
- `status: confirmed` only when the user explicitly confirmed it or it comes
  from an approved spec; everything else is `draft`, and guessed details are
  tagged `[ASSUMPTION]` inline.
- Write notes in the language of the conversation (Japanese discussion →
  Japanese notes), regardless of this skill being English.

## Step 4 — Link

- Cross-link related notes with `[[wiki-links]]` (e.g. a rule links to the
  domain terms it uses).
- Link each note to its source spec/plan/ADR using vault-root-relative links
  matching the path that actually exists —
  `[[superpowers/plans/2026-07-01-shipping]]` (current superpowers layout)
  or `[[plans/2026-07-01-shipping]]` (older layout). ADRs created by
  `adr-capture` this session are linked as `[[adr/NNNN-...]]`.
- Add genuinely new notes to the relevant list in `knowledge/Home.md`.
- Never edit anything under `plans/`, `specs/` (either path generation), or
  the ADR directory. They are immutable point-in-time artifacts; the vault
  links *to* them.

## Step 5 — Report to the user

Finish with a short summary the user can review at a glance:

- Notes created (path + one-line gist) and notes updated (path + what
  changed).
- Every `draft` / `[ASSUMPTION]` item, phrased as a confirmable question so
  the user can answer tersely and you can flip items to `confirmed`.
- Anything you deliberately did not capture and why, if the user might
  expect it (e.g. "the retry-strategy discussion is an ADR topic").

## Quality checklist (before reporting)

- [ ] Every note traces to a statement in this conversation or a cited document.
- [ ] No new note duplicates an existing concept (search was actually done).
- [ ] Changed rules keep their previous value under `## History`.
- [ ] All unconfirmed items are `draft` and surfaced in the report.
- [ ] No file outside `docs/knowledge/` and `Home.md` was modified.
