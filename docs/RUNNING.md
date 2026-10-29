# Run a new evaluation

Toolkit **0.2.0**, protocol **draftbench-portable/0.2**, frozen data **draft-bench-v0.1**.
Python 3.10+ on macOS/Linux. The subprocess runner uses POSIX process groups for timeouts.

The repository contains all released inputs for **43 design conditions / 35 briefs** and **40 RFQ scenarios**.
Each design condition has its own prompt, permitted assets, inline copy/specifications and optional preference context.
All 24 image/mask fixtures are included with hashes; there is no private download step. RFQ includes opening messages,
evaluator-only customer facts, and fixed customer replies. Three design briefs deliberately lack legal copy,
material thickness or a manufacturer dieline. Their absence is part of the task; never manufacture an approved value.
The wider numeric archive is not an additional executable task set.

## Install and configure the evaluator

```sh
git clone https://github.com/super-inbox/agentic-generation-benchmark.git
cd agentic-generation-benchmark
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-eval.txt
cp .env.example .env
# Edit .env locally: set DRAFTBENCH_EVAL_API_KEY to your Gemini API key.
python -m draftbench --env-file .env doctor
python -m draftbench list --track design
python -m draftbench list --track rfq
```

`doctor` checks all public input bundles, optional image/PDF dependencies, and whether a key is configured.
It does not print the key or call a model. `doctor --check-api --out runs/api-check-1` additionally sends one tiny
paid request and stores its request, response and model metadata. Use a fresh output directory per attempt.

