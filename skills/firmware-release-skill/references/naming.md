# 命名与识别规则

## 发布文件命名（协议）

发布文件名由 Keil 工程 after-build 脚本 `Brun/update_size.py` 生成，格式固定：

```
{Product}_V{ver}_组{group}_{date}_校验{crc}.bin
{Product}_V{ver}_组{group}_{date}_校验{crc}.hex
```

- `Product`：产品名，从 bin 配置区读取，如 `BCMU`
- `ver`：版本号，从配置区读取并规范化（`010A00010 → 1.A.0.10`），如 `5.1.7.12`
- `group`：组号（组网/项目标识），从配置区读取，如 `20`
- `date`：构建日期 `YYYYMMDD`
- `crc`：bin 内容的 CRC32（大端 hex），如 `0x0CCB38FA`

旧格式（2026-07 前）无日期段：`BCMU_V5.1.7.12_组19_校验0xA04CF297.hex`。
解析器兼容两种格式（日期段可选）。

**校验值的意义**：`crc` 是 bin 内容指纹。两次发布校验值相同 = 内容相同；
不同 = 内容确实变了。发布报告中必须出示校验值。

## 固件类型识别（路由到 releases/firmware/{category}）

| 依据（文件名，不区分大小写） | 分类 | 发布目录 |
|----------------------------|------|---------|
| `.exe` 扩展名，或含 `AppManager` | hmi | `releases/firmware/hmi/` |
| 含 `BCMU` 或 `HC32F4A0-BC-W` | bcmu | `releases/firmware/bcmu/` |
| 含 `BMU`（排除 BCMU） | bmu | `releases/firmware/bmu/` |
| 均不匹配 | 未知 | 询问用户或 `--category` |

**判断顺序必须固定**：`BCMU` 是 `BMU` 的子串，先判 bcmu 再判 bmu。

历史文件名参考：
- `BCMU_V5.1.7.12_组20_20260818_校验0x0CCB38FA.bin` → bcmu
- `HC32F4A0-BC-W-V5.1.7.11.200466408天青德博.hex` → bcmu（旧命名，含 BC-W）
- `AppManagerSetup_1.0.3.21_release.exe` → hmi
- `S32K144-BC-H-xinguobiao.21.hex` → **无法自动识别**（无 BCMU/BMU/AppManager 标识，需人工确认，S32K144 也是 BCMU 产品线）

## 发布仓库布局

```
releases/firmware/
├── bcmu/          # 电池控制管理单元固件（bin + hex 成对）
├── bmu/           # 电池管理单元固件（当前为空，预留）
├── hmi/           # 人机界面安装包（exe）
└── README.md      # 变更日志（新条目在最上方）
```

## README 变更日志格式

```markdown
## 变更日志

<!-- 新条目添加在最上方 -->

### 2026-08-18

- **feat**: 发布 BCMU V5.1.7.12 组20 固件（扩展故障补全 8 位）（`bcmu`）

### 2026-07-01
...
```

- 同一日期的多次发布合并进同一 `### 日期` 块
- 条目格式：`- **feat**: 发布 {Product} V{ver} 组{group} 固件（可选说明）（`{category}`）`
- 提交信息惯例：`feat({category}): 发布 {Product} V{ver} 组{group} 固件`
