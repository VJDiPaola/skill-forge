---
name: autonomy-map
description: Map autonomy levels for an AI component using a scenario-based decision matrix. Use when deciding how much autonomy to give an AI system, defining auto-act vs. human-review rules, or planning approval workflows for AI actions. Trigger on "autonomy levels," "auto-send vs review," "human in the loop," "when should the AI just do it vs. ask me first." Based on the "No Vibes, Just Evals" methodology by Shankha Dey.
---

# Autonomy Map

Help the user define exactly how much independence their AI component gets across different scenarios. The output is a decision matrix mapping every scenario to an autonomy level, with hard rules that override everything.

## Why this matters

The biggest deployment failures aren't accuracy failures — they're autonomy failures. The model was right 95% of the time, but the 5% it got wrong were cases where it shouldn't have been acting autonomously at all. The autonomy map forces you to think through every scenario *before* you build the architecture, because autonomy level determines architecture (queuing systems, approval flows, fallback routing).

## The five autonomy levels

| Level | Name | Description |
|-------|------|-------------|
| **L1** | Review All | Every output queued for human review. You decide on each one. |
| **L2** | Soft Auto | Auto-act on high confidence + known patterns. Review the rest. |
| **L3** | Smart | Auto-act on most. Review low confidence and unknowns. |
| **L4** | Full Auto | Sends autonomously. Hard rules still enforced. |
| **L5** | Autonomous | Self-improving. Extreme caution. Rarely appropriate. |

Most production AI components live at L2–L4. L1 is for initial deployment or very high-stakes domains. L5 is almost never the right starting point — if the user wants L5, push them to explain why L4 with monitoring isn't sufficient.

## The interview

1. **What's the component and what action does it take?** (e.g., "sends reply emails," "classifies and routes tickets," "generates reports"). The action matters because it determines the consequences of a wrong autonomous decision.
2. **What's your starting autonomy level?** Walk through the five levels and help them pick. Most teams should start at L2 or L3 and relax over time as they build confidence.
3. **List the scenarios.** Go through the common situations this component will encounter. For each, ask: "At your chosen level, what happens? What about one level up?"
4. **What are the hard rules?** These are scenarios where the component must *always* route to human review regardless of autonomy level or confidence score. Hard rules are the floor beneath all levels. Common hard rules: unknown sender, attachments present, confidence below threshold, financial/calendar actions.
5. **Are there scenarios that should behave differently at each level?** This is where the matrix gets interesting — the same scenario might be "draft → review" at L1 but "auto-send" at L4.

## Building the autonomy map

Create a matrix with scenarios as rows and autonomy levels as columns. For each cell, define the behavior. Mark hard rules with a ✓ in the rightmost column.

Key principles:
- **Hard rules override everything.** If "unknown sender → review" is a hard rule, it applies at L1 *and* L5. No confidence score overrides a hard rule.
- **Set autonomy level BEFORE architecture.** The level you pick determines whether you need approval queues, review dashboards, notification systems, or none of the above.
- **Write hard rules first.** They are the floor beneath all levels. Get consensus on these before debating whether normal emails should be L3 or L4.

## Output format

Generate the map in markdown:

```
# Autonomy Map: [Component Name]

_Complete this before architecture. Hard rules apply at ALL levels — no confidence score overrides them._

## Autonomy Levels

| Level | Name | Description |
|-------|------|-------------|
| L1 | Review All | Every output queued. You decide. |
| L2 | Soft Auto | Auto: high conf + known. Review: rest. |
| L3 | Smart | Auto: most. Review: low conf, unknowns. |
| L4 | Full Auto | Sends autonomously. Hard rules enforced. |
| L5 | Autonomous | Self-improving. Extreme caution. |

## Decision Matrix

| Scenario / Trigger | L1 | L2/L3 | L4 | L4+ | Hard Rule |
|--------------------|-----|-------|-----|------|-----------|
| [Scenario 1] | [behavior] | [behavior] | [behavior] | [behavior] | |
| [Scenario 2] | [behavior] | [behavior] | [behavior] | [behavior] | |
| [Hard rule scenario] | Review | Review | Review | Review | ✓ |
| [Your scenario] | [your rule] | [your rule] | [your rule] | [your rule] | |

## Hard Rules Summary
- [Hard rule 1]: Always route to review because [reason]
- [Hard rule 2]: Always route to review because [reason]

---

**The rule:** Set your autonomy level BEFORE architecture. Write your hard rules first. They are the floor beneath all levels.
```

## Guidance for filling it out

- **Start with hard rules.** Ask: "What scenarios should ALWAYS go to a human, even if we fully trust the model?" These are usually: unknown entities, financial actions, legal implications, anything with attachments, confidence below threshold. Hard rules are the easiest to agree on and the most important to get right.
- **Then fill in the normal path.** For the component's most common scenario (e.g., "normal email, known sender"), define what happens at each level. This establishes the baseline.
- **Then add the interesting scenarios.** Availability requests, multi-step workflows, escalations — these are where autonomy levels actually diverge and where the matrix earns its keep.
- **Leave blank rows.** Include 2-3 "[Your scenario] / [Your rule]" rows so the team can add scenarios they discover in production.
- **L5 is a conversation.** If someone wants L5, ask: "What does 'self-improving' mean here? What would it change about its own behavior, and how would you know if it went wrong?" Most of the time, L4 with good monitoring is what they actually want.

## After generating

Remind the user: "This map determines your architecture. A component at L2 needs a review queue and dashboard. A component at L4 needs monitoring and alerting but no approval flow. Decide the level, then build the system around it."
