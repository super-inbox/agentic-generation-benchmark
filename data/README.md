# data/

## Available data

### `draft-bench-v0.1/`

DRAFT-Bench v0.1.0 contains 35 authored design briefs / 43 conditions, 24
project-owned input fixtures, 40 RFQ scenarios, and 100 replayable RFQ run
records (99 scored, one infrastructure exclusion). Numeric archive metadata
and the separate R1 pilot are included with explicit scope and provenance.
See the [dataset card](../DATA_CARD.md) and [reproduction guide](../docs/REPRODUCIBILITY.md).

### `2026-08-03-production-gemini/`

Visual Intent Routing (VIR) v2 end-to-end production image checkpoint:

- 115 Query folders and 316 successful images;
- 166 GPT-direct images generated with `gpt-image-2`;
- 150 Curify images routed through Curify templates and rendered with
  `gemini-3-pro-image-preview`;
- 96 Queries have successful output from both systems;
- 144 matched Query/direction pairs are colocated under
  `<stage>/by-query/<normalized-query>/`;
- each Query folder contains an exact `query-manifest.json`.

See `2026-08-03-production-gemini/RUN_STATUS.md` and
`comparison-manifest.json` for the full checkpoint status, omissions, pending
jobs, provenance, and limitations.

This directory is a generated-image subset of VIR v2, not the complete
696-record VIR v2 query corpus and not the separate 100-query scored set
described in the original repository scaffold. It is published for reproducible
side-by-side inspection; image completion is not a visual-quality score and
does not replace routing Ground Truth.
