# Evaluation protocol

## Design track: requirements and evidence

A base brief contains allowed inputs, reference roles, constraints, checkpoints, later feedback, expected deliverables, a scoring contract and observable verification requirements. `context_conditions` selects which inputs and preference memory are available. The four ablation briefs have `zero_shot`, `reference_grounded` and `personalized` conditions; other briefs have one condition. Conditions of the same brief are not independent business tasks.

For an evaluation runner:

1. Export the chosen first-turn request and only its permitted input assets. Preserve the source files and their hashes.
2. Reveal scripted feedback only when its checkpoint/session is due. Keep the expected state and later feedback with the controller.
3. Record the agent's delivered version, the requested edit, protected properties, and declared blockers. Do not replace the actual candidate output with a candidate-authored diagnostic image.
4. Test structural facts and semantic obligations separately. Missing files, unchanged content, incorrect edits and unmet prerequisites require different evidence.
5. Record completion, unobserved quality, justified clarification and professional acceptance separately. A model judgment or file-presence check is not an expert acceptance label.

`prepare` exports the original first-turn projection; `prepare --complete` adds public deliverables and constraints.
Toolkit v0.2 supplies a separate portable runner and provisional API evaluator, documented in [RUNNING.md](RUNNING.md).
Its scripted feedback follows each completed adapter turn, and its judge sees public replies as well as submitted files.
Those choices define a new protocol; the historical settings below describe archived evidence, not the new runner.
Neither input projection nor a subprocess cwd creates OS isolation.

### Historical design settings

The main comparison attempts 43 conditions per system, with a **60-minute active-call limit per turn**. The authored feedback is delivered in sequence. Claude's eight failures are first-turn timeouts, with no infrastructure retries in this design track. Astra has built-in image generation; Claude uses code/native production without an image-generation model, MCP, skills or subagents. Runtime, date, tools and isolation therefore differ.

Archived judgments use Gemini 2.5 Pro at temperature zero, with condition-aware scoring and the `v04-weighted-only-v1` policy. Hard-gate vetoes are disabled; external weighted pass is ≥0.70. Core intervals preserve unmeasured dimensions. These are coverage bounds, not statistical confidence intervals.

### What the judge saw

The main core scorer sees condition-specific requirements, scripted feedback, input images, selected output-version images, business-deliverable text and evaluator-computed file facts. It does not read the complete tool trace or turn-final responses. Candidate verification reports are excluded as proof. Image selection defaults to at most ten core or twelve external images, with further size and text limits. The external scorer additionally receives aggregate trajectory counts.

The paper's direct artifact audit reads additional final responses to distinguish declared dependencies from completion claims. That richer view does not retroactively alter the original scoring input. The open data release does not include the design output artifacts needed to independently rejudge those scores.

## RFQ track: elicited coverage

Each of 40 immutable scenarios has seven fields: use case, volume, input assets, output, style/reference, deadline and budget. A field can be known, undecided, unknown or not applicable. Some fields are marked critical; the candidate cannot see these labels or hidden answers.

One round is an agent message followed by one actual customer reply. The opening is not a round. The maximum is eight rounds; an early stop carries forward the observed prefix without synthetic replies. A router identifies explicitly requested fields in message order, and the controller selects the **first** understandable field, including repeats and unknowns. Fixed rendering returns only that field's authored answer. Router and annotator judgments remain distinct roles.

Independently annotated, literal dialogue evidence determines when each component first appears. Later repetition cannot convert an unprompted disclosure into elicited credit. The deterministic scorer computes:

- **Elicited Coverage@6 / @8:** macro-average across cases of fully elicited applicable fields, excluding initially complete fields from the denominator.
- **Success@8:** unrounded elicited coverage ≥0.8 and every critical field initially complete or fully elicited.
- **Simulator leak rate:** total unique unprompted fields divided by total unique disclosed fields across scored cases; null when unresolvable.

There is no composite score. A final summary is diagnostic only and cannot backfill earlier evidence. Simulator mistakes and agent failures remain in the denominator; approved infrastructure exclusions have null metrics. Incomplete annotations are an error, not a zero. Uncertain labels produce provisional bounds.

The reference arithmetic and worked examples are in `draftbench/rfq/`. [Role prompts](RFQ_ROLE_PROMPTS.md) describe the candidate/router/renderer/annotator boundaries. Toolkit v0.2 includes an online Gemini router and a separate evidence-auditor call, with fixed authored customer replies. These new auxiliary-model settings are distinct from the archived experiments.

## R1 and human calibration

R1 is a separate seven-pair historical Sol/Astra rejudging pilot with fourteen Gemini calls, two opposite anonymous presentations per pair, and revised task-specific rules. Original aggregates remain unchanged. Three pairs vary between presentations; rule changes, evidence handling and random/order effects are not separately isolated. Final expert adjudication remains pending.

The proposed `acceptance-record` schema supports future expert audits. The new API evaluator supplies provisional requirement verdicts in its own evaluation-result format; it does not populate expert labels or establish accepted delivery. Selected disagreement cases can develop criteria; a separate blind sample is needed to estimate evaluator error rates.
