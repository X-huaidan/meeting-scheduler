---
name: meeting-scheduler
version: 1.6.0
description: 孟总会议行程表（腾讯文档在线表格 docs.qq.com/sheet/DT3Z4cGNQZmVpU2xV，子表"时间表"）的排会与排版技能，中文别名"孟总会务助手"。当用户要求把会议信息（文字或截图）写入该行程表、调整会议行底色/对齐/换行、隐藏或展开每天的行（Ctrl+Alt+9 隐藏行 / Alt+Shift+9 取消隐藏）、按"每天只显示有会议的行"整理版面、展示或修改排会规则（references/rules.md）、展示或修改功能清单（references/features.md）、展示更新日志（references/CHANGELOG.md）、手动触发发版（"更新上传/打包上传"）时使用。也适用于任何需要在腾讯在线表格中精确模拟 UI 操作（CDP 接管 Chrome）的场景。
agent_created: true
---

# 孟总会务助手

把用户提供的会议信息（文字 / 企业微信截图）整理后写入「孟总会议行程表」，并完成版面整理
（底色、对齐、换行、隐藏空白行）。

**目标表格**：file_id `DT3Z4cGNQZmVpU2xV` · 子表 `时间表`（sheet_id `000001`，另有 `时间表2`）
· URL `https://docs.qq.com/sheet/DT3Z4cGNQZmVpU2xV?tab=000001` · 引擎 = 腾讯在线表格（个人版），**canvas 渲染**

---

## 🚦 开工前必读（闸门，不得跳过）

**本文件是"导航 + 红线"，不是操作手册。动手前按需读：**

| 你要做的事 | 必读 |
|---|---|
| **任何写入 / 改样式 / 改对齐** | **`references/rules.md` A.1 · A.2 · A.3 · A.11 · A.12**（A.11 是最高优先级铁律） |
| 隐藏 / 展开行、判断隐藏状态 | `rules.md` A.7~A.10 + `references/cdp_notes.md` 第 4 节 |
| 判定"这场会要不要排" | `rules.md` **B.11**（**以孟总实际是否参加为准**） |
| 参会领导 / 参会人员怎么写 | `rules.md` B.2 · B.3（含范本） |
| 整日版面收版 | `rules.md` B.8（尤其 B.8.9 目标可见集） |
| CDP / 键盘 / 截图 / 像素校验 | `references/cdp_notes.md` 全文 |
| 发版 / 问版本大小 | `references/publishing.md` |

> **规则之上的总原则：文档比记忆可靠。** 本文件正文是**摘要**；`references/rules.md` 与
> `references/features.md` 才是**权威来源**，两者不一致时**以 references 为准**。
> ⚠️ **表格会被用户随时调整 —— 每次开工前必须重新读取实际结构（合并块 + 行高），不要依赖旧锚点。**

---

## 🚨 安全红线（2026-09-11 全表清空事故后新增，必须遵守）

**绝对禁止**在网格上发送 `Ctrl+A` 和 `Delete` 组合。

- ❌ 不要用「点 Name box → `Ctrl+A` → 输入范围 → `Enter` → `Delete`」清空数据。
  Name box 的点击经常**抢不到焦点**，`Enter` 也不一定提交范围；此时 `Ctrl+A`
  会选中**整张子表**，紧跟的 `Delete` 会把整表清空。2026-09-11 就是这样把
  「时间表」整表清掉的（用户发现后叫停，靠修订记录回滚）。
- ✅ **清空数据一律走 MCP API**：`sheet.clear_range_cells(file_id, sheet_id, range)`。
  精确、可回读校验、不依赖焦点。
- ✅ **隐藏 / 取消隐藏走键盘链路**（`Ctrl+Alt+9` / `Alt+Shift+9`，比右键菜单快 50 倍）。
- ✅ 任何破坏性操作前：先 MCP 读一遍目标区域，把"将要清空的范围 + 当前内容摘要"
  列给用户，等确认后再执行。
- ✅ **每一步之后用 MCP `sheet.get_cell_data` 回读校验，而不是只看截图。**

**一直有用的关键事实**：网格和行号列都是 `<canvas>`；右键菜单**是 DOM**。
读活动单元格用 `document.querySelector('.bar-label').value`（返回如 `A40`）。
（细节见 `references/cdp_notes.md` 第 3 节。）

> ⚠️ **2026-09-14 更正**：旧文档「canvas 收不到键盘事件、别用 `Alt+Shift+9`」是**错的** ——
> 病因是 `Input.dispatchKeyEvent` 用了 `keyDown`，改用 **`rawKeyDown`** 后键盘完全可用。
> 隐藏/展开**一律优先走键盘**，不要走右键菜单。

### ⚠️ 改样式前必读：`set_cell_style` 是全量覆盖

