# firmware-release-skill

固件发布与归档技能：把编译产物发布到 `releases/firmware` 仓库的正确子目录
（自动识别 `bcmu` / `bmu` / `hmi`），处理同名冲突，更新 README 变更日志并 git 提交。

## 功能

- **自动识别路由**：`BCMU_*` / `HC32F4A0-BC-W-*` → `bcmu`；`AppManager*.exe` → `hmi`；`BMU_*` → `bmu`；无法识别时报错而不是瞎猜
- **最新发布发现**：自动从 Keil 工程 `Output/` 目录取最新 bin+hex 发布对
- **同名冲突保护**：目标文件已存在时拒绝覆盖（默认），确认后 `--force`
- **变更日志**：自动在 README `## 变更日志` 插入条目（同日合并、含校验值指纹）
- **git 提交**：按命名自动生成提交信息并提交发布仓库

## 安装

### Claude Code（推荐）

```bash
# 直接安装到用户技能目录
cp -R firmware-release-skill ~/.claude/skills/firmware-release-skill

# 或使用自带的跨平台安装器
./firmware-release-skill/install.sh
```

### 插件方式（Claude Code）

```bash
# 在技能目录内
cd firmware-release-skill
/plugin marketplace add .
```

### GitHub Copilot CLI

```bash
cp -R firmware-release-skill ~/.copilot/skills/firmware-release-skill
```

### Cursor（仅项目级）

```bash
cp -R firmware-release-skill .cursor/skills/firmware-release-skill
```

### 其他平台

运行 `./firmware-release-skill/install.sh --all` 自动检测并安装到所有已检测到的平台
（Codex CLI / Gemini CLI / Goose / OpenCode / Cline / Roo Code / Windsurf / Trae 等），
或指定 `--platform <name>`。

## 使用

安装后在任意对话中：

```
/firmware-release-skill 发布最新固件
/firmware-release-skill 把 BCMU 固件发布到 releases
```

或直接运行脚本：

```bash
cd firmware-release-skill
python scripts/run_pipeline.py                       # 默认源目录最新发布
python scripts/run_pipeline.py --dry-run             # 演练
python scripts/run_pipeline.py --source-dir DIR --repo DIR --note "改动说明"
```

## 验证与自检

```bash
cd firmware-release-skill
python scripts/run_evals.py          # 回归门禁（识别/解析/路由检查）
python scripts/check_pipeline.py .   # 管线完整性检查
```

## 目录结构

```
firmware-release-skill/
├── SKILL.md                # 技能主文件（触发与三步工作流）
├── AGENTS.md               # AAIF 指令文件（跨工具可达）
├── scripts/
│   ├── release.py          # 核心库：识别/发现/发布/日志/提交
│   ├── run_pipeline.py     # 单入口编排
│   ├── run_evals.py        # eval 运行器
│   └── evolve.py           # 自维护工具链
├── references/             # 命名规则与边界情况详解
├── assets/                 # README 条目模板
├── evals/                  # 回归门禁 spec 与 golden cases
├── .claude-plugin/         # Claude Code 插件清单
└── install.sh              # 跨平台安装器
```

## 许可

MIT
