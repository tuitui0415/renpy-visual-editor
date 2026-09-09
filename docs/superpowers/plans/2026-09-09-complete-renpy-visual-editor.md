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
- Create: `src/launcher/game/visual_editor/actions.rpy`
- Create: `src/launcher/game/visual_editor/screens/workspace.rpy`
- Create: `src/launcher/game/visual_editor/screens/event_list.rpy`
- Create: `src/launcher/game/visual_editor/theme.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_event_actions.py`

**Interfaces:**
- Consumes: parsed `Scene` objects.
- Produces: `insert_event(scene_id, index, kind)`, `move_event(scene_id, from_index, to_index)`, `delete_event(scene_id, event_id)`, `set_note(event_id, value)`, and `save_project()` actions.

- [ ] **Step 1: Write failing action tests**

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

- [ ] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_event_actions -v`

Expected: FAIL because editing actions do not exist.

- [ ] **Step 3: Implement the workspace screens and actions**

Use a three-pane screen: project tree left, vertical event list and stage center, Inspector right. Add toolbar actions for Scene, Background, Character, Video CG, Text, Pause, Choice, Interaction, and Code. Make every row show kind, short content, advance mode, and a note indicator. Use plain panels, text, borders, and functional resource thumbnails only.

- [ ] **Step 4: Run action tests and launch the launcher**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_event_actions -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/launcher/game/visual_editor; git commit -m "feat: add visual event-list workspace"`

## Task 6: Add Inspector editing, resources, notes, and direct stage manipulation

**Files:**
- Create: `src/launcher/game/visual_editor/screens/inspector.rpy`
- Create: `src/launcher/game/visual_editor/screens/resources.rpy`
- Create: `src/launcher/game/visual_editor/screens/stage.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_transforms.py`

**Interfaces:**
- Consumes: selected `Event` and scanned `Resource` values.
- Produces: `assign_resource(event_id, relative_path)`, `set_transform(event_id, xalign, yalign, zoom, zorder)`, and `set_attachment(event_id, attachment)`.

- [ ] **Step 1: Write failing transform tests**

```python
def test_drag_result_is_relative_and_not_pixel_based(self):
    transform = canvas_to_transform(x=960, y=540, width=1920, height=1080)
    assert transform.xalign == 0.5
    assert transform.yalign == 0.5

def test_character_assignment_rejects_background_asset(self):
    assert assign_resource_to_kind(EventKind.CHARACTER, "assets/backgrounds/rain.png").code == "kind-mismatch"
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_transforms -v`

Expected: FAIL because transform conversion is absent.

- [ ] **Step 3: Implement Inspector, scanning list, and canvas**

Show only resources valid for the selected event kind. For characters, list complete images from the selected character folder. Render selected background, character, video placeholder, and overlay text on the stage. Add selection bounds, drag movement, resize handles, center/edge snapping, and Inspector numeric fields. Persist `xalign`, `yalign`, `zoom`, and `zorder` through the emitter. Provide note editing for every event and attachment.

- [ ] **Step 4: Run transform tests to confirm success**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_transforms -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/launcher/game/visual_editor; git commit -m "feat: add stage inspector and resource assignment"`

## Task 7: Implement visual, audio, video, and advancement attachments

**Files:**
- Create: `src/launcher/game/visual_editor/screens/attachments.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_emission.py`
- Modify: `src/launcher/game/visual_editor/core/rpy_blocks.py`

**Interfaces:**
- Consumes: `Attachment` kinds `visual` and `audio`.
- Produces: emitted `with`, ATL transform, `play music`, `play sound`, `Movie`, and pause statements.

- [ ] **Step 1: Write failing emission tests**

```python
def test_emits_music_attachment_with_fade(self):
    text = emit_scene(scene_with_music("assets/bgm/healing.ogg", fadein=1.0))
    assert 'play music "assets/bgm/healing.ogg" fadein 1.0' in text

def test_video_keep_last_frame_emits_non_looping_movie(self):
    text = emit_scene(scene_with_video("assets/cg/ark.webm", keep_last_frame=True))
    assert "keep_last_frame=True" in text
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_emission -v`

Expected: FAIL because attachments are not emitted.

- [ ] **Step 3: Implement attachments and advance modes**

Support visual fade, move, zoom, filter, and screen-level flash/shake/blur. Support BGM, ambience, and SFX with loop/stop/fade controls. Support WebM video as full-screen cutscene or positioned displayable, with restore, transparent end, or last-frame behavior. Emit click waits as dialogue or `pause`, timed waits as numeric `pause`, and label explicit modes in the event list.

- [ ] **Step 4: Run emission tests to confirm success**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_emission -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/launcher/game/visual_editor; git commit -m "feat: support audiovisual event attachments"`

## Task 8: Implement branches, interactive-module insertion, and native state hooks

**Files:**
- Create: `src/launcher/game/visual_editor/screens/branches.rpy`
- Create: `src/project_template/game/code/runtime_helpers.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_branches.py`
- Modify: `src/launcher/game/visual_editor/core/rpy_blocks.py`

**Interfaces:**
- Produces: `ChoiceOption`, `InteractionTarget`, `emit_menu(event) -> str`, `emit_interaction_call(event) -> str`, and `discover_module_labels(code_dir: Path) -> list[str]`.

- [ ] **Step 1: Write failing branch tests**

```python
def test_choice_emits_standard_menu_and_targets(self):
    text = emit_menu(choice_event("去哪？", [("去甲板", "deck"), ("留在原地", "stay")]))
    assert 'menu:' in text and 'jump deck' in text and 'jump stay' in text

def test_interaction_emits_call_and_keeps_note(self):
    text = emit_interaction_call(interaction_event("gameplay_search_deck"))
    assert 'call gameplay_search_deck' in text
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_branches -v`

