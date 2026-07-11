# ADR template and conventions

The default format is **MADR (Markdown Any Decision Records), required
sections only** — the de-facto standard whose structure makes the
considered options and their rejection reasons first-class. If the project
already has ADRs, their existing convention wins (see SKILL.md Step 1);
this template is the greenfield default.

ADR titles and bodies are written in the language of the conversation
(Japanese discussion → Japanese ADR). Section headings and frontmatter
keys stay in English so files remain machine-searchable and
MADR-compatible.

## Common conventions

- **File name**: `NNNN-title-with-dashes.md` — 4-digit sequential number +
  short lowercase-English dashed title (`0001-use-meilisearch.md`).
  Filenames stay ASCII even when the body is Japanese.
- **Frontmatter keys**:
  - `status`: `proposed` | `accepted` | `deprecated` | `superseded by ADR-NNNN`
  - `date`: ISO date of the decision (last update on change)
  - `source`: list of origins — wiki-links to the spec/plan the decision
    came from (vault-root-relative; use the path that actually exists:
    `"[[superpowers/specs/...]]"` for current superpowers,
    `"[[specs/...]]"` for older layouts) and/or a session marker
    (`"brainstorming 2026-07-11"`). This key is a local extension to MADR,
    shared with the knowledge vault's note format.
- **Links**: `[[wiki-links]]`; the vault root is `docs/`, so other ADRs
  are `[[adr/NNNN-...]]` and knowledge notes are `[[knowledge/...]]`.
- **One decision per file.** Three independent decisions → three ADRs.

## Template

```markdown
---
status: proposed
date: YYYY-MM-DD
source: []
---
# <決定のタイトル（会話の言語で）>

## Context and Problem Statement

<1〜3文。何を決める必要があったか。詳細は spec への wiki-link で示し、
復唱しない>

## Considered Options

- <選択肢 1（採用案）>
- <選択肢 2>
- <選択肢 3>

## Decision Outcome

Chosen option: "<選択肢 1>", because <採用理由。決め手になった事実>.

却下した選択肢とその理由:

- <選択肢 2>: <却下理由 — 必須。技術的理由はここに書く。業務的事実が理由
  なら1行で触れ、詳細は knowledge ノートへリンク>
- <選択肢 3>: <却下理由>

### Consequences

- Good: <この決定で楽になること>
- Bad: <この決定で難しくなること・引き受けたリスク>

## More Information

<!-- 任意セクション。内容があるときだけ。Decision Drivers（決定要因の箇条書き）
     もここではなく Considered Options の前に任意で置ける -->
- 関連: [[superpowers/specs/YYYY-MM-DD-topic-design]]
- Supersedes: [[adr/NNNN-old-decision]]（置換時のみ）
```

Optional MADR sections — `## Decision Drivers` (before Considered
Options) and `## More Information` — are included only when there is real
content for them. The full-MADR items `decision-makers` / `consulted` /
`informed` and the per-option `## Pros and Cons of the Options` tables are
deliberately omitted: in agent-session-born ADRs they go stale or empty.
The rejection reasons live inline in Decision Outcome instead.

## Filled example

```markdown
---
status: proposed
date: 2026-07-11
source: ["[[superpowers/specs/2026-07-11-product-search-design]]"]
---
# 商品検索エンジンに Meilisearch を採用する

## Context and Problem Statement

商品検索に日本語の全文検索とタイポ許容が必要になった。要件の詳細は
[[superpowers/specs/2026-07-11-product-search-design]] を参照。

## Considered Options

- Meilisearch
- Elasticsearch
- PostgreSQL + pg_bigm

## Decision Outcome

Chosen option: "Meilisearch", because 単一バイナリで運用負荷が最小であり、
日本語トークナイザとタイポ許容が組み込みのため.

却下した選択肢とその理由:

- Elasticsearch: 機能は十分だがクラスタ運用の専任者を置けない
- PostgreSQL + pg_bigm: 追加インフラ不要だがランキング調整とタイポ許容が
  要件を満たせない

### Consequences

- Good: 追加インフラはコンテナ1つで済み、インデックス定義もコードで管理できる
- Bad: 将来データ量が分散構成を要するレベルに達したら移行の再検討が必要

## More Information

- 関連: [[knowledge/rules/検索対象商品の範囲]]
```

## Post-ratification edits

An ADR is a point-in-time record. After it is `accepted`, do not rewrite
its body when things change — write a new ADR that supersedes it. The only
in-place edits ever made are the `status` flips described in
[adr-criteria.md](adr-criteria.md).
