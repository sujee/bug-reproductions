# Nemotron transition nudge during a single-turn filesystem task

## Summary

**bug in `deepagents==0.7.10`**

`NemotronPolicyNudgeMiddleware` can classify an in-progress, single-turn
filesystem task as a transition to new work. It then injects guidance to call
`compact_conversation` even though the user has not supplied a second request.

**Tested version**

- Python 3.12 or later
- `deepagents==0.7.10`

https://github.com/langchain-ai/deepagents/issues/5982

Verified fix in v0.7.23 ✅

## Reproduction

- [repro](repro/) - **minimal reproduction code**.  The reproduction is deterministic. It exercises the transition heuristic
directly and does not make a model call or require an API key.
- [bug](bug/) - original code where the bug surfaced.  (Needs NEBIUS_API_KEY to run)
- [fix](fix/) - fix verification with updated version.  (Needs NEBIUS_API_KEY to run)
