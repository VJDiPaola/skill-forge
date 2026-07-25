# AGENTS.md

Contributor guide for AI agents (Claude Code, Codex, Factory droids, etc.) working in this repo.

If you are a human, `README.md` is the friendlier overview. This file encodes the rules, pitfalls, and judgement calls that the lint tooling can't enforce automatically.

---

## 1. What this repo is

This is the **single source of truth** for AI skills shared across five tools:

| Tool | Location | Sync method | Direction |
|---|---|---|---|
| Codex | `~/.codex/skills/` | NTFS directory junctions | Bidirectional |
| Warp | `~/.codex/skills/` (shared with Codex) | Via Codex junctions | Bidirectional |
| Claude Code | `~/.claude/commands/` | Generated `.md` | Library → Claude (one-way) |
| Factory | `~/.factory/droids/` | Generated `.md` | Library → Factory (one-way) |
| Claude desktop (Cowork) | `%APPDATA%\Claude\local-agent-mode-sessions\skills-plugin\<guid>\<guid>\skills\` | Mirrored skill dirs (opt-in via `targets.desktop`) | Library → Desktop (one-way) |

Desktop notes: only skills with `desktop: true` in `catalog.yaml` targets are pushed; app-managed stock skills (docx, pptx, xlsx, skill-creator, mcp-builder, etc.) are never touched. The GUID path segments change if the app reinstalls — both sync scripts print a SKIP warning with recovery steps if the dir vanishes.

Every change must flow through this repo. Edits made directly in tool directories are only safe for Codex/Warp (bidirectional); Claude and Factory files are regenerated and will be overwritten.

Non-skill directories at the repo root (intentionally absent from `catalog.json`): `evals/` is the skill eval harness (`eval.py` + reports).

---

## 2. Non-negotiables

These rules exist because violating them silently corrupts sync state or ships broken skills.

1. **Never hand-edit generated Claude or Factory files** under `~/.claude/commands/` or `~/.factory/droids/`. Edit the source in this repo and run `sync.ps1 push`. The auto-generated marker in the file header is not decorative — `pull` relies on it.
2. **Never hand-edit `catalog.json`.** It is regenerated on every `push` and `pull`. Edit `catalog.yaml` inside the skill directory instead.
3. **Never promote a `scope: project` skill to Claude or Factory targets.** Project-scoped skills name specific products and will mislead agents working in unrelated codebases.
4. **Never push to `main` with failing lint.** Run `.\sync.ps1 lint` before committing. If lint fails, fix the skill, don't suppress the check.
5. **Never rename a skill directory without updating its `id` in `catalog.yaml`.** The `id` is the stable identifier used by `related` cross-links; a mismatch silently breaks the cluster graph.
6. **Never delete a skill without first grepping for its id in other skills' `related:` fields.** Orphaned cross-links are a lint failure.

---

## 3. Skill anatomy

```
skill-name/
  SKILL.md              # Required — YAML frontmatter + markdown body
  catalog.yaml          # Required — library metadata
  agents/openai.yaml    # Optional — Codex UI metadata
  scripts/              # Optional — executable code (bash, python, ps1)
  references/           # Optional — long-form reference docs
  assets/               # Optional — icons, templates, sample data
```

### `SKILL.md` frontmatter

```yaml
---
name: "skill-name"
description: "When to use this skill — include concrete trigger phrases"
model: inherit          # Optional, Factory-specific
---
```

The `description` is the single most important field. It determines when the skill auto-invokes. Write it as trigger phrases the user would actually say, not as a summary.

### `catalog.yaml` required keys

```yaml
id: skill-name          # Must match directory name
origin: codex           # codex | claude | factory (where the skill was authored)
kind: skill             # skill | command | droid
tags: [security, review]
targets:
  codex: true
  claude: true
  factory: false
