# 通道 B：CDP 接管 Chrome —— 操作手册

> 本文件是 **SKILL.md 的配套操作手册**，只装"怎么做"的细节。
> **规则层**（什么该做、什么绝对不能做）以 `references/rules.md` 的 **A.8 ~ A.13** 为准，本文件不重复规则编号。
> 2026-09-14 从 SKILL.md 拆出（SKILL.md 瘦身：41 KB → 15 KB）。

---

## 0. 两条通道的分工

| 通道 | 能力 | 局限 |
|---|---|---|
| **A. MCP sandbox**（`mcp__tencent-docs__sheet.operation_sheet`） | 读写单元格值、底色、对齐、换行、行高 | **不能隐藏行**；不能判断某行是否被隐藏 |
| **B. CDP 接管 Chrome**（键盘链路，模拟真实用户 UI 操作） | 隐藏行 / 取消隐藏 / 选中整行 / 判断隐藏状态 | 需要一个带调试端口的 Chrome（`_hold.py` 常驻） |

**结论：写数据用 A，隐藏行用 B（B 走键盘链路，不走右键菜单）。**

---

## 1. 环境与前置条件

```
Python: %USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\python.exe
        （系统 python 没有 websocket 模块，必须用这个 venv）
依赖:   websocket-client；拼图/裁图需要 Pillow（已装，12.3.0）
连接:   websocket.create_connection(ws_url, timeout=120, suppress_origin=True, origin=None)  # 否则 403
代理:   企业代理会吞掉 127.0.0.1 → 必须设 no_proxy=127.0.0.1,localhost（_boot.py 已固化）
```

**操作脚本不要自己启动 Chrome**，统一 `from _boot import connect` —— `_boot.connect()` 会连现有实例，
连不上才自己拉。`cdp.py` 在 **import 时**读 `CDP_PORT`，所以必须在 `import cdp` **之前**设好环境变量。

### Chrome 常驻（用户要求，2026-09-11 起）

> 用户明确要求：**单独打开的 Chrome 要持续展示、不要关闭**，方便随时查看进度。

WorkBuddy 沙箱会在 shell 命令返回时回收子进程，所以 Chrome 必须由一个**后台常驻进程**持有：

```bash
python scripts/_hold.py      # 用 run_in_background 启动，不要前台跑
```

`_hold.py` 每 5 秒探活，端口死了自动重新拉起 Chrome（调试端口默认 `9223`，
独立 profile 在 `~/.workbuddy/chrome-debug`，不污染用户日常浏览器）。

### ⚠️ 在"新机器"上首次使用：必须先登录一次（2026-09-14 家里电脑实测）

调试 profile 是**全新的**，与用户日常浏览器不共享 Cookie → 第一次打开表格会看到：

> 🔒 **此文档已设置权限，请登录后使用。**（页面只有一个「立即登录」按钮）

此时**任何 CDP 键盘操作都会作用在一个错误页面上**（键盘链路全部失效，且可能误触）。
所以流程是：

1. `python scripts/_launch_chrome.py` 启动，或直接 `_hold.py`
2. `_boot.connect()` 后先 `snap(c, "login_check.png")` **截图确认页面状态**
   —— 标题是 `孟总会议行程表` **不代表已登录**，权限墙页面标题同样是这个
3. 若看到权限墙 → **请用户在那个 Chrome 窗口里点「立即登录」扫码**（微信/QQ），
   **登录态会持久化在这个 profile 里，只需一次**
4. 用户确认已登录后，再跑 `_j_do.py` 等键盘任务

---

## 2. 通道 A：sandbox 用法（写数据）

```javascript
// 必须用 console.log 输出，且不支持顶层 return
var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('时间表');
var out = [];
for (var r = 41; r <= 62; r++) {
  var b = String(sh.getRange(r, 2).getValue());
  var c = String(sh.getRange(r, 3).getValue());
  var h = sh.getRowHeight(r);
  out.push(r + '|B=' + b + '|C=' + c + '|h=' + h);
}
console.log(out.join('\n'));   // 分批 20 行左右，过长会被截断
```

可用方法：`getValue` / `setValue` / `getBackground` / `setBackground` / `getRowHeight` /
`setRowHeightsForced` / `setHorizontalAlignment` / `setWrapText`

**关键认知**