`sheet.set_cell_style` **未传的属性会被重置成默认值**（底→白、字→黑、粗→关、对齐→左、字号→10）。
2026-09-14 就是因为"只想开自动换行，只传了 `wrap_text=true`"，把**表头蓝底/白字/加粗/居中
和会议行底色全抹了**（用户次日发现）。

**铁律**：每次调用都把该区域要保留的属性**显式传全**：
`bg_color` `font_color` `bold` `font_size` `horizontal_align` `vertical_align` `wrap_text`。

**格式基线**（实测可逐像素还原，权威版见 `rules.md` A.11–A.12）：

| 区域 | 属性 |
|---|---|
| A1:I1 表头 | `bg=FF2972F4` `font_color=FFFFFFFF` `bold=true` `font_size=11` `h=center` `v=center` `wrap=true` |
| B:D | `h=center` `v=center` `wrap=true` |
| E | `h=left` `v=center` `wrap=true` |
| F:G | `h=center` `v=center` `wrap=true` |
| H:I | `h=left` `v=center` `wrap=true` |
| 绿行（含姜）/ 橙行（含邓），均 C:I | `bg=FFC3EAD5` / `bg=FFFFDCC4` + 该列对齐 + `v=center` `wrap=true` |

> 底色必须**最后**恢复（对齐调用会抹掉它），且恢复底色时**也要带上 bg 参数**。
> **底色一行要拆 3 次调用**（各带 bg）：`C:I`（h=center）→ `E`（h=left）→ `H:I`（h=left）。
> ⚠️ **腾讯文档没有版本回滚接口** → 格式务必一次写对，别指望能撤销。

---

## 何时触发

- "帮我安排会议 / 把这个会议加进行程表 / 排会" · "调整底色 / 对齐 / 换行" · "隐藏行 / 展开行 / 取消隐藏"
- 提供会议截图或文字，要求写入
- **"展示"类**（一律**完整 Read 并显示，不要总结/精简**）：
  "展示排会规则 / 看看规则 / 显示规则" → `references/rules.md`；
  "展示功能 / 功能清单 / 这个技能能干啥" → `references/features.md`；
  "展示更新日志 / 看变更历史" → `references/CHANGELOG.md`
- "技能多大 / 文件多大 / 现在多少 KB" → `scripts/publish_to_baidu.py --size`（不发版）；
  发版完成后 → 自动输出"已发版 + 当前大小 + 效率评估"汇报（无需触发词）
- "增加/删除一条规则" → 编辑 `references/rules.md`；"增加/删除一个功能" → 编辑 `references/features.md`
  （两者都**仅改文档 + 追加 CHANGELOG 草稿，不发版**）
- "**更新上传 / 打包上传 / 上传到网盘**" → 手动触发发版（流程见 `references/publishing.md`）
- "清理本周 / 跑一次清理 / 模拟周日清理 / 执行 8.1" → 清空本周一到周五的 C:I + 展开隐藏行
  （**破坏性操作，先列清单等用户确认**）
- "周末不用排 / 周末的会议数据不需要排" → 「周末不排会」生效，**跳过周六周日**，
  表格里周末现有内容保持原状（见 B.10）

---

## 表格结构

**列**（共 11 列 A~K，A 列空）：`B` 日期（每天第一行写"周一/…/周日"，即**标记行**）· `C` 时间
（`11:20-12:00`）· `D` 会议名称 · `E` 会议议程 · `F` 地点 · `G` 参会领导 · `H` 参会人员 · `I` 组织人

**行结构**（每天约 10~14 行）：
`[标记行] → [上午会议行] → [午休分隔行] → [下午会议行] → [空白行...]`

### 🔑 午休分隔行怎么定（2026-09-14 修正，务必照此）

不要靠"标记行 + 常数"推算——**每天偏移不一样**（实测 3/4/6/5/5）。用两个 API 精确定位：

1. 沙箱 `SpreadsheetApp.getActiveSheet().getRowHeight(r)`（**1-based**）读行高：
   普通会议行 = `60`，**午休分隔行 = `9~10`（很矮）**，天间间隔行 = `19~20`
2. `sheet.get_merged_cells` 取 B 列日期合并块（`B3:B12` 这样）= 该天的行区域，
   区域里那条窄行就是当天的午休分隔行

**已知锚点（2026-09-14 实测，仅参考，每次重新实测）**：
周一 `R3`/午休`R6`（`B3:B12`）· 周二 `R14`/`R18`（`B14:B24`）· 周三 `R26`/`R32`（`B26:B39`）·
周四 `R41`/`R46`（`B41:B50`）· 周五 `R52`/`R57`（`B52:B64`）· 周六 `R66`/`R69` · 周日 `R76`/`R79`

