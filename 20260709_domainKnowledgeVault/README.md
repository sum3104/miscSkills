# domainKnowledgeVault スキル

brainstorming・設計セッション中に出てくる**ドメイン知識・業務ルール・技術的
意思決定**を、プロジェクト内の git 管理された Obsidian vault と ADR に自動で
蒸留・記録するためのスキル一式です。superpowers によるスペック駆動開発サイクル
（brainstorm → spec/plan 自動生成）を補完し、「会話の中にしか残らない知識」を
引き継ぎ可能な資産にします。

以前は ADR（Architecture Decision Record）の作成を手動としていましたが、
「人間が重要な決定だと気付かないまま流れる」取りこぼしを防ぐため、
`adr-capture` スキルにより **ADR も自動で draft 作成**するようになりました。
自動生成された ADR は `status: proposed` で書かれ、ユーザーの承認で
`accepted` に昇格します（勝手に確定はしません）。

MCP は使いません。vault も ADR もただの Markdown なので、エージェントは
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
├── adr-capture/                         # 新スキル: 技術的意思決定を draft ADR として自動記録
│   ├── SKILL.md                         # （英語）5ステップのワークフロー
│   └── references/
│       ├── adr-criteria.md              # ADR 化の基準（ノイズ抑制）、knowledge との境界
│       └── adr-template.md              # MADR 準拠テンプレートと記述規約
├── knowledge-backfill/                  # 補助スキル: 既存の specs/plans/ADR から遡及抽出
│   └── SKILL.md                         # （英語）knowledge-capture の references を共用
├── local-exclude-setup/                 # 任意: 生成物を git 管理から外すローカル設定
│   └── SKILL.md                         # （英語）.git/info/exclude + commit ガードを安全に設定
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
  エージェント自身が蒸留して書き込む」方式を採ります。
  Agent Skills 標準（SKILL.md）なので Claude Code / GitHub Copilot / Cursor の
  いずれでも動きます。
- **docs/ を vault ルートにする**: superpowers が生成する plans / specs や
  ADR を移動せず、蒸留ノートから `[[wiki-link]]` で直接参照できます。
  グラフビューにも乗ります。superpowers の出力先は世代によって
  `docs/superpowers/specs|plans/`（現行）と `docs/specs|plans/`（旧）が
  あるため、スキルは実在する方を自動検出します。
- **specs / plans は不変**: 「その時点の成果物」として書き換えません。
  生きた知識（用語・ルールの現在の姿）は vault 側が持ち、出典として
  specs / plans にリンクします。ルールが変わったら上書きではなく
  `## History` に旧値を残します。
- **ADR は proposed → accepted のライフサイクル**: `adr-capture` が自動生成
  する ADR は必ず `status: proposed` で、記録の最後に確認質問として提示され
  ます。承認で `accepted` へ。決定が置き換わった場合も旧 ADR の本文は
  書き換えず、新 ADR + `superseded by ADR-NNNN` のステータス変更
  （ユーザー確認後のみ）で履歴を残します。knowledge ノートの
  draft → confirmed と対になる設計です。
- **ADR のノイズ抑制**: すべての選択を ADR にはしません。「影響が大きい／
  覆しにくい／横断的／複数案から選択した／既存設計からの逸脱」という基準
  （`adr-criteria.md`）を満たす決定だけを記録します。全部書くと何も
  見つけられなくなるためです。
- **ADR フォーマットは MADR 準拠（必須部分）**: デファクト標準の MADR
  （Context and Problem Statement / Considered Options / Decision Outcome /
  Consequences、ファイル名 `NNNN-title-with-dashes.md`）を採用。標準見出しは
  LLM の学習知識・既存ツールとの互換を活かせます。却下案とその理由が必須
  構造に入っているのが採用理由です（spec には採用案しか残らないため）。
  既存 ADR があるプロジェクトではその規約を踏襲します。見出し・frontmatter
  キーは英語固定、タイトル・本文は会話の言語、ファイル名は英語ダッシュ
  区切りです。
- **正確性優先**: 会話・文書で述べられていない知識は創作しません。
  未確認の内容は `status: draft` + `[ASSUMPTION]` タグで区別し、
  記録の最後に質問としてまとめて提示します（design-to-test-cases と同じ思想）。
