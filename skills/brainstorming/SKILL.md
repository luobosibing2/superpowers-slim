---
name: brainstorming
description: Use when an explicit Plan or Default-mode planning request needs product, architecture, or behavior clarification before a substantial implementation plan.
---

# Brainstorming

## Purpose

Resolve the few product, architecture, or behavior choices that materially change
a substantial Plan. Do not turn ordinary exploration into a planning ceremony.

Do not use for code research, repository exploration, call-chain tracing,
mechanism explanations, status checks, or a small change whose intent is clear.

## Method

1. Inspect discoverable project facts before asking the user.
2. Identify only unresolved choices that change the outcome or approach.
3. When a real tradeoff exists, recommend one option and explain the meaningful
   alternatives briefly.
4. Treat a direction as approved only through explicit user direction or an
   authoritative repository source. Silence is not approval.

When `request_user_input` is listed for the current turn, use it. When it is not
listed, ask one necessary question directly. Do not create question IDs, markers,
pending states, or a separate record merely to prove that the conversation happened.

## Alignment Reminder

When material alignment changes, keep the active `alignment.md` as a concise
summary of the decisions that are current now. Rewrite obsolete content instead
of appending an audit history. The conversation and explicit user direction remain
authoritative; a missing or stale reminder does not erase approval.

When the important choices are settled, pass the current direction to
`superpowers:writing-plans` if a substantial Plan is useful. Brainstorming never
authorizes implementation, delegation, or Git writes unless the same user
instruction grants that authority.
