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
wait for approval before rebuilding the plan. Do not create persistent Plan Check
state, and do not require a plan file when conversation context is sufficient.

## Execution Boundary

The plan does not choose an execution engine. The root Codex agent and active
user/repository policy decide whether work is performed inline or delegated.
Planning does not itself authorize delegation or Git writes.

Keep plans in the conversation by default. Write a plan file only when the user or
repository requires a durable artifact. Only after Plan Self-Review is clean, end
with a concise Plan Handoff containing
the chosen approach, constraints, interfaces, tasks, verification, explicit
assumptions, and unresolved risks. Then stop and wait for the user to authorize
implementation unless the user already authorized Plan plus execution. A Plan
request by itself is not execution authorization.
