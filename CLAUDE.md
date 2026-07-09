# miscSkills リポジトリ規約

エージェント用スキル（Agent Skills 形式）の置き場。スキル一式ごとに
`YYYYMMDD_名前/` のサブフォルダを切る（例: `20260707_testFirstSkills/`）。

## 言語規約

- **README.md は日本語**で書く（リポジトリ直下・各スキルフォルダとも）。
  対象読者は人間の利用者。
- **スキルのプロンプトは英語**で書く。対象は `SKILL.md` と `references/`
  配下などエージェントが読むファイルすべて。
- スキルが生成する**成果物の言語は対象ドキュメントに従う**
  （日本語の設計書 → 日本語の成果物）。この規約は各 SKILL.md 内にも明記する。

## スキル形式の可搬性（エージェント間互換性）

- スキル本体は Agent Skills オープン標準
  （<https://agentskills.io/specification>）に従う: スキルルート直下に
  `SKILL.md` を置き、frontmatter は `name` と `description` のみを基本とする。
  補助ファイルは `scripts/` / `references/` / `assets/` に収める。
  この形式は Claude Code / GitHub Copilot / Cursor など主要エージェントが
  共通で読み取れるため、特定エージェント固有の frontmatter
  （Claude Code の `allowed-tools` など）を使う場合は、可搬性が下がる旨を
  該当スキルの README に明記する。
- 各スキルフォルダの README には「導入方法」節を設け、以下の配置パスを
  列挙する（`YYYYMMDD_名前/` 配下は原本置き場で、利用時はそこからコピーする）:
  - Claude Code: `.claude/skills/<name>/`（プロジェクト）または
    `~/.claude/skills/<name>/`（ユーザー共通）
  - GitHub Copilot: `.github/skills/<name>/`（`.claude/skills/` も読み取れる）
  - Cursor: `.cursor/skills/<name>/`（ユーザー共通は `~/.cursor/skills/`）
- `.cursor/rules/*.mdc` は Cursor 専用の常時適用ルール形式であり、
  SKILL.md 標準とは別物（他エージェントには移植できない）。
  `repo-conventions.mdc` はこちらに属する。スキルを `.mdc` 形式で
  書かないこと。

## 作業終了時のコミット前チェック（必須）

作業を終えるとき・コミットする前に、`git status` で**未追跡ファイルを含めて**
差分を確認し、GitHub にコミットすべきでないファイルが混ざっていないか
チェックすること。混ざっていた場合は `.gitignore` に追加するか削除し、
何を除外したかをユーザーに報告する。

チェック対象の例:

- スキルのランタイム出力・作業ファイル（`test-case-work/` など）
- 検証・ドライランで作った一時ファイル（スクラッチは本来リポジトリ外に置く）
- 秘密情報（`.env`、鍵ファイル、トークン、認証情報を含むファイル）
- 個人情報・業務データを含むテスト入力（設計書の docx / xlsx / pdf など）
- エディタ・ツールのローカル状態（Obsidian の `workspace.json`、
  `.cursor/` 配下の rules 以外、OS のゴミファイル）
- 大きなバイナリ

`.gitignore` は `.cursor/rules/` だけを共有対象として許可している
（それ以外の `.cursor/*` はローカル状態なので除外）。この構造を壊さないこと。

## Cursor との共用

Cursor 用のルールは `.cursor/rules/repo-conventions.mdc` にあり、内容は
この CLAUDE.md を参照する形で一元化している。規約を変えるときはこの
ファイルだけを編集すればよい。
