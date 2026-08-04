---
name: writing-plans
description: Use when stable requirements must be converted into a decision-complete plan for a substantial multi-step change.
---

# Writing Plans

## Purpose

Produce a plan another engineer or agent can execute without inventing product or
architecture decisions. Match detail to risk; a plan is not a ritual.

## Preconditions

- The intended outcome and acceptance criteria are known.
- Discoverable repository facts have been inspected.
- Material design choices are settled or explicitly recorded as assumptions.

Use the conversation's Design Handoff when present. If an important product,
architecture, or behavior decision is unresolved, return to
`superpowers:brainstorming` instead of guessing. Stable requirements from explicit
user direction or authoritative repository sources do not require extra questions.

Do not use for simple answers, research-only exploration, one-line changes, or
tasks whose implementation path is already obvious.

An explicit request for a Plan can activate this method in Plan or Default mode.
It does not switch Codex collaboration mode or authorize implementation.

## Plan Artifacts

During Plan work, the plugin hook associates this Codex task with one directory
under `.plan/`. Its short injected context names two paths without injecting their
contents:

- `alignment.md` is the requirement source of truth. It contains user directives
  and paired AI questions and user answers.
- `current.md` is the last complete candidate Plan presented for approval.

Entering Plan mode again in the same Codex session reuses that directory. Leaving
Plan mode for Default or Execute does not close or unlink it; each later distinct
complete Plan is appended as the next revision in the same directory. Start a new
Codex task when the work is an independent Plan rather than a revision.

Before creating or revising a Plan, read the complete `alignment.md` and, when it
exists, `current.md`. Treat an artifact read or required write failure as blocking;
do not continue with a partial or unrecorded understanding.

## Plan Contract

Start with the goal and a short architecture summary. Include these sections when
they materially apply:

### Global Constraints

Record project-wide limits such as compatibility, dependencies, naming, security,
performance, migration, rollout, and repository conventions.

### Tasks

Each task must define:

- **Outcome:** the observable result.
- **Ownership:** the subsystem or files affected.
- **Interfaces:** APIs, schemas, commands, files, prompts, or user-visible behavior
  created or changed.
- **Implementation:** the chosen approach and important edge cases.
- **Verification:** commands or scenarios and their expected results.

Group work by independently verifiable outcomes. Do not force arbitrary
two-minute steps, full source listings, per-task commits, or reviewer gates.

## Plan Self-Review

Before producing the Plan Handoff, review the complete plan with fresh eyes.
This is an inline root-agent check, not a sub-agent or reviewer dispatch.

1. **Requirement coverage:** Map every approved requirement and success criterion
   to a task. Add any missing work.
2. **Decision completeness:** Find choices the implementer would still need to
   make about product behavior, architecture, or interfaces.
3. **Placeholder and ambiguity scan:** Remove `TBD`, `TODO`, vague actions,
   undefined interfaces, and verification that cannot prove an outcome.
4. **Cross-task consistency:** Check names, types, signatures, produced and
   consumed interfaces, dependencies, and task ordering across the whole plan.
5. **Constraints and verification:** Confirm Global Constraints, boundary cases,
   and verification expectations are carried into the tasks they govern.

Fix plan-only issues inline, then rerun the affected checks. If the check exposes
a material requirement or design gap, return to `superpowers:brainstorming` and
wait for approval before rebuilding the plan. Do not overwrite the current Plan
with a candidate that still has a requirement or design gap. Do not create
`PLAN_CHECKED`, reviewer state, hashes, or a separate Plan Check workflow.

## Plan Revision Safety

For every revision:

1. Use the complete existing `current.md` as the baseline, not a summary or the
   latest requested change in isolation.
2. Apply only approved changes. Preserve unaffected experiment definitions,
   behavior, interfaces, constraints, edge cases, and verification.
3. Reconcile the full candidate against every entry in `alignment.md`.
4. Run Plan Self-Review again over the complete candidate. Fix plan-only defects
   inline; route requirement or design gaps back to `superpowers:brainstorming`.
5. Only after the full candidate is clean, use the handoff for the active mode:
   - In native Plan mode, emit it once inside
     `<proposed_plan>...</proposed_plan>`.
   - In Default mode with Plan artifacts active, do not emit `<proposed_plan>`.
     Present the complete visible Plan once between the invisible HTML markers
     `<!-- superpowers-artifact-plan -->` and
     `<!-- /superpowers-artifact-plan -->`. This is an artifact handoff, not a
     native Plan approval card.

The Stop hook writes a changed candidate to the next non-overwriting
`revisions/NNNN.md`, then atomically replaces `current.md`, before the Handoff can
be treated as valid. Identical content creates no duplicate revision. A first H1
may rename the task's draft directory, but a naming failure must never discard the
Plan. The files contain no Plan hash, and revision numbers are not prompt state.

## Execution Boundary

The plan does not choose an execution engine. The root Codex agent and active
user/repository policy decide whether work is performed inline or delegated.
Planning does not itself authorize delegation or Git writes.

The fixed order is: requirement alignment, complete candidate Plan, Plan
Self-Review, durable write, Plan Handoff, then user approval. The Handoff contains
the chosen approach, constraints, interfaces, tasks, verification, explicit
assumptions, and unresolved risks. Stop and wait for the user to authorize
implementation unless the user already authorized Plan plus execution. A Plan
request by itself is not execution authorization. In Plan mode, Codex's native
Plan-to-Execute handoff remains authoritative. In Default mode, the artifact
handoff only persists the candidate and still waits for explicit execution
authorization. A file-diff review action is not Plan approval.
The plugin injects only artifact paths and never a second copy of the Plan.
