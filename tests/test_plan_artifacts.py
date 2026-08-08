import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
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
        path = self.transcripts / f"{session_id.replace('/', '-')}.jsonl"
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
                "item": {"type": "Plan", "text": plan},
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

    def directory(self, session_id: str = "session-a1b2c3d4") -> Path:
        return plan_artifacts.plan_directory(str(self.cwd), session_id)

    def start_plan(self, session_id: str = "session-a1b2c3d4") -> dict:
        return plan_artifacts.handle_payload(
            self.payload("UserPromptSubmit", session_id=session_id, prompt="Plan this change.")
        )

    def save_native(
        self,
        plan: str,
        session_id: str = "session-a1b2c3d4",
        turn_id: str = "turn-plan",
    ) -> dict:
        return plan_artifacts.handle_payload(
            self.payload(
                "Stop",
                session_id=session_id,
                turn_id=turn_id,
                last_assistant_message=f"<proposed_plan>\n{plan}\n</proposed_plan>",
            )
        )

    def save_default(
        self,
        plan: str,
        session_id: str = "session-a1b2c3d4",
        turn_id: str = "turn-default-plan",
    ) -> dict:
        return plan_artifacts.handle_payload(
            self.payload(
                "Stop",
                session_id=session_id,
                turn_id=turn_id,
                mode="default",
                last_assistant_message=(
                    "<!-- superpowers-artifact-plan -->\n"
                    f"{plan}\n"
                    "<!-- /superpowers-artifact-plan -->"
                ),
            )
        )

    def test_plan_mode_injects_two_paths_without_file_contents(self) -> None:
        result = self.start_plan()
        directory = self.directory()

        self.assertTrue(result["continue"])
        self.assertEqual("# Current alignment\n", (directory / "alignment.md").read_text())
        self.assertFalse((directory / "current.md").exists())
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(directory / "alignment.md"), context)
        self.assertIn(str(directory / "current.md"), context)
        self.assertNotIn("Plan this change.", context)
        self.assertNotIn("# Current alignment", context)

    def test_alignment_is_plain_mutable_markdown_not_a_parsed_journal(self) -> None:
        self.start_plan()
        alignment = self.directory() / "alignment.md"
        current_summary = "# Current alignment\n\nUse the simpler design.\n"
        alignment.write_text(current_summary, encoding="utf-8")

        result = self.start_plan()

        self.assertTrue(result["continue"])
        self.assertEqual(current_summary, alignment.read_text(encoding="utf-8"))

    def test_default_conversation_without_reminders_creates_nothing(self) -> None:
        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                mode="default",
                prompt="Explain this function.",
            )
        )

        self.assertTrue(result["continue"])
        self.assertFalse((self.cwd / ".plan").exists())
        self.assertNotIn("hookSpecificOutput", result)

    def test_new_plan_replaces_current_without_history_or_versions(self) -> None:
        self.start_plan()
        first = "# First plan\n\nUse the first approach."
        second = "# Current plan\n\nUse the approved simpler approach."

        self.assertTrue(self.save_native(first)["continue"])
        self.assertTrue(self.save_native(second, turn_id="turn-plan-2")["continue"])

        directory = self.directory()
        self.assertEqual(second + "\n", (directory / "current.md").read_text())
        self.assertEqual(
            {"alignment.md", "current.md"},
            {path.name for path in directory.iterdir()},
        )

    def test_sessions_in_one_cwd_use_independent_directories(self) -> None:
        first_session = "session/one"
        second_session = "session-two"
        self.start_plan(first_session)
        self.start_plan(second_session)
        self.save_native("# One\n\nFirst task.", first_session)
        self.save_native("# Two\n\nSecond task.", second_session)

        first = self.directory(first_session)
        second = self.directory(second_session)
        self.assertNotEqual(first, second)
        self.assertEqual("# One\n\nFirst task.\n", (first / "current.md").read_text())
        self.assertEqual("# Two\n\nSecond task.\n", (second / "current.md").read_text())
        self.assertEqual((self.cwd / ".plan").resolve(), first.parent.resolve())
        self.assertEqual((self.cwd / ".plan").resolve(), second.parent.resolve())

    def test_session_start_restores_paths_only(self) -> None:
        self.start_plan()
        plan = "# Resume\n\nRemember this content."
        self.save_native(plan)

        result = plan_artifacts.handle_payload(
            self.payload("SessionStart", turn_id="turn-resume", source="resume")
        )

        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(self.directory() / "alignment.md"), context)
        self.assertIn(str(self.directory() / "current.md"), context)
        self.assertNotIn("Remember this content.", context)

    def test_native_plan_item_is_saved_when_wrapper_is_not_in_last_message(self) -> None:
        payload = self.payload(
            "Stop",
            turn_id="turn-native-item",
            last_assistant_message="The Plan is shown in the native card.",
        )
        plan = "# Native Plan\n\nRecovered from the transcript item."
        self.append_plan_item(Path(payload["transcript_path"]), "turn-native-item", plan)

        result = plan_artifacts.handle_payload(payload)

        self.assertTrue(result["continue"])
        self.assertEqual(plan + "\n", (self.directory() / "current.md").read_text())

    def test_default_marker_saves_plan_and_unmarked_reply_does_not_replace_it(self) -> None:
        plan = "# Default Plan\n\nVisible body."
        self.assertTrue(self.save_default(plan)["continue"])
        current = self.directory() / "current.md"
        self.assertEqual(plan + "\n", current.read_text())

        result = plan_artifacts.handle_payload(
            self.payload(
                "Stop",
                turn_id="turn-ordinary",
                mode="default",
                last_assistant_message="An ordinary explanation, not a Plan.",
            )
        )
        self.assertTrue(result["continue"])
        self.assertEqual(plan + "\n", current.read_text())

    def test_marker_example_inside_other_text_is_not_treated_as_a_plan(self) -> None:
        message = (
            "Example only:\n```html\n<!-- superpowers-artifact-plan -->\n"
            "Placeholder\n<!-- /superpowers-artifact-plan -->\n```"
        )
        result = plan_artifacts.handle_payload(
            self.payload("Stop", mode="default", last_assistant_message=message)
        )

        self.assertTrue(result["continue"])
        self.assertFalse((self.cwd / ".plan").exists())

    def test_reminder_write_failure_warns_and_never_blocks(self) -> None:
        warning = io.StringIO()
        with mock.patch.object(
            plan_artifacts, "replace_text", side_effect=OSError("read only")
        ), redirect_stderr(warning):
            result = self.save_native("# Plan\n\nStill visible in the conversation.")

        self.assertTrue(result["continue"])
        self.assertNotIn("decision", result)
        self.assertNotIn("stopReason", result)
        self.assertIn("was not saved", warning.getvalue())

    def test_fresh_implementation_prompt_is_not_exact_matched_or_blocked(self) -> None:
        self.start_plan("original-session")
        self.save_native("# Approved\n\nImplement this.", "original-session")

        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                session_id="fresh-session",
                mode="default",
                prompt="PLEASE IMPLEMENT THIS PLAN:\n# Approved\n\nReworded.",
            )
        )

        self.assertTrue(result["continue"])
        self.assertNotIn("hookSpecificOutput", result)
        self.assertFalse(self.directory("fresh-session").exists())

    def test_subagent_events_do_not_create_or_update_reminders(self) -> None:
        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                agent_id="child-agent",
                prompt="Plan from a child.",
            )
        )

        self.assertTrue(result["continue"])
        self.assertFalse((self.cwd / ".plan").exists())

    def test_unreadable_transcript_is_a_soft_miss(self) -> None:
        result = plan_artifacts.handle_payload(
            self.payload(
                "UserPromptSubmit",
                transcript_path=str(self.cwd / "missing.jsonl"),
                prompt="Continue.",
            )
        )

        self.assertTrue(result["continue"])
        self.assertFalse((self.cwd / ".plan").exists())


if __name__ == "__main__":
    unittest.main()
