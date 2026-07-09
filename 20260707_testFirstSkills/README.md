# design-to-test-cases スキル

設計書（Word / Excel / PDF / テキスト）だけがある状態から、テストファーストで
「どの画面・どの機能に、どのようなテストケースを作成すべきか」を検討し、
レビュー可能なテストケース一覧を作成するためのスキルです。

## 構成

```
design-to-test-cases/
├── SKILL.md                        # スキル本体（英語）: 6ステップのワークフロー
├── scripts/
│   └── extract_doc.py              # 省トークン抽出スクリプト（Python標準ライブラリのみ）
└── references/
    ├── test-perspectives.md        # テスト観点カタログ（画面/API/バッチ/マスタ/横断）
    └── output-template.md          # 成果物（テストケース一覧）のテンプレートと記述ルール
```

## 導入方法

Agent Skills オープン標準（SKILL.md + frontmatter）に従っているため、
お使いのエージェントのスキルディレクトリに `design-to-test-cases`
フォルダごとコピーしてください。

- Claude Code: `.claude/skills/design-to-test-cases/`（プロジェクト用）
  または `~/.claude/skills/design-to-test-cases/`（ユーザー共通）
- GitHub Copilot: `.github/skills/design-to-test-cases/`
  （`.claude/skills/` に置いたものも読み取れます）
- Cursor: `.cursor/skills/design-to-test-cases/`（プロジェクト用）
  または `~/.cursor/skills/design-to-test-cases/`（ユーザー共通）

## 設計上のポイント

- **省トークン**: Office/PDFファイルを直接読まず、`extract_doc.py` で
  「structure（見出し・シート一覧・ページ数）→ 必要箇所のみ extract」の
  2段階で読みます。出力には文字数上限（既定20,000字）があり、超過時は
  絞り込み方法を案内します。読んだ内容は inventory.md に集約し、
  同じ箇所を二度読みしません。
- **正確性優先**: テストケースは必ず設計書の記述またはユーザー回答に
  トレースされます。曖昧な点は Step 4 でまとめて質問し、回答なしで
  進める場合は `[ASSUMPTION]` タグ付きで仮定を明示します。
- **観点の網羅**: 権限（できる/できないの両面）、入力チェック、境界値、
  状態遷移、正常/異常のペアなどをカタログ化し、機能ごとに意識的に
  適用・除外します。同値分割・境界値分析・デシジョンテーブルで
  ケース数の膨張を抑えます。
- **成果物の言語**: SKILL.md は英語ですが、テストケース自体は
  設計書の言語（日本語の設計書なら日本語）で出力します。

## 制限事項

- 旧形式の `.doc` / `.xls` は非対応です（.docx / .xlsx への変換を依頼します）。
- PDFの抽出は `pypdf`（`pip install pypdf`）またはエージェント自身の
  PDF読み取り機能が必要です。docx / xlsx / テキストは追加インストール不要です。
