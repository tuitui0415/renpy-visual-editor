import binascii
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from src.launcher.game.visual_editor.core.model import Event, EventKind, Scene
from src.launcher.game.visual_editor.core.stage_process import (
    run_stage_render,
    write_stage_render_entry,
)
from src.launcher.game.visual_editor.core.stage_render import build_stage_render_source


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SDK = PROJECT_ROOT / ".runtime" / "renpy-8.5.3-sdk"


def _png_chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_solid_png(path, width, height, color):
    row = b"\0" + bytes(color) * width
    data = b"\x89PNG\r\n\x1a\n"
    data += _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    data += _png_chunk(b"IDAT", zlib.compress(row * height, 9))
    data += _png_chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def read_png(path):
    data = path.read_bytes()
    position = 8
    compressed = []
    while position < len(data):
        length = struct.unpack(">I", data[position : position + 4])[0]
        kind = data[position + 4 : position + 8]
        payload = data[position + 8 : position + 8 + length]
        position += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            compressed.append(payload)
        elif kind == b"IEND":
            break
    channels = {2: 3, 6: 4}[color_type]
    if depth != 8:
        raise AssertionError("Expected an 8-bit PNG")
    raw = zlib.decompress(b"".join(compressed))
    stride = width * channels
    rows = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        current = bytearray(raw[offset + 1 : offset + 1 + stride])
        offset += stride + 1
        for index in range(stride):
            left = current[index - channels] if index >= channels else 0
            above = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                current[index] = (current[index] + left) & 255
            elif filter_type == 2:
                current[index] = (current[index] + above) & 255
            elif filter_type == 3:
                current[index] = (current[index] + ((left + above) // 2)) & 255
            elif filter_type == 4:
                predictor = left + above - upper_left
                distances = (abs(predictor - left), abs(predictor - above), abs(predictor - upper_left))
                current[index] = (current[index] + (left, above, upper_left)[distances.index(min(distances))]) & 255
            elif filter_type != 0:
                raise AssertionError("Unsupported PNG filter")
        rows.append(bytes(current))
        previous = current
    return width, height, channels, rows


def pixel(image, x, y):
    _, _, channels, rows = image
    offset = x * channels
    return tuple(rows[y][offset : offset + 3])


@unittest.skipUnless((SDK / "renpy.py").is_file(), "assembled Ren'Py SDK is required")
class ExactStageRenderTests(unittest.TestCase):
    def assert_color_close(self, actual, expected, tolerance=2):
        self.assertTrue(
            all(abs(left - right) <= tolerance for left, right in zip(actual, expected)),
            "{} is not within {} of {}".format(actual, tolerance, expected),
        )

    def test_project_say_screen_is_present_in_exact_frame(self):
        with tempfile.TemporaryDirectory(prefix="exact-stage-") as directory:
            root = Path(directory)
            project = root / "project"
            game = project / "game"
            (game / "fonts").mkdir(parents=True)
            shutil.copy2(SDK / "sdk-fonts" / "SourceHanSansLite.ttf", game / "fonts" / "cjk.ttf")
            write_solid_png(game / "assets/backgrounds/blue.png", 1280, 720, (20, 70, 180))
            write_solid_png(game / "assets/characters/square.png", 200, 200, (30, 200, 70))
            (game / "options.rpy").write_text(
                'define config.name = "Exact Stage Fixture"\n'
                "define config.screen_width = 1280\n"
                "define config.screen_height = 720\n"
                "define config.quit_action = Quit(confirm=False)\n"
                "style default:\n"
                '    font "fonts/cjk.ttf"\n',
                encoding="utf-8",
            )
            (game / "screens.rpy").write_text(
                "screen say(who, what):\n"
                "    window:\n"
                '        background Solid("#e02020")\n'
                "        xfill True\n"
                "        ysize 180\n"
                "        yalign 1.0\n"
                "        text what:\n"
                '            id "what"\n'
                "            xpos 48\n"
                "            yalign 0.5\n"
                '            color "#ffffff"\n'
                "            size 38\n",
                encoding="utf-8",
            )
            (game / "script.rpy").write_text("label start:\n    return\n", encoding="utf-8")

            scene = Scene(
                "fixture",
                [
                    Event("bg", EventKind.BACKGROUND, asset="assets/backgrounds/blue.png"),
                    Event(
                        "square",
                        EventKind.CHARACTER,
                        asset="assets/characters/square.png",
                        xalign=0.75,
                        yalign=0.5,
                    ),
                    Event("line", EventKind.TEXT, text="中文对话测试", speaker="安"),
                ],
            )
            pythonw = SDK / "lib/py3-mac-universal/pythonw"
            exact_paths = write_stage_render_entry(
                project,
                build_stage_render_source(scene, "line"),
                root / "exact.png",
                root / "exact.log",
            )
            exact_result = run_stage_render(SDK / "renpy.py", pythonw, project, exact_paths)
            self.assertIsNone(exact_result.error, exact_result.error)

            control_paths = write_stage_render_entry(
                project,
                build_stage_render_source(scene, "square"),
                root / "control.png",
                root / "control.log",
            )
            control_result = run_stage_render(SDK / "renpy.py", pythonw, project, control_paths)
            self.assertIsNone(control_result.error, control_result.error)

            exact = read_png(root / "exact.png")
            control = read_png(root / "control.png")
            self.assertEqual(exact[:2], (1280, 720))
            self.assert_color_close(pixel(exact, 20, 20), (20, 70, 180))
            self.assert_color_close(pixel(exact, 20, 650), (224, 32, 32))
            self.assert_color_close(pixel(exact, 960, 360), (30, 200, 70))
            self.assertFalse(
                all(
                    abs(left - right) <= 2
                    for left, right in zip(pixel(control, 20, 650), (224, 32, 32))
                )
            )
            self.assertNotEqual((root / "exact.png").read_bytes(), (root / "control.png").read_bytes())


if __name__ == "__main__":
    unittest.main()
