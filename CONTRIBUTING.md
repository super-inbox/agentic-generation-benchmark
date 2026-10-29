# Contributing to DRAFT-Bench

Please identify the track, release version and affected case IDs in an issue or pull request. A useful contribution includes a reproducible example and explains which observable requirement or evidence boundary changes.

## New tasks

1. Use newly authored or consented, anonymized material. Record provenance, asset rights and whether people or customer profiles are synthetic.
2. Define task inputs, context conditions, due deliverables and preservation constraints before running candidates.
3. Keep later feedback and evaluator answers out of the initial candidate projection. Export only permitted assets and preference memory.
4. Give each task a stable ID. Link variants to the base task; do not count variants, repeats or historical associations as independent customers.
5. Put new data in a versioned release and provide a checksum manifest. Do not silently overwrite v0.1 scores or transcripts.

## Results

Record the candidate/runtime/tool configuration, model label as used, seed where available, sampling settings, budgets, date, attempt IDs and frozen evaluator version. Preserve timeouts, exclusions, missing annotations and unobserved dimensions. A new RFQ result must contain independent target/disclosure annotations with exact public-dialogue evidence; a candidate's self-score is not an evaluator label.

Do not claim an exact historical rerun when prompts, tools, judge visibility, customer policy or attempt selection changed. Design submissions should identify artifact version and requirement provenance. `schemas/acceptance-record.schema.json` describes a proposed audit record, not a completed automatic evaluator.

## Expert review and calibration

Use purposively selected disagreement cases to develop acceptance criteria, then freeze the criteria before a separate, representative blind evaluation. Record expert roles, sampling, disagreement resolution and coverage. Do not estimate overall evaluator error rates from the selected R1 cases, and do not add fictional expert decisions.

## Checks

```sh
python3 -m draftbench validate
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
python3 tools/release_audit.py
```

After installing dependencies, checks have no model costs or network requirements. `tools/export_from_archive.py` is a maintainer tool for preparing a **new** release from source archives, not a requirement for normal users. `tools/build_manifest.py` rebuilds the checksum inventory during preparation; review data changes before publishing a new version.
