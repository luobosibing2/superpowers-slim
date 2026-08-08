# Local Development Rules

This repository is a Codex-only slim profile, not the upstream complete workflow.

- Keep exactly four skill directories: `brainstorming`, `writing-plans`,
  `systematic-debugging`, and `code-review`.
- Trust the model with semantic work. Do not add a parser, state machine, version,
  exact-content check, or fail-closed path merely to prevent a hypothetical model
  misunderstanding. Enforce only authorization, security, privacy, funds,
  irreversible data integrity, and task isolation in code. If the model can recover
  from the conversation or rewrite an internal reminder, warn and continue.
- Keep contracts narrow: fix only the minimum observable behavior a named current
  consumer needs. When producer and consumer can change together, update both
  directly instead of preserving or versioning the old internal protocol.
- Orchestrate methodology only through explicit handoffs between matching skills.
  The sole runtime exception is `hooks/hooks.json` plus
  `scripts/plan_artifacts.py`, which inject two reminder paths and replace the
  current Plan under the task cwd. Do not add MCP servers, Git snapshots, diff hashes,
  completion gates, or a top-level workflow controller.
- Do not make planning authorize implementation or delegation. An explicit Plan
  request is planning-only unless the same instruction also authorizes execution
  or the user authorizes it later; do not add an Edit/Write runtime gate.
- Before Plan Handoff, read the Plan once for missing outcome-changing decisions
  or accidental internal contracts. Fix plan prose inline and return material
  design gaps to brainstorming; do not create a reviewer, proof state, or field-by-
  field completion ritual.
- Use `request_user_input` whenever it is listed for the current turn. When it is
  absent, ask a necessary question directly; question delivery does not require a
  persistence protocol.
- Each Codex task has one stable `.plan/<session>/` directory. `alignment.md` is a
  model-maintained summary of current decisions and `current.md` is the latest
  complete Plan. Rewrite either in place. Do not add entry metadata, question
  states, revisions, exact Plan matching, recovery bridges, or format versions.
  Different sessions in one cwd must resolve to different directories.
- Native Plan mode uses `<proposed_plan>` for the Codex handoff. When an associated
  task produces a complete Plan in Default mode, make it recognizable with the
  invisible `superpowers-artifact-plan` markers and never expose `<proposed_plan>` or call a
  file-diff review action Plan approval. The hook best-effort replaces `current.md`;
  reminder failure does not erase user direction, authorize work, or freeze the
  task. Unmarked Default replies must not alter `current.md`.
- Keep all `SKILL.md` files at or below 500 lines in total.
- Invoke `code-review` only when the user explicitly requests implementation
  review. Risk, difficulty, complexity, or change size must not trigger it.
- Keep Review Loops to one full review plus one scoped re-review.
- Keep reviewers read-only and prohibit nested delegation from the reviewer.
- Keep code research and repository exploration outside `brainstorming`.
- Update `tests/test_slim_contract.py` when the public skill contract changes.
