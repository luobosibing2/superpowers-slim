#!/usr/bin/env python3
"""Persist Superpowers Slim planning questions and plan revisions."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLAN_RE = re.compile(r"<proposed_plan>\s*(.*?)\s*</proposed_plan>", re.DOTALL)
ENTRY_RE = re.compile(r"<!-- superpowers-entry (\{.*?\}) -->")
QUESTION_RE = re.compile(
    r"<!-- superpowers-plan-question -->\s*(.*?)\s*"
    r"<!-- /superpowers-plan-question -->",
    re.DOTALL,
)
META_PREFIX = "<!-- superpowers-slim-plan "
META_SUFFIX = " -->"
NATIVE_IMPLEMENT_PROMPT = "Implement the plan."
NATIVE_HANDOFF_RE = re.compile(r"^\s*PLEASE IMPLEMENT THIS PLAN:\s*(.*)\s*$", re.DOTALL)


class JournalError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def emit(value: dict[str, Any] | None) -> None:
    if value is not None:
        print(json.dumps(value, ensure_ascii=False))


def stop_output(reason: str) -> dict[str, Any]:
    return {"continue": False, "stopReason": reason}


def block_output(reason: str) -> dict[str, Any]:
    return {"decision": "block", "reason": reason}


def success_output(additional_context: str | None = None) -> dict[str, Any]:
    if additional_context is None:
        return {"continue": True, "suppressOutput": True}
    return {
        "continue": True,
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        },
    }


def session_start_output(additional_context: str | None = None) -> dict[str, Any]:
    if additional_context is None:
        return {"continue": True, "suppressOutput": True}
    return {
        "continue": True,
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        },
    }


def noop_output(event: str | None) -> dict[str, Any]:
    if event in {"PreToolUse", "PostToolUse"}:
        return {"continue": True}
    return {"continue": True, "suppressOutput": True}


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def write_exclusive(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary_path, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def plan_root(cwd: str) -> Path:
    return Path(cwd).resolve() / ".plan"


def read_alignment(path: Path) -> tuple[dict[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise JournalError(f"cannot read {path}: {exc}") from exc
    first, separator, body = text.partition("\n")
    if not separator or not first.startswith(META_PREFIX) or not first.endswith(META_SUFFIX):
        raise JournalError(f"invalid alignment metadata in {path}")
    try:
        metadata = json.loads(first[len(META_PREFIX) : -len(META_SUFFIX)])
    except json.JSONDecodeError as exc:
        raise JournalError(f"invalid alignment metadata in {path}: {exc}") from exc
    return metadata, body


def write_alignment(path: Path, metadata: dict[str, Any], body: str) -> None:
    marker = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    atomic_write(path, f"{META_PREFIX}{marker}{META_SUFFIX}\n{body.rstrip()}\n")


def entry_metadata(body: str) -> list[tuple[re.Match[str], dict[str, Any]]]:
    entries: list[tuple[re.Match[str], dict[str, Any]]] = []
    for match in ENTRY_RE.finditer(body):
        try:
            entries.append((match, json.loads(match.group(1))))
        except json.JSONDecodeError as exc:
            raise JournalError(f"invalid alignment entry metadata: {exc}") from exc
    return entries


def next_entry_id(body: str, kind: str) -> str:
    numbers = [
        int(metadata["id"].split("-", 1)[1])
        for _, metadata in entry_metadata(body)
        if metadata.get("kind") == kind and re.fullmatch(rf"{kind}-\d+", metadata.get("id", ""))
    ]
    return f"{kind}-{max(numbers, default=0) + 1:04d}"


def short_session(session_id: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]", "", session_id)
    return (compact or "session")[:8].lower()


def slugify(value: str, limit: int = 64) -> str:
    chars: list[str] = []
    last_dash = False
    for char in value.strip().lower():
        category = unicodedata.category(char)
        if category.startswith(("L", "N")):
            chars.append(char)
            last_dash = False
        elif not last_dash:
            chars.append("-")
            last_dash = True
    slug = re.sub(r"-{2,}", "-", "".join(chars)).strip("-")
    return slug[:limit].rstrip("-")


def plan_directories(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.iterdir() if path.is_dir() and (path / "alignment.md").is_file()
    )


def find_plan_for_session(root: Path, session_id: str) -> Path | None:
    matches: list[Path] = []
    for directory in plan_directories(root):
        metadata, _ = read_alignment(directory / "alignment.md")
        if session_id in metadata.get("sessions", []):
            matches.append(directory)
    if len(matches) > 1:
        raise JournalError(
            f"session {session_id} is linked to multiple Plan directories: "
            + ", ".join(str(path) for path in matches)
        )
    return matches[0] if matches else None


def create_plan_for_session(root: Path, session_id: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    base = f"draft-{short_session(session_id)}"
    counter = 1
    while True:
        name = base if counter == 1 else f"{base}-{counter}"
        directory = root / name
        try:
            directory.mkdir()
            break
        except FileExistsError:
            counter += 1
    try:
        (directory / "revisions").mkdir()
        metadata = {
            "created_at": utc_now(),
            "format": 1,
            "sessions": [session_id],
            "title": None,
        }
        write_alignment(directory / "alignment.md", metadata, "# Plan Alignment\n")
    except Exception:
        try:
            (directory / "revisions").rmdir()
            directory.rmdir()
        except OSError:
            pass
        raise
    return directory


def get_or_create_plan(root: Path, session_id: str) -> Path:
    return find_plan_for_session(root, session_id) or create_plan_for_session(root, session_id)


def link_session(directory: Path, session_id: str) -> None:
    path = directory / "alignment.md"
    metadata, body = read_alignment(path)
    sessions = list(metadata.get("sessions", []))
    if session_id not in sessions:
        sessions.append(session_id)
        metadata["sessions"] = sessions
        write_alignment(path, metadata, body)


def native_handoff_plan(prompt: str) -> str | None:
    match = NATIVE_HANDOFF_RE.match(prompt)
    return match.group(1).strip() if match else None


def read_current_plan(directory: Path) -> str | None:
    current = directory / "current.md"
    if not current.is_file():
        return None
    try:
        return current.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise JournalError(f"cannot read {current}: {exc}") from exc


def find_plan_for_handoff(root: Path, handoff_plan: str) -> Path | None:
    matches: list[Path] = []
    for directory in plan_directories(root):
        plan = read_current_plan(directory)
        if plan and plan == handoff_plan:
            matches.append(directory)
    if len(matches) > 1:
        raise JournalError(
            "fresh-context Plan matches multiple artifact directories; specify the intended .plan path"
        )
    return matches[0] if matches else None


def latest_collaboration_mode(transcript_path: Any, turn_id: str | None = None) -> str | None:
    if not transcript_path:
        return None
    path = Path(str(transcript_path))
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise JournalError(f"cannot read hook transcript {path}: {exc}") from exc
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


def pointer_context(directory: Path) -> str:
    alignment = directory / "alignment.md"
    current = directory / "current.md"
    current_line = str(current) if current.is_file() else "not created yet"
    return (
        "Superpowers Plan artifacts are active for this task.\n"
        f"Alignment: {alignment}\n"
        f"Current plan: {current_line}\n"
        "Before revising or implementing, read these files only when their exact content is not "
        "already present in the current context. Keep Codex's native Plan handoff; do not inject "
        "the full Plan automatically."
    )


def append_directive(directory: Path, payload: dict[str, Any]) -> None:
    path = directory / "alignment.md"
    metadata, body = read_alignment(path)
    session_id = str(payload.get("session_id", ""))
    turn_id = str(payload.get("turn_id", ""))
    for _, entry in entry_metadata(body):
        if (
            entry.get("kind") == "D"
            and entry.get("session_id") == session_id
            and entry.get("turn_id") == turn_id
        ):
            return
    entry_id = next_entry_id(body, "D")
    entry = {
        "id": entry_id,
        "kind": "D",
        "recorded_at": utc_now(),
        "session_id": session_id,
        "source": "UserPromptSubmit",
        "turn_id": turn_id,
    }
    marker = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    section = (
        f"\n## {entry_id}\n\n<!-- superpowers-entry {marker} -->\n\n"
        f"### Directive\n\n{str(payload.get('prompt', '')).strip()}\n"
    )
    write_alignment(path, metadata, body.rstrip() + "\n" + section)


def render_question(question: Any) -> str:
    if not isinstance(question, dict):
        return str(question)
    header = str(question.get("header", "")).strip()
    prompt = str(question.get("question", "")).strip()
    lines = [line for line in (header, prompt) if line]
    options = question.get("options")
    if isinstance(options, list) and options:
        lines.append("Options:")
        for option in options:
            if isinstance(option, dict):
                label = str(option.get("label", "")).strip()
                description = str(option.get("description", "")).strip()
                lines.append(f"- {label}: {description}" if description else f"- {label}")
            else:
                lines.append(f"- {option}")
    return "\n\n".join(lines)


def append_question(
    directory: Path,
    payload: dict[str, Any],
    question: Any,
    source: str,
    question_id: str | None = None,
) -> str:
    path = directory / "alignment.md"
    metadata, body = read_alignment(path)
    session_id = str(payload.get("session_id", ""))
    turn_id = str(payload.get("turn_id", ""))
    tool_use_id = str(payload.get("tool_use_id", "")) or None
    for _, entry in entry_metadata(body):
        if (
            entry.get("kind") == "Q"
            and entry.get("source") == source
            and entry.get("session_id") == session_id
            and entry.get("turn_id") == turn_id
            and entry.get("tool_use_id") == tool_use_id
            and entry.get("question_id") == question_id
        ):
            return str(entry["id"])
    entry_id = next_entry_id(body, "Q")
    entry = {
        "asked_at": utc_now(),
        "id": entry_id,
        "kind": "Q",
        "question_id": question_id,
        "session_id": session_id,
        "source": source,
        "status": "pending",
        "tool_use_id": tool_use_id,
        "turn_id": turn_id,
    }
    marker = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    section = (
        f"\n## {entry_id}\n\n<!-- superpowers-entry {marker} -->\n\n"
        f"### Question\n\n{render_question(question).strip()}\n\n"
        f"### Answer\n\n<!-- superpowers-answer {entry_id} -->\n"
        "_Pending_\n"
        f"<!-- /superpowers-answer {entry_id} -->\n"
    )
    write_alignment(path, metadata, body.rstrip() + "\n" + section)
    return entry_id


def render_answer(answer: Any) -> str:
    if isinstance(answer, str):
        return answer.strip()
    if isinstance(answer, list):
        if not answer:
            return "_No answer returned (empty or auto-resolved)._"
        if len(answer) == 1:
            return str(answer[0]).strip()
        return "\n".join(f"- {item}" for item in answer)
    return f"```json\n{json.dumps(answer, ensure_ascii=False, indent=2, sort_keys=True)}\n```"


def decode_tool_response(response: Any) -> Any:
    if not isinstance(response, str):
        return response
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return response


def answer_for_question(response: Any, question_id: str | None) -> Any:
    response = decode_tool_response(response)
    if not isinstance(response, dict):
        return response
    answers = response.get("answers")
    if isinstance(answers, dict):
        answer = answers.get(question_id, [])
        if isinstance(answer, dict) and isinstance(answer.get("answers"), list):
            return answer["answers"]
        return answer
    if question_id in response:
        return response[question_id]
    return response


def answer_pending(
    directory: Path,
    payload: dict[str, Any],
    source: str,
    response: Any,
    tool_use_id: str | None = None,
    latest_only: bool = False,
) -> int:
    path = directory / "alignment.md"
    metadata, body = read_alignment(path)
    session_id = str(payload.get("session_id", ""))
    pending = [
        (match, entry)
        for match, entry in entry_metadata(body)
        if entry.get("kind") == "Q"
        and entry.get("status") == "pending"
        and entry.get("source") == source
        and entry.get("session_id") == session_id
        and (tool_use_id is None or entry.get("tool_use_id") == tool_use_id)
    ]
    if latest_only and pending:
        pending = [pending[-1]]
    if not pending:
        return 0
    for match, entry in reversed(pending):
        entry_id = str(entry["id"])
        entry["answered_at"] = utc_now()
        entry["status"] = "answered"
        new_marker = "<!-- superpowers-entry " + json.dumps(
            entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + " -->"
        body = body[: match.start()] + new_marker + body[match.end() :]
        answer = answer_for_question(response, entry.get("question_id"))
        answer_re = re.compile(
            rf"<!-- superpowers-answer {re.escape(entry_id)} -->.*?"
            rf"<!-- /superpowers-answer {re.escape(entry_id)} -->",
            re.DOTALL,
        )
        replacement = (
            f"<!-- superpowers-answer {entry_id} -->\n"
            f"{render_answer(answer)}\n"
            f"<!-- /superpowers-answer {entry_id} -->"
        )
        body, count = answer_re.subn(lambda _: replacement, body, count=1)
        if count != 1:
            raise JournalError(f"missing answer slot for {entry_id}")
    write_alignment(path, metadata, body)
    return len(pending)


def cancel_pending_structured(directory: Path, session_id: str) -> int:
    path = directory / "alignment.md"
    metadata, body = read_alignment(path)
    pending = [
        (match, entry)
        for match, entry in entry_metadata(body)
        if entry.get("kind") == "Q"
        and entry.get("status") == "pending"
        and entry.get("source") == "request_user_input"
        and entry.get("session_id") == session_id
    ]
    if not pending:
        return 0
    for match, entry in reversed(pending):
        entry_id = str(entry["id"])
        entry["resolved_at"] = utc_now()
        entry["status"] = "cancelled_or_failed"
        new_marker = "<!-- superpowers-entry " + json.dumps(
            entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + " -->"
        body = body[: match.start()] + new_marker + body[match.end() :]
        answer_re = re.compile(
            rf"<!-- superpowers-answer {re.escape(entry_id)} -->.*?"
            rf"<!-- /superpowers-answer {re.escape(entry_id)} -->",
            re.DOTALL,
        )
        replacement = (
            f"<!-- superpowers-answer {entry_id} -->\n"
            "_Cancelled or tool failed before PostToolUse._\n"
            f"<!-- /superpowers-answer {entry_id} -->"
        )
        body, count = answer_re.subn(lambda _: replacement, body, count=1)
        if count != 1:
            raise JournalError(f"missing answer slot for {entry_id}")
    write_alignment(path, metadata, body)
    return len(pending)


def extract_title(plan: str) -> str | None:
    for line in plan.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped[2:].strip() if stripped.startswith("# ") else None
    return None


def rename_draft(directory: Path, title: str | None) -> Path:
    if not directory.name.startswith("draft-") or not title:
        return directory
    slug = slugify(title)
    if not slug:
        return directory
    metadata, body = read_alignment(directory / "alignment.md")
    session_id = str(metadata.get("sessions", ["session"])[0])
    base = f"{local_stamp()}-{slug}-{short_session(session_id)}"
    target = directory.parent / base
    counter = 2
    while target.exists():
        target = directory.parent / f"{base}-{counter}"
        counter += 1
    metadata["title"] = title
    write_alignment(directory / "alignment.md", metadata, body)
    try:
        directory.rename(target)
    except OSError:
        return directory
    return target


def save_plan(directory: Path, plan: str) -> Path:
    normalized = plan.rstrip() + "\n"
    directory = rename_draft(directory, extract_title(plan))
    current = directory / "current.md"
    if current.is_file():
        try:
            if current.read_text(encoding="utf-8") == normalized:
                return directory
        except OSError as exc:
            raise JournalError(f"cannot read {current}: {exc}") from exc
    revisions = directory / "revisions"
    existing = sorted(revisions.glob("[0-9][0-9][0-9][0-9].md"))
    if existing:
        try:
            if existing[-1].read_text(encoding="utf-8") == normalized:
                atomic_write(current, normalized)
                return directory
        except OSError as exc:
            raise JournalError(f"cannot recover Plan revision {existing[-1]}: {exc}") from exc
    number = 1
    while True:
        revision = revisions / f"{number:04d}.md"
        try:
            write_exclusive(revision, normalized)
            break
        except FileExistsError:
            number += 1
        except OSError as exc:
            raise JournalError(f"cannot write Plan revision {revision}: {exc}") from exc
    try:
        atomic_write(current, normalized)
    except OSError as exc:
        raise JournalError(f"cannot write current Plan {current}: {exc}") from exc
    return directory


def request_questions(payload: dict[str, Any]) -> list[tuple[str | None, Any]]:
    tool_input = payload.get("tool_input", {})
    questions = tool_input.get("questions", []) if isinstance(tool_input, dict) else []
    if not isinstance(questions, list):
        return []
    result: list[tuple[str | None, Any]] = []
    for index, question in enumerate(questions):
        question_id = str(question.get("id", index)) if isinstance(question, dict) else str(index)
        result.append((question_id, question))
    return result


def handle_user_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    root = plan_root(str(payload["cwd"]))
    session_id = str(payload.get("session_id", ""))
    mode = latest_collaboration_mode(payload.get("transcript_path"), payload.get("turn_id"))
    directory = find_plan_for_session(root, session_id)
    prompt = str(payload.get("prompt", ""))
    handoff_plan = native_handoff_plan(prompt)
    if mode == "plan":
        directory = directory or create_plan_for_session(root, session_id)
        cancel_pending_structured(directory, session_id)
        answer_pending(
            directory,
            payload,
            source="conversation",
            response=str(payload.get("prompt", "")),
            latest_only=True,
        )
        if prompt.strip() != NATIVE_IMPLEMENT_PROMPT:
            append_directive(directory, payload)
    elif handoff_plan is not None:
        if directory is None:
            directory = find_plan_for_handoff(root, handoff_plan)
            if directory is None:
                raise JournalError(
                    "fresh-context Plan handoff does not match any .plan current.md; "
                    "specify the intended artifact path before execution"
                )
            link_session(directory, session_id)
        elif read_current_plan(directory) != handoff_plan:
            raise JournalError(
                f"native Plan handoff does not match {directory / 'current.md'}; "
                "confirm the intended Plan before execution"
            )
        cancel_pending_structured(directory, session_id)
    elif directory is not None:
        cancel_pending_structured(directory, session_id)
    return success_output(pointer_context(directory) if directory is not None else None)


def handle_pre_tool(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("tool_name") != "request_user_input":
        return noop_output("PreToolUse")
    mode = latest_collaboration_mode(payload.get("transcript_path"), payload.get("turn_id"))
    if mode != "plan":
        return noop_output("PreToolUse")
    directory = get_or_create_plan(plan_root(str(payload["cwd"])), str(payload["session_id"]))
    for question_id, question in request_questions(payload):
        append_question(directory, payload, question, "request_user_input", question_id)
    return noop_output("PreToolUse")


def handle_post_tool(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("tool_name") != "request_user_input":
        return noop_output("PostToolUse")
    directory = find_plan_for_session(
        plan_root(str(payload["cwd"])), str(payload.get("session_id", ""))
    )
    if directory is not None:
        answer_pending(
            directory,
            payload,
            source="request_user_input",
            response=payload.get("tool_response"),
            tool_use_id=str(payload.get("tool_use_id", "")),
        )
    return noop_output("PostToolUse")


def handle_stop(payload: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get("last_assistant_message") or "")
    plan_match = PLAN_RE.search(message)
    mode = latest_collaboration_mode(payload.get("transcript_path"), payload.get("turn_id"))
    if mode != "plan" and not plan_match:
        return {"continue": True, "suppressOutput": True}
    directory = get_or_create_plan(plan_root(str(payload["cwd"])), str(payload["session_id"]))
    cancel_pending_structured(directory, str(payload.get("session_id", "")))
    if plan_match:
        save_plan(directory, plan_match.group(1).strip())
        return {"continue": True, "suppressOutput": True}
    marked = QUESTION_RE.findall(message)
    question = "\n\n".join(part.strip() for part in marked if part.strip())
    if not question and ("?" in message or "？" in message):
        question = message.strip()
    if question:
        append_question(directory, payload, question, "conversation")
    return {"continue": True, "suppressOutput": True}


def handle_session_start(payload: dict[str, Any]) -> dict[str, Any]:
    directory = find_plan_for_session(
        plan_root(str(payload["cwd"])), str(payload.get("session_id", ""))
    )
    if directory is not None:
        cancel_pending_structured(directory, str(payload.get("session_id", "")))
    return session_start_output(pointer_context(directory) if directory is not None else None)


def handle_payload(payload: dict[str, Any]) -> dict[str, Any]:
    event = payload.get("hook_event_name")
    if payload.get("agent_id"):
        return noop_output(event)
    try:
        if event == "UserPromptSubmit":
            return handle_user_prompt(payload)
        if event == "PreToolUse":
            return handle_pre_tool(payload)
        if event == "PostToolUse":
            return handle_post_tool(payload)
        if event == "Stop":
            return handle_stop(payload)
        if event == "SessionStart":
            return handle_session_start(payload)
        return noop_output(event)
    except (JournalError, OSError, KeyError, ValueError) as exc:
        reason = f"Superpowers Plan artifact write failed; processing stopped: {exc}"
        if event == "PreToolUse":
            return block_output(reason)
        return stop_output(reason)


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        emit(stop_output(f"Superpowers Plan hook received invalid JSON: {exc}"))
        return 0
    emit(handle_payload(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
