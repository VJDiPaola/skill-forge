---
name: api-prompt-optimizer
description: "Systematic prompt optimization for image/video generation APIs (Runway, Midjourney, DALL-E, Flux, etc.). Trigger on: 'optimize this prompt', 'A/B test prompts', 'improve generation quality', 'prompt iteration', 'eval my prompts', 'systematic prompt comparison', or when scoring generation outputs is mentioned, comparing before/after results, or building a prompt testing pipeline."
---

# API Prompt Optimizer

A methodology for systematically improving prompts for image and video generation APIs. This isn't about writing one good prompt. It's about building a testing loop that reliably finds the best prompt for a specific use case through structured iteration.

This methodology was validated on a real project: 10 prompt iterations across 33+ generations with scored evaluations on Runway's Gen-4 Image API, producing measurable improvement in shape preservation, color accuracy, and realism.

## Phase 1: Define Evaluation Criteria

Before writing a single prompt, define what "good" looks like. Without this, you're optimizing by vibes.

### Set Up the Rubric

Pick 3-5 scoring dimensions relevant to your use case. Common dimensions for image generation:

- **Shape/form accuracy** -- Does the output preserve the intended geometry?
- **Color accuracy** -- Does the output match the target color/palette?
- **Realism** -- Does the output look photographic/believable?
- **Style consistency** -- Does the output match the intended aesthetic?
- **Prompt adherence** -- Did the model follow the specific instructions?
- **Detail preservation** -- Are fine details (textures, edges, small elements) maintained?

For each dimension, anchor the scale:
- **1/5:** [Describe what failure looks like for this dimension]
- **3/5:** [Describe acceptable but not great]
- **5/5:** [Describe the ideal output]

### Identify Ground Truth

If available, find a real reference for what the output should look like. A real photo, an existing design, a previous generation that nailed it. Ground truth makes scoring less subjective and helps calibrate across test runs.

### Build the Test Set

Select 3-5 diverse inputs that cover the range of what the system will encounter:
- The easy case (what should always work)
- The hard case (where you expect the model to struggle)
- The edge case (unusual inputs that test robustness)
- At least 2 different "types" of input if applicable

More inputs = more reliable results, but 3-5 is enough for rapid iteration. Expand to 10+ for final validation.

## Phase 2: Baseline Prompt

Write a straightforward prompt that describes what you want without any optimization tricks. Run it on all test inputs. Score every output on every dimension.

This is your baseline. Every future iteration gets compared against this, not against the previous iteration. Comparing against baseline prevents drift where you "improve" on a bad iteration without actually getting better than where you started.

### Record the Baseline

For each test input, record:

| Input | Dim 1 | Dim 2 | Dim 3 | Notes |
|-------|-------|-------|-------|-------|
| input_1 | 3/5 | 2/5 | 4/5 | [What went wrong/right] |
| input_2 | ... | ... | ... | ... |
| **Average** | **X** | **X** | **X** | |

## Phase 3: Hypothesis-Driven Iterations

Each new prompt version tests ONE specific change. This is the discipline that makes the process work. If you change three things at once and the output improves, you don't know which change helped.

### How to Form Hypotheses

Look at where the baseline failed and ask why. Common prompt optimization hypotheses:

**Anti-drift language:** "Adding explicit constraints ('do NOT alter the shape') will prevent the model from making unwanted changes."
- When to try: Model is modifying things you want preserved

**Descriptive vs. prescriptive:** "Describing what the result looks like ('a thin band may be visible at the base') will work better than instructing ('leave 10% unglazed')."
- When to try: Prescriptive instructions get wildly misinterpreted

**Negative constraints:** "Telling the model what NOT to do ('do NOT flatten, widen, or compress') will prevent common failure modes."
- When to try: The model keeps making the same specific mistakes

**Context injection:** "Adding context about the input ('this piece is made of red stoneware clay') will improve output accuracy."
- When to try: The model lacks domain knowledge that affects the output

**Intensity calibration:** "Softening/strengthening the instruction language will move the model's output closer to the target."
- When to try: Outputs are consistently too aggressive or too subtle on a dimension

