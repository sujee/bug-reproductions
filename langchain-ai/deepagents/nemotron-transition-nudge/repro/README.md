# Nemotron transition nudge during a single-turn filesystem task

https://github.com/langchain-ai/deepagents/issues/5982

## Summary

`NemotronPolicyNudgeMiddleware` can classify an in-progress, single-turn
filesystem task as a transition to new work. It then injects guidance to call
`compact_conversation` even though the user has not supplied a second request.

The reproduction is deterministic. It exercises the transition heuristic
directly and does not make a model call or require an API key.

## Tested version

- Python 3.12 or later
- `deepagents==0.7.10`

## Expected behavior

The transition heuristic returns `False` because the message history contains
only one external user message.

## Actual behavior

The heuristic returns `True` after normal filesystem calls make the history
long enough to cross its transition threshold:

```text
External user messages: 1
Should compact on transition: True
```

The script then raises `AssertionError` because the observed value differs from
the expected value.

## Run

From this directory:

```shell
uv run repro.py
```

A failing assertion reproduces the bug.

## Why it happens

After several filesystem calls, the heuristic sees prior file work and tests
the original user request again. The request contains `Analyze` and the
filename `input.csv`, so it matches the large-file-work and file-reference
expressions even though it is still the first and only user turn.

## Upstream context

- Repository: <https://github.com/langchain-ai/deepagents>
- Nemotron harness profile: <https://github.com/langchain-ai/deepagents/pull/4192>
- Upstream issue: https://github.com/langchain-ai/deepagents/issues/5982
