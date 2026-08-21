# Audit Skill Conflicts

`audit-skill-conflicts` 是一个面向 Codex 和 Agent Skills 的只读冲突审计 Skill。它会逐对比较指定范围内的 Skill，并明确展示冲突双方、冲突类型、证据位置、触发条件、严重级别和修复建议。

> A read-only auditor for detecting and explaining pairwise conflicts across Codex and Agent Skills.

## 能发现什么

- Skill 名称或调用身份冲突
- 触发描述重叠且工作流不兼容
- `必须`、`禁止`、`always`、`never` 等强制指令相互矛盾
- 工具选择、权限和外部副作用冲突
- 输出格式、目标路径和共享资源冲突
- 执行顺序、停止条件和生命周期冲突
- 插件、运行时、版本或环境依赖冲突

内容相似并不自动等于冲突。扫描脚本只生成候选和完整配对清单，最终报告会通过语义核实区分：

- 已确认冲突
- 仅在特定条件下发生的冲突
- 可以共存的普通重叠

## 特点

- **逐对覆盖**：记录已检查的 Skill 数量和组合数量。
- **双边证据**：每条冲突同时引用两个 Skill 的文件与行号。
- **严重级别**：使用 Critical、High、Medium 和 Low 分级。
- **按 Skill 汇总**：每个 Skill 都会列出关联冲突；没有冲突则显示 `none`。
- **默认只读**：审计过程不会编辑、安装、禁用或删除其他 Skill。
- **中英文兼容**：扫描器可以提取中文和英文的限制性指令。

## 安装

在 Codex 中使用内置的 `skill-installer`：

```text
$skill-installer install https://github.com/1841175465li-byte/turbo-goggles/tree/main/skills/audit-skill-conflicts
```

也可以把 `skills/audit-skill-conflicts` 目录复制到个人 Codex Skills 目录。安装后如果没有立即显示，请开启新任务或重启 Codex。

## 使用

检查当前可发现的 Skill：

```text
$audit-skill-conflicts 检查当前可用的所有 Skill，并用中文列出它们之间的冲突。
```

检查指定目录：

```text
$audit-skill-conflicts 检查 D:\my-skills 中所有 Skill 的冲突。
```

只关注高风险冲突：

```text
$audit-skill-conflicts 审计这些 Skill，只展开 High 和 Critical 冲突，但仍报告完整覆盖数量。
```

## 输出内容

报告包含：

1. 扫描根目录、Skill 数量、配对数量和严重级别统计
2. 冲突总表
3. 每项冲突的双边证据、触发条件和最小修复建议
4. 每个 Skill 对应的冲突索引
5. 无法读取的路径、解析警告和其他覆盖限制

## 工作原理

1. `scripts/scan_skill_conflicts.py` 发现 `SKILL.md`，读取名称、描述、调用策略和限制性指令。
2. 扫描器生成全部无序 Skill 配对，并标记同名、描述重叠和调用策略差异等候选信号。
3. Skill 根据 `references/conflict-taxonomy.md` 进行语义判断。
4. 只有无法同时满足的要求才会确认为冲突；单纯相似不会被当成证据。

扫描器仅依赖 Python 标准库，建议使用 Python 3.10 或更高版本。

## 仓库结构

```text
skills/audit-skill-conflicts/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── conflict-taxonomy.md
└── scripts/
    └── scan_skill_conflicts.py
```

## 安全说明

该 Skill 默认只做读取和报告。修复建议不会自动应用；只有用户另外明确授权后，才应修改其他 Skill。

