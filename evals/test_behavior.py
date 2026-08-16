#!/usr/bin/env python3
"""Fixture-based behavioral checks for high-stakes skills.

These are not LLM evals. They assert that a skill's trigger and instructions
would actually fire and constrain behavior on a representative request.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_SKILL = REPO_ROOT / "security-audit" / "SKILL.md"
FIXTURE = REPO_ROOT / "evals" / "fixtures" / "security-audit-target"

GOLDEN_SHOULD_TRIGGER = (
    "Run a supply-chain audit of my npm and pip packages and editor "
    "extensions on Windows."
)
GOLDEN_SHOULD_NOT = "Deploy this Next.js app to Cloudflare Workers."


def _load_skill(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise SystemExit(f"error: {path} is missing YAML frontmatter")
    front, body = match.group(1), match.group(2)
    desc_match = re.search(r'^description:\s*"(.*)"\s*$', front, re.MULTILINE)
    if not desc_match:
        raise SystemExit(f"error: {path} is missing a quoted description")
    return desc_match.group(1), body


def _assert(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    description, body = _load_skill(AUDIT_SKILL)
    desc_l = description.lower()
    body_l = body.lower()
    request_l = GOLDEN_SHOULD_TRIGGER.lower()
    negative_l = GOLDEN_SHOULD_NOT.lower()

    _assert(
        AUDIT_SKILL.is_file(),
        f"missing skill file: {AUDIT_SKILL}",
        failures,
    )
    _assert(
        "use when" in desc_l,
        "security-audit description must be a trigger ('use when'), not a summary",
        failures,
    )
    _assert(
        all(token in desc_l for token in ("npm", "pip", "windows")),
        "security-audit description must name npm, pip, and Windows so it can match the fixture request",
        failures,
    )
    _assert(
        "audit" in request_l and "npm" in desc_l and "pip" in desc_l,
        "fixture request should overlap the skill trigger (audit + npm + pip)",
        failures,
    )
    _assert(
        "cloudflare" not in desc_l and "deploy" not in desc_l,
        "security-audit must not steal Cloudflare deploy requests",
        failures,
    )
    _assert(
        "workers" in negative_l and "cloudflare" in negative_l,
        "negative fixture is a deploy request, not an audit",
        failures,
    )
    _assert(
        "never print secret" in body_l or "never print secret values" in body_l,
        "security-audit must forbid printing secret values",
        failures,
    )
    _assert(
        "critical" in body_l and "high" in body_l and "medium" in body_l,
        "security-audit must rank findings by severity",
        failures,
    )
    _assert(
        "npm audit" in body_l and "pip-audit" in body_l,
        "security-audit must run npm audit and pip-audit on a fixture like this one",
        failures,
    )
    _assert(
        ".env" in body_l,
        "security-audit must inspect .env files present in the fixture target",
        failures,
    )

    pkg = FIXTURE / "package.json"
    env_file = FIXTURE / ".env.example"
    _assert(pkg.is_file(), f"missing fixture package.json at {pkg}", failures)
    _assert(env_file.is_file(), f"missing fixture env example at {env_file}", failures)
    pkg_text = pkg.read_text(encoding="utf-8") if pkg.is_file() else ""
    _assert(
        "lodahs" in pkg_text or "postinstall" in pkg_text,
        "fixture package.json should contain a supply-chain smell (typosquat or postinstall)",
        failures,
    )

    if failures:
        print("behavior checks failed:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("behavior checks passed: security-audit vs evals/fixtures/security-audit-target")
    return 0


if __name__ == "__main__":
    sys.exit(main())
