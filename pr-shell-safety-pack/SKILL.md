---
name: pr-shell-safety-pack
description: Apply Windows-safe GitHub, PowerShell, npm, time-zone, and PR creation tactics for Codex sessions. Use when creating repos or PRs, pushing branches, writing multiline PR bodies, running Node/npm commands on Windows, handling PowerShell quoting, using local review windows, or falling back from GitHub connector misses to `gh`.
---

# PR And Shell Safety Pack

Use this skill to avoid recurring Windows and GitHub workflow failures while keeping changes reviewable.

## Workflow

1. Prefer Windows-stable commands.
   - Use `npm.cmd` for package scripts when `npm` or `npm.ps1` behavior is brittle.
   - Use direct `node` scripts for syntax checks when PowerShell quoting fights inline commands.
   - Prefer simple `Select-String` patterns over dense one-liners when verifying text.

2. Create repos in two steps.
   - Use `gh repo create <name> --private`.
   - Add the remote and push from the checkout afterward.
   - If Git reports dubious ownership, add the exact checkout path to `safe.directory` only after confirming it is the intended repo.

3. Write PR bodies through files.
   - Put multiline PR bodies in a temp markdown file.
   - Use `gh pr create --body-file <file>`.
   - Avoid inline multiline bodies in PowerShell.

4. Handle time zones with host-compatible IDs.
   - For PowerShell conversions on this host, use `Eastern Standard Time` rather than IANA `America/New_York`.
   - Still report human-readable windows as America/New_York when that is the user's requested language.

5. Fall back from connector misses deliberately.
   - If a GitHub connector cannot see a repo that `gh` can inspect, switch to lighter `gh pr view`, `gh pr list`, local git history, or cached memory.
   - Do not retry expensive network-heavy API probes indefinitely.

6. Verify the exact staged state.
   - After material patch changes, rerun verifier or checks on the exact staged diff before accepting PASS.
   - Run `git diff --check` for markdown and skill packages.

## Guardrails

- Do not bypass branch protection, merge automatically, or weaken checks.
- Do not use destructive git commands unless the user explicitly authorized that exact operation.
- Do not request broad escalation prefixes for arbitrary scripts.
- Do not put secrets or private logs in PR bodies.

## Output

When finishing PR or shell-heavy work, report commands that passed, commands skipped, and any known environmental failure separately from code failures.
