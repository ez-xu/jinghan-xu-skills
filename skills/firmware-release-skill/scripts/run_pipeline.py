#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""firmware-release-skill 单入口编排器。

固件发布管线的执行顺序编码在此（而不是交给 agent 从散文里推理）：
    1. 发现发布文件（源目录最新发布对，或用户显式指定）
    2. 识别固件类型（bcmu / bmu / hmi，自动路由）
    3. 复制到发布仓库对应子目录（同名冲突可 --force 覆盖）
    4. 更新 README 变更日志
    5. git 提交发布仓库

用法：
    python3 scripts/run_pipeline.py                       # 默认源目录最新发布
    python3 scripts/run_pipeline.py --source-dir DIR      # 指定源目录
    python3 scripts/run_pipeline.py --repo DIR --category bcmu
    python3 scripts/run_pipeline.py <file.bin> <file.hex> # 显式文件
    python3 scripts/run_pipeline.py --dry-run             # 演练
    python3 scripts/run_pipeline.py --skip-commit         # 不提交

退出码：0 成功；1 发布/提交失败；2 输入或识别错误。
"""

from __future__ import annotations

import sys

import release


def main(argv=None):
    """直接透传 release.main —— 管线顺序已在 release.main 内固定。"""
    return release.main(argv)


if __name__ == "__main__":
    sys.exit(main())
