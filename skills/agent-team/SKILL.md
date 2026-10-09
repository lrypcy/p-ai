---
name: agent-team
description: "创建并管理多 Agent 团队协作模式。把一个复杂任务拆成多个分工明确的 agent（lead 主导者、researcher 调研、builder 执行、reviewer 评审、recorder 记录），为每个 agent 定制刚好够用的上下文契约（Context Contract），按长连接/用完即弃两种模式管理 agent 生命周期，支持会话恢复（session resume），提供自下而上的上报通道（横向 peer 通信不支持）、预算熔断与渐进式重试换手，并对所有 agent 行为做全量结构化记录。当用户要求组建 agent 团队/agent team、多 agent 协作、多个 agent 分工干活、agent 团队常驻或临时拉起、恢复某个 agent 会话、查看 agent 团队工作记录时使用。Also use when the user asks to spin up a multi-agent team with roles, delegate work across agents, keep agents resident vs ephemeral, resume an agent session, or audit agent team activity."
agent_created: true
---

# agent-team

组建并运营一支多Agent 团队：定角色 → 签上下文契约 → 定工作模式 → 拉起/收摊 → 留痕可追溯。

## 核心原则

**1. 角色 ≠ 窗口。** 角色是职责（一份 Context Contract），窗口是运行载体（tmux window）。同一个角色可以在需要时拉起、用完即关；不要把"有窗口"当成"必须一直在"。

**2. 上下文按契约发放，不做广播。** 每个 agent 只拿到完成自己任务所需的最小充分上下文。团队信息通过**共享黑板文件**交换（O(N)），不通过 agent 之间互相对话（O(N²)）。

**3. 通道只向上，不横向。** 需要其他 agent 的信息时只能 escalate 给 lead，由 lead 中转。横向 peer 通信一律不支持（会制造多源真相与互相覆盖）。

**4. 上下文可丢失，产出不可丢失。** agent 进程是易失的，会话可能恢复失败。所有结论、决策、产出必须落盘到 `results/` 与 `decisions.md`，**不能只存在于某个 agent 的对话历史里**。

**5. 默认用完即弃，常驻需要理由。** 默认 checkpoint-then-retire；resident 必须在 roster 里写明理由。

**6. 完成判定看产出，不看自述。** lead 依据任务契约里的完成标准核验 `results/` 里的实际产物，不接受"我做好了"的口头/文字汇报作为完成依据。

**7. 拿不准就问用户，不要自己发挥。** lead 遇到契约未定义的语义、超出授权的决策、不可逆操作、目标本身不合理等情形，**必须**通过人机通道（IM / 对话）向用户确认，附背景、代价与 2-3 个选项。只有契约已明确授权的实现细节才可自行决定。

**8. 预算与时间是硬约束。** 任务超软超时写 checkpoint 收摊，超硬上限必须熔断上报；反复退回用渐进式换手，不搞"2 次即死"的一刀切。

## 团队工作空间骨架

```
ROOT/<team-name>/            # git init 的独立仓库
├── TEAM.md           # 团队章程：目标、角色 roster、协作协议、工作模式、窗口布局
├── tasks.md          # 任务看板：契约表（每行含完成标准、负责人角色、模式）
├── contracts/        # 每个角色的上下文契约 *.md —— 角色专属，启动时投放
│   ├── lead.md
│   ├── researcher.md
│   └── builder.md
├── decisions.md      # 决策账本：为什么这么选（不只是做了什么）
├── notes.md# 时间戳协作流水
├── results/          # 产出物落地目录
├── logs/             # 行为记录与治理状态
│   ├── <role>.pipe.log         # L1 原始窗口输出
│   ├── events.jsonl            # L2 结构化事件
│   ├── inbox.jsonl             # 上报队列（worker → lead）
│   ├── attempts.jsonl          # 退回重试计数
│   ├── budget.json             # 预算额度
│   ├── sessions.json           # 会话登记与 resume 命令
│   ├── im-channel.json         # 人机通道配置（或继承全局 ~/.workbuddy/agent-team/im.json）
│   └── checkpoints/            # 生命周期检查点
├── .agents/          # agent 专属 skill（可选，如 lead 加载 team-lead skill）
└── .gitignore
```

骨架由 `scripts/create_team.sh` 生成，已有文件不覆盖。

## 工作流

### Step 0：已有 init-exp 实验目录？先 adopt

若目标目录已经由 `init-exp` 的 `init_experiment.sh` 生成（特征：有 `AGENTS.md` + `tasks.md`），**不要重建骨架**，改用适配：

```bash
scripts/teamctl.py --team <team> adopt --exp-dir <ROOT>/<exp-name> --lead-alias main
```

