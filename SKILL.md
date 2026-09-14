---
name: meeting-scheduler
version: 1.1.0
description: 孟总会议行程表（腾讯文档在线表格 docs.qq.com/sheet/DT3Z4cGNQZmVpU2xV，子表"时间表"）的排会与排版技能，中文别名"孟总会务助手"。当用户要求把会议信息（文字或截图）写入该行程表、调整会议行底色/对齐/换行、隐藏或展开每天的行（Ctrl+Alt+9 隐藏行 / Alt+Shift+9 取消隐藏）、按"每天只显示有会议的行"整理版面、展示或修改排会规则（references/rules.md）、展示或修改功能清单（references/features.md）、展示更新日志（references/CHANGELOG.md）、手动触发发版（"更新上传/打包上传"）时使用。也适用于任何需要在腾讯在线表格中精确模拟 UI 操作（CDP 接管 Chrome）的场景。
agent_created: true
---

# 孟总会务助手

## 用途

把用户提供的会议信息（文字 / 企业微信截图）整理后写入「孟总会议行程表」，并完成版面整理（底色、对齐、换行、隐藏空白行）。

**目标表格**
- file_id: `DT3Z4cGNQZmVpU2xV`
- URL: `https://docs.qq.com/sheet/DT3Z4cGNQZmVpU2xV?tab=000001`
- 子表名: `时间表`（sheet_id `000001`），另有 `时间表2`
- 引擎: 腾讯在线表格（个人版），canvas 渲染

## 🚨 安全红线（2026-09-11 全表清空事故后新增，必须遵守）

**绝对禁止**在网格上发送 `Ctrl+A` 和 `Delete` 组合。

- ❌ 不要用「点 Name box → `Ctrl+A` → 输入范围 → `Enter` → `Delete`」清空数据。
  Name box 的点击经常**抢不到焦点**，`Enter` 也不一定提交范围；此时 `Ctrl+A`
  会选中**整张子表**，紧跟的 `Delete` 会把整表清空。2026-09-11 就是这样把
  「时间表」整表清掉的（用户发现后叫停，靠修订记录回滚）。
- ✅ **清空数据一律走 MCP API**：`sheet.clear_range_cells(file_id, sheet_id, range)`。
  精确、可回读校验、不依赖焦点。
- ✅ **展开隐藏行一律走** `scripts/weekly_unhide.py`（点行号 + Shift 点行号 + 右键 +
  DOM 定位「取消隐藏行」）。不要再用 `Alt+Shift+9`，canvas 收不到键盘事件。
- ✅ 任何破坏性操作前：先 MCP 读一遍目标区域，把"将要清空的范围 + 当前内容摘要"
  列给用户，等确认后再执行。
- ✅ 每一步之后用 MCP `sheet.get_cell_data` 回读校验，而不是只看截图。

**事故后已验证的关键事实**（省得下次再摸索）：
- 网格和行号列都是 `<canvas>`；右键菜单**是 DOM**（`div.dui-menu.context-menu_contextmenu__*`）。
- 菜单项的**可见文字不在 textContent 里**，只有右侧快捷键提示在：
  `Ctrl+Alt+9` = 隐藏行，`Alt+Shift+9` = 取消隐藏行 → 用快捷键文本定位菜单项。
- 「取消隐藏行」只有在**选中整行范围且跨越隐藏行**时才出现；点行号 + Shift 点行号
  **两步必须在同一屏内**完成，中间滚动会丢掉 Shift 扩展锚点。
- 读活动单元格用 `document.querySelector('.bar-label').value`（返回如 `A40`）。
- 扫行号列时点击 y **避开视口最上/最下 60px**，否则会触发自动滚动、扫描数据错乱。

## 何时触发

