# Complete RenPy Visual Editor Implementation Plan

> 本文档是持续维护的实施计划。任务进度、方案调整与实际验证结果应直接更新到本文档，不以预期结果代替实测结果。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows and macOS custom RenPy distribution whose launcher creates, opens, visually edits, validates, and runs RenPy visual-novel projects.

**Architecture:** Extend the upstream RenPy launcher, which is itself a RenPy application. Keep every game project as standard `.rpy` plus relative assets; the launcher parses a supported linear subset into an event list, and writes only marked editor-owned blocks. A reusable Python core provides project scanning, resource validation, script parsing, and event-to-script emission; launcher screens present that core as a minimal project hub and visual editor.

**Tech Stack:** RenPy 8.5.x source distribution; RenPy Screen Language and Python; Python `unittest`; RenPy lint and test-case runner; Git.

**Spec:** `docs/superpowers/specs/2026-09-09-renpy-visual-editor-design.md`

## Global Constraints

- Target Windows and macOS from one customized RenPy source tree.
- Use `.rpy` as the only project source; use adjacent structured comments only for editor node IDs and notes.
- Store only relative paths in projects. Use lowercase ASCII file names with digits and underscores for scanned assets.
- Use `game/assets/backgrounds`, `characters`, `cg`, `bgm`, and `sfx` as the resource roots.
- Use WebM for video CG. Do not build a body-part character compositor, Word importer, or built-in code editor.
- Keep the UI functional and minimal: no decorative images, gradients, or nonfunctional animation.
- Every editable scene, event, attachment, choice, and interaction node has a persisted note.
- Never rewrite source the parser does not fully understand; preserve it as a code block with an external-editor action.

---

## File Structure

| Path | Responsibility |
|---|---|
| `upstream/` | Pinned upstream RenPy source and launcher baseline. |
| `launcher/game/visual_editor/core/model.py` | Event, attachment, scene, branch, resource, and validation data types. |
| `launcher/game/visual_editor/core/resources.py` | Relative-path asset scanning and portable-name validation. |
| `launcher/game/visual_editor/core/rpy_blocks.py` | Marked-block parser and `.rpy` emitter. |
| `launcher/game/visual_editor/core/projects.py` | Project template creation, project discovery, and validation orchestration. |
| `launcher/game/visual_editor/core/preview.py` | Temporary current-scene launch-script generation. |
| `launcher/game/visual_editor/screens/*.rpy` | Project hub, event list, Inspector, canvas, branch view, validation, and preferences screens. |
| `launcher/game/visual_editor/actions.rpy` | Screen actions that bind screens to Python core operations. |
| `launcher/game/visual_editor/theme.rpy` | Minimal shared styles and cross-platform key bindings. |
| `launcher/game/visual_editor/tests/` | Python unit tests and RenPy launcher smoke tests. |
| `project_template/` | Files copied into newly created projects, including asset folders and game runtime helpers. |
| `docs/creator-guide.md` | Resource rules, editor workflow, code-module contract, and test workflow. |

## Task 1: Vendor and pin the RenPy launcher baseline

**Files:**
- Create: `upstream/README.md`
- Create: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Produces: a checked-out RenPy 8.5.x source tree at `upstream/renpy` and documented build commands.

- [ ] **Step 1: Add a baseline test document**

Create `upstream/README.md` requiring `upstream/renpy/launcher/game/project.rpy`, `new_project.rpy`, and `front_page.rpy` to exist before customization.

- [ ] **Step 2: Verify the baseline check fails before obtaining source**

Run: `Test-Path upstream/renpy/launcher/game/project.rpy`

Expected: `False`.

- [ ] **Step 3: Obtain and pin upstream source**

Clone the official `renpy/renpy` repository into `upstream/renpy`, checkout the chosen 8.5.x tag, and record the tag and commit hash in `upstream/README.md`. Add only generated build artifacts, Python caches, RenPy bytecode, and temporary preview files to `.gitignore`; do not ignore source `.rpy` files.

- [ ] **Step 4: Verify the launcher baseline**

Run: `Test-Path upstream/renpy/launcher/game/project.rpy; Test-Path upstream/renpy/launcher/game/new_project.rpy; Test-Path upstream/renpy/launcher/game/front_page.rpy`

Expected: three `True` values.

- [ ] **Step 5: Commit**

Run: `git add upstream README.md .gitignore; git commit -m "chore: pin RenPy launcher baseline"`

## Task 2: Define the editor domain model and portable resource scanner