`adopt` 幂等地补齐 `logs/` 下的七个管控文件（events / inbox / attempts / sessions / budget / checkpoints）与 `contracts/` 目录，并生成 `TEAM-MAPPING.md` 命名映射草案（`main`→`lead`、`worker`→`builder`、负责人列填角色名而非窗口名）。**映射草案必须人工审校后合并进 `AGENTS.md`**——脚本不做语义改写。详见 `references/adopt-init-exp.md`。

### Step 1：明确任务与交付物

先问清三件事（**不可猜测**）：

1. **最终要交付什么**（一个 PR / 一份报告 / 一个可运行 demo / 一个结论）
2. **怎么算做完了**（可验证的完成标准清单）
3. **团队工作目录** `ROOT`（绝对路径；已存在的项目目录可直接用）

任务交付物不清楚就不要开团——没有完成标准的团队会无限返工。

### Step 2：选规模梯度与角色

按 `references/org-model.md` 选梯度。**默认从最小梯度开始**，不够再加：

| 梯度 | 构成 | 适用 |
| --- | --- | --- |
| `solo` | 1 个 agent 全干 | 任务单一、上下文自洽、无需并行 |
| `duo` | lead + 1 个执行 | 需要有人核验，但不需要分工调研 |
| `squad` | lead + 2~4 个执行/调研/评审 | 大多数真实任务 |
| `council` | N 个平级专家 + 1 裁决者 | 方案取舍、技术选型争论 |

角色库与职责边界矩阵见 `references/org-model.md`。角色**按需**增加，不要为了凑齐角色表而设岗。

### Step 3：为每个角色签上下文契约

**这是整个 skill 的核心动作。** 每个角色一份 `contracts/<role>.md`，由 lead 撰写，包含八段：

```markdown
# 契约：<role>

## 1. Identity       你是谁、代号、职责范围（一句话）
## 2. Objective      本轮要达成的目标（引用 tasks.md 的任务号）
## 3. Task           具体做什么、边界在哪
## 4. Do-Not-Touch    禁止修改的文件/目录、禁止决策的领域
## 5. Deliverables   产出落到哪个路径、什么格式、命名规范
## 6. Inputs         上游产出在哪、该读哪些文件（给路径，不给全文）
## 7. Done Criteria  可验证的完成标准（lead 会据此核验）
## 8. Stop Conditions 什么情况必须停下并上报，而不是硬猜
```

撰写规则详见 `references/context-protocol.md`。四条硬约束：

- **给路径，不给全文**：第6 段只列文件路径与阅读顺序，让 agent 自己去读；把大段代码/文档粘贴进契约会挤爆上下文且容易过期。
- **Do-Not-Touch 必须写**：多agent 并发最大的失败模式是抢改同一个文件。
- **Done Criteria 必须可核验**："代码写好了"不可核验，"`pytest -q` 全绿且 `results/bench.json` 有 200 条记录"可核验。
- **必须声明上报通道**：第 8 段之后追加"遇到契约未覆盖的不确定点，用 `escalate` 找 lead，不要横向问 peer"。

### Step 4：决定工作模式、预算与人机通道

**工作模式**：对每个角色标注 `resident`（长连接）或 `ephemeral`（用完即弃），判据见 `references/lifecycle.md`。速查：

| 选 resident 当 | 选 ephemeral 当 |
| --- | --- |
| 该 agent 是决策中枢（lead/架构） | 任务边界清晰、一次性 |
| 连续任务共享大上下文，重读成本 >> 保活成本 | 上下文是"任务包"不是"累积知识" |
| 需要保持外部连接（训练进程/dev server/watch） | 只需要产出物，不需要连续性 |
| 任务是"守着"（等 CI / 等实验结果） | 探索性、发散性、不确定结果 |
| 需频繁打断追问 | 并行 fan-out（10 个方向各查一次） |

默认中间态：**checkpoint-then-retire**——干完活写 checkpoint、登事件、退出 agent，tmux 窗口留着当 shell 备查。

**预算**：同时定额度，防止 agent 空转或无限重试（详见 `references/governance.md`）：

```bash
scripts/teamctl.py budget set --per-task-min 60 --hard-cap-min 120 --total-min 600
scripts/teamctl.py budget set --role researcher --role-min 180# 慢角色单独放宽
```

**人机通道（Team Leader ↔ 用户）**——**先查再配，幂等**：

```bash
scripts/teamctl.py im check     # ← 必须先跑这个
```

| check 结果 | 动作 |
| --- | --- |
| 已配置且验证过 | **直接复用，不要问用户**，打印通道信息后继续 |
| 有全局配置 | **询问用户是否复用**，不要重新问一遍 webhook |
| 存在但未验证 | 跑一次 `im test`；失败则询问是否重配 |
| 不存在 | 走新配置（见下） |

