# -*- coding: utf-8 -*-
"""周日新一周清理：清空周一~周五 R3~R60 的会议字段 + 展开所有行。

⚠️ 安全约定（2026-09-11 事故后重写）
--------------------------------------
**绝对不要**用「点 Name box → Ctrl+A → 输入范围 → Enter → Delete」这条路径来清空表格。
Name box 的点击经常抢不到焦点（Enter 也不一定提交），此时 Ctrl+A 会选中**整张表**，
紧接着的 Delete 就会把整张子表清空——这正是 2026-09-11 全表数据丢失的原因。

因此本脚本被拆成两段，各走各的可靠通道：

  1. 清空数据  →  用腾讯文档 MCP `sheet.clear_range_cells`（API，精确到 C3:I60）
                  由 agent 在对话里调用，**不由本脚本用键盘模拟**。
  2. 展开隐藏行 →  `weekly_unhide.py`（点行号 + Shift 点行号 + 右键 +
                  DOM 定位「取消隐藏行」菜单项）。

用法:
    python weekly_cleanup.py           # 只做第 2 步（展开隐藏行）
    python weekly_cleanup.py --check   # 只体检：报告当前隐藏行，不做任何修改

调用方（agent）标准流程：
    # (a) 先清空上一周的数据（MCP，安全）
    #     sheet.clear_range_cells(file_id="DT3Z4cGNQZmVpU2xV",
    #                             sheet_id="000001", range="C3:I60")
    # (b) 再展开隐藏行
    #     python weekly_cleanup.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNHIDE = os.path.join(HERE, "weekly_unhide.py")
PY = sys.executable


def main():
    args = sys.argv[1:]
    check = "--check" in args

    print("=" * 60)
    print("第一步（清空 C3:I60）请用 MCP sheet.clear_range_cells 完成，")
    print("不要用键盘模拟 Delete —— 见本文件顶部说明。")
    print("=" * 60)

    cmd = [PY, UNHIDE] + (["--report"] if check else [])
    print("-> ", " ".join(cmd))
    rc = subprocess.call(cmd)
    if rc == 0 and not check:
        print("隐藏行已全部展开。")
    return rc


if __name__ == "__main__":
    sys.exit(main())