**Minimal prompt:** "Removing most instructions and letting the model use its own judgment will actually produce better results."
- When to try: Always worth testing. Sometimes less is more.

### Run and Score

For each iteration:
1. Change one thing from the baseline (or from the best-performing version so far)
2. Run on all test inputs
3. Score every output on every dimension
4. Compare against baseline (not just the previous iteration)

### The Results Table

| Input | Baseline Dim 1 | Prompt A Dim 1 | Baseline Dim 2 | Prompt A Dim 2 | Winner |
|-------|---------------|----------------|----------------|----------------|--------|
| input_1 | 3/5 | 4/5 | 2/5 | 3/5 | A |
| input_2 | 3/5 | 2/5 | 4/5 | 4/5 | Baseline |

Check per-input scores, not just averages. An improvement that raises the average but causes regression on specific inputs is a tradeoff, not a pure win.

## Phase 4: Compound Improvements

Once you've validated individual hypotheses, combine the winners. But test the compound prompt against baseline, because prompt instructions can interact in unexpected ways.

Common interactions to watch for:
- **Shape lock + color matching** can conflict (aggressive shape preservation may suppress color changes)
- **Negative constraints stacking** can over-constrain the model (too many "do NOT" instructions)
- **Context + style instructions** may pull in different directions

If the compound prompt underperforms on any dimension compared to its individual components, there's an interaction effect. Try removing one element at a time to find the conflict.

## Phase 5: Document the Evolution

For each prompt version, record:

### Prompt [Letter]: [Descriptive Name]

**Hypothesis:** What you expected this change to do

**Prompt text:**
> [The exact prompt, quoted]

**Key change from previous:** [What was added/removed/modified]

**Results:**

| Input | Dim 1 | Dim 2 | Dim 3 | vs. Baseline |
|-------|-------|-------|-------|-------------|
| ... | ... | ... | ... | +/- |

**Decision:** Keep / Discard / Merge into next iteration. [One sentence why.]

## Phase 6: Final Validation

Once you have a winning prompt:
1. Run it on an expanded test set (10+ inputs including new ones not used during iteration)
2. Score everything
3. Compare against baseline on the full set
4. Document the final pipeline (prompt + preprocessing + parameters)

## Key Principles

**Change one thing at a time.** This is the single most important discipline. Without it, you're guessing.

**Check per-input scores, not just averages.** A prompt that scores 4.0 average but fails catastrophically on one input type is worse than a 3.5 that's consistent.

**Watch for instruction conflicts.** Aggressive instructions on one dimension can suppress performance on another. If adding something helps dimension A but hurts dimension B, the instructions are fighting each other.

**Descriptive beats prescriptive.** For most generation models, describing what the result looks like ("a thin unglazed band at the base") works better than telling the model what to do ("leave 5-10% unglazed"). Prescriptive instructions get misinterpreted more often.

**The winning prompt is rarely the most aggressive.** It's the one that balances all dimensions. Over-optimizing for one dimension usually costs you on others.

**Test on diverse inputs.** A prompt that works great on your best test case but fails on edge cases isn't production-ready.

**Don't chase variance.** If running the same prompt twice gives scores of 3/5 and 5/5, that's noise, not a real difference. Run at least 2-3 generations per configuration before drawing conclusions.

## Quick Reference: Common Failure Patterns

| Symptom | Likely Cause | Try This |
|---------|-------------|----------|
| Model changes things you want preserved | No explicit preservation language | Add anti-drift constraints |
| Output is too intense/saturated | Aggressive reference material | Add calibration language ("softer than the reference") |
| Specific instructions wildly misinterpreted | Prescriptive phrasing | Rewrite as descriptive observation |
| Good on average but catastrophic on some inputs | Over-fit to easy cases | Test on harder inputs, soften constraints |
| Multiple dimensions regressing together | Instruction conflicts | Remove elements one at a time to find the conflict |
| Inconsistent results across runs | High model variance | Run 3x per config, use the median |
