# Superpowers: Codex Slim Profile

This local fork keeps five scoped methods derived from upstream Superpowers
v6.1.1. It is not a complete development workflow and does not bootstrap itself
into every conversation.

## Included skills

- `brainstorming`: clarify design decisions during Plan work.
- `writing-plans`: produce decision-complete plans for substantial changes.
- `systematic-debugging`: investigate failures from evidence to root cause.
- `verification-before-completion`: require fresh evidence before completion claims.
- `code-review`: run a bounded independent review for manual or high-risk changes.

Codex, direct user instructions, and `AGENTS.md` own the overall workflow.
Multi-agent delegation, worktree preparation, implementation, ordinary review,
and branch completion remain native Codex or separate-plugin responsibilities.

## Lightweight handoffs

Requirement clarification is a conversational handoff between `brainstorming`
and `writing-plans`. An approved design moves to planning; a material unresolved
decision moves back to brainstorming. Code research and repository exploration
do not trigger this path, and a completed plan does not authorize execution.
Before the Plan Handoff, `writing-plans` runs an inline Plan Self-Review for
requirement coverage, decision completeness, cross-task consistency, constraints,
and verification. It fixes plan-only gaps inline and returns material design gaps
to `brainstorming`; it does not dispatch an independent plan reviewer.

## Durable Plan journal

During Plan work, one lightweight hook adapter records each Codex task in its own
`.plan/<timestamp>-<title>-<session>/` directory. `alignment.md` preserves user
directives plus paired AI questions and user answers, `current.md` holds the
complete current Plan, and `revisions/` preserves every distinct prior candidate.
Different tasks in the same cwd use different directories and never share a
`current.md`. Re-entering Plan mode in the same Codex session keeps using the same
directory, including after a Default or Execute turn, and appends each distinct
complete Plan as the next revision. A separate independent Plan requires a new
Codex task.

The planning order is requirement alignment, complete candidate, inline
Self-Review, durable write, Plan Handoff, and user approval. Required writes fail
closed. In native Plan mode, Codex's Plan-to-Execute handoff remains intact. When
an associated task produces or revises a Plan in Default mode, the visible Plan
body uses invisible HTML markers so the same Stop hook can append the revision
without exposing `<proposed_plan>` or pretending a file-diff review is Plan
approval. The adapter injects only the active artifact paths. It adds no reviewer
loop, Plan hash, MCP server, Git snapshot, completion gate, or top-level workflow
controller, and it does not change `.gitignore` or decide whether `.plan/` is
committed.

Codex discovers the adapter through the standard `hooks/hooks.json` plugin path;
the manifest advertises its `Write` capability and Plan-journal keywords. A
cancelled structured question is finalized as cancelled or failed at the next
Stop, prompt submission, or session start if no successful PostToolUse arrived.

Manual or high-risk implementation review uses one fresh, read-only reviewer.
Round one reviews the complete task scope. If blocking findings are fixed, one
fresh scoped re-review may inspect those fixes and nearby regressions. There is no
third round. The root agent owns fixes, integration, verification, and the final
completion decision.

## Local installation

Register this checkout as the `superpowers-local` marketplace and install
`superpowers@superpowers-local`. Use a new Codex task after installation so the
skill inventory is loaded from the new plugin version.

## Provenance

The baseline is upstream commit
`d884ae04edebef577e82ff7c4e143debd0bbec99` (v6.1.1). `RELEASE-NOTES.md` is
retained as historical upstream material; it does not describe this slim
profile's active contract.

## License

MIT License. See `LICENSE`.