- `setRowHeightsForced(r, 1, 60)` 实际可能只落到 45，无法把已被改小的行恢复成原值
- `getRowHeight` 返回的是**行高设置值**；**行被隐藏时该值不变**（仍是 60）→ **沙箱无法判断隐藏状态**
- **禁止**用 `setRowHeightsForced(r,1,1)` 模拟隐藏：它是"改高度"而非"隐藏"，
  用户无法用取消隐藏恢复，会永久污染表格
- `getBackground()` 在沙箱里**返回值不可信**（常全返回 `#000000`）；
  `getFontWeight` / `getHorizontalAlignment` / `getWrap` 直接 `not a function`
  → **要校验样式就去截图做像素测量**（用 `_pix.py`），不要信沙箱

---

## 3. 通道 B：坐标与定位

**先记住这几条基本事实**

- 网格和行号列都是 `<canvas>`；**右键菜单是 DOM**（`div.dui-menu.context-menu_contextmenu__*`）
- 菜单项的**可见文字不在 textContent 里**，只有右侧快捷键提示在：
  `Ctrl+Alt+9` = 隐藏行，`Alt+Shift+9` = 取消隐藏行 → 用快捷键文本定位菜单项
- 「取消隐藏行」只有在**选中整行范围且跨越隐藏行**时才出现
- 读活动单元格用 `document.querySelector('.bar-label').value`（返回如 `A40`）；
  **名称框不随 `Shift+↓` 更新**，不能当校验信号
- 扫行号列时点击 y **避开视口最上/最下 60px**，否则会触发自动滚动、扫描数据错乱

**坐标要点**（视口约 1092x711，100% 缩放）

- 名称框：`(30, 111)`
- **行号列 x ≈ 28**（x=40 会落到单元格区，无法选中整行）
- 行号 y ≈ 该行视觉中心；行高 60pt 时步进约 47px
- 选中整行成功的标志：行号变深灰 + 整行浅蓝 + 底部显示"计数:N"

**可靠定位手法**

- `Ctrl+Home` 回顶部（需先点击网格区域获得焦点）
- 按 N 次 `PageDown` 逐屏滚动，**每次截图确认**（滚动步长因行高不同而非线性）
- 名称框可输入并跳转单元格（如 `A48`），但**不能用它选行区间**（输入 `2:60` 会被解析成 `A2`）

**无效操作（不要浪费时间）**

- 鼠标 wheel 事件 —— **不是无效，是会阻塞 40 秒直到超时**（表格主体是 canvas，
  没有 DOM 滚动容器，wheel 事件永远等不到 ack）。这是历史上一系列"操作龟速"的真凶。
- `Ctrl+A`（只选单元格区域，不是整行；且紧跟 Delete 会清全表，见 SKILL.md 安全红线）
- `Shift+PageDown` / `Ctrl+Shift+Down` / `Ctrl+Shift+End` 扩展整行选择
- `Ctrl+Shift+9`（这不是隐藏行快捷键）
- 名称框输入行区间（如 `2:60`、`A30:A39`）—— 只会回显 `A2`/`A30`，**不提交选区**

---

## 4. 键盘链路（首选路径，2026-09-14 打通）

**这是目前操作本表最快、最可靠的方式，隐藏/展开一律走这里，不要走右键菜单。**

### 4.1 为什么改用键盘：性能实测

| 事件类型 | 单次耗时 | 备注 |
|---|---|---|
| `Input.dispatchMouseEvent` | **~1.7 秒** | 每次都要等浏览器重绘才 ack |
| `Input.dispatchMouseEvent` (mouseWheel) | **40 秒 → 超时** | canvas 无滚动容器，永不 ack |
| `Input.dispatchKeyEvent` | **~30 毫秒** | 快 50 倍以上 |

结论：**能走键盘就一定走键盘**。一次"展开 60 行"的操作，右键菜单路径要几分钟，键盘路径只要几秒。

### 4.2 关键前提：必须用 `rawKeyDown`

`Input.dispatchKeyEvent` 的 `type` 字段必须填 **`rawKeyDown`**（不是 `keyDown`）。
这正是历史上误判"canvas 收不到键盘事件"的原因。

