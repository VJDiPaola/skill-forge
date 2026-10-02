"""Regression checks for configured project leakage, without model calls."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import eval as harness


class ProjectNameChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def load_skill(self, description="Use when reviewing a reusable workflow.",
                   body="Do not use for unrelated requests.", scope="general"):
        skill_dir = self.root / "sample"
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: sample\ndescription: '{description}'\n---\n{body}\n",
            encoding="utf-8",
        )
        (skill_dir / "catalog.yaml").write_text(
            "id: sample\norigin: codex\nkind: skill\ntags: [review]\n"
            f"targets:\n  codex: true\nscope: {scope}\nrelated: []\n",
            encoding="utf-8",
        )
        with patch.object(harness, "REPO_ROOT", self.root), \
                patch.object(harness, "git_last_modified", return_value=(None, None)):
            return harness.load_skill(skill_dir)

    def findings(self, **kwargs):
        return harness.check_no_project_names(self.load_skill(**kwargs), {})

    def test_public_names_are_enabled_in_descriptions_and_bodies(self):
        names = (
            "SpendForge", "RefereeOS", "ResumeTailor", "teamvince", "PersonalOS",
            "Commons Copilot", "earned-autonomy", "software-factory", "skill-forge",
        )
        for name in names:
            for field in ("description", "body"):
                for spelling in (name, name.lower(), name.upper()):
                    with self.subTest(name=name, field=field, spelling=spelling):
                        issues = self.findings(**{field: f"Use {spelling}."})
                        self.assertEqual(len(issues), 1)
                        self.assertIn(name, issues[0].message)
                        self.assertEqual(issues[0].severity, "warning")

    def test_project_scope_is_exempt(self):
        self.assertEqual(self.findings(
            description="Use when working on RefereeOS.",
            body="Ship SpendForge and skill-forge.", scope="project",
        ), [])

    def test_generic_words_and_larger_identifiers_do_not_match(self):
        self.assertEqual(self.findings(body=(
            "Build a software factory with earned autonomy and a copilot for commons. "
            "SpendForgeable preRefereeOS RefereeOS2 my_teamvince teamvince_config "
            "PersonalOSmosis skill-forgery"
        )), [])

    def test_paths_urls_and_punctuation_match(self):
        for text, name in (
            (r"C:\projects\RefereeOS\src", "RefereeOS"),
            ("https://teamvince.com/portfolio", "teamvince"),
            ("https://github.com/VJDiPaola/software-factory", "software-factory"),
            ("SpendForge's workflow", "SpendForge"),
            ("`Commons Copilot`", "Commons Copilot"),
        ):
            with self.subTest(text=text):
                self.assertIn(name, self.findings(body=text)[0].message)

    def test_configured_names_are_literal_not_regular_expressions(self):
        with patch.object(harness, "PROJECT_NAMES", ["acme.portal"]):
            self.assertEqual(self.findings(body="acmeXportal"), [])
            self.assertEqual(len(self.findings(body="ACME.PORTAL")), 1)

    def test_repeated_names_produce_one_warning_with_unique_hits(self):
        issues = self.findings(body="RefereeOS RefereeOS and SpendForge")
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].message,
                         "general-scope skill mentions project name(s): SpendForge, RefereeOS")

    def test_report_contains_warning_and_project_scope_stays_clean(self):
        for scope, expected in (("general", 1), ("project", 0)):
            with self.subTest(scope=scope):
                skill = self.load_skill(body="Use RefereeOS.", scope=scope)
                with patch.object(harness, "git_head", return_value="fixture"):
                    report = harness.build_report([skill], {skill.id: skill}, "all")
                findings = [issue for issue in report["skills"][0]["issues"]
                            if issue["check"] == "no_project_names"]
                self.assertEqual(len(findings), expected)
                self.assertEqual(report["summary"]["errors"], 0)
                if expected:
                    self.assertEqual(findings[0]["severity"], "warning")
                    self.assertIn("no_project_names", harness.format_markdown(report))


if __name__ == "__main__":
    unittest.main()