新配置时依次确认五件事（**每件给默认建议，不要逐条追问**）：是否配置（默认是）/ 通道类型（问用户实际用哪个，不要猜）/ 能力档位（默认 **L1**）/ **是否有可用的飞书自建应用**（仅当考虑 L2 时问）/ webhook URL（**必须由用户提供，绝不凭空编造**）：

```bash
scripts/teamctl.py im init --channel feishu --tier L1 \
  --notify-cmd 'curl -s -X POST -H "Content-Type: application/json" -d @- "$FEISHU_WEBHOOK"' \
  --webhook-env FEISHU_WEBHOOK
scripts/teamctl.py im test    # 验证失败不算配置成功
```

**第 4 项（L2 前提）怎么问**：直接问「**你有没有已经建好的飞书自建应用？**」，不要问"要不要我帮你建"——建应用要在飞书开放平台手工操作，本 skill 做不了。有则继续确认 `app_id`/`app_secret` 放哪（只记环境变量名）、消息权限是否已申请、接入方式（**推荐长连接**，可绕开公网穿透）；没有或不确定则建议留在 L1，如实说明 L2 的门槛。

```bash
# 有可用的飞书应用 → 登记 L2 意图（入向尚未实现，命令会明确告知）
scripts/teamctl.py im init --channel feishu --tier L2 \
  --notify-cmd 'curl -s -X POST -H "Content-Type: application/json" -d @- "$FEISHU_WEBHOOK"' \
  --webhook-env FEISHU_WEBHOOK \
  --app-id-env FEISHU_APP_ID --app-secret-env FEISHU_APP_SECRET \
  --app-verify-mode longconn
```

**必须诚实告知用户 IM 的能力边界**：群机器人 webhook **只能发不能收**，用户在群里回复 lead 收不到。默认推荐 **L1**（webhook 提问 + `tmux attach` 回答），零额外依赖且响应最快。**L2 入向接收当前尚未实现**——即使登记了 L2，用户回复仍需 `tmux attach`，`teamctl.py` 会在 check/status/ask 三处都提示这一点，不要对外宣称"可在飞书里直接回复"。企业微信有群机器人 webhook，**个人微信没有合规方案**。详见 `references/human-channel.md`。

### Step 5：拉起团队

```bash
scripts/create_team.sh -n <team-name> -r <root> -l <gradient> -m <resident,ephemeral...>
```

脚本生成骨架、初始 `TEAM.md`、`.gitignore`、`git init`。**tmux session 按需单独创建**（团队目录可以先建好、agent 后拉起）：

```bash
tmux new-session -d -s at-<team-name> -n <role>
tmux send-keys -t at-<team-name>:<role> "<agent-cli>" Enter
```

agent CLI 的启动与 session 恢复命令见 `references/agent-cli.md`。**不要擅自attach**，把attach 命令告诉用户即可。

启动每个 agent 后立刻做三件事：**开 pipe**（`tmux pipe-pane`，行为记录的前提）、**投放契约**（让它读 `contracts/<role>.md` + `TEAM.md` 里自己那一行）、**登记会话**（`session set`）。

### Step 6：生命周期管理（运行期）

lead 在运行期的核心动作循环，完整状态机与操作见 `references/lifecycle.md`。

```
spawn ──► active ──► checkpoint ──► retire ──► dormant ──► resume ──► active
             │                      │
             └───── block/escalate ─┘（卡住：只向上 escalate 给 lead）
```

**lead 每个任务周期必做五件事**：

1. **派活前**：`teamctl.py record --role <role> --event task_start --task <T1>`
2. **处理上报**：`teamctl.py ask list` —— 只处理 `blocker` 级，其余按需
3. **需要用户决策时**：`teamctl.py im ask`（详见下方「lead 向用户确认」）
4. **agent 汇报时**：`teamctl.py record --role <role> --event task_done --task <T1> --summary "..."`
5. **判定时**：`teamctl.py status --team <name>` 拉全量视图，然后**实际打开 `results/` 里的产物核验**，再决定 `done` / `needs-revision`

#### lead 向用户确认（不得自行发挥）

**必须问的情形**（ask-required）：契约未定义的语义 / 需超出契约授权的决策 / 不可逆操作（删数据、改配置、对外发布、force push）/ 显著影响范围或成本的决定 / 重试 ≥7 次 / 目标本身不合理 / 需要用户提供上下文才能继续。

**可以自己定**（ask-omitted）：契约 Task 段已覆盖的实现细节 / Do-Not-Touch 与 Done Criteria 已界定的技术选型 / 可逆的局部调整 / 已记录决策的常规应用 / 纯形式问题。

