from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.forge.validate_extension_docs import validate_extension_docs


class ExtensionDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]

    def test_complete_phase_corpus_is_self_consistent(self) -> None:
        report = validate_extension_docs(self.repo_root)

        self.assertTrue(report["valid"], json.dumps(report["issues"], indent=2))
        self.assertEqual(report["counts"]["phase_directories"], 12)
        self.assertEqual(report["counts"]["phase_readmes"], 12)
        self.assertEqual(report["counts"]["books"], 58)
        self.assertGreaterEqual(report["counts"]["mermaid_blocks"], 70)

    def test_broken_relative_link_blocks_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory) / "repo"
            fixture_root.mkdir()
            fixture_extension = fixture_root / "QUANT-LAB-INFRA-UPGRADE"
            shutil.copytree(
                self.repo_root / "QUANT-LAB-INFRA-UPGRADE",
                fixture_extension,
            )
            readme = fixture_extension / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\n[Missing build anchor](not-present.md)\n",
                encoding="utf-8",
            )

            report = validate_extension_docs(fixture_root)

        self.assertFalse(report["valid"])
        self.assertIn(
            "broken_relative_link",
            {issue["code"] for issue in report["issues"]},
        )


if __name__ == "__main__":
    unittest.main()
