# Complete RenPy Visual Editor Implementation Plan

> 本文档是持续维护的实施计划。任务进度、方案调整与实际验证结果应直接更新到本文档，不以预期结果代替实测结果。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one shared RenPy-based editor codebase and release it as separate Windows and macOS distributions whose launcher creates, opens, visually edits, validates, and runs RenPy visual-novel projects.

**Architecture:** Extend the upstream RenPy launcher, which is itself a RenPy application. Keep a small source overlay in Git and apply it to a generated working copy of an exact RenPy SDK; never edit the installed SDK in place or commit its platform runtimes. Keep every game project as standard `.rpy` plus relative assets; the launcher parses a supported linear subset into an event list, and writes only marked editor-owned blocks. A reusable Python core provides project scanning, resource validation, script parsing, and event-to-script emission; launcher screens present that core as a minimal project hub and visual editor.

**Tech Stack:** RenPy 8.5.3 SDK (`8.5.3.26051504`); RenPy Screen Language and Python; Python `unittest`; RenPy lint and test-case runner; Git.

**Spec:** `docs/superpowers/specs/2026-09-09-renpy-visual-editor-design.md`

## Global Constraints

- Maintain one shared source tree and produce separate Windows and macOS release packages from the same commit.
- Treat the source SDK as read-only; assemble development and release copies under Git-ignored directories.
- Keep platform differences behind narrow adapters for input, paths, file dialogs, external processes, and packaging.
- Use `.rpy` as the only project source; use adjacent structured comments only for editor node IDs and notes.
- Store only relative paths in projects. Use lowercase ASCII file names with digits and underscores for scanned assets.
- Use `game/assets/backgrounds`, `characters`, `cg`, `bgm`, and `sfx` as the resource roots.
- Use WebM for video CG. Do not build a body-part character compositor, Word importer, or built-in code editor.
- Keep the UI functional and minimal: no decorative images, gradients, or nonfunctional animation.
- Every editable scene, event, attachment, choice, and interaction node has a persisted note.
- Never rewrite source the parser does not fully understand; preserve it as a code block with an external-editor action.
- Write tests with `unittest.TestCase`; test snippets below are methods of a test case, and tests needing a temporary path create `self.temp_dir` in `setUp` with `tempfile.TemporaryDirectory`.
- Commands use `python3` on macOS and Linux; use `py -3` for the same commands on Windows.

---

## File Structure

| Path | Responsibility |
|---|---|
| `renpy-sdk.lock.json` | Exact compatible SDK version, build number, and required baseline paths. |
| `scripts/bootstrap_sdk.py` | Validate a source SDK, create an ignored working copy, and apply the source overlay. |
| `.runtime/renpy-8.5.3-sdk/` | Generated local SDK working copy; never committed. |
| `src/launcher/game/visual_editor/core/model.py` | Event, attachment, scene, branch, resource, and validation data types. |
| `src/launcher/game/visual_editor/core/resources.py` | Relative-path asset scanning and portable-name validation. |
| `src/launcher/game/visual_editor/core/rpy_blocks.py` | Marked-block parser and `.rpy` emitter. |
| `src/launcher/game/visual_editor/core/projects.py` | Project template creation, project discovery, and validation orchestration. |
| `src/launcher/game/visual_editor/core/preview.py` | Temporary current-scene launch-script generation. |
| `src/launcher/game/visual_editor/screens/*.rpy` | Project hub, event list, Inspector, canvas, branch view, validation, and preferences screens. |
| `src/launcher/game/visual_editor/actions.rpy` | Screen actions that bind screens to Python core operations. |
| `src/launcher/game/visual_editor/theme.rpy` | Minimal shared styles and cross-platform key bindings. |
| `src/launcher/game/visual_editor/tests/` | Python unit tests and RenPy launcher smoke tests. |
| `src/project_template/` | Files copied into newly created projects, including asset folders and game runtime helpers. |
| `docs/creator-guide.md` | Resource rules, editor workflow, code-module contract, and test workflow. |

## Task 1: Pin and assemble the local RenPy SDK baseline

**Files:**
- Create: `renpy-sdk.lock.json`
- Create: `scripts/bootstrap_sdk.py`
- Create: `tests/test_bootstrap_sdk.py`
- Create: `docs/upstream-renpy.md`
- Modify: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `--sdk-dir` or `RENPY_SDK_DIR` pointing to a RenPy SDK.
- Produces: a validated working copy at `.runtime/renpy-8.5.3-sdk` with the repository's `src/` overlay applied.

- [x] **Step 1: Write failing SDK validation and assembly tests**

Use temporary minimal SDK fixtures. Test rejection of a wrong version or missing launcher file, successful copy of required files, exclusion of `tmp`, logs, screenshots and generated cache directories, preservation of SDK-shipped runtime bytecode, application of the `src/` overlay, and preservation of the source SDK.

- [x] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest tests.test_bootstrap_sdk -v`

Expected: import failure because `scripts/bootstrap_sdk.py` does not exist.

- [x] **Step 3: Implement the SDK lock and bootstrap script**

Lock RenPy `8.5.3.26051504` and require `renpy.py`, `renpy.sh`, `renpy.exe`, `renpy.app`, `launcher/game/project.rpy`, `launcher/game/new_project.rpy`, and `launcher/game/front_page.rpy`. Resolve the SDK from `--sdk-dir`, then `RENPY_SDK_DIR`, then the macOS default `/Applications/renpy-8.5.3-sdk`. Copy it to `.runtime/renpy-8.5.3-sdk` without modifying the source, exclude user data and generated cache directories, then overlay `src/`. Preserve SDK-shipped `.pyc`, `.rpyc`, and `.rpymc` runtime files. Ignore `.runtime/`, `.dist/`, caches, logs, screenshots, and saves without ignoring source `.rpy` files. Document licensing and the requirement that developers obtain RenPy 8.5.3 separately.

- [x] **Step 4: Verify the launcher baseline**

Run: `python3 -m unittest tests.test_bootstrap_sdk -v`

Expected: PASS.

Run: `python3 scripts/bootstrap_sdk.py --sdk-dir /Applications/renpy-8.5.3-sdk`

Expected: the exact version is accepted, required launcher and both platform runtimes exist in the generated working copy, and the installed SDK remains unchanged.

- [x] **Step 5: Commit**

Run: `git add renpy-sdk.lock.json scripts tests docs/upstream-renpy.md README.md .gitignore; git commit -m "chore: assemble pinned RenPy SDK baseline"`

**Actual verification (2026-09-09):** Four bootstrap unit tests passed. The script assembled the local `8.5.3.26051504` SDK with both `py3-mac-universal` and `py3-windows-x86_64` runtimes, source-file hashes remained unchanged, and the generated `renpy.sh --version` command succeeded. An initial real-SDK run exposed that shipped `.pyc` files are runtime dependencies; the copy filter was corrected and covered by a regression assertion before this task was marked complete.

## Task 2: Define the editor domain model and portable resource scanner

**Files:**
- Create: `src/launcher/game/visual_editor/core/model.py`
- Create: `src/launcher/game/visual_editor/core/resources.py`
- Create: `src/launcher/game/visual_editor/tests/test_resources.py`

**Interfaces:**
- Produces: `ResourceKind`, `EventKind`, `AdvanceMode`, `Resource`, `Attachment`, `Event`, `Scene`, and `ValidationIssue` dataclasses; `scan_assets(game_dir: Path) -> list[Resource]`; `validate_portable_name(path: PurePosixPath) -> list[ValidationIssue]`.

- [x] **Step 1: Write failing scanner tests**

```python
def test_scans_allowed_asset_roots(self):
    (self.temp_dir / "assets" / "characters" / "ann").mkdir(parents=True)
    (self.temp_dir / "assets" / "characters" / "ann" / "smile.png").write_bytes(b"png")
    assert [r.relative_path.as_posix() for r in scan_assets(self.temp_dir)] == [
        "assets/characters/ann/smile.png"
    ]

