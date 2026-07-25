---
name: "git-workflows"
description: "Git beyond the basics: interactive rebase, bisect, history surgery, recovering lost work, and untangling messy branch states. Use when the user asks to clean up commits before a PR, find which commit broke something, undo a bad merge or rebase, split or combine commits, recover deleted work, or fix a detached HEAD. Trigger on rebase, bisect, cherry-pick, reflog, squash, amend, force push, or I messed up my branch."
---

# Git Workflows

History surgery, regression hunting, and recovery. Complements `gh-fix-ci` (which handles failing GitHub Actions checks).

## Not in scope

Repo hosting administration (branch protection, permissions), monorepo tooling, git LFS setup, and CI configuration. Routine add/commit/push needs no skill.

## First rule of recovery: almost nothing is lost

Committed work survives branch deletion, bad rebases, and hard resets for ~90 days. Before declaring data loss:

```bash
git reflog                    # every position HEAD has held
git reflog show <branch>      # every position a branch has held
git branch rescue <sha>       # pin the good state before doing anything else
git fsck --lost-found         # dangling commits not in any reflog
```

Uncommitted-but-staged work: `git fsck --unreachable | grep blob` can still find the blobs. Uncommitted, unstaged work is the one thing actually gone.

**Before any destructive operation** (`reset --hard`, `rebase`, `filter-repo`): `git branch backup-$(date +%s)` costs nothing and turns every mistake into a checkout.

## Cleaning up a branch before a PR

Goal: commits that each build and tell one story.

```bash
git rebase -i $(git merge-base main HEAD)
```

- `squash`/`fixup` the "wip", "typo", "address review" commits into their parent.
- `reword` messages to say why, not what.
- `edit` + `git reset HEAD^` to split a commit doing two things; stage and commit in pieces (`git add -p`).
- During ongoing review, prefer `git commit --fixup <sha>` then `git rebase -i --autosquash` at the end, so reviewers can see what changed between pushes.
- After any rebase of a pushed branch: `git push --force-with-lease` (never bare `--force`; the lease aborts if someone else pushed).

Note: some agent environments can't run interactive rebase. The non-interactive equivalent for "squash everything since main into one commit": `git reset --soft $(git merge-base main HEAD) && git commit`.

## Finding the commit that broke it

```bash
git bisect start
git bisect bad                # current state is broken
git bisect good v1.4          # last known good ref
# git checks out midpoints; test each and mark:
git bisect good|bad|skip
git bisect reset              # when done
```

Automate when the failure is scriptable: `git bisect run npm test` (or any command exiting 0 for good, non-zero for bad, 125 for skip). Bisect over ~1000 commits is ~10 tests; always prefer it over reading diffs.

Cheaper first checks: `git log -S "someString" --oneline` (when did this string appear/disappear), `git log -L :funcName:path/file.js` (history of one function), `git blame -w -C path/file` (ignore whitespace, follow moves).

## Undoing things: pick the right tool

| Situation | Command |
|---|---|
| Fix message/contents of last unpushed commit | `git commit --amend` |
| Unstage a file | `git restore --staged <f>` |
| Discard local edits to a file | `git restore <f>` (destructive) |
| Undo last commit, keep changes staged | `git reset --soft HEAD^` |
| Undo a pushed commit safely | `git revert <sha>` (new inverse commit) |
| Undo a pushed merge | `git revert -m 1 <merge-sha>` |
| Rebase went wrong | `git rebase --abort`, or after the fact `git reset --hard <sha-from-reflog>` |
| Committed to the wrong branch | `git branch right-branch && git reset --hard origin/wrong-branch` then switch |
| Need one commit from another branch | `git cherry-pick <sha>` (`-x` to record origin) |

Rule: `reset` rewrites your branch (fine while unpushed), `revert` adds history (required once shared).

## Untangling common messes

- **Detached HEAD with work on it:** `git branch save-me` right there, then switch back.
- **Merge conflict panic:** `git merge --abort` / `git rebase --abort` returns to the pre-attempt state; nothing is committed yet.
- **Accidentally committed a secret:** rotating the secret comes first; then `git filter-repo` (not filter-branch) to purge history, force-push, and accept that forks/clones still have it.
- **Diverged from remote after someone force-pushed:** `git fetch` then `git reset --hard origin/<branch>` (stash or branch local work first).
- **Huge accidental file blocking push:** `git rm --cached <file>`, add to `.gitignore`, amend or rebase it out of the offending commits.
