---
name: repo-first-vercel-build
description: Build urgent repo-first Next.js or Vercel-ready MVPs with clean GitHub history, stable dependency choices, parallel review, and honest deployment readiness. Use when the user asks to create a GitHub repo first, one-shot a hackathon or MVP build, deploy to Vercel quickly, use subagents in parallel, or prove a Vercel app works beyond a demo flow.
---

# Repo-First Vercel Build

Use this skill when speed matters but the deliverable still needs source history, build verification, and truthful live-readiness reporting.

## Workflow

1. Establish the repo before major implementation.
   - If the user asks for a GitHub repo first, create the empty private repo before building.
   - On Windows, prefer `gh repo create <name> --private`, then `git remote add origin <url>` and `git push`.
   - Avoid relying on `gh repo create --source .` when path handling is flaky.

2. Scaffold conservatively.
   - If the checkout is basically empty, scaffold directly instead of searching for nonexistent structure.
   - Pin stable framework versions when `latest` resolves to previews or broken Windows SWC behavior.
   - Avoid `next/font/google` for reproducible builds when network fetches may break build.

3. Ship the vertical slice.
   - Build the first screen as the usable app, not a landing page, unless the user asked for marketing.
   - Keep optional capabilities optional and user-controlled.
   - Add demo-safe fallback behavior only when it is visibly labeled and does not mask live readiness.

4. Add public readiness proof.
   - Include `GET /api/health` or equivalent when live integrations matter.
   - Return booleans, mode, and missing integration names only. Never return secret values.
   - Add smoke probes for expected bad inputs, guarded actions, and fallback mode.

5. Use bounded parallel review.
   - Keep implementation moving in the mainline.
   - Use separate review lanes for approval gates, persistence fallback, security boundaries, and deployment readiness when useful.
   - Treat reviewer findings as real blockers if they affect safety or completion truth.

6. Verify locally and after deploy.
   - Prefer `npm.cmd` on Windows.
   - Typical local sequence: lint, typecheck, build, audit if dependency risk matters, then one-shot production server smoke checks.
   - Restart the production server after route changes before treating route misses as app bugs.
   - After Vercel deploy, verify public URLs and health outputs.

## Guardrails

- Do not claim live provider success from demo fallback behavior.
- Do not invent env vars or mark missing credentials as complete.
- Do not hide integration gaps in a happy-path UI.
- Do not push secrets, local logs, temporary clones, or generated caches.

## Verification

Final response should separate:

- Built and deployed behavior.
- Local checks actually executed.
- Public smoke checks actually executed.
- Missing credentials or unproven live integrations.
- Repo URL, branch, deployment URL, and any known blockers.
