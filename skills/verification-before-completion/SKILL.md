---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, or immediately before creating a commit or pull request.
---

# Verification Before Completion

## Rule

Completion claims require fresh evidence from the environment where the result is
supposed to hold. Confidence, an earlier run, or a neighboring checkout is not
evidence.

## Verification Check

1. Translate the user's goal into concrete deliverables and acceptance criteria.
2. Choose the command or inspection that proves each deliverable.
3. Run every command in the correct repository, branch,
   worktree, service, or target. Read the complete result, including failures,
   warnings, and skipped cases.
4. Map each requirement to its evidence and identify anything not covered.
5. Decide whether independent review is required. Invoke `superpowers:code-review`
   only when the user explicitly asks or the change is high risk. Do not invoke it
   again when the conversation already contains a Review Handoff for the current
   scope.
6. State the result precisely. If verification is partial or failed, report that
   boundary instead of using completion language.

Before a commit or pull request, also inspect the final diff and repository status
so unrelated or generated changes are not silently included.

## Scope

Use this check for final claims and durable publication boundaries. Do not run it
before every ordinary reply, planning step, exploration result, or intermediate
task. Material regression risk may justify demonstrating that a regression test
fails without the fix and passes with it; this is not required for every change.

High-risk changes include security, authentication, permissions, payments, data
migrations, persistent schemas, and public API or compatibility contracts. A
cross-module change with comparable semantic impact may also qualify. File or line
count alone does not.

## Evidence Format

Include the command or inspected artifact, its context, the observed outcome, and
any unverified scope. Say "not verified" when evidence is unavailable.