> ⚠️ **上一轮的重大误判**：曾按"标记行 + 3"推出 R17/R29/R44/R55 是午休行，其实那只是普通空行；
> 真正的午休行 R18/R32/R46/R57 一直被藏在隐藏区里。
> ⚠️ **读长区间数空行必错**（曾把周五标记行误判为 R54 实为 R52、周二会议数成 R15 实为 **R19**）
> → **定位锚点用 `get_cell_data` 的 `return_csv=false` 结构化返回**（每格带 `row` 字段），别数空行。

### 每天目标可见集（整日收版标准，**完整版见 `rules.md` B.8.9**）

每天只留「标记行 + 会议行 + 午休行 + 当天末尾 1 个间隔行」：
周一 `R3 R5 R6 R7-9 R13` · 周二 `R14 R18 R19 R25` · 周三 `R26-28 R32 R40` ·
周四 `R41-43 R46 R51` · 周五 `R52 R53 R57 R58 R65`（周一 `R7`、周五 `R58` 是**绿行**）
隐藏集：周一 `H4 H10-12` · 周二 `H15-17 H20-24` · 周三 `H29-31 H33-39` ·
周四 `H44-45 H47-50` · 周五 `H54-56 H59-64`

> **「把会议紧挨着午休分割行来排」= 隐藏中间空白行，不是搬动会议内容**（周三会议 R27/R28、午休 R32，
> 隐藏 R29-31 即视觉紧贴）。⚠️ `R54` 曾是绿行，但已随 G318 撤销，别再往那找。
> ⚠️ 目标行自己是隐藏行时 `ArrowDown` 跳不到它（`rules.md` A.9.8），要先锚定可见的午休行再向下横扫。
> **周一、周二当时未收版（仍全展开）**，要统一补跑 `_j_do.py "H4-4" "H10-12" "H15-17" "H20-24"`。

### 数据源（源截图在哪，随时可复核）

用户贴进来的企业微信截图会被 WorkBuddy **落盘保留**在
**`%USERPROFILE%\.workbuddy\clipboard-images\clipboard-<UTC时间戳>.jpg`**。
本表当前源图 = **`clipboard-2026-09-14T02-11-53-384Z-e9e13a86.jpg`（1920×1231）
=「房总 2026/9/14–9/20 会议安排表」** → **有疑问直接重裁这张图，不要凭记忆或猜**。
⚠️ 该图小字只有约 8px 高，**参会人名单读不准就必须问用户**（详见 `rules.md` C.2.5）。

---

## 关键技术：两条通道

| 通道 | 能力 | 局限 |
|---|---|---|
| **A. MCP sandbox**（`sheet.operation_sheet`） | 读值/结构、写值、写样式、行高列宽、合并 | **不能隐藏行**；不能判断某行是否隐藏；**样式读取只对第 1 行有效**（其余恒返回 `#000000`）；无 `copyTo`/`clearContent` |
| **B. CDP 接管 Chrome**（键盘链路） | 隐藏行 / 取消隐藏 / 判断隐藏状态 / **截图 + 像素校验** | 需要带调试端口的 Chrome（`_hold.py` 常驻） |

**结论：写数据用 A；隐藏行、以及一切样式校验用 B（走键盘链路）。**
> ⚠️ **永远不要用沙箱回读底色来判断"样式有没有丢"** —— 第 2 行起恒返回 `#000000`，
> 既不能证明保留也不能证明丢失。2026-09-11 整表被清、09-14 表头格式被抹，两次事故当场漏掉就是这个原因。
> 能力对照表 + 可直接抄的 JS 片段：**`references/api_caps.md`**；通道 B 细节：`references/cdp_notes.md`。
**性能常识**：键盘 `~30ms/次`、鼠标 `~1.7s/次`、**鼠标滚轮 40s 直接超时**（canvas 无滚动容器）
→ **能走键盘就别走鼠标**。

---

## 标准工作流

**1. 读取结构（每次必做）** — 先读 `rules.md`（至少 A.11/A.12 + 相关 B 章节），
再用通道 A 分批读 B~I 列 + 行高。**JS 片段直接抄 `api_caps.md` 第 5 节，不要重写。**

**2. 识别与预览** — 截图需识别：时间、会议名称、议程、地点、参会领导、参会人员、组织人。
**截图先跑一条命令自动切片**（别手写像素扫描代码）：
`python scripts/_png.py auto "<截图路径>" "<输出目录>" --prefix img` → 再并行 Read 产出的片段。
按 `rules.md` B.1~B.12 推导：**这场会排不排（B.11）** → 目标日期与行号 → 底色 → 领导栏/参会人写法。
**给用户预览，确认后再写**（仅时间冲突需问；缺时段按 B.12 直接排、人名用字不确定才问）。

