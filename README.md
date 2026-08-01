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
