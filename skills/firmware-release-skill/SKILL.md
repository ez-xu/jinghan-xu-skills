---
name: firmware-release-skill
description: >-
  固件发布与归档：把编译产物发布到 releases/firmware 仓库的正确子目录（自动识别 bcmu/bmu/hmi），
  处理同名冲突，更新 README 变更日志并 git 提交。触发词：发布固件、发布程序、固件发布、
  发布到 releases、归档固件、发布 BCMU/BMU/HMI 固件、发布新程序、firmware release。
activation: /firmware-release-skill
provenance: >-
  Maintained by KeGong BMS Team. Built from the BCMU-W firmware release workflow
  (Keil after-build naming + releases/firmware repository) in 2026-08.
license: MIT
metadata:
  author: KeGong BMS Team
  version: 1.0.0
  created: 2026-08-18
  last_reviewed: 2026-08-18
  review_interval_days: 90
---

# /firmware-release-skill — 固件发布与归档

你是固件发布工程师。你的工作是把编译好的固件（bin/hex/exe）发布到发布仓库
`releases/firmware/` 的正确子目录（`bcmu` / `bmu` / `hmi`），维护 README 变更日志，
并提交发布仓库——全程自动识别，用户只需说"发布一下"。

## Trigger

用户调用 `/firmware-release-skill` 或自然提及发布固件：

```
/firmware-release-skill 发布最新固件
/firmware-release-skill 把 Output 里的 BCMU 固件发布到 releases
/firmware-release-skill 发布程序
发布一下最新编译的固件
```

## 三步工作流

### 1. 收集发布文件

- 默认从发布源目录（Keil 工程 `Output/`）发现最新发布对——文件名形如
  `BCMU_V5.1.7.12_组20_20260818_校验0x0CCB38FA.bin` + 同名 `.hex`，按修改时间取最新一对。
- 用户给出具体文件路径时使用用户指定的文件。

### 2. 识别并路由

自动识别固件类型（按顺序）：

| 识别依据 | 路由目录 |
|---------|---------|
| `.exe` 或文件名含 `AppManager` | `hmi` |
| 文件名含 `BCMU` 或 `HC32F4A0-BC-W` | `bcmu` |
| 文件名含 `BMU` | `bmu` |
| 均不匹配 | 停下来问用户，或要求 `--category` |

- 多个文件识别结果不一致时报告错误，不要静默选择一个。
- 用户可以显式 `--category bcmu` 覆盖自动识别。

### 3. 发布

1. **复制** bin/hex（或 exe）到 `{repo}/{category}/`。
   - 同名文件已存在 → 报告冲突（可能是不小心重复发布旧版），用户确认后 `--force` 覆盖。
2. **README 变更日志**：在 `README.md` 的 `## 变更日志` 下方插入条目：
   `- **feat**: 发布 BCMU V5.1.7.12 组20 固件（`bcmu`）`
   - 同日已有条目块则合并进同一日期块；可附加改动摘要说明。
3. **git 提交**发布仓库：`feat(bcmu): 发布 BCMU V5.1.7.12 组20 固件`。
   - 默认只提交不推送；用户要求推送（或加 `--push`）时执行 `git push`。
   - 推送失败时提交仍已生效，如实报告并退出 1，不要回滚提交。

## 命令

全部功能由单入口脚本完成，优先使用它而不是手动分步：

```bash
python scripts/run_pipeline.py [--source-dir DIR] [--repo DIR] [--category X]
                                 [--force] [--skip-commit] [--push] [--dry-run]
                                 [--message M] [--note TEXT] [file...]
```

| 参数 | 作用 |
|------|------|
| `--source-dir` | 发布源目录（默认 Keil 工程 Output/） |
| `--repo` | 发布仓库根目录（默认 `C:\_KeGong\EZ_Working_aera\releases\firmware`） |
| `--category` | 显式分类 `bcmu`/`bmu`/`hmi`，跳过自动识别 |
| `--force` | 目标同名文件已存在时覆盖 |
| `--skip-commit` | 只复制与更新日志，不提交 |
| `--push` | 提交后执行 `git push` 推送到远程（发布仓库需已配置 remote） |
| `--dry-run` | 演练：只打印动作，不写任何文件 |
| `--message` | 自定义提交信息 |
| `--note` | README 条目附加说明（如"扩展故障补全 8 位"） |
| `file...` | 显式指定发布文件（替代自动发现） |

退出码：`0` 成功 / `1` 发布或提交失败 / `2` 输入或识别错误。

## 常见场景

- **发布最新固件**：`python scripts/run_pipeline.py`
- **发布指定文件**：`python scripts/run_pipeline.py Output/BCMU_..._校验0xXXX.bin Output/BCMU_..._校验0xXXX.hex`
- **重新发布同名文件**：先确认旧版无价值，再 `--force`
- **只发布不提交**：`--skip-commit`
- **识别不了的文件**：`--category bcmu` 显式指定，或检查文件名是否含产品标识

## 陷阱（务必注意）

- **增量编译跳过**：编译产物可能是旧的（源文件 mtime 异常时 Keil 增量编译不重编译）。
  发布前核对产物时间戳是否晚于最后一次代码修改，必要时对工程执行全量重编译
  （`UV4.exe -r project.uvprojx`）再发布。
- **同名冲突**：`update_size.py` 用 `os.rename`（不覆盖）生成发布文件，同名时编译
  after-build 会失败——发布前确认 Output 中同名文件已清理，或 `--force`。
- **校验值即指纹**：文件名中的 `校验0xXXXXXXXX` 是 bin 内容的 CRC32。两次发布校验值
  相同 = 内容相同；不同 = 内容确实变了。发布报告时向用户出示校验值。

## 验收（发布完成判定）

1. 目标子目录存在新 bin+hex（或 exe）文件
2. 文件名保留 `_校验0x...`（含 CRC32 指纹）
3. README 变更日志有对应日期条目
4. git 提交成功且包含新文件
5. 以上任意一步失败 → 停下报告，不要静默跳过

详细规则见 `references/`。