scope: general          # general | project
related: [sibling-skill-id, other-sibling-id]   # Optional
```

`scope` and `related` are mandatory for any skill touched after 2026-04-13.

---

## 4. Command cheatsheet

Run from the repo root. PowerShell and Bash have the same command surface.

| Command | Purpose |
|---|---|
| `.\sync.ps1 push [tool]` | Copy/generate library → tool dirs. Tool is optional; default is all. |
| `.\sync.ps1 pull [tool]` | Import changes from tool dirs → library (Codex/Warp only for now). |
| `.\sync.ps1 status` | Show which skills exist where. |
| `.\sync.ps1 diff` | Content diff between library and tool dirs. |
| `.\sync.ps1 search <query>` | Grep across skill bodies and metadata. |
| `.\sync.ps1 lint` | Validate frontmatter, catalog.yaml, cross-links, targets. |

Bash equivalents: `./sync.sh <same subcommand>`.

Always run `diff` before `push` when you're unsure what will change, and `lint` before committing.

---

## 5. Adding a new skill

1. Create `skill-library/my-skill/`.
2. Write `SKILL.md`:
   - Make `description` a list of concrete trigger phrases.
   - Say what the skill **does not** do (scope boundary).
   - Keep the body short; push long reference material into `references/`.
3. Write `catalog.yaml` with all required keys, including `scope`.
4. If it belongs to an existing cluster (see §7), add its id to the siblings' `related:` and add theirs to yours.
5. `.\sync.ps1 lint` — fix anything it complains about.
6. `.\sync.ps1 diff` — sanity-check what will be written to tool dirs.
7. `.\sync.ps1 push` — sync.
8. Commit the new skill directory.

---

## 6. Modifying an existing skill

1. Edit the source files in this repo, never the tool-side copies (except Codex/Warp, which are junctions and therefore equivalent).
2. Preserve the `related:` field unless you deliberately restructure a cluster.
3. If tags change, re-check cluster membership.
4. If you change `scope` from `general` to `project`, remove Claude/Factory from `targets`.
5. `.\sync.ps1 diff` to preview, then `.\sync.ps1 lint`, then `push`.
6. Commit with a message that names the skill and the reason.

---

## 7. Cluster map

When updating a skill, check whether it belongs to a cluster and keep `related` consistent.

| Cluster | Members |
|---|---|
| **Security** | `security-best-practices`, `security-audit`, `security-threat-model`, `security-ownership-map` |
| **Browser automation** | `playwright`, `playwright-interactive`, `screenshot` |
| **AI APIs** | `speech`, `transcribe`, `imagegen` |
| **Deployment** (general only) | `cloudflare-deploy`, `gh-fix-ci` |
| **3D / UI generation** | `3d-bloom-scene`, `force-graph-3d`, `glassmorphic-ui` |
| **Evals methodology** | `eval-framework`, `behavior-spec-canvas`, `autonomy-map`, `api-prompt-optimizer` |
| **Capture & media** | `screenshot`, `photo-geolocator` (paired one way from `screenshot`) |

The five clusters that the harness enforces mechanically are defined in `evals/eval.py` (`CLUSTERS`). Keep that dict and this table in sync; `check_cluster_membership` reads the code, not the docs.

**Standalone skills** (no cluster, no `related` enforcement): `pdf`, `worker`, `api-drift-scout`, `sdk-ui-override-specialist`, `react-query-test-harness-fixer`, `scrutiny-feature-reviewer`, `user-testing-flow-validator`, `windows-cli-wsl-repair`, `windows-node-sandbox-troubleshooting`, `seeded-catalog-sync`, `pr-shell-safety-pack`, `repo-first-vercel-build`, `database-design`, `docker-debug`, `git-workflows`, `testing-strategy`, `api-design-review`, `interactive-artifact-generator`.

These are genuinely loose couplings; `related` would dilute signal rather than improve discoverability.

If you add a skill that naturally belongs in one of the clusters above, update both sides of the `related` relationship. Project-scoped skills never cross-link to general-scope skills.

---

## 8. Cross-pollination decision tree

Use this when deciding whether a Codex skill should also be promoted to Claude or Factory (or vice versa).

Promote **only if all** of these are true:

- [ ] `scope: general` (not `project`).
- [ ] No hardcoded project name, path, or repo reference in the body.
- [ ] No OS coupling the target tool can't satisfy (e.g., a Windows-only CLI probably shouldn't become a Factory droid).
- [ ] The target tool can actually execute any bundled scripts, or the skill is pure reasoning.
- [ ] The skill is lean enough to carry everywhere (a 300-file reference tree is probably Codex-only).
- [ ] Adding it fills a real gap in the target tool, not just completeness.

If any box is unchecked, leave it where it is.

---

## 9. Quality rubric

Run this mental checklist on any skill you add or modify. Items marked **[lint]** are enforced by `sync.ps1 lint`; the rest require human/agent judgement.

1. **Trigger quality** — Does `description` name concrete user phrases an LLM can match against intent? Vague descriptions never auto-invoke.
2. **Scope correctness [lint]** — Does `scope: project` appear anywhere a general name is used, or vice versa?
3. **Out-of-scope clarity** — Does the body explicitly say what the skill does **not** do? (See `speech/SKILL.md` for the template: "Custom voice creation is out of scope.")
4. **Freshness** — When was the last edit? Are pinned model IDs, SDK versions, and API versions still current?
5. **Target-kind fit [lint]** — Are the `targets` consistent with what the skill actually needs to run?
6. **Cross-link completeness [lint]** — If it belongs to a cluster, does `related` list its siblings, and do they list it back?
7. **Size discipline** — Is `SKILL.md` under ~300 lines? Long reference material belongs in `references/`.
8. **Frontmatter validity [lint]** — All required keys present, YAML parses cleanly, description under the target tools' length limits.

---

## 10. Common pitfalls

Real footguns that have bitten this repo before:

- **YAML multi-line scalars** — Descriptions that span lines using `>` or `|` broke the Bash parser before the 2026-04-13 fix. Prefer single-line descriptions; if you must go multi-line, run `sync.sh lint` on WSL/Git Bash before committing.
- **Description length limits** — Claude and Factory truncate very long descriptions. Keep under ~500 characters.
- **Junction vs real directory** — On Windows, `sync.ps1` detects junctions by reparse point. Don't copy Codex skill dirs with `cp -r`; use the sync script so the junction semantics stay intact.
- **PowerShell 5.1 compatibility** — Don't use PowerShell 7-only syntax in `sync.ps1` without a fallback. The watcher runs under whatever shell Task Scheduler launches.
- **Factory overwrites on pull** — `pull` previously clobbered Factory edits. The current logic is defensive, but still run `diff` first if you suspect a tool edited files out-of-band.
- **UTF-8 BOM** — Some Windows editors add a BOM to `SKILL.md`, which breaks frontmatter parsing on Unix. Save as UTF-8 without BOM.
- **`.gitignore` for tool dirs** — Never add `~/.codex/skills/` or similar to `.gitignore` in this repo; they aren't tracked here anyway, and confusion leads to deleted work.

---

## 11. When in doubt

- Read `README.md` for the human-facing overview.
- Read `CHANGELOG.md` for the latest infrastructure changes.
- Read `recommendations-2026-04-13.md` for the active backlog.
- Run `sync.ps1 search <keyword>` before writing a new skill — there may already be one.
- If you are about to do something irreversible (delete a skill, rename a directory, change `origin`), stop and ask the user.
