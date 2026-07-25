---
name: eval-framework
description: Build an eval framework for an AI feature before writing code. Use when planning an AI component, defining test scenarios, or setting up evals. Trigger on "eval framework," "test scenarios," "edge cases for AI," "how do I know if this works," "what should I test," or when someone shares an AI feature idea without saying how they'd evaluate it. Based on the "No Vibes, Just Evals" methodology by Shankha Dey.
---

# Eval Framework

Help the user define concrete test scenarios for an AI feature **before any code is written**. The goal is a filled-out eval table they can share with their engineering team at sprint kickoff.

## Why this matters

Most AI features fail not because the model is bad, but because nobody agreed on what "good" looks like before building. This framework forces that conversation upfront by defining specific inputs, expected outputs, and pass/fail thresholds for every scenario that matters — including the scary ones.

## The interview

Start by understanding what the user is building. Ask about:

1. **What's the AI component?** (e.g., email classifier, reply drafter, sentiment detector, summarizer)
2. **What's a typical input?** Get a concrete example, not an abstraction.
3. **What does a good output look like for that input?** Pin down format, tone, length, content.
4. **What's the worst thing this component could do?** This surfaces the failure mode and high-stakes scenarios naturally.
5. **Who sees the output?** (internal team, end user, customer) — this shapes thresholds.

Don't ask all five at once. Lead with #1 and #2, then let the conversation flow. If the user already described their component in the conversation, extract what you can and confirm rather than re-asking.

## Building the eval table

Once you understand the component, build a table with **at least 5 scenarios** covering these categories:

| Category | What it tests | Threshold guidance |
|---|---|---|
| **Normal case** | Typical input, happy path | >90% — this is table stakes |
| **Edge case 1** | Boundary input (unusual but valid) | >80% — should handle gracefully |
| **Edge case 2** | Another boundary (different dimension) | >80% |
| **Failure mode** | Input that should trigger refusal or fallback | 0% — must never produce normal output for this |
| **High stakes** | Input where mistakes have real consequences | 100% — conservative behavior required |
| **Your biggest fear** | The scenario the team dreads most | TBD — discuss with team |

For each scenario, fill in:

- **Scenario name** and brief description
- **Input**: A specific, realistic example (not "some text" — actual text)
- **Expected output**: What the component should produce (or refuse to produce)
- **Threshold**: The pass rate target

The "your biggest fear" scenario is intentionally left TBD — it's meant to spark a team conversation about risk tolerance.

## Output format

Generate a clean markdown table the user can paste into a doc, Notion page, or Linear issue:

```
# Eval Framework: [Component Name]

_Fill this in before you write a single line of code. Minimum 5 scenarios. Include 2 edge cases._

| Scenario | Input | Expected Output | Threshold | ✓ |
|----------|-------|-----------------|-----------|---|
| **Normal case**: [description] | [specific input] | [specific output] | >90% | ☐ |
| **Edge case 1**: [description] | [specific input] | [expected behavior] | >80% | ☐ |
| **Edge case 2**: [description] | [specific input] | [expected behavior] | >80% | ☐ |
| **Failure mode**: [description] | [specific input] | [should NOT do X] | 0% | ☐ |
| **High stakes**: [description] | [specific input] | [conservative behavior] | 100% | ☐ |
| **Your biggest fear**: [description] | [specific input] | [expected behavior] | TBD | ☐ |

**The rule:** Write at least 5 scenarios. Include 2 edge cases. Share with your team BEFORE the sprint starts.
```

## Tips for good scenarios

- Make inputs concrete. "A customer email asking about refunds" is weak. "Subject: WHERE IS MY REFUND?? Body: I ordered 3 weeks ago and still nothing. This is ridiculous. I want my money back NOW or I'm calling my bank." is strong.
- Edge cases should test different dimensions — don't just vary the same thing twice. If edge case 1 tests unusual length, edge case 2 should test unusual format or language or ambiguity.
- The failure mode threshold is 0% because this is something the component should *never* do. If your email reply drafter gets a phishing email, the correct action is to flag it, not draft a reply.
- High stakes threshold is 100% because when the consequences are real (financial actions, medical info, legal commitments), conservative behavior beats clever behavior every time.

## After generating

Remind the user: "This is a living document. Review and update it after each production incident. Use the checkboxes to track which scenarios you've actually tested."
