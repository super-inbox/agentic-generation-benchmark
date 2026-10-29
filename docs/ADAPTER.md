# Candidate adapter contract

The runner invokes a trusted command with `shell=False`, `cwd=RUN/candidate`, and one JSON request on stdin.
Use absolute paths for the interpreter and adapter script; the cwd is not the repository.
No hidden field values, scoring rubric, future feedback or judge response is included in the request.

Design initial bundles use `draftbench-candidate-bundle/2`; RFQ retains `/1`. The runtime adds:

| Field | Meaning |
|---|---|
| `track`, `id` | Public task condition/scenario identity |
| `messages` | System instruction where present, initial user prompt, prior public replies, and currently revealed feedback |
| `input_context`, `assets`, `preference_memory` | Condition-filtered design inputs; assets have local relative paths and SHA-256 |
| `task_contract` | Design deliverables/counts/formats, constraints, reference roles, structured files, initial state and edit parameters |
| `turn_index`, `version`, `session_id` | Current turn/version and authored session label if applicable |
| `output_dir` | Directory for the current version's deliverables, e.g. `outputs/v1` |

The task contract's `inputs` distinguishes provided content from intentionally unavailable prerequisites.
The adapter must provide the entire request to the candidate, including context and contract; forwarding only the last
message would discard necessary information. Asset paths are relative to cwd. The candidate may retain local files and
tool state across invocations, but the bridge itself does not resume a provider-native chat session.

Return exactly one object on stdout:

```json
{
  "message": "Here are the requested variants; I am waiting for your selection.",
  "status": "ok",
  "artifacts": ["outputs/v0/variants.png", "outputs/v0/source.svg", "outputs/v0/verification.json"],
  "done": false
}
```

- `message` is required public-facing text, without private reasoning.
- `status` is `ok` (default) or `blocked`. A blocked response stops the episode and should explain the missing dependency.
- `artifacts` lists **all deliverables for that version**, including sources, previews and structured evidence. Paths must
  be unique, relative, existing files inside the candidate workspace; absolute paths, traversal and escaping symlinks fail.
  Maximum 100 files per turn, 50 MB each. Accepted paths are copied and hashed outside the workspace immediately.
- `done=true` ends RFQ without a new customer reply. It does not suppress authored design feedback. Final RFQ summaries
  cannot add requirements evidence. Custom adapters can express early stopping; the generic CLI bridge always sets false.
- Nonzero exit, invalid JSON, invalid artifacts, oversized stdout (>1 MB) or timeout is an agent failure, not a successful delivery.

The working [CLI bridge](../examples/command_adapter.py) feeds the full request as a prompt and collects files recursively
under `output_dir`. It supports stdin or an exact `{prompt}` argument. Configure the installed agent's noninteractive mode,
file access, tools and credentials yourself. The [mock adapter](../examples/mock_agent.py) is solely a synthetic test fixture.

For remote/container evaluation, implement the same interface, upload only candidate-visible files and current request,
and return actual output files to the candidate workspace before responding. Evaluator records must not be mounted there.