- "帮我安排会议 / 把这个会议加进行程表 / 排会"
- "调整底色 / 对齐 / 换行"
- "隐藏行 / 展开行 / 取消隐藏"
- 提供会议截图或文字，要求写入
- "展示排会规则 / 看看规则 / 显示规则" → 读取并展示 `references/rules.md`
- "展示功能 / 看看功能 / 功能清单 / 这个技能能干啥" → 读取并展示 `references/features.md`
- "展示更新日志 / 看更新日志 / 看变更历史 / 变更记录" → 读取并展示 `references/CHANGELOG.md`
- "技能多大 / 技能大小 / 文件多大 / 现在多少 KB" → 调 `scripts/publish_to_baidu.py --size` 输出当前大小 + 阈值评估（不发版）
- 发版完成后 → agent 自动输出"已发版 + 当前大小 + 效率评估"汇报（无需触发词）
- "增加/删除一条规则" → 编辑 `references/rules.md`（**仅修改文档 + 追加 CHANGELOG 草稿，不触发发版**）
- "增加/删除一个功能" → 编辑 `references/features.md`（**仅修改文档 + 追加 CHANGELOG 草稿，不触发发版**）
- "**更新上传 / 打包上传 / 上传到网盘**" → 手动触发发版：把 CHANGELOG 草稿合并到已发布段、打包 zip、push 到 GitHub
- "清理本周 / 跑一次清理 / 模拟周日清理 / 执行 8.1" → 清空本周一到周五的 C:I 会议信息 + 展开所有隐藏行（**破坏性操作，先列清单等用户确认**）

> **规则与功能的权威来源是 `references/rules.md` 和 `references/features.md` 两份文档。** 本文件正文里残留的"排版规则/注意事项"章节是历史快照，权威解释以这两份文档为准。如果发现两份内容不一致，**以 references 目录下的为准**，并通知用户同步更新本文件。

## 表格结构

列（共 11 列 A~K，A 列空）：

| 列 | 含义 |
|---|---|
| B | 日期（每天第一行写"周一/周二/…/周六"，作为当天标记行） |
| C | 时间（如 `11:20-12:00`） |
| D | 会议名称 |
| E | 会议议程（可多行，如 `1.xxx 2.xxx`） |
| F | 地点 |
| G | 参会领导 |
| H | 参会人员 |
| I | 组织人 |

行结构（每天约 11~12 行）：

```
[标记行 B=周X]
[上午若干会议行]
[午休分隔行]  ← 行高 9~20 的窄行
[下午若干会议行]
[空白行...]
```

**已知锚点行（2026-09-11 数据）**

| 天 | 标记行 | 午休分隔行 |
|---|---|---|
| 周一 | R3 | R6 |
| 周二 | R14 | R18 |
| 周三 | R26 | R32 |
| 周四 | R41 | R46 |
| 周五 | R52 | R57 |
| 周六 | R70 | — |

> 表格会被用户随时调整，**每次开工前必须重新读取实际结构**（见"读取结构"）。

## 排版规则（用户约定）

### 底色
- 含 **邓** → 参会领导只写"邓"，整行 C:I 填 **浅橙2 `#FFDCC4`**（RGB 255,220,196）
- 无邓、含 **姜** → 只写"姜"，整行 C:I 填 **浅绿2 `#C3EAD5`**（RGB 195,234,213）
- 其他情况按原样写
- 填色范围：**C 列到 I 列**

### 对齐
- **左对齐**：E 列（会议议程）、H 列（参会人员）
- **居中**：C、D、F、G、I 列

### 换行
- E 列（议程）、H 列（参会人员）设 **自动换行**

### 隐藏行
- 会议时段：上午 08:30-12:00，下午 13:30-18:00
- **每天排好后，只保留"有会议的行 + 午休分隔行 + 当天标记行"，其余空白行隐藏**
- 若某天上午只有一场会议，则该场会议应紧贴午休分隔行上方可见，上午其余空白行隐藏

### 其他
- 信息先识别 → 给预览 → 用户确认 → 再写入
- 时间冲突由用户协调，agent 只标记不裁决
- 领导/参会人中若没有"孟"，自动补在"房"之后（本表专属规则）

---

## 关键技术：如何可靠操作这张表

### 两条通道

| 通道 | 能力 | 局限 |
|---|---|---|
| **A. MCP sandbox**（`mcp__tencent-docs__sheet.operation_sheet`） | 读写单元格值、底色、对齐、换行、行高 | **不能隐藏行**；不能判断某行是否被隐藏 |
| **B. CDP 接管 Chrome**（模拟真实用户 UI 操作） | 隐藏行 / 取消隐藏 / 选中整行 / 右键菜单 | 依赖用户 Chrome 开着调试端口 |

