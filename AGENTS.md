# Local Development Rules

This repository is a Codex-only slim profile, not the upstream complete workflow.

- Keep exactly five skill directories: `brainstorming`, `writing-plans`,
  `systematic-debugging`, `verification-before-completion`, and `code-review`.
- Orchestrate only through explicit text handoffs between matching skills. Do not
  add hooks, MCP servers, persistent state, or a top-level workflow bootstrap.
- Do not make planning authorize implementation or delegation.
- Require `writing-plans` to run an inline Plan Self-Review before Plan Handoff;
  plan-only gaps are fixed inline and material design gaps return to brainstorming.
  Do not turn this check into a reviewer dispatch or persistent state.
- Keep all `SKILL.md` files at or below 500 lines in total.
- Keep Review Loops to one full review plus one scoped re-review.
- Keep reviewers read-only and prohibit nested delegation from the reviewer.
- Keep code research and repository exploration outside `brainstorming`.
- Update `tests/test_slim_contract.py` when the public skill contract changes.
