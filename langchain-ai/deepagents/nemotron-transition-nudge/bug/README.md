# Agent Cost Comparison

Original code from : https://github.com/nebius/token-factory-cookbook/tree/main/agents/agent-cost-comparison-1

## Bug Reproduction

There is a bug in `deepagents == 0.7.10`

`NemotronPolicyNudgeMiddleware` can classify an in-progress, single-turn
filesystem task as a transition to new work. It then injects guidance to call
`compact_conversation` even though the user has not supplied a second request.

Issue created : [langchain-ai/deepagents/issues/5982](https://github.com/langchain-ai/deepagents/issues/5982)   

Verified fix in v0.7.23 ✅   

See [fixed example](../fix/)

### How to reproduce

```bash
uv run python agent_cost_comparison_1_buggy.py --data-dir data-1
```

You will see `nvidia/Nemotron-3-Ultra-550b-a55b` will fail to produce the correct answer.

```
========================================================================
Running model: nvidia/Nemotron-3-Ultra-550b-a55b
========================================================================

Validation
  result_created       FAIL
  valid_json           FAIL
  keys_match_expected  FAIL
  result_parse_error   PASS
  region               FAIL
  change               FAIL
  primary_product      FAIL
  summary_created      FAIL
  summary_nonempty     FAIL
```

### Workaround

Deep Agents' built-in Ultra profile can mistake this single-turn filesystem
task for a task transition. The benchmark keeps the rest of that profile but
disables `NemotronPolicyNudgeMiddleware`:

```python
register_harness_profile(
    "nebius:nvidia/Nemotron-3-Ultra-550b-a55b",
    HarnessProfile(excluded_middleware={"NemotronPolicyNudgeMiddleware"}),
)
```

file: [agent_cost_comparison_2_workaround.py](agent_cost_comparison_2_workaround.py)

```bash
uv run python agent_cost_comparison_2_workaround.py --data-dir data-1
```

This run will succeed every time.

## About Benchmark

Benchmark Nebius-hosted LLMs on a small data-analysis task and compare their
**cost**, **latency**, **token usage**, and **correctness**.

Each model is run as a [deepagents](https://github.com/langchain-ai/deepagents)
filesystem agent with no shell or code-execution tool. The agent must inspect
the input files, reason over their contents, and write `result.json` and
`summary.md` to the workspace output directory.

## Task

The benchmark task is the same for every model:

1. Compare Q1 vs Q2 revenue by region.
2. Find the region with the largest absolute revenue change.
3. Calculate its signed change as Q2 minus Q1.
4. Within that region, find the product with the largest change in the same
   direction as the region's change.
5. Write `/output/result.json` and `/output/summary.md`.

The agent has to do all reasoning and arithmetic itself over the file contents —
there is no code-execution tool available.

## Output format

`result.json` must contain exactly these keys:

```json
{
  "region": "west",
  "change": -60000,
  "primary_product": "widget-b"
}
```

The values above illustrate the required types; each run must use values
calculated from its workspace files.

`summary.md` must contain the `# Sales Analysis` heading and exactly three
bullets with the actual computed values:

```markdown
# Sales Analysis

- Region with the largest revenue change: <actual region>
- Dollar amount of that change (signed): <actual signed change>
- Product that contributed most to the change: <actual product>
```

The angle-bracketed text is instructional. The agent must replace every
placeholder rather than copy it or emit label-only bullets. No Executive
Summary section is required.

## Models compared

Configured in `MODELS` in `agent_cost_comparison_1_buggy.py`:

- `nvidia/Nemotron-3-Ultra-550b-a55b`
- `nvidia/nemotron-3-super-120b-a12b`
- `nvidia/Nemotron-3_5-Lightning`

## Setup

```bash
uv sync
```

Create a `.env` file in this directory with your Nebius API key:

```bash
NEBIUS_API_KEY=<your-key>
```

The script validates the key before making any LLM calls.

## Run

Run the benchmark against the default `data-1` suite:

```bash
uv run agent_cost_comparison_1_buggy.py
```

Use a different data suite:

```bash
uv run agent_cost_comparison_1_buggy.py --data-dir data-2
```

For each model, a workspace is created at
`benchmarks/<data-suite>/<model>/` (input is copied in, output is written to
`output/`). Each result is validated against `<data-dir>/expected.json`. Once
all models finish, a comparison table is printed sorted by estimated cost.

Different data suites retain separate artifacts. Rerunning the same suite and
model replaces only that model's existing workspace for that suite.

### Options

| Option | Default | Description |
|---|---|---|
| `--data-dir` | `data-1` | Data suite directory under this folder |
| `--dump-transcript` | off | Write messages to `<workspace>/output/_transcript.json` |

## Configuration

Key configuration values live in `agent_cost_comparison_1_buggy.py`:

| Constant | Default | Description |
|---|---|---|
| `AGENT_TIMEOUT` | `300` seconds (5 minutes) | Timeout threshold for each `agent.invoke()` call |
| `MODELS` | 3 Nebius models | Models to benchmark and their pricing |
| `OUTPUT_DATA_DIR` | `output` | Output subdirectory inside each workspace |

Adjust `AGENT_TIMEOUT` if slow runs regularly cross the threshold.


## Validation

The built-in score compares `result.json` with the selected suite's
`expected.json`. It also reports whether `summary.md` exists and is nonempty.
It does not currently validate the summary heading, bullet count, or values;
inspect the generated summary or transcript when verifying a run.

## Sample output

```text
MODEL COMPARISON

| Model                             | Success | Score | Turns | Calls | In Tok | Out Tok | Tot Tok | Time   | Cost ▲    |
|-----------------------------------|---------|-------|-------|-------|--------|---------|---------|--------|-----------|
| nvidia/Nemotron-3_5-Lightning     | YES     | 100%  | 8     | 11    | 30,873 | 1,214   | 32,087  | 6.67s  | $0.002144 |
| nvidia/nemotron-3-super-120b-a12b | YES     | 100%  | 9     | 8     | 32,332 | 3,850   | 36,182  | 16.86s | $0.013165 |
| nvidia/Nemotron-3-Ultra-550b-a55b | YES     | 100%  | 17    | 23    | 79,116 | 1,936   | 81,052  | 23.30s | $0.084924 |
```

## Files

- `agent_cost_comparison_1_buggy.py` — buggy run: configuration, orchestration,
  and per-model execution (parsing, validation, cost metrics, comparison
  table).
- `agent_cost_comparison_2_workaround.py` — same benchmark, but disables
  `NemotronPolicyNudgeMiddleware` for the Ultra profile.
- `utils.py` — workspace setup, usage/cost collection, validation, printing,
  transcript serialization, and invocation helpers.
- `data-1/input/` — source data copied into each model's workspace.
- `data-1/expected.json` — ground-truth answer used for scoring.
- `data-2/` — second input suite and its expected result.
- `benchmarks/<data-suite>/` — per-model run artifacts (gitignored).

## Debugging

Add `--dump-transcript` to preserve the complete message and tool-call history
for each model run:

```bash
uv run agent_cost_comparison_1_buggy.py --data-dir data-2 --dump-transcript
```

## Nemotron-3-Ultra compatibility

There was a bug in deepagents v0.7.10.

Deep Agents' built-in Ultra profile can mistake this single-turn filesystem
task for a task transition. `agent_cost_comparison_1_buggy.py` runs with the
unmodified profile and exhibits the bug; `agent_cost_comparison_2_workaround.py`
disables `NemotronPolicyNudgeMiddleware` as described in
[Workaround](#workaround).

Issue created : [langchain-ai/deepagents/issues/5982](https://github.com/langchain-ai/deepagents/issues/5982)   
Fixed in v0.7.23 ✅
