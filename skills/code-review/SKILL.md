---
name: code-review
description: Use when the user explicitly requests implementation review or a completed change has high semantic risk.
---

# Code Review

## Scope

Run a bounded independent implementation review. This is not a per-task reviewer
pipeline. Ordinary low-risk work does not trigger it automatically.

## Trigger

- The user explicitly asks for implementation review.
- The completed change affects security, authentication, permissions, payments,
  data migration, persistent schema, public API, compatibility, or comparable
  cross-module semantics.

File count and line count alone are not high-risk signals. If neither trigger is
present, return to `superpowers:verification-before-completion`.

## Review Loops

1. The root agent identifies the exact task requirements and review scope from the
   conversation, plan, and current Git evidence.
2. Spawn exactly one fresh reviewer for round one. Give it the requirements,
   scope, diff or commit evidence, and review rubric. It must be read-only and
   must not delegate to another agent.
3. Round one is a full review of the requested implementation scope. Report
   findings first, ordered by severity and grounded in files and lines.
4. If fixes are required, the root agent owns the fixes, integration, and tests.
5. After blocking findings are fixed, spawn one fresh reviewer for a scoped
   re-review of those fixes and nearby regressions. Include the prior findings and
   the fix scope.
6. Never start a third round. Report unresolved critical or major findings as
   blockers without claiming completion.

Minor observations may accompany a pass. A critical or major finding always
forces `fix_required`, even if a reviewer emits an inconsistent verdict.

## Review Handoff

Record the round, scope, review range, verdict, and blocking findings. Then return
to `superpowers:verification-before-completion` for the final evidence audit.
