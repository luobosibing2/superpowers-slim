---
name: brainstorming
description: Use in Plan mode when product, architecture, or behavior requirements need clarification and approval before a substantial implementation plan.
---

# Brainstorming

## Purpose

Turn an uncertain design problem into an approved direction before planning.
This is a Plan-stage method, not a prerequisite for every task.

## Use When

- The user is in Plan mode and important product or technical choices remain open.
- A substantial behavior change has multiple plausible approaches.
- Success criteria, audience, constraints, or boundaries need clarification.

Do not use for ordinary conversation, code research, repository exploration,
call-chain tracing, mechanism explanations, status checks, or a small change
whose intent is already clear. Do not use it merely because implementation may
happen later.

## Method

1. Inspect the immediately discoverable project context before asking the user
   for facts. Code research by itself does not activate this method.
2. State the goal, audience, constraints, current state, and success criteria.
3. Identify only the decisions that materially change the design.
4. Offer two or three viable approaches when a real tradeoff exists. Lead with a
   recommendation and explain the cost of each alternative.
5. Resolve failure modes, compatibility, data flow, and testing expectations.
6. Treat a direction as approved only when the user explicitly accepts it or an
   authoritative repository source settles it. Silence is not approval.

## Alignment Recording

During Plan work, every question and answer must be recoverable in the active
Plan's `alignment.md`. Prefer `request_user_input` for structured questions; the
Plan artifact hook records the question before display and pairs the tool result
afterward. For a directly written question, wrap the complete question context in
the invisible markers below so the Stop hook can record it as one Q entry:

```html
<!-- superpowers-plan-question -->
Complete question context
<!-- /superpowers-plan-question -->
```

Ask only questions that can materially change the design. If a required write
fails, stop: an unrecorded question or answer is not an approved requirement.

## Design Handoff

Record the approved direction, approval evidence, constraints, success criteria,
and any unresolved items in the active alignment artifact. If material items
remain, ask one focused recorded question and stop. Otherwise invoke
`superpowers:writing-plans` when a substantial implementation plan is needed.

Brainstorming never authorizes code changes, sub-agent delegation, worktree
creation, or any other execution action.
