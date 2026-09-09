# Ren'Py 上游基线

本项目固定使用 Ren'Py 8.5.3，内部构建号为 `8.5.3.26051504`。版本和必需文件记录在根目录的 `renpy-sdk.lock.json`。

Ren'Py SDK 不提交到本仓库。开发者需要单独取得官方 Ren'Py 8.5.3 SDK；组装脚本验证版本后，将 SDK 复制到被 Git 忽略的 `.runtime/renpy-8.5.3-sdk`，再应用 `src/` 中的项目源码覆盖层。源 SDK 始终作为只读输入。

## macOS

当前开发机已确认 SDK 位于 `/Applications/renpy-8.5.3-sdk`：

```sh
python3 scripts/bootstrap_sdk.py --sdk-dir /Applications/renpy-8.5.3-sdk
./.runtime/renpy-8.5.3-sdk/renpy.sh --version
```

不传 `--sdk-dir` 时，脚本先读取 `RENPY_SDK_DIR`，再尝试上述默认路径。

## Windows

在 Windows 中显式指定本机 SDK 目录：

```powershell
py -3 scripts/bootstrap_sdk.py --sdk-dir C:\path\to\renpy-8.5.3-sdk
.runtime\renpy-8.5.3-sdk\renpy.exe --version
```

Windows 和 macOS 使用同一份 `src/`。最终发布物是分别构建的 Windows x86_64 包和 macOS universal 包。

## 复制规则

组装时排除 `tmp`、`cache`、`saves`、`__pycache__`、日志和截图等用户或生成数据。SDK 在 `lib/python3.12` 中自带的 `.pyc` 标准库以及 launcher 的 `.rpyc` 是运行时内容，必须保留。

Ren'Py 及其第三方组件的许可文本来自 SDK 根目录的 `LICENSE.txt`。构建和分发自定义发行版时必须保留适用的版权及许可信息。
