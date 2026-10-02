# evals/

Skill library evaluation harness. Runs a rubric of mechanical checks against skills in this repo and emits structured findings (JSON) plus a human-readable Markdown report.

The rubric is documented in `AGENTS.md` section 9 (quality rubric) and section 7 (cluster map used for cross-link consistency).

## Install

```bash
pip install -r evals/requirements.txt
```

Only dependency is PyYAML.

## Run

```bash
# Default: audit general-scope skills, write to evals/reports/baseline.{json,md}
python evals/eval.py

# Include project-scoped skills too
python evals/eval.py --scope all

# Only project-scoped
python evals/eval.py --scope project

# Single skill
python evals/eval.py --skill playwright

# Stream markdown to stdout instead of writing files
python evals/eval.py --stdout --format markdown

# Custom output prefix (writes <prefix>.json and <prefix>.md)
python evals/eval.py --output-prefix evals/reports/run-2026-05-01
```

Exit code is `0` if there are no errors, `2` if any errors are present. Useful for CI.

Run harness regression tests with `python -m unittest discover -s evals -p 'test_*.py'`.
The separate `python evals/test_behavior.py` command checks the security-audit fixture.

## Checks

### Layer 1 — mechanical (always run)

| Check | Severity | What it flags |
|---|---|---|
| `load` | error | SKILL.md or catalog.yaml missing or unparseable |
| `frontmatter_valid` | error | missing `name` or `description` in SKILL.md frontmatter |
| `catalog_required` | error | missing one of: id, origin, kind, tags, targets, scope |
| `id_matches_dir` | error | catalog.yaml `id` does not match the directory name |
| `scope_valid` | error | scope must be `general` or `project` |
| `targets_any` | error | at least one target must be `true` |
| `description_length` | warning | description under 60 chars or over 500 |
| `description_triggers` | warning | no intent-matching phrases like "use when", "user asks" |
| `no_project_names` | warning | general-scope skill hardcodes a known project name |
| `out_of_scope_clarity` | info | body does not state what the skill *does not* do |
| `size_discipline` | warning / error | SKILL.md body over 300 / over 500 lines |
| `related_exists` | error | a `related` id does not match any known skill |
| `related_bidirectional` | warning | cross-link is not reciprocal |
| `cluster_membership` | warning | skill is in a known cluster but missing siblings from `related` |
| `tags_non_empty` | warning | tags field is empty |
| `freshness` | info / warning | more than 90 / 180 days since last commit touching the skill |

### Project-name leakage

`PROJECT_NAMES` in `eval.py` ships with the owner's public project names:
SpendForge, RefereeOS, ResumeTailor, teamvince, PersonalOS, Commons Copilot,
earned-autonomy, software-factory, and skill-forge. Adapt this list for your own
library. Use explicit names or aliases, not generic terms such as `commons`,
`factory`, or `software`.

`no_project_names` checks the `SKILL.md` description and body for literal,
case-insensitive matches. Names next to punctuation, in paths, and in URLs match;
names embedded in larger word/underscore identifiers do not. Spaces and hyphens
are literal: `software-factory` matches, while the generic phrase `software factory`
does not. Add alternate spellings explicitly when needed.

Project-scoped skills are exempt, including when running `--scope all`. A skill
that intentionally specializes in one project should declare `scope: project`
and follow the target restrictions in `AGENTS.md`. The check remains a warning,
so it affects the grade but does not fail CI by itself. Library documentation,
tests, and reference files are outside this check; self-references to skill-forge
in this README do not become skill findings. This bounded list is not a general
detector for unknown project names or paths.

### Layer 2 — category-specific

Routed by cluster membership (see `AGENTS.md` section 7). These are informational only — the harness does not judge content quality, just the presence of conventions that well-formed skills in that category tend to have.

| Cluster | Checks |
|---|---|
| AI APIs (`speech`, `transcribe`, `imagegen`) | documents API key handling; names a default model ID |
| Security (`security-*`) | references a taxonomy (CWE / CVE / OWASP) or severity levels |
| Deployment (`cloudflare-deploy`, `gh-fix-ci`) | documents auth / credentials; documents post-deploy verification |

## Scoring

Each skill gets a grade based on its issue counts:

| Grade | Condition |
|---|---|
| **A** | 0 errors, 0 warnings |
| **B** | 0 errors, 1–2 warnings |
| **C** | 0 errors, 3–5 warnings |
| **D** | exactly 1 error, OR 6+ warnings |
| **F** | 2+ errors |

Infos never affect the grade — they exist to surface judgment calls for human review.

Grade A means the skill is well-formed. It is not a claim that the skill makes an agent better. `evals/test_behavior.py` is a separate fixture check for high-stakes skills (currently `security-audit`).

## Output

- `reports/baseline.json` — machine-readable; stable schema for comparison runs.
- `reports/baseline.md` — human-readable; per-skill findings sorted worst-first.

Commit new baselines to track drift over time, or pass `--output-prefix` to run ad-hoc audits without overwriting the checked-in baseline.

### JSON schema

```json
{
  "meta": {
    "generated_at": "...",
    "repo_head": "...",
    "scope_filter": "general|project|all",
    "total_skills": 0
  },
  "summary": {
    "errors": 0, "warnings": 0, "infos": 0,
    "grades": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
    "top_issues": [{"check": "...", "count": 0}]
  },
  "skills": [
    {
      "id": "...",
      "path": "...",
      "grade": "A",
      "errors": 0, "warnings": 0, "infos": 0,
      "metadata": {
        "scope": "general",
        "targets": ["codex", "claude"],
        "tags": ["..."],
        "related": ["..."],
        "body_lines": 0,
        "last_modified": "ISO8601 or null",
        "last_modified_days_ago": 0
      },
      "issues": [
        {"check": "...", "severity": "error|warning|info", "message": "..."}
      ]
    }
  ]
}
```

## Adding a check

Each check is a function with signature:

```python
def check_xxx(skill: Skill, all_skills: dict[str, Skill]) -> list[Issue]:
    ...
```

Return an empty list when the skill passes. Append the function to the `CHECKS` list in `eval.py`. Use the existing checks as templates — they are all short and side-effect free.

Guidelines for severity:

- **error** — the skill is broken or will mis-sync. Must fail CI.
- **warning** — the skill works but violates a lint-enforceable convention.
- **info** — judgment call surfaced for human review; never fails CI.

## Promoting to `sync.ps1 lint`

Checks in this harness are intentionally separate from `sync.ps1 lint` for now. Once a check has been stable for a while and the corpus is clean under it, promote it into the PowerShell/Bash lint so it runs on every push without requiring Python.

## Relationship to `AGENTS.md`

`AGENTS.md` section 9 is the **source of truth** for the rubric. This harness is the mechanical implementation. If you change one, update the other.
