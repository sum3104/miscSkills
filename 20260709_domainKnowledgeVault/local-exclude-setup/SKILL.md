---
name: local-exclude-setup
description: Configure local-only git exclusion of generated documentation artifacts (.superpowers/, docs/superpowers/, docs/knowledge/, docs/adr/, docs/.obsidian/) via .git/info/exclude, without touching the shared .gitignore — and set up a local-only agent instructions file carrying a commit guard, so workflows that instruct commits of those artifacts (e.g. superpowers' "Commit the design document") are skipped instead of forced with git add -f. Use when the user wants to keep superpowers or knowledge-vault outputs out of commits in a team repository — e.g. "superpowersをgit除外でローカル運用にして", "exclude the vault from git locally", or "don't commit the docs the agent generates".
---

# Local-Exclude-Setup

Set up `.git/info/exclude` so that agent-generated documentation artifacts
stay out of `git status` and commits **in this clone only**. Unlike
`.gitignore`, `.git/info/exclude` is never committed, so teammates and the
shared repository are unaffected — the whole point is using the
superpowers / knowledge-vault workflow privately in a team repository.

Exclusion alone is not enough: some workflows explicitly instruct the agent
to commit the artifacts (e.g. superpowers' brainstorming skill says "Commit
the design document to git"). `git add` on an excluded path fails with a
hint to use `-f`, and an agent that follows that hint silently defeats the
exclusion — the file becomes tracked and leaves a trace. So this skill also
installs a **commit guard** in a **local-only instructions file** (Step 4).

Three principles govern everything below:

1. **Local only, shared files untouched.** Never edit `.gitignore` or any
   tracked file. All writes go to the repository's `info/exclude`, inside
   a marked block this skill owns, plus one local instructions file that is
   itself excluded.
2. **Exclude, never delete or untrack.** `.git/info/exclude` only hides
   *untracked* files. If a target path already has tracked files, warn and
   explain — never run `git rm --cached` or delete anything yourself.
3. **Instructions stay local too.** Never write the commit guard or the
   vault auto-trigger snippet into a shared or tracked instructions file —
   that would itself leave a trace, and would make teammates' agents skip
   commits they actually want.

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
`docs/plans/` instead of `docs/superpowers/`. Step 4 will add one more
entry — the local instructions file — once its path is decided.

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

## Step 4 — Local instructions file with commit guard

1. **Pick the file.** Ask which agent(s) are used in this clone (skip the
   question if the session makes it obvious) and use the dedicated
   local-only file per agent:

   | Agent          | Local instructions file                        | Required frontmatter    |
   |----------------|------------------------------------------------|-------------------------|
   | GitHub Copilot | `.github/instructions/dkv-local.instructions.md` | `applyTo: "**"`       |
   | Claude Code    | `CLAUDE.local.md`                              | none                    |
   | Cursor         | `.cursor/rules/dkv-local.mdc`                  | `alwaysApply: true`     |

   **Never create `.github/copilot-instructions.md` yourself.** It is the
   team's shared filename; if the team later commits one, a local untracked
   copy makes their `git pull` / `git checkout` fail with "untracked
   working tree file would be overwritten". Exception: if an **untracked**
   `.github/copilot-instructions.md` already exists locally (the user made
   it by hand), offer to append to it and exclude it instead of creating a
   new file. If the file with that name is *tracked*, leave it alone and
   use the dedicated file above.

2. **Write the content.** Into the chosen file, write:
   - the domainKnowledgeVault auto-trigger section (the content of
     `vault-template/copilot-instructions-snippet.md`) — first ask whether
     it is already transcribed in a shared instructions file; if so, skip
     it here to avoid double-triggering;
   - the commit guard below, with the path list matching the scope agreed
     in Step 1 plus this instructions file itself:

   ```markdown
   ## Local-only paths — commit guard

   The following paths are excluded via `.git/info/exclude` and must stay
   out of git in this clone:

   - .superpowers/
   - docs/superpowers/
   - docs/knowledge/
   - docs/adr/
   - docs/.obsidian/
   - <path of this instructions file>

   Rules:

   - Never commit, `git add`, or push files under these paths.
   - Never use `git add -f` on them — it silently defeats the exclusion
     and the file becomes tracked.
   - When a workflow instructs you to commit such a file (e.g.
     superpowers' "Commit the design document to git"), skip that commit
     step and continue the workflow. Commits of ordinary source code are
     unaffected.
   - If a file under these paths ever shows up as staged, unstage it
     (`git restore --staged <file>`) before committing.
   ```

3. **Exclude the file itself.** Add the local instructions file's path to
   the marked block (re-apply Step 3's replace logic — the block must
   still appear exactly once).

## Step 5 — Verify and report

- Verify each entry with `git check-ignore -v <path>/x` (a hypothetical
  file under the path) and confirm the match comes from `info/exclude`.
  Verify the local instructions file itself the same way (its literal
  path, no `/x` suffix).
- Report to the user:
  - which paths are now excluded, and the exclude file's location;
  - the local instructions file's path, and that it carries the commit
    guard (workflow commit steps for excluded paths will be skipped;
    source-code commits are unaffected);
  - any still-tracked files found in Step 2 (they will keep appearing in
    `git status` when modified);
  - that this setting is per-clone: a fresh clone needs this skill run
    again;
  - how to undo: delete the marked block from the exclude file and the
    local instructions file.

## Quality checklist (before reporting)

- [ ] `.gitignore` and all tracked files are untouched.
- [ ] The marked block appears exactly once in `info/exclude`.
- [ ] Tracked files under excluded paths were detected and reported, not removed.
- [ ] Every excluded path was verified with `git check-ignore -v`.
- [ ] The commit guard and snippet were written only to a local, excluded
      instructions file — never to a tracked or shared one.
- [ ] The local instructions file itself is listed in the marked block and
      passes `git check-ignore -v`.
- [ ] `.github/copilot-instructions.md` was not newly created by this skill.
- [ ] The user was told the setting is local to this clone and how to undo it.
