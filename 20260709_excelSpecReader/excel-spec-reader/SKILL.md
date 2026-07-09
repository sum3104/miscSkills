---
name: excel-spec-reader
description: Read Excel spec workbooks (API specs, test specs, screen lists) accurately and token-efficiently, without writing throwaway parser scripts. Use when a task requires reading .xlsx/.xlsm design documents - especially messy real-world ones where the header row is not row 1, merged cells abound, formats differ per project, or one workbook mixes many purposes across sheets. Also use to locate one item (an API, a test case) in a large book, or to convert a sheet to JSON/Markdown via a saved format profile.
---

# Excel-Spec-Reader

Read Excel-based spec documents the way a careful human does — find the right
sheet, find the real header row, respect merged cells and formulas — while
loading only the cells the task needs. What you learn about a workbook's
layout is saved once as a *format profile* in the target project and reused
by every later session.

Two principles govern everything below:

1. **Accuracy over invention.** A header guess is a hint, not a fact: verify
   it against real data rows before relying on it, and ask the user when a
   column's meaning is ambiguous. Never guess what a merged or blank cell
   means, and never save an unverified profile — a wrong profile poisons
   every future session.
2. **Token discipline.** Never open an .xlsx with a plain file reader and
   never dump whole sheets into context. The order is always: existing
   profile → `structure` → `search` → narrow `extract` → profile-driven
   `convert`. Everything goes through the bundled script, which caps its own
   output.

All reading is done with the bundled extractor (Python 3, standard library
only, no pip install):

```
python scripts/xlsx_reader.py structure FILE
python scripts/xlsx_reader.py extract FILE --sheet NAME [--rows A-B] [--cols A-C] [--raw] [--show-formulas]
python scripts/xlsx_reader.py search  FILE --text KEYWORD [--sheet NAME] [--limit N]
python scripts/xlsx_reader.py convert FILE --sheet NAME --profile PROFILE.json [--format json|markdown]
```

Merged cells are filled from their anchor value, date serials are rendered
ISO (Japanese era formats included), and formula cells show the cached value
a human sees on screen. Task-shaped examples:
[references/reading-recipes.md](references/reading-recipes.md).
Legacy `.doc`/`.xls` files are not supported — ask the user to re-save as
`.xlsx` first.

## Step 1 — Look for an existing profile

Check the target project for `docs/excel-formats/*.json` and match the
workbook against each profile's `file_pattern` and `name`. If one matches:

- Use its `sheets` role map to jump straight to the sheets relevant to the
  task (e.g. the task says "read the API spec" → the sheet whose
  `role` is `api-spec`), skipping Steps 2-4 entirely.
- Stay alert for `# WARNING` header-drift lines from `convert`; they send
  you back to Step 3 to re-verify and update the profile.

If no profile matches, continue and create one.

## Step 2 — Take inventory with `structure`

Run `structure` once. For each sheet note: is it hidden, how many merges,
where the header probably is (`header-guess`), and — from the sheet name and,
when unclear, a 10-30 row peek — what the sheet is *for*. Real workbooks mix
many purposes (cover page, revision history, design mocks, API spec, unit
tests, integration tests) and usually only one or two sheets matter for the
task. Decide the role of every sheet once; sheets that will never be read
(covers, histories, shape-only design mocks) get recorded in the profile's
`skip_sheets` with the reason.

## Step 3 — Verify the header row and column meanings

For each sheet the task needs, extract the top region
(`extract --sheet NAME --rows 1-30`) and confirm against real data rows:

- Where is the actual header row? Trust data over the guess; with two-row
  headers prefer the lower, more specific row.
- What does each column mean? Map column letters to semantic fields. If a
  column's values look computed from other columns, check with
  `--show-formulas` and mark it `derived`.
- Batch every ambiguity into one round of questions for the user (what is
  ambiguous → why it matters → your proposed default). Do not save guesses
  as facts: if the user tells you to proceed unanswered, record the open
  point in the profile's `notes`.

## Step 4 — Save or update the profile

Write the verified layout to `docs/excel-formats/<format-name>.json` in the
target project, following
[references/profile-format.md](references/profile-format.md): the sheet role
map, per-sheet header/column config, `skip_sheets` with reasons, and a
verification date in `notes`. One profile per document format (all workbooks
sharing the layout), committed to the project so other sessions and
teammates' agents reuse it. On header-drift warnings, fix the profile in
place rather than creating a duplicate.

## Step 5 — Read what the task needs

With the layout known, choose the cheapest reading motion
(details and examples in
[references/reading-recipes.md](references/reading-recipes.md)):

- **One item** (an endpoint, a test case): `search --text` first, then
  `extract --rows` around the hit. Never page through a book sheet by sheet.
- **A region**: `extract --sheet --rows --cols`, in slices, distilling each
  slice into your working notes before pulling the next — do not re-extract
  what you already read.
- **A whole table, structured**: `convert` with the profile, `--format json`
  for downstream processing (each object carries `_row` for traceability)
  or `--format markdown` for human review. `convert` refuses to run without
  a profile by design — unverified bulk conversion produces confidently
  wrong data.

## Output language

Deliverables follow the target documents' language (Japanese workbook →
Japanese summaries, findings, and Markdown output), regardless of this skill
being written in English. Profile `field` keys stay ASCII snake_case;
profile `label` and `description` values stay in the document's language.

## Quality checklist (before delivering)

- [ ] No .xlsx was opened with a plain file reader, and no full-sheet dump was pasted into context.
- [ ] The header row and every mapped column were verified against at least 2 real data rows.
- [ ] Ambiguous column meanings were asked about, or recorded as open points in the profile `notes` — never silently guessed.
- [ ] The profile exists in the target project's `docs/excel-formats/`, has a sheet role map, and its `notes` records the verification date.
- [ ] Every fact extracted for the task is traceable to a sheet and row number.
- [ ] Any header-drift warnings were resolved by re-verifying and updating the profile, not ignored.
