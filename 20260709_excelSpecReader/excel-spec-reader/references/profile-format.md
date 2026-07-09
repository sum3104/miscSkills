# Format profile — schema and rules

A format profile records what you learned about one workbook format (header
row position, what each column means, which sheet serves which purpose) so
that no future session has to rediscover it. It is also the required input
for `convert`.

## Location

Save profiles in the **target project**, not in the skill folder:

```
<target project>/docs/excel-formats/<format-name>.json
```

One profile per document *format*, not per file — every "API仕様書" workbook
that follows the same layout shares one profile. Commit the profile to the
project repository so teammates' agents reuse it too.

## Full example

```json
{
  "profile_version": 1,
  "name": "api-spec",
  "description": "API仕様書。1行=1パラメータ、API単位でA列を縦結合",
  "file_pattern": "*API仕様書*.xlsx",
  "skip_sheets": {
    "表紙": "cover page, no data",
    "改訂履歴": "revision history",
    "デザイン見本": "design mock, shapes only - text not extractable"
  },
  "sheet_defaults": {
    "header_row": 3,
    "data_start_row": 4,
    "columns": {
      "A": { "field": "item_id",  "label": "項目番号", "derived": true },
      "B": { "field": "api_id",   "label": "API ID" },
      "C": { "field": "name",     "label": "API名" },
      "E": { "field": "method",   "label": "メソッド" },
      "F": { "field": "endpoint", "label": "エンドポイント" },
      "H": { "field": "updated",  "label": "更新日" }
    },
    "skip_row_if_empty": ["api_id"]
  },
  "sheets": {
    "API一覧":   { "role": "api-spec" },
    "単体テスト": {
      "role": "unit-test",
      "header_row": 2,
      "data_start_row": 3,
      "columns": {
        "B": { "field": "test_id",  "label": "No" },
        "C": { "field": "target",   "label": "対象機能" },
        "D": { "field": "steps",    "label": "テスト内容" },
        "E": { "field": "expected", "label": "期待結果" }
      }
    }
  },
  "notes": "Verified against 顧客管理API仕様書.xlsx with the user on 2026-07-09."
}
```

## Field reference

| Key | Meaning |
|---|---|
| `profile_version` | Always `1` for now. Readers ignore unknown keys, so the format is forward compatible. |
| `name` | Short kebab-case id; also the file name (`api-spec.json`). |
| `description` | One line, in the document's language, saying what one data row represents. |
| `file_pattern` | Glob matched against workbook file names to find the right profile. |
| `skip_sheets` | Map of sheet name → *reason* it is skipped. Recording the reason stops future sessions from re-investigating. |
| `sheet_defaults` | Layout used by every sheet that has no override in `sheets`. |
| `sheets` | Per-sheet entries. Each key overrides `sheet_defaults` **key-by-key** (an entry with only `role` inherits everything else). |
| `role` | The sheet's purpose: `api-spec`, `unit-test`, `integration-test`, `screen-spec`, `design-mock`, … Free vocabulary, but keep it consistent within a project. This is the sheet map that lets an agent jump straight to the right sheet in a multi-purpose workbook. |
| `header_row` | Excel row number (1-based) of the header line. Used for the drift check. |
| `data_start_row` | First data row. Defaults to `header_row + 1`. |
| `columns` | Column letter → `{ field, label, derived? }`. Unmapped columns are ignored by `convert` (they can still be read with `extract`). |
| `field` | Stable snake_case ASCII key used in JSON output. Never localized. |
| `label` | The header cell's original text, verbatim, in the document's language. Used for the drift check and as Markdown table headers. |
| `derived` | `true` when the column is computed by a formula from other cells (seen via `extract --show-formulas`). Its cached value is still read normally; the flag tells readers the value is redundant with other columns. |
| `skip_row_if_empty` | Fields that must all be empty for a row to be dropped as a non-data row (group separators, decoration). When omitted, rows with all mapped fields empty are dropped. |
| `notes` | Free text: verification date, quirks, open questions. |

## Rules

- **Never save an unverified profile.** `structure`'s `header-guess` is a
  hint; confirm the header row against 2+ real data rows, and confirm
  ambiguous column meanings with the user, before writing the file.
- **Update, don't fork.** When `convert` prints a header-drift WARNING,
  re-run the layout check (extract the header region), fix the profile in
  place, and note the change in `notes`. Only create a second profile when
  the project genuinely has two coexisting formats.
- Keep `field` values unique within one sheet config.
- A profile is data about a format, not about file contents — do not store
  extracted values in it.
