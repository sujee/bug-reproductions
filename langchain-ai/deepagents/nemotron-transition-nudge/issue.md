# Nemotron NemotronPolicyNudgeMiddleware Issue


## Title 

NemotronPolicyNudgeMiddleware misclassifies an in-progress single-turn filesystem task as a task transition


## Description 

`NemotronPolicyNudgeMiddleware._should_compact_on_transition()` can classify an
in-progress single-turn filesystem task as a transition to new work.

I expect transition compaction to be considered only when a later external user
turn starts a new task or substantial follow-on work.

Instead, the heuristic can fire during the original user turn after the agent
has accumulated enough AI and tool messages.

The reproduction contains exactly one external `HumanMessage`. After normal
filesystem calls increase the history past `_TRANSITION_NUDGE_MIN_MESSAGES`,
the following conditions become true:

1. `has_prior_file_work` is true because filesystem tools have been called.
2. The original request matches `_COMPACT_LARGE_READ_RE` because it contains
   “Analyze” followed by “files.”
3. `_should_compact_on_transition()` consequently returns `True`, despite there
   being no later user request or task transition.

This causes `_transition_nudge()` to inject a message saying that the latest
request appears to start a new task. In a live agent run, that can prompt an
unnecessary `compact_conversation` call while the agent is still completing the
original task.

A local workaround is to disable the entire middleware for the Nemotron Ultra
profile:

```python
register_harness_profile(
    "nebius:nvidia/Nemotron-3-Ultra-550b-a55b",
    HarnessProfile(
        excluded_middleware={"NemotronPolicyNudgeMiddleware"},
    ),
)
```

## Repro

`https://github.com/sujee/bug-reproductions/tree/main/langchain-ai/deepagents/nemotron-transition-nudge`

## Env

```
OS : MacOS Tahoe
Python : 3.12
Deep agents : 0.7.11
```
