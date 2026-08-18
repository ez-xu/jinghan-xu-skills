#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""firmware-release-skill 核心库：固件类型识别、发布文件发现、发布、变更日志、提交。

只依赖 Python 标准库，Windows / Linux / macOS 通用。

命名约定（与 Brun/update_size.py 生成格式一致）：
    {Product}_V{ver}_组{group}_{date}_校验{crc}.bin / .hex
    例: BCMU_V5.1.7.12_组20_20260818_校验0x0CCB38FA.bin
识别规则（按顺序）：
    1. .exe 或文件名含 appmanager          -> hmi（人机界面安装包）
    2. 文件名含 bcmu 或 hc32f4a0-bc-w     -> bcmu（电池控制管理单元）
    3. 文件名含 bmu                        -> bmu（电池管理单元）
    4. 其余                                -> None（无法识别，需人工确认）
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 发布文件名模式：BCMU_V5.1.7.12_组20_20260818_校验0x0CCB38FA(.bin/.hex)
# 注意 group 不能含下划线，否则会吞掉后面的日期段（如 组20_20260818）
RELEASE_NAME_RE = re.compile(
    r"^(?P<product>[A-Za-z0-9-]+)_V(?P<ver>[\d.]+)_组(?P<group>[A-Za-z0-9]+)"
    r"(?:_(?P<date>\d{8}))?_校验(?P<crc>0x[0-9A-Fa-f]{8})$"
)

DEFAULT_REPO_ROOT = r"C:\_KeGong\EZ_Working_aera\releases\firmware"
DEFAULT_SOURCE_DIR = r"C:\_KeGong\EZ_Working_aera\BCMU\standard\BC-W\HC32F4A0_Lwip_V5.1.7.12\Output"

CATEGORIES = ("bcmu", "bmu", "hmi")


# ---------------------------------------------------------------------------
# 固件类型识别
# ---------------------------------------------------------------------------

def classify_firmware(path: str) -> Optional[str]:
    """识别固件属于哪个发布子目录（bcmu / bmu / hmi），无法识别返回 None。

    Args:
        path: 固件文件路径（只读文件名与扩展名）。

    Returns:
        "bcmu" / "bmu" / "hmi"，或无法识别时的 None。
    """
    name = os.path.basename(str(path)).lower()
    ext = os.path.splitext(name)[1].lower()
    if ext == ".exe" or "appmanager" in name:
        return "hmi"
    # 注意顺序：BCMU 包含 BMU 子串，必须先判 bcmu
    if "bcmu" in name or "hc32f4a0-bc-w" in name:
        return "bcmu"
    if "bmu" in name:
        return "bmu"
    return None


# ---------------------------------------------------------------------------
# 发布文件发现
# ---------------------------------------------------------------------------