The default judge is `gemini-3.8-flash`, configurable through `DRAFTBENCH_EVAL_MODEL` or the global
`--judge-model` option. Freeze the model and settings before comparing systems. The historical judge label
is not silently reused: new accounts may have different model access. The client uses the documented
[Gemini generateContent API](https://ai.google.dev/api/generate-content), JSON output, temperature 0 and
inline [image inputs](https://ai.google.dev/gemini-api/docs/image-understanding).
Current model access is described in Google's [model catalog](https://ai.google.dev/gemini-api/docs/models).
The client makes no semantic resampling retries. HTTP 429/500/502/503/504 have at most two logged transport
retries; all other API errors stop that evaluation and produce no score. Provider calls may incur charges.

## Connect your candidate agent

The **evaluator key** is sufficient to evaluate saved portable runs. Running a new task additionally requires
your own candidate agent, its tools and its credentials. There is no hidden hosted candidate service.

An adapter is any trusted executable that reads **one JSON request from stdin**, works in the exported
candidate directory, and prints **one JSON response to stdout**. Send diagnostic logs to stderr.
The full interface and a working bridge are in [the adapter contract](ADAPTER.md).

If your CLI reads a prompt on stdin, no adapter implementation is needed:

```sh
BENCH_ROOT="$PWD"
AGENT_COMMAND="python $BENCH_ROOT/examples/command_adapter.py -- your-agent-cli your-noninteractive-flags"
```

Replace `your-agent-cli your-noninteractive-flags` with the actual installed agent command. The bridge also
supports a literal `{prompt}` argument for CLIs that take their prompt as an argument. Use absolute executable/script
paths and quote paths containing spaces. Keep candidate settings constant across conditions and record its tool environment.
This bridge captures text replies and files; it does not configure provider-specific sandboxes or image-generation tools.

For an **offline plumbing check**, this command is runnable as written and makes no model calls:

```sh
python -m draftbench run design 'DAB-L4-BID-001@zero_shot' \
  --agent-command "python $PWD/examples/mock_agent.py" --out runs/plumbing-demo
python -m draftbench summarize --runs runs/plumbing-demo
```

The mock writes a labelled placeholder, not a task solution. Never report its synthetic checks as empirical results.

## One real task and its evaluation

```sh
python -m draftbench --env-file .env run design 'DAB-L4-BID-001@zero_shot' \
  --agent-command "$AGENT_COMMAND" --out runs/design-one --evaluate

python -m draftbench --env-file .env run rfq RFQ-IC-001 \
  --agent-command "$AGENT_COMMAND" --out runs/rfq-one --evaluate
```

Design runs receive the complete public task contract, initial references and only the feedback revealed so far.
One adapter invocation produces v0; each subsequent invocation receives the next authored feedback message.
The harness keeps the candidate workspace between turns and snapshots declared artifacts outside it.
The full public conversation is supplied at every invocation, including across authored session labels;
this is filesystem/version continuation, **not a native provider context-reset experiment**.
The authored checkpoint labels do not gate the harness: scripted feedback advances after an `ok` response.
Whether the agent earned that checkpoint is evaluated from its artifacts and reply. This schedule is a
declared new protocol, not identical to the historical checkpoint-driven runners.

RFQ runs need the evaluator key even without `--evaluate`, because a pre-response router identifies the first
explicitly requested field. The renderer returns exactly that field's authored answer; repeats and unknown values
still consume a round. A separate post-run auditor annotates literal evidence and audits routing. The existing
RFQ v0.3 scorer computes coverage@6, coverage@8, success@8 and leak rate from those annotations.
At most eight actual customer replies are generated; an early final summary generates no artificial reply.

Default candidate timeout: 3,600 seconds **per turn**, configurable with `--timeout`. No failed candidate turn is retried.
The suite records failures and continues. A nonzero CLI exit signals agent/timeout/router/evaluation errors.

## Batch and rejudge

```sh
# Start small: these explicitly select the first two public conditions.
python -m draftbench --env-file .env run design --all --limit 2 \
  --agent-command "$AGENT_COMMAND" --out runs/design-pilot --evaluate

# Omit --limit only when you intend to run all 43 design conditions (or all 40 RFQ cases).
# Rejudge a saved run without rerunning its candidate:
python -m draftbench --env-file .env evaluate --run runs/design-one --out runs/design-one/evaluation-r2
python -m draftbench summarize --runs runs/design-one --evaluation-name evaluation-r2 --out runs/summary-r2
```

Maximum evaluator calls: one per scored design episode; up to eight router calls plus one auditor call per RFQ episode,
before transport retries. Candidate calls, tool usage, image generation and costs are additional.
`--all` writes `summary.json` and `summary.csv`. Separate repeats, rejudges and different judge settings into different
summaries; the summarizer rejects duplicate task IDs and mixed requested judge configurations.

## What is actually evaluated

Design evidence includes the task inputs, candidate's public replies, revealed feedback, immutable version snapshots,
and local file facts. PNG/JPEG/WebP pixels are decoded and attached as JPEG previews up to 1,280 pixels on each side.
PDFs of at most 4 MB and 30 pages are attached as PDFs. Text/JSON/SVG/HTML is read as source text up to 64 KB per file;
SVG/HTML is **not rendered or executed**. Supply PNG or PDF previews for visual inspection of those formats.
Unsupported formats still appear in the inventory, with `content_seen=false`.

The total attachment budget is 12 MB / 32 visual attachments. Inputs come first, followed by latest-to-oldest outputs.
Every omission, resize and truncation is recorded in `evaluation/evidence.json`. Original files and hashes remain in the run.
A candidate's own `verification.json` is an assertion, not independent proof. Internal tool traces and private reasoning
are not part of this evaluator's input; efficiency stays unobserved. Pixel-exact preservation, vector structure, fonts,
print readiness and factory approval require suitable original-file tests or human checks; a preview cannot establish them.

Each authored criterion receives PASS / VIOLATED / UNKNOWN / NOT_APPLICABLE with cited evidence IDs and reasons.
Each rubric dimension receives a score in [0,1] or null. Code calculates a lower/upper quality bound from the frozen weights:
the lower bound adds observed contributions, and the upper adds the unobserved weight. The lower bound is **not** a point
estimate. Semantic gate flags are reported separately without a score veto. `accepted_delivery` stays null.
These are provisional model judgments; no expert calibration or error-rate estimate is implied.

Execution completion, evaluation coverage and quality are separate. A design timeout/agent error leaves quality unobserved.
An RFQ agent failure with a valid dialogue prefix is scored on that prefix under the existing protocol; router/API failures
leave evaluation missing. A blocked design can be inspected for appropriate clarification, but is not counted as completed.

## Outputs and reproducibility

```text
RUN/
  candidate/                 public requests, permitted input assets, candidate working files
  evidence/v0/...            immutable declared output snapshots, then v1, v2, ...
  run.json                   inputs, public replies, status, timings, command, source hashes
  router/round-N/             RFQ router request/response and transport metadata (evaluator-only)
  evaluation/
    result.json              typed result, nullable metrics, coverage and provenance
    evidence.json            design payload and inspected/omitted file inventory
    annotation.json          raw model annotation, including invalid outputs for audit
    judge-call/              prompt/input, response, resolved model, usage and retry logs
    annotated_episode.json   RFQ independently annotated evidence
    rfq_score.json           RFQ deterministic score and diagnostic bounds
```

`.env` and `runs/` are ignored by Git. API keys are sent only in request headers, not saved configuration.
Evaluator key environment variables are removed from the candidate subprocess. **This is not an OS sandbox**:
for formal adversarial evaluation, the adapter must dispatch to a separate container/machine with only `candidate/`
mounted and candidate-only credentials. Do not mount the repository, evaluator records or `.env` into that environment.
Public task data can be memorized; it is not a secret holdout. Preserve the adapter version, provider/model IDs, tool versions,
isolation setup, installed dependencies and budgets when publishing new results. No exact repeatability of hosted model
sampling or equivalence to historical Codex/Claude configurations is promised.

Offline historical replay still works without dependencies or API keys. See [reproduction coverage](REPRODUCIBILITY.md).
