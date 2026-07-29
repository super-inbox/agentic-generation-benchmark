# Agent Generation Benchmark

A public benchmark for **agentic design-generation** — given a natural-language request, does the
agent route to the right tool/template, fill the right slots, and produce a successful result
(including across multi-turn). Built and maintained by [Curify](https://curify-ai.com).

> **Status:** scaffold — data drop pending. Methodology below is final; the 100-query scored
> set lands in [`data/`](data/).

## What this measures

A 4-layer evaluation, scored per query. Each layer isolates a different failure mode, so a
single "task failed" turns into an actionable diagnosis (wrong route? wrong slots? bad output?).

| Layer | Question | Metric |
|---|---|---|
| **1. Routing** | Did the agent pick the correct template / tool for the intent? | accuracy |
| **2. Slot filling** | Did it extract/fill the right parameters (subject, style, format…)? | slot F1 |
| **3. Task success** | Is the generated artifact actually what was asked for? | success rate (human 0/1 or 0–5) |
| **4. Multi-turn** | Does it hold context and recover across follow-up turns? | multi-turn score |

**Set:** 100 queries, balanced across intents (edu / merch / ecom / brand …).

## Data format (`data/`)

`queries.jsonl` — one request per line:
```json
{"query_id": "a001", "query": "make a sticker sheet of my dog", "intent": "merch",
 "expected_route": "template-original-character-sticker-pack",
 "expected_slots": {"concept": "dog"}}
```

`results.jsonl` — one scored run per line:
```json
{"query_id": "a001", "routed_to": "template-original-character-sticker-pack",
 "routing_correct": true, "slot_f1": 1.0, "task_success": 1, "multi_turn_score": null,
 "reviewer": "rong", "notes": ""}
```

> Field names are a proposal — align to Rong's actual agentic-eval export; keep JSONL + fixed schema.

## Use

```python
import json
res = [json.loads(l) for l in open("data/results.jsonl")]
routing_acc = sum(r["routing_correct"] for r in res) / len(res)
task_success = sum(r["task_success"] for r in res) / len(res)
```

## Links

- Research page & findings: https://curify-ai.com/resources/agent-evaluation
- Hugging Face dataset (mirror): `curify/agent-generation-benchmark`
- Catalog: `curify-datasets`

## License

Data: **CC BY 4.0** (see [`LICENSE`](LICENSE)).

## Citation

See [`CITATION.cff`](CITATION.cff), or:

> Curify (2026). *Agent Generation Benchmark: routing / slot / task-success / multi-turn
> evaluation of agentic design generation.* https://curify-ai.com/resources/agent-evaluation