def parse_release_name(filename: str) -> Optional[dict]:
    """解析发布命名（不含扩展名），返回字典或 None。

    例: BCMU_V5.1.7.12_组20_20260818_校验0x0CCB38FA
        -> {product: "BCMU", ver: "5.1.7.12", group: "20",
            date: "20260818", crc: "0x0CCB38FA"}
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    m = RELEASE_NAME_RE.match(stem)
    if not m:
        return None
    return m.groupdict()


def find_published_pairs(source_dir: str) -> List[dict]:
    """在发布源目录中发现 bin+hex 成对的发布文件，按修改时间新→旧排序。

    Args:
        source_dir: 发布源目录（Keil 工程的 Output 目录）。

    Returns:
        列表，每项 {bin, hex, info, mtime}；按 mtime 降序。
    """
    root = Path(source_dir)
    if not root.is_dir():
        return []
    entries: List[dict] = {}
    for p in root.iterdir():
        if not p.is_file():
            continue
        info = parse_release_name(p.name)
        if info is None:
            continue
        key = info["product"], info["ver"], info["group"], info.get("date"), info.get("crc")
        if key not in entries:
            entries[key] = {
                "bin": None,
                "hex": None,
                "info": info,
                "mtime": 0.0,
            }
        entry = entries[key]
        if p.suffix.lower() == ".bin":
            entry["bin"] = str(p)
        elif p.suffix.lower() == ".hex":
            entry["hex"] = str(p)
        entry["mtime"] = max(entry["mtime"], p.stat().st_mtime)
    pairs = [e for e in entries.values() if e["bin"] is not None or e["hex"] is not None]
    pairs.sort(key=lambda e: e["mtime"], reverse=True)
    return pairs


# ---------------------------------------------------------------------------
# 发布动作
# ---------------------------------------------------------------------------

def resolve_release_dir(repo_root: str, category: str) -> Path:
    """解析发布子目录并确保存在。"""
    target = Path(repo_root) / category
    target.mkdir(parents=True, exist_ok=True)
    return target


def publish_files(files: List[str], release_dir: Path, force: bool = False) -> List[str]:
    """复制固件文件到发布目录。

    Args:
        files: 待发布文件绝对路径。
        release_dir: 发布子目录。
        force: 目标已存在时覆盖（shutil.copy2 默认覆盖，此参数保留语义）。

    Returns:
        已复制到目标目录的绝对路径列表。
    """
    copied = []
    for f in files:
        src = Path(f)
        dst = release_dir / src.name
        if dst.exists() and not force:
            # 同名已存在：不覆盖，报告冲突（与 update_size.py 的 os.rename 行为一致）
            raise FileExistsError(
                f"发布目标已存在（未覆盖）：{dst}\n"
                f"如需覆盖请使用 --force，或先确认该文件是否为旧版"
            )
        shutil.copy2(str(src), str(dst))
        copied.append(str(dst))
    return copied


def build_readme_entry(info: dict, category: str, note: str = "") -> str:
    """从发布文件解析信息生成 README 变更日志条目。

    例: "- **feat**: 发布 BCMU V5.1.7.12 组20 固件（`bcmu`）"
    """
    product = info.get("product", "FW")
    ver = info.get("ver", "?")
    group = info.get("group", "?")
    detail = f"（{note}）" if note else ""
    return f"- **feat**: 发布 {product} V{ver} 组{group} 固件{detail}（`{category}`）"


def update_readme(readme_path: Path, entry: str) -> None:
    """在 README 变更日志（## 变更日志 下，<!-- 新条目 --> 下方）插入新条目。

    - 若 README 不存在则创建最小结构。
    - 若缺少变更日志栏则追加。
    - 新条目插入到变更日志标题下方（历史最新在上）。
    """
    if not readme_path.exists():
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        readme_path.write_text(
            "# 固件发布仓库\n\n## 变更日志\n\n<!-- 新条目添加在最上方 -->\n\n",
            encoding="utf-8",
        )
    text = readme_path.read_text(encoding="utf-8", errors="replace")

    today = datetime.now().strftime("%Y-%m-%d")
    block = f"### {today}\n\n{entry}\n"

    marker = "<!-- 新条目添加在最上方 -->"
    if marker in text:
        # 在 marker 行后插入新日期块；同日已有块则在其条目列表内追加
        insert_at = text.index(marker) + len(marker)
        rest = text[insert_at:]
        today_header = f"### {today}\n"
        if today_header in rest:
            # 同日块已存在：把新条目插入该块的第一条之前
            block_start = rest.index(today_header)
            lines = rest[block_start + len(today_header):].splitlines()
            # 找到第一条以 "- " 开头的行的位置
            first_item = next((i for i, ln in enumerate(lines) if ln.startswith("- ")), None)
            if first_item is not None:
                new_lines = lines[:first_item] + [entry] + lines[first_item:]
                block = today_header + "\n".join(new_lines) + "\n"
                text = text[:insert_at] + rest[:block_start] + block
            else:
                text = text[:insert_at] + rest[:block_start] + today_header + entry + "\n"
        else:
            block = "\n" + block
            text = text[:insert_at] + rest and text[:insert_at] + "\n" + block + rest
    else:
        text = text.rstrip() + "\n\n---\n\n## 变更日志\n\n<!-- 新条目添加在最上方 -->\n\n" + block
    readme_path.write_text(text, encoding="utf-8")


def git_commit(repo_dir: Path, message: str, paths: Optional[List[str]] = None) -> subprocess.CompletedProcess:
    """在发布仓库执行 git add + commit。

    Args:
        repo_dir: 发布仓库根目录（含 .git）。
        message: 提交信息。
        paths: 要暂存的路径（默认 git add -A）。

    Returns:
        subprocess.CompletedProcess；失败时抛出 CalledProcessError。
    """
    if not (repo_dir / ".git").exists():
        raise FileNotFoundError(f"不是 git 仓库：{repo_dir}")
    add_args = ["git", "add", "-A"] if paths is None else ["git", "add", *paths]
    subprocess.run(add_args, cwd=str(repo_dir), check=True, capture_output=True,
                   text=True, errors="replace")
    return subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(repo_dir),
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    )


def git_push(repo_dir: Path) -> subprocess.CompletedProcess:
    """推送发布仓库到远程（git push）。

    Args:
        repo_dir: 发布仓库根目录（含 .git）。

    Returns:
        subprocess.CompletedProcess；失败时抛出 CalledProcessError。
    """
    if not (repo_dir / ".git").exists():
        raise FileNotFoundError(f"不是 git 仓库：{repo_dir}")
    return subprocess.run(
        ["git", "push"],
        cwd=str(repo_dir),
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _categorize(files: List[str], category: Optional[str]) -> Tuple[str, List[str]]:
    """统一分类：--category 显式指定优先；否则逐个识别，结果须一致。"""
    if category:
        if category not in CATEGORIES:
            raise ValueError(f"无效分类 {category!r}，可选：{', '.join(CATEGORIES)}")
        return category, files
    cats = {classify_firmware(f) for f in files}
    none_cats = [f for f in files if classify_firmware(f) is None]
    if none_cats:
        raise ValueError(
            f"无法识别固件类型：{none_cats}\n"
            f"文件名应包含 BCMU / BMU / AppManager 等标识，或使用 --category 显式指定"
        )
    if len(cats) > 1:
        raise ValueError(
            f"文件分类不一致：{dict(zip(files, [classify_firmware(f) for f in files]))}\n"
            f"请拆分发布或使用 --category 指定"
        )
    return cats.pop(), files


def main(argv: Optional[List[str]] = None) -> int:
    # Windows 控制台默认 GBK：统一 UTF-8 输出，避免中文/替换字符编码崩溃
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="固件发布：识别类型 → 复制到发布仓库 → 更新变更日志 → git 提交",
    )
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR,
                        help=f"发布源目录（默认 {DEFAULT_SOURCE_DIR}）")
    parser.add_argument("--repo", default=DEFAULT_REPO_ROOT,
                        help=f"发布仓库根目录（默认 {DEFAULT_REPO_ROOT}）")
    parser.add_argument("--category", choices=CATEGORIES, default=None,
                        help="显式指定发布子目录（默认自动识别）")
    parser.add_argument("--force", action="store_true",
                        help="目标同名文件存在时覆盖")
    parser.add_argument("--skip-commit", action="store_true",
                        help="只复制与更新日志，不执行 git 提交")
    parser.add_argument("--push", action="store_true",
                        help="提交后执行 git push 推送到远程（发布仓库需已配置远程）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印将要执行的动作，不写任何文件")
    parser.add_argument("--message", default=None,
                        help="自定义 git 提交信息（默认按命名生成）")
    parser.add_argument("--note", default="",
                        help="README 条目补充说明（如改动摘要）")
    parser.add_argument("files", nargs="*",
                        help="显式指定发布文件；缺省时自动取 --source-dir 中最新发布对")
    args = parser.parse_args(argv)

    # 1) 确定发布文件
    files: List[str] = list(args.files)
    if not files:
        pairs = find_published_pairs(args.source_dir)
        if not pairs:
            print(f"[ERROR] {args.source_dir} 中未发现发布文件（{RELEASE_NAME_RE.pattern}）")
            return 2
        latest = pairs[0]
        picked = [latest["bin"], latest["hex"]]
        files = [p for p in picked if p]
        print(f"[INFO] 取最新发布文件（{datetime.fromtimestamp(latest['mtime']):%Y-%m-%d %H:%M}）：")
        for f in files:
            print(f"  {os.path.basename(f)}")

    # 2) 识别分类
    try:
        category, files = _categorize(files, args.category)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 2
    print(f"[INFO] 分类：{category}（{', '.join(os.path.basename(f) for f in files)}）")

    # 3) 复制
    release_dir = resolve_release_dir(args.repo, category)
    if args.dry_run:
        for f in files:
            print(f"[DRY-RUN] 复制 {f} -> {release_dir / os.path.basename(f)}")
    else:
        try:
            publish_files(files, release_dir, force=args.force)
        except FileExistsError as exc:
            print(f"[ERROR] {exc}")
            return 1
        print(f"[OK] 已复制 {len(files)} 个文件到 {release_dir}")

    # 4) 变更日志
    readme_path = Path(args.repo) / "README.md"
    entry = build_readme_entry(parse_release_name(files[0]) or {}, category, args.note)
    print(f"[INFO] README 条目：{entry}")
    if not args.dry_run:
        update_readme(readme_path, entry)

    # 5) 提交
    if not args.skip_commit and not args.dry_run:
        info = parse_release_name(files[0]) or {}
        message = args.message or (
            f"feat({category}): 发布 {info.get('product', 'FW')} "
            f"V{info.get('ver', '?')} 组{info.get('group', '?')} 固件"
        )
        try:
            result = git_commit(Path(args.repo), message)
            print(f"[OK] 已提交：{message}")
            print((result.stdout or "").strip()[-400:])
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(f"[WARN] git 提交失败：{exc}")
            return 1

        # 6) 推送（可选）
        if args.push:
            try:
                push_result = git_push(Path(args.repo))
                print(f"[OK] 已推送到远程：{(push_result.stdout or '').strip()[-200:] or '(无输出)'}")
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                print(f"[WARN] git 推送失败（提交已生效，未推送）：{exc}")
                return 1
    elif args.dry_run:
        print("[DRY-RUN] 跳过复制/日志/提交"
              + ("/推送" if args.push else ""))

    print(f"[DONE] 发布完成 -> {release_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
