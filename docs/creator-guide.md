# Ren'Py Visual Editor 创作指南

## 发行方式

编辑器只维护一套源码，并从同一个 Git 提交生成两个发行包：

- `windows-x86_64`：Windows 64 位，启动 `renpy.exe`；
- `macos-universal`：同时包含 Apple Silicon 和 Intel 代码，启动 `renpy.app` 或 `renpy.sh`。

两个包使用相同的 Ren'Py `8.5.3.26051504` 核心、项目格式和 `.rpy` 输出。项目目录可以直接在两台电脑之间移动，不需要转换。

当前 alpha 尚未用项目自己的 Apple Developer ID 签名。macOS 首次打开时，先在 Finder 中按住 Control 点击 `renpy.app`，选择“打开”。如果 Gatekeeper 仍提示应用已损坏，可打开终端，进入解压后的目录并运行：

```sh
./renpy.sh
```

经过 Apple Developer ID 签名和公证后，正式版本才可以在新电脑上直接双击且不显示这类安全提示。

## 创建和打开项目

1. 启动 Ren'Py Visual Editor。
2. 在项目中心选择 **Create Visual Project**。
3. 输入项目名并选择保存位置。项目名可以包含中文和内部空格，但不能包含 Windows 非法字符、路径分隔符或设备保留名，也不能以空格或句点结尾。
4. 选中带有 `# visual-editor-project: 1` 标记的项目后，选择 **Visual Editor** 进入工作区。

普通 Ren'Py 项目仍可使用上游启动器功能运行、检查和打包，但只有带标记的项目显示可视化编辑入口。

## 项目目录

```text
game/
├─ story/                  剧情、场景和分支
├─ code/                   gameplay_ 互动模块和扩展代码
└─ assets/
   ├─ backgrounds/         背景
   ├─ characters/          完整角色立绘，可再按角色分目录
   ├─ cg/                  图片 CG 和 WebM 视频
   ├─ bgm/                 BGM 和环境音
   └─ sfx/                 音效
```

编辑器扫描这些文件夹，不复制素材。资源路径相对于 `game` 保存。资源目录和文件名使用小写英文、数字和下划线；文件保留扩展名，例如：

```text
assets/backgrounds/rain_night.png
assets/characters/ann/smile.png
assets/cg/opening.webm
assets/bgm/healing.ogg
assets/sfx/door_close.ogg
```

不要创建只有大小写不同的路径。Windows 不区分这种路径，macOS 项目移动到 Windows 后会发生冲突。

## 工作区

工作区由三部分组成：左侧场景树和资源库，中间舞台与纵向事件列表，右侧 Inspector。事件列表从上到下就是 Ren'Py 的执行顺序。

上方新增按钮包括场景、背景、角色、视频 CG、文本、暂停、选择、互动和代码。选中事件后可以上移、下移或删除。所有这些操作都有可点击按钮，不依赖右键。

保存会直接更新对应的 `game/story/*.rpy`。编辑器拥有的语句由 `visual-editor` 注释包围；编辑器无法安全理解的外部代码显示为只读代码事件，并在再次保存时保持原文。

## 备注

事件、影音附加、互动节点和每个选择选项都可以填写备注。备注保存为紧邻运行语句的结构化注释，进入 Git，但不会显示在游戏中。事件列表中的 `• note` 表示事件或其附加项包含备注。

## 舞台与 Inspector

选择事件或修改内容后，中间舞台会等待约 300 毫秒，然后调用当前项目的 Ren'Py 生成新画面。截图使用项目自己的分辨率、字体、`screen say`、对话框和其他界面定义，因此文字位置和对话框外观与游戏运行时一致。刷新期间显示“正在刷新…”，并继续保留上一张成功画面；如果项目脚本报错，舞台保留旧画面并显示文件、行号和错误信息。

自动舞台预览不会播放声音。视频和过渡只显示截图触发时的稳定单帧。代码、选择和互动事件不会被自动执行；选中这些事件时会显示此前可以安全重建的画面和原因提示，需要完整交互时使用 **Preview**。

背景、角色和视频 CG 支持：

- 拖动主体改变位置；
- 拖动右下缩放手柄，或使用 **Zoom − / Zoom +**；
- 在 Inspector 输入 `xalign`、`yalign`、`zoom` 和 `zorder`；
- 在画面中心或边缘 8 像素范围内自动吸附；
- 按住 Space 拖动舞台背景进行视图平移，选择 **Fit** 恢复视图。