**Files:**
- Create: `upstream/renpy/launcher/game/visual_editor/core/model.py`
- Create: `upstream/renpy/launcher/game/visual_editor/core/resources.py`
- Create: `upstream/renpy/launcher/game/visual_editor/tests/test_resources.py`

**Interfaces:**
- Produces: `ResourceKind`, `EventKind`, `AdvanceMode`, `Resource`, `Attachment`, `Event`, `Scene`, and `ValidationIssue` dataclasses; `scan_assets(game_dir: Path) -> list[Resource]`; `validate_portable_name(path: PurePosixPath) -> list[ValidationIssue]`.

- [ ] **Step 1: Write failing scanner tests**

```python
def test_scans_allowed_asset_roots(tmp_path):
    (tmp_path / "assets" / "characters" / "ann").mkdir(parents=True)
    (tmp_path / "assets" / "characters" / "ann" / "smile.png").write_bytes(b"png")
    assert [r.relative_path.as_posix() for r in scan_assets(tmp_path)] == [
        "assets/characters/ann/smile.png"
    ]

def test_rejects_case_collision_and_windows_invalid_character(tmp_path):
    assert any(i.code == "case-collision" for i in validate_resource_paths([
        PurePosixPath("assets/bgm/Rain.ogg"), PurePosixPath("assets/bgm/rain.ogg")
    ]))
    assert any(i.code == "portable-name" for i in validate_portable_name(
        PurePosixPath("assets/bgm/rain:night.ogg")
    ))
```

- [ ] **Step 2: Run the scanner tests to confirm failure**

Run: `python -m unittest launcher.game.visual_editor.tests.test_resources -v`

Expected: import failure because the core modules do not exist.

- [ ] **Step 3: Implement the model and scanner**

Implement string enums for `BACKGROUND`, `CHARACTER`, `CG`, `BGM`, `SFX`, `SCENE`, `TEXT`, and `CONTROL`; scan only the five declared asset roots; normalize every stored path to POSIX form; reject uppercase collisions, empty names, Windows reserved names, and `<>:"/\\|?*`.

- [ ] **Step 4: Run the scanner tests to confirm success**

Run: `python -m unittest launcher.game.visual_editor.tests.test_resources -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add upstream/renpy/launcher/game/visual_editor; git commit -m "feat: add visual editor resource model"`

## Task 3: Create projects from the fixed template and open them in the hub

**Files:**
- Create: `upstream/renpy/project_template/game/script.rpy`
- Create: `upstream/renpy/project_template/game/story/01_chapter_01.rpy`
- Create: `upstream/renpy/project_template/game/code/.keep`
- Create: `upstream/renpy/project_template/game/assets/*/.keep`
- Create: `upstream/renpy/launcher/game/visual_editor/core/projects.py`
- Create: `upstream/renpy/launcher/game/visual_editor/tests/test_projects.py`
- Modify: `upstream/renpy/launcher/game/front_page.rpy`

**Interfaces:**
- Consumes: `scan_assets`.
- Produces: `create_project(base_dir: Path, name: str) -> Path`, `is_visual_project(base_dir: Path) -> bool`, and a launcher action that opens the editor workspace.

- [ ] **Step 1: Write failing project-template tests**

```python
def test_create_project_creates_required_directories(tmp_path):
    project = create_project(tmp_path, "salt_lake")
    assert (project / "game" / "story" / "01_chapter_01.rpy").is_file()
    assert (project / "game" / "assets" / "cg").is_dir()
    assert is_visual_project(project)
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python -m unittest launcher.game.visual_editor.tests.test_projects -v`

Expected: FAIL because `create_project` is absent.

- [ ] **Step 3: Implement creation and hub entry**

Copy the template, reject invalid project names, create all five asset roots, and include a marker in `game/script.rpy` that identifies the project as editor-managed. Add one minimal “Visual Editor” action to the upstream launcher project pane without removing upstream run, lint, directory, or distribution actions.

- [ ] **Step 4: Run tests and launcher smoke check**

Run: `python -m unittest launcher.game.visual_editor.tests.test_projects -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add upstream/renpy; git commit -m "feat: create visual editor projects from template"`

## Task 4: Parse and emit editor-owned `.rpy` event blocks

**Files:**
- Create: `upstream/renpy/launcher/game/visual_editor/core/rpy_blocks.py`
- Create: `upstream/renpy/launcher/game/visual_editor/tests/test_rpy_blocks.py`

