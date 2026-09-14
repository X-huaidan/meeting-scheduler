# 通道能力与实测陷阱（api_caps）

> 目的：**别再重复试探**。每次新会话都可能重踩一遍"沙箱到底支持什么"，
> 2026-09-14 就为 `hideRows` / `copyTo` / `getBackground` 白花了 4 轮工具调用。
> 本文件是**实测结论**，不是推测。改动通道行为后请重跑文末的探测脚本并更新本表。

---

## 0. ⚠️ 五条最容易踩的结论（先看这个）

| # | 结论 | 后果 |
|---|---|---|
| 1 | **样式读取不可信：只有第 1 行返回真值，第 2 行及以后一律 `#000000`** | 用沙箱"看底色有没有丢"**等于没看**；样式校验只能走截图 + `_pix.py` |
| 2 | **沙箱没有任何 hideRows / showRows / isRowHiddenByUser** | 收版（隐藏行）**只能**走 CDP 键盘链路 |
| 3 | **`set_cell_style` 必须一次传全 7 个属性**，缺的会被重置为默认 | 少传参数 = 抹掉底色（2026-09-14 表头事故的根因） |
| 4 | **读值要用 `sheet.get_cell_data` 批量读**，不要在沙箱写 `getRange()` 循环 | 见 §2.1 —— 这是**最大的一处人为浪费**，不是工具限制 |
| 5 | **OCR 看图需要腾讯文档 VIP**，当前账号报错 `400014` | 截图识别只能靠 agent 自身视觉 + `_png.py` 切片，见 §7 |

---

## 1. 两条通道分工

| 通道 | 实现 | 干什么 |
|---|---|---|
| **A. MCP** | `sheet.*` 工具 + `sheet.operation_sheet`（裸 JS 沙箱） | 读值、读结构、写值、写样式、行列增删/尺寸、合并 |
| **B. CDP** | 带调试端口的 Chrome + 键盘链路（`_kb.py` / `_j_do.py`） | **隐藏/取消隐藏行**、判断隐藏状态、**截图 + 像素校验** |

**决策表**

| 任务 | 走哪条 |
|---|---|
| 读单元格值 / 读行高 / 读合并块 | A |
| 写单元格值 | A（`sheet.set_range_value` 批量） |
| 写样式（底色/对齐/换行） | A（`sheet.set_cell_style`，**全 7 参数**） |
| **验证样式是否被保留** | **B**（截图 + `_pix.py`）—— A 不可信 |
| 隐藏行 / 取消隐藏 | **B** |
| 判断某行当前是否隐藏 | **B** |

---

## 2. 通道 A：MCP 工具层

**有**（`sheet.` 前缀）：
`get_sheet_info` · `get_cell_data` · `get_merged_cells` ·
`set_cell_value` · `set_range_value` · `set_cell_style` ·
`clear_range_all` / `clear_range_cells` / `clear_range_style` ·
`insert_dimension` / `delete_dimension` / `set_dimension_size` ·
`merge_cell` / `unmerge_cell` · `add_sheet` / `rename_sheet` / `delete_sheet` ·
`set_freeze` / `unset_freeze` · `set_filter` / `remove_filter` ·
`set_link` / `clear_link` · `insert_image` · `operation_sheet`（裸 JS）

**没有**：任何 hide / unhide rows / columns 接口。**行可见性完全不归通道 A 管。**

---

### 2.1 📌 批量读值：`get_cell_data` 是唯一正确的打开方式（2026-09-14 实测）

**别再在沙箱里写 `getRange(r,c).getValue()` 循环了。** 那是 2026-09-14 之前的老习惯，
一次几十行的表要跑一大圈脚本，纯粹的人为浪费。

实测：一次调用 `get_cell_data{start_row:0, end_row:70, start_col:1, end_col:9, return_csv:true}`
**直接拿到完整 71 行 × 9 列的 CSV**，内容完好（含周几标记行、合并行留空、换行文本）。

| 场景 | 用什么 | 说明 |
|---|---|---|
| **读值**（绝大多数情况） | `get_cell_data` + `return_csv:true` | ✅ **一次拿全表**，首选 |
| 读公式源串 | `get_cell_data` + `include_formula:true` | 需 `return_csv:false` |
| **读行高 / 行可见性** | 沙箱 JS `getRowHeight()` | ⚠️ `get_cell_data` **不返回行高**，只有这时才用 JS 循环 |
| 读结构（合并块） | `get_merged_cells` | 独立于值读取 |

**决策口诀：先 `get_cell_data` 拿全表的"是什么"，行高只在需要的时候单独问。**

> 反例（本技能 SKILL.md 里曾长期挂着这段，2026-09-14 已删）：
> ```javascript
> for (var r = 14; r <= 30; r++) {           // ❌ 别这样逐行读
>   for (var c = 2; c <= 9; c++) vals.push(sh.getRange(r, c).getValue());
> }
> ```
> 这段只在你需要**行高**时才合理（`getRowHeight`），纯读值时完全多余。

