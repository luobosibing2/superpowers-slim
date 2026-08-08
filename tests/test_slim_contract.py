import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "brainstorming",
    "code-review",
    "writing-plans",
    "systematic-debugging",
}
REMOVED_SKILLS = {
    "using-superpowers",
    "dispatching-parallel-agents",
    "executing-plans",
    "finishing-a-development-branch",
    "receiving-code-review",
    "requesting-code-review",
    "subagent-driven-development",
    "test-driven-development",
    "using-git-worktrees",
    "writing-skills",
    "verification-before-completion",
}


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text()


class SlimSuperpowersContractTest(unittest.TestCase):
    def test_only_four_scoped_skills_are_exposed(self) -> None:
        actual = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual(SKILLS, actual)

    def test_skill_prompt_budget_is_below_500_lines(self) -> None:
        total = sum(len(skill_text(name).splitlines()) for name in SKILLS)
        self.assertLessEqual(total, 500)

    def test_skills_are_markdown_only(self) -> None:
        for name in SKILLS:
            files = {
                path.relative_to(ROOT / "skills" / name).as_posix()
                for path in (ROOT / "skills" / name).rglob("*")
                if path.is_file()
            }
            self.assertEqual({"SKILL.md"}, files, name)

    def test_removed_workflows_are_not_runtime_dependencies(self) -> None:
        surfaces = [ROOT / "README.md", ROOT / ".codex-plugin" / "plugin.json"]
        surfaces.extend(ROOT / "skills" / name / "SKILL.md" for name in SKILLS)
        text = "\n".join(path.read_text() for path in surfaces)
        for name in REMOVED_SKILLS:
            self.assertNotIn(name, text)
        for term in ("mcpServers", "diff hash", "PLAN_CHECKED"):
            self.assertNotIn(term, text)

    def test_plan_reminder_is_the_only_runtime_adapter(self) -> None:
        expected = {"hooks/hooks.json", "scripts/plan_artifacts.py"}
        actual = {
            path.relative_to(ROOT).as_posix()
            for parent in (ROOT / "hooks", ROOT / "scripts")
            for path in parent.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(expected, actual)
        for relative in (".mcp.json", "schemas"):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_manifest_describes_two_mutable_reminders(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        self.assertEqual("superpowers", manifest["name"])
        self.assertIn("scoped", manifest["description"].lower())
        self.assertIn("plan-reminders", manifest["keywords"])
        self.assertNotIn("plan-journal", manifest["keywords"])
        self.assertIn("Write", manifest["interface"]["capabilities"])
        self.assertNotIn("mcpServers", manifest)

    def test_planning_keeps_semantic_freedom_and_execution_boundary(self) -> None:
        brainstorming = skill_text("brainstorming")
        planning = skill_text("writing-plans")
        compact_planning = " ".join(planning.split())
        self.assertIn("code research", brainstorming.lower())
        self.assertIn("superpowers:writing-plans", brainstorming)
        self.assertIn("superpowers:brainstorming", planning)
        self.assertIn("model-maintained summary", planning)
        self.assertIn("latest complete Plan", planning)
        self.assertIn("real consumer", planning)
        self.assertIn("minimum observable verification", planning)
        self.assertIn(
            "does not switch collaboration mode or authorize implementation",
            compact_planning,
        )
        self.assertIn("explicit implementation authorization", planning)
        self.assertNotIn("Each task must define:", planning)
        self.assertNotIn("Global Constraints", planning)
        self.assertNotIn("Plan Revision Safety", planning)

    def test_internal_representation_is_not_promoted_to_contract(self) -> None:
        planning = skill_text("writing-plans")
        compact_planning = " ".join(planning.split())
        self.assertIn("Do not freeze internal functions", planning)
        self.assertIn("producer and consumer can change together", planning)
        self.assertIn("ordinary model judgment", compact_planning)
        self.assertNotIn("Map every approved requirement", planning)
        self.assertNotIn("revisions/NNNN.md", planning)

    def test_alignment_is_current_summary_not_question_protocol(self) -> None:
        brainstorming = skill_text("brainstorming")
        adapter = (ROOT / "scripts" / "plan_artifacts.py").read_text()
        self.assertIn("Rewrite obsolete content", brainstorming)
        self.assertIn("request_user_input", brainstorming)
        for term in (
            "superpowers-plan-question",
            "ENTRY_RE",
            "question_id",
            "pending",
            "cancelled_or_failed",
            "append_question",
            "answer_pending",
        ):
            self.assertNotIn(term, adapter)

    def test_runtime_has_no_version_or_identity_protocol(self) -> None:
        adapter = (ROOT / "scripts" / "plan_artifacts.py").read_text()
        for term in (
            "revisions",
            "find_plan_for_handoff",
            "native_handoff_plan",
            "sha256",
            "stop_output",
            "block_output",
            "JournalError",
        ):
            self.assertNotIn(term, adapter)

    def test_structured_questions_remain_native(self) -> None:
        brainstorming = skill_text("brainstorming")
        compact_brainstorming = " ".join(brainstorming.split())
        self.assertIn("When `request_user_input` is listed", compact_brainstorming)
        self.assertIn("When it is not listed", compact_brainstorming)
        self.assertIn("ask one necessary question directly", compact_brainstorming)

    def test_hook_manifest_has_no_question_interception(self) -> None:
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual({"SessionStart", "UserPromptSubmit", "Stop"}, set(hooks))
        commands = {
            hook["command"]
            for groups in hooks.values()
            for group in groups
            for hook in group["hooks"]
        }
        self.assertEqual(
            {'/usr/bin/env python3 "${PLUGIN_ROOT}/scripts/plan_artifacts.py"'},
            commands,
        )

    def test_debugging_keeps_scoped_root_cause_method(self) -> None:
        debugging = skill_text("systematic-debugging")
        self.assertIn("root cause", debugging.lower())
        self.assertIn("rerun the reproduction", debugging.lower())
        self.assertIn("not a fixed attempt counter", debugging)
        self.assertNotIn("final completion claim", debugging.lower())
        self.assertNotIn("After two", debugging)
        self.assertNotIn("After three", debugging)

    def test_review_keeps_the_user_selected_bounded_policy(self) -> None:
        review = " ".join(skill_text("code-review").lower().split())
        self.assertIn("user explicitly requests", review)
        self.assertIn("full review", review)
        self.assertIn("scoped", review)
        self.assertIn("third round", review)
        self.assertIn("read-only", review)
        self.assertIn("must not delegate", review)
        self.assertIn("return control to the root agent", review)
        self.assertNotIn("evidence audit", review)
        self.assertNotIn("fix_required", review)


if __name__ == "__main__":
    unittest.main()
