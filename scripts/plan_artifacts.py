#!/usr/bin/env python3
"""Keep two lightweight Plan reminders for the current Codex task."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote


PLAN_RE = re.compile(
    r"<proposed_plan>[ \t]*\r?\n(.*?)\r?\n[ \t]*</proposed_plan>",
    re.DOTALL,
)
ARTIFACT_PLAN_RE = re.compile(
    r"<!-- superpowers-artifact-plan -->[ \t]*\r?\n(.*?)\r?\n"
    r"[ \t]*<!-- /superpowers-artifact-plan -->",
    re.DOTALL,
)


def emit(value: dict[str, Any] | None) -> None:
    if value is not None:
        print(json.dumps(value, ensure_ascii=False))


def success_output(additional_context: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"continue": True, "suppressOutput": True}
    if additional_context:
        result["hookSpecificOutput"] = {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        }
    return result


def session_start_output(additional_context: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"continue": True, "suppressOutput": True}
    if additional_context:
        result["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        }
    return result


def plan_directory(cwd: str, session_id: str) -> Path:
    safe_session = quote(session_id, safe="-_.") or "session"
    return Path(cwd).resolve() / ".plan" / f"session-{safe_session}"


def ensure_reminders(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    alignment = directory / "alignment.md"
    try:
        with alignment.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write("# Current alignment\n")
    except FileExistsError:
        pass


def replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def latest_collaboration_mode(transcript_path: Any, turn_id: str | None = None) -> str | None:
    if not transcript_path:
        return None
    try:
        lines = Path(str(transcript_path)).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    latest: str | None = None
    exact: str | None = None
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") != "turn_context":
            continue
        payload = item.get("payload", {})
        mode = payload.get("collaboration_mode", {}).get("mode")
        if isinstance(mode, str):
            latest = mode.lower()
            if turn_id and payload.get("turn_id") == turn_id:
                exact = latest
    return exact or latest


def marked_plan(message: str) -> str | None:
    stripped = message.strip()
    for pattern in (PLAN_RE, ARTIFACT_PLAN_RE):
        match = pattern.fullmatch(stripped)
        if match:
            plan = match.group(1).strip()
            return plan or None
    return None


def plan_from_transcript(transcript_path: Any, turn_id: str) -> str | None:
    if not transcript_path:
        return None
    try:
        lines = Path(str(transcript_path)).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    candidate: str | None = None
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = record.get("payload", {})
        if record.get("type") == "event_msg":
            item = payload.get("item", {})
            if (
                payload.get("type") == "item_completed"
                and payload.get("turn_id") == turn_id
                and isinstance(item, dict)
                and item.get("type") == "Plan"
                and isinstance(item.get("text"), str)
            ):
                candidate = item["text"].strip()
        elif record.get("type") == "response_item":
            metadata = payload.get("internal_chat_message_metadata_passthrough", {})
            if payload.get("role") != "assistant" or metadata.get("turn_id") != turn_id:
                continue
            content = payload.get("content", [])
            if not isinstance(content, list):
                continue
            message = "".join(
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict) and part.get("type") == "output_text"
            )
            candidate = marked_plan(message) or candidate
    return candidate or None


def pointer_context(directory: Path, mode: str | None = None) -> str:
    context = (
        "Superpowers Plan reminders for this task:\n"
        f"Alignment: {directory / 'alignment.md'}\n"
        f"Current plan: {directory / 'current.md'}\n"
        "They are mutable reminders, not authority. Read them when useful, keep the alignment "
        "note current when material decisions change, and do not inject either file automatically.\n"
    )
    if mode == "plan":
        return context + "Use Codex's native Plan handoff in Plan mode."
    if mode == "default":
        return context + (
            "In Default mode, wrap a complete visible Plan with the invisible "
            "superpowers-artifact-plan markers so the hook can replace current.md."
        )
    return context


def handle_user_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    directory = plan_directory(str(payload["cwd"]), str(payload.get("session_id", "")))
    mode = latest_collaboration_mode(payload.get("transcript_path"), payload.get("turn_id"))
    if mode == "plan":
        try:
            ensure_reminders(directory)
        except OSError as exc:
            print(f"Superpowers Plan reminder unavailable: {exc}", file=sys.stderr)
            return success_output()
    if not directory.is_dir():
        return success_output()
    return success_output(pointer_context(directory, mode))


def handle_stop(payload: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get("last_assistant_message") or "")
    plan = marked_plan(message) or plan_from_transcript(
        payload.get("transcript_path"), str(payload.get("turn_id", ""))
    )
    if not plan:
        return success_output()
    directory = plan_directory(str(payload["cwd"]), str(payload.get("session_id", "")))
    try:
        ensure_reminders(directory)
        replace_text(directory / "current.md", plan.rstrip() + "\n")
    except OSError as exc:
        print(f"Superpowers current Plan reminder was not saved: {exc}", file=sys.stderr)
    return success_output()


def handle_session_start(payload: dict[str, Any]) -> dict[str, Any]:
    directory = plan_directory(str(payload["cwd"]), str(payload.get("session_id", "")))
    if not directory.is_dir():
        return session_start_output()
    mode = latest_collaboration_mode(payload.get("transcript_path"), payload.get("turn_id"))
    return session_start_output(pointer_context(directory, mode))


def handle_payload(payload: dict[str, Any]) -> dict[str, Any]:
    event = payload.get("hook_event_name")
    if payload.get("agent_id"):
        return success_output()
    if event == "UserPromptSubmit":
        return handle_user_prompt(payload)
    if event == "Stop":
        return handle_stop(payload)
    if event == "SessionStart":
        return handle_session_start(payload)
    return success_output()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        emit(handle_payload(payload))
    except Exception as exc:  # The reminder hook must never freeze the task.
        print(f"Superpowers Plan reminder unavailable: {exc}", file=sys.stderr)
        emit({"continue": True, "suppressOutput": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
