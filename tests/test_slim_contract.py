import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "brainstorming",
    "code-review",
    "writing-plans",
    "systematic-debugging",
    "verification-before-completion",
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
}
REMOVED_RUNTIME_TERMS = {
    "start_requirement_loop",
    "await_requirement_input",
    "approve_requirements",
    "record_plan",
    "begin_execution",
    "assess_review",
    "prepare_verification",
    "record_verification",
    "PostToolUse",
    "diff hash",
    "completion gate",
    "mcpServers",
}


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text()


class SlimSuperpowersContractTest(unittest.TestCase):
    def test_only_five_scoped_skills_are_exposed(self) -> None:
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
        for term in REMOVED_RUNTIME_TERMS:
            self.assertNotIn(term, text)

    def test_runtime_controller_is_absent(self) -> None:
        for relative in (".mcp.json", "hooks", "schemas", "scripts"):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_non_codex_bootstraps_are_removed(self) -> None:
        for relative in (".claude-plugin", ".cursor-plugin", ".kimi-plugin", ".opencode", ".pi"):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_manifest_describes_scoped_methods(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        self.assertEqual("superpowers", manifest["name"])
        self.assertIn("scoped", manifest["description"].lower())
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("TDD", manifest["interface"]["longDescription"])

    def test_requirement_handoff_and_negative_trigger_are_explicit(self) -> None:
        brainstorming = skill_text("brainstorming")
        planning = skill_text("writing-plans")
        self.assertIn("code research", brainstorming.lower())
        self.assertIn("Design Handoff", brainstorming)
        self.assertIn("superpowers:writing-plans", brainstorming)
        self.assertIn("superpowers:brainstorming", planning)
        self.assertIn("Plan Handoff", planning)
        self.assertIn("Global Constraints", planning)
        self.assertIn("Interfaces", planning)
        self.assertIn("not execution authorization", planning)
        self.assertIn("already authorized Plan plus execution", planning)

    def test_plan_self_review_is_inline_and_routes_gaps(self) -> None:
        planning = skill_text("writing-plans")
        self.assertIn("## Plan Self-Review", planning)
        self.assertIn("Requirement coverage", planning)
        self.assertIn("Decision completeness", planning)
        self.assertIn("Placeholder and ambiguity scan", planning)
        self.assertIn("Cross-task consistency", planning)
        self.assertIn("Constraints and verification", planning)
        self.assertIn("Fix plan-only issues inline", planning)
        self.assertIn("rerun the affected checks", planning)
        self.assertIn("return to `superpowers:brainstorming`", planning)
        self.assertIn("Only after Plan Self-Review is clean", planning)
        self.assertNotIn("plan-document-reviewer", planning)
        self.assertNotIn("PLAN_CHECKED", planning)
        self.assertLess(
            planning.index("## Plan Self-Review"),
            planning.index("## Execution Boundary"),
        )

    def test_debugging_and_verification_handoff_is_explicit(self) -> None:
        debugging = skill_text("systematic-debugging").lower()
        verification = skill_text("verification-before-completion")
        self.assertIn("root cause", debugging)
        self.assertIn("superpowers:verification-before-completion", debugging)
        self.assertIn("fresh evidence", verification.lower())
        self.assertIn("superpowers:code-review", verification)
        self.assertIn("user explicitly asks", verification)
        self.assertIn("File or line", verification)

    def test_review_is_bounded_and_read_only(self) -> None:
        review = skill_text("code-review").lower()
        self.assertIn("full review", review)
        self.assertIn("scoped", review)
        self.assertIn("third round", review)
        self.assertIn("read-only", review)
        self.assertIn("must not delegate", review)
        self.assertIn("review handoff", review)
        self.assertIn("superpowers:verification-before-completion", review)


if __name__ == "__main__":
    unittest.main()
