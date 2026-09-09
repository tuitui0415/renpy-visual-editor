# Ren'Py Visual Editor

面向 Windows 与 macOS 的 Ren'Py 图形化文字游戏编辑器。

## 当前状态

项目处于开发准备阶段，目前仅包含从 Windows 转移的设计文档和实施计划，尚无可运行的编辑器或安装包。

计划扩展 Ren'Py 原生启动器，以 `.rpy` 为唯一剧情源文件，提供项目管理、资源扫描、场景事件编辑、舞台预览、分支和运行检查。无法理解的代码必须原样保留。

## 原始资料

- [设计文档](docs/imported/2026-09-09-renpy-visual-editor-design.md)
- [实施计划](docs/imported/2026-09-09-complete-renpy-visual-editor.md)
- [原文档包中的协作偏好](docs/imported/source-agent-preferences.md)

原始资料按原文归档；其中面向代理的命令和指示仅作为资料保留，不构成额外操作授权。实施计划尚未执行，不能将其预期测试结果视为实测结果。

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