**Interfaces:**
- Consumes: `Scene`, `Event`, `Attachment`, and `AdvanceMode`.
- Produces: `parse_editor_blocks(text: str) -> list[Scene]`, `emit_scene(scene: Scene) -> str`, `replace_editor_block(text: str, scene: Scene) -> str`.

- [ ] **Step 1: Write failing round-trip tests**

```python
def test_event_round_trip_keeps_note_and_click_dialogue():
    scene = Scene(label="chapter_01.salt_lake", events=[
        Event(id="n01", kind=EventKind.BACKGROUND, asset="assets/backgrounds/rain.png"),
        Event(id="n02", kind=EventKind.TEXT, text="下雨了。", advance=AdvanceMode.CLICK,
              note="雨声在文本前开始")
    ])
    parsed = parse_editor_blocks(emit_scene(scene))
    assert parsed[0].events[1].note == "雨声在文本前开始"
    assert parsed[0].events[1].advance is AdvanceMode.CLICK

def test_unknown_source_is_a_read_only_code_event():
    parsed = parse_editor_blocks("label x:\n    python:\n        dangerous()\n")
    assert parsed[0].events[0].kind is EventKind.CODE
    assert parsed[0].events[0].editable is False
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python -m unittest launcher.game.visual_editor.tests.test_rpy_blocks -v`

Expected: FAIL because parser functions are missing.

- [ ] **Step 3: Implement marked blocks and safe fallback**

Emit `# visual-editor: begin <node-id>` and `# visual-editor: end <node-id>` around each editor-owned event, plus `# visual-editor-note:` comment lines. Parse only supported `scene`, `show`, `hide`, `play`, dialogue, `pause`, `menu`, `jump`, and `call` forms. Convert every other statement block into a non-editable `CODE` event and preserve its exact text.

- [ ] **Step 4: Run parser tests to confirm success**

Run: `python -m unittest launcher.game.visual_editor.tests.test_rpy_blocks -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add upstream/renpy/launcher/game/visual_editor; git commit -m "feat: map visual events to RenPy script blocks"`

## Task 5: Build the minimal editor workspace and event-list editing actions

**Files:**
- Create: `upstream/renpy/launcher/game/visual_editor/actions.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/screens/workspace.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/screens/event_list.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/theme.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/tests/test_event_actions.py`

**Interfaces:**
- Consumes: parsed `Scene` objects.
- Produces: `insert_event(scene_id, index, kind)`, `move_event(scene_id, from_index, to_index)`, `delete_event(scene_id, event_id)`, `set_note(event_id, value)`, and `save_project()` actions.

- [ ] **Step 1: Write failing action tests**

```python
def test_move_event_preserves_attached_audio():
    scene = sample_scene_with_character_and_sound()
    move_event(scene, 0, 1)
    assert scene.events[1].attachments[0].kind == "audio"

def test_delete_event_removes_only_selected_event():
    scene = sample_scene_with_two_events()
    delete_event(scene, "first")
    assert [event.id for event in scene.events] == ["second"]
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python -m unittest launcher.game.visual_editor.tests.test_event_actions -v`

Expected: FAIL because editing actions do not exist.

- [ ] **Step 3: Implement the workspace screens and actions**

Use a three-pane screen: project tree left, vertical event list and stage center, Inspector right. Add toolbar actions for Scene, Background, Character, Video CG, Text, Pause, Choice, Interaction, and Code. Make every row show kind, short content, advance mode, and a note indicator. Use plain panels, text, borders, and functional resource thumbnails only.

- [ ] **Step 4: Run action tests and launch the launcher**

Run: `python -m unittest launcher.game.visual_editor.tests.test_event_actions -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add upstream/renpy/launcher/game/visual_editor; git commit -m "feat: add visual event-list workspace"`

## Task 6: Add Inspector editing, resources, notes, and direct stage manipulation

**Files:**
- Create: `upstream/renpy/launcher/game/visual_editor/screens/inspector.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/screens/resources.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/screens/stage.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/tests/test_transforms.py`

**Interfaces:**
- Consumes: selected `Event` and scanned `Resource` values.
- Produces: `assign_resource(event_id, relative_path)`, `set_transform(event_id, xalign, yalign, zoom, zorder)`, and `set_attachment(event_id, attachment)`.

- [ ] **Step 1: Write failing transform tests**

