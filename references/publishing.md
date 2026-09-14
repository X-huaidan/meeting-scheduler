# 发版与版本管理（自我管理）

> 2026-09-14 从 SKILL.md 拆出。只在**发版**或**问版本/大小**时读，日常排会不需要。
> SKILL.md 里保留 5 行摘要 + 指针。

---

## 1. 核心理念：编辑即时落盘，发版批量进行

- **改文档**（加/删规则、加/删功能、修 SKILL.md）→ **立即落盘 + 追加 CHANGELOG "待发布"草稿**
  ——**不发版、不 push**
- **发版**（合并草稿 + 打包 + push）→ **只在两个条件触发时执行**：
  - 条件 A：用户说"**更新上传 / 打包上传 / 上传到网盘/上传到GitHub**"（手动触发，立即跑）
  - 条件 B：每天 23:59 的 automation 定时跑一次（自动触发，无变化则跳过）
- 这样避免每次微调都刷一版，但累积到一定量又能集中发版

---

## 2. 版本号约定

- frontmatter 必填 `version: X.Y.Z`
- 文件名格式：`meeting-scheduler-v{X.Y.Z}_{YYYYMMDD}.zip`
- 例：`meeting-scheduler-v1.0.0_20260911.zip`、`meeting-scheduler-v1.3.0_20260914.zip`
- 递增规则：
  - **Z 修订**（v1.0.0→v1.0.1）：改错别字、补充注释、调整示例
  - **Y 次版本**（v1.0→v1.1）：加新功能、新快捷键、新规则
  - **X 主版本**（v1→v2）：表格结构变化、通道变化、整体重构
- 工作区 `version` 字段 = **当前正在工作的版本号（= 下次发版要用的号）**
- 发版流程：**用当前 version commit + push → bump 到 +1 次版本号**（agent 自动；主版本需手动改）

---

## 3. `references/CHANGELOG.md` 的两段结构

- **"已发布"**（按版本倒序）+ **"待发布（草稿）"**（按时间顺序）
- 加/删规则/功能时，agent 自动追加一条到"待发布"段
- 发版时 agent 自动把"待发布"段合并到"已发布"段（给本次发版指定版本号）、清空"待发布"段、commit + push
- 用户说"展示更新日志 / 看更新日志" → **完整 Read 并显示**本文档

**追加草稿条目格式**：

```markdown
- **YYYY-MM-DD HH:MM** | 变更简述
  - 详细点 1
  - 详细点 2
```

**合并草稿到已发布**（发版时）：

```markdown
### vX.Y.Z (YYYY-MM-DD)
- (草稿合并后的条目...)
```

---

## 4. 发版 6 步

```
1. 合并 CHANGELOG 草稿（如果"待发布"段非空）
   └─ 把草稿条目打包成 ### vX.Y.Z (date) 段
   └─ 插入到"已发布"段顶部
   └─ 清空"待发布"段（保留 <!-- draft:start/end --> 标记）
2. git add -A && git commit -m 'vX.Y.Z: <变更摘要>' && git push
   └─ 此时 SKILL.md frontmatter 仍是 vX.Y.Z（已发版的版本号）
3. bump SKILL.md frontmatter version 为 X.(Y+1).0（为下次发版准备）
4. 打包 → outputs/meeting-scheduler.zip
5. （可选）同步百度网盘 / EdgeOne Pages
6. 写本地 .last_publish.json 记录本次 hash/version/date
```

### ⚠️ 本机 git 的两个坑

1. **`git` 不在默认 PATH 里**，且 WorkBuddy 沙箱 bash 环境异常（`ls`/`dirname`/`head`
   都 command not found）。用绝对路径：
   ```
   C:\Users\changan\.workbuddy\binaries\PortableGit\versions\1.2.0\cmd\git.exe
   ```
   并把 `cmd` 与 `mingw64/bin` 加进 PATH 后调用。
2. **远端只走 SSH，HTTPS 走不通**（企业代理连 `github.com:443` 超时）：
   ```
   origin  git@github.com:X-huaidan/meeting-scheduler.git
   ```
   依赖 `~/.ssh/github_meeting_scheduler`（`~/.ssh/config` 里配 `IdentityFile` + `IdentitiesOnly yes`）。
   ⚠️ **不要用 HTTPS + PAT**。

---

## 5. 发版触发详解

### 触发 A：用户手动说"更新上传"等触发词

- agent 立即执行：
  1. 把 CHANGELOG "待发布"段合并成新的 `### vX.Y.Z (今天)` 段，插到"已发布"段顶部
  2. 清空"待发布"段（保留标记）
  3. `git add -A && git commit && git push`（此时 frontmatter 还是 vX.Y.Z）
  4. bump SKILL.md frontmatter `version` 为下一个待发版号（+1 次版本）
  5. 调 `scripts/publish_to_baidu.py --force` 同步网盘（可选）
  6. 告诉用户"已发版 vX.Y.Z，包含以下变更：..."
  7. **发版汇报（功能 7.7）**：调 `compute_size()` 输出当前技能大小 + 阈值评估，例：
     ```
     📦 已发版 v1.3.0 → 百度网盘
     📊 技能大小：14.9 KB（SKILL.md）
     ✅ 效率评估：🟢 健康
     ```

### 触发 B：每天 23:59 automation 定时跑

- 调 `scripts/publish_to_baidu.py`
- 脚本行为：先检测技能目录 hash → 无变化则跳过（exit 0）；有变化则走触发 A 相同的流程
- "待发布"段为空时自然跳过

---

## 6. 常用命令

```bash
python scripts/publish_to_baidu.py --status       # 当前/上次发布状态
python scripts/publish_to_baidu.py --hash-only    # 只输出当前 hash
python scripts/publish_to_baidu.py --show-draft   # 显示 CHANGELOG 当前"待发布"段
python scripts/publish_to_baidu.py --size         # 技能大小 + 阈值评估（不发版）
python scripts/publish_to_baidu.py --force        # 强制发版（即使 hash 没变）
python scripts/publish_to_baidu.py                # 不带参数：有变化才发，无变化跳过
```

---

## 7. 文档体积纪律（2026-09-14 立）

**SKILL.md 每次触发都会被完整读入，是唯一有"每轮成本"的文件；references 只在需要时读。**

原则：

1. **SKILL.md 只放**：红线 · 开工闸门 · 触发词 · 通道结论 · 工作流骨架 · 文档地图 · 指针
   ——**目标 ≤ 15 KB**
2. **细节一律进 references**（rules / cdp_notes / features / cheatsheet / publishing / CHANGELOG）
3. **禁止重复**：同一段内容只允许有一个权威位置，别处只放指针
   （2026-09-14 SKILL.md 曾因此涨到 41 KB，其中约一半是 references 的副本）
4. 新增内容前先问："这是不是在别处已经写过？"——是就只加指针
5. 每次发版汇报时看 `--size` 的 SKILL.md 单项：**超过 30 KB 就必须拆**

阈值表（总大小 / SKILL.md 双口径）见 `references/features.md` 7.7。

---

## 8. 跨设备使用（git 同步）

- **公司电脑**（本机）：发版时 push 到 `git@github.com:X-huaidan/meeting-scheduler.git`
- **家里电脑**：Git Bash 执行 `cd ~/.workbuddy/skills/meeting-scheduler && git pull`
- **百度网盘**（辅助渠道）：`/软件/WorkBuddy/` 目录里有 zip 副本，家里电脑没装 git 也能装
