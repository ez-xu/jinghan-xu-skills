# AGENTS.md — firmware-release-skill

## Purpose

发布固件到发布仓库：自动识别固件类型（bcmu/bmu/hmi）、复制到 releases/firmware 正确子目录、
更新 README 变更日志、git 提交。消除手动复制/命名/日志/提交的重复劳动与出错点。

## Activation triggers

用户提及以下任一意图时使用本技能：

- "发布固件 / 发布程序 / 发布新程序 / 归档固件"
- "发布到 releases / 发布到 firmware 仓库"
- "发布 BCMU / BMU / HMI 固件"
- 文件名形如 `BCMU_V5.1.7.12_组20_20260818_校验0x0CCB38FA.bin` 的发布动作

## Usage

1. **收集**：从发布源目录（默认 Keil 工程 `Output/`）发现最新发布对（bin+hex），
   或使用用户显式给出的文件。
2. **识别**：按文件名自动路由——`AppManager`/`.exe` → `hmi`；`BCMU`/`HC32F4A0-BC-W` → `bcmu`；
   `BMU` → `bmu`；识别不了时询问用户或要求 `--category`。
3. **发布**：优先运行单入口脚本：
   ```bash
   python scripts/run_pipeline.py [--source-dir DIR] [--repo DIR] [--category X]
                                    [--force] [--skip-commit] [--push] [--dry-run] [--note TEXT]
   ```
   脚本完成：复制 → README 变更日志 → git 提交 →（可选 --push 推送）。
   同名冲突需用户确认后 `--force`。
4. **报告**：向用户出示发布目标路径、文件名（含校验值）、README 条目、提交哈希（及推送结果）。

## Rules

- 识别不一致（多文件跨类别）时报错，不静默选择。
- 发布前核对产物时间戳（防增量编译跳过导致发布旧固件）。
- 发布仓库是独立 git 仓库：默认只提交不推送；用户要求推送（或 `--push`）时才推送。
- 推送失败时提交已生效——如实报告，不回滚提交。
- 失败即停，报告原因；不跳过任何一步。
- 完整规范见 `SKILL.md`；命名与识别细节见 `references/naming.md`。