- **`.git/info/exclude` によるローカル除外（任意）**: チーム開発の
  リポジトリで superpowers / vault の生成物をコミットしたくない場合、
  `local-exclude-setup` スキルが `.git/info/exclude`（コミットされない
  クローン限定の除外設定）に生成物パスを登録します。共有の `.gitignore` を
  汚しません。ただし**追跡済みのファイルには効かない**（スキルが検出して
  警告します）ことと、クローンし直すたびに再設定が必要なことに注意。
- **commit ガード + ローカル instructions（除外運用時）**: superpowers の
  brainstorming は spec 保存直後に「Commit the design document to git」と
  指示するため、除外設定と衝突します（`git add` が失敗し、エージェントが
  git のヒントに従って `git add -f` すると除外が黙って無効化され痕跡が
  残る）。そこで `local-exclude-setup` は、**それ自体も除外された
  ローカル専用 instructions ファイル**（Claude Code: `CLAUDE.local.md`、
  Cursor: `.cursor/rules/dkv-local.mdc`）を作成し、
  「除外パス配下の commit 指示はスキップ / `git add -f` 禁止」という
  ガード文を書き込みます。ガードを共有の instructions に書くとそれ自体が
  痕跡になり、チームメンバーのエージェントまで commit をスキップして
  しまうため、必ずローカルファイル側に置きます。
- **Copilot のローカル instructions は2方式から選択**: VS Code Copilot では
  `.github/copilot-instructions.md` が**全チャットリクエストに無条件添付**
  されるのに対し、`*.instructions.md`（`applyTo: "**"`）は**作業対象の
  ファイル・タスクに基づく動的添付**であり、応答言語やスキル自動起動の
  ようなセッション全体の指示には効きが弱いことがあります。そこで
  `local-exclude-setup` は「チームが `.github/copilot-instructions.md` や
  `AGENTS.md` を共有している / する予定があるか」を確認し、
  **共有しない場合**は未追跡の `.github/copilot-instructions.md` を作成して
  除外リストに追加します（常時適用で確実。ただしチームが後日同名ファイルを
  コミットすると `git pull` が untracked 衝突のエラーで停止する——
  `.git/info/exclude` ではこの衝突は防げません。ローカルファイルを退避して
  pull すれば復旧できます）。**共有している / 不明な場合**は従来どおり
  `.github/instructions/dkv-local.instructions.md`（`applyTo: "**"`）を
  使います（衝突リスクゼロだが動的添付のため効きが弱め。起動されなかったら
  スキル名で明示的に依頼する運用）。

## 導入方法（実プロジェクト側の作業）

1. **スキルの配置**: `knowledge-capture/`・`adr-capture/`・
   `knowledge-backfill/` の3フォルダを、お使いのエージェントのスキル
   ディレクトリに**並べて**コピーします（backfill が capture の references を
   相対パスで参照するため、同じ親ディレクトリに置くこと）。
   `local-exclude-setup/` は任意で、単独でも動きます。
   - Claude Code: `.claude/skills/`（ユーザー共通は `~/.claude/skills/`）
   - GitHub Copilot: `.github/skills/`（`.claude/skills/` も読み取れます）
   - Cursor: `.cursor/skills/`（ユーザー共通は `~/.cursor/skills/`）
2. **vault の配置**: `vault-template/` の中身（`copilot-instructions-snippet.md`
   を除く）をプロジェクトの `docs/` にコピーします。既存の
   `docs/superpowers/` や `docs/specs|plans/` はそのままで構いません。
   Obsidian で `docs/` を「vault として開く」だけで使えます。
   `docs/adr/` は事前に作る必要はありません（`adr-capture` が初回に作成を
   提案します。既に別の場所で ADR を管理している場合はそちらを踏襲します）。
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
   design doc を書き終えたタイミングで `adr-capture` → `knowledge-capture` が
   この順に自動で起動するようになります（フック・MCP 不要）。
   **チームのリポジトリに痕跡を残したくない場合は、共有 instructions への
   転記はせず**、手順 6 の `local-exclude-setup` が作成するローカル専用
   instructions ファイルにスニペットを書き込みます（スキルが対話で
   セットアップします）。
