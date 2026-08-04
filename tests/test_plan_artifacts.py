import importlib.util
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "plan_artifacts", ROOT / "scripts" / "plan_artifacts.py"
)
assert SPEC and SPEC.loader
plan_artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plan_artifacts)


class PlanArtifactsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.cwd = Path(self.temporary.name)
        self.transcripts = self.cwd / "transcripts"
        self.transcripts.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def transcript(self, session_id: str, turn_id: str, mode: str) -> Path:
        path = self.transcripts / f"{session_id}.jsonl"
        item = {
            "type": "turn_context",
            "payload": {
                "turn_id": turn_id,
                "collaboration_mode": {"mode": mode},
            },
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item) + "\n")
        return path

    def append_plan_item(self, path: Path, turn_id: str, plan: str) -> None:
        item = {
            "type": "event_msg",
            "payload": {
                "type": "item_completed",
                "turn_id": turn_id,
                "item": {"type": "Plan", "id": f"{turn_id}-plan", "text": plan},
            },
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item) + "\n")

    def append_assistant_message(self, path: Path, turn_id: str, message: str) -> None:
        item = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": message}],
                "internal_chat_message_metadata_passthrough": {"turn_id": turn_id},
            },
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item) + "\n")

    def append_user_message(self, path: Path, turn_id: str, message: str) -> None:
        item = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": message}],
                "internal_chat_message_metadata_passthrough": {"turn_id": turn_id},
            },
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item) + "\n")

    def payload(
        self,
        event: str,
        session_id: str = "session-a1b2c3d4",
        turn_id: str = "turn-1",
        mode: str = "plan",
        **extra,
    ) -> dict:
        value = {
            "hook_event_name": event,
            "session_id": session_id,
            "turn_id": turn_id,
            "cwd": str(self.cwd),
            "transcript_path": str(self.transcript(session_id, turn_id, mode)),
        }
        value.update(extra)
        return value

    def plan_dirs(self) -> list[Path]:
        root = self.cwd / ".plan"
        return sorted(path for path in root.iterdir() if path.is_dir()) if root.exists() else []

    def alignment(self, directory: Path) -> str:
        return (directory / "alignment.md").read_text(encoding="utf-8")

    def start_plan(self, session_id: str = "session-a1b2c3d4") -> Path:
        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                session_id=session_id,
                prompt="Keep every approved experiment definition.",
            )
        )
        self.assertTrue(result["continue"])
        directory = plan_artifacts.find_plan_for_session(self.cwd / ".plan", session_id)
        assert directory is not None
        return directory

    def save(self, body: str, session_id: str = "session-a1b2c3d4", turn_id: str = "turn-2"):
        return plan_artifacts.handle_payload(
            self.payload(
                "Stop",
                session_id=session_id,
                turn_id=turn_id,
                last_assistant_message=f"<proposed_plan>\n{body}\n</proposed_plan>",
            )
        )

    def save_default_artifact(
        self,
        body: str,
        session_id: str = "session-a1b2c3d4",
        turn_id: str = "turn-default-plan",
    ):
        return plan_artifacts.handle_payload(
            self.payload(
                "Stop",
                session_id=session_id,
                turn_id=turn_id,
                mode="default",
                last_assistant_message=(
                    "<!-- superpowers-artifact-plan -->\n"
                    f"{body}\n"
                    "<!-- /superpowers-artifact-plan -->\n\n"
                    "The complete Plan was written to the active artifact."
                ),
            )
        )

    def test_plan_prompt_creates_draft_and_records_directive(self) -> None:
        directory = self.start_plan()
        self.assertTrue(directory.name.startswith("draft-sessiona"))
        alignment = self.alignment(directory)
        self.assertIn("## D-0001", alignment)
        self.assertIn("Keep every approved experiment definition.", alignment)

        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-2",
                prompt="Add a second constraint.",
            )
        )
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(directory / "alignment.md"), context)
        self.assertIn("This turn is in Plan mode", context)
        self.assertNotIn("Keep every approved experiment definition.", context)
        self.assertNotIn("SHA", context)
        self.assertNotIn("revision", context.lower())

        default_result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-3",
                mode="default",
                prompt="Revise the active Plan without switching modes.",
            )
        )
        default_context = default_result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("This turn is in Default mode", default_context)
        self.assertIn("Do not emit <proposed_plan> tags", default_context)
        self.assertIn("<!-- superpowers-artifact-plan -->", default_context)

    def test_structured_tool_questions_and_answers_are_recorded(self) -> None:
        self.start_plan()
        questions = [
            {
                "id": "storage",
                "header": "Storage",
                "question": "Where should the journal live?",
                "options": [
                    {"label": ".plan", "description": "Keep it next to the work."},
                    {"label": "Home", "description": "Keep it globally."},
                ],
            }
        ]
        pre = plan_artifacts.handle_payload(
            self.payload(
                "PreToolUse",
                turn_id="turn-2",
                tool_name="request_user_input",
                tool_use_id="tool-1",
                tool_input={"questions": questions},
            )
        )
        self.assertEqual({"continue": True}, pre)

        post = plan_artifacts.handle_payload(
            self.payload(
                "PostToolUse",
                turn_id="turn-2",
                tool_name="request_user_input",
                tool_use_id="tool-1",
                tool_response=json.dumps(
                    {"answers": {"storage": {"answers": [".plan"]}}}
                ),
            )
        )
        self.assertEqual({"continue": True}, post)
        alignment = self.alignment(self.plan_dirs()[0])
        self.assertIn("## Q-0001", alignment)
        self.assertIn("Where should the journal live?", alignment)
        self.assertIn(".plan", alignment)
        self.assertIn('"status":"answered"', alignment)
        self.assertNotIn("_Pending_", alignment)
        self.assertNotIn('"answers": {', alignment)

    def test_default_structured_questions_create_alignment_without_prefix(self) -> None:
        turn_id = "turn-default-question"
        pre_payload = self.payload(
            "PreToolUse",
            turn_id=turn_id,
            mode="default",
            tool_name="request_user_input",
            tool_use_id="tool-default",
            tool_input={
                "questions": [
                    {"id": "scope", "question": "Which scope should we use?"},
                    {"id": "format", "question": "Which format should we emit?"},
                ]
            },
        )
        transcript = Path(pre_payload["transcript_path"])
        self.append_user_message(transcript, turn_id, "Injected AGENTS.md context")
        self.append_user_message(transcript, turn_id, "Help me compare the available choices.")

        pre = plan_artifacts.handle_payload(pre_payload)

        self.assertEqual({"continue": True}, pre)
        directory = self.plan_dirs()[0]
        alignment = self.alignment(directory)
        self.assertIn("Help me compare the available choices.", alignment)
        self.assertNotIn("Injected AGENTS.md context", alignment)
        self.assertIn('"question_id":"scope"', alignment)
        self.assertIn('"question_id":"format"', alignment)
        self.assertFalse((directory / "current.md").exists())

        post = plan_artifacts.handle_payload(
            self.payload(
                "PostToolUse",
                turn_id=turn_id,
                mode="default",
                tool_name="request_user_input",
                tool_use_id="tool-default",
                tool_response={
                    "answers": {
                        "scope": {"answers": ["Narrow"]},
                        "format": {"answers": ["Markdown"]},
                    }
                },
            )
        )
        self.assertEqual({"continue": True}, post)
        alignment = self.alignment(directory)
        self.assertIn("Narrow", alignment)
        self.assertIn("Markdown", alignment)
        self.assertEqual(2, alignment.count('"status":"answered"'))

    def test_marked_conversation_question_is_paired_with_next_answer(self) -> None:
        self.start_plan()
        question = (
            "<!-- superpowers-plan-question -->\n"
            "Should the old plan remain the baseline?\n"
            "<!-- /superpowers-plan-question -->"
        )
        plan_artifacts.handle_payload(
            self.payload("Stop", turn_id="turn-2", last_assistant_message=question)
        )
        plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-3",
                prompt="Yes, only replace the approved section.",
            )
        )
        alignment = self.alignment(self.plan_dirs()[0])
        self.assertIn("Should the old plan remain the baseline?", alignment)
        self.assertIn("Yes, only replace the approved section.", alignment)
        self.assertEqual(1, alignment.count("## Q-"))
        self.assertEqual(2, alignment.count("## D-"))

    def test_default_marked_question_creates_alignment_and_pairs_answer(self) -> None:
        turn_id = "turn-default-direct-question"
        stop_payload = self.payload(
            "Stop",
            turn_id=turn_id,
            mode="default",
            last_assistant_message=(
                "<!-- superpowers-plan-question -->\n"
                "Should this remain a lightweight artifact?\n"
                "<!-- /superpowers-plan-question -->"
            ),
        )
        self.append_user_message(
            Path(stop_payload["transcript_path"]),
            turn_id,
            "Ask one direct clarification before planning.",
        )

        stopped = plan_artifacts.handle_payload(stop_payload)

        self.assertTrue(stopped["continue"])
        directory = self.plan_dirs()[0]
        self.assertIn("Ask one direct clarification before planning.", self.alignment(directory))
        plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-default-direct-answer",
                mode="default",
                prompt="Yes, keep it lightweight.",
            )
        )
        alignment = self.alignment(directory)
        self.assertIn("Should this remain a lightweight artifact?", alignment)
        self.assertIn("Yes, keep it lightweight.", alignment)
        self.assertIn('"status":"answered"', alignment)

    def test_empty_structured_response_records_no_answer_resolution(self) -> None:
        self.start_plan()
        plan_artifacts.handle_payload(
            self.payload(
                "PreToolUse",
                turn_id="turn-2",
                tool_name="request_user_input",
                tool_use_id="tool-empty",
                tool_input={
                    "autoResolutionMs": 60000,
                    "questions": [{"id": "optional", "question": "Optional choice?"}],
                },
            )
        )
        result = plan_artifacts.handle_payload(
            self.payload(
                "PostToolUse",
                turn_id="turn-2",
                tool_name="request_user_input",
                tool_use_id="tool-empty",
                tool_response=json.dumps({"answers": {}}),
            )
        )
        self.assertTrue(result["continue"])
        alignment = self.alignment(self.plan_dirs()[0])
        self.assertIn("_No answer returned (empty or auto-resolved)._", alignment)
        self.assertIn('"status":"answered"', alignment)

    def test_cancelled_structured_question_is_settled_without_post_tool_use(self) -> None:
        self.start_plan()
        plan_artifacts.handle_payload(
            self.payload(
                "PreToolUse",
                turn_id="turn-2",
                tool_name="request_user_input",
                tool_use_id="tool-cancelled",
                tool_input={
                    "questions": [{"id": "required", "question": "Required choice?"}]
                },
            )
        )
        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-3",
                prompt="Continue after cancelling that question.",
            )
        )
        self.assertTrue(result["continue"])
        alignment = self.alignment(self.plan_dirs()[0])
        self.assertIn('"status":"cancelled_or_failed"', alignment)
        self.assertIn("_Cancelled or tool failed before PostToolUse._", alignment)
        self.assertIn("Continue after cancelling that question.", alignment)
        self.assertNotIn("_Pending_", alignment)

    def test_one_linked_session_cannot_cancel_another_sessions_question(self) -> None:
        self.start_plan("session-a1b2c3d4")
        plan = "# Shared Plan\n\nKeep session ownership."
        self.save(plan, "session-a1b2c3d4")
        directory = self.plan_dirs()[0]
        linked = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                session_id="session-e5f6a7b8",
                mode="default",
                prompt=f"PLEASE IMPLEMENT THIS PLAN:\n{plan}",
            )
        )
        self.assertTrue(linked["continue"])
        plan_artifacts.handle_payload(
            self.payload(
                "PreToolUse",
                session_id="session-a1b2c3d4",
                turn_id="turn-question",
                tool_name="request_user_input",
                tool_use_id="tool-owned-by-a",
                tool_input={"questions": [{"id": "owner", "question": "Answer in A?"}]},
            )
        )

        plan_artifacts.handle_payload(
            self.payload(
                "SessionStart",
                session_id="session-e5f6a7b8",
                turn_id="turn-b-resume",
                mode="default",
                source="resume",
            )
        )
        alignment = self.alignment(directory)
        self.assertIn('"status":"pending"', alignment)
        self.assertIn("_Pending_", alignment)

        plan_artifacts.handle_payload(
            self.payload(
                "SessionStart",
                session_id="session-a1b2c3d4",
                turn_id="turn-a-resume",
                source="resume",
            )
        )
        alignment = self.alignment(directory)
        self.assertIn('"status":"cancelled_or_failed"', alignment)
        self.assertNotIn("_Pending_", alignment)

    def test_plan_save_renames_draft_versions_and_deduplicates(self) -> None:
        self.start_plan()
        first = "# 工作流 Evals\n\n## Task 1\n\nKeep the baseline."
        result = self.save(first)
        self.assertTrue(result["continue"])
        directory = self.plan_dirs()[0]
        self.assertFalse(directory.name.startswith("draft-"))
        self.assertIn("工作流-evals-sessiona", directory.name)
        self.assertEqual(first + "\n", (directory / "current.md").read_text())
        self.assertEqual(first + "\n", (directory / "revisions" / "0001.md").read_text())

        second = first + "\n\n## Task 2\n\nAdd the new fixture."
        self.save(second, turn_id="turn-3")
        self.save(second, turn_id="turn-4")
        self.assertEqual(second + "\n", (directory / "current.md").read_text())
        self.assertEqual(
            ["0001.md", "0002.md"],
            sorted(path.name for path in (directory / "revisions").iterdir()),
        )

    def test_reentering_plan_mode_reuses_one_directory_and_appends_versions(self) -> None:
        self.start_plan()
        first = "# Reentry Plan\n\nVersion one."
        second = "# Reentry Plan\n\nVersion two."
        third = "# Reentry Plan\n\nVersion three."
        self.save(first, turn_id="turn-2")
        directory = self.plan_dirs()[0]

        plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-3",
                mode="default",
                prompt="Explain the current status.",
            )
        )
        reentered = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-4",
                mode="plan",
                prompt="Revise this Plan to version two.",
            )
        )
        self.assertIn(
            str(directory / "current.md"),
            reentered["hookSpecificOutput"]["additionalContext"],
        )
        self.save(second, turn_id="turn-4")

        plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-5",
                mode="default",
                prompt="Implement the plan.",
            )
        )
        plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-6",
                mode="plan",
                prompt="Revise this Plan to version three.",
            )
        )
        self.save(third, turn_id="turn-6")

        self.assertEqual([directory], self.plan_dirs())
        self.assertEqual(third + "\n", (directory / "current.md").read_text())
        self.assertEqual(
            ["0001.md", "0002.md", "0003.md"],
            sorted(path.name for path in (directory / "revisions").iterdir()),
        )
        alignment = self.alignment(directory)
        self.assertIn("Revise this Plan to version two.", alignment)
        self.assertIn("Revise this Plan to version three.", alignment)
        self.assertNotIn("Explain the current status.", alignment)
        self.assertNotIn("Implement the plan.", alignment)

    def test_default_artifact_handoff_appends_revision_without_native_wrapper(self) -> None:
        self.start_plan()
        first = "# Default Artifact Plan\n\nVersion one."
        second = "# Default Artifact Plan\n\nVersion two."
        self.save(first)
        directory = self.plan_dirs()[0]

        result = self.save_default_artifact(second)

        self.assertTrue(result["continue"])
        self.assertEqual([directory], self.plan_dirs())
        self.assertEqual(second + "\n", (directory / "current.md").read_text())
        self.assertEqual(
            ["0001.md", "0002.md"],
            sorted(path.name for path in (directory / "revisions").iterdir()),
        )

    def test_default_artifact_handoff_can_create_journal_without_plan_mode(self) -> None:
        plan = "# Default-Only Plan\n\nStart the journal from this handoff."

        result = self.save_default_artifact(plan)

        self.assertTrue(result["continue"])
        directory = self.plan_dirs()[0]
        self.assertEqual(plan + "\n", (directory / "current.md").read_text())
        self.assertEqual(plan + "\n", (directory / "revisions" / "0001.md").read_text())

    def test_plan_can_contain_fenced_code_without_losing_content(self) -> None:
        plan = (
            "# Plan With Code\n\n"
            "```python\n"
            "print('keep the full body')\n"
            "```\n\n"
            "Verify the saved artifact byte for byte."
        )

        result = self.save_default_artifact(plan)

        self.assertTrue(result["continue"])
        directory = self.plan_dirs()[0]
        self.assertEqual(plan + "\n", (directory / "current.md").read_text())

    def test_default_artifact_handoff_recovers_from_transcript(self) -> None:
        plan = "# Recovered Default Plan\n\nRead the invisible markers from rollout."
        turn_id = "turn-default-transcript"
        transcript = self.transcript("session-a1b2c3d4", turn_id, "default")
        self.append_assistant_message(
            transcript,
            turn_id,
            "<!-- superpowers-artifact-plan -->\n"
            f"{plan}\n"
            "<!-- /superpowers-artifact-plan -->",
        )

        result = plan_artifacts.handle_payload(
            {
                "hook_event_name": "Stop",
                "session_id": "session-a1b2c3d4",
                "turn_id": turn_id,
                "cwd": str(self.cwd),
                "transcript_path": str(transcript),
                "last_assistant_message": None,
            }
        )

        self.assertTrue(result["continue"])
        directory = self.plan_dirs()[0]
        self.assertEqual(plan + "\n", (directory / "current.md").read_text())

    def test_inline_and_fenced_markers_are_not_artifacts(self) -> None:
        messages = [
            "Example only: <proposed_plan>...</proposed_plan>",
            "Should this explanatory response persist?",
            (
                "```html\n"
                "<!-- superpowers-artifact-plan -->\n"
                "# Example Plan\n\n"
                "Do not persist this fenced example.\n"
                "<!-- /superpowers-artifact-plan -->\n"
                "```"
            ),
            (
                "```html\n"
                "<!-- superpowers-plan-question -->\n"
                "Do not record this fenced example?\n"
                "<!-- /superpowers-plan-question -->\n"
                "```"
            ),
        ]
        for index, message in enumerate(messages):
            result = plan_artifacts.handle_payload(
                self.payload(
                    "Stop",
                    session_id=f"session-example-{index}",
                    turn_id=f"turn-example-{index}",
                    mode="default",
                    last_assistant_message=message,
                )
            )
            self.assertTrue(result["continue"])
        self.assertFalse((self.cwd / ".plan").exists())

    def test_placeholder_plan_is_rejected(self) -> None:
        result = plan_artifacts.handle_payload(
            self.payload(
                "Stop",
                mode="default",
                last_assistant_message="<proposed_plan>\n...\n</proposed_plan>",
            )
        )
        self.assertFalse(result["continue"])
        self.assertIn("placeholder", result["stopReason"].lower())
        self.assertFalse((self.cwd / ".plan").exists())

    def test_unmarked_default_reply_does_not_overwrite_active_plan(self) -> None:
        self.start_plan()
        plan = "# Durable Plan\n\nKeep this version."
        self.save(plan)
        directory = self.plan_dirs()[0]

        result = plan_artifacts.handle_payload(
            self.payload(
                "Stop",
                turn_id="turn-default-explanation",
                mode="default",
                last_assistant_message="# Status\n\nThis is an ordinary explanation.",
            )
        )

        self.assertTrue(result["continue"])
        self.assertEqual(plan + "\n", (directory / "current.md").read_text())
        self.assertEqual(
            ["0001.md"],
            sorted(path.name for path in (directory / "revisions").iterdir()),
        )

    def test_stop_recovers_native_plan_item_when_last_message_is_stripped(self) -> None:
        self.start_plan()
        plan = "# Native Plan Item\n\nCodex strips the wrapper before Stop."
        transcript = self.transcript("session-a1b2c3d4", "turn-native", "plan")
        self.append_plan_item(transcript, "turn-native", plan)
        result = plan_artifacts.handle_payload(
            {
                "hook_event_name": "Stop",
                "session_id": "session-a1b2c3d4",
                "turn_id": "turn-native",
                "cwd": str(self.cwd),
                "transcript_path": str(transcript),
                "last_assistant_message": None,
            }
        )
        self.assertTrue(result["continue"])
        directory = self.plan_dirs()[0]
        self.assertIn("native-plan-item", directory.name)
        self.assertEqual(plan + "\n", (directory / "current.md").read_text())
        self.assertEqual(plan + "\n", (directory / "revisions" / "0001.md").read_text())

    def test_current_write_retry_reuses_the_durable_revision(self) -> None:
        self.start_plan()
        plan = "# Recoverable\n\nKeep the durable revision."
        original_atomic_write = plan_artifacts.atomic_write

        def fail_current(path: Path, text: str) -> None:
            if path.name == "current.md":
                raise OSError("current unavailable")
            original_atomic_write(path, text)

        with mock.patch.object(plan_artifacts, "atomic_write", side_effect=fail_current):
            failed = self.save(plan)
        self.assertFalse(failed["continue"])
        directory = self.plan_dirs()[0]
        self.assertEqual(["0001.md"], [path.name for path in (directory / "revisions").iterdir()])
        self.assertFalse((directory / "current.md").exists())

        recovered = self.save(plan, turn_id="turn-3")
        self.assertTrue(recovered["continue"])
        self.assertEqual(["0001.md"], [path.name for path in (directory / "revisions").iterdir()])
        self.assertEqual(plan + "\n", (directory / "current.md").read_text())

    def test_two_sessions_in_one_cwd_keep_independent_plans(self) -> None:
        self.start_plan("session-a1b2c3d4")
        self.start_plan("session-e5f6a7b8")
        self.save("# First\n\nFirst task.", "session-a1b2c3d4")
        self.save("# Second\n\nSecond task.", "session-e5f6a7b8")
        directories = self.plan_dirs()
        self.assertEqual(2, len(directories))
        currents = {(path / "current.md").read_text() for path in directories}
        self.assertEqual({"# First\n\nFirst task.\n", "# Second\n\nSecond task.\n"}, currents)
        for directory in directories:
            self.assertEqual(1, len(list((directory / "revisions").glob("*.md"))))

    def test_two_plan_sessions_can_write_concurrently_in_one_cwd(self) -> None:
        start_barrier = threading.Barrier(2)
        save_barrier = threading.Barrier(2)

        def worker(session_id: str, title: str) -> None:
            prompt = self.payload(
                "UserPromptSubmit",
                session_id=session_id,
                turn_id="turn-start",
                prompt=f"Requirements for {title}.",
            )
            start_barrier.wait()
            self.assertTrue(plan_artifacts.handle_payload(prompt)["continue"])
            stop = self.payload(
                "Stop",
                session_id=session_id,
                turn_id="turn-save",
                last_assistant_message=(
                    f"<proposed_plan>\n# {title}\n\nIndependent task.\n</proposed_plan>"
                ),
            )
            save_barrier.wait()
            self.assertTrue(plan_artifacts.handle_payload(stop)["continue"])

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(worker, "session-a1b2c3d4", "Parallel One"),
                executor.submit(worker, "session-e5f6a7b8", "Parallel Two"),
            ]
            for future in futures:
                future.result()

        directories = self.plan_dirs()
        self.assertEqual(2, len(directories))
        self.assertEqual(
            {"# Parallel One\n\nIndependent task.\n", "# Parallel Two\n\nIndependent task.\n"},
            {(directory / "current.md").read_text() for directory in directories},
        )

    def test_session_start_restores_paths_only(self) -> None:
        self.start_plan()
        plan = "# Resume Me\n\nThe complete plan stays on disk."
        self.save(plan)
        directory = self.plan_dirs()[0]
        for source in ("resume", "compact"):
            result = plan_artifacts.handle_payload(
                self.payload("SessionStart", turn_id=f"turn-{source}", source=source)
            )
            context = result["hookSpecificOutput"]["additionalContext"]
            self.assertIn(str(directory / "alignment.md"), context)
            self.assertIn(str(directory / "current.md"), context)
            self.assertNotIn("The complete plan stays on disk.", context)

    def test_fresh_context_links_exact_plan_without_injecting_its_body(self) -> None:
        self.start_plan()
        plan = "# Existing Plan\n\nPreserve all decisions."
        self.save(plan)
        directory = self.plan_dirs()[0]
        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                session_id="fresh-session-2222",
                mode="default",
                prompt=f"PLEASE IMPLEMENT THIS PLAN:\n{plan}",
            )
        )
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(directory / "current.md"), context)
        self.assertNotIn("Preserve all decisions.", context)
        metadata, _ = plan_artifacts.read_alignment(directory / "alignment.md")
        self.assertIn("fresh-session-2222", metadata["sessions"])

        unrelated = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                session_id="unrelated-session",
                mode="default",
                prompt="Explain an unrelated module.",
            )
        )
        self.assertNotIn("hookSpecificOutput", unrelated)

    def test_plan_without_h1_keeps_draft_name_and_content(self) -> None:
        self.start_plan()
        plan = "Goal\n\nKeep this Plan even without a title."
        result = self.save(plan)
        self.assertTrue(result["continue"])
        directory = self.plan_dirs()[0]
        self.assertTrue(directory.name.startswith("draft-"))
        self.assertEqual(plan + "\n", (directory / "current.md").read_text())

    def test_rename_failure_keeps_draft_and_still_saves_plan(self) -> None:
        self.start_plan()
        plan = "# Rename Can Fail\n\nThe Plan content remains required."
        with mock.patch.object(Path, "rename", side_effect=OSError("rename denied")):
            result = self.save(plan)
        self.assertTrue(result["continue"])
        directory = self.plan_dirs()[0]
        self.assertTrue(directory.name.startswith("draft-"))
        self.assertEqual(plan + "\n", (directory / "current.md").read_text())
        self.assertEqual(plan + "\n", (directory / "revisions" / "0001.md").read_text())

    def test_ambiguous_fresh_context_fails_closed(self) -> None:
        first = self.start_plan("session-a1b2c3d4")
        second = self.start_plan("session-e5f6a7b8")
        body = "# Same Plan\n\nOne shared body.\n"
        plan_artifacts.atomic_write(first / "current.md", body)
        plan_artifacts.atomic_write(second / "current.md", body)
        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                session_id="fresh-session-3333",
                mode="default",
                prompt="PLEASE IMPLEMENT THIS PLAN:\n" + body,
            )
        )
        self.assertFalse(result["continue"])
        self.assertIn("multiple artifact directories", result["stopReason"])

    def test_unmatched_or_changed_native_handoff_fails_closed(self) -> None:
        self.start_plan()
        self.save("# Original\n\nKeep this body.")
        unmatched = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                session_id="fresh-session-4444",
                mode="default",
                prompt="PLEASE IMPLEMENT THIS PLAN:\n# Unknown\n\nDifferent body.",
            )
        )
        self.assertFalse(unmatched["continue"])
        self.assertIn("does not match any", unmatched["stopReason"])

        changed = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                mode="default",
                prompt="PLEASE IMPLEMENT THIS PLAN:\n# Original\n\nChanged body.",
            )
        )
        self.assertFalse(changed["continue"])
        self.assertIn("does not match", changed["stopReason"])

    def test_default_task_and_subagent_do_not_create_artifacts(self) -> None:
        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                mode="default",
                prompt="Explain this function.",
            )
        )
        self.assertTrue(result["continue"])
        self.assertFalse((self.cwd / ".plan").exists())

        pre = plan_artifacts.handle_payload(
            self.payload(
                "PreToolUse",
                agent_id="child-agent",
                tool_name="request_user_input",
            )
        )
        self.assertEqual({"continue": True}, pre)
        self.assertFalse((self.cwd / ".plan").exists())

    def test_native_implement_prompt_is_not_a_new_directive(self) -> None:
        self.start_plan()
        self.save("# Ready\n\nImplement it.")
        directory = self.plan_dirs()[0]
        before = self.alignment(directory)
        plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                turn_id="turn-9",
                mode="default",
                prompt="Implement the plan.",
            )
        )
        self.assertEqual(before, self.alignment(self.plan_dirs()[0]))

    def test_required_writes_fail_closed(self) -> None:
        with mock.patch.object(plan_artifacts, "atomic_write", side_effect=OSError("read only")):
            prompt = plan_artifacts.handle_payload(
                self.payload("UserPromptSubmit", prompt="A required directive.")
            )
        self.assertFalse(prompt["continue"])
        self.assertIn("read only", prompt["stopReason"])

        self.start_plan()
        with mock.patch.object(plan_artifacts, "write_alignment", side_effect=OSError("full disk")):
            pre = plan_artifacts.handle_payload(
                self.payload(
                    "PreToolUse",
                    turn_id="turn-10",
                    tool_name="request_user_input",
                    tool_use_id="tool-fail",
                    tool_input={"questions": [{"id": "q", "question": "Continue?"}]},
                )
            )
        self.assertEqual("block", pre["decision"])
        self.assertIn("full disk", pre["reason"])

    def test_post_stop_and_session_read_fail_closed(self) -> None:
        self.start_plan()
        pre_payload = self.payload(
            "PreToolUse",
            turn_id="turn-2",
            tool_name="request_user_input",
            tool_use_id="tool-2",
            tool_input={"questions": [{"id": "q", "question": "Choose?"}]},
        )
        plan_artifacts.handle_payload(pre_payload)
        with mock.patch.object(plan_artifacts, "write_alignment", side_effect=OSError("no answer")):
            post = plan_artifacts.handle_payload(
                self.payload(
                    "PostToolUse",
                    turn_id="turn-2",
                    tool_name="request_user_input",
                    tool_use_id="tool-2",
                    tool_response={"answers": {"q": "Choice"}},
                )
            )
        self.assertFalse(post["continue"])
        self.assertIn("no answer", post["stopReason"])

        with mock.patch.object(plan_artifacts, "write_exclusive", side_effect=OSError("no revision")):
            stopped = self.save("# Blocked\n\nDo not hand off this Plan.", turn_id="turn-3")
        self.assertFalse(stopped["continue"])
        self.assertIn("no revision", stopped["stopReason"])

        directory = self.plan_dirs()[0]
        (directory / "alignment.md").write_text("invalid\n", encoding="utf-8")
        resumed = plan_artifacts.handle_payload(
            self.payload("SessionStart", turn_id="turn-resume", source="resume")
        )
        self.assertFalse(resumed["continue"])
        self.assertIn("invalid alignment metadata", resumed["stopReason"])


if __name__ == "__main__":
    unittest.main()
