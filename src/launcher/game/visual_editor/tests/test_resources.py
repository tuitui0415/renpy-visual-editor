import tempfile
import unittest
from pathlib import Path, PurePosixPath

from src.launcher.game.visual_editor.core.model import ResourceKind
from src.launcher.game.visual_editor.core.resources import (
    scan_assets,
    validate_portable_name,
    validate_resource_paths,
)


class ResourceScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.game_dir = Path(self.temp_directory.name)

    def add_asset(self, relative_path):
        path = self.game_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"asset")

    def test_scans_only_declared_asset_roots_in_stable_order(self):
        self.add_asset("assets/characters/ann/smile.png")
        self.add_asset("assets/backgrounds/rain.png")
        self.add_asset("assets/other/ignored.png")
        self.add_asset("images/ignored.png")
        self.add_asset("assets/cg/.keep")

        resources = scan_assets(self.game_dir)

        self.assertEqual(
            [resource.relative_path.as_posix() for resource in resources],
            [
                "assets/backgrounds/rain.png",
                "assets/characters/ann/smile.png",
            ],
        )

    def test_assigns_resource_kind_from_asset_root(self):
        for relative_path in (
            "assets/backgrounds/room.png",
            "assets/characters/ann/smile.png",
            "assets/cg/opening.webm",
            "assets/bgm/theme.ogg",
            "assets/sfx/door.ogg",
        ):
            self.add_asset(relative_path)

        resources = scan_assets(self.game_dir)

        self.assertEqual(
            {resource.relative_path.as_posix(): resource.kind for resource in resources},
            {
                "assets/backgrounds/room.png": ResourceKind.BACKGROUND,
                "assets/characters/ann/smile.png": ResourceKind.CHARACTER,
                "assets/cg/opening.webm": ResourceKind.CG,
                "assets/bgm/theme.ogg": ResourceKind.BGM,
                "assets/sfx/door.ogg": ResourceKind.SFX,
            },
        )

    def test_rejects_nonportable_and_reserved_path_components(self):
        paths = (
            PurePosixPath("assets/bgm/Rain.ogg"),
            PurePosixPath("assets/bgm/rain:night.ogg"),
            PurePosixPath("assets/sfx/con.ogg"),
        )

        issues = [issue for path in paths for issue in validate_portable_name(path)]

        self.assertEqual([issue.code for issue in issues], ["portable-name"] * 3)

    def test_reports_case_collisions_once(self):
        issues = validate_resource_paths(
            [
                PurePosixPath("assets/bgm/Rain.ogg"),
                PurePosixPath("assets/bgm/rain.ogg"),
                PurePosixPath("assets/sfx/door.ogg"),
            ]
        )

        collisions = [issue for issue in issues if issue.code == "case-collision"]
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0].path, PurePosixPath("assets/bgm/rain.ogg"))


if __name__ == "__main__":
    unittest.main()
