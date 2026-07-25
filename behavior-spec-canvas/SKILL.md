---
name: behavior-spec-canvas
description: Define the behavioral contract for an AI component using a Behavior Spec Canvas covering guardrails, tone, confidence thresholds, and edge cases. Trigger on "how should this behave," "what are the guardrails," "spec out this AI feature," "what should this AI always/never do," or when an eval framework exists and the behavioral rules come next. Based on the "No Vibes, Just Evals" methodology by Shankha Dey.
---

# Behavior Spec Canvas

Help the user define the complete behavioral contract for a single AI component — what it must always do, what it must never do, its voice, its confidence rules, and its edge cases. One canvas per component, written in plain language, completed before code.

## Why this matters

Eval frameworks test whether the component works. Behavior specs define *how* it should work. Without a spec, every developer on the team has a slightly different mental model of what the AI should do, and you end up with inconsistent behavior that's impossible to debug. The canvas makes the implicit explicit.

## The interview

Start by identifying the component. Ask:

1. **What's the component?** Get a one-sentence description (e.g., "Email classifier that routes incoming support emails to the right team").
2. **What must it always do, no matter what?** These are non-negotiable behaviors — the things that are true regardless of input. (e.g., "Always include a confidence score," "Always preserve the original email text")
3. **Does it generate text?** If yes, ask about tone, length, style, sign-off conventions, and any forbidden phrases. If no, skip the tone/voice section.
4. **What should it absolutely never do?** Hard stops — behaviors that would be harmful, embarrassing, or dangerous regardless of context. (e.g., "Never auto-send without human review," "Never include customer PII in logs")
5. **What's your confidence threshold?** Below X% → route to human review. Above X% → proceed automatically. How did you pick X?
6. **What are the three edge cases you're most worried about?** Not hypotheticals — the specific scenarios that keep the team up at night.

Adapt the sequence to the conversation. If the user already described some of these, confirm and fill gaps.

## Building the canvas

Organize the spec into five sections:

### Always Do
Non-negotiable behaviors. These apply to every single input, every time, no exceptions. Frame them as positive statements ("Always X") rather than double negatives.

### Tone / Voice
Only relevant if the component generates text. Define:
- **Style**: Formal? Casual? Match the customer's tone?
- **Length**: One sentence? One paragraph? As long as needed?
- **Sign-off**: How does it end? (e.g., "Best, [Agent Name]" or no sign-off)
- **Forbidden phrases**: Words or patterns that should never appear (e.g., "I'm just an AI," "As a language model," company competitor names)

### Never Do
Hard stops that override everything else — including confidence scores. If the component is about to do one of these things, it should refuse or escalate, period. These are the behavioral equivalent of a circuit breaker.

### Confidence Threshold
Define the decision boundary:
- Below X% → human review
- Above X% → proceed automatically
- Document *why* X was chosen (regulatory requirement? team comfort level? error cost analysis?)

### Edge Cases
The three scenarios the team is most worried about. Write them out explicitly — not as categories ("unusual inputs") but as specific situations ("customer writes in a language we don't support while referencing an open legal case"). For each, state what the component should do.

## Output format

Generate a structured canvas in markdown:

```
# Behavior Spec Canvas: [Component Name]

_[One-sentence description of what this component does]_

---

## Always Do
- [Non-negotiable behavior 1]
- [Non-negotiable behavior 2]
- [Non-negotiable behavior 3]

## Tone / Voice
- **Style:** [description]
- **Length:** [constraints]
- **Sign-off:** [convention]
- **Forbidden phrases:** [list]

## Never Do
- [Hard stop 1]
- [Hard stop 2]
- [Hard stop 3]

## Confidence Threshold
- Below [X]% → [action, e.g., "route to human review"]
- Above [X]% → [action, e.g., "proceed automatically"]
- **Rationale:** [Why this threshold was chosen]

## Edge Cases
1. **[Scenario]:** [What should happen]
2. **[Scenario]:** [What should happen]
3. **[Scenario]:** [What should happen]

---

**The rule:** One canvas per AI component. Written in plain language. Completed before a line of code is written.
```

## Guidance for each section

- **Always Do**: Aim for 3-5 items. If you're listing 10+, you're probably mixing in preferences with non-negotiables. Ask: "Would you ship without this?" If the answer is "maybe," it's not an Always Do.
- **Tone / Voice**: The forbidden phrases list is often the most valuable part. Teams rarely think about what *not* to say until something embarrassing goes out.
- **Never Do**: These should be genuinely dangerous or unacceptable outcomes, not just suboptimal ones. "Never sounds slightly formal" is not a Never Do. "Never auto-sends financial transactions without confirmation" is.
- **Confidence Threshold**: If the user doesn't know where to set it, suggest starting conservative (higher threshold = more human review) and relaxing it after they have production data. A common starting point is 80% for low-stakes, 95% for high-stakes.
- **Edge Cases**: Push for specificity. "What if the input is weird" is useless. "What if a customer writes in Spanish but our support team only speaks English, and they're asking about a billing dispute" is actionable.

## After generating

Remind the user: "Share this with your team before sprint kickoff. If anyone disagrees with a Never Do or a threshold, that's the conversation you need to have *now*, not after launch."
