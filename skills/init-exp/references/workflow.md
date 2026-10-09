# 实验协作协议（实验特有部分）

> **通用协作协议已转调 `agent-team` skill。** 本文件只保留 init-exp 特有的内容：目标验收、实验 git 纪律、任务状态机细节。角色职责、上下文契约、生命周期、会话恢复、上报通道、预算熔断、行为记录 → 见 agent-team 的对应 references。

## 职责分工

- **main（lead 角色）**：加载 `contracts/main.md`（八段契约，覆盖原 team-lead 职责）。编辑 `goals.md` 与 `tasks.md`；分配任务给其他角色；核验 `results/`、更新任务状态、判定完成或退回。
- **worker（builder 角色）**：从 `tasks.md` 领取任务；执行并把产出写入 `results/`；日志写入 `logs/`；完成后更新 `tasks.md` 状态。
- **logs / monitor 窗口（观察者）**：不执行任务，观察运行状态，异常时在 `notes.md` 记录。

协同靠共享文件系统 + **只向上的上报通道**：窗口之间不直接互相打字，任务与状态通过 `goals.md` / `tasks.md` / `notes.md` / `results/` 传递；过程中的疑问由 worker 用 `teamctl.py escalate` 上报给 main，由 main 用 `ask` 处理。**不支持横向 peer 通信。**

**决策权分层（关键）**：worker **不能直接问用户**，必须经 main 上报。只有 main 能通过人机通道（IM）向用户提问。这样用户只需面对一个对话方，不会被 N 个 agent 同时问住。

契约规范（八段结构、Inputs 只给路径、Do-Not-Touch、Stop Conditions）见 agent-team 的 `references/context-protocol.md`；main 契约追加第 9 段「向用户确认」。

## 循环流程

### 1. 制定目标

main 在 `goals.md` 中写入目标。**每条目标必须包含可验证的验收标准**：

```markdown
## G1: <目标简述>

- 状态: open
- 验收标准:
  - [ ] <可验证的条件 1>
  - [ ] <可验证的条件 2>
```

### 2. 分配任务

main 在 `tasks.md` 中为每个目标拆解任务，标注负责人**角色**与关联目标：

```markdown
| ID | 任务 | 负责人(角色) | 关联目标 | 模式 | 状态 | 完成标准 | 产出 |
|----|------|--------------|----------|------|------|----------|------|
| T1 | <任务> | worker | G1 | ephemeral | pending | <可验证标准> | results/... |
```

> 表头用「负责人(角色)」而非「负责人(窗口)」——角色名跨 session 稳定，窗口名可能变。分配后 agent 读取自己的契约即知任务；需要提示时在该窗口执行 `cat tasks.md` 提示其领取。

### 3. 执行

worker 领取任务后更新状态为 `in_progress`，执行，产出放入 `results/`。完成后：

1. 更新 `tasks.md` 对应行状态 → `done`。
2. 在 `notes.md` 追加一条记录（时间戳 + 角色名 + 做了什么 + 结果摘要）。
3. 写 checkpoint 到 `logs/checkpoints/<role>-<task>.md`（**retire 前的强制动作**，格式见 agent-team 的 `observability.md`）。
4. 登事件：`teamctl.py record --role worker --event task_done --task T1 --summary "..."`。
5. 若撞到契约未覆盖的不确定点 → `escalate` 上报 main，不要自行拍板、不要横向问 peer。

### 4. 完成判定（main）

main 依据 `tasks.md` 中的**完成标准**与 `goals.md` 中的**验收标准**，**实际打开 `results/` 里的产物**核验：

- **满足** → 状态保持 `done`；若是目标最后一个任务，把 `goals.md` 中该目标状态改为 `done`，勾选验收标准。
- **不满足** → 状态改为 `needs-revision`，在备注写明**具体缺陷**（文件 + 行号），并登记重试计数：
  ```bash
  scripts/teamctl.py attempts bump --role worker --task T1 --reason "具体缺陷"
  scripts/teamctl.py attempts judge --task T1
  ```
  按渐进建议处置（≤3 次同角色可继续 / 4-6 次改契约或缩范围 / ≥7 次换角色或拆任务）。
- 全部目标 `done` → 汇总结果，宣告实验完成。

**不凭主观感觉，也不接受 agent 的文字自述作为完成依据**——必须打开产物文件核验。

**涉及代码的核验补充**：凡任务产出涉及编程开发，main 除功能核验外还必须验收工程规范：

1. **开发规范**：代码遵循所使用语言/框架的典型工程实践，并沿用项目既有约定。
2. **Lint 通过**：运行项目声明的 lint / typecheck / format 校验命令并确认通过（无显式命令则运行对应 linter CLI，如 ruff、eslint、biome、golangci-lint、clippy）。
3. **无逃逸手段**：检查是否存在掩盖 lint 问题的 `# noqa`、`@ts-ignore`、`eslint-disable` 等；存在时必须能在备注给出站得住脚的理由。
4. **reviewer 独立性**（若设了 reviewer）：确认 reviewer ≠ builder；要更高独立性档位时（不同 CLI/模型）应在派活时就指定，见 agent-team 的 `org-model.md`。
5. 任一不满足 →判定 `needs-revision` 并明确列出规范缺陷。

