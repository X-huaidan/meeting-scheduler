#!/usr/bin/env python3
"""
publish_to_baidu.py
====================
孟总会务助手（meeting-scheduler）技能 → 百度网盘 /软件/WorkBuddy/ 一键发布

行为：
1. 计算技能目录的 content hash
2. 若与上次发布的 hash 相同 → 跳过（不浪费 token 和网盘空间）
3. 否则：
   a. 读取 SKILL.md frontmatter 的 version
   b. 用官方 package_skill.py 打包
   c. 部署 zip 到 EdgeOne Pages 拿公网 URL
   d. 调百度网盘 MCP（file_upload_by_url）转存到 /软件/WorkBuddy/
   e. 追加一行到 /软件/WorkBuddy/CHANGELOG.md（包含 version/date/hash/size/变更摘要）
   f. 写本地状态文件 .last_publish.json

调用方式：
  python publish_to_baidu.py              # 检测更新并按需发布
  python publish_to_baidu.py --force      # 强制重新发布（即使 hash 没变）
  python publish_to_baidu.py --status     # 只看当前/上次发布状态

依赖：
  - Python 3.10+ (仅标准库)
  - 环境里能调 workbuddy 的两个 MCP：
      sites_deploy    → 部署 zip 到 EdgeOne 拿 URL
      baidu_netdisk   → URL 转存到网盘、写 CHANGELOG
  这两个 MCP 在 WorkBuddy agent 进程里可直接调用；
  如果作为独立脚本跑，需要改造为对应 CLI。

退出码：
  0 = 已发布（或已是最新，无需更新）
  1 = 出错
  2 = 跳过（内容没变）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(r"C:\Users\changan\.workbuddy\skills\meeting-scheduler")
OUTPUT_DIR = Path(r"D:\WorkBuddy\2026-09-11-08-46-35\outputs")
STATE_FILE = SKILL_DIR / ".last_publish.json"
PACKAGER = Path(
    r"D:\SOFT\WorkBuddy\resources\app.asar.unpacked\resources\plugins"
    r"\workbuddy-builtin\skills\skill-creator\scripts\package_skill.py"
)
PYTHON = Path(r"C:\Users\changan\.workbuddy\binaries\python\versions\3.13.12\python.exe")

BAIDU_TARGET_DIR = "/软件/WorkBuddy"
BAIDU_CHANGELOG = f"{BAIDU_TARGET_DIR}/CHANGELOG.md"


def read_frontmatter(text: str) -> dict:
    """极简 YAML frontmatter 解析（只支持 key: value 单行）"""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def content_hash() -> str:
    """计算技能目录所有文件的 SHA1（按路径排序，排除 .last_publish.json）"""
    h = hashlib.sha1()
    for p in sorted(SKILL_DIR.rglob("*")):
        if p.is_file() and p.name != ".last_publish.json":
            h.update(str(p.relative_to(SKILL_DIR)).encode("utf-8"))
            h.update(p.read_bytes())
    return h.hexdigest()[:12]


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def package_zip(version: str) -> Path:
    """调官方 package_skill.py 打包，返回 zip 路径"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📦 打包 {SKILL_DIR.name} v{version} ...")
    subprocess.run(
        [str(PYTHON), str(PACKAGER), str(SKILL_DIR), str(OUTPUT_DIR)],
        check=True,
    )
    zip_path = OUTPUT_DIR / f"{SKILL_DIR.name}.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"打包后未找到 {zip_path}")
    return zip_path


def deploy_to_edgeone(zip_path: Path) -> str:
    """
    部署到 EdgeOne Pages 拿公网 URL。

    实际操作（agent 进程内）:
      1. 把 zip 拷贝到一个临时目录，目录里只放这一个 zip（EdgeOne 部署的是目录）
         例如: D:\\WorkBuddy\\2026-09-11-08-46-35\\.workbuddy\\publish_tmp\\meeting-scheduler\\
                → meeting-scheduler.zip
      2. 调 workbuddy_sites_deploy:
           action="deploy"
           directory=<临时目录绝对路径>
           language="static"
           port=0
           userAskedToPublish=true    # 用户在最近一条消息里授权了"打包上传"
           appName="meeting-scheduler-zip"   # 任意短名字
      3. 返回 deploy 响应里的 public URL
         （注意：EdgeOne Pages 部署是临时的，URL 在沙箱回收后会失效；
          必须在同一回合内立刻调 file_upload_by_url 把它转到百度网盘）
    """
    raise NotImplementedError("占位 — 见 docstring，由 agent 调用 workbuddy_sites_deploy")


