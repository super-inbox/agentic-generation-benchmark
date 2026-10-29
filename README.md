# DRAFT-Bench

**Design Reliability Across Feedback and Tasks** — open benchmark data for studying whether general-purpose agents carry design requirements through revisions and deliver verifiable work.

This is the successor to **Agentic Generation Benchmark**. The repository URL stays the same; the earlier [VIR production-image archive](https://github.com/super-inbox/agentic-generation-benchmark/tree/main/data/2026-08-03-production-gemini) remains available as a separate dataset.

**Runnable toolkit v0.2.0 · October 29, 2026**, using the unchanged **v0.1.0 frozen data**. Run all 43 public design conditions and 40 RFQ scenarios with your own agent, then evaluate with a configured Gemini API key. This software release adds no empirical model results or expert labels. [中文说明](README.zh-CN.md) · [Run guide](docs/RUNNING.md) · [Dataset card](DATA_CARD.md) · [Protocol](docs/PROTOCOL.md)

## What's included

| Component | Released content | What can be reproduced |
|---|---|---|
| Brief Bank v0.3 | **35 briefs / 43 conditions**, complete authored episode contracts, feedback, rubrics, and **24 project-owned input fixtures** | Export complete inputs; run scripted multi-turn tasks; evaluate versioned artifacts |
| RFQ v0.3 | **40 authored scenarios**, separate openings and evaluator truth; **100 run records** across recorded configurations, of which 99 are scored and one is infrastructure-excluded | Run new conversations with independent routing/auditing; replay archived annotations with the original scorer |
| Design/archive results | **333 observation associations / 301 protocol units / 272 ID lineages** | Recompute archive accounting and completion coverage; inspect numeric score intervals |
| R1 diagnostic pilot | **7 historical Sol/Astra pairs / 14 judge calls** | Inspect score repetitions and changes under revised acceptance rules |

The archive counts are **not** the number of fully runnable public tasks or statistically independent samples. Thirty-two observations are historical associations with Brief Bank conditions. Tasks outside Brief Bank and RFQ have **metadata-only** coverage in this release. R1 does not include Claude and has no final expert adjudication.

## Quick start — no API keys or dependencies

Use Python **3.10+** from this checkout:

The [archived v0.1.0 ZIP](https://github.com/super-inbox/agentic-generation-benchmark/releases/download/draftbench-v0.1.0/draftbench-v0.1.0.zip) remains available for offline replay. Use the current checkout for the v0.2 runner and API evaluator.

```sh
git clone https://github.com/super-inbox/agentic-generation-benchmark.git
cd agentic-generation-benchmark
python3 -m draftbench validate
python3 -m draftbench report
python3 -m draftbench list
```

`validate` checks every released data file, input-asset hashes, condition boundaries, IDs and denominators. It also recalculates **all 100 RFQ records** from archived dialogue annotations and compares the result with the frozen scores. No model is called.

Export one candidate input into a fresh directory:

```sh
python3 -m draftbench prepare design 'DAB-L4-BID-001@zero_shot' --complete --out /tmp/draftbench-bid-input
python3 -m draftbench prepare rfq RFQ-IC-001 --out /tmp/draftbench-rfq-input
python3 -m draftbench rfq-example
```

These bundles contain an initial request and only the permitted input files. **Mount only the exported bundle in the candidate environment.** Exporting files is not an OS sandbox; the full repository contains evaluator answers and future feedback. `prepare` is a portable input projection, not a byte-for-byte recreation of the historical provider runners.

## Run and evaluate your agent

```sh
python3 -m pip install -r requirements-eval.txt
cp .env.example .env
# Set DRAFTBENCH_EVAL_API_KEY in .env, keeping it local.
python3 -m draftbench --env-file .env doctor

# Replace this with your installed agent adapter; use an absolute path.
AGENT_COMMAND="python3 /absolute/path/to/your_adapter.py"
python3 -m draftbench --env-file .env run design 'DAB-L4-BID-001@zero_shot' \
  --agent-command "$AGENT_COMMAND" --out runs/design-one --evaluate
python3 -m draftbench --env-file .env run rfq RFQ-IC-001 \
  --agent-command "$AGENT_COMMAND" --out runs/rfq-one --evaluate
python3 -m draftbench summarize --runs runs/design-one --out runs/design-summary
```

The evaluator key is enough for **judging saved runs**; generating new outputs also needs your agent and its tools/credentials.
The [working CLI bridge](examples/command_adapter.py) accepts a prompt-reading agent executable, so a custom adapter is optional.
The [step-by-step guide](docs/RUNNING.md) includes an offline demo, API connectivity check, all-task batches, rejudging,
JSON/CSV outputs and the [adapter interface](docs/ADAPTER.md).

The evaluator reads actual image/PDF evidence and public dialogue. Internal tool traces are not included.
Unobserved dimensions remain null with explicit quality bounds; model flags do not establish professional acceptance.
Three missing-prerequisite briefs intentionally require clarification. No private asset download is needed.

## What the current evidence says

- Runtime completion and professional acceptance are different endpoints. In the primary 43-condition design comparison, recorded completion is Astra **43/43** and Claude **35/43**; the eight missing Claude quality observations are timeouts, not measured zero-quality designs.
- RFQ results depend on the comparison cohort. On the **39 jointly scored cases**, Astra succeeds on **36** and Claude on **34**. Removing three original-cohort Claude reattempt cases from both systems gives **33/36** and **32/36**. Router/auditor settings and continuation histories also differ across cohorts.
- The R1 pilot demonstrates sensitivity to acceptance rules and evidence handling. Three pairs vary between the two presentations. It does not establish a validated evaluator or an expert acceptance rate.

These are archived configured-system results, **not a universal model ranking**. The configurations differ in runtime, tools, isolation and dates; the recorded model labels are not claims of current public API availability. See [results and denominators](docs/RESULTS.md).

## Repository map

```text
data/draft-bench-v0.1/
  briefs/       authored episodes and initial condition projections
  assets/       24 input fixtures, rights metadata, and hashes
  rfq/          candidate openings and evaluator-only cases
  results/      archived RFQ evidence/scores, numeric archive, R1, settings
  manifest.json checksums and reproducible counts
  provenance.json source hashes and export transformations
draftbench/     offline replay, input export, runner, API evaluation and summaries
examples/       CLI bridge and synthetic plumbing demo
schemas/        machine-readable record contracts
docs/           protocol, evidence limits, and reproduction instructions
tests/          scoring and release-boundary regressions
data/2026-08-03-production-gemini/  earlier VIR image archive
```

## Scope and next contributions

The portable runner and provisional API evaluator are included. A completed expert blind study and validated automatic acceptance grader are still absent. The new protocol exposes a fuller public task contract and uses its own feedback schedule and judge visibility; do not pool its scores with historical experiments. Historical design output artifacts are not redistributed here, so their original semantic judgments cannot be independently re-created from this release alone. [Reproduction coverage](docs/REPRODUCIBILITY.md) distinguishes new runs from historical replay.

Contributions should preserve candidate/evaluator boundaries, record attempts and exclusions, and add evidence without overwriting frozen scores. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License and citation

Data, authored protocols and input fixtures: **CC BY 4.0**, attributed to Curify; see [LICENSE](LICENSE) and [asset provenance](DATA_CARD.md#provenance-and-rights). New Python code: **MIT**, see [LICENSE-CODE](LICENSE-CODE). Public-source task patterns are paraphrased; the new release does not redistribute the original third-party media.

Please cite the dataset using [CITATION.cff](CITATION.cff):

> Curify (2026). *DRAFT-Bench: Design Reliability Across Feedback and Tasks*. Open data release v0.1.0. https://github.com/super-inbox/agentic-generation-benchmark

Maintained by [Curify](https://curify-ai.com). The accompanying research paper is a working draft; this repository does not claim an arXiv identifier or conference acceptance.
