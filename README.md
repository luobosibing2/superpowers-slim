# Superpowers: Codex Slim Profile

This local fork keeps four scoped methods derived from upstream Superpowers
v6.1.1. It is not a complete development workflow and does not bootstrap itself
into every conversation.

## Included skills

- `brainstorming`: clarify material design decisions during explicit planning.
- `writing-plans`: produce decision-complete plans for substantial changes.
- `systematic-debugging`: investigate failures from evidence to root cause.
- `code-review`: run a bounded independent review only when manually requested.

Codex, direct user instructions, and `AGENTS.md` own the overall workflow.
Multi-agent delegation, worktree preparation, implementation, ordinary review,
and branch completion remain native Codex or separate-plugin responsibilities.

## Lightweight handoffs

Requirement clarification is a conversational handoff between `brainstorming`
and `writing-plans`. An approved direction moves to planning; a material unresolved
decision moves back to brainstorming. Code research and repository exploration do
not trigger this path, and a Plan does not authorize execution unless the user also
requests implementation.

Before Plan Handoff, `writing-plans` reads the Plan once for missing outcome-changing
decisions and accidental internal contracts. It fixes plan prose inline and returns
material design gaps to `brainstorming`; it does not dispatch a plan reviewer or
create a proof state.

## Plan reminders

One small hook adapter gives each Codex task a stable `.plan/<session>/` directory
with two mutable Markdown reminders:

- `alignment.md` is a model-maintained summary of decisions that are current now.
- `current.md` is the latest complete Plan.

The adapter injects only these paths, never their contents. New alignment replaces
obsolete alignment, and a new complete Plan replaces `current.md`; there is no Q/A
journal, entry metadata, revision directory, exact-content identity check, or
versioned reader. The conversation and explicit user direction remain authoritative.
A missing, stale, or unwritable reminder produces at most a warning and never
freezes the task or changes implementation authorization.

Different sessions in one cwd resolve to different directories. This is the only
artifact isolation the adapter enforces. In native Plan mode, Codex's Plan handoff
remains intact. In Default mode, a complete visible Plan uses invisible HTML
markers so the Stop hook can best-effort replace `current.md` without exposing
`<proposed_plan>` or pretending a file-diff review is Plan approval. Unmarked
Default replies do not alter the Plan reminder.

Structured questions still use `request_user_input` whenever Codex lists it for
the current turn. Question delivery is independent of Plan persistence; the hook
does not intercept, pair, or validate questions and answers. It adds no reviewer
loop, Plan hash, MCP server, Git snapshot, completion gate, or top-level workflow
controller, and it does not change `.gitignore` or decide whether `.plan/` is
committed.

Manually requested implementation review uses one fresh, read-only reviewer.
Round one reviews the complete task scope. If blocking findings are fixed, one
fresh scoped re-review may inspect those fixes and nearby regressions. There is no
third round. The root agent owns fixes, integration, and the final completion
decision.

## Local installation

Register this checkout as the `superpowers-local` marketplace and install
`superpowers@superpowers-local`. Use a new Codex task after installation so the
skill inventory is loaded from the new plugin version.

## Provenance

The baseline is upstream commit
`d884ae04edebef577e82ff7c4e143debd0bbec99` (v6.1.1). `RELEASE-NOTES.md` is
retained as historical upstream material; it does not describe this slim
profile's active behavior.

## Research notes

- [Superpowers 压缩方法与行为评估实验研究](docs/research/2026-07-26-superpowers-compression-and-behavior-evals.md)

## License

MIT License. See `LICENSE`.
