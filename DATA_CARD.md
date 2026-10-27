# DRAFT-Bench v0.1.0 dataset card

## Purpose and version

DRAFT means **Design Reliability Across Feedback and Tasks**. The release supports analysis of requirement elicitation, design revisions, preservation obligations and delivery evidence. Release date: **2026-10-26**. Archive data date: **2026-10-23**. Paper reconciliation: **2026-10-24**. Packaging version v0.1.0 is distinct from the underlying **Brief Bank v0.3** and **RFQ v0.3** protocols.

The intended users are agent researchers and evaluation developers. These development cases and diagnostic examples are not a previously unseen holdout and must not be presented as one. We publish evaluator material for reproducibility; candidate agents must not access it during evaluation.

## Composition and counting

| Level | Count | Meaning |
|---|---:|---|
| Brief Bank base briefs | 35 | 24 core plus 11 public-corpus-grounded authored extensions |
| Brief Bank conditions | 43 | 32 core conditions plus 11 external conditions; four core briefs have three context conditions |
| Project-owned input fixtures | 24 | 18 reference-pack assets plus six extension assets, including two edit masks |
| RFQ scenarios | 40 | 20 original synthetic scenarios plus 20 authored variants from four real-scenario families |
| RFQ archived run records | 100 | Original 20 × three configurations; extension 20 × two configurations |
| Scored RFQ run records | 99 | One extension Claude infrastructure exclusion remains unscored |
| Archive observations | 333 | Associations with protocol records, not model runs |
| Archive protocol units | 301 | 261 design-related units plus 40 RFQ units |
| Archive ID lineages | 272 | Deduplication by archived brief/scenario identity, not statistical independence |
| Historical associations | 32 | Earlier Brief Bank v0.2 observations associated with the v0.3 core; no new executions |
| R1 pilot | 7 pairs / 14 calls | Historical Sol/Astra only; no new candidate runs |

The separate Sol extension attempt had 20 planned cases but zero scored cases, with 60 HTTP 429 failures among 64 native calls and two actual customer rounds. Its summary is in experiment settings; these incomplete attempts are **not** among the 100 replayable RFQ records and are not zeros in ability comparisons.

## Data files and access roles

All paths below are relative to `data/draft-bench-v0.1/`.

| File | Contents | Evaluation access |
|---|---|---|
| `briefs/episodes.jsonl` | Full authored design contracts, constraints, conditions, later feedback, rubrics and verification requirements | Evaluator/controller only |
| `briefs/conditions.jsonl` | 43 condition-specific first-turn projections | Controller; export only the selected condition |
| `assets/manifest.jsonl` | Paths, sizes, hashes, rights and synthetic-person metadata | Controller; export only condition-allowed assets |
| `rfq/openings.jsonl` | 40 vague opening messages | Controller; export one opening |
| `rfq/evaluator_cases.jsonl` | Immutable fields, critical labels, expected answers and initially known components | Evaluator/controller only |
| `results/rfq_episodes.jsonl` | Candidate/customer utterances, routing, selected fields and disclosure annotations | Offline evaluator; never candidate context |
| `results/rfq_scores.jsonl` | Frozen per-run metrics and checkpoint evidence | Analysis only |
| `results/archive_observations.jsonl` | Observation-to-unit and brief-lineage associations | Analysis only |
| `results/archive_units.jsonl` | Numeric status/score records with input-release scope | Analysis only |
| `results/calibration_r1.json` | Separate diagnostic rejudging scores and repetitions | Analysis only |
| `results/experiment_settings.json` | Settings, denominators, amendment and continuation metadata | Analysis/controller |
| `provenance.json` | Input hashes and explicit export transformations | Maintainer/audit |
| `manifest.json` | Release inventory and SHA-256 checksums | Validation |

Design contracts are mainly Chinese with mixed English technical terms. RFQ candidate/customer dialogue is English. An episode's `expected_workflow` describes observable checkpoints, not private chain-of-thought or a mandatory internal reasoning path.

## Provenance and rights

All 35 brief contracts explicitly have `customer_data: false`: nine are reverse-constructed from documented workflows, seven are de-identified or substituted internal scenarios, eight are controlled synthetic cases, and eleven paraphrase public-corpus task/failure patterns. Their prompts and controlled feedback are authored benchmark material, not verbatim customer conversations.

All 24 input fixtures carry upstream `project_owned_test_fixture` metadata and `contains_personal_data: false`; generated people are flagged as synthetic. Their bytes are verified against the original asset manifests. The six extension assets contain four newly generated sources and two deterministic masks; no Reddit post image is copied. The release applies the existing repository **CC BY 4.0** terms to these data and fixtures, with attribution to **Curify, DRAFT-Bench**. Original third-party media is not included in the new release. The earlier VIR dataset keeps its existing files and scope.

The RFQ extension is grounded in hotel retouching, paired scene enhancement, educational animation and ski-opening-poster scenarios, with authored variants and assumptions. “Real-scenario-grounded” does not mean a recorded customer transcript. Candidate/customer dialogue here comes from benchmark model runs and fixed replies. Author-side private source pointers, raw provider/tool logs, access tokens, local filesystem paths and hidden reasoning are not exported. Private archive identifiers retained in some brief provenance are historical references, not dependencies or publicly downloadable files.

The source archive is pinned to dashboard source commit `67815928a139bd2f878e1bdedf517a93f00da5ba`; logical source IDs and content hashes are included without private paths. No API credentials or account access are needed to consume the release.

## Labels and limitations

- **Human review is not completed.** Archived semantic annotations and R1 scores are model judgments. There is no expert-confirmed acceptance, false-positive or false-negative rate.
- Runtime completion, selected-subset quality bounds and professional acceptance must be reported separately. Bounds for unobserved dimensions are not statistical confidence intervals.
- Eight Claude design timeouts have missing quality observations. A completed-subset comparison has selection bias; missing values cannot be silently replaced with zero or dropped from completion denominators.
- The two RFQ cohorts differ in auxiliary models and continuation history. An amended view includes original Claude reattempts for cases 004, 009 and 019; the strict paired view removes those from both systems. It does not remove the other confounds.
- R1 used revised acceptance rules, evidence handling and two opposite anonymous presentations. Rule changes and stochastic/order variation are not separately identifiable. R1 neither replaces original scores nor validates the evaluator.
- RFQ and design are unpaired tracks. No downstream design improvement from higher RFQ coverage has been established.
- Source/output artwork, complete traces and online provider runners for the broader archive are not supplied. Metadata-only groups cannot be rerun from this release. The new design input bundles are not historical prompt-byte replicas.
- Fixed development cases, single candidate samples and purposive case studies do not establish broad model rankings or population error rates.

## Maintenance

Data releases are immutable after publication. Correct a discovered issue through an explicit version/amendment that preserves original evidence, affected IDs and changed denominators. Report a rights, privacy or data-quality issue through this repository's issue tracker without posting additional sensitive material. See [contribution guidance](CONTRIBUTING.md).
