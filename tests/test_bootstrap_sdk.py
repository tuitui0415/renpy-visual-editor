import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_sdk import (
    SdkValidationError,
    assemble_sdk,
    resolve_sdk_dir,
    validate_sdk,
)


EXPECTED_BUILD = "8.5.3.26051504"
REQUIRED_PATHS = (
    "renpy.py",
    "renpy.sh",
    "renpy.exe",
    "renpy.app",
    "renpy/vc_version.py",
    "launcher/game/project.rpy",
    "launcher/game/new_project.rpy",
    "launcher/game/front_page.rpy",
    "lib/py3-mac-universal",
    "lib/py3-windows-x86_64",
)


class BootstrapSdkTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.temp_dir = Path(self.temp_directory.name)
        self.lock = {
            "version": "8.5.3",
            "build": EXPECTED_BUILD,
            "required_paths": list(REQUIRED_PATHS),
        }

    def make_sdk(self, build=EXPECTED_BUILD):
        sdk_dir = self.temp_dir / "source-sdk"
        for relative_path in REQUIRED_PATHS:
            path = sdk_dir / relative_path
            if path.suffix or path.name in {"renpy.py", "renpy.sh", "renpy.exe"}:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("baseline\n", encoding="utf-8")
            else:
                path.mkdir(parents=True, exist_ok=True)

        (sdk_dir / "renpy" / "vc_version.py").write_text(
            f"version = '{build}'\nversion_name = 'We Can Go to the Moon'\n",
            encoding="utf-8",
        )
        return sdk_dir

    def test_validate_sdk_rejects_wrong_build(self):
        sdk_dir = self.make_sdk(build="8.5.2.26010301")

        with self.assertRaisesRegex(SdkValidationError, "8.5.3.26051504"):
            validate_sdk(sdk_dir, self.lock)

    def test_validate_sdk_reports_missing_required_path(self):
        sdk_dir = self.make_sdk()
        (sdk_dir / "launcher" / "game" / "front_page.rpy").unlink()

        with self.assertRaisesRegex(SdkValidationError, "launcher/game/front_page.rpy"):
            validate_sdk(sdk_dir, self.lock)

    def test_assemble_copies_sdk_applies_overlay_and_excludes_generated_data(self):
        sdk_dir = self.make_sdk()
        (sdk_dir / "tmp").mkdir()
        (sdk_dir / "tmp" / "private-project.txt").write_text("private", encoding="utf-8")
        (sdk_dir / "log.txt").write_text("log", encoding="utf-8")
        (sdk_dir / "screenshot0001.png").write_bytes(b"image")
        (sdk_dir / "renpy" / "__pycache__").mkdir()
        (sdk_dir / "renpy" / "__pycache__" / "module.pyc").write_bytes(b"cache")
        runtime_bytecode = sdk_dir / "lib" / "python3.12" / "encodings" / "utf_8.pyc"
        runtime_bytecode.parent.mkdir(parents=True)
        runtime_bytecode.write_bytes(b"runtime")
        (sdk_dir / "launcher" / "game" / "front_page.rpyc").write_bytes(b"compiled launcher")
        (sdk_dir / "launcher" / "game" / "cache").mkdir()
        (sdk_dir / "launcher" / "game" / "cache" / "script.rpyc").write_bytes(b"cache")

        overlay_dir = self.temp_dir / "overlay"
        overlay_file = overlay_dir / "launcher" / "game" / "visual_editor" / "marker.rpy"
        overlay_file.parent.mkdir(parents=True)
        overlay_file.write_text("# visual editor\n", encoding="utf-8")
        destination = self.temp_dir / "working-sdk"

        result = assemble_sdk(sdk_dir, destination, overlay_dir, self.lock)

        self.assertEqual(result, destination)
        self.assertTrue((destination / "launcher" / "game" / "project.rpy").is_file())
        self.assertEqual(
            (destination / "launcher" / "game" / "visual_editor" / "marker.rpy").read_text(encoding="utf-8"),
            "# visual editor\n",
        )
        self.assertFalse((destination / "tmp").exists())
        self.assertFalse((destination / "log.txt").exists())
        self.assertFalse((destination / "screenshot0001.png").exists())
        self.assertFalse((destination / "renpy" / "__pycache__").exists())
        self.assertFalse((destination / "launcher" / "game" / "cache").exists())
        self.assertEqual(
            (destination / "lib" / "python3.12" / "encodings" / "utf_8.pyc").read_bytes(),
            b"runtime",
        )
        self.assertEqual(
            (destination / "launcher" / "game" / "front_page.rpyc").read_bytes(),
            b"compiled launcher",
        )
        self.assertTrue((sdk_dir / "tmp" / "private-project.txt").is_file())

    def test_resolve_sdk_dir_prefers_cli_then_environment_then_default(self):
        cli_path = self.temp_dir / "cli"
        env_path = self.temp_dir / "env"
        default_path = self.temp_dir / "default"

        self.assertEqual(
            resolve_sdk_dir(str(cli_path), {"RENPY_SDK_DIR": str(env_path)}, default_path),
            cli_path,
        )
        self.assertEqual(
            resolve_sdk_dir(None, {"RENPY_SDK_DIR": str(env_path)}, default_path),
            env_path,
        )
        self.assertEqual(resolve_sdk_dir(None, {}, default_path), default_path)


if __name__ == "__main__":
    unittest.main()
