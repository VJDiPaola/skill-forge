---
name: interactive-artifact-generator
description: Create standalone browser-openable interactive HTML artifacts for decision boards, curated recommendation lists, job shortlists, hackathon idea explorers, option comparisons, and other visual deliverables. Use when the user asks for interactive HTML, visual output, a list they can filter or decide from, or a non-prose artifact they can open locally.
---

# Interactive Artifact Generator

Use this skill to turn research, options, or scored candidates into a useful local HTML artifact instead of a static prose dump.

## Artifact Shape

Prefer a single self-contained `.html` file when:

- The user asks for interactive HTML or visual output.
- The deliverable is a decision list, shortlist, comparison, or curated set.
- The artifact should work by opening the file directly in a browser.

Use a small app only when the artifact needs server-side APIs, uploads, auth, or persistent backend data.

## Workflow

1. Define the decision model.
   - Identify the user's primary decision: shortlist, choose, compare, apply, visit, build, or approve.
   - Choose filters and sort keys that directly support that decision.
   - Keep source links and evidence strength visible.

2. Build useful interactions.
   - Include search for lists over 10 items.
   - Include filters for category, evidence type, status, location, score, or decision state as appropriate.
   - Include sortable cards or tables.
   - Use localStorage only for local decision state such as selected, saved, or pass.

3. Preserve evidence and scarcity.
   - Do not pad a list to meet a target count when verified supply is lower.
   - Put checked-but-rejected or weaker candidates in a separate panel.
   - Label official-source, secondary-source, and inferred evidence separately.

4. Design for scanning.
   - Use dense but readable cards or tables.
   - Show the strongest next action on each item.
   - Avoid decorative layouts that hide the content.
   - Ensure mobile and desktop text does not overflow controls.

5. Verify before handoff.
   - Parse inline JavaScript with Node using `new Function(...)`.
   - Count expected records.
   - Check that every primary item has a title, source or evidence, and decision-relevant metadata.
   - If visual layout is central, open the file or inspect screenshots where browser access is available.

## Guardrails

- Do not embed secrets or private tokens in HTML.
- Do not rely on remote scripts unless the user asked for a hosted app and the dependency is justified.
- Do not describe how to use the page inside the page when controls are self-evident.
- Do not put nested cards inside cards.

## Output

Return the absolute path to the HTML file, a one-line description of the interactions, and the verification performed.