```python
def kd(c, key, code, vk, mods):
    c.send("Input.dispatchKeyEvent", type="rawKeyDown", key=key, code=code,
           windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk, modifiers=mods)
# 修饰键: Shift=8, Ctrl=2, Alt=1, 可相加
```

### 4.3 快捷键链路（全部实测可用）

| 按键 | 作用 |
|---|---|
| `Ctrl+Home` | 活动单元格回到 `A2`（第 1 行是冻结表头，所以是 A2 不是 A1） |
| `ArrowDown` | 移到**下一个可见行**——**自动跳过隐藏行**，这是全链路的基石 |
| `Shift+Space` | 选中活动单元格所在的**整行** |
| `Shift+ArrowDown` | 向下扩展行选区（按住 Shift 连发 ArrowDown，不要每次重按修饰键） |
| `Ctrl+Alt+9` | 隐藏选中行 |
| `Alt+Shift+9` | 取消隐藏选中行 |

### 4.4 由此衍生的两个能力

**1. 判断隐藏行（权威，无需截图）**

反复按 `ArrowDown` 枚举可见行序列，**缺口即隐藏区间**：

```python
vis = visible_rows(c, upto=70)          # 如 [2,5,6,7,8,9,13,...]
hidden = [r for r in range(2, 71) if r not in set(vis)]
```

比"截图看行号跳号"准得多，而且可编程校验。

**2. 精确跳转到第 N 行**

不能按固定次数 ArrowDown（隐藏行会导致 overshoot）。先用可见行列表算：

```python
before = [r for r in vis if r < row]    # 目标行之前有几个可见行
to_top(c); down(c, len(before))
```

### 4.5 隐藏 / 取消隐藏 —— 核心操作

- **隐藏行**：定位到起始行 → `Shift+Space` 选整行 → `Shift+↓` 扩展 → **`Ctrl+Alt+9`**
- **取消隐藏**：定位到起始行 → `Shift+Space` → `Shift+↓` 扩展（**要多扫 30 行余量**，
  确保跨越隐藏段）→ **`Alt+Shift+9`**
- 前提：必须是**整行选区**（`Shift+Space` 保证），且取消隐藏时选区要**跨越**隐藏段
- ⚠️ **目标行自己被隐藏时 `goto_row` 永远跳不到它**（`ArrowDown` 跳过隐藏行）
  → 必须锚定**隐藏段上方最近的可见行**再向下横扫（详见 rules.md A.9.8）
- 兜底：**点击行号列左侧的 ▲/▼ 小三角图标**（腾讯文档自带的折叠标记）
- `Ctrl+Z` **不能**撤销隐藏行操作
- 菜单路径（右键行号 → 「隐藏行」/「取消隐藏行」）仍可用但**慢 50 倍**，仅作兜底

**判断某行当前是否隐藏**

- 首选：**枚举可见行取缺口**（见 4.4，可编程、可校验）
- 兜底：截图看行号是否跳号
- 行高 9~20 的窄行是"午休分隔行"，不是隐藏行

---

## 5. 封装脚本

| 脚本 | 作用 |
|---|---|
| `_boot.py` | 入口基建：钉死 `CDP_PORT`、绕过代理、**端口不通时本进程内拉起 Chrome**、带重试的截图、`reload_page` |
| `_hold.py` | **Chrome 常驻守护**：后台运行，端口死了自动重启 |
| `_kb.py` | 键盘原语：`to_top` / `down` / `select_row` / `extend_down` / `hide_rows` / `unhide_rows` / `active` |
| `_rowsx.py` | 行导航：`visible_rows` / `hidden_in` / `goto_row` |
| `_j_do.py` | **批量执行算子**，每步操作后重新探测可见行自校验（日常主力） |
| `_check.py` | **版面体检**：输出当前隐藏集 + 校验"必须可见"的行（如午休行）没被藏掉 |
| `_shot.py` | **截图助手**：`connect_ready()` 自动 `bringToFront` + 激活单元格 + 回 A2；`shot(c, path, clip, scale)` 带重试 |
| `_pix.py` | **像素校验**：`colors`（行底色）/ `align`（各列文字区间与对齐）/ `row`（单行配色范围）。**需要 Pillow** |
| `_png.py` | **截图自动切片（零依赖，不需要 Pillow）**：`auto` / `crop` / `bands`。识别企微截图时**先跑它**（用法见下方） |

