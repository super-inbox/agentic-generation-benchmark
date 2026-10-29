# Reproduction coverage

## New runnable evaluations (toolkit v0.2)

The [run guide](RUNNING.md) supplies all-task input listing, complete candidate export, a subprocess adapter,
multi-turn design/RFQ execution, Gemini API judgments and JSON/CSV summaries. All 43 public design conditions
and 40 RFQ scenarios have bundled inputs. Online design inspection needs `requirements-eval.txt`; calls need
an evaluator key, and candidate execution needs the team's agent and tools. This is a new protocol, not a
reconstruction of historical provider prompts or execution environments.

## Supported offline

Python 3.10+ and the repository checkout are sufficient. There are no Python package dependencies, credentials, private filesystem paths or model calls in the consumption commands.

| Operation | Command | What it establishes |
|---|---|---|
| Data integrity | `python3 -m draftbench validate` | Release hashes, IDs, fixture availability, role boundaries, counts and archived RFQ arithmetic match |
| Historical summaries | `python3 -m draftbench report` | Archive denominators, completion coverage, RFQ cohort metrics and R1 repetition counts |
| One design input | `python3 -m draftbench prepare design 'DAB-L4-BID-001@zero_shot' --out /tmp/draftbench-bid-input` | A request with one permitted source asset, without optional references, memory or future feedback |
| One RFQ input | `python3 -m draftbench prepare rfq RFQ-IC-001 --out /tmp/draftbench-rfq-input` | The candidate role prompt and one opening; no hidden field values |
| Worked scoring examples | `python3 -m draftbench rfq-example` | Two synthetic test examples illustrating the metric contract, not new model results |
| New annotated RFQ episode | `python3 -m draftbench rfq-score --case-id RFQ-IC-001 --episode /path/to/episode.json` | Deterministic arithmetic over independently supplied annotations |

Output folders must be new. Input projection checks asset hashes and rejects path traversal. Mount only the output folder for a candidate; this tool does not sandbox a model or prevent it from reading the rest of the machine. The repository, evaluator truth and future feedback must remain outside that mount.

The initial design bundle uses the original first-turn projection and condition filtering. It does not claim to reproduce every system instruction, output-location wrapper, runtime capability or judge payload used by the historical candidates.

## Inspect one archived RFQ episode

```python
import json
from pathlib import Path

root = Path('data/draft-bench-v0.1')
episodes = [json.loads(line) for line in (root / 'results/rfq_episodes.jsonl').read_text().splitlines()]
episode = next(e for e in episodes if e['case_id'] == 'RFQ-IC-001' and e['model'] == 'astra')
Path('/tmp/draftbench-episode.json').write_text(json.dumps(episode, ensure_ascii=False))
```

```sh
python3 -m draftbench rfq-score --case-id RFQ-IC-001 --episode /tmp/draftbench-episode.json
```

The export retains candidate/customer utterances and the original routing/disclosure annotations. Replay compares all freshly computed fields with the stored result, including checkpoint evidence, provisional bounds and infrastructure exclusions. It validates the calculation given annotations; it does not establish the semantic correctness of those annotations.

## What is not reproduced

- **Historical online behavior:** the new portable runner does not recreate historical provider environments, system wrappers or sampling. Its documented router/auditor and feedback schedule define a new experiment.
- **Original design judgments:** output artifacts and complete judge payloads are not in this new data release. Numeric archive summaries are inspectable, but a fresh semantic rejudge needs the missing evidence.
- **Broader archive tasks:** routing, preference, 21q and planning groups have numeric metadata only here. Their counts must not be advertised as fully executable public design briefs. The separately preserved VIR archive has its own content and protocol.
- **Expert acceptance:** there is no completed human study or validated automatic acceptance score. R1 is a model pilot, with pending expert adjudication.
- **Generalization or downstream benefit:** the released cases are development material, not a secret holdout; RFQ is not paired with design delivery.

## Frozen evidence and amendments

The 100 RFQ records include 60 original-cohort runs (20 each for recorded Astra, Claude and Sol configurations), plus 40 extension runs (20 each for Astra and Claude). One extension Claude record is infrastructure-excluded. The later unsuccessful Sol extension attempt is separately summarized, not inserted as 20 ability failures.

The original Claude comparison uses amendment AMENDMENT-01, including reattempts for 004, 009 and 019. Both amended and strict paired summaries are computed. The original RFQ cohort uses Sol router/auditor configurations; the extension uses Astra configurations. The extension Astra continuation retained 13 earlier candidate questions and one Sol-routed customer reply. Strict exclusion does not remove these confounds.

`results/experiment_settings.json` records these facts. `provenance.json` preserves upstream hashes and export transformations. `manifest.json` freezes the released bytes. Future corrections should use a new data version, retain original records, and explain affected denominators.

## Maintainer export

Consumers do not need the private upstream archive. To prepare a new release, maintainers may run:

```sh
python3 tools/export_from_archive.py \
  --eval-root /path/to/archived/eval \
  --dashboard-dist /path/to/pinned/dashboard/dist \
  --paper-snapshot /path/to/paper-dashboard-snapshot.json \
  --output /path/to/new-release
```

The exporter refuses to replace an existing directory and copies only allowlisted authored data, project-owned fixtures and selected evidence. The current bundled scorer differs from the frozen reference only in package/test import paths; a private experiment-directory pointer was removed from its rubric. Reference source hashes are recorded. CI runs data validation, metric/boundary tests and the release text audit.
