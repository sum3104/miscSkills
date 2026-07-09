# domainKnowledgeVault スキル

brainstorming・設計セッション中に出てくる**ドメイン知識・業務ルール**を、
プロジェクト内の git 管理された Obsidian vault に自動で蒸留・記録するための
スキル一式です。superpowers によるスペック駆動開発サイクル
（brainstorm → spec/plan 自動生成、重要な意思決定は手動 ADR）を補完し、
「会話の中にしか残らない知識」を引き継ぎ可能な資産にします。

MCP は使いません。vault はただの Markdown フォルダなので、エージェントは
通常のファイル操作だけで読み書きできます。

## 構成

```
20260709_domainKnowledgeVault/
├── README.md                            # このファイル
├── knowledge-capture/                   # メインスキル: セッション内で会話から知識を蒸留
│   ├── SKILL.md                         # （英語）5ステップのワークフロー
│   └── references/
│       ├── extraction-guide.md          # 何を抽出するか/しないか、重複排除・更新ルール
│       └── note-templates.md            # ノートのテンプレートと記述規約
├── knowledge-backfill/                  # 補助スキル: 既存の specs/plans/ADR から遡及抽出
│   └── SKILL.md                         # （英語）knowledge-capture の references を共用
└── vault-template/                      # 実プロジェクトの docs/ にコピーする雛形
    ├── .obsidian/app.json               # 最小限の Obsidian 設定
    ├── knowledge/
    │   ├── Home.md                      # MOC（ノートへのリンク集）
    │   ├── domain/                      # ドメイン用語: 1概念1ノート
    │   └── rules/                       # 業務ルール: 1ルール1ノート
    └── copilot-instructions-snippet.md  # 自動起動用の追記文面（下記参照）
```

## 設計上のポイント

- **会話ログはパースしない**: Copilot / Claude Code のセッションログは
  非公開形式で変更されやすく、パースは脆い上に追加の LLM 呼び出しコストが
  かかります。代わりに「会話コンテキストがまだ生きているセッション内で、
  エージェント自身が蒸留して vault に書き込む」方式を採ります。
  Agent Skills 標準（SKILL.md）なので Claude Code / GitHub Copilot / Cursor の
  いずれでも動きます。
- **docs/ を vault ルートにする**: superpowers が生成する plans / specs や
  ADR を移動せず、蒸留ノートから `[[wiki-link]]` で直接参照できます。
  グラフビューにも乗ります。
- **specs / plans は不変**: 「その時点の成果物」として書き換えません。
  生きた知識（用語・ルールの現在の姿）は vault 側が持ち、出典として
  specs / plans にリンクします。ルールが変わったら上書きではなく
  `## History` に旧値を残します。
- **正確性優先**: 会話・文書で述べられていない知識は創作しません。
  未確認の内容は `status: draft` + `[ASSUMPTION]` タグで区別し、
  記録の最後に質問としてまとめて提示します（design-to-test-cases と同じ思想）。

## 導入方法（実プロジェクト側の作業）

1. **スキルの配置**: `knowledge-capture/` と `knowledge-backfill/` の
   2フォルダを、お使いのエージェントのスキルディレクトリに**並べて**
   コピーします（backfill が capture の references を相対パスで参照するため、
   同じ親ディレクトリに置くこと）。
   - Claude Code: `.claude/skills/`（ユーザー共通は `~/.claude/skills/`）
   - GitHub Copilot: `.github/skills/`（`.claude/skills/` も読み取れます）
   - Cursor: `.cursor/skills/`（ユーザー共通は `~/.cursor/skills/`）
2. **vault の配置**: `vault-template/` の中身（`copilot-instructions-snippet.md`
   を除く）をプロジェクトの `docs/` にコピーします。既存の `docs/plans/` や
   `docs/specs/` はそのままで構いません。Obsidian で `docs/` を
   「vault として開く」だけで使えます。
3. **.gitignore への追記**: Obsidian のウィンドウ状態はコミット不要です。
   ```gitignore
   docs/.obsidian/workspace.json
   ```
4. **自動起動の設定**: `vault-template/copilot-instructions-snippet.md` の
   内容（英語のセクション）を、プロジェクトの
   `.github/copilot-instructions.md`（Claude Code なら `CLAUDE.md`、
   Cursor なら `.cursor/rules/` の alwaysApply ルール）に
   **転記**します。ファイル自体を置くのではなく中身をコピーしてください。
   エージェントは毎セッションこの instructions を読むため、brainstorming で
   design doc を書き終えたタイミングで knowledge-capture が自動で起動する
   ようになります（フック・MCP 不要）。
5. **初回のみ — バックフィル**: 既存の specs / plans / ADR が溜まっている
   場合は、`knowledge-backfill` スキルを一度起動して vault に初期投入します
   （例:「knowledge-backfill で既存ドキュメントから知識を抽出して」）。

## 運用フロー

```
brainstorming ──▶ design doc (spec/plan) 生成   ← superpowers（従来どおり）
      │                    │
      │                    ▼
      │          knowledge-capture が自動起動   ← copilot-instructions 経由
      │                    │
      ▼                    ▼
 重要な意思決定 ─▶ ADR（手動、従来どおり）    docs/knowledge/ にノート作成・更新
                                               │
                                               ▼
                                    ユーザーが draft 項目を確認 → confirmed へ
```

- ノートは会話の言語（日本語の議論なら日本語）で書かれます。
- 同じ概念のノートは重複作成せず更新されます。ルールの内容が変わった場合は
  `## History` に旧値と日付が残ります。
- 記録のたびに「作成/更新したノート一覧」と「未確認事項の質問」が提示される
  ので、その場で答えると `draft` が `confirmed` に昇格します。

## 制限事項

- 自動起動は instructions ファイルの指示に依存します。エージェントが指示を
  読み飛ばした場合は「知識を記録して」と明示的に依頼してください
  （skill の description にもトリガーを記載済み）。
- vault の品質は会話の明示性に依存します。暗黙の前提はノートにならないか
  `[ASSUMPTION]` 付きの draft になります — これは仕様です（創作防止）。
- `knowledge-backfill` はドキュメントの日付順（ファイル名 frontmatter、
  なければ git の初回コミット日）で処理します。日付が取れない場合は
  ユーザーに確認します。
