# 跨平台验收矩阵

状态含义：`PASS` 表示已在目标环境执行；`AUTOMATED PASS` 表示核心或包结构自动验证通过；`NOT RUN` 表示必须在指定硬件或虚拟机继续人工验收。macOS 本机是 Apple Silicon，Windows 目标环境当前不可用，因此不能把包结构检查写成 Windows 实机通过。

| 场景 | 环境与输入 | 预期行为 | 当前状态 |
|---|---|---|---|
| Windows 鼠标 | Windows x86_64，鼠标 | 所有事件、资源、Inspector 和分支操作可通过左键与滚轮完成 | NOT RUN — 需 Windows |
| Windows 触控板 | Windows x86_64，触控板 | 双指滚动列表，Space 加左键平移舞台，不依赖右键 | NOT RUN — 需 Windows |
| macOS 鼠标 | macOS，鼠标 | 按钮、滚轮、拖动、缩放手柄可操作 | PARTIAL PASS — Inspector Text 已实机点击、全选、输入并触发 Stage 刷新；滚轮和手柄仍待完整人工验收 |
| macOS 触控板 | macOS，触控板 | 双指滚动和 Space 平移可操作 | NOT RUN — 需人工 UI 验收 |
| 保存与重新载入 | 两个平台 | 保存直接更新 `.rpy`，重新打开后事件、变换、附加与备注一致 | AUTOMATED PASS — round trip 与持久化测试 |
| 自动推进 | 两个平台 | 文字和对话框按设定秒数保持显示，然后自动继续 | PASS — `{nw=秒数}` 生成与旧格式迁移测试通过；实际 `123` 项目的 2.8 秒引子已运行确认 |
| Speaker 显示名 | 两个平台 | 直接输入“安”等 Unicode 姓名可预览和保存；外部脚本的角色变量保持 | AUTOMATED PASS — `Character("安")` 生成、往返、Stage 源码与原有 `e "台词"` 保留测试 |
| 回滚 | 两个平台 | 普通剧情使用 Ren'Py 原生回滚；互动状态可恢复 | AUTOMATED PASS — 原生 store 模板和编辑器撤销测试；运行时人工验收待执行 |
| 视频 CG | 两个平台 | WebM 非循环播放，按设置恢复、透明结束或保留最后一帧 | AUTOMATED PASS — 生成语法 lint；播放人工验收待执行 |
| 音频淡入淡出 | 两个平台 | BGM、环境音、SFX 输出正确通道、循环、停止和淡入淡出 | AUTOMATED PASS — 生成测试与 lint |
| 选择分支 | 两个平台 | 每个选项跳转到目标 label，缺失目标在检查中报告 | AUTOMATED PASS — 生成、往返与验证测试 |
| 互动调用 | 两个平台 | 只列出 `gameplay_` 标签，`call` 后在模块 `return` 时继续 | AUTOMATED PASS — 发现、生成与 lint |
| 外部代码刷新 | 两个平台 | 外部应用打开当前源文件，刷新后重新解析脚本和资源 | AUTOMATED PASS — 命令选择测试；外部应用人工验收待执行 |
| 项目迁移 | macOS → Windows | 同一项目目录直接打开，路径和结构化数据不转换 | NOT RUN — 需 Windows |
| 资源大小写冲突 | 两个平台 | 检查报告 `case-collision`，不静默覆盖 | AUTOMATED PASS — 路径验证测试 |
| Windows 发行包 | Windows x86_64 | 解压后 `renpy.exe` 启动编辑器并创建、检查、运行项目 | AUTOMATED PASS — 压缩包完整、无其他平台运行时，入口为 PE32+ x86-64；Windows 启动仍为 NOT RUN |
| macOS 发行包 | Apple Silicon 与 Intel | 解压后应用或脚本启动，二进制同时包含 arm64 和 x86_64 | AUTOMATED PASS — 解压后 `renpy.sh --version` 与启动器 lint 通过，应用入口含 arm64/x86_64；Intel 实机仍为 NOT RUN |
| macOS 首次启动 | 从 GitHub 下载的 alpha 包 | Control 点击后允许打开，或从终端运行 `./renpy.sh` | PASS — 下载包校验和正确，隔离标记导致 Gatekeeper 拦截，终端入口成功报告固定 Ren'Py 版本；项目签名与公证待配置 |
| 编辑器三栏布局 | 1440 × 900 虚拟画布，窗口缩放 | 场景/资源、中间舞台/事件和右侧 Inspector 全部位于窗口内，启动器底栏不透出 | AUTOMATED PASS — 列宽总和、全屏模态层和底栏隐藏回归测试；修复前截图已复现溢出 |
| 自动真实舞台预览 | macOS Apple Silicon，Ren'Py 8.5.3 | 选择或修改后自动显示项目分辨率、字体、角色和自定义对话框；旧任务不能覆盖新画面 | PASS — 1280×720 集成截图的蓝色背景、绿色角色和红色自定义 `screen say` 像素均通过；实际 `123` 项目的引子、序章、盐湖背景和角色方块均成功渲染，热启动单帧约 0.7–0.9 秒 |
| 自动真实舞台预览 | Windows x86_64，Ren'Py 8.5.3 | 使用同一源码和 Windows `pythonw.exe` 自动截图，无残留子窗口 | NOT RUN — 命令构造与队列行为自动测试通过，仍需 Windows 实机运行 |

## 自动验证命令

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s src/launcher/game/visual_editor/tests -v
python3 scripts/bootstrap_sdk.py --sdk-dir /Applications/renpy-8.5.3-sdk
./.runtime/renpy-8.5.3-sdk/renpy.sh ./.runtime/renpy-8.5.3-sdk/launcher lint
```

## 目标平台人工验收记录

人工执行时记录操作系统版本、CPU、输入设备、发行文件 SHA-256、结果和问题链接。Windows 行只有在 Windows 真机或虚拟机运行对应发行包后才能改为 `PASS`；macOS Intel 行只有在 Intel 设备或受支持的等价环境执行后才能改为 `PASS`。
