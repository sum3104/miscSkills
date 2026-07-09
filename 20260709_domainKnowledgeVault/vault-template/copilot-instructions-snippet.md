<!--
Copy the section below into the real project's agent instructions file:
  - GitHub Copilot: .github/copilot-instructions.md
  - Claude Code:    CLAUDE.md
  - Cursor:         an alwaysApply rule under .cursor/rules/
Do NOT place this file itself in the project; transcribe its content.
-->

## Knowledge capture

- After finishing a brainstorming or design session — right after the design
  document (spec / plan) has been written — invoke the `knowledge-capture`
  skill to record the domain terms and business rules discussed in the
  session into the Obsidian vault under `docs/knowledge/`.
- Also invoke `knowledge-capture` before ending any session that contained
  substantial domain discussion, even if no design document was produced.
- When recording knowledge, never modify files under `docs/specs/`,
  `docs/plans/`, or the ADR directory; they are immutable point-in-time
  artifacts that vault notes link back to.
- Distinguish confirmed knowledge from assumptions: unconfirmed items are
  `status: draft` with `[ASSUMPTION]` tags, and must be surfaced to the user
  as questions at the end of the capture.
