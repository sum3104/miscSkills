# Output Template for the Test Case List

Write test cases in the language of the design documents. The example below
is Japanese because the design documents it derives from are Japanese; keep
the structure identical for any language. Default file name: `test-cases.md`.
If the user asks for CSV/Excel, keep the same columns.

## Required structure

````markdown
# テストケース一覧

- 作成日: <date>
- 入力設計書: <file list, with the sections actually used>
- 対象機能数: <n> / テストケース数: <n>
- ステータス凡例: ✅ 設計書で確認済み / ⚠ 要確認（[ASSUMPTION] は回答待ちの仮定に基づく）

## <機能名（例: メインメニュー画面）>

対象: <one-line description>  （出典: <file> §<section>）

| ID | 分類 | テストケース | 出典 | 状態 |
|----|------|--------------|------|------|
| MENU-001 | 権限 | メインメニュー画面では、一般ユーザーは閲覧画面を表示できること | 設計書A §2.1 | ✅ |
| MENU-002 | 権限 | メインメニュー画面では、一般ユーザーはマスタ編集画面を表示できないこと | 設計書A §2.1 | ✅ |
| MENU-003 | 権限 | メインメニュー画面では、管理者ユーザーは閲覧画面に加えてマスタ編集画面も表示できること | 設計書A §2.1 | ✅ |

## <機能名（例: WebAPI /login）>

| ID | 分類 | テストケース | 出典 | 状態 |
|----|------|--------------|------|------|
| LOGIN-001 | 認証・正常 | /loginエンドポイントでは、アクセストークンが有効であれば認証を行うこと | API仕様書 §3 | ✅ |
| LOGIN-002 | 認証・異常 | /loginエンドポイントでは、アクセストークンが無効であれば認証せず、エラーを返すこと | API仕様書 §3 | ✅ |
| LOGIN-003 | 認証・異常 | /loginエンドポイントでは、アクセストークンが失効している場合は401を返すこと [ASSUMPTION: 失効時の挙動は無効時と同一と仮定] | Q&A #2 | ⚠ |

## 未解決の質問・前提

1. <question> — 現在の仮定: <default> — 影響するケース: <IDs>
````

## Rules

- **ID**: short feature prefix + zero-padded number (`MENU-001`). Stable
  across revisions — never renumber existing IDs when adding cases.
- **分類 (category)**: pick from 初期表示 / 権限 / 入力チェック / 境界値 /
  遷移 / 正常 / 異常 / 状態 / 組合せ — or the closest equivalent in the
  output language. One category per case.
- **テストケース (test case)**: one sentence, one verifiable behavior,
  ending in a checkable claim (Japanese: 「〜こと」). Include the actor and
  the screen/endpoint in the sentence so it stands alone.
- **出典 (source)**: document + section/sheet/page, or `Q&A #n` for cases
  born from a user answer. No source → the case must not exist.
- **状態 (status)**: ✅ only when the design or a user answer states the
  behavior explicitly. Everything else is ⚠ with the assumption written
  inline as `[ASSUMPTION: ...]`.
- The final section must list every unresolved question, even if the user
  chose to proceed without answering — silent assumptions are the failure
  mode this skill exists to prevent.
