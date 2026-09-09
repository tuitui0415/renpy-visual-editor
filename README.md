# Ren'Py Visual Editor

基于 Ren'Py 源码开发、面向 Windows 与 macOS 的自定义文字游戏编辑器发行版。

## 当前状态

项目处于开发准备阶段，已经建立设计规格、实施计划和协作约束，尚无可运行的编辑器或安装包。

本项目固定使用 Ren'Py 8.5.3，在其源码和原生启动器基础上开发自己的发行版。编辑器以 `.rpy` 为唯一剧情源文件，提供项目管理、资源扫描、场景事件编辑、舞台预览、分支和运行检查。无法理解的代码必须原样保留。

仓库维护一套通用源码，发布时分别生成 Windows 和 macOS 两个安装包。当前开发基线来自本机 `/Applications/renpy-8.5.3-sdk`；原 SDK 保持只读，开发脚本会在仓库的忽略目录中生成工作副本并应用项目源码。

## 项目文档

- [设计规格](docs/superpowers/specs/2026-09-09-renpy-visual-editor-design.md)
- [实施计划](docs/superpowers/plans/2026-09-09-complete-renpy-visual-editor.md)
- [协作约束](AGENTS.md)

这三个 Markdown 文件是持续维护的项目文档。后续实现必须以它们为约束；需求、架构、任务状态或验证结果发生变化时，在同一次提交中直接更新对应文档。实施计划中的预期结果在实际执行前不视为实测结果。

## 建立开发工作副本

本机已安装的 Ren'Py SDK 仅作为只读输入。以下命令验证精确版本，将 SDK 复制到 `.runtime/`，然后应用仓库中 `src/` 的自定义源码：

```sh
python3 scripts/bootstrap_sdk.py --sdk-dir /Applications/renpy-8.5.3-sdk
./.runtime/renpy-8.5.3-sdk/renpy.sh --version
```

Windows 使用 `py -3` 运行同一脚本。详细规则见 [Ren'Py 上游基线](docs/upstream-renpy.md)。

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
