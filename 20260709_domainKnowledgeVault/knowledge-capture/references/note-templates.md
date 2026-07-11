# Note templates and conventions

Notes are written in the language of the conversation / source documents
(Japanese project → Japanese notes). The templates' fixed keys (frontmatter)
stay in English so they are machine-searchable.

## Common conventions

- **File name** = the canonical term or a short rule name, in the note
  language: `knowledge/domain/引当.md`, `knowledge/rules/送料無料の適用条件.md`.
- **Frontmatter keys** (all notes):
  - `type`: `domain-term` | `business-rule`
  - `status`: `draft` | `confirmed`
  - `aliases`: synonyms and easily-confused spellings, so future searches hit
  - `source`: list of origins — wiki-links to specs/plans/ADRs
    (vault-root-relative, e.g. `"[[plans/2026-07-01-shipping]]"`) and/or a
    session marker (`"brainstorming 2026-07-09"`)
  - `created` / `updated`: ISO dates
- **Links**: `[[wiki-links]]` between notes; vault root is `docs/`. Address
  specs and plans by the path that actually exists —
  `[[superpowers/specs/...]]`, `[[superpowers/plans/...]]` (current
  superpowers layout) or `[[specs/...]]`, `[[plans/...]]` (older layout) —
  and ADRs as `[[adr/...]]`.
- **Unconfirmed details**: tag the specific line with `[ASSUMPTION]`, keep
  `status: draft`.
- **History**: when a rule's content changes or sources conflict, append the
  superseded/conflicting statement under `## History` with a date — never
  silently overwrite.

## Template — domain term (`knowledge/domain/<term>.md`)

```markdown
---
type: domain-term
status: draft
aliases: []
source: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
# <用語>

<1〜3文の定義。会話・文書で述べられた内容のみ>

- 補足・境界: <何を含み、何を含まないか。紛らわしい用語との違い>
- 関連: [[domain/関連用語]] [[rules/この用語を使うルール]]
```

## Template — business rule (`knowledge/rules/<rule>.md`)

```markdown
---
type: business-rule
status: draft
aliases: []
source: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
# <ルール名>

- 条件: <いつ・何に適用されるか>
- 内容: <何がどうなる / 何をしてよい・してはいけない>
- 例外: <あれば。なければ「なし（確認済み）」か「不明」を明記>
- 経緯・理由: <なぜこのルールなのか。却下案の理由もここ>
- 関連: [[domain/使っている用語]] [[rules/関連ルール]]

## History
<!-- 変更時のみ。例: - 2026-07-09 閾値を3,000円→5,000円に変更（[[plans/...]]） -->
```

## Filled example

```markdown
---
type: business-rule
status: confirmed
aliases: [送料無料条件, free-shipping]
source: ["[[plans/2026-07-01-shipping]]", "brainstorming 2026-07-09"]
created: 2026-07-09
updated: 2026-07-09
---
# 送料無料の適用条件

- 条件: 1回の注文の商品合計が 5,000 円以上（税抜）
- 内容: 配送料を 0 円にする
- 例外: 沖縄・離島への配送は対象外（通常送料を適用）
- 経緯・理由: 平均注文単価 4,200 円を引き上げる施策。閾値は粗利シミュレーション
  に基づく（詳細は [[plans/2026-07-01-shipping]]）
- 関連: [[domain/商品合計]] [[rules/離島配送の扱い]]
```

## Home.md maintenance

`knowledge/Home.md` is a hand-maintained map of content: plain bulleted lists
of `[[domain/...]]` and `[[rules/...]]` links grouped by topic. When creating
a note, add it to the matching list (create a new topic group if none fits).
Do not turn Home.md into a copy of note contents — links only.