def upload_to_baidu(public_url: str, target_name: str) -> str:
    """
    URL 转存到百度网盘 /软件/WorkBuddy/。

    实际操作（agent 进程内）:
      调 mcp__baidu-netdisk__file_upload_by_url:
        url = <EdgeOne 公开 URL>
        save_path = "/软件/WorkBuddy"
        file_name = <target_name，如 meeting-scheduler-v1.0.0_20260911.zip>
        返回 fs_id 字符串
    """
    raise NotImplementedError("占位 — 见 docstring，由 agent 调用 mcp__baidu-netdisk__file_upload_by_url")


def append_changelog(entry: dict) -> None:
    """
    追加一行到 /软件/WorkBuddy/CHANGELOG.md。

    实际操作（agent 进程内）:
      1. 先 mcp__baidu-netdisk__file_doc_list(dir="/软件/WorkBuddy") 找 CHANGELOG.md 是否存在
      2. 若存在 → 读旧内容（file_upload_by_content 没法追加，必须读+写）
         通过 mcp__baidu-netdisk__scrape_url? 不行；改用：
           a. 调 mcp__baidu-netdisk__file_semantics_search 找 fs_id
           b. 用 file_get_download_url 拿一个临时下载链接
           c. curl 读出来
         （如果太复杂，可以退化为：每次发布都覆盖整个 CHANGELOG，
          用本地的 .changelog_history.json 累积所有历史条目再写一次）
      3. 拼接新条目:
         ## v{version} ({date})
         - hash: {hash}
         - size: {size} bytes
         - file: {file_name}
         - changes: {changes}
         - ---
      4. 调 mcp__baidu-netdisk__file_upload_by_content:
          content = <完整文本>
          save_path = "/软件/WorkBuddy/CHANGELOG.md"
    """
    raise NotImplementedError("占位 — 见 docstring，由 agent 调用 mcp__baidu-netdisk__file_upload_by_content")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="强制重新发布（hash 相同也跑）")
    ap.add_argument("--status", action="store_true", help="只显示状态")
    ap.add_argument("--hash-only", action="store_true", help="只输出当前 hash")
    args = ap.parse_args()

    if not SKILL_DIR.exists():
        print(f"❌ 技能目录不存在: {SKILL_DIR}")
        sys.exit(1)

    fm_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    fm = read_frontmatter(fm_text)
    version = fm.get("version", "0.0.0")
    name = fm.get("name", SKILL_DIR.name)
    cur_hash = content_hash()

    if args.hash_only:
        print(cur_hash)
        return

    state = load_state()
    last_hash = state.get("hash")
    last_version = state.get("version")

    print(f"🔍 技能: {name} v{version}")
    print(f"   当前 hash: {cur_hash}")
    print(f"   上次发布: v{last_version or '?'}  hash={last_hash or '?'}")
    print(f"   目标网盘: {BAIDU_TARGET_DIR}/")

    if args.status:
        return

    if not args.force and last_hash == cur_hash:
        print("✅ 内容无变化，跳过发布（用 --force 强制重发）")
        sys.exit(2)

    # 下面是真正的发布流程（在 agent 进程里依次调 MCP）
    print("\n🚀 开始发布流程（agent 模式）")
    print(f"   1) 打包 v{version} ...")
    zip_path = package_zip(version)
    zip_size = zip_path.stat().st_size
    print(f"      → {zip_path}  ({zip_size} bytes)")

    print(f"   2) 部署到 EdgeOne Pages ...")
    print(f"      → (由 agent 调 workbuddy_sites_deploy)")

    print(f"   3) URL 转存到百度网盘 {BAIDU_TARGET_DIR}/ ...")
    print(f"      → (由 agent 调 mcp__baidu-netdisk__file_upload_by_url)")

    print(f"   4) 追加 CHANGELOG.md ...")
    print(f"      → (由 agent 调 mcp__baidu-netdisk__file_upload_by_content)")

    print(f"   5) 写本地状态文件 ...")
    new_state = {
        "name": name,
        "version": version,
        "hash": cur_hash,
        "zip": str(zip_path),
        "size": zip_size,
        "published_at": datetime.now().isoformat(timespec="seconds"),
        "baidu_dir": BAIDU_TARGET_DIR,
    }
    save_state(new_state)
    print(f"      → {STATE_FILE}")
    print("\n✅ 流程占位完成。agent 模式请把上述 3 个 NotImplementedError 替换为实际 MCP 调用。")


if __name__ == "__main__":
    main()
