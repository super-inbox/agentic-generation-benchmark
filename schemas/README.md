# Record contracts

- `brief-v0.3.schema.json`: original authored design-episode schema, copied unchanged.
- `rfq-case.schema.json`: evaluator-side case contract for the portable 40-scenario export.
- `candidate-bundle.schema.json`: first-turn request exported by `draftbench prepare`.
- `candidate-bundle-v2.schema.json`: complete public design task contract from `prepare --complete`; preserves condition filtering.
- `adapter-response.schema.json`: candidate JSON stdout for the portable runner; file containment is additionally checked in Python.
- `evaluation-result.schema.json`: new portable result with nullable metrics; automated labels remain provisional.
- `acceptance-record.schema.json`: **proposed** requirement-to-delivery audit record for future evaluations; not a claim of an implemented acceptance grader.

Schemas use JSON Schema draft 2020-12. The CLI additionally checks semantic rules that JSON Schema alone cannot express, including case/asset identity, allowed context inputs, first-disclosure provenance, exact evidence quotes and metric denominators. JSON Schema libraries are optional consumer tools and are not runtime dependencies of the CLI.
