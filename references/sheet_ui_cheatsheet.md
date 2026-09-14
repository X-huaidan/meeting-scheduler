# 腾讯在线表格 UI 操作速查（供排会助手使用）

## 环境

| 项 | 值 |
|---|---|
| 目标文件 | `docs.qq.com/sheet/DT3Z4cGNQZmVpU2xV` |
| file_id | `DT3Z4cGNQZmVpU2xV` |
| 子表 | `时间表` (sheet_id `000001`)、`时间表2` |
| Chrome 调试端口 | `9222` |
| Python venv | `%USERPROFILE%\.workbuddy\binaries\python\envs\cdp_venv` |
| 依赖 | `websocket-client` |
| 视口参考 | 约 1092 x 711，缩放 100% |

启动调试 Chrome：

```bash
chrome.exe --remote-debugging-port=9222
```

## 连接

```python
import websocket, json, urllib.request
data = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
page = next(t for t in data if t["type"] == "page" and "docs.qq.com" in t["url"])
ws = websocket.create_connection(page["webSocketDebuggerUrl"],
                                 timeout=120, suppress_origin=True, origin=None)
```

> 不加 `suppress_origin=True` 会收到 403（Origin 校验）。

## 坐标表（视口 1092x711）

| 元素 | 坐标 |
|---|---|
| 名称框输入区 | x ≈ 8~55, y ≈ 111（点 `(30, 111)`） |
| 行号列 | **x ≈ 28**（x=40 会落到单元格区） |
| 列头（A/B/C…） | y ≈ 138 |
| 网格区起点 | y ≈ 150，第一数据行 R1 行号中心 ≈ 161（Ctrl+Home 后） |
| 行高 60pt 时的行步进 | ≈ 47 px |
| 行高 10（分隔行）渲染高度 | ≈ 18 px |

## 关键操作配方

### 选中整行
```python
click(c, 28, row_y)          # 行号列 + 行中心
```
成功标志：行号变深灰、整行浅蓝、底部"计数:N"。

### 隐藏行

> ⚠️ **2026-09-14 更正**：**首选键盘链路** —— `Ctrl+Home` → `↓` 定位 →
> `Shift+Space` 选整行 → `Shift+↓` 扩展 → **`Ctrl+Alt+9`**（`~30ms/次`）。
> 下面两条旧路径（快捷键 chord / 右键菜单）**慢 50 倍**，仅在键盘链路不可用时兜底。
> 详见 `cdp_notes.md` 第 4 节。日常批量操作用 `_j_do.py`，别手搓。

```python
# 旧路径 1：单发 chord（曾疑受输入法干扰；现在确认要用 rawKeyDown 才有效）
chord(c, "9", "Digit9", 57, CTRL | ALT)     # Ctrl+Alt+9

# 旧路径 2（兜底）：右键菜单
click(c, 28, row_y)                          # 选中
right_click(c, 28, row_y)                    # 右键出行菜单
snap(c, "menu.png")                          # 先截图看清菜单项位置
click(c, menu_x, menu_y)                     # 点"隐藏行"
```

菜单项（右键行号后）实测位置：

| 项 | 快捷键 | 相对点击点偏移 |
|---|---|---|
| 剪切 | Ctrl+X | ~(+72, -225) |
| 复制 | Ctrl+C | ~(+72, -200) |
| 粘贴 | Ctrl+V | ~(+72, -150) |
| 在上方插入 1 行 | — | ~(+72, -105) |
| 在下方插入 1 行 | — | ~(+72, -80) |
| **隐藏行** | **Ctrl+Alt+9** | **~(+72, -55)** |
| 设置行高 ▶ | — | ~(+72, -40) |
| 删除所在行 | Alt+Shift+- | ~(+72, -15) |
| 设置单元格格式 | Ctrl+1 | ~(+72, +10) |
| 合并单元格 | Alt+Shift+D | ~(+72, +35) |
| 将 [x-y] 行分为一组 | — | ~(+72, +135) |

> 菜单实际位置随点击点变化，**首次务必截图校准**。

### 取消隐藏
```python
# 选中被隐藏行**上下邻行构成的整行区间**（必须跨越整个隐藏段，多扫 30 行余量），然后：
chord(c, "9", "Digit9", 57, ALT | SHIFT)    # Alt+Shift+9
```
⚠️ **目标行自己是被隐藏行时，`ArrowDown` 永远跳不到它**（会跳过隐藏行）——
必须先锚定**隐藏段上方最近的可见行**再向下横扫。详见 `rules.md` A.9.8。

也可点击行号列左侧的 ▲/▼ 小三角图标（x ≈ 5~12）。

### 判断隐藏状态

**首选：枚举可见行取缺口**（可编程、可校验）——`Ctrl+Home` 后反复按 `↓`（自动跳过隐藏行），
收集到的行号序列里缺失的就是隐藏行；脚本用 `_rowsx.visible_rows()` / `_check.py`。
兜底：截图看行号是否跳号，例 `1, 49, 51, 54, 55, 58` → R50/R52/R53/R56/R57 被隐藏或为极窄分隔行。
⚠️ 出现"几乎全隐藏"这种极端结果时，先 `Page.reload` 复核，别急着补救（见 `rules.md` A.8.8）。

## 定位手法

| 目的 | 方法 | 可靠性 |
|---|---|---|
| 回到顶部 | 点网格后 `Ctrl+Home` | 高 |
| 逐屏滚动 | `PageDown` N 次 + 每次截图 | 高（步长非线性，必须截图确认） |
| 跳到指定单元格 | 点名称框 `(30,111)` → Ctrl+A → 输入如 `A48` → Enter | 中（视口显示位置可能异常） |
| 选行区间 | 名称框输入 `2:60` | **低**（会被解析成 A2，不可用） |

## 已知无效操作（勿尝试）

- 鼠标 wheel 滚轮事件（`Input.dispatchMouseEvent type=mouseWheel`）
- `Ctrl+A` 全选后 `Alt+Shift+9`（选中的是单元格区域而非整行）
- `Shift+PageDown`、`Ctrl+Shift+Down`、`Ctrl+Shift+End`
- `Ctrl+Shift+9`（不存在此隐藏快捷键）
- 从 DOM 读取行号/表格数据（canvas 渲染，无 table/iframe，数据在闭包内）

## 沙箱（operation_sheet）能力边界

**能用**：`getValue` `setValue` `getBackground` `setBackground` `getRowHeight` `setRowHeightsForced` `setHorizontalAlignment` `setWrapText`

**不能**：隐藏行、判断隐藏状态、顶层 return、返回表达式值（**必须 `console.log`**）

**陷阱**
- `setRowHeightsForced(r,1,60)` 实际可能只落到 45（有上限）
- 隐藏行的 `getRowHeight` 仍返回原值（如 60）→ 读行高**不能**判断是否隐藏
- `console.log` 输出过长会截断，分批 20 行
- 偶发 tcp timeout / `code -12 missing data not found` → 重试即可