Expected: FAIL because branch models are absent.

- [ ] **Step 3: Implement branch view and module insertion**

Display a compact node graph only for a selected choice event. Create, rename, connect, and delete choices; validate every target. Scan `game/code` for labels prefixed `gameplay_`, offer them in the Interaction Inspector, and emit a native `call`. Keep save/load/rollback native; template helpers document that gameplay state must use serializable RenPy store values and persistent progress uses `persistent`.

- [ ] **Step 4: Run branch tests to confirm success**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_branches -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src; git commit -m "feat: add choices and interaction insertion"`

## Task 9: Add validation, current-scene preview, external editing, and cross-platform controls

**Files:**
- Create: `src/launcher/game/visual_editor/core/preview.py`
- Create: `src/launcher/game/visual_editor/screens/validation.rpy`
- Create: `src/launcher/game/visual_editor/screens/preferences.rpy`
- Create: `src/launcher/game/visual_editor/tests/test_validation.py`
- Modify: `src/launcher/game/visual_editor/theme.rpy`

**Interfaces:**
- Produces: `validate_project(base_dir: Path) -> list[ValidationIssue]`, `create_preview_entry(project: Path, label: str) -> Path`, and `open_external(path: Path) -> None`.

- [ ] **Step 1: Write failing validation tests**

```python
def test_validation_reports_missing_resource_and_unresolved_choice(self):
    issues = validate_project(make_project_with_missing_asset_and_target(self.temp_dir))
    assert {issue.code for issue in issues} == {"missing-resource", "missing-target"}

def test_preview_entry_jumps_to_requested_scene(self):
    entry = create_preview_entry(self.temp_dir, "chapter_01.salt_lake")
    assert 'jump chapter_01.salt_lake' in entry.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_validation -v`

Expected: FAIL because validation and preview modules are absent.

- [ ] **Step 3: Implement validation and controls**

Validate missing assets, portable paths, duplicate labels, empty choices, unresolved targets, missing gameplay labels, parser fallback blocks, and RenPy lint output. Generate a temporary preview entry excluded from normal distribution, run it from the selected label, then remove it after execution. Store external-editor configuration only in launcher preferences. Bind Ctrl on Windows and Command on macOS for Save, Run, Refresh, Undo, Redo, and Open External; bind Space-drag for canvas pan and wheel/touchpad scrolling for lists.

- [ ] **Step 4: Run validation tests and lint a sample project**

Run: `python3 -m unittest src.launcher.game.visual_editor.tests.test_validation -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src; git commit -m "feat: add validation preview and platform controls"`

## Task 10: Verify distributions and document the complete workflow

**Files:**
- Create: `docs/creator-guide.md`
- Create: `docs/test-matrix.md`
- Modify: `src/launcher/game/options.rpy`
- Modify: `README.md`

**Interfaces:**
- Consumes: the final launcher, project template, core tests, and sample project.
- Produces: Windows/macOS build instructions and a verified creator workflow.

- [ ] **Step 1: Write the cross-platform acceptance matrix**

Create `docs/test-matrix.md` with rows for Windows mouse, Windows trackpad, macOS mouse, macOS trackpad, save/load, auto-forward, rollback, video CG, audio fade, choice branch, interaction call, external code refresh, project relocation, and resource case conflict. Each row must list expected behavior and pass/fail status.

- [ ] **Step 2: Run all Python tests and RenPy lint**

Run: `python3 -m unittest discover -s src/launcher/game/visual_editor/tests -v`

Expected: PASS.

- [ ] **Step 3: Build Windows and macOS SDK distributions**

From one exact Git commit and the pinned RenPy SDK baseline, create two artifacts: a Windows x86_64 distribution and a macOS universal distribution. Do not maintain platform-specific feature branches. Install each artifact in its target operating system, create the sample project, and execute every applicable row of `docs/test-matrix.md`. A package assembled on macOS is not marked Windows-verified until the Windows rows pass on Windows hardware or a Windows virtual machine.

- [ ] **Step 4: Write the creator guide**

Document creating/opening a project, folder-based resource import, event-list authoring, notes, stage drag controls, advancement, video CG, choices, interactive modules, saves, validation, external code editing, and cross-platform filename rules.

- [ ] **Step 5: Commit**

Run: `git add docs README.md src/launcher/game/options.rpy; git commit -m "docs: add visual editor creator workflow"`

## Plan Self-Review

Baseline consistency: Task 1 uses the confirmed local RenPy `8.5.3.26051504` SDK as a read-only input, stores only the custom source overlay in Git, and replaces the original Windows-only `Test-Path` checks with cross-platform Python tests.

Platform consistency: every feature is implemented once in shared source. Task 10 emits separate Windows x86_64 and macOS universal artifacts from the same commit and requires target-platform verification before either artifact is marked verified.

Spec coverage: Tasks 2 through 9 implement every complete-version requirement: project hub, fixed folders, direct `.rpy`, safe fallback, resources, all event kinds, attachments, notes, stage manipulation, advances, branches, interactions, saves, external editing, inputs, validation, and tests. Task 10 covers both desktop distributions and user documentation.

No-placeholder scan: the plan contains no deferred implementation markers. Every task names files, interfaces, tests, commands, and expected results.

Type consistency: `Scene`, `Event`, `Attachment`, `AdvanceMode`, `ValidationIssue`, `scan_assets`, `parse_editor_blocks`, `emit_scene`, and `validate_project` are introduced before consumers use them.
