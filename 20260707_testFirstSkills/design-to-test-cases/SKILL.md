---
name: design-to-test-cases
description: Enumerate test cases from design documents before any code exists (test-first, not TDD). Use when the user asks to derive, list, or review test cases, test items, or test viewpoints from specs or design documents (Word .docx, Excel .xlsx, PDF, or text) covering screens, Web APIs, batches, or other features.
---

# Design-to-Test-Cases

Read a set of design documents and produce a reviewable list of test cases —
one verifiable behavior per case — before implementation starts. The output is
a checklist a human can approve, not executable test code.

Two principles govern everything below:

1. **Accuracy over invention.** A test case must be traceable to a statement
   in a design document or to an answer from the user. When the design is
   silent or ambiguous, ask — do not guess. Only skip asking when the
   documents leave literally no open questions.
2. **Token discipline.** Design documents are often large Office files. Never
   read them whole and never read binary formats directly. Read structure
   first, then extract only the sections you need, and persist what you learn
   so nothing is read twice.

## Step 1 — Inventory the documents

List the design files the user points you at (or discover them in the given
directory). Record for each: path, format, approximate size. If any file is
legacy `.doc` / `.xls`, ask the user to re-save it as `.docx` / `.xlsx` before
continuing.

## Step 2 — Read structure first, then extract selectively

Use the bundled extractor (Python 3, standard library only; PDF needs `pypdf`
or your own native PDF reading):

```
python scripts/extract_doc.py structure <file>
python scripts/extract_doc.py extract <file> [--heading TEXT | --sheet NAME | --pages A-B | --lines A-B]
```

- `structure` shows a Word heading outline, Excel sheet list with ranges, PDF
  page count/bookmarks, or text headings — a few hundred tokens per file.
- `extract` pulls one section, one sheet, one page range, or one line range.
  Output is capped (default 20,000 chars) and tells you if it was truncated.

Rules:

- Run `structure` on every file first. From the outlines alone, decide which
  sections matter for test design (screen specs, API specs, permission
  matrices, validation rules, state transitions) and which to skip (revision
  history, glossaries, styling guides).
- Extract one feature's worth of content at a time, immediately distill it
  into the inventory (Step 3), and do not re-extract the same section later.
- Never open `.docx`/`.xlsx`/`.pdf` with a plain file reader — you would pay
  tokens for XML/binary noise. If your environment reads PDFs natively, page
  ranges of a few pages at a time are acceptable instead of the script.
- For very large Excel sheets, extract the first ~30 rows to learn the column
  layout before deciding whether the rest is needed.

## Step 3 — Build a feature inventory (working file)

Create `test-case-work/inventory.md` and, as you read, record one entry per
screen / API endpoint / batch / feature:

```
## <Feature name> (source: <file> § <section/sheet/pages>)
- Type: screen | api | batch | other
- Actors/roles involved:
- Inputs and their constraints:
- Behaviors stated in the design:
- Error/edge behaviors stated:
- Ambiguities noticed:            <- feed Step 4
```

This file is your memory: later steps work from the inventory, not by
re-reading the documents. Note contradictions between documents here too.

## Step 4 — Ask the user about every ambiguity

Before writing test cases, collect the `Ambiguities noticed` entries and ask
the user about them **in one batch**. Typical triggers:

- Roles/permissions mentioned but not fully enumerated (who else can log in?)
- Behavior on invalid input or failure not specified
- Boundary values implied but not stated (max lengths, ranges, date limits)
- State transitions with unspecified source/target states
- Two documents that disagree
- Scope: are non-functional aspects (performance, security hardening) in
  scope for this test list?

Format each question as: what is ambiguous → why it changes the test cases →
your proposed default. Number them so the user can answer tersely. If an
interactive question tool is available, use it; otherwise write the questions
to `test-case-work/questions.md`, tell the user, and stop until answered.

Skip this step only when there are genuinely zero open questions — that is
rare. If the user tells you to proceed without answers, apply your stated
defaults and tag every affected case `[ASSUMPTION]` in the output.

## Step 5 — Derive test cases

For each inventory entry, walk the perspective catalog in
[references/test-perspectives.md](references/test-perspectives.md) and write
cases. Granularity and phrasing rules:

- One case = one verifiable behavior with an observable outcome. Split "and"
  cases. Model: "On the main menu screen, an administrator can open the
  master-edit screen in addition to the view screen."
- Always pair positive and negative: for every "accepts / allows / shows",
  ask what the matching "rejects / denies / hides" case is. If the design
  doesn't state the negative behavior, that is a Step 4 question, not an
  invented case.
- Cover every role × every role-gated behavior; every stated input rule as
  both a passing and a failing case; boundaries at min/max and just outside.
- Write test cases in the language of the design documents (Japanese
  documents → Japanese test cases), regardless of this skill being English.
- Do not pad. A behavior the design does not state and the user did not
  confirm produces no test case.

## Step 6 — Produce the deliverable

Write the final list using the format in
[references/output-template.md](references/output-template.md): a summary,
per-feature tables with ID / category / test case / source / status, and a
trailing section listing open questions and assumptions. Every case cites its
design-document source (or the Q&A answer). Default output file:
`test-cases.md` in the user's chosen output directory.

## Quality checklist (before delivering)

- [ ] Every feature in the inventory has at least one normal and one error case, or a stated reason why not.
- [ ] Every role that appears in the design appears in some permission case.
- [ ] No test case exists without a source citation or a confirmed answer.
- [ ] All unresolved ambiguities appear in the open-questions section, none silently dropped.
- [ ] Case IDs are unique and stable (feature prefix + number).
