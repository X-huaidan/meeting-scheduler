---
name: meeting-scheduler
version: 1.1.0
description: 孟总会议行程表（腾讯文档在线表格 docs.qq.com/sheet/DT3Z4cGNQZmVpU2xV，子表"时间表"）的排会与排版技能，中文别名"孟总会务助手"。当用户要求把会议信息（文字或截图）写入该行程表、调整会议行底色/对齐/换行、隐藏或展开每天的行（Ctrl+Alt+9 隐藏行 / Alt+Shift+9 取消隐藏）、按"每天只显示有会议的行"整理版面、展示或修改排会规则（references/rules.md）、展示或修改功能清单（references/features.md）时使用。也适用于任何需要在腾讯在线表格中精确模拟 UI 操作（CDP 接管 Chrome）的场景。
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

## 何时触发

- "帮我安排会议 / 把这个会议加进行程表 / 排会"
- "调整底色 / 对齐 / 换行"
- "隐藏行 / 展开行 / 取消隐藏"
- 提供会议截图或文字，要求写入
- "展示排会规则 / 看看规则 / 显示规则" → 读取并展示 `references/rules.md`
- "展示功能 / 看看功能 / 功能清单 / 这个技能能干啥" → 读取并展示 `references/features.md`
- "增加/删除一条规则" → 编辑 `references/rules.md`
- "增加/删除一个功能" → 编辑 `references/features.md`

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

**修改**：用户说"加规则/删规则/改规则" → 引导用户说出具体内容 → Edit `references/rules.md` 对应章节

### `references/features.md` — 功能清单

- 包含技能当前所有功能
- 7 个分类：会议录入 / 会议读取 / 版面整理 / 表格结构 / 跨设备同步 / 工具脚本 / 自我管理
- 每个功能有编号，方便引用

**展示**：用户说"展示功能 / 看看功能 / 功能清单" → **完整 Read 并显示** `references/features.md` 全文

**修改**：用户说"加功能/删功能" → 引导用户说出具体内容 → Edit `references/features.md` 对应章节

### 为什么分离到独立文档

1. **易维护**：规则/功能变更只改一个文件
2. **易查阅**：用户能直接 cat 文件，不依赖 agent
3. **权威唯一**：避免 SKILL.md 正文与外部文档不一致
4. **可共享**：规则文档可以单独发给其他人 review

---

## 注意事项

- **破坏性操作前先确认基线**：隐藏行会改变用户看到的版面，操作前先截图留档
- **不要用 `setRowHeightsForced` 模拟隐藏**（见上）
- 腾讯文档 MCP 对这张表偶发 `code -12 missing data not found` 或 tcp timeout —— **直接重试**，通常第二次成功
- sandbox 的日志会截断长输出，**分批读取**
- 若 CDP 端口不通，请用户重新以调试端口启动 Chrome：`chrome.exe --remote-debugging-port=9222`

---

## 版本管理与自动发布到百度网盘

### 版本号约定

- frontmatter 必填 `version: X.Y.Z`
- 文件名格式：`meeting-scheduler-v{X.Y.Z}_{YYYYMMDD}.zip`
- 例：`meeting-scheduler-v1.0.0_20260911.zip`、`meeting-scheduler-v1.1.0_20260920.zip`
- 递增规则：
  - **Z 修订**（v1.0.0→v1.0.1）：改错别字、补充注释、调整示例
  - **Y 次版本**（v1.0→v1.1）：加新功能、新快捷键、新规则
  - **X 主版本**（v1→v2）：表格结构变化、通道变化、整体重构

### 发布触发

**自动触发（每天 23:59）：**
- WorkBuddy automation 定时跑 `scripts/publish_to_baidu.py`
- 脚本计算技能目录 SHA1，与 `.last_publish.json` 里的 hash 对比
- 若有变化 → 走完整发布；无变化 → 跳过

**手动触发（用户说"打包上传 / 打包发到网盘 / 上传到网盘"）：**
- agent 立即调 `scripts/publish_to_baidu.py --force` 跑一次

### 发布链路（5 步）

```
1. 计算 content hash
   └─ 变化？─否─→ 跳过退出
2. 调 package_skill.py → outputs/meeting-scheduler.zip
3. 调 workbuddy_sites_deploy 部署到 EdgeOne Pages 拿公网 URL
   └─ EdgeOne 沙箱是临时的，必须在同一回合内转存到网盘
4. 调 mcp__baidu-netdisk__file_upload_by_url
   └─ url=<EdgeOne URL>  save_path=/软件/WorkBuddy  file_name=vX.Y.Z_YYYYMMDD.zip
5. 调 mcp__baidu-netdisk__file_upload_by_content 覆盖 /软件/WorkBuddy/CHANGELOG.md
   └─ 内容 = 旧日志（如果存在）+ 本次新条目
最后写本地 .last_publish.json 记录本次 hash/version/date
```

### 跨设备使用

- 家里的电脑打开百度网盘客户端 → `/软件/WorkBuddy/`
- 下载 `meeting-scheduler-vX.Y.Z_YYYYMMDD.zip`
- WorkBuddy 客户端 → 技能 → 右上角 + → "上传第三方 Skill（zip）" → 选这个 zip → 安装
- 新版本发布后 CHANGELOG.md 会显示变更摘要，便于判断要不要更新