### 5. 向用户确认（main 专属，不得自行发挥）

**这一步是实验里防止 AI 擅自决策的关键闸门。** main 遇到以下情形**必须**通过人机通道问用户，不能自己拍板：

| 情形 | 为什么不能自决 |
| --- | --- |
| 契约/文档未定义的语义 | 猜错会静默污染下游结果 |
| 需超出实验约定的决策（如改指标定义、换数据集） | 越界就是擅自改实验 |
| 不可逆操作（删数据、覆盖已有结果、force push） | 不可回滚 |
| 显著影响成本或范围的决定（加数据源、扩实验矩阵） | 影响用户的钱和时间 |
| 同一任务退回 >=7 次 | 该问的是「这实验还该不该继续做」，main 无权决定 |
| 验收标准与用户真实意图明显不符 | main 的理解可能整体跑偏 |
| 实验依据的外部前提缺失（如 baseline 论文数据拿不到） | 前提变了，结论就变了 |

**提问纪律**（详见 agent-team 的 `references/human-channel.md`）：

- **一次问一件事**，不要打包三个问题（用户只会答最显眼那个）
- **必须给 2-3 个选项**，不要开放式提问。开放式把思考成本推回给用户，选项式只需判断
- **附背景与代价**：当前卡在哪、已试过什么、每个选项的代价分别是什么
- **blocker 级停下等答复**，不得继续推进相关任务
- **答复必须落盘** `decisions.md` + `im answer` 记录事件——否则 main 冷重启会重新讨论同一问题

```bash
scripts/teamctl.py --team <name> im ask --task T3 --severity blocker \
  --question "baseline 数据源用论文原表还是自己重跑？" \
  --options "论文原表（快，但口径与我们的预处理不一致）|自己重跑（一致，要 6 小时）|混合，缺失项用论文值补（折中，需标注来源）" \
  --background "论文原表用的是不同版本的 tokenizer，直接对比会失真" \
  --default "混合，缺失项用论文值补" --auto-after-min 120
```

未配置 IM 通道时（`channel: none`）：main **在当前对话里直接问用户**，规则完全不变。**不要因为没有 IM 通道就放宽自行决定的尺度。**

### 6. 复盘（可选）

实验收尾时，main 在 `notes.md` 末尾写入：结论、踩坑、可复用经验。**决策类内容写进 `decisions.md`**（init-exp 骨架里的决策账本，由 adopt 补位），格式见 agent-team 的 `observability.md`。

## Git 提交纪律

每个实验目录都是**独立 git 仓库**，文本文件与进展全部用 git 管理。**重大进展或独立进展必须单独 commit**，禁止把多个不相关进展混在一个 commit 里。

- **什么算一个 commit**：每个独立/可验证的进展单元。例如：
  - 一份目标/任务设定（goals/tasks/contracts 更新）
  - 一次实验运行的完整结果（某轮跑通、某组参数结果产出）
  - 一个独立结论/分析
  - 对既有结果的一次修正
- **何时必须 commit**：所有执行者完成一个任务、main 判定一个目标达成、产生一版可复现的结果时。
- **commit message 规范**：一句话说明该进展（动词开头 + 对象），如：
  - `run: 完成 baseline 首次运行，结果写入 results/`
  - `goal: G2 达成，验收标准全部通过`
  - `fix: 修正数据预处理漏样本问题`
  - `dec: 分页参数固定 page/page_size（见 decisions.md D3）`
- **执行规则**：
  1. main 完成目标设定后即 commit（goals.md / tasks.md / contracts / AGENTS.md 变更）。
  2. worker 完成任务并确认产出落盘后，commit 自己的成果；若共用同一仓库则先 `git pull`/`git fetch` 再提交（避免覆盖他人）。
  3. main 判定目标达成同 commit，保证每个里程碑可回退、可追溯。

> 若执行者无法 commit（如权限/冲突），把待提交变更留在工作区并在 `notes.md` 说明，由 main 统一提交。

## 状态机

```
pending ──► in_progress ──► done
                ▲              │
                └── needs-revision ◄──┘
```

任务状态与会话状态是两套独立状态机，不要混用。会话生命周期（常驻/用完即弃、会话恢复）见 agent-team 的 `lifecycle.md`。

## 冲突与异常

- 多 worker 并发时，**一个任务同一时刻只允许一个负责人角色**。
- 发现任务被重复领取：后领取者主动释放，状态回 pending。
- 任务长时间卡住 `in_progress`：agent 应 `escalate` 上报，main 在备注标注卡住原因，决定接手、拆分或取消。
- **不要让 agent 反复重试卡住的事**——每重试一次就往会话里灌无用上下文，加速污染。配合预算熔断：卡住超过软超时即 checkpoint 收摊等 main 答复，不要硬撑到硬上限（见 agent-team 的 `governance.md`）。
- 环境问题（命令缺失、权限、网络）：负责人先在 `notes.md` 记录，再尝试自行解决或 escalate 给 main。