**结论：写数据用 A，隐藏行用 B。**

### 通道 A：sandbox 用法

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

可用方法：`getValue` / `setValue` / `getBackground` / `setBackground` / `getRowHeight` / `setRowHeightsForced` / `setHorizontalAlignment` / `setWrapText`

**关键认知**
- `setRowHeightsForced(r, 1, 60)` 实际可能只落到 45，无法把已被改小的行恢复成原值
- `getRowHeight` 返回的是**行高设置值**；**行被隐藏时该值不变**（仍是 60）→ **沙箱无法判断隐藏状态**
- **禁止**用 `setRowHeightsForced(r,1,1)` 模拟隐藏：它是"改高度"而非"隐藏"，用户无法用取消隐藏恢复，会永久污染表格

### 通道 B：CDP 用法

**前置条件**：用户 Chrome 以 `--remote-debugging-port=9222` 启动，并已打开目标表格页。

```
Python venv: C:\Users\changan\.workbuddy\binaries\python\envs\cdp_venv
依赖: websocket-client
连接注意: websocket.create_connection(ws_url, timeout=120, suppress_origin=True, origin=None)  # 否则 403
```

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
- 鼠标 wheel 事件
- `Ctrl+A`（只选单元格区域，不是整行）
- `Shift+PageDown` / `Ctrl+Shift+Down` / `Ctrl+Shift+End` 扩展整行选择
- `Ctrl+Shift+9`（这不是隐藏行快捷键）

### 隐藏 / 取消隐藏 —— 核心操作

**隐藏行**
- 快捷键 **`Ctrl+Alt+9`**
- 或：**右键行号 → 菜单点"隐藏行"**（推荐，不受输入法干扰）
- 前提：先点击行号列**选中整行**

**取消隐藏**
- 快捷键 **`Alt+Shift+9`**：先选中被隐藏行的**上下邻行（整行）**，再按
- 或：**点击行号列左侧的 ▲/▼ 小三角图标**（腾讯文档自带的折叠标记）
- `Ctrl+Z` **不能**撤销隐藏行操作

**判断某行当前是否隐藏**
- 唯一可靠办法：**截图看行号是否跳号**（跳过的行号 = 隐藏行）
- 行高 9~20 的窄行是"分隔行"，不是隐藏行

---

## 标准工作流

### 1. 读取结构（每次必做）

用通道 A 分批 `console.log` 读取 B~I 列内容 + 行高，得到每天的行范围和会议清单。

```javascript
var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('时间表');
var out = [];
for (var r = START; r <= END; r++) {   // 每次 20 行
  var vals = [];
  for (var col = 2; col <= 9; col++) vals.push(sh.getRange(r, col).getValue());
  out.push(r + '|' + vals.join('|') + '|h=' + sh.getRowHeight(r));
}
console.log(out.join('\n'));
```

### 2. 识别与预览

- 输入可能是文字或截图。截图需识别：时间、会议名称、议程、地点、参会领导、参会人员、组织人
- 按"排版规则"推导：目标日期 → 目标行号、底色、领导栏写法、是否补"孟"
- **给用户预览，确认后再写**

### 3. 写入

- 单元格值：优先 `set_cell_value`（用 `string_value` 字段），或 sandbox `setValue`
- 底色 / 对齐 / 换行：用 sandbox（`setBackground` / `setHorizontalAlignment` / `setWrapText` 最稳）
- 写入后**回读校验**（sandbox 或 `get_cell_data`）

### 4. 整理版面（隐藏空白行）

1. 用 CDP `Ctrl+Home` + `PageDown` 逐屏截图，定位目标天所在屏
2. 校准该屏的行号 y 坐标（点击行号列验证，看名称框回显的行号是否匹配）
3. 对该天要隐藏的每一行：
   - 点击行号 `(28, y)` 选中整行
   - 右键行号 → 点"隐藏行"
