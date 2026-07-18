# Hell Claude MVP 设计规格

日期：2026-07-18

状态：已确认，待实施计划

## 1. 项目目标

Hell Claude 收集用户遇到的 Agent 失败案例。客户端插件在用户表达不满或执行 `/hell` 时生成报告草稿；用户检查并确认后，插件向本仓库创建 GitHub Issue。GitHub Actions 校验 Issue、写入标准记录，并更新 README 和分类索引。

项目记录用户提交的案例，不把记录数量解释为经过控制变量的模型失败率。README 和后续展示页面必须说明这个统计边界。

## 2. MVP 范围

MVP 提供 Codex 和 Claude Code 的直接安装方式。两者共用报告 schema、上下文筛选、脱敏和提交逻辑，只在安装清单和 Hook 配置上保留薄适配层。

报告 schema 和 Issue Form 支持以下 Agent：

| Canonical ID | 显示名称 |
| --- | --- |
| `claude-code` | Claude Code |
| `codex` | Codex |
| `opencode` | OpenCode |
| `forgecode` | ForgeCode |
| `kimi-code` | Kimi Code |
| `trae` | Trae |
| `openclaw` | OpenClaw |
| `hermes` | Hermes |
| `pi` | Pi |

用户可以通过兼容 Skill 或 GitHub Issue Form 投稿其他七种 Agent 的案例。MVP 不为这些 Agent 提供安装包。未知 Agent 使用 `other`，记录同时保留用户输入的 `raw_name`。

MVP 不包含中央 API、数据库、OAuth 服务、其他七种 Agent 的安装包、静默投稿、综合模型评分或完整的交互式 GitHub Pages 看板。

## 3. 架构

仓库采用单仓库结构：

```text
hell-claude/
├── plugins/
│   ├── codex/
│   └── claude-code/
├── core/
│   ├── report-schema/
│   ├── context-selection/
│   ├── redaction/
│   └── submission/
├── records/
│   └── YYYY/
├── scripts/
│   ├── validate-report
│   ├── archive-issue
│   └── generate-stats
├── docs/
│   ├── install/
│   └── agents/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
└── README.md
```

系统划分为两个信任边界：

1. 用户本机：Hook 触发 Skill；Skill 选择上下文、脱敏并生成预览。用户确认前，报告内容不离开本机。
2. GitHub：仓库接收结构化 Issue。Action 将 Issue 当作不可信输入，完成校验、安全扫描、规范化、归档和统计生成。

数据流如下：

```text
Hook 或 /hell
  -> Skill 选择相关上下文
  -> 本地脱敏
  -> 用户预览、编辑、取消或确认
  -> gh issue create
  -> 未安装或未登录 gh 时打开预填 Issue 页面
  -> GitHub Action 校验和安全扫描
  -> 写入 records/YYYY/issue-N.yaml
  -> 更新 README 统计区与分类索引
```

## 4. 客户端插件

### 4.1 Hook

Hook 只判断是否需要调用 Skill。它不读取工作区、不生成报告，也不提交内容。

Hook 支持两类触发方式：

- 用户输入 `/hell` 时主动触发。
- 用户 Prompt 命中中英文负面表达、脏话或用户追加的词表时触发。

自动检测忽略大小写和常见标点，支持简单文本变体。用户可以关闭自动检测或追加本地规则。Hook 为同一任务设置冷却时间，避免连续 Prompt 反复弹出草稿；`/hell` 不受冷却限制。Hook 出错时不阻断 Agent 当前任务。

### 4.2 Skill 阶段

Skill 按固定顺序执行：

1. Detect：记录触发来源，识别当前 Agent 和已知模型信息。
2. Select：在限定窗口内建立最小证据链。
3. Redact：在本机扫描并替换敏感内容。
4. Preview：展示最终 Issue payload，允许用户编辑、取消或确认。
5. Submit：用户确认后创建 GitHub Issue。

Skill 输出结构化草稿，不生成无约束的吐槽文章。用户的原话可以作为可选字段保留，统计逻辑不使用辱骂强度。

### 4.3 上下文选择

Skill 从触发消息开始向前寻找最多 20 条 `role=user` 消息。这个上限按用户消息数量计算，不按 conversation turn、消息总数或 Agent 回复数量计算，因此不代表 20 个 turn。选择器把最早一条入选用户消息到触发消息之间的 Agent 回复、工具调用和工具结果纳入候选范围，实际候选消息总数通常大于 20。程序负责计数，不要求 Agent 判断自己的 context 长度。