`_j_do.py` 用法（token 语法，`U`=取消隐藏，`H`=隐藏）：

```bash
python _j_do.py "U13-68"              # 先把 13..68 全部展开，拿到干净基线
python _j_do.py "H16-16" "H18-24" "H30-39"   # 再按清单逐段隐藏
```

推荐**两阶段模式**（用户 2026-09-14 明确要求"先清空再添加"）：
先 `U` 一大段把目标区间全部展开成干净基线，再按清单 `H` 逐段隐藏。
每个 op 之后脚本都会打印当前隐藏集，丢按键立刻暴露。
行号扫描窗口可用环境变量 `SHEET_LO` / `SHEET_HI` 调整（默认 2..90）。

### `_png.py` 用法（识别会议截图的**第一步**）

企微截图常常是 1728×6328 这种长图，直接 Read 会被缩成糊图。**不要手写像素扫描代码**
（2026-09-14 为此反复试错 10 轮），一条命令自动切片：

```bash
python _png.py auto "<截图路径>" "<输出目录>" --prefix img
# 可选：--maxh 420（片段高度）--targetw 1400（放大目标宽）--cols 2（强制竖切）
```

它会：识别背景色 → 逐行密度扫描 → 合并文字带（自动丢掉表格横线）→ 按 `--maxh`
在**文字最少的那一行**切开（不会拦腰斩断会议记录）→ 内容左右留白砍掉 → 自动放大 →
输出编号片段 + 坐标清单。

产出后**并行 Read 这些片段**即可。典型效果：一张 6 屏的长图 → 6 个片段 = 1 次命令 + 6 次并行 Read。

其它两个子命令：
- `python _png.py bands <png>` — 只看检测到的文字带（调试用，不产文件）
- `python _png.py crop <png> <dst> <x> <y> <w> <h> <scale>` — 手动精确裁切放大
  （只在"某个字拿不准"时用，例如确认人名用字）

**零依赖**：只用 `zlib` + `struct`，**不需要 Pillow**（`_pix.py` 才需要）。
换新机器、Pillow 还没装好时它照样能用。

**为什么必须有 `_boot.py`**

1. `cdp.py` 在 **import 时**读 `CDP_PORT`，所以必须在 `import cdp` **之前**
   `os.environ["CDP_PORT"] = str(PORT)`，否则连错端口。
2. WorkBuddy 沙箱会在 shell 命令返回时回收子进程，所以"启动 Chrome"和"操作 Chrome"
   必须在**同一个 python 进程内**完成 → `_boot.connect()` 连不上就自己拉。

> ⚠️ **截图落盘纪律**：`_boot.snap()` 写到环境变量 `SNAP_DIR`，**不开就落在 `scripts/` 里**。
> 跑 `_j_do.py` 等作业时**务必设 `SNAP_DIR=<工作区目录>`**，
> 否则截图会污染技能目录、把技能撑大（2026-09-14 发生过两次）。

---

## 6. CDP 踩坑清单（2026-09-14 血泪）

- **菜单类名必须精确等值匹配**：`contextmenu-item-cancel-hide-row` **包含**
  `contextmenu-item-hide-row` 子串，用子串匹配会点错菜单项（两项垂直仅差 32px）。
  用 `===` 而不是 `includes`。
- **菜单定位用命中测试**：`document.elementsFromPoint()` 网格采样。因为菜单有
  多份预渲染副本，`getBoundingClientRect()` 受 transform 影响会返回假坐标；
  且同一 stack 里 `<li>` 和外层 `<ul>` 并存，要**优先取 `<li>`**。
- **菜单可能弹在点击点右侧**，扫描区要覆盖整个视口，不能只扫左侧。
- **菜单残留卡住、Esc 无效** → 用 `Page.reload` 硬重置（`_boot.reload_page()`）。
- **内联 JS 先过 `node --check`**：JS 语法错误在 CDP 里只返回 `{'error': 'Uncaught'}`，
  没有任何行号信息，极难排查。
- **截图会偶发超时**（渲染繁忙）→ `snap()` 带 5 次重试。
- **`Shift+↓` 扩展时名称框不更新**（仍显示锚点行），不能用作校验信号 →
  唯一可靠校验是**操作后重新探测可见行序列**。