---

## 3. 通道 A：沙箱 JS（SpreadsheetApp 子集）

这是**阉割版** Apps Script，很多标准方法不存在。

### Sheet 对象

| 有 | `getRowHeight` `setRowHeight` `getRowHeights` `setRowHeights` `getColumnWidth` `setColumnWidth` `getColumnWidths` `setColumnWidths` `getRange` |
|---|---|
| **没有** | `hideRows` `showRows` `hideRow` `showRow` `hideColumns` `showColumns` `isRowHiddenByUser` `isRowHiddenByFilter` |
| **没有** | 所有**单元格级** getter —— Sheet 上 `getValue` `getValues` `getBackground` `getFontColor` `getFontSize` `getVerticalAlignment`… **全是 undefined**，必须 `getRange()` 之后再调 |

### Range 对象

**有**

```
值     getValue  getValues  setValue  setValues
底色   getBackground  getBackgrounds  setBackground  setBackgrounds
字色   getFontColor  getFontColors  setFontColor  setFontColors
字号   getFontSize   getFontSizes   setFontSize
        setFontWeight(只写)   setHorizontalAlignment(只写)   setWrapText(只写)
格式   getNumberFormat  setNumberFormat  clearFormat  setBorder
结构   merge  breakApart  getRow  getColumn
```

**没有**

```
copyTo                 ← 整行"连格式一起复制"不可用
getHorizontalAlignment(s)  ← 读不到水平对齐
getVerticalAlignment(s)    ← 读不到垂直对齐
getWrapText                ← 读不到换行设置
getFontWeight              ← 读不到粗体
clearContent               ← 清空单元格请用 setValue("")
getMergedRanges  offset  getA1Notation  getWidth  getHeight  getDisplayValue
```

### ⚠️ 头号陷阱：样式读取只对第 1 行有效

2026-09-14 实测（同一张表，同一批单元格）：

| 单元格 | `getBackground()` | `getFontColor()` | 判定 |
|---|---|---|---|
| R1C2（冻结首行 · "日期"） | `#2972F4` | `#FFFFFF` | ✅ 真值（蓝底白字） |
| R2C2 · R2C3 · R2C7 | `#000000` | `#000000` | ❌ 假 |
| R14C2 · R17C2 · R18C2 · R19C3 · R20C3 | `#000000` | `#000000` | ❌ 假 |

**读法**：冻结行（第 1 行）走的是真实数据，**第 2 行及以后恒返回 `#000000`**。

> 所以「写完样式后用沙箱回读一遍确认底色还在」是**假安全** —— 它永远返回
> `#000000`，既不能证明保留、也不能证明丢失。2026-09-11 整表被清、2026-09-14
> 表头格式被抹，两次事故当场都没被发现，就是因为当时拿沙箱值当校验依据。

**正确做法**：样式相关的一切校验 → `Page.reload` 后截图 → `_pix.py` 像素分析。

### 其它已知坑

- `Range` 无 `clearContent` → 清空格子用 `rg.setValue("")`
- `Range` 无 `copyTo` → **整行下移**只能"把值写进下方预格式化空行"，格式靠原有的
  （好在 R20 这类行本来就是同高的预格式化空行，见 `rules.md` B.8）
- 行高**不能**用来判断隐藏 —— 已隐藏的 R29/R33-39 仍报告真实高度

---

## 4. 通道 B：CDP

- 隐藏行 `Ctrl+Alt+9` / 取消隐藏 `Alt+Shift+9`（经 `_j_do.py` 批量算子，自带隐藏集自校验）
- 截图 + 像素分析：`_shot.py` 截图，`_pix.py` 量底色/对齐/文字区间
- 完整坐标、脚本清单、键盘原语 → `cdp_notes.md`

**依赖**（换机需复查）：
- `%USERPROFILE%\.workbuddy\binaries\python\envs\default` + `websocket-client`
- `_pix.py` **需要 Pillow**（2026-09-14 本机已装 12.3.0，装一次约 5 分钟）；
  `_png.py` **零依赖**，不需要 Pillow

---

## 5. 常用 JS 片段库（直接抄，别重写）

**① 读某段的值 + 行高（每次开工必做）**
```javascript
var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('时间表');
var out = [];
for (var r = 14; r <= 30; r++) {          // 每次 ≤20 行，太长会被截断
  var v = [];
  for (var c = 2; c <= 9; c++) v.push(sh.getRange(r, c).getValue());
  out.push('R' + r + ' h=' + sh.getRowHeight(r) + ' | ' + v.join(' ~ '));
}
console.log(out.join('\n'));
```

**② 扫全表会议名称（判断某场会是否已存在）**
```javascript
var v = sh.getRange(1, 2, 110, 3).getValues();   // B/C/D 列
var out = [];
for (var i = 0; i < v.length; i++)
  if (v[i][1] || v[i][2]) out.push('R' + (i + 1) + ': [' + v[i][0] + '] ' + v[i][1] + ' / ' + v[i][2]);
console.log(out.join('\n'));
```

