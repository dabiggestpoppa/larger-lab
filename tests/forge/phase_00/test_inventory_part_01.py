from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.forge.phase0_inventory import (
    InventoryError,
    REQUIRED_COMPONENTS,
    build_core_inventory,
    collect_repository_fingerprint,
    sanitize_remote_url,
    write_part1_artifacts,
)


class InventoryPart01Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self.repo = Path(self._temporary_directory.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-b", "main")
        self._git("config", "user.email", "forge-fixture@example.invalid")
        self._git("config", "user.name", "FORGE Fixture")

        self._write(
            "oce/main.py",
            "def main():\n"
            "    return 0\n\n"
            "if __name__ == '__main__':\n"
            "    raise SystemExit(main())\n",
        )
        self._write(
            "projects/trading/nautilus/run_backtest.py",
            "def main():\n"
            "    return 0\n\n"
            "if __name__ == '__main__':\n"
            "    raise SystemExit(main())\n",
        )
        self._write("README.md", "# Fixture repository\n")
        self._write(".gitignore", ".env\nnode_modules/\n")
        self._git("add", ".")
        self._git("commit", "-m", "fixture")

    def _git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def _write(self, relative_path: str, content: str) -> None:
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _credential(self) -> str:
        # Construct at runtime so the test source is not itself a secret-shaped fixture.
        return "gh" + "p_" + ("A" * 36)

    def test_p0_sec_002_sanitizes_remote_credentials(self) -> None:
        credential = self._credential()
        remote = (
            f"https://fixture-user:{credential}@github.com/example/lab.git"
            f"?access_token={credential}&safe=value"
        )

        sanitized = sanitize_remote_url(remote)

        self.assertNotIn(credential, sanitized)
        self.assertNotIn("fixture-user", sanitized)
        self.assertNotIn("access_token", sanitized)
        self.assertIn("safe=value", sanitized)

    def test_remote_sanitization_fails_closed_on_invalid_port(self) -> None:
        credential = self._credential()
        remote = (
            f"https://fixture-user:{credential}@github.com:not-a-port/example/lab.git"
            f"?token={credential}"
        )

        sanitized = sanitize_remote_url(remote)

        self.assertNotIn(credential, sanitized)
        self.assertNotIn("fixture-user", sanitized)
        self.assertNotIn("token=", sanitized)

    def test_p0_rep_001_fingerprint_is_reproducible(self) -> None:
        credential = self._credential()
        self._git(
            "remote",
            "add",
            "origin",
            f"https://fixture-user:{credential}@github.com/example/lab.git",
        )

        first = collect_repository_fingerprint(self.repo)
        second = collect_repository_fingerprint(self.repo)

        self.assertEqual(first["stable_fingerprint"], second["stable_fingerprint"])
        self.assertEqual(first["stable"], second["stable"])
        serialized = json.dumps(first, sort_keys=True)
        self.assertNotIn(credential, serialized)

    def test_fingerprint_preserves_git_porcelain_status_columns(self) -> None:
        self._write("README.md", "# Changed fixture repository\n")

        fingerprint = collect_repository_fingerprint(self.repo)
        status = fingerprint["stable"]["repository"]["status"]
        readme = [
            item
            for item in status["entries"]
            if item["path"] == "README.md"
        ]

        self.assertEqual(len(readme), 1)
        self.assertIn(readme[0]["status"], {" M", "M "})
        self.assertEqual(status["tracked_change_count"], 1)
        self.assertEqual(readme[0]["content_identity"]["status"], "hashed")

    def test_fingerprint_changes_when_dirty_file_content_changes(self) -> None:
        self._write("README.md", "# First dirty value\n")
        first = collect_repository_fingerprint(self.repo)

        self._write("README.md", "# Second dirty value\n")
        second = collect_repository_fingerprint(self.repo)

        self.assertNotEqual(first["stable_fingerprint"], second["stable_fingerprint"])

    def test_self_output_does_not_create_recursive_fingerprint_drift(self) -> None:
        output_dir = self.repo / "artifacts/forge/phase-00/book-01-part-01"

        write_part1_artifacts(self.repo, output_dir)
        write_part1_artifacts(self.repo, output_dir)
        second = json.loads(
            (output_dir / "repository-fingerprint.json").read_text(encoding="utf-8")
        )
        write_part1_artifacts(self.repo, output_dir)
        third = json.loads(
            (output_dir / "repository-fingerprint.json").read_text(encoding="utf-8")
        )

        self.assertEqual(second["stable_fingerprint"], third["stable_fingerprint"])
        excluded = [
            item
            for item in third["stable"]["repository"]["status"]["entries"]
            if item["content_identity"]["status"] == "excluded_self_output"
        ]
        self.assertTrue(excluded)

    def test_collection_fails_if_repository_state_changes_mid_scan(self) -> None:
        first = collect_repository_fingerprint(self.repo)
        changed = {**first, "stable_fingerprint": "0" * 64}
        output_dir = Path(self._temporary_directory.name) / "evidence"

        with patch(
            "tools.forge.phase0_inventory.collect_repository_fingerprint",
            side_effect=(first, changed),
        ):
            with self.assertRaisesRegex(
                InventoryError,
                "Repository state changed during Part 1 collection",
            ):
                write_part1_artifacts(self.repo, output_dir)

    def test_p0_cov_001_required_paths_are_present_or_absent(self) -> None:
        inventory = build_core_inventory(self.repo)
        records = {item["path"]: item for item in inventory["components"]}

        self.assertEqual(set(REQUIRED_COMPONENTS), set(records))
        self.assertTrue(records["oce"]["present"])
        self.assertTrue(records["projects/trading/nautilus"]["present"])
        self.assertFalse(records["projects/trading/mt5-mcp"]["present"])
        self.assertFalse(records["QUANT-LAB-INFRA-UPGRADE"]["present"])
        self.assertTrue(all(item["presence"] in {"present", "absent"} for item in records.values()))

    def test_p0_cov_002_every_entrypoint_has_one_component(self) -> None:
        inventory = build_core_inventory(self.repo)
        component_ids = {item["component_id"] for item in inventory["components"]}
        entrypoint_paths = []

        for entrypoint in inventory["entrypoints"]:
            self.assertIn(entrypoint["component_id"], component_ids)
            self.assertTrue(entrypoint["path"])
            entrypoint_paths.append(entrypoint["path"])

        self.assertEqual(len(entrypoint_paths), len(set(entrypoint_paths)))
        self.assertIn("oce/main.py", entrypoint_paths)
        self.assertIn("projects/trading/nautilus/run_backtest.py", entrypoint_paths)

    def test_part_01_artifacts_are_machine_readable_and_bound_to_head(self) -> None:
        output_dir = Path(self._temporary_directory.name) / "evidence"

        result = write_part1_artifacts(self.repo, output_dir)

        self.assertEqual(
            set(result),
            {
                "repository_fingerprint",
                "core_component_inventory",
                "part_evidence",
            },
        )
        for artifact_path in result.values():
            self.assertTrue(artifact_path.is_file())
            json.loads(artifact_path.read_text(encoding="utf-8"))

        evidence = json.loads(result["part_evidence"].read_text(encoding="utf-8"))
        self.assertEqual(evidence["source_head_sha"], self._git("rev-parse", "HEAD"))
        self.assertEqual(evidence["disposition"], "implemented_unverified")


if __name__ == "__main__":
    unittest.main()