**提问纪律**：一次问一件事 · **必须给 2-3 个选项**（不要开放式提问）· 附背景与每个选项的代价：

```bash
scripts/teamctl.py im ask --task T2 --severity blocker \
  --question "收计划模块要抽成插件层还是硬加到主文件？" \
  --options "抽成插件层（改动大但根治）|硬加到主文件（今天能完）|先硬加上再重构（折中）" \
  --background "三处策略业务逻辑重复，加新计划要改两处" \
  --default "先硬加上，下个迭代再重构" --auto-after-min 120
```

`blocker` 级**停下等答复，不得自行决定**；非 blocker 继续做不依赖的部分。**用户答复必须落盘** `decisions.md` + `im answer` 记录事件，否则 lead 冷重启会重新讨论同一问题。用户不在线时按 `auto_default` 走并标 `auto_resolved`——**不允许静默自行发挥**。

未配置 IM 时（`channel: none`）：lead 在当前对话里直接问用户，规则不变。

**判定 needs-revision 时必须登记重试计数**（不搞"2 次即死"的一刀切）：

```bash
scripts/teamctl.py attempts bump --role builder-a --task T3 --reason "具体缺陷"
scripts/teamctl.py attempts judge --task T3   # ≤3 同角色可继续 / 4-6 换角度 / ≥7 换角色
```

**会话恢复的三级降级**（会话 id 丢失或 CLI 不支持恢复时）：

1. 原生 resume：`claude -r <session_id>`（快恢复，上下文完整）
2. 快恢复：`claude -c`（继续最近一次会话，不指定 id）
3. **冷重建**：读 `logs/checkpoints/<role>-<task>.md` + `decisions.md` + `results/` 产出，重新投契约

第 3 级必须能走通——所以 **checkpoint 是强制动作**，不是可选项。

**agent 侧的上报纪律**（写进契约，让 agent 知道怎么做）：

```bash
# 撞到不确定点：停下上报，不要猜、不要横向问
scripts/teamctl.py escalate --role <role> --task <T1> --severity blocker \
  --question "..." --tried "已排除的可能"
```

### Step 7：收尾归档

1. 核验全部 Done Criteria
2. `decisions.md` 补齐"为什么"（这一栏最容易空着，也最值钱）
3. 检查 `budget check` 与 `ask list` 是否还有未处理的熔断告警 / 未答上报
4. 团队销毁：`teamctl.py team kill --team <name>`（先给最后一次 snapshot，再决定是否 kill tmux session）
5. 向用户汇报：交付物路径、各角色产出、遗留项、未验证项

## 脚本

| 脚本 | 用途 |
| --- | --- |
| `scripts/create_team.sh` | 生成团队目录骨架 + 初始 TEAM.md + `.gitignore` + `git init`。支持 `-n` 名称 / `-r` 根目录 / `-l` 梯度 / `-m` 常驻角色列表 |
| `scripts/teamctl.py` | 团队运行时管控，12 个子命令：`init` / `record` / `escalate` / `ask` / `budget` / `attempts` / `im`（人机通道）/ `session` / `checkpoint` / `status` / `adopt` / `team kill` |

## 参考文档

| 文件 | 内容 | 需要时机 |
| --- | --- | --- |
| `references/org-model.md` | 角色库（lead/researcher/builder/reviewer/recorder）、职责边界矩阵、规模梯度、reviewer 独立性分级 | Step 2 |
| `references/context-protocol.md` | 上下文契约八段详解、黑板模式、三层披露、上报通道约束、裁剪清单 | Step 3 |
| `references/lifecycle.md` | 生命周期状态机、resident/ephemeral 判据、checkpoint 规范、会话恢复三级降级、预算对生命周期的影响 | Step 4 / Step 6 |
| `references/governance.md` | 上报通道（只向上）、三级预算阈值与熔断、渐进式重试换手策略、block 成因对照表 | Step 4 / Step 6 |
| `references/agent-cli.md` | 各 agent CLI（claude/opencode/codex/pi/hermes...）启动命令、session 恢复命令、上下文窗口差异 | Step 5 / Step 6 |
| `references/observability.md` | 行为记录规范：事件 schema、pipe-pane 落盘、决策账本写法 | Step 6 |
| `references/human-channel.md` | 人机通道：IM 能力分级（L0/L1/L2）、幂等配置流程、lead 提问纪律与ask-required/omitted/forbidden 清单 | Step 4 / Step 6 |
| `references/adopt-init-exp.md` | init-exp team 模式转调 agent-team 的适配流程与命名映射 | Step 0 |