**③ 能力探测（只需重跑这一条，就能刷新本文件的表格）**
```javascript
var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('时间表');
function t(f){ try { return String(f()); } catch(e) { return 'ERR:'+e.message; } }
var rg = sh.getRange(2,2);
var rangeFns = ['copyTo','getBackground','getBackgrounds','setBackgrounds','getFontColor',
  'getFontColors','getFontSize','setFontWeight','getHorizontalAlignment','getVerticalAlignment',
  'getWrapText','getValues','setValues','setValue','clearContent','clearFormat','setBorder',
  'merge','breakApart','getNumberFormat'];
var have = [], miss = [];
for (var i=0;i<rangeFns.length;i++)
  (typeof rg[rangeFns[i]] === 'function' ? have : miss).push(rangeFns[i]);
console.log('Range HAS: ' + have.join(', '));
console.log('Range MISSING: ' + miss.join(', '));
console.log('R1 bg=' + t(function(){return sh.getRange(1,2).getBackground();})
          + ' | R2 bg=' + t(function(){return sh.getRange(2,2).getBackground();}));
```
> 判定标准：**R1 返回真实色值、R2 返回 `#000000`** → 样式读取仍不可信（即结论 1 仍成立）。

---

**④ 批写一整场会（首选 `sheet.set_range_value`，一次调用写完 C~I）**

`row` / `col` 都是 **1-based 表格坐标**：B=2 · C=3 · D=4 · E=5 · F=6 · G=7 · H=8 · I=9

```
values = [
  {row: 17, col: 2, value_type: "STRING", string_value: "09:00-10:00"},
  {row: 17, col: 3, value_type: "STRING", string_value: "深蓝S05四季度社媒传播方案"},
  {row: 17, col: 4, value_type: "STRING", string_value: "思路讨论"},
  {row: 17, col: 5, value_type: "STRING", string_value: "M503"},
  {row: 17, col: 6, value_type: "STRING", string_value: "孟总"},
  {row: 17, col: 7, value_type: "STRING", string_value: "唐婧瑶、何颖"},
  {row: 17, col: 8, value_type: "STRING", string_value: "何颖"}
]
```

- **一次调用写完一场会的全部字段**，不要逐格 `set_cell_value`
- 空字段（如无议程）**跳过不传**，不要传空串
- 多场会合并到同一个 `values` 数组里一次写完（本次 2 场会 12 个字段 = 1 次调用）
- ⚠️ **写入只用 `set_range_value` / `set_cell_value`；不要顺手调 `set_cell_style`**
  （全量覆盖会抹底色，见 §0 结论 3）
- 写完立刻用片段 **①** 回读校验

---

## 6. OCR 看图：**需要腾讯文档 VIP**（2026-09-14 实测）

工具清单里**确实有** OCR（`ocr.extract` / `ocr.toexcel`），曾经以为可以用来直接读会议截图、
省掉整套识图流程。实测结论：**当前账号用不了**。

```
code:400014  msg: vip required
  https://docs.qq.com/vip?immediate_buy=1&part_aid=agent_mcp
```

### 排查过程（别重踩）

调真实截图（24 KB base64）时报的是：

```
code:400001  msg: image_base64 must be a pure base64 string (no URL, no data URI prefix)
```

这个错具有**误导性** —— 它让人以为是传输格式问题，实际不是。用一张 100% 纯净的
1×1 最小 PNG（`iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ...`）重试后，真正的错误才浮出来
（`400014 vip required`）。**排错方法：先用最小素材排除参数问题，再看真实错误码。**

### 结论与替代路径

| 想做的事 | 能不能靠 MCP OCR | 替代 |
|---|---|---|
| 读**腾讯在线表格**里的数据 | ✅ 不需要 OCR | `get_cell_data`（§2.1） |
| 识别**本地截图**（企微通知等） | ❌ 需 VIP | **`_png.py auto` 切片 + 多模态直读**（见 `cdp_notes.md` §6） |
| 把识别结果落成结构化表格 | ❌ 需 VIP | 同上，然后 `set_range_value` 写入 |

> **重要区分**：源截图是**本地 PNG 文件**，跟腾讯文档连接器本来就不是一个东西 ——
> 连接器读写的是"腾讯文档里的在线表格"，它对本地图片文件一无所知。
> 所以"识别截图"这件事，**即使开了 VIP 也只是多一条可选捷径，不是连接器该管的职责**。

---

## 7. 变更记录

- **2026-09-14** 首次建立。实测于「孟总会议行程表」`DT3Z4cGNQZmVpU2xV` / 子表「时间表」。
- **2026-09-14 (2)** 补 §2.1 批量读值（纠正"逐行 getRange 循环"的老习惯）、
  §6 OCR 需 VIP 的实测结论；§0 结论增至 5 条。
