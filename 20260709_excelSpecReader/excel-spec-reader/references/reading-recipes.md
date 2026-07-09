# Reading recipes

Task-shaped command sequences for `scripts/xlsx_reader.py`. All commands share
`--max-chars` (default 20,000; `convert` is unlimited) and print a truncation
notice with narrowing advice when the budget is hit.

## Recipe 1 — First contact with an unknown workbook

```
python scripts/xlsx_reader.py structure 仕様書.xlsx
```

One line per sheet: range, non-empty row count, merge count, hidden flag, and
a `header-guess`. Triage from names alone where possible (表紙, 改訂履歴,
目次 are skippable; a sheet with rows=2 and merges=40 is probably a diagram).
Peek at anything unclear:

```
python scripts/xlsx_reader.py extract 仕様書.xlsx --sheet "API一覧" --rows 1-30
```

## Recipe 2 — Verify a header guess

`header-guess=3` means row 3 *looks* like a header. Confirm it: extract rows
1-30 and check that (a) row 3's cells read like column names, (b) the rows
after it hold data that matches those names, (c) nothing above row 3 is data.
Two-row headers (a merged group label above the real header) are common —
prefer the lower, more specific row as `header_row` and record the situation
in the profile's `notes`.

## Recipe 3 — Find one API / test case in a big book

Do not extract sheet after sheet looking for it:

```
python scripts/xlsx_reader.py search 仕様書.xlsx --text "注文取得"
python scripts/xlsx_reader.py search 仕様書.xlsx --text "API-042" --sheet "API一覧"
```

Each hit prints the sheet, row number, and the full row (merged cells
filled, so a row inside a merged group shows its group value). Then read the
context around a hit:

```
python scripts/xlsx_reader.py extract 仕様書.xlsx --sheet "API一覧" --rows 55-70
```

Hidden sheets are skipped unless you name them with `--sheet`.

## Recipe 4 — Understand a formula-built column

When a column's values look derived (sequence numbers assembled from other
columns, cross-references), check the formulas:

```
python scripts/xlsx_reader.py extract 仕様書.xlsx --sheet "API一覧" --rows 4-10 --show-formulas
```

Cells then render as `api-1-1-IN-1 {=B4&"-IN-"&C4}`. The plain value (what a
human sees) is always the part before `{...}`; a cell showing only `{=...}`
has no cached value stored in the file. Mark such columns `"derived": true`
in the profile.

## Recipe 5 — Read a region precisely

```
python scripts/xlsx_reader.py extract 仕様書.xlsx --sheet "単体テスト" --rows 3-80 --cols B-F
```

Output is TSV with the Excel row number first, merged cells filled downward/
rightward from their anchor. Use `--raw` to see the sheet exactly as stored
(merge anchors only) when you need to know where merges physically are.

## Recipe 6 — Structured output via a profile

Only after a profile exists (see
[profile-format.md](profile-format.md)):

```
python scripts/xlsx_reader.py convert 仕様書.xlsx --sheet "API一覧" \
    --profile docs/excel-formats/api-spec.json --format json
python scripts/xlsx_reader.py convert 仕様書.xlsx --sheet "単体テスト" \
    --profile docs/excel-formats/api-spec.json --format markdown --rows 3-40
```

JSON output is one object per row with a `_row` key for traceability back to
the sheet. Watch for `# WARNING` lines about header drift: they mean the
workbook's layout no longer matches the profile — re-verify and update the
profile before trusting the output.