4. 截图确认行号已跳号（隐藏成功）、有会议的行仍可见
5. 用 sandbox 回读内容，确认数据未丢失

### 5. 汇报

- 说明改了哪些行、隐藏了哪些行、最终版面效果
- 若中途有误操作（如误改行高），说明并给出恢复方案

## 规则与功能文档

技能维护两份独立的 markdown 文档，作为权威来源：

### `references/rules.md` — 排会规则

- 包含所有排会时遵循的规则
- 5 个分类：表格操作 / 会议安排 / 输入处理 / 工作流 / 自定义
- 每条规则有编号，方便引用和修改

**展示**：用户说"展示排会规则 / 看看规则 / 显示规则" → **完整 Read 并显示** `references/rules.md` 全文（不要总结、不要精简）

**修改**：用户说"加规则/删规则/改规则" → 引导用户说出具体内容 → Edit `references/rules.md` 对应章节 → **追加一行到 `references/CHANGELOG.md` 的"待发布"段（草稿）**。**不会触发发版。**

### `references/features.md` — 功能清单

- 包含技能当前所有功能
- 7 个分类：会议录入 / 会议读取 / 版面整理 / 表格结构 / 跨设备同步 / 工具脚本 / 自我管理
- 每个功能有编号，方便引用

**展示**：用户说"展示功能 / 看看功能 / 功能清单" → **完整 Read 并显示** `references/features.md` 全文

**修改**：用户说"加功能/删功能" → 引导用户说出具体内容 → Edit `references/features.md` 对应章节 → **追加一行到 `references/CHANGELOG.md` 的"待发布"段（草稿）**。**不会触发发版。**

### 为什么分离到独立文档

1. **易维护**：规则/功能变更只改一个文件
2. **易查阅**：用户能直接 cat 文件，不依赖 agent
3. **权威唯一**：避免 SKILL.md 正文与外部文档不一致
4. **可共享**：规则文档可以单独发给其他人 review
5. **编辑/发版解耦**：加规则不立刻发版，避免每次微调都刷一版（详见"版本管理与自动发布"）

---

## 注意事项

- **破坏性操作前先确认基线**：隐藏行会改变用户看到的版面，操作前先截图留档
- **不要用 `setRowHeightsForced` 模拟隐藏**（见上）
- 腾讯文档 MCP 对这张表偶发 `code -12 missing data not found` 或 tcp timeout —— **直接重试**，通常第二次成功
- sandbox 的日志会截断长输出，**分批读取**
- 若 CDP 端口不通，请用户重新以调试端口启动 Chrome：`chrome.exe --remote-debugging-port=9222`

---

## 版本管理与自动发布

### 核心理念：编辑即时落盘，发版批量进行

- **改文档**（加/删规则、加/删功能、修 SKILL.md）→ **立即落盘 + 追加 CHANGELOG "待发布"草稿**——**不发版、不 push**
- **发版**（打包 + push + 同步网盘）→ **只在两个条件触发时才执行**：
  - 条件 A：用户说"**更新上传 / 打包上传 / 上传到网盘**"（手动触发，立即跑）
  - 条件 B：每天 23:59 的 automation 定时跑一次（自动触发，无变化则跳过）
- 这样避免每次微调都刷一版，但累积到一定量又能集中发版

### 版本号约定

- frontmatter 必填 `version: X.Y.Z`
- 文件名格式：`meeting-scheduler-v{X.Y.Z}_{YYYYMMDD}.zip`
- 例：`meeting-scheduler-v1.0.0_20260911.zip`、`meeting-scheduler-v1.1.0_20260920.zip`
- 递增规则：
  - **Z 修订**（v1.0.0→v1.0.1）：改错别字、补充注释、调整示例
  - **Y 次版本**（v1.0→v1.1）：加新功能、新快捷键、新规则
  - **X 主版本**（v1→v2）：表格结构变化、通道变化、整体重构
- 工作区 `version` 字段 = **当前正在工作的版本号（= 上次发版的版本号）**
- 发版流程：**用当前 version commit + push → bump 到 +1 次版本号**（agent 自动；主版本需要手动改）

### `references/CHANGELOG.md` — 更新日志

