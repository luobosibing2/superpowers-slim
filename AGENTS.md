# Local Development Rules

This repository is a Codex-only slim profile, not the upstream complete workflow.

- Keep exactly five skill directories: `brainstorming`, `writing-plans`,
  `systematic-debugging`, `verification-before-completion`, and `code-review`.
- Orchestrate methodology only through explicit handoffs between matching skills.
  The sole runtime exception is `hooks/hooks.json` plus
  `scripts/plan_artifacts.py`, which persist Plan alignment and complete revisions
  under the task cwd. Do not add MCP servers, Git snapshots, diff hashes,
  completion gates, or a top-level workflow controller.
- Do not make planning authorize implementation or delegation.
- Require `writing-plans` to run an inline Plan Self-Review before Plan Handoff;
  plan-only gaps are fixed inline and material design gaps return to brainstorming.
  After the check, require the complete candidate to be durably written before
  the Handoff is valid. Do not turn this check into a reviewer dispatch or Plan
  Check state.
- During Plan work, record user directives and all AI question/user answer pairs
  in the task's `alignment.md`. Each session has at most one associated Plan;
  leaving and re-entering Plan mode in that session must reuse its directory and
  append distinct complete Plans as revisions. Different sessions in one cwd may
  use independent Plan directories.
- Native Plan mode uses `<proposed_plan>` for the Codex handoff. When an associated
  task produces a complete Plan in Default mode, persist it with the invisible
  `superpowers-artifact-plan` markers and never expose `<proposed_plan>` or call a
  file-diff review action Plan approval. Unmarked Default replies must not alter
  `current.md`.
- Keep all `SKILL.md` files at or below 500 lines in total.
- Keep Review Loops to one full review plus one scoped re-review.
- Keep reviewers read-only and prohibit nested delegation from the reviewer.
- Keep code research and repository exploration outside `brainstorming`.
- Update `tests/test_slim_contract.py` when the public skill contract changes.