def test_rejects_case_collision_and_windows_invalid_character(self):
    assert any(i.code == "case-collision" for i in validate_resource_paths([
        PurePosixPath("assets/bgm/Rain.ogg"), PurePosixPath("assets/bgm/rain.ogg")
    ]))
    assert any(i.code == "portable-name" for i in validate_portable_name(
        PurePosixPath("assets/bgm/rain:night.ogg")
    ))
```

- [x] **Step 2: Run the scanner tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_resources -v`

Expected: import failure because the core modules do not exist.

- [x] **Step 3: Implement the model and scanner**

Implement string enums for `BACKGROUND`, `CHARACTER`, `CG`, `BGM`, `SFX`, `SCENE`, `TEXT`, and `CONTROL`; scan only the five declared asset roots; normalize every stored path to POSIX form; reject uppercase collisions, empty names, Windows reserved names, and `<>:"/\\|?*`.

- [x] **Step 4: Run the scanner tests to confirm success**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_resources -v`

Expected: PASS.

- [x] **Step 5: Commit**

Run: `git add src/launcher/game/visual_editor; git commit -m "feat: add visual editor resource model"`

**Actual verification (2026-09-09):** Four resource scanner tests passed. They cover declared-root filtering, deterministic ordering, resource-kind mapping, lowercase portable names, Windows reserved names, hidden files, and case-insensitive collisions.

## Task 3: Create projects from the fixed template and open them in the hub

**Files:**
- Create: `src/project_template/game/script.rpy`
- Create: `src/project_template/game/story/01_chapter_01.rpy`
- Create: `src/project_template/game/code/.keep`
- Create: `src/project_template/game/assets/*/.keep`
- Create: `src/launcher/game/visual_editor/core/projects.py`
- Create: `src/launcher/game/visual_editor/entry.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_projects.py`
- Modify: `src/launcher/game/front_page.rpy`

**Interfaces:**
- Consumes: `scan_assets`.
- Produces: `create_project(base_dir: Path, name: str) -> Path`, `is_visual_project(base_dir: Path) -> bool`, and a launcher action that opens the editor workspace.

- [x] **Step 1: Write failing project-template tests**

```python
def test_create_project_creates_required_directories(self):
    project = create_project(self.temp_dir, "salt_lake")
    assert (project / "game" / "story" / "01_chapter_01.rpy").is_file()
    assert (project / "game" / "assets" / "cg").is_dir()
    assert is_visual_project(project)
```

- [x] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_projects -v`

Expected: FAIL because `create_project` is absent.

- [x] **Step 3: Implement creation and hub entry**

Copy the template, reject project names that are not portable between Windows and macOS, create all five asset roots, and include a marker in `game/script.rpy` that identifies the project as editor-managed. Unicode and internal spaces are allowed in project names; the lowercase ASCII rule applies to resource file names. Add “Create Visual Project” and “Visual Editor” actions to the upstream launcher without removing upstream project creation, run, lint, directory, or distribution actions. Until Task 5 replaces it, the editor action opens a minimal workspace placeholder.

- [x] **Step 4: Run tests and launcher smoke check**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_projects -v`

Expected: PASS.

- [x] **Step 5: Commit**

Run: `git add src; git commit -m "feat: create visual editor projects from template"`

**Actual verification (2026-09-09):** Five project tests passed, including Unicode and internal-space names, invalid cross-platform names, marker detection, required folders, and no-overwrite behavior. The assembled RenPy launcher completed lint without visual-editor warnings. A generated project named `示例项目 01` also completed RenPy lint with one dialogue block and no script errors.

## Task 4: Parse and emit editor-owned `.rpy` event blocks

**Files:**
- Create: `src/launcher/game/visual_editor/core/rpy_blocks.py`
- Create: `src/launcher/game/visual_editor/tests/test_rpy_blocks.py`

**Interfaces:**
- Consumes: `Scene`, `Event`, `Attachment`, and `AdvanceMode`.
- Produces: `parse_editor_blocks(text: str) -> list[Scene]`, `emit_scene(scene: Scene) -> str`, `replace_editor_block(text: str, scene: Scene) -> str`.

- [x] **Step 1: Write failing round-trip tests**

```python
def test_event_round_trip_keeps_note_and_click_dialogue(self):
    scene = Scene(label="chapter_01.salt_lake", events=[
        Event(id="n01", kind=EventKind.BACKGROUND, asset="assets/backgrounds/rain.png"),
        Event(id="n02", kind=EventKind.TEXT, text="下雨了。", advance=AdvanceMode.CLICK,
              note="雨声在文本前开始")
    ])
    parsed = parse_editor_blocks(emit_scene(scene))
    assert parsed[0].events[1].note == "雨声在文本前开始"
    assert parsed[0].events[1].advance is AdvanceMode.CLICK

def test_unknown_source_is_a_read_only_code_event(self):
    parsed = parse_editor_blocks("label x:\n    python:\n        dangerous()\n")
    assert parsed[0].events[0].kind is EventKind.CODE
    assert parsed[0].events[0].editable is False
```

- [x] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_rpy_blocks -v`

Expected: FAIL because parser functions are missing.

- [x] **Step 3: Implement marked blocks and safe fallback**

Emit `# visual-editor: begin <node-id>` and `# visual-editor: end <node-id>` around each editor-owned event, plus `# visual-editor-note:` comment lines. Parse only supported `scene`, `show`, `hide`, `play`, dialogue, `pause`, `menu`, `jump`, and `call` forms. Convert every other statement block into a non-editable `CODE` event and preserve its exact text.

- [x] **Step 4: Run parser tests to confirm success**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_rpy_blocks -v`

Expected: PASS.

- [x] **Step 5: Commit**

Run: `git add src/launcher/game/visual_editor; git commit -m "feat: map visual events to RenPy script blocks"`

**Actual verification (2026-09-09):** Seven parser/emitter tests passed. They cover marked-event round trips, notes, click dialogue, character speakers, standard scene/show/hide syntax, supported unmarked statements, preservation of other labels and Python blocks, and safe fallback for dynamic expressions. A generated scene containing a background path, structured note, and Chinese dialogue completed RenPy lint without script errors.

## Task 5: Build the minimal editor workspace and event-list editing actions

**Files:**
- Create: `src/launcher/game/visual_editor/core/editing.py`
- Create: `src/launcher/game/visual_editor/actions.rpy`
- Create: `src/launcher/game/visual_editor/screens/workspace.rpy`
- Create: `src/launcher/game/visual_editor/screens/event_list.rpy`
- Create: `src/launcher/game/visual_editor/theme.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_event_actions.py`

**Interfaces:**
- Consumes: parsed `Scene` objects.
- Produces: `insert_event(scene_id, index, kind)`, `move_event(scene_id, from_index, to_index)`, `delete_event(scene_id, event_id)`, `set_note(event_id, value)`, and `save_project()` actions.

- [x] **Step 1: Write failing action tests**

```python
def test_move_event_preserves_attached_audio(self):
    scene = sample_scene_with_character_and_sound()
    move_event(scene, 0, 1)
    assert scene.events[1].attachments[0].kind == "audio"

def test_delete_event_removes_only_selected_event(self):
    scene = sample_scene_with_two_events()
    delete_event(scene, "first")
    assert [event.id for event in scene.events] == ["second"]
```

- [x] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_event_actions -v`

Expected: FAIL because editing actions do not exist.

- [x] **Step 3: Implement the workspace screens and actions**

Use a three-pane screen: project tree left, vertical event list and stage center, Inspector right. Add toolbar actions for Scene, Background, Character, Video CG, Text, Pause, Choice, Interaction, and Code. Make every row show kind, short content, advance mode, and a note indicator. Use plain panels, text, borders, and functional resource thumbnails only.

- [x] **Step 4: Run action tests and launch the launcher**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_event_actions -v`

Expected: PASS.

- [x] **Step 5: Commit**

Run: `git add src/launcher/game/visual_editor; git commit -m "feat: add visual event-list workspace"`

**Actual verification (2026-09-09):** The action test module first failed because `core/editing.py` did not exist, then all six action and persistence tests passed after implementation. The full test suite through Task 5 passed 26 tests. The reassembled RenPy 8.5.3 launcher completed lint with no visual-editor errors or warnings. The workspace now loads the selected project, shows scenes and events in a three-pane layout, supports insert, reorder, delete, field editing, notes, dirty state, and saves managed blocks while preserving surrounding source.

## Task 6: Add Inspector editing, resources, notes, and direct stage manipulation

**Files:**
- Create: `src/launcher/game/visual_editor/core/transforms.py`
- Create: `src/launcher/game/visual_editor/screens/inspector.rpy`
- Create: `src/launcher/game/visual_editor/screens/resources.rpy`
- Create: `src/launcher/game/visual_editor/screens/stage.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_transforms.py`

**Interfaces:**
- Consumes: selected `Event` and scanned `Resource` values.
- Produces: `assign_resource(event_id, relative_path)`, `set_transform(event_id, xalign, yalign, zoom, zorder)`, and `set_attachment(event_id, attachment)`.

- [x] **Step 1: Write failing transform tests**

```python
def test_drag_result_is_relative_and_not_pixel_based(self):
    transform = canvas_to_transform(x=960, y=540, width=1920, height=1080)
    assert transform.xalign == 0.5
    assert transform.yalign == 0.5

def test_character_assignment_rejects_background_asset(self):
    assert assign_resource_to_kind(EventKind.CHARACTER, "assets/backgrounds/rain.png").code == "kind-mismatch"
```

- [x] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_transforms -v`

Expected: FAIL because transform conversion is absent.

- [x] **Step 3: Implement Inspector, scanning list, and canvas**

Show only resources valid for the selected event kind. For characters, list complete images from the selected character folder. Render selected background, character, video placeholder, and overlay text on the stage. Add selection bounds, drag movement, resize handles, center/edge snapping, and Inspector numeric fields. Persist `xalign`, `yalign`, `zoom`, and `zorder` through the emitter. Provide note editing for every event and attachment.

- [x] **Step 4: Run transform tests to confirm success**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_transforms -v`

Expected: PASS.

- [x] **Step 5: Commit**

Run: `git add src/launcher/game/visual_editor; git commit -m "feat: add stage inspector and resource assignment"`

**Actual verification (2026-09-09):** The transform test module first failed because `core/transforms.py` did not exist, then all seven transform tests passed. Coverage includes pixel-to-relative conversion, center and edge snapping, resource-kind rejection, valid assignment, bounded position and zoom values, attachment replacement, and transform metadata round trips. The full suite through Task 6 passed 33 tests. The reassembled RenPy 8.5.3 launcher completed lint after replacing unsupported `add` fill properties with explicit preview dimensions, with no visual-editor errors or warnings.

## Task 7: Implement visual, audio, video, and advancement attachments

**Files:**
- Create: `src/launcher/game/visual_editor/screens/attachments.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_emission.py`
- Modify: `src/launcher/game/visual_editor/core/rpy_blocks.py`

**Interfaces:**
- Consumes: `Attachment` kinds `visual` and `audio`.
- Produces: emitted `with`, ATL transform, `play music`, `play sound`, `Movie`, and pause statements.

- [x] **Step 1: Write failing emission tests**

```python
def test_emits_music_attachment_with_fade(self):
    text = emit_scene(scene_with_music("assets/bgm/healing.ogg", fadein=1.0))
    assert 'play music "assets/bgm/healing.ogg" fadein 1.0' in text

def test_video_keep_last_frame_emits_non_looping_movie(self):
    text = emit_scene(scene_with_video("assets/cg/ark.webm", keep_last_frame=True))
    assert "keep_last_frame=True" in text
```

- [x] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_emission -v`

Expected: FAIL because attachments are not emitted.

- [x] **Step 3: Implement attachments and advance modes**

Support visual fade, move, zoom, filter, and screen-level flash/shake/blur. Support BGM, ambience, and SFX with loop/stop/fade controls. Support WebM video as full-screen cutscene or positioned displayable, with restore, transparent end, or last-frame behavior. Emit click waits as dialogue or `pause`, timed waits as numeric `pause`, and label explicit modes in the event list.

- [x] **Step 4: Run emission tests to confirm success**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_emission -v`

Expected: PASS.

- [x] **Step 5: Commit**

Run: `git add src/launcher/game/visual_editor; git commit -m "feat: support audiovisual event attachments"`

**Actual verification (2026-09-09):** Six emission tests first failed on absent audio, video, ATL, and timed-advance output, then passed after implementation. Attachments and advance metadata survive parse/emit round trips. The full suite through Task 7 passed 39 tests. Separate RenPy 8.5.3 lint runs passed for the assembled launcher and a generated project containing BGM, SFX, ambience stop, positioned non-looping WebM, no-wait timed text, ATL move, zoom, blur, saturation filter, dissolve, fade, shake, and flash statements.

## Task 8: Implement branches, interactive-module insertion, and native state hooks

**Files:**
- Create: `src/launcher/game/visual_editor/core/branches.py`
- Create: `src/launcher/game/visual_editor/screens/branches.rpy`
- Create: `src/project_template/game/code/runtime_helpers.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_branches.py`
- Modify: `src/launcher/game/visual_editor/core/rpy_blocks.py`

**Interfaces:**
- Produces: `ChoiceOption`, `InteractionTarget`, `emit_menu(event) -> str`, `emit_interaction_call(event) -> str`, and `discover_module_labels(code_dir: Path) -> list[str]`.

- [x] **Step 1: Write failing branch tests**

```python
def test_choice_emits_standard_menu_and_targets(self):
    text = emit_menu(choice_event("去哪？", [("去甲板", "deck"), ("留在原地", "stay")]))
    assert 'menu:' in text and 'jump deck' in text and 'jump stay' in text

def test_interaction_emits_call_and_keeps_note(self):
    text = emit_interaction_call(interaction_event("gameplay_search_deck"))
    assert 'call gameplay_search_deck' in text
```

- [x] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_branches -v`

Expected: FAIL because branch models are absent.

- [x] **Step 3: Implement branch view and module insertion**

Display a compact node graph only for a selected choice event. Create, rename, connect, and delete choices; validate every target. Scan `game/code` for labels prefixed `gameplay_`, offer them in the Interaction Inspector, and emit a native `call`. Keep save/load/rollback native; template helpers document that gameplay state must use serializable RenPy store values and persistent progress uses `persistent`.

- [x] **Step 4: Run branch tests to confirm success**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_branches -v`

Expected: PASS.

- [x] **Step 5: Commit**

Run: `git add src; git commit -m "feat: add choices and interaction insertion"`

**Actual verification (2026-09-09):** The branch test module first failed because `core/branches.py` did not exist, then all five branch tests passed. They cover standard menu targets, interaction calls and notes, stable `gameplay_` discovery, option mutation, and structured choice round trips. The full suite through Task 8 passed 44 tests. RenPy 8.5.3 lint passed for the assembled launcher, the updated project template with native store and persistent helpers, and a generated Chinese menu that jumps to two labels and calls `gameplay_example`.

## Task 9: Add validation, current-scene preview, external editing, and cross-platform controls

**Files:**
- Create: `src/launcher/game/visual_editor/core/preview.py`
- Create: `src/launcher/game/visual_editor/core/validation.py`
- Create: `src/launcher/game/visual_editor/screens/validation.rpy`
- Create: `src/launcher/game/visual_editor/screens/preferences.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_validation.py`
- Create: `src/project_template/game/options.rpy`
- Modify: `src/launcher/game/visual_editor/actions.rpy`
- Modify: `src/launcher/game/visual_editor/core/editing.py`
- Modify: `src/launcher/game/visual_editor/screens/workspace.rpy`
- Modify: `src/launcher/game/visual_editor/theme.rpy`

**Interfaces:**
- Produces: `validate_project(base_dir: Path) -> list[ValidationIssue]`, `create_preview_entry(project: Path, label: str) -> Path`, and `open_external(path: Path) -> None`.

- [x] **Step 1: Write failing validation tests**

```python
def test_validation_reports_missing_resource_and_unresolved_choice(self):
    issues = validate_project(make_project_with_missing_asset_and_target(self.temp_dir))
    assert {issue.code for issue in issues} == {"missing-resource", "missing-target"}

def test_preview_entry_jumps_to_requested_scene(self):
    entry = create_preview_entry(self.temp_dir, "chapter_01.salt_lake")
    assert 'jump chapter_01.salt_lake' in entry.read_text(encoding="utf-8")
```

- [x] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_validation -v`

Expected: FAIL because validation and preview modules are absent.

- [x] **Step 3: Implement validation and controls**

Validate missing assets, portable paths, duplicate labels, empty choices, unresolved targets, missing gameplay labels, parser fallback blocks, and RenPy lint output. Generate a temporary preview entry excluded from normal distribution, run it from the selected label, then remove it after execution. Store external-editor configuration only in launcher preferences. Bind Ctrl on Windows and Command on macOS for Save, Run, Refresh, Undo, Redo, and Open External; bind Space-drag for canvas pan and wheel/touchpad scrolling for lists.

- [x] **Step 4: Run validation tests and lint a sample project**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_validation -v`

Expected: PASS.

- [x] **Step 5: Commit**

Run: `git add src; git commit -m "feat: add validation preview and platform controls"`

**Actual verification (2026-09-09):** The validation tests first failed because preview and validation modules did not exist, then five validation/preview tests and one workspace undo/redo test passed. The full suite through Task 9 passed 50 tests. RenPy 8.5.3 lint passed for the assembled launcher and for the project template while its temporary preview entry was present. The editor now merges its structural checks with RenPy lint locations, previews the selected scene using a temporary warp entry, excludes that entry from distributions and project Git, opens the scene source externally, refreshes external edits, keeps 100 undo checkpoints, and binds Ctrl on Windows plus Command on macOS.

## Task 10: Verify distributions and document the complete workflow

**Files:**
- Create: `docs/creator-guide.md`
- Create: `docs/test-matrix.md`
- Create: `scripts/package_editor.py`
- Create: `tests/test_package_editor.py`
- Modify: `src/launcher/game/options.rpy`
- Modify: `README.md`

**Interfaces:**
- Consumes: the final launcher, project template, core tests, and sample project.
- Produces: Windows/macOS build instructions and a verified creator workflow.

- [x] **Step 1: Write the cross-platform acceptance matrix**

Create `docs/test-matrix.md` with rows for Windows mouse, Windows trackpad, macOS mouse, macOS trackpad, save/load, auto-forward, rollback, video CG, audio fade, choice branch, interaction call, external code refresh, project relocation, and resource case conflict. Each row must list expected behavior and pass/fail status.

- [x] **Step 2: Run all Python tests and RenPy lint**

Run: `python3 -m unittest discover -s src/launcher/game/visual_editor/tests -v`

Expected: PASS.

- [ ] **Step 3: Build Windows and macOS SDK distributions**

From one exact Git commit and the pinned RenPy SDK baseline, create two artifacts: a Windows x86_64 distribution and a macOS universal distribution. Do not maintain platform-specific feature branches. Install each artifact in its target operating system, create the sample project, and execute every applicable row of `docs/test-matrix.md`. A package assembled on macOS is not marked Windows-verified until the Windows rows pass on Windows hardware or a Windows virtual machine.

- [x] **Step 4: Write the creator guide**

Document creating/opening a project, folder-based resource import, event-list authoring, notes, stage drag controls, advancement, video CG, choices, interactive modules, saves, validation, external code editing, and cross-platform filename rules.

- [x] **Step 5: Commit**

Run: `git add docs README.md src/launcher/game/options.rpy; git commit -m "docs: add visual editor creator workflow"`

**Actual verification (2026-09-09):** Five repository tests and 46 editor-core tests passed, and the assembled RenPy 8.5.3 launcher completed lint. Both `0.1.0-alpha.1` archives were generated from one source commit and passed ZIP integrity, target-runtime isolation, manifest, and generated-file exclusion checks. The extracted macOS package reported RenPy `8.5.3.26051504`, completed launcher lint, and contained both arm64 and x86_64 executable slices. The GitHub-downloaded macOS archive matched the published SHA-256 and its terminal entry ran successfully; Gatekeeper blocks direct launch because the alpha lacks the project's own Apple Developer ID signing and notarization, so the creator guide documents the first-launch path. The Windows launcher was confirmed as PE32+ x86-64. Step 3 remains open because Windows startup and the Windows input rows require Windows hardware or a virtual machine; the first public release is therefore a prerelease.

## Task 11: Correct the launcher workspace layout regression

**Files:**
- Create: `src/launcher/game/visual_editor/core/layout.py`
- Create: `tests/test_launcher_layout.py`
- Modify: `src/launcher/game/visual_editor/actions.rpy`
- Modify: `src/launcher/game/visual_editor/entry.rpy`
- Modify: `src/launcher/game/visual_editor/screens/workspace.rpy`
- Modify: `src/launcher/game/visual_editor/screens/inspector.rpy`
- Modify: `src/launcher/game/visual_editor/screens/event_list.rpy`
- Modify: `src/launcher/game/visual_editor/theme.rpy`

- [x] **Step 1: Reproduce the overflow and launcher-overlay defects**

The alpha.1 screenshot shows the center `xfill` child consuming the hbox width and moving Inspector off-canvas. The persistent `bottom_info` screen has zorder 100, above the editor's default zorder, while the inherited `l_root` style retains the upstream launcher's 800 × 600 padding assumptions.

- [x] **Step 2: Add failing geometry and screen-isolation tests**

Assert that left, center, right, padding, and gaps total exactly 1440 pixels; the center retains space for the 640-pixel stage; the workspace is a full-size modal screen above the launcher footer; and the workspace label hides `bottom_info`.

- [x] **Step 3: Implement the layout correction**

Use computed explicit column widths, a full-canvas opaque root style, modal input, zorder 200, and hide the launcher footer while the workspace label is active. Replace unsupported separator glyphs with ASCII so the launcher font does not show missing-character boxes.

- [x] **Step 4: Verify and publish alpha.2**

Run all repository and editor tests, assemble the pinned SDK, run RenPy lint, build both platform archives from the final commit, verify their manifests and architectures, and publish `0.1.0-alpha.2` as a prerelease. Windows UI remains subject to the Windows target rows in the acceptance matrix.

**Actual verification (2026-09-09):** The two new layout regression tests first failed because `core/layout.py` did not exist, then passed after the workspace correction. All seven repository tests and 46 editor-core tests passed, followed by RenPy 8.5.3 launcher lint. Both alpha.2 archives passed integrity, manifest, target-runtime isolation, generated-file exclusion, and architecture checks; the extracted macOS package reported the pinned RenPy build and completed launcher lint. GitHub prerelease `v0.1.0-alpha.2` was published from source commit `d59b45f`.

## Task 12: Repair current-scene preview startup and minimal-project shutdown

**Files:**
- Modify: `src/launcher/game/visual_editor/core/preview.py`
- Modify: `src/launcher/game/visual_editor/tests/test_validation.py`
- Modify: `src/launcher/game/visual_editor/tests/test_projects.py`
- Modify: `src/project_template/game/options.rpy`
- Modify: `src/project_template/.gitignore`
- Create: `src/project_template/game/fonts/source_han_sans_lite.ttf`
- Create: `src/project_template/game/fonts/source_han_sans_lite-OFL.txt`

- [x] **Step 1: Reproduce both runtime failures**

Closing a generated minimal project invoked RenPy's default confirmation action, but the project has no `yesno_prompt` screen. Current-scene preview wrote a dot-prefixed source file, which RenPy ignored while compiling, so `--warp game/.visual_editor_preview.rpy:2` had no matching statement.

- [x] **Step 2: Add focused regression tests**

Assert that generated projects configure an immediate quit action, include their cross-platform CJK font and license, and use a normal compilable preview filename which is excluded from Git and distributions.

- [x] **Step 3: Implement and verify the repair**

Use `Quit(confirm=False)` in the minimal project template, rename the temporary entry to `game/visual_editor_preview.rpy`, and make the bundled Source Han Sans Lite the default style font. Verify the Python regression tests, CJK glyph shaping, RenPy lint, and an actual current-scene launch against the imported intro project.

- [x] **Step 4: Publish alpha.3**

Build both platform archives from the repair commit, verify their manifests and platform runtimes, and publish `0.1.0-alpha.3` as a GitHub prerelease. Windows UI remains subject to the Windows target rows in the acceptance matrix.

**Actual verification (2026-09-09):** The focused tests first failed on the old quit configuration, dot-prefixed preview filename, and absent CJK project font, then passed after the repair. All 47 editor-core tests and seven repository tests passed. HarfBuzz mapped representative intro Chinese text to nonzero glyphs in the bundled font. RenPy 8.5.3 lint completed for the assembled launcher, a freshly generated Chinese project, and the imported 180-dialogue project. A real `--warp game/visual_editor_preview.rpy:2` launch entered the intro and remained running past its first timed pause without a traceback; the font-configured launch also remained running without a runtime error. Both alpha.3 archives contain the font and license and passed ZIP integrity and manifest checks. The extracted macOS package reported the pinned RenPy build, completed launcher lint, and contained arm64 and x86_64 slices; the Windows launcher remained PE32+ x86-64. GitHub prerelease `v0.1.0-alpha.3` was published from source commit `1aa87e4`, and GitHub's recorded SHA-256 digests match the local archives.

## Task 13: Load external project assets in the editor stage

**Files:**
- Modify: `src/launcher/game/visual_editor/actions.rpy`
- Modify: `tests/test_launcher_layout.py`

- [x] **Step 1: Reproduce and test the path failure**

Selecting a real project background showed `Couldn't find file 'Users/.../assets/backgrounds/salt_lake.png'`. The launcher passed an absolute macOS path to RenPy's image loader, which only searches the launcher's own resource roots. Add a regression assertion that external stage images are constructed from file bytes.

- [x] **Step 2: Implement the external image loader**

Read the selected project image as bytes, use its filename only as a format hint, cache the resulting displayable, and clear the cache when a project is opened or refreshed.

- [x] **Step 3: Verify and publish alpha.4**

Run the Python suites and RenPy launcher lint, verify the imported salt-lake background in the actual workspace, then build and publish both platform archives from one commit.

**Actual verification (2026-09-09):** The new stage assertion first failed because the launcher still constructed `im.Image` from the absolute project path, then passed after switching to byte-backed `im.Data`. All 47 editor-core tests and eight repository tests passed, and the assembled launcher completed RenPy 8.5.3 lint. The updated launcher entered the actual `1234` visual-editor workspace without an image-load exception. Both alpha.4 archives passed ZIP, manifest, font, target-runtime, and architecture checks; the extracted macOS package also completed launcher lint. GitHub prerelease `v0.1.0-alpha.4` was published from source commit `8e6cf0f`, with uploaded SHA-256 digests matching the verified local files.

## Exact Automatic Stage Rendering Increment

This increment implements the approved “真实游戏画面自动预览” section in the product specification. It keeps `.rpy` as the project source, renders unsaved in-memory edits through a temporary entry, and uses the project’s own RenPy UI as the visual authority.

### Increment File Structure

| Path | Responsibility |
|---|---|
| `src/launcher/game/visual_editor/core/stage_render.py` | Select safe visual state through the current event and emit the temporary RenPy render entry. |
| `src/launcher/game/visual_editor/core/render_queue.py` | Debounce requests, serialize render jobs, and reject stale results without importing RenPy. |
| `src/launcher/game/visual_editor/core/stage_process.py` | Build the cross-platform RenPy child command, run it with capture environment variables, parse failures, and clean temporary files. |
| `src/launcher/game/visual_editor/actions.rpy` | Submit edits, start the worker thread, and transfer results back to the RenPy main thread. |
| `src/launcher/game/visual_editor/screens/stage.rpy` | Display the exact frame, status, error, black bars, and coordinate-correct editing overlay. |
| `src/launcher/game/visual_editor/core/layout.py` | Calculate aspect-fit frame bounds shared by the screenshot and drag overlay. |
| `src/launcher/game/visual_editor/tests/test_stage_render.py` | Cover scene-prefix reconstruction and temporary capture source. |
| `src/launcher/game/visual_editor/tests/test_render_queue.py` | Cover debounce, serialization, and stale-result rejection. |
| `src/launcher/game/visual_editor/tests/test_stage_process.py` | Cover Windows/macOS commands, result parsing, and cleanup. |
| `tests/test_exact_stage_render.py` | Run RenPy 8.5.3 against a custom dialogue screen and verify the captured PNG. |

### Task 14: Reconstruct a safe frame at the selected event

**Files:**
- Create: `src/launcher/game/visual_editor/core/stage_render.py`
- Create: `src/launcher/game/visual_editor/tests/test_stage_render.py`
- Modify: `src/launcher/game/visual_editor/core/rpy_blocks.py`

**Interfaces:**
- Consumes: `Scene`, `Event`, `EventKind`, `AdvanceMode`, and the existing event emitter.
- Produces: `StageRenderSource(source: str, blocked_reason: Optional[str])`; `build_stage_render_source(scene: Scene, selected_event_id: str) -> StageRenderSource`.

- [x] **Step 1: Write the failing scene-prefix tests**

```python
def test_render_source_keeps_visual_state_and_only_current_dialogue(self):
    scene = Scene("chapter", [
        Event("bg", EventKind.BACKGROUND, asset="assets/backgrounds/room.png"),
        Event("old", EventKind.TEXT, text="旧台词"),
        Event("hero", EventKind.CHARACTER, asset="assets/characters/hero.png"),
        Event("now", EventKind.TEXT, text="当前台词", speaker="e"),
    ])
    result = build_stage_render_source(scene, "now")
    self.assertIn("assets/backgrounds/room.png", result.source)
    self.assertIn("assets/characters/hero.png", result.source)
    self.assertIn('e "当前台词"', result.source)
    self.assertNotIn("旧台词", result.source)

def test_control_or_code_selection_reports_static_render_reason(self):
    scene = Scene("chapter", [Event("custom", EventKind.CODE, text="python:\n    work()")])
    result = build_stage_render_source(scene, "custom")
    self.assertIn("代码", result.blocked_reason)
```

- [x] **Step 2: Run the tests and confirm the missing module failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_stage_render -v`

Expected: FAIL because `core/stage_render.py` does not exist.

- [x] **Step 3: Expose reusable event-body emission**

Add `emit_event_statements(event: Event, *, include_audio: bool = True, include_advance: bool = True) -> list[str]` to `rpy_blocks.py`. Make `emit_scene` call it so normal saves retain current behavior. When either flag is false, omit only the corresponding generated statements and metadata; do not alter the event.

- [x] **Step 4: Implement selected-frame reconstruction**

```python
@dataclass(frozen=True)
class StageRenderSource:
    source: str
    blocked_reason: Optional[str] = None

def build_stage_render_source(scene, selected_event_id):
    selected_index = next(i for i, e in enumerate(scene.events) if e.id == selected_event_id)
    selected = scene.events[selected_index]
    blocked_reason = None
    if selected.kind == EventKind.CODE:
        blocked_reason = "代码事件不能自动执行；显示此前的安全画面。"
    elif selected.choices or selected.interaction:
        blocked_reason = "选择或互动事件需要运行游戏；显示此前的安全画面。"
    lines = ["label visual_editor_stage_render_entry:"]
    for index, event in enumerate(scene.events[: selected_index + 1]):
        if event.kind in (EventKind.BACKGROUND, EventKind.CHARACTER, EventKind.CG):
            lines.extend("    " + line for line in emit_event_statements(
                event, include_audio=False, include_advance=False))
        elif index == selected_index and event.kind == EventKind.TEXT:
            current = copy.deepcopy(event)
            current.advance = AdvanceMode.CLICK
            current.advance_delay = None
            lines.extend("    " + line for line in emit_event_statements(
                current, include_audio=False, include_advance=False))
    if selected.kind != EventKind.TEXT:
        lines.append("    pause")
    return StageRenderSource("\n".join(lines) + "\n", blocked_reason)
```

Treat choices, interactions, and non-editable code as non-executable selections. Preserve the preceding safe visual state and set a Chinese `blocked_reason`; never run their source during automatic rendering.

- [x] **Step 5: Run the focused and emitter suites**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_stage_render src.launcher.game.visual_editor.tests.test_rpy_blocks src.launcher.game.visual_editor.tests.test_emission -v`

Expected: PASS, with normal save emission unchanged.

- [x] **Step 6: Commit the safe frame builder**

```bash
git add -- src/launcher/game/visual_editor/core/stage_render.py src/launcher/game/visual_editor/core/rpy_blocks.py src/launcher/game/visual_editor/tests/test_stage_render.py
git commit -m "feat: build safe stage render frames"
```

**Actual verification (2026-09-09):** The focused test first failed because `core/stage_render.py` was absent. After implementation, 16 safe-frame, parser, and emitter tests passed. Background and character state are retained, earlier dialogue is omitted, and selected code is never emitted.

### Task 15: Capture one frame with the project’s RenPy runtime

**Files:**
- Create: `src/launcher/game/visual_editor/core/stage_process.py`
- Create: `src/launcher/game/visual_editor/tests/test_stage_process.py`
- Modify: `src/project_template/.gitignore`
- Modify: `src/project_template/game/options.rpy`

**Interfaces:**
- Consumes: `StageRenderSource`.
- Produces: `StageRenderPaths(entry_path: Path, output_path: Path, log_path: Path, warp_spec: str)`; `StageRenderResult(image_path: Optional[Path], error: Optional[str], source_path: Optional[PurePosixPath], line: Optional[int])`; `write_stage_render_entry(project_dir: Path, render_source: StageRenderSource, output_path: Path, log_path: Path) -> StageRenderPaths`; `build_stage_render_command(renpy_script: Path, python_executable: Path, project_dir: Path, warp_spec: str) -> list[str]`; `run_stage_render(renpy_script: Path, python_executable: Path, project_dir: Path, paths: StageRenderPaths, timeout_seconds: float = 15.0) -> StageRenderResult`; `cleanup_stage_render(paths: StageRenderPaths) -> None`.

- [x] **Step 1: Write failing capture-source, command, and cleanup tests**

```python
def test_capture_entry_uses_overlay_timer_and_environment_output(self):
    paths = write_stage_render_entry(
        project,
        StageRenderSource('label visual_editor_stage_render_entry:\n    pause\n'),
        output_path,
        log_path,
    )
    text = paths.entry_path.read_text(encoding="utf-8")
    self.assertIn('os.environ["RENPY_VISUAL_EDITOR_STAGE_OUTPUT"]', text)
    self.assertIn("timer 0.15 action Function(_visual_editor_capture_frame)", text)
    self.assertIn("renpy.screenshot(_visual_editor_stage_output)", text)

def test_command_runs_project_at_temporary_entry(self):
    command = build_stage_render_command(Path("renpy.py"), Path("pythonw"), project, "game/visual_editor_stage_render.rpy:20")
    self.assertEqual(command[:3], ["pythonw", "renpy.py", str(project)])
    self.assertEqual(command[3:], ["run", "--warp", "game/visual_editor_stage_render.rpy:20"])
```

- [x] **Step 2: Run the tests and confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_stage_process -v`

Expected: FAIL because `core/stage_process.py` does not exist.

- [x] **Step 3: Write the self-capturing temporary entry**

Prefix the frame source with an early init block and an invisible overlay screen:

```renpy
init -1000 python:
    import os
    _visual_editor_stage_output = os.environ["RENPY_VISUAL_EDITOR_STAGE_OUTPUT"]
    _visual_editor_stage_captured = False
    def _visual_editor_capture_frame():
        global _visual_editor_stage_captured
        if _visual_editor_stage_captured:
            return
        _visual_editor_stage_captured = True
        if not renpy.screenshot(_visual_editor_stage_output):
            raise Exception("Visual editor could not save the stage frame.")
        renpy.quit(status=0)
    config.overlay_screens.append("_visual_editor_stage_capture")

screen _visual_editor_stage_capture():
    timer 0.15 action Function(_visual_editor_capture_frame)
```

Write this plus the generated label to `game/visual_editor_stage_render.rpy`. Return the label’s actual one-based executable line in the warp spec rather than hard-coding it.

- [x] **Step 4: Implement the child process and result contract**

Use the current RenPy script and adjacent `pythonw`/`pythonw.exe` interpreter. Pass `RENPY_VISUAL_EDITOR_STAGE_OUTPUT`, `RENPY_SKIP_SPLASHSCREEN=1`, `SDL_AUDIODRIVER=dummy`, `SDL_VIDEODRIVER=dummy`, and `RENPY_RENDERER=sw`. Capture stdout/stderr, enforce a 15-second timeout, and return:

```python
@dataclass(frozen=True)
class StageRenderResult:
    image_path: Optional[Path]
    error: Optional[str]
    source_path: Optional[PurePosixPath] = None
    line: Optional[int] = None
```

Success requires exit status 0 and a nonempty PNG. On failure, parse the first `File "game/...", line N` location and keep at most the final 20 nonempty log lines in `error`. Always remove the temporary `.rpy` and its `.rpyc`; screenshots live in the launcher’s project temp directory and are replaced atomically.

- [x] **Step 5: Exclude render artifacts**

Add `game/visual_editor_stage_render.rpy` to the template `.gitignore`, and add `build.classify("game/visual_editor_stage_render.rpy", None)` beside the current preview exclusion in template `options.rpy`.

- [x] **Step 6: Run the stage-process and project-template tests**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_stage_process src.launcher.game.visual_editor.tests.test_projects -v`

Expected: PASS on POSIX and simulated Windows command inputs.

- [x] **Step 7: Commit the capture process**

```bash
git add -- src/launcher/game/visual_editor/core/stage_process.py src/launcher/game/visual_editor/tests/test_stage_process.py src/project_template/.gitignore src/project_template/game/options.rpy
git commit -m "feat: capture exact project stage frames"
```

**Actual verification (2026-09-09):** Eleven process and project-template tests passed. A real RenPy `8.5.3.26051504` run with the dummy video/audio drivers created a nonempty 1280 × 720 PNG and removed the temporary source and bytecode.

### Task 16: Debounce automatic renders and reject stale frames

**Files:**
- Create: `src/launcher/game/visual_editor/core/render_queue.py`
- Create: `src/launcher/game/visual_editor/tests/test_render_queue.py`

**Interfaces:**
- Produces: `QueuedStageRender(generation: int, payload: object)` and `StageRenderCoordinator.submit(payload: object, now: float) -> int`, `.claim(now: float) -> Optional[QueuedStageRender]`, `.complete(generation: int) -> bool`, `.has_pending -> bool`, `.active -> bool`.

- [x] **Step 1: Write failing debounce and serialization tests**

```python
def test_submit_debounces_to_latest_payload(self):
    queue = StageRenderCoordinator(debounce_seconds=0.3)
    queue.submit("first", now=0.0)
    latest = queue.submit("second", now=0.2)
    self.assertIsNone(queue.claim(now=0.49))
    self.assertEqual(queue.claim(now=0.5), QueuedStageRender(latest, "second"))

def test_active_job_blocks_second_claim_and_old_result_is_stale(self):
    queue = StageRenderCoordinator(0.3)
    first = queue.submit("first", 0.0)
    self.assertEqual(queue.claim(0.3).generation, first)
    second = queue.submit("second", 0.4)
    self.assertIsNone(queue.claim(0.7))
    self.assertFalse(queue.complete(first))
    self.assertEqual(queue.claim(0.7).generation, second)
```

- [x] **Step 2: Run the tests and confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_render_queue -v`

Expected: FAIL because `core/render_queue.py` does not exist.

- [x] **Step 3: Implement the coordinator with one lock**

Keep `latest_generation`, one pending payload and due time, and one active generation behind `threading.Lock`. `complete` clears the active job and returns true only when its generation is still the newest submission. Do not create threads or import RenPy in this module.

- [x] **Step 4: Run queue tests repeatedly**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_render_queue -v`

Expected: PASS in three consecutive invocations without sleeps or timing-dependent assertions.

- [x] **Step 5: Commit the coordinator**

```bash
git add -- src/launcher/game/visual_editor/core/render_queue.py src/launcher/game/visual_editor/tests/test_render_queue.py
git commit -m "feat: debounce automatic stage rendering"
```

**Actual verification (2026-09-09):** All three coordinator tests passed in three consecutive runs without sleeps. A pending edit replaces the earlier payload, one active render blocks the next claim, and stale completion is rejected.

### Task 17: Connect every selection and edit to the exact Stage frame

**Files:**
- Modify: `src/launcher/game/visual_editor/actions.rpy`
- Modify: `src/launcher/game/visual_editor/screens/stage.rpy`
- Modify: `src/launcher/game/visual_editor/screens/workspace.rpy`
- Modify: `src/launcher/game/visual_editor/theme.rpy`
- Modify: `src/launcher/game/visual_editor/core/layout.py`
- Modify: `tests/test_launcher_layout.py`

**Interfaces:**
- Consumes: `StageRenderCoordinator`, `build_stage_render_source`, and `run_stage_render`.
- Produces: `visual_editor_schedule_stage_render()`, `visual_editor_poll_stage_render()`, `visual_editor_run_stage_render(request)`, `visual_editor_apply_stage_render(generation, result)`, and `aspect_fit_rect(source_width, source_height, target_width, target_height) -> tuple[int, int, int, int]`.

- [x] **Step 1: Write failing Stage-state and geometry assertions**

Assert that the workspace has a repeating 0.1-second render poll, Stage uses the exact-frame displayable when available, status values `waiting`, `rendering`, `ready`, and `error` are visible, the old frame remains under progress/error overlays, and `aspect_fit_rect(1280, 720, 640, 400)` returns `(0, 20, 640, 360)`.

- [x] **Step 2: Run layout tests and confirm failure**

Run: `python3 -m unittest tests.test_launcher_layout -v`

Expected: FAIL on the absent render poll, status UI, and aspect-fit helper.

- [x] **Step 3: Add the launcher render state and worker bridge**

Create one coordinator at launcher init. `visual_editor_schedule_stage_render` deep-copies the selected scene and event ID into a payload, submits it with `time.monotonic()`, sets `waiting`, and restarts interaction. `visual_editor_poll_stage_render` calls `claim`; when it receives a request, set `rendering` and call `renpy.invoke_in_thread(visual_editor_run_stage_render, request)`. The worker writes and runs the temporary entry, then calls `renpy.invoke_in_main_thread(visual_editor_apply_stage_render, generation, result)`.

`visual_editor_apply_stage_render` accepts the PNG only when `coordinator.complete(generation)` is true, reads it through `renpy.display.im.Data`, stores its native dimensions, and sets `ready`. A stale completion leaves the displayed frame unchanged. A current failure sets `error` without clearing the last successful frame.

- [x] **Step 4: Schedule after every user-visible state change**

Call the single scheduling helper after project open/refresh, scene selection, event selection, field/numeric/mapping input, insert/move/delete, resource assignment, drag/resize/zoom, attachment changes, advance changes, choice changes, interaction selection, undo, and redo. Repeated keystrokes remain cheap because only the coordinator’s pending payload changes until the 300-millisecond deadline.

- [x] **Step 5: Replace simulated content with the exact frame**

Use `aspect_fit_rect` to draw the PNG inside Stage with black bars. Remove the duplicated selected asset/text rendering when an exact frame is ready. Keep the existing byte-loaded compositor only as the first-render fallback. Draw a transparent selection rectangle and resize handle over supported visual events using the same fitted rectangle; translate pointer positions from the fitted viewport back to normalized project coordinates.

- [x] **Step 6: Add status and error presentation**

Show a compact `正在刷新…` badge for `waiting` and `rendering`. On `error`, keep the old image and show the parsed message plus source location; on a blocked code/choice/interaction selection, show the safe-render reason without launching project code. Do not open modal dialogs during automatic refresh.

- [x] **Step 7: Run unit and launcher lint checks**

Run: `python3 -m unittest discover -s src/launcher/game/visual_editor/tests -v`

Run: `python3 -m unittest discover -s tests -v`

Run: `python3 scripts/bootstrap_sdk.py --sdk-dir /Applications/renpy-8.5.3-sdk`

Run: `./.runtime/renpy-8.5.3-sdk/renpy.sh .runtime/renpy-8.5.3-sdk/launcher lint /tmp/exact-stage-launcher-lint.txt`

Expected: all Python tests pass and lint contains no visual-editor error.

- [x] **Step 8: Commit the Stage integration**

```bash
git add -- src/launcher/game/visual_editor/actions.rpy src/launcher/game/visual_editor/screens/stage.rpy src/launcher/game/visual_editor/screens/workspace.rpy src/launcher/game/visual_editor/theme.rpy src/launcher/game/visual_editor/core/layout.py tests/test_launcher_layout.py
git commit -m "feat: show exact automatic game previews"
```

**Actual verification (2026-09-09):** All 58 editor-core tests and 11 repository tests passed, including a real RenPy integration capture. The assembled launcher completed lint with no visual-editor error. The actual `123` project opened in the workspace and displayed its generated frame while the child renderer exited without leaving a window.

### Task 18: Prove the exact dialogue frame and publish alpha.5

**Files:**
- Create: `tests/test_exact_stage_render.py`
- Modify: `docs/creator-guide.md`
- Modify: `docs/test-matrix.md`
- Modify: `scripts/package_editor.py`
- Modify: `src/launcher/game/options.rpy`
- Modify: `tests/test_package_editor.py`
- Modify: `docs/superpowers/plans/2026-09-09-complete-renpy-visual-editor.md`

- [x] **Step 1: Create the RenPy integration fixture**

Generate a temporary visual project containing a 1280 × 720 blue background, a custom `screen say(who, what)` with a distinctive red bottom dialogue frame, Chinese text, and one positioned character square. Use `write_stage_render_entry` for the text event and the assembled RenPy 8.5.3 runtime to capture its frame.

- [x] **Step 2: Verify exact rendered pixels and dialogue text presence**

Run: `python3 -m unittest tests.test_exact_stage_render -v`

Expected: PASS only when the output is a 1280 × 720 PNG, a background sample is blue, a dialogue-frame sample is red, and the screenshot differs from a control frame without the `say` screen. This verifies actual project-screen use without brittle OCR.

- [x] **Step 3: Verify the imported project interactively**

Open `/Users/yunhanwei/Desktop/天狼星/123`, select representative intro text, prologue text, salt-lake background, and a character-square event. Confirm each selection automatically reaches `ready`, the Chinese dialogue uses the project font and dialogue UI, visual layers match a normal Preview run, and no child render window remains open.

- [x] **Step 4: Document the workflow and measured limits**

Update the creator guide and test matrix with automatic refresh, the 300-millisecond debounce, the stable-frame treatment for video/transitions, muted audio, blocked code/choice/interaction behavior, last-frame error fallback, and measured macOS render latency. Leave Windows runtime status unverified until a Windows machine runs the corresponding rows.

- [x] **Step 5: Bump and test alpha.5 packaging**

Set `EDITOR_VERSION` and launcher `config.version` to `0.1.0-alpha.5`, update the package assertion, and run both full Python suites again.

- [x] **Step 6: Build and verify both archives**

Build from the exact feature commit. Verify ZIP integrity, `BUILD-INFO.json`, absence of temporary render sources and screenshots, bundled font/license, Windows PE32+ x86-64 launcher, macOS arm64/x86_64 slices, extracted macOS `--version`, and extracted launcher lint.

- [x] **Step 7: Publish the GitHub prerelease**

Publish `v0.1.0-alpha.5` with both archives and release notes describing exact automatic Stage rendering. Confirm GitHub’s asset SHA-256 digests match the local archives and mark alpha.4 as replaced.

- [x] **Step 8: Record actual results and commit documentation**

Mark completed steps only after their checks run, add commands and observed outcomes to this task’s Actual verification paragraph, then commit and push the living plan update.

**Actual verification (2026-09-09):** The integration test first exposed a one-level software-renderer color rounding difference and then passed with a two-level tolerance. The final run passed all 58 editor-core tests and 11 repository tests, including the real 1280 × 720 capture with blue background, green character, Chinese text, and the project-defined red `screen say`. The actual `123` project rendered representative intro text, prologue text, salt-lake background, and character-square frames in 0.710–0.848 seconds after warm-up. Both archives were built from source commit `56a958e`, passed ZIP integrity and generated-artifact exclusion checks, and contained the bundled CJK font and license. The Windows launcher is PE32+ x86-64; the macOS runtime contains x86_64 and arm64 slices, reports RenPy `8.5.3.26051504`, and completed extracted launcher lint. GitHub prerelease `v0.1.0-alpha.5` was published, alpha.4 was marked as replaced, and GitHub’s recorded digests match the local SHA-256 values: macOS `4cd6f93d2024463a4c9c845f80580d4652cc90889e896ab1eb104e10692d2e5d`, Windows `6a5546bfa8fcdaa3164d903b1a40ac0a30e323af21f6c864a5c2f917f4e3cbda`. Windows runtime behavior remains `NOT RUN` pending a Windows machine.

### Task 19: Restore editable inputs and keep Auto text visible

**Files:**
- Modify: `src/launcher/game/visual_editor/actions.rpy`
- Create: `src/launcher/game/visual_editor/screens/input.rpy`
- Modify: `src/launcher/game/visual_editor/screens/inspector.rpy`
- Modify: `src/launcher/game/visual_editor/screens/stage.rpy`
- Modify: `src/launcher/game/visual_editor/screens/attachments.rpy`
- Modify: `src/launcher/game/visual_editor/screens/branches.rpy`
- Modify: `src/launcher/game/visual_editor/screens/preferences.rpy`
- Modify: `src/launcher/game/visual_editor/core/rpy_blocks.py`
- Modify: `src/launcher/game/visual_editor/tests/test_emission.py`
- Modify: `tests/test_launcher_layout.py`
- Modify: product documentation and alpha packaging version

- [x] **Step 1: Reproduce both regressions and add failing checks**

Assert that reusable input values inherit RenPy's equality-aware `FieldInputValue` or `DictInputValue`, every editable input has an explicit mouse `Enable()` action, Stage can focus the selected Text field, and timed Auto text emits `{nw=seconds}` without a following `pause`.

- [x] **Step 2: Make Inspector and Stage text input clickable**

Use stable equality for field, number, mapping, and preference input values. Wrap the visible input in a full-width clickable button. When a Text event is selected, clicking its Stage frame enables the same Text input value. Keep the existing 300-millisecond render scheduling in `set_text`.

- [x] **Step 3: Keep timed Auto dialogue visible**

Generate `{nw=seconds}` on the dialogue itself so RenPy dismisses it only after the configured delay. Continue reading the previous `{nw}` plus numeric `pause` representation, stripping both generated parts from editable text and rewriting it to the new form on save.

- [x] **Step 4: Migrate and run the user's project**

Back up `/Users/yunhanwei/Desktop/天狼星/123/game/story/00_intro.rpy`, migrate all managed Auto events, run RenPy lint, and start the game to observe the dialogue during the configured 2.8-second interval.

- [x] **Step 5: Exercise the fixed editor UI**

Open the actual project in the assembled editor, select a Text event, click the Inspector Text area, replace it with a temporary test value, and verify the Inspector, event row, and Stage all update. Reload the project without saving so the temporary value does not enter the script.

- [x] **Step 5a: Treat typed Speaker text as a display name**

Reproduce the `Sayer '安' is not defined` Stage failure. Add a source-level distinction between imported RenPy speaker expressions and display names typed in Inspector. Emit typed names as `Character("名字")`, preserve imported `e "台词"` expressions, and verify both representations round-trip. Limit the caret to two pixels and keep the focused input background dark.

- [ ] **Step 6: Complete validation and publish alpha.6**

Run both full Python suites and launcher/project lint. Build Windows x86_64 and macOS universal archives from one source commit, verify their manifests and binaries, publish `v0.1.0-alpha.6`, compare GitHub and local SHA-256 digests, mark alpha.5 as replaced, and install the macOS archive in Downloads.

**Actual verification (2026-09-09):** Steps 1–5a are complete. The focused tests passed, launcher lint contained no visual-editor errors, and the actual `123` project linted without errors after 32 Auto events were migrated from `{nw}` plus `pause 2.8` to `{nw=2.8}`. A live run displayed each intro line in its dialogue frame through the configured interval and then entered the prologue. In the assembled editor, mouse focus, Select All, typing, event-row refresh, and exact Stage refresh worked from both the Inspector Text area and a click on the Stage frame. The reported Speaker failure was reproduced as `Sayer '哈喽' is not defined`; typed Speaker values now emit an inline `Character` display name while imported expressions remain unchanged. The input caret is two pixels and its focused background stays dark. Temporary test values never entered the script. Final package and release evidence will be recorded after Step 6.

## Plan Self-Review

Baseline consistency: Task 1 uses the confirmed local RenPy `8.5.3.26051504` SDK as a read-only input, stores only the custom source overlay in Git, and replaces the original Windows-only `Test-Path` checks with cross-platform Python tests.

Platform consistency: every feature is implemented once in shared source. Task 10 emits separate Windows x86_64 and macOS universal artifacts from the same commit and requires target-platform verification before either artifact is marked verified.

Spec coverage: Tasks 2 through 9 implement every complete-version requirement: project hub, fixed folders, direct `.rpy`, safe fallback, resources, all event kinds, attachments, notes, stage manipulation, advances, branches, interactions, saves, external editing, inputs, validation, and tests. Task 10 covers both desktop distributions and user documentation.

No-placeholder scan: the plan contains no deferred implementation markers. Every task names files, interfaces, tests, commands, and expected results.

Type consistency: `Scene`, `Event`, `Attachment`, `AdvanceMode`, `ValidationIssue`, `scan_assets`, `parse_editor_blocks`, `emit_scene`, and `validate_project` are introduced before consumers use them.