5. **初回のみ — バックフィル**: 既存の specs / plans / ADR が溜まっている
   場合は、`knowledge-backfill` スキルを一度起動して vault に初期投入します
   （例:「knowledge-backfill で既存ドキュメントから知識を抽出して」）。
6. **任意 — git 除外のローカル設定**: チームのリポジトリに生成物を
   コミットしたくない場合は、エージェントに
   「superpowersをgit除外でローカル運用にして」と依頼すると
   `local-exclude-setup` が起動します。デフォルトの除外対象は
   `.superpowers/` `docs/superpowers/` `docs/knowledge/` `docs/adr/`
   `docs/.obsidian/` で、対話で調整できます（例:「知識はチーム共有、
   作業過程だけローカル」なら `.superpowers/` と `docs/superpowers/` のみ）。
   あわせてローカル専用の instructions ファイル（自動起動スニペット+
   commit ガード入り。それ自体も除外対象に追加）をセットアップするため、
   superpowers の「design doc を commit せよ」という指示と除外設定が
   衝突しません。Copilot の場合は「チームが copilot-instructions.md を
   共有しているか」を確認され、共有していなければ常時適用で確実な
   未追跡 `.github/copilot-instructions.md` 方式が選べます
   （「設計上のポイント」参照）。

## 運用フロー

```
brainstorming ──▶ design doc (spec/plan) 生成      ← superpowers（従来どおり）
                           │
                           ▼
                 adr-capture が自動起動             ← copilot-instructions 経由
                 技術的意思決定を docs/adr/ に
                 draft ADR（status: proposed）として作成
                           │
                           ▼
                 knowledge-capture が自動起動
                 docs/knowledge/ にノート作成・更新
                 （新しい ADR にも wiki-link）
                           │
                           ▼
                 ユーザーが確認質問に回答
                 proposed → accepted / draft → confirmed
```

- 実装中に合意済み設計から逸脱する決定があった場合も、セッション終了前に
  `adr-capture` が起動します（design doc なしの濃い議論にも
  セーフティネットあり）。
- ADR・ノートの本文は会話の言語（日本語の議論なら日本語）で書かれます。
- 同じ概念のノートは重複作成せず更新されます。ルールの内容が変わった場合は
  `## History` に旧値と日付が残ります。ADR は本文を書き換えず、新 ADR で
  置き換えます（supersede）。
- 記録のたびに「作成/更新した一覧」と「確認質問」が提示されるので、
  その場で答えると `draft`/`proposed` が `confirmed`/`accepted` に昇格します。

## 制限事項

- 自動起動は instructions ファイルの指示に依存します。エージェントが指示を
  読み飛ばした場合は「知識を記録して」「ADRを記録して」と明示的に依頼して
  ください（各 SKILL.md の description にもトリガーを記載済み）。特に
  Copilot の `.instructions.md`（`applyTo: "**"`）方式は動的添付のため、
  ファイル編集を伴わないターンでは指示自体が添付されないことがあり、
  応答言語の指定や自動起動が `copilot-instructions.md` 記載時より
  効きにくくなります。常時適用が必要なら、`local-exclude-setup` で
  未追跡 `.github/copilot-instructions.md` 方式を選んでください。
- ADR 化基準（`adr-criteria.md`）を満たさない些末な決定は記録されません — 
  これは仕様です（ノイズ抑制）。基準未満でも残したい決定は明示的に
  依頼してください。
- vault の品質は会話の明示性に依存します。暗黙の前提はノートにならないか
  `[ASSUMPTION]` 付きの draft になります — これは仕様です（創作防止）。
- `knowledge-backfill` はドキュメントの日付順（ファイル名 frontmatter、
  なければ git の初回コミット日）で処理します。日付が取れない場合は
  ユーザーに確認します。
- `local-exclude-setup` の除外は**このクローン限定**です。追跡済みの
  ファイルには効かず（検出して警告します）、クローンし直したら再設定が
  必要です。`docs/knowledge/`・`docs/adr/` を除外した場合、知識と ADR は
  チームに共有されません（バックアップも各自の責任になります）。
- 除外運用時は commit ガードにより、superpowers 等が指示する spec / plan
  など**除外パス配下のドキュメントの commit ステップはスキップ**されます
  （ソースコードの commit は通常どおり）。これは仕様です — commit して
  しまうとファイルが追跡され、チームのリポジトリに痕跡が残るためです。
