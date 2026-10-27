# DRAFT-Bench

**Design Reliability Across Feedback and Tasks** — open benchmark data for studying whether general-purpose agents carry design requirements through revisions and deliver verifiable work.

This is the successor to **Agentic Generation Benchmark**. The repository URL stays the same; the earlier [VIR production-image archive](https://github.com/super-inbox/agentic-generation-benchmark/tree/main/data/2026-08-03-production-gemini) remains available as a separate dataset.

**Data release v0.1.0 · October 26, 2026.** This release packages existing evidence used in the October 24 paper draft. It introduces no new model runs or expert labels. [中文说明](README.zh-CN.md) · [Dataset card](DATA_CARD.md) · [Protocol](docs/PROTOCOL.md) · [Reproduction guide](docs/REPRODUCIBILITY.md)

## What's included

| Component | Released content | What can be reproduced |
|---|---|---|
| Brief Bank v0.3 | **35 briefs / 43 conditions**, complete authored episode contracts, feedback, rubrics, and **24 project-owned input fixtures** | Inspect tasks; export condition-specific initial inputs; implement a new episode runner |
| RFQ v0.3 | **40 authored scenarios**, separate openings and evaluator truth; **100 run records** across recorded configurations, of which 99 are scored and one is infrastructure-excluded | Replay annotated transcripts with the original deterministic scorer and reproduce cohort metrics |
| Design/archive results | **333 observation associations / 301 protocol units / 272 ID lineages** | Recompute archive accounting and completion coverage; inspect numeric score intervals |
| R1 diagnostic pilot | **7 historical Sol/Astra pairs / 14 judge calls** | Inspect score repetitions and changes under revised acceptance rules |

The archive counts are **not** the number of fully runnable public tasks or statistically independent samples. Thirty-two observations are historical associations with Brief Bank conditions. Tasks outside Brief Bank and RFQ have **metadata-only** coverage in this release. R1 does not include Claude and has no final expert adjudication.

## Quick start — no API keys or dependencies

Use Python **3.10+** from this checkout:

For a smaller download, use the [standalone v0.1.0 data-and-tools ZIP](https://github.com/super-inbox/agentic-generation-benchmark/releases/download/draftbench-v0.1.0/draftbench-v0.1.0.zip), extract it, and run the Python commands below from its directory. The ZIP contains the complete DRAFT-Bench release and tools; the legacy VIR archive remains in the repository.

```sh
git clone https://github.com/super-inbox/agentic-generation-benchmark.git
cd agentic-generation-benchmark
python3 -m draftbench validate
python3 -m draftbench report
python3 -m unittest discover -s tests -v
```

`validate` checks every released data file, input-asset hashes, condition boundaries, IDs and denominators. It also recalculates **all 100 RFQ records** from archived dialogue annotations and compares the result with the frozen scores. No model is called.

Export one candidate input into a fresh directory:

```sh
python3 -m draftbench prepare design 'DAB-L4-BID-001@zero_shot' --out /tmp/draftbench-bid-input
python3 -m draftbench prepare rfq RFQ-IC-001 --out /tmp/draftbench-rfq-input
python3 -m draftbench rfq-example
```

These bundles contain an initial request and only the permitted input files. **Mount only the exported bundle in the candidate environment.** Exporting files is not an OS sandbox; the full repository contains evaluator answers and future feedback. `prepare` is a portable input projection, not a byte-for-byte recreation of the historical provider runners.

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
draftbench/     dependency-free validation, reports, input export, RFQ scoring
schemas/        machine-readable record contracts
docs/           protocol, evidence limits, and reproduction instructions
tests/          scoring and release-boundary regressions
data/2026-08-03-production-gemini/  earlier VIR image archive
```

## Scope and next contributions

This is an **open data and offline-replay release**. A provider-independent live multi-turn runner, automated design acceptance evaluator, and completed expert blind study are not included. Design output artifacts are not redistributed here, so archived design semantic judgments cannot be independently re-created from this release alone. [Reproduction coverage](docs/REPRODUCIBILITY.md) lists what works and what remains.

Contributions should preserve candidate/evaluator boundaries, record attempts and exclusions, and add evidence without overwriting frozen scores. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License and citation

Data, authored protocols and input fixtures: **CC BY 4.0**, attributed to Curify; see [LICENSE](LICENSE) and [asset provenance](DATA_CARD.md#provenance-and-rights). New Python code: **MIT**, see [LICENSE-CODE](LICENSE-CODE). Public-source task patterns are paraphrased; the new release does not redistribute the original third-party media.

Please cite the dataset using [CITATION.cff](CITATION.cff):

> Curify (2026). *DRAFT-Bench: Design Reliability Across Feedback and Tasks*. Open data release v0.1.0. https://github.com/super-inbox/agentic-generation-benchmark

Maintained by [Curify](https://curify-ai.com). The accompanying research paper is a working draft; this repository does not claim an arXiv identifier or conference acceptance.
