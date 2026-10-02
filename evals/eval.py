#!/usr/bin/env python3
"""
Skill library evaluation harness.

Runs a rubric of mechanical checks against skills in this repo and emits
structured findings (JSON) plus a human-readable Markdown report. Defaults
to general-scope skills; use --scope to include project-scoped ones.

Usage:
    python evals/eval.py
    python evals/eval.py --scope all
    python evals/eval.py --skill playwright
    python evals/eval.py --stdout --format markdown

See evals/README.md for the full check list and scoring rubric.
Rubric source of truth: AGENTS.md sections 7 (clusters) and 9 (rubric).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError:
    sys.exit("error: PyYAML is required. Run: pip install -r evals/requirements.txt")


REPO_ROOT = Path(__file__).resolve().parent.parent


# --- Cluster definitions -----------------------------------------------------
# Used for cross-link consistency checks and Layer-2 category checks.
# Keep in sync with AGENTS.md section 7.
#
# Notes on what is NOT a cluster:
# - pdf: standalone (not part of the AI-API cluster; uses its own rendering path)
# - project-scoped deployment skills: they stay out of the general deployment
#   cluster so they are never cross-linked into unrelated codebases.
# - worker, Factory specialists, code-review droids: intentionally standalone;
#   the couplings are too loose for `related` to help discoverability.
CLUSTERS: dict[str, list[str]] = {
    "security": [
        "security-best-practices",
        "security-audit",
        "security-threat-model",
        "security-ownership-map",
    ],
    "browser": [
        "playwright",
        "playwright-interactive",
        "screenshot",
    ],
    "ai-api": [
        "speech",
        "transcribe",
        "imagegen",
    ],
    "deployment": [
        "cloudflare-deploy",
        "gh-fix-ci",
    ],
    "3d-ui": [
        "3d-bloom-scene",
        "force-graph-3d",
        "glassmorphic-ui",
    ],
}

# Public project names checked in general-scope descriptions and bodies.
# Add explicit product/repo spellings, not generic words such as "factory" or
# "commons". Aliases are opt-in; matching is literal and case-insensitive.
PROJECT_NAMES: list[str] = [
    "SpendForge",
    "RefereeOS",
    "ResumeTailor",
    "LinkedIn-Resume-Builder",
    "teamvince",
    "PersonalOS",
    "Commons Copilot",
    "commons-copilot",
    "earned-autonomy",
    "software-factory",
    "skill-forge",
]

# Trigger phrases that signal intent-matching descriptions.
TRIGGER_PATTERNS = [
    r"\buse when\b",
    r"\buse this\b",
    r"\buse for\b",
    r"\bwhen the user\b",
    r"\bwhen user\b",
    r"\bwhen asked\b",
    r"\buser asks\b",
    r"\buser wants\b",
    r"\bif the user\b",
    # The library's own convention: descriptions written as "Trigger on X" / "Trigger when Y happens"
    r"\btriggers? on\b",
    r"\btriggers? when\b",
    r"\btrigger:",
]


# --- Data model --------------------------------------------------------------

@dataclass
class Issue:
    check: str
    severity: str  # "error" | "warning" | "info"
    message: str


@dataclass
class Skill:
    id: str
    path: Path
    frontmatter: dict[str, Any]
    body: str
    body_lines: int
    catalog: dict[str, Any]
    scope: str
    targets: dict[str, bool]
    tags: list[str]
    related: list[str]
    last_modified: str | None
    last_modified_days_ago: int | None
    load_errors: list[str] = field(default_factory=list)

    @property
    def description(self) -> str:
        return (self.frontmatter or {}).get("description", "") or ""


# --- Loading -----------------------------------------------------------------

def strip_bom(data: bytes) -> bytes:
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:]
    return data


def parse_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    """Return (frontmatter, body, error). frontmatter is None on failure."""
    if not text.startswith("---"):
        return None, text, "missing frontmatter"
    end = text.find("\n---", 3)
    if end == -1:
        return None, text, "unterminated frontmatter"
    fm_text = text[3:end].strip()
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]
    try:
        fm = yaml.safe_load(fm_text) or {}
        if not isinstance(fm, dict):
            return None, body, "frontmatter is not a mapping"
        return fm, body, None
    except yaml.YAMLError as e:
        return None, body, f"YAML parse error: {e}"


def git_last_modified(path: Path) -> tuple[str | None, int | None]:
    try:
        rel = path.relative_to(REPO_ROOT)
        r = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(rel)],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        iso = r.stdout.strip()
        if not iso:
            return None, None
        dt = datetime.fromisoformat(iso)
        days = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days
        return iso, days
    except Exception:
        return None, None


def load_skill(skill_dir: Path) -> Skill:
    load_errors: list[str] = []

    skill_md = skill_dir / "SKILL.md"
    catalog_path = skill_dir / "catalog.yaml"

    frontmatter: dict = {}
    body = ""
    if not skill_md.exists():
        load_errors.append("SKILL.md missing")
    else:
        raw = strip_bom(skill_md.read_bytes()).decode("utf-8", errors="replace")
        fm, body, err = parse_frontmatter(raw)
        if err:
            load_errors.append(f"SKILL.md: {err}")
        frontmatter = fm or {}

    catalog: dict = {}
    if not catalog_path.exists():
        load_errors.append("catalog.yaml missing")
    else:
        try:
            raw = strip_bom(catalog_path.read_bytes()).decode("utf-8", errors="replace")
            parsed = yaml.safe_load(raw) or {}
            if not isinstance(parsed, dict):
                load_errors.append("catalog.yaml is not a mapping")
            else:
                catalog = parsed
        except yaml.YAMLError as e:
            load_errors.append(f"catalog.yaml parse error: {e}")

    last_modified, days_ago = git_last_modified(skill_dir)

    targets = catalog.get("targets") or {}
    if not isinstance(targets, dict):
        targets = {}

    return Skill(
        id=catalog.get("id") or skill_dir.name,
        path=skill_dir.relative_to(REPO_ROOT),
        frontmatter=frontmatter,
        body=body,
        body_lines=len(body.splitlines()) if body else 0,
        catalog=catalog,
        scope=catalog.get("scope", ""),
        targets={k: bool(v) for k, v in targets.items()},
        tags=list(catalog.get("tags") or []),
        related=list(catalog.get("related") or []),
        last_modified=last_modified,
        last_modified_days_ago=days_ago,
        load_errors=load_errors,
    )


# --- Layer 1: mechanical checks ---------------------------------------------

CheckFn = Callable[["Skill", dict[str, "Skill"]], list[Issue]]


def check_load_errors(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    return [Issue("load", "error", e) for e in s.load_errors]


def check_frontmatter_valid(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    if not s.frontmatter:
        return [Issue("frontmatter_valid", "error", "SKILL.md has no parseable frontmatter")]
    out: list[Issue] = []
    if not s.frontmatter.get("name"):
        out.append(Issue("frontmatter_valid", "error", "frontmatter missing required 'name'"))
    if not s.frontmatter.get("description"):
        out.append(Issue("frontmatter_valid", "error", "frontmatter missing required 'description'"))
    return out


def check_catalog_required(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    required = ["id", "origin", "kind", "tags", "targets", "scope"]
    return [
        Issue("catalog_required", "error", f"catalog.yaml missing '{k}'")
        for k in required if k not in s.catalog
    ]


def check_id_matches_dir(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    cid = s.catalog.get("id")
    if cid and cid != s.path.name:
        return [Issue("id_matches_dir", "error",
                      f"catalog.yaml id '{cid}' != directory '{s.path.name}'")]
    return []


def check_scope_valid(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    if s.scope not in ("general", "project"):
        return [Issue("scope_valid", "error",
                      f"scope must be 'general' or 'project', got {s.scope!r}")]
    return []


def check_targets_any(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    if not any(s.targets.values()):
        return [Issue("targets_any", "error", "no targets enabled")]
    return []


def check_description_length(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    desc = s.description
    n = len(desc)
    if not desc:
        return []  # covered by frontmatter_valid
    if n < 60:
        return [Issue("description_length", "warning",
                      f"description is {n} chars (<60); add trigger phrases")]
    if n > 500:
        return [Issue("description_length", "warning",
                      f"description is {n} chars (>500); Claude/Factory may truncate")]
    return []


def check_description_triggers(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    desc = s.description.lower()
    if not desc:
        return []
    if not any(re.search(p, desc) for p in TRIGGER_PATTERNS):
        return [Issue("description_triggers", "warning",
                      "description lacks intent-matching trigger phrases (e.g. 'use when', 'user asks')")]
    return []


def check_no_project_names(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    if s.scope != "general":
        return []
    haystack = s.description + "\n" + s.body
    # Word boundaries avoid matching names embedded in unrelated identifiers;
    # punctuation still allows repo URLs, paths, domains and possessives.
    hits = [
        p for p in PROJECT_NAMES
        if re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", haystack, re.IGNORECASE)
    ]
    if hits:
        return [Issue("no_project_names", "warning",
                      f"general-scope skill mentions project name(s): {', '.join(hits)}")]
    return []


def check_out_of_scope_clarity(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    text = (s.description + "\n" + s.body).lower()
    markers = [
        "out of scope", "out-of-scope", "not for", "do not use",
        "don't use", "does not", "is not for", "not intended",
    ]
    if not any(m in text for m in markers):
        return [Issue("out_of_scope_clarity", "info",
                      "no explicit scope boundary; consider saying what the skill does NOT do")]
    return []


def check_size_discipline(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    n = s.body_lines
    if n > 500:
        return [Issue("size_discipline", "error",
                      f"SKILL.md body is {n} lines (>500); move detail to references/")]
    if n > 300:
        return [Issue("size_discipline", "warning",
                      f"SKILL.md body is {n} lines (>300); consider moving detail to references/")]
    return []


def check_related_exists(s: Skill, all_skills: dict[str, Skill]) -> list[Issue]:
    return [
        Issue("related_exists", "error", f"related id '{rid}' does not match any skill")
        for rid in s.related if rid not in all_skills
    ]


def check_related_bidirectional(s: Skill, all_skills: dict[str, Skill]) -> list[Issue]:
    out: list[Issue] = []
    for rid in s.related:
        other = all_skills.get(rid)
        if other and s.id not in other.related:
            out.append(Issue("related_bidirectional", "warning",
                             f"'{rid}' does not list '{s.id}' in its related field"))
    return out


def check_cluster_membership(s: Skill, all_skills: dict[str, Skill]) -> list[Issue]:
    for cluster_name, members in CLUSTERS.items():
        if s.id not in members:
            continue
        expected = [m for m in members if m != s.id and m in all_skills]
        missing = [m for m in expected if m not in s.related]
        if missing:
            return [Issue("cluster_membership", "warning",
                          f"in {cluster_name} cluster but missing siblings in related: {', '.join(missing)}")]
    return []


def check_tags_non_empty(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    if not s.tags:
        return [Issue("tags_non_empty", "warning", "tags field is empty")]
    return []


def check_freshness(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    d = s.last_modified_days_ago
    if d is None:
        return []
    if d > 180:
        return [Issue("freshness", "warning", f"last modified {d} days ago (>180)")]
    if d > 90:
        return [Issue("freshness", "info", f"last modified {d} days ago (>90)")]
    return []


# --- Layer 2: category-specific checks --------------------------------------

def check_ai_api_conventions(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    if s.id not in CLUSTERS["ai-api"]:
        return []
    out: list[Issue] = []
    body = s.body.lower()
    if not any(k in body for k in ["api_key", "openai_api_key", "api key"]):
        out.append(Issue("ai_api_key", "info",
                         "AI-API skill should document API key requirement"))
    if not re.search(r"\b(gpt|dall|whisper|tts|model)[\w-]*\b", body):
        out.append(Issue("ai_api_model", "info",
                         "consider naming the default model ID"))
    return out


def check_security_conventions(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    if s.id not in CLUSTERS["security"]:
        return []
    body = s.body.lower()
    if not any(t in body for t in ["cwe", "cve", "owasp", "severity"]):
        return [Issue("security_taxonomy", "info",
                      "security skill should reference a taxonomy (CWE/CVE/OWASP) or severity levels")]
    return []


def check_deployment_conventions(s: Skill, _all: dict[str, Skill]) -> list[Issue]:
    if s.id not in CLUSTERS["deployment"]:
        return []
    body = s.body.lower()
    out: list[Issue] = []
    if not any(t in body for t in ["auth", "login", "token", "api key", "credential"]):
        out.append(Issue("deployment_auth", "info",
                         "deployment skill should document auth/credentials"))
    if not any(t in body for t in ["verify", "smoke", "post-deploy", "health"]):
        out.append(Issue("deployment_verify", "info",
                         "deployment skill should document post-deploy verification"))
    return out


# --- Check registry ----------------------------------------------------------

CHECKS: list[CheckFn] = [
    check_load_errors,
    check_frontmatter_valid,
    check_catalog_required,
    check_id_matches_dir,
    check_scope_valid,
    check_targets_any,
    check_description_length,
    check_description_triggers,
    check_no_project_names,
    check_out_of_scope_clarity,
    check_size_discipline,
    check_related_exists,
    check_related_bidirectional,
    check_cluster_membership,
    check_tags_non_empty,
    check_freshness,
    # Layer 2
    check_ai_api_conventions,
    check_security_conventions,
    check_deployment_conventions,
]


# --- Runner ------------------------------------------------------------------

def discover_skills(repo_root: Path) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    for entry in sorted(repo_root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if entry.name == "evals":
            continue
        if not (entry / "catalog.yaml").exists() and not (entry / "SKILL.md").exists():
            continue
        s = load_skill(entry)
        skills[s.id] = s
    return skills


def run_checks(skill: Skill, all_skills: dict[str, Skill]) -> list[Issue]:
    issues: list[Issue] = []
    for check in CHECKS:
        try:
            issues.extend(check(skill, all_skills))
        except Exception as e:
            issues.append(Issue(check.__name__, "error", f"check crashed: {e}"))
    return issues


def grade_from_issues(issues: list[Issue]) -> str:
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    if errors >= 2:
        return "F"
    if errors == 1:
        return "D"
    if warnings >= 6:
        return "D"
    if warnings >= 3:
        return "C"
    if warnings >= 1:
        return "B"
    return "A"


def filter_skills(skills: dict[str, Skill], scope: str, only: str | None) -> list[Skill]:
    out: list[Skill] = []
    for s in skills.values():
        if only and s.id != only:
            continue
        if scope == "general" and s.scope != "general":
            continue
        if scope == "project" and s.scope != "project":
            continue
        out.append(s)
    return sorted(out, key=lambda x: x.id)


def git_head() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        return r.stdout.strip()
    except Exception:
        return ""


def build_report(skills: list[Skill], all_skills: dict[str, Skill], scope: str) -> dict:
    results = []
    totals = {"error": 0, "warning": 0, "info": 0}
    grades = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    issue_counts: dict[str, int] = {}
    for s in skills:
        issues = run_checks(s, all_skills)
        for i in issues:
            totals[i.severity] = totals.get(i.severity, 0) + 1
            issue_counts[i.check] = issue_counts.get(i.check, 0) + 1
        g = grade_from_issues(issues)
        grades[g] += 1
        results.append({
            "id": s.id,
            "path": str(s.path),
            "grade": g,
            "errors": sum(1 for i in issues if i.severity == "error"),
            "warnings": sum(1 for i in issues if i.severity == "warning"),
            "infos": sum(1 for i in issues if i.severity == "info"),
            "metadata": {
                "scope": s.scope,
                "targets": [k for k, v in s.targets.items() if v],
                "tags": s.tags,
                "related": s.related,
                "body_lines": s.body_lines,
                "last_modified": s.last_modified,
                "last_modified_days_ago": s.last_modified_days_ago,
            },
            "issues": [asdict(i) for i in issues],
        })
    top_issues = sorted(issue_counts.items(), key=lambda x: -x[1])[:10]
    return {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo_head": git_head(),
            "scope_filter": scope,
            "total_skills": len(skills),
        },
        "summary": {
            "errors": totals["error"],
            "warnings": totals["warning"],
            "infos": totals["info"],
            "grades": grades,
            "top_issues": [{"check": c, "count": n} for c, n in top_issues],
        },
        "skills": results,
    }


def format_markdown(report: dict) -> str:
    meta = report["meta"]
    summary = report["summary"]
    lines: list[str] = []
    lines.append("# Skill Eval Report")
    lines.append("")
    lines.append(f"- Generated: `{meta['generated_at']}`")
    lines.append(f"- Commit: `{meta['repo_head']}`")
    lines.append(f"- Scope filter: `{meta['scope_filter']}`")
    lines.append(f"- Skills audited: **{meta['total_skills']}**")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Errors: **{summary['errors']}**")
    lines.append(f"- Warnings: **{summary['warnings']}**")
    lines.append(f"- Infos: **{summary['infos']}**")
    lines.append("")
    lines.append("| Grade | Count |")
    lines.append("|---|---|")
    for g in ("A", "B", "C", "D", "F"):
        lines.append(f"| {g} | {summary['grades'][g]} |")
    lines.append("")
    if summary["top_issues"]:
        lines.append("## Top issues")
        lines.append("")
        for entry in summary["top_issues"]:
            lines.append(f"- `{entry['check']}` x {entry['count']}")
        lines.append("")
    lines.append("## Per-skill findings")
    lines.append("")
    lines.append("_Sorted worst-first (F, D, C, B, A), then by id._")
    lines.append("")
    grade_order = {"F": 0, "D": 1, "C": 2, "B": 3, "A": 4}
    skills_sorted = sorted(
        report["skills"], key=lambda x: (grade_order[x["grade"]], x["id"])
    )
    for sk in skills_sorted:
        lines.append(
            f"### {sk['id']} - {sk['grade']} "
            f"({sk['errors']}E / {sk['warnings']}W / {sk['infos']}I)"
        )
        md = sk["metadata"]
        targets = ", ".join(md["targets"]) or "(none)"
        lines.append("")
        lines.append(f"- path: `{sk['path']}`")
        lines.append(f"- scope: {md['scope']}, targets: {targets}")
        lines.append(f"- tags: {', '.join(md['tags']) or '(none)'}")
        if md["related"]:
            lines.append(f"- related: {', '.join(md['related'])}")
        lines.append(f"- body: {md['body_lines']} lines")
        if sk["issues"]:
            lines.append("")
            lines.append("**Issues:**")
            for i in sk["issues"]:
                marker = {
                    "error": "[ERROR]",
                    "warning": "[WARN] ",
                    "info": "[INFO] ",
                }.get(i["severity"], "[    ] ")
                lines.append(f"- {marker} `{i['check']}`: {i['message']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Skill library evaluation harness")
    ap.add_argument("--scope", choices=["general", "project", "all"], default="general",
                    help="which skills to audit (default: general)")
    ap.add_argument("--skill", help="audit only this skill id")
    ap.add_argument("--format", choices=["json", "markdown", "both"], default="both")
    ap.add_argument("--output-prefix", default="evals/reports/baseline",
                    help="output path prefix relative to repo root")
    ap.add_argument("--stdout", action="store_true",
                    help="print to stdout instead of writing files")
    args = ap.parse_args()

    all_skills = discover_skills(REPO_ROOT)
    selected = filter_skills(all_skills, args.scope, args.skill)
    if not selected:
        print("no skills matched", file=sys.stderr)
        return 1

    report = build_report(selected, all_skills, args.scope)
    json_text = json.dumps(report, indent=2) + "\n"
    md_text = format_markdown(report)

    if args.stdout:
        if args.format == "json":
            sys.stdout.write(json_text)
        elif args.format == "markdown":
            sys.stdout.write(md_text)
        else:
            sys.stdout.write(md_text)
    else:
        out_path = (REPO_ROOT / args.output_prefix)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if args.format in ("json", "both"):
            (REPO_ROOT / f"{args.output_prefix}.json").write_text(json_text, encoding="utf-8")
        if args.format in ("markdown", "both"):
            (REPO_ROOT / f"{args.output_prefix}.md").write_text(md_text, encoding="utf-8")
        summary = report["summary"]
        print(
            f"wrote {args.output_prefix}.json / .md -- "
            f"{report['meta']['total_skills']} skills: "
            f"{summary['errors']} errors, "
            f"{summary['warnings']} warnings, "
            f"{summary['infos']} infos"
        )
    return 0 if report["summary"]["errors"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