保存的位置使用 0 到 1 的相对坐标，不依赖编辑器窗口像素。缩放保持素材原始宽高比。

## 推进方式

- **Immediate**：立即执行，适合背景、角色、音频和效果。
- **Click**：等待玩家点击，普通台词默认使用。
- **Auto**：文本使用 `{nw}` 后按 Inspector 的秒数执行数值 `pause`。
- **Video**：定位视频按 Inspector 的秒数等待。
- **Choice**：等待玩家选择。
- **Interaction**：等待 `gameplay_` 模块 `return`。

正式运行仍使用 Ren'Py 原生点击推进、自动播放、跳过、回滚、存档和读档。

## 影音附加

在 Inspector 中给事件添加：

- **BGM**：选择 `assets/bgm` 文件，设置循环、淡入、淡出或停止通道；
- **Ambience**：使用独立 `audio` 通道，配置方式同 BGM；
- **SFX**：选择 `assets/sfx` 文件，默认单次播放；
- **Visual**：选择 dissolve、fade、shake、flash、move、zoom、blur 或 filter；
- **Video**：给 WebM 配置恢复原画面、透明结束或保留最后一帧。

编辑器输出标准 Ren'Py `play`、`stop`、`with`、`Movie` 和 ATL 语句。WebM 是项目的视频标准格式。

## 选择分支

添加 **Choice** 后，在右侧填写提示文字。每个选项包含显示文字、目标 label 和备注。可以新增、重命名、重新连接或删除选项。保存时生成标准：

```renpy
menu:
    "去哪？"
    "去甲板":
        jump deck
```

选择 **Check** 会报告空选项和不存在的目标 label。

## 互动模块

技术人员在 `game/code/**/*.rpy` 中编写以 `gameplay_` 开头的 label：

```renpy
label gameplay_search_deck:
    # 互动实现
    return
```

添加 **Interaction** 后，从 Inspector 发现的列表选择入口。编辑器生成 `call gameplay_search_deck`，模块 `return` 后继续下一事件。

需要存档和回滚的状态放在 `default` 声明的 Ren'Py store 值中。模板提供 `gameplay_state`；跨存档和跨周目的解锁内容使用 `persistent`。不要把文件、套接字或原生句柄放入可保存状态。

## 保存、检查和预览

- **Save**：保存 `.rpy`。
- **Undo / Redo**：在当前会话中撤销或重做，最多保留 100 个编辑前状态。
- **Check**：检查资源、路径、标签、分支、玩法入口和只读回退，并合并 Ren'Py lint 的文件与行号。
- **Preview**：先保存，再通过临时入口运行当前场景；游戏退出后删除入口。
- **Refresh**：重新扫描外部修改的脚本、资源和玩法标签。

完整场景预览和自动舞台截图使用的临时文件同时被项目 `.gitignore` 和 Ren'Py 构建规则排除。

## 外部编辑器

选择 **Preferences** 可以填写外部编辑器的可执行文件路径。留空时使用操作系统默认应用。选择 **External** 打开当前场景源文件，保存外部改动后回到编辑器选择 **Refresh**。

## 快捷键

“主修饰键”在 Windows 是 Ctrl，在 macOS 是 Command。

| 操作 | 快捷键 |
|---|---|
| 保存 | 主修饰键 + S |
| 预览当前场景 | 主修饰键 + R |
| 刷新 | 主修饰键 + Shift + R |
| 撤销 | 主修饰键 + Z |
| 重做 | 主修饰键 + Shift + Z |
| 外部打开 | 主修饰键 + E |
| 平移舞台 | Space + 左键拖动 |

资源库、事件列表、Inspector 和检查结果支持鼠标滚轮与触控板双指滚动。

## 本地版本管理

项目内容就是普通文本和素材，可以直接使用 Git：

```sh
git init
git add game .gitignore
git commit -m "story: add chapter 1"
```

提交 `.rpy`、结构化备注、项目内置字体和素材；不要提交存档、日志、编译缓存、`visual_editor_preview.rpy` 或 `visual_editor_stage_render.rpy`。新建项目已将 `game/fonts/source_han_sans_lite.ttf` 设为默认字体，可直接显示中文；替换字体时应同时保留相应许可证文件。
