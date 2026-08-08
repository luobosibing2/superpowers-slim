---
name: writing-plans
description: Use when stable requirements must be converted into a decision-complete plan for a substantial multi-step change.
---

# Writing Plans

## Purpose

Produce a Plan that states the intended outcome and chosen implementation approach
clearly enough for another engineer or agent to continue. Trust the implementer
with local choices that do not change observable behavior or real interfaces.

Use the conversation's Design Handoff when present. Return to
`superpowers:brainstorming` only when an unresolved product, architecture, or
behavior choice would materially change the Plan. Do not use this Skill for simple
answers, research-only work, or changes whose path is already obvious.

An explicit Plan request can activate this Skill in Plan or Default mode. It does
not switch collaboration mode or authorize implementation.

## Plan Reminders

The plugin may provide two paths for the current Codex task without injecting
their contents:

- `alignment.md` is a model-maintained summary of decisions that are current now.
- `current.md` is the latest complete Plan.

Read them when useful. Rewrite obsolete alignment instead of accumulating history,
and replace the current Plan directly when it changes. These files help memory;
they are not approval records, compatibility protocols, or a substitute for the
conversation. Missing, stale, or unwritable reminders should be reported briefly
and reconstructed from context when possible.

## Plan Content

Choose the structure that makes the work easiest to understand. Normally cover:

- the outcome and chosen approach;
- the implementation work at a useful level of grouping;
- constraints or interfaces only when a real consumer or user-visible boundary
  depends on them;
- the minimum observable verification and any material unresolved risk.

Do not freeze internal functions, files, prompts, call order, types, signatures,
representation, or test mechanics when producer and consumer can change together.
Do not invent edge cases, compatibility layers, versions, or independent proof
steps for hypothetical consumers.

Before handoff, read the Plan once as its implementer. Fix missing requirements or
decisions that would change the result, remove accidental internal contracts, and
ask the user only if a material choice remains unresolved. This is ordinary model
judgment, not a field checklist, reviewer dispatch, or proof state.

## Handoff and Execution

In native Plan mode, use Codex's `<proposed_plan>` handoff. In Default mode with
Plan reminders active, present the complete visible Plan once between
`<!-- superpowers-artifact-plan -->` and
`<!-- /superpowers-artifact-plan -->`; do not expose `<proposed_plan>` there.
The hook best-effort replaces `current.md`. It does not keep revisions, compare the
Plan with prior text, or decide whether the Plan is correct or approved.

Stop for explicit implementation authorization unless the user already requested
Plan plus execution. Planning does not authorize delegation or Git writes, and a
file-diff review action is not Plan approval.
