import io
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CoreTests(unittest.TestCase):
    def run_extract(self, url):
        return subprocess.run(
            ["python3", str(ROOT / "scripts/extract_request.py")],
            env={**os.environ, "INPUT_ROM_URL": url, "GITHUB_EVENT_PATH": ""},
            text=True,
            capture_output=True,
        )

    def test_extract_accepts_tgz_query(self):
        result = self.run_extract("https://example.com/a.tgz?token=x")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_extract_rejects_http(self):
        self.assertNotEqual(self.run_extract("http://example.com/a.tgz").returncode, 0)

    def test_safe_tar_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "bad.tgz"
            with tarfile.open(archive, "w:gz") as handle:
                member = tarfile.TarInfo("../escape")
                payload = b"bad"
                member.size = len(payload)
                handle.addfile(member, io.BytesIO(payload))
            result = subprocess.run(["python3", str(ROOT / "scripts/safe_tar.py"), str(archive)])
            self.assertNotEqual(result.returncode, 0)

    def test_patch_report_accumulates(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            report = base / "report.json"
            env = {**os.environ, "PATCH_FRAMEWORK": "1", "PRIVAPP_MODE": "log"}
            for partition in ("system", "product"):
                extracted = base / partition
                extracted.mkdir()
                (extracted / "build.prop").write_text("ro.control_privapp_permissions=enforce\n")
                subprocess.run([
                    "python3", str(ROOT / "scripts/patch_engine.py"), "--root", str(extracted),
                    "--partition", partition, "--apps", str(ROOT / "assets/apps"),
                    "--plugins", str(ROOT / "plugins/app-patches"), "--report", str(report),
                ], env=env, check=True)
            data = json.loads(report.read_text())
            self.assertEqual([run["partition"] for run in data["runs"]], ["system", "product"])


if __name__ == "__main__":
    unittest.main()