- **脚本里不要依赖 bash**：WorkBuddy 沙箱的 bash 环境异常（`ls`/`dirname`/`head`
  都 command not found，且找不到 `git`）。一律用 python 绝对路径 + 脚本文件方式，不依赖管道。
  （顺带：`git` 要用 `%USERPROFILE%\.workbuddy\binaries\PortableGit\versions\1.2.0\cmd\git.exe`）
- 拼图/裁图需要 Pillow，已装在 `python/envs/default`（12.3.0）

---

## 7. 隐藏集"误报"陷阱（2026-09-14 血泪）

- **`ArrowDown` 会失灵**：页面处于异常状态（选区/编辑态残留）时，`ArrowDown` 完全不动，
  `visible_rows()` 只返回极短列表，于是把整表**误判成"几乎全隐藏"**。
  上一轮因此白跑了一轮 fix 脚本——**其实隐藏集一直是对的**。
- **判据**：一旦探测结果出现"极端值"（全隐藏 / 可见行只剩 1 个），
  **先 `Page.reload` 再复核**（`_boot.reload_page()`，然后 `_check.py`），别急着补救。
- **不要拉高视口**：`Emulation.setDeviceMetricsOverride(height=3800)` 只会截出一张
  3800px 的图，**canvas 仍只渲染原视口那部分**，下面全是空白；还会让渲染状态变脏。
- **要看别处就用 `_rowsx.goto_row(c, r)`**：移动活动单元格，表格会自动把该行滚入视野。
  （`PageDown` 在网格里**无效**，不会翻页。）

---

## 8. CDP 输入与截图踩坑（2026-09-14）

- **点击前必须 `Page.bringToFront`**：标签页不在前台时 `Input.dispatchMouseEvent` 被丢弃、点了没反应。
  正确序列：`bringToFront` → `mouseMoved` → `mousePressed` → `mouseReleased`，带 `pointerType:"mouse"`。
- **`Page.reload` 后名称框是空的**：没有活动单元格，`.bar-label` 返回 `''`，
  `visible_rows()` 只返回 `[None]`，看起来像"整表全隐藏"（就是第 7 节的误报）。
  **重载后先点一次网格再走键盘**；`eval` 本身在 reload 后仍然可用，不用重连 websocket。
- **表头行 1 是冻结行**：任何滚动位置下都在屏幕同一 y（1920×922 截图为 y≈186–214）。
  量表头永远准；**量正文行前必须先确认滚动位置**。
- **还原格式要用像素校验**：改动前后各截一张，比"同一行同一列的文字像素区间 `text[x0-x1]`"。
  裁剪窗口**要比目标宽 100px 以上**，否则会把边框像素当成文字、或漏掉真正的文字。
- **⚠️ 写完样式/内容后画布不一定重绘**：`set_cell_style` 之后立刻截图可能还是**旧画面**
  （2026-09-14 新增的绿行截出来是全白，差点误判"底色没写进去"）。
  **顺序固定为：写入 → 回读校验（沙箱 `getRange`）→ `Page.reload` → 再截图/像素校验。**
- **⚠️ 行号口径别搞混**：沙箱 `getRange(r,c)` 用 **1-based = 表格 UI 行号**
  （与 rules.md 的 `R52`、`_j_do.py` 的 `"H54-54"` 同口径）；
  MCP 的 `get_cell_data` / `set_cell_style` / `clear_range_cells` 用 **0-based**
  （**`MCP 行号 = UI 行号 - 1`**，实测 `start_row=52` 返回 UI 第 53 行）。
  **多行 CSV 输出偶发错位 → 关键行一律用"单行小窗口"或沙箱复核，别数空行。**

---

## 9. 临时文件纪律

- 调试脚本和截图**不要留在技能目录里**。2026-09-14 一轮调试产生了 326 个临时文件
  （90 个 `_j_*`/`_dbg*`/`_probe*` 脚本 + 250 张截图），已整体移出技能目录到
  `outputs/meeting-scheduler-archive/`（参与打包会把技能从 119 KB 撑到 23 MB）。
- 工作产物统一放 `D:\WorkBuddy\<session>\outputs\` 下，用绝对路径。
- `.gitignore` 已排除 `scripts/*.png`、`__pycache__`、`_trash/`。
- 跑完作业顺手 `find <skill> -name "__pycache__"` 清一下。
