import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package_editor import build_archive


class PackageEditorTests(unittest.TestCase):
    def test_platform_archives_share_source_and_keep_only_target_runtime(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            sdk = root / "sdk"
            output = root / "dist"
            for relative in (
                "LICENSE.txt",
                "renpy.py",
                "launcher/game/editor.rpy",
                "renpy/core.py",
                "lib/python3.12/os.pyc",
                "lib/py3-windows-x86_64/renpy.exe",
                "lib/py3-mac-universal/renpy",
                "renpy.exe",
                "renpy.sh",
                "renpy.app/Contents/MacOS/renpy",
            ):
                path = sdk / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(relative.encode("utf-8"))

            windows = build_archive(sdk, output, "windows-x86_64", "abc123")
            macos = build_archive(sdk, output, "macos-universal", "abc123")

            with zipfile.ZipFile(windows) as archive:
                names = archive.namelist()
                manifest = json.loads(archive.read(next(name for name in names if name.endswith("BUILD-INFO.json"))))
                self.assertTrue(any(name.endswith("renpy.exe") for name in names))
                self.assertFalse(any("py3-mac-universal" in name for name in names))
                self.assertEqual(manifest["editor_version"], "0.1.0-alpha.3")
                self.assertEqual(manifest["source_commit"], "abc123")
            with zipfile.ZipFile(macos) as archive:
                names = archive.namelist()
                self.assertTrue(any("renpy.app/Contents/MacOS/renpy" in name for name in names))
                self.assertFalse(any("py3-windows-x86_64" in name for name in names))


if __name__ == "__main__":
    unittest.main()