- 分两段：**"已发布"**（按版本倒序） + **"待发布（草稿）"**（按时间顺序）
- 加/删规则/功能时，agent 自动追加一行到"待发布"段
- 发版时 agent 自动把"待发布"段合并到"已发布"段（给本次发版指定一个版本号）、清空"待发布"段、commit + push
- 用户说"展示更新日志 / 看更新日志" → 完整 Read 并显示本文档

**追加草稿条目格式**（agent 自动生成）：

```markdown
- **YYYY-MM-DD HH:MM** | 变更简述
  - 详细点 1
  - 详细点 2
```

**合并草稿到已发布**（发版时 agent 自动执行）：

```markdown
### vX.Y.Z (YYYY-MM-DD)
- (草稿合并后的条目...)
```

### 发版触发详解

**触发 A：用户手动说"更新上传"等触发词**

- agent 立即执行：
  1. 把 CHANGELOG "待发布"段所有条目合并成新的"### v1.2.0 (今天)"段，插入到"已发布"段顶部
  2. 清空"待发布"段（保留 `<!-- draft:start/end -->` 标记）
  3. `git add . && git commit -m 'v1.2.0: <变更摘要>' && git push`（**注意此时 SKILL.md frontmatter 还是 v1.2.0**）
  4. bump SKILL.md frontmatter `version` 为下一个待发版号（自动 +1 次版本，即 1.3.0）
  5. 调 `scripts/publish_to_baidu.py --force` 同步到百度网盘
  6. 告诉用户"已发版 v1.2.0，包含以下变更：..."
  7. **发版汇报（功能 7.7）**：调 `compute_size()` 输出当前技能大小 + 阈值评估，例：
     ```
     📦 已发版 v1.2.0 → 百度网盘
     📊 技能大小：55.83 KB（9 文件）
        - SKILL.md：16.39 KB
        - references/：21.17 KB（4 文件）
        - scripts/：18.09 KB（3 文件）
     ✅ 效率评估：🟢 良好（健康到 100 KB 警戒线还有 ~44 KB 余量）
     ```

**触发 B：每天 23:59 automation 定时跑**

- WorkBuddy automation 调 `scripts/publish_to_baidu.py`
- 脚本行为：
  - 先检测技能目录 hash 是否变化
  - 若**无变化** → 直接跳过（exit 0）
  - 若**有变化** → 执行与触发 A 相同的 6 步流程
- "待发布"段为空时不需要合并（自然跳过）

### 发版链路（完整 6 步）

```
1. 合并 CHANGELOG 草稿（如果"待发布"段非空）
   └─ 把草稿条目打包成 ### vX.Y.Z (date) 段
   └─ 插入到"已发布"段顶部
   └─ 清空"待发布"段
2. git add . && git commit -m 'vX.Y.Z: <变更摘要>' && git push
   └─ 此时 SKILL.md frontmatter 仍是 vX.Y.Z（已发版的版本号）
3. bump SKILL.md frontmatter version 为 X.(Y+1).0（为下次发版准备）
4. 调 package_skill.py → outputs/meeting-scheduler.zip
5. （可选）部署到 EdgeOne Pages 拿公网 URL → 百度网盘 URL 转存
6. 写本地 .last_publish.json 记录本次 hash/version/date
```

### 跨设备使用（git 同步）

- **公司电脑**（我这边）：发版时自动 push 到 https://github.com/X-huaidan/meeting-scheduler
- **家里电脑**：打开 Git Bash 执行 `cd ~/.workbuddy/skills/meeting-scheduler && git pull` 即可拉取新版
- **百度网盘**（辅助渠道）：`/软件/WorkBuddy/` 目录里也有 zip 副本，家里电脑没装 git 也能下载安装

### 工具脚本

- `scripts/publish_to_baidu.py` — 发版主脚本
  - `--status` 查看当前/上次发布状态
  - `--hash-only` 只输出当前 hash
  - `--show-draft` 显示 CHANGELOG 当前"待发布"段（确认待发内容）
  - `--force` 强制发版（即使 hash 没变）
  - 不带参数 → 自动检测：有变化才发，无变化跳过