扫描窗口内的 Agent 回复和工具事件不另设数量上限。最终 Issue payload 的字符上限控制上传量，选择器不会因为候选范围较大而上传全部内容。

选择器优先保留：

- 投诉前最近一次明确的用户目标；
- Agent 对目标的解释、计划或完成声明；
- 造成问题的工具调用、文件修改或命令结果；
- 用户指出错误的反馈；
- 能说明预期行为与实际行为差异的最短片段。

选择器默认移除无关的早期会话、重复输出、完整文件、大段终端日志、系统 Prompt、隐藏指令和平台内部元数据。

最终 Issue payload 使用一个较宽且可配置的字符上限。确定性程序负责超限裁剪，并按以下顺序保留内容：投诉消息、用户目标、错误表现、用户纠正。程序优先裁掉旧日志和重复片段。实现计划需要根据 GitHub 当时允许的 Issue 正文长度确定默认值，并预留安全余量。

### 4.4 本地脱敏

脱敏器至少检查：

- API key、access token、私钥和常见凭证格式；
- 邮箱、用户名和主目录；
- 绝对路径；
- Git remote 中的私有仓库地址；
- `.env` 和凭证文件内容；
- 未经用户选择的完整 diff 或文件内容。

脱敏程序用明确占位符替换命中内容，例如 `[REDACTED_TOKEN]`。用户在 Preview 阶段查看插件准备提交的全部文本。插件未经确认不得调用 GitHub、打开带报告内容的远程 URL或写入远程系统。

### 4.5 GitHub 提交

插件优先调用用户本机已登录的 `gh issue create`。文档推荐用户安装 `gh` 并执行 `gh auth login`。插件不读取、保存或传输 GitHub token。

当系统找不到 `gh`、用户尚未登录或命令权限不足时，插件生成预填 Issue URL并在浏览器中打开。用户仍需在 GitHub 页面确认提交。

## 5. Issue 与归档格式

### 5.1 Issue Form

Issue Form 和插件生成相同字段：

- schema 版本；
- Agent canonical ID 和可选原始名称；
- 模型原始值和可选规范化值；
- 客户端与插件版本，可选；
- 任务类型；
- 用户目标；
- 预期行为；
- 实际行为；
- 关键证据；
- 失败类型；
- 失败影响；
- 本地脱敏状态。

插件默认不提交用户名、仓库名和绝对路径。

### 5.2 归档记录

每个 Issue 对应一个稳定文件：`records/YYYY/issue-N.yaml`。Issue 编辑后，Action 更新同一个文件。

```yaml
id: github-issue-42
schema_version: 1
status: archived
source_issue: 42
submitted_at: "2026-07-18T12:00:00Z"

agent:
  framework: codex
  raw_name: Codex
  model: unknown
  raw_model: unknown
  client_version: null

task:
  category: debugging
  goal: "示例用户目标"
  expected: "示例预期行为"
  actual: "示例实际行为"

failure:
  categories:
    - instruction-misunderstanding
    - destructive-action
  impact:
    - file-changes
  evidence: "经过脱敏的示例证据"

privacy:
  client_redaction: true
  server_scan: passed
```

实现必须提供 versioned schema。后续版本可以迁移旧记录，但统计生成器在迁移完成前仍需读取已支持的旧版本。

### 5.3 Alias 规范化

仓库维护 Agent alias 表。每项包含 canonical ID、显示名称和常见别名，例如：

```yaml
claude-code:
  display_name: Claude Code
  aliases: [claude, claude_code, claudecode]

opencode:
  display_name: OpenCode
  aliases: [open-code, open_code]

kimi-code:
  display_name: Kimi Code
  aliases: [kimi, kimi-cli, kimi_code]
```

模型字段保留原始值，并在 alias 已知时写入规范化值。未知模型不阻止投稿或归档。

## 6. 分类体系

任务类型首版包含编码、调试、重构、解释、工具操作和 `other`。失败类型首版包含：

- `instruction-misunderstanding`
- `context-loss`
- `hallucinated-result`
- `incorrect-code`
- `destructive-action`
- `tool-misuse`
- `repetitive-loop`
- `false-success-claim`
- `privacy-or-security`
- `other`

一条记录可以包含多个失败类型。统计以规范化 Agent、规范化模型和失败类型为维度，不分析用户的措辞强度。

