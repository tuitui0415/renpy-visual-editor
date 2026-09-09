# Ren'Py Visual Editor

基于 Ren'Py 源码开发、面向 Windows 与 macOS 的自定义文字游戏编辑器发行版。

## 当前状态

第一版完整开发基线已经实现：项目创建、资源扫描、事件列表、舞台与 Inspector、影音附加、选择分支、互动模块、直接 `.rpy` 保存、检查、当前场景预览、撤销重做和跨平台快捷键均已进入功能分支。macOS 可进行本机验证；Windows 包可以从同一提交生成，但仍须在 Windows 真机或虚拟机执行验收矩阵后才能标记为 Windows 已验证。

本项目固定使用 Ren'Py 8.5.3，在其源码和原生启动器基础上开发自己的发行版。编辑器以 `.rpy` 为唯一剧情源文件，提供项目管理、资源扫描、场景事件编辑、舞台预览、分支和运行检查。无法理解的代码必须原样保留。

仓库维护一套通用源码，发布时分别生成 Windows 和 macOS 两个安装包。当前开发基线来自本机 `/Applications/renpy-8.5.3-sdk`；原 SDK 保持只读，开发脚本会在仓库的忽略目录中生成工作副本并应用项目源码。

## 项目文档

- [设计规格](docs/superpowers/specs/2026-09-09-renpy-visual-editor-design.md)
- [实施计划](docs/superpowers/plans/2026-09-09-complete-renpy-visual-editor.md)
- [协作约束](AGENTS.md)
- [创作指南](docs/creator-guide.md)
- [跨平台验收矩阵](docs/test-matrix.md)

这三个 Markdown 文件是持续维护的项目文档。后续实现必须以它们为约束；需求、架构、任务状态或验证结果发生变化时，在同一次提交中直接更新对应文档。实施计划中的预期结果在实际执行前不视为实测结果。

## 建立开发工作副本

本机已安装的 Ren'Py SDK 仅作为只读输入。以下命令验证精确版本，将 SDK 复制到 `.runtime/`，然后应用仓库中 `src/` 的自定义源码：

```sh
python3 scripts/bootstrap_sdk.py --sdk-dir /Applications/renpy-8.5.3-sdk
./.runtime/renpy-8.5.3-sdk/renpy.sh --version
```

Windows 使用 `py -3` 运行同一脚本。详细规则见 [Ren'Py 上游基线](docs/upstream-renpy.md)。

## 测试与发行

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s src/launcher/game/visual_editor/tests -v
python3 scripts/bootstrap_sdk.py --sdk-dir /Applications/renpy-8.5.3-sdk
./.runtime/renpy-8.5.3-sdk/renpy.sh ./.runtime/renpy-8.5.3-sdk/launcher lint
python3 scripts/package_editor.py --commit "$(git rev-parse HEAD)"
```

最后一条命令在 `.dist/` 生成 `windows-x86_64.zip` 与 `macos-universal.zip`。每个包内的 `BUILD-INFO.json` 记录同一个精确 Git 提交和 Ren'Py 构建号。macOS 包包含 arm64 与 x86_64 通用二进制；Windows 包只包含 x86_64 运行时。

当前 alpha 尚未使用项目自己的 Apple Developer ID 签名。macOS 从 GitHub 下载后可能被 Gatekeeper 拦截；首次启动可在 Finder 中按住 Control 点击 `renpy.app` 并选择“打开”。如果系统仍提示应用已损坏，可在终端进入解压目录后运行 `./renpy.sh`。正式无提示分发需要 Apple Developer ID 签名和公证。

## 已知开发事项

- macOS 可在当前设备验证；Windows 发布包仍需在 Windows 真机执行验收矩阵。

## 本地版本管理

`main` 保存稳定里程碑，功能开发使用 `codex/` 前缀分支。每个完成且经过对应验证的改动独立提交。

```sh
git status
git log --oneline
git switch -c codex/project-foundation
git add <本次修改的文件>
git commit -m "feat: describe the change"
git push -u origin HEAD
```

运行缓存、存档、日志、本机配置与密钥不进入仓库。游戏素材及其许可由各游戏项目单独管理。