```python
def test_drag_result_is_relative_and_not_pixel_based():
    transform = canvas_to_transform(x=960, y=540, width=1920, height=1080)
    assert transform.xalign == 0.5
    assert transform.yalign == 0.5

def test_character_assignment_rejects_background_asset():
    assert assign_resource_to_kind(EventKind.CHARACTER, "assets/backgrounds/rain.png").code == "kind-mismatch"
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python -m unittest launcher.game.visual_editor.tests.test_transforms -v`

Expected: FAIL because transform conversion is absent.

- [ ] **Step 3: Implement Inspector, scanning list, and canvas**

Show only resources valid for the selected event kind. For characters, list complete images from the selected character folder. Render selected background, character, video placeholder, and overlay text on the stage. Add selection bounds, drag movement, resize handles, center/edge snapping, and Inspector numeric fields. Persist `xalign`, `yalign`, `zoom`, and `zorder` through the emitter. Provide note editing for every event and attachment.

- [ ] **Step 4: Run transform tests to confirm success**

Run: `python -m unittest launcher.game.visual_editor.tests.test_transforms -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add upstream/renpy/launcher/game/visual_editor; git commit -m "feat: add stage inspector and resource assignment"`

## Task 7: Implement visual, audio, video, and advancement attachments

**Files:**
- Create: `upstream/renpy/launcher/game/visual_editor/screens/attachments.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/tests/test_emission.py`
- Modify: `upstream/renpy/launcher/game/visual_editor/core/rpy_blocks.py`

**Interfaces:**
- Consumes: `Attachment` kinds `visual` and `audio`.
- Produces: emitted `with`, ATL transform, `play music`, `play sound`, `Movie`, and pause statements.

- [ ] **Step 1: Write failing emission tests**

```python
def test_emits_music_attachment_with_fade():
    text = emit_scene(scene_with_music("assets/bgm/healing.ogg", fadein=1.0))
    assert 'play music "assets/bgm/healing.ogg" fadein 1.0' in text

def test_video_keep_last_frame_emits_non_looping_movie():
    text = emit_scene(scene_with_video("assets/cg/ark.webm", keep_last_frame=True))
    assert "keep_last_frame=True" in text
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python -m unittest launcher.game.visual_editor.tests.test_emission -v`

Expected: FAIL because attachments are not emitted.

- [ ] **Step 3: Implement attachments and advance modes**

Support visual fade, move, zoom, filter, and screen-level flash/shake/blur. Support BGM, ambience, and SFX with loop/stop/fade controls. Support WebM video as full-screen cutscene or positioned displayable, with restore, transparent end, or last-frame behavior. Emit click waits as dialogue or `pause`, timed waits as numeric `pause`, and label explicit modes in the event list.

- [ ] **Step 4: Run emission tests to confirm success**

Run: `python -m unittest launcher.game.visual_editor.tests.test_emission -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add upstream/renpy/launcher/game/visual_editor; git commit -m "feat: support audiovisual event attachments"`

## Task 8: Implement branches, interactive-module insertion, and native state hooks

**Files:**
- Create: `upstream/renpy/launcher/game/visual_editor/screens/branches.rpy`
- Create: `upstream/renpy/project_template/game/code/runtime_helpers.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/tests/test_branches.py`
- Modify: `upstream/renpy/launcher/game/visual_editor/core/rpy_blocks.py`

**Interfaces:**
- Produces: `ChoiceOption`, `InteractionTarget`, `emit_menu(event) -> str`, `emit_interaction_call(event) -> str`, and `discover_module_labels(code_dir: Path) -> list[str]`.

- [ ] **Step 1: Write failing branch tests**

```python
def test_choice_emits_standard_menu_and_targets():
    text = emit_menu(choice_event("去哪？", [("去甲板", "deck"), ("留在原地", "stay")]))
    assert 'menu:' in text and 'jump deck' in text and 'jump stay' in text

def test_interaction_emits_call_and_keeps_note():
    text = emit_interaction_call(interaction_event("gameplay_search_deck"))
    assert 'call gameplay_search_deck' in text
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python -m unittest launcher.game.visual_editor.tests.test_branches -v`

Expected: FAIL because branch models are absent.

- [ ] **Step 3: Implement branch view and module insertion**

Display a compact node graph only for a selected choice event. Create, rename, connect, and delete choices; validate every target. Scan `game/code` for labels prefixed `gameplay_`, offer them in the Interaction Inspector, and emit a native `call`. Keep save/load/rollback native; template helpers document that gameplay state must use serializable RenPy store values and persistent progress uses `persistent`.

- [ ] **Step 4: Run branch tests to confirm success**