**3. 写入** — 单元格值用 `sheet.set_range_value`（`string_value`）或 sandbox `setValue`；
底色/对齐/换行用 `sheet.set_cell_style`（**一次传全 7 个属性**）；写入后**回读校验**。

**4. 整理版面（隐藏空白行）** — 走键盘链路：
① 算出目标隐藏清单 → ② **先展开拿干净基线** `python _j_do.py "U13-68"` →
③ **再逐段隐藏** `python _j_do.py "H16-16" "H18-24" ...`（每个 op 后自动打印隐藏集，核对清单）→
④ 体检 `python _check.py 6 18 32 46 57`（午休行必须全部可见）→
⑤ **`Page.reload` 后**再截图 + `_pix.py` 像素校验 → ⑥ `get_cell_data` 回读内容确认不丢。
> **不要逐行点击行号 + 右键菜单**：一次排 4 天会要几分钟且容易丢 Shift 锚点；键盘链路几秒完成且每步自校验。

**5. 汇报** — 说清改了哪些行、隐藏了哪些行、最终版面；**贴校验结果**（不是"看起来对了"）。

---

## 文档地图

| 文件 | 装什么 |
|---|---|
| `references/rules.md` | **排会规则权威来源**：A 表格操作 / B 会议安排 / C 输入处理 / D 工作流 / E 用户专属 |
| `references/api_caps.md` | **通道能力实测矩阵 + 可抄的 JS 片段**：沙箱有哪些方法、哪些读数是假的、什么任务走哪条通道 |
| `references/cdp_notes.md` | 通道 B 操作手册：sandbox 用法、CDP 坐标、键盘链路、脚本清单、踩坑清单 |
| `references/features.md` | **功能清单权威来源**（8 类） |
| `references/publishing.md` | 发版与版本管理：版本号约定、发版 6 步、git 踩坑、**文档体积纪律** |
| `references/sheet_ui_cheatsheet.md` | UI 操作坐标速查（右键菜单兜底时用） |
| `references/CHANGELOG.md` | 更新日志（"已发布" + "待发布草稿"） |

> **为什么拆成多份**：SKILL.md 每次触发都会被完整读入，必须保持精简（**目标 ≤ 15 KB**）；
> 细节放 references 按需加载，同一内容只保留一个权威位置。详见 `publishing.md` 第 7 节。

---

## 版本管理与脚本清单

**版本管理**（**完整流程见 `references/publishing.md`**）：**编辑即时落盘**（只改文件 + 追 CHANGELOG 草稿）→
**🚫 只有用户明确说"发版"才发**（**禁止每次改动就自动发版**；~~每天 23:59 定时自查~~ 已取消）→
版本号 `X.Y.Z`（`X` 结构/通道变化 · `Y` 新功能规则 · `Z` 错别字），
**发版 = 用当前 version commit+push → 再 bump +1 次版本**。
⚠️ **push 前先探测通路**：远端 `git@github.com:X-huaidan/meeting-scheduler.git`（SSH 为默认）；
本机 SSH / HTTPS 谁通**每次要现场测**（2026-09-11 SSH 通、2026-09-14 SSH 被重置而 HTTPS 通）——
`git` 不在默认 PATH，用 `...\PortableGit\versions\1.2.0\cmd\git.exe`。
**发版后自动报大小 + 阈值评估（功能 7.7）；SKILL.md 单项超 30 KB 就必须拆。**
跨设备：家里电脑 `cd ~/.workbuddy/skills/meeting-scheduler && git pull`。

**`scripts/` 脚本**（作用详见 `references/cdp_notes.md` 第 5 节）：
`_png.py` **截图自动切片（零依赖，识图主力）** · `_boot.py` 入口基建 · `_hold.py` Chrome 常驻 ·
`_kb.py` 键盘原语 · `_rowsx.py` 行导航 ·
`_j_do.py` **批量算子（日常主力）** · `_check.py` 版面体检 · `_pix.py` 像素校验（**需 Pillow**） ·
`_shot.py` 截图 · `cdp.py` CDP 封装 · `sheet_ui.py` / `_menu.py` / `_icons.json` UI 兜底 ·
`publish_to_baidu.py` 发版 · `weekly_unhide.py` / `weekly_cleanup.py` 周维护

> ⚠️ **截图落盘纪律**：`_boot.snap()` 写到环境变量 `SNAP_DIR`，**不开就落在 `scripts/` 里**。
> 跑作业时**务必设 `SNAP_DIR=<工作区目录>`**，否则会把技能目录撑大（2026-09-14 发生过两次）。
> **临时文件纪律**：调试脚本和截图别留在技能目录，产物统一放 `D:\WorkBuddy\<session>\outputs\`；
> `.gitignore` 已排除 `scripts/*.png`、`__pycache__`、`_trash/`；跑完顺手清 `__pycache__`。