## 7. GitHub 自动化

Action 在 Issue 新建或编辑时执行：

1. 解析固定字段并校验 schema、必填字段和正文大小。
2. 扫描疑似密钥和高风险隐私信息。
3. 规范化 Agent、模型和分类字段。
4. 检测可能的重复记录。
5. 写入或更新对应的 YAML 文件。
6. 重新生成统计和分类索引。
7. 给 Issue 添加状态标签并回复处理结果。

Action 使用 workflow concurrency 串行处理会修改归档和统计的任务。归档脚本必须幂等；同一 Issue 和相同内容重复执行不产生额外记录或无意义 diff。

Action 不执行 Issue 中的代码，也不把 Issue 文本拼接进 shell 命令。Workflow 只申请完成任务所需的 `contents: write` 和 `issues: write` 等权限。

## 8. 状态与异常处理

仓库使用以下 Issue 标签：

- `invalid-report`：字段或 schema 不合法；
- `needs-redaction`：安全扫描发现疑似敏感内容；
- `possible-duplicate`：报告可能与已有记录重复；
- `archived`：报告已写入记录库。

`invalid-report` 和 `needs-redaction` 采用 fail-closed 行为。Action 不写入归档，并回复需要修改的字段；回复不得重复显示疑似敏感文本。用户编辑 Issue 后，Action 重新校验。

格式与安全扫描通过的报告直接归档，不等待维护者添加审核标签。重复报告仍可归档，Action 添加 `possible-duplicate` 并关联已有 Issue。

Action 暂时失败时保留 Issue，GitHub 重试或维护者重新运行 workflow 后继续处理。关闭 Issue 不删除记录。投稿者删除正文或明确提出删除请求后，维护者从当前分支删除归档内容；删除日志只保留 ID 和删除原因。若敏感内容已经进入 Git 历史，维护者按独立的历史清理流程处理。

## 9. README 与展示

README 包含人工维护区和 Action 生成区。

人工维护区包括：

1. 项目介绍和统计边界；
2. 工作流程；
3. Codex 与 Claude Code 的快速安装、手动安装、升级和卸载；
4. `gh` 安装与登录建议；
5. 自动触发、`/hell`、预览、取消和确认示例；
6. 隐私规则和删除流程；
7. 九种 Agent、失败类型和手动 Issue 投稿方式；
8. 贡献说明和路线图。

`docs/install/` 保存两种客户端的详细安装文档。README 的快速安装步骤必须足以让用户完成安装和验证。

Action 只改写以下标记内的内容：

```markdown
<!-- HELL-STATS:START -->
自动生成的统计内容
<!-- HELL-STATS:END -->
```

MVP 动态区展示总记录数、更新时间、Agent 排行、模型排行、失败类型排行和最近记录。仓库同时生成按 Agent 分类的索引页。

第二阶段使用相同 YAML 数据生成 GitHub Pages。页面可以提供筛选、趋势图、Agent 与模型交叉分析和单条记录页面。展示层只读，不反向修改归档数据。

## 10. 测试策略

项目使用虚构 fixture，禁止把真实用户会话复制到测试数据。

- Schema 测试覆盖合法报告、缺失字段、未知模型、九种 Agent alias 和旧 schema 版本。
- 脱敏测试使用虚构 token、邮箱、路径和仓库地址，验证最终 payload 不含原值。
- Action 测试覆盖 Issue 新建、编辑、重复执行、并发投稿、校验失败和修正后恢复。
- 插件端到端测试分别覆盖 Codex 和 Claude Code 的自动触发、`/hell`、取消、编辑、确认、`gh` 提交和浏览器回退。
- 统计生成器使用快照测试，防止修改代码后清空或错误重排 README 数据。

## 11. 发布要求

首个版本标记为 experimental。发布前必须完成：

- 两种客户端的安装、升级和卸载验证；
- 本地不确认不上传的端到端验证；
- 脱敏与 Action fail-closed 测试；
- README 快速安装和 `/hell` 使用验证；
- 至少一个完全虚构的归档示例；
- 项目隐私说明、内容许可和删除请求流程。

MVP 完成标准是：用户能在 Codex 或 Claude Code 中触发报告、检查并确认内容、创建 Issue；仓库能自动校验 Issue、生成稳定记录并更新 README 统计。整个流程不需要维护者手动搬运数据。
