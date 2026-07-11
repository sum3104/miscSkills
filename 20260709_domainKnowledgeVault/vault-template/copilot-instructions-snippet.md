<!--
Copy the section below into the real project's agent instructions file:
  - GitHub Copilot: .github/copilot-instructions.md
  - Claude Code:    CLAUDE.md
  - Cursor:         an alwaysApply rule under .cursor/rules/
Do NOT place this file itself in the project; transcribe its content.
-->

## Decision & knowledge capture

- Right after a design document (spec / plan) has been written — whether
  under `docs/superpowers/specs|plans/` or `docs/specs|plans/` — invoke the
  `adr-capture` skill first, then the `knowledge-capture` skill. adr-capture
  records the session's ADR-worthy technical decisions as draft ADRs under
  `docs/adr/`; knowledge-capture then records the domain terms and business
  rules into the Obsidian vault under `docs/knowledge/` and can wiki-link
  the fresh ADRs.
- During plan-writing or implementation, if a decision deviates from or
  significantly extends the agreed design, invoke `adr-capture` before the
  session ends.
- Safety net: before ending any session that contained substantial
  technical-decision or domain discussion — even if no design document was
  produced — invoke `adr-capture` and/or `knowledge-capture` as applicable.
- Never modify files under the spec/plan directories; they are immutable
  point-in-time artifacts that ADRs and vault notes link back to. Existing
  ADRs are edited only by adr-capture's user-confirmed status flip
  (`superseded by ADR-NNNN`).
- Distinguish ratified content from drafts: new ADRs are `status: proposed`
  and unconfirmed vault notes are `status: draft` with `[ASSUMPTION]` tags;
  both must be surfaced to the user as confirmation questions at the end of
  the capture, and flipped to `accepted` / `confirmed` on approval.
