# Ren'Py Visual Editor

基于 Ren'Py 源码开发、面向 Windows 与 macOS 的自定义文字游戏编辑器发行版。

## 当前状态

项目处于开发准备阶段，已经建立设计规格、实施计划和协作约束，尚无可运行的编辑器或安装包。

本项目将固定一个上游 Ren'Py 版本，在其源码和原生启动器基础上开发自己的发行版。编辑器以 `.rpy` 为唯一剧情源文件，提供项目管理、资源扫描、场景事件编辑、舞台预览、分支和运行检查。无法理解的代码必须原样保留。

## 项目文档

- [设计规格](docs/superpowers/specs/2026-09-09-renpy-visual-editor-design.md)
- [实施计划](docs/superpowers/plans/2026-09-09-complete-renpy-visual-editor.md)
- [协作约束](AGENTS.md)

这三个 Markdown 文件是持续维护的项目文档。后续实现必须以它们为约束；需求、架构、任务状态或验证结果发生变化时，在同一次提交中直接更新对应文档。实施计划中的预期结果在实际执行前不视为实测结果。

## 开发前需要校正

- 将 PowerShell 的 `Test-Path` 替换为跨平台检查。
- 统一仓库根目录与 `upstream/renpy` 下的代码、测试工作目录。
- 计划声明使用 `unittest`，示例却使用 pytest 风格的 `tmp_path`；正式测试需统一。
- 明确上游源码的版本固定和跟踪方式，避免嵌套 Git 仓库导致修改未被本仓库记录。
- 核实并固定 Ren'Py 版本后，再记录构建和运行命令。
- Windows 与 macOS 的实际运行验证需要分别执行。

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