Run: `python -m unittest launcher.game.visual_editor.tests.test_branches -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add upstream/renpy; git commit -m "feat: add choices and interaction insertion"`

## Task 9: Add validation, current-scene preview, external editing, and cross-platform controls

**Files:**
- Create: `upstream/renpy/launcher/game/visual_editor/core/preview.py`
- Create: `upstream/renpy/launcher/game/visual_editor/screens/validation.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/screens/preferences.rpy`
- Create: `upstream/renpy/launcher/game/visual_editor/tests/test_validation.py`
- Modify: `upstream/renpy/launcher/game/visual_editor/theme.rpy`

**Interfaces:**
- Produces: `validate_project(base_dir: Path) -> list[ValidationIssue]`, `create_preview_entry(project: Path, label: str) -> Path`, and `open_external(path: Path) -> None`.

- [ ] **Step 1: Write failing validation tests**

```python
def test_validation_reports_missing_resource_and_unresolved_choice(tmp_path):
    issues = validate_project(make_project_with_missing_asset_and_target(tmp_path))
    assert {issue.code for issue in issues} == {"missing-resource", "missing-target"}

def test_preview_entry_jumps_to_requested_scene(tmp_path):
    entry = create_preview_entry(tmp_path, "chapter_01.salt_lake")
    assert 'jump chapter_01.salt_lake' in entry.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python -m unittest launcher.game.visual_editor.tests.test_validation -v`

Expected: FAIL because validation and preview modules are absent.

- [ ] **Step 3: Implement validation and controls**

Validate missing assets, portable paths, duplicate labels, empty choices, unresolved targets, missing gameplay labels, parser fallback blocks, and RenPy lint output. Generate a temporary preview entry excluded from normal distribution, run it from the selected label, then remove it after execution. Store external-editor configuration only in launcher preferences. Bind Ctrl on Windows and Command on macOS for Save, Run, Refresh, Undo, Redo, and Open External; bind Space-drag for canvas pan and wheel/touchpad scrolling for lists.

- [ ] **Step 4: Run validation tests and lint a sample project**

Run: `python -m unittest launcher.game.visual_editor.tests.test_validation -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add upstream/renpy; git commit -m "feat: add validation preview and platform controls"`

## Task 10: Verify distributions and document the complete workflow

**Files:**
- Create: `docs/creator-guide.md`
- Create: `docs/test-matrix.md`
- Modify: `upstream/renpy/launcher/game/options.rpy`
- Modify: `README.md`

**Interfaces:**
- Consumes: the final launcher, project template, core tests, and sample project.
- Produces: Windows/macOS build instructions and a verified creator workflow.

- [ ] **Step 1: Write the cross-platform acceptance matrix**

Create `docs/test-matrix.md` with rows for Windows mouse, Windows trackpad, macOS mouse, macOS trackpad, save/load, auto-forward, rollback, video CG, audio fade, choice branch, interaction call, external code refresh, project relocation, and resource case conflict. Each row must list expected behavior and pass/fail status.

- [ ] **Step 2: Run all Python tests and RenPy lint**

Run: `python -m unittest discover launcher/game/visual_editor/tests -v`

Expected: PASS.

- [ ] **Step 3: Build Windows and macOS SDK distributions**

Use the pinned RenPy build process to build both desktop distributions, install each in its target environment, create the sample project, and execute every row of `docs/test-matrix.md`.

- [ ] **Step 4: Write the creator guide**

Document creating/opening a project, folder-based resource import, event-list authoring, notes, stage drag controls, advancement, video CG, choices, interactive modules, saves, validation, external code editing, and cross-platform filename rules.

- [ ] **Step 5: Commit**

Run: `git add docs README.md upstream/renpy/launcher/game/options.rpy; git commit -m "docs: add visual editor creator workflow"`

## Plan Self-Review

Spec coverage: Tasks 2 through 9 implement every complete-version requirement: project hub, fixed folders, direct `.rpy`, safe fallback, resources, all event kinds, attachments, notes, stage manipulation, advances, branches, interactions, saves, external editing, inputs, validation, and tests. Task 10 covers both desktop distributions and user documentation.

No-placeholder scan: the plan contains no deferred implementation markers. Every task names files, interfaces, tests, commands, and expected results.

Type consistency: `Scene`, `Event`, `Attachment`, `AdvanceMode`, `ValidationIssue`, `scan_assets`, `parse_editor_blocks`, `emit_scene`, and `validate_project` are introduced before consumers use them.
