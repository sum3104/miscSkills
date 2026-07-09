# Extraction guide — what to capture, what to skip, how to deduplicate

Shared by `knowledge-capture` (from conversations) and `knowledge-backfill`
(from existing specs/plans/ADRs). "Session" below means the conversation for
capture, or the document being read for backfill.

## Capture — domain terms (`knowledge/domain/`)

A term earns a note when the session did any of the following:

| Signal | Example |
|---|---|
| Defined a term | "「引当」とは在庫を注文に紐付けて確保することを指す" |
| Corrected usage | User: "それは『出荷』ではなく『出庫』です" — highest value; record both the correct meaning and the confusable term as an alias or a "not to be confused with" line |
| Disambiguated near-synonyms | "会員と顧客は別概念。顧客は法人を含む" |
| Introduced an actor/role | "承認者は課長職以上の別ユーザー" |
| Named a state or lifecycle | "注文は 受付→引当→出荷→完了 の状態を持つ" |

Not every noun is a domain term. Skip words used only in passing with their
everyday meaning.

## Capture — business rules (`knowledge/rules/`)

A statement earns a rule note when it constrains what the system or the
business may do, in one of these shapes:

- **Condition → outcome**: "注文合計が5,000円以上なら送料無料"
- **Exception**: "ただし沖縄・離島は対象外"
- **Threshold / limit**: "1回の注文は100点まで"
- **Permission**: "キャンセルは出荷前かつ本人または管理者のみ"
- **Temporal**: "月末締め、翌月10日払い"
- **Calculation**: "ポイントは税抜価格の1%を切り捨て"
- **External / regulatory constraint**: "特商法の表記が必須"

Also capture the **domain reason behind a rejected alternative** when the
reason is a business fact, not a technical one ("後払いを外したのは与信コスト
が単価に見合わないため" → that cost structure is domain knowledge).

## Do NOT capture

- **Technical / implementation decisions** — library choice, architecture,
  schema design. These belong in an ADR; suggest the ADR skill instead.
- **Task/session logistics** — plans for the day, TODO ordering, tooling talk.
- **Generic industry knowledge** the session did not confirm as applying to
  this project. If it was confirmed ("うちも標準の消費税区分に従う"), capture
  the confirmation, not a textbook.
- **Restatements** of knowledge an existing note already covers with nothing
  new — drop silently.

## Deduplication and updates

1. Search `knowledge/` for the candidate's canonical name, its synonyms, and
   its frontmatter `aliases` before creating anything.
2. Same concept, new detail → **update** the existing note; bump `updated`,
   append the new `source`.
3. Same concept, changed content (a threshold moved, an exception added that
   reverses prior behavior) → update the body **and** append the superseded
   statement to the note's `## History` with the date. Never silently
   overwrite a rule's previous value.
4. Same concept under a different name → keep one note, add the other name to
   `aliases`. Do not create alias stub notes.
5. Two sources that **conflict** and cannot be ordered in time → do not pick a
   winner. Record both under `## History`, set `status: draft`, and raise it
   in the report/questions batch.

## Granularity

- One concept or one rule per note. "Free shipping over ¥5,000, except
  remote islands, capped at 3 uses per month" is one rule with an exception
  and a limit — one note. "Free shipping rule" and "point calculation rule"
  are two notes.
- A cluster of related rules (e.g. everything about 送料) may get a short hub
  note that only links to its members.

## Status lifecycle

- `draft` — stated once, inferred, or assumed; every `[ASSUMPTION]` line
  forces `draft`.
- `confirmed` — the user explicitly confirmed it, or it comes verbatim from
  an approved spec/ADR.
- Flip `draft → confirmed` when the user answers the report's questions;
  remove the `[ASSUMPTION]` tags that the answer resolves.
