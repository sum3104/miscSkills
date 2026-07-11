---
name: local-exclude-setup
description: Configure local-only git exclusion of generated documentation artifacts (.superpowers/, docs/superpowers/, docs/knowledge/, docs/adr/, docs/.obsidian/) via .git/info/exclude, without touching the shared .gitignore. Use when the user wants to keep superpowers or knowledge-vault outputs out of commits in a team repository — e.g. "superpowersをgit除外でローカル運用にして", "exclude the vault from git locally", or "don't commit the docs the agent generates".
---

# Local-Exclude-Setup

Set up `.git/info/exclude` so that agent-generated documentation artifacts
stay out of `git status` and commits **in this clone only**. Unlike
`.gitignore`, `.git/info/exclude` is never committed, so teammates and the
shared repository are unaffected — the whole point is using the
superpowers / knowledge-vault workflow privately in a team repository.

Two principles govern everything below:

1. **Local only, shared files untouched.** Never edit `.gitignore` or any
   tracked file. All writes go to the repository's `info/exclude`, inside
   a marked block this skill owns.
2. **Exclude, never delete or untrack.** `.git/info/exclude` only hides
   *untracked* files. If a target path already has tracked files, warn and
   explain — never run `git rm --cached` or delete anything yourself.

## Step 1 — Confirm the scope

Present the default exclusion list and let the user trim or extend it:

```
.superpowers/        # subagent-driven-development progress ledger
docs/superpowers/    # specs and plans (current superpowers layout)
docs/knowledge/      # knowledge vault notes
docs/adr/            # ADRs
docs/.obsidian/      # Obsidian vault state
```

Projects on the older superpowers layout may need `docs/specs/` and
`docs/plans/` instead of `docs/superpowers/`.

State the trade-off explicitly before proceeding: excluding
`docs/knowledge/` and `docs/adr/` means the knowledge vault and ADRs are
**not shared with the team** — they exist only in this clone (and are lost
with it unless backed up). If the user wants "process private, knowledge
shared", drop those two entries and keep only `.superpowers/` and
`docs/superpowers/`.

## Step 2 — Check for already-tracked files (mandatory)

For each path in the agreed scope, run:

```
git ls-files -- <path>
```

If any hits: warn that `.git/info/exclude` does NOT affect files already
tracked by git, list the affected files, and explain that the user would
need `git rm --cached <file>` (keeps the working copy, stops tracking —
but the file's history remains visible to the team and its deletion will
appear in their next pull). Do not run it yourself; let the user decide
and proceed with the exclusion for future files either way.

## Step 3 — Write the exclude entries idempotently

- Resolve the target file with `git rev-parse --git-path info/exclude`
  (correct even in worktrees and submodules — never hardcode
  `.git/info/exclude`). Create the file if it does not exist.
- Manage the entries inside a marked block:

  ```
  # BEGIN domainKnowledgeVault local-exclude
  .superpowers/
  docs/superpowers/
  docs/knowledge/
  docs/adr/
  docs/.obsidian/
  # END domainKnowledgeVault local-exclude
  ```

- If the block already exists, **replace its contents** with the new
  scope; otherwise append the whole block. Never duplicate the block,
  never touch lines outside it.

## Step 4 — Verify and report

- Verify each entry with `git check-ignore -v <path>/x` (a hypothetical
  file under the path) and confirm the match comes from `info/exclude`.
- Report to the user:
  - which paths are now excluded, and the exclude file's location;
  - any still-tracked files found in Step 2 (they will keep appearing in
    `git status` when modified);
  - that this setting is per-clone: a fresh clone needs this skill run
    again;
  - how to undo: delete the marked block from the exclude file.

## Quality checklist (before reporting)

- [ ] `.gitignore` and all tracked files are untouched.
- [ ] The marked block appears exactly once in `info/exclude`.
- [ ] Tracked files under excluded paths were detected and reported, not removed.
- [ ] Every excluded path was verified with `git check-ignore -v`.
- [ ] The user was told the setting is local to this clone and how to undo it.
