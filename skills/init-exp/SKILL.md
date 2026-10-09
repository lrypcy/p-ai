---
name: init-exp
description: 初始化并管理规范化个人实验（experiments），支持把 tmux 多agent 团队协作**转调 agent-team skill** 实现。当用户想要：创建/初始化新实验（创建实验、初始化实验、新建实验、实验目录）、确认实验根目录并把实验直接建在根目录下（实验根目录）、为实验搭建标准文件骨架（目标/任务/笔记/结果）、初始化时针对项目做定制化适配（定制、技术栈、python/node/go/rust、lint、实验类型）、启动 tmux team 并创建命名窗口（tmux team、tmux session、多窗口协作、团队模式）、用 main agent（opencode/pi/hermes/claude 等）作为主导分配任务并判定完成情况（分配任务、制定目标、完成判定、main 主导）时使用。Also use when the user asks to scaffold a lab experiment layout, spin up a tmux-based agent team where the main window runs an agent CLI, or run a main-led collaboration loop with goal-setting and task verification.
---

# init-exp

创建规范化实验，并可选转调 `agent-team` skill 启动 tmux 多agent 团队协作，由 main 窗口的 agent 主导目标制定、任务分配与完成判定。

**职责边界**：本 skill 负责**实验骨架 + 项目定制化**（类型 × 技术栈 × lint 规范）；团队协作治理（角色、上下文契约、生命周期、会话恢复、上报通道、预算熔断、行为记录）**统一由 `agent-team` skill 提供**，本 skill 只做转调与适配。

## 核心概念

- **实验根目录 `ROOT`**：所有实验的顶层目录。开始前必须与用户确认（不可猜测）。
- **实验目录**：直接创建在根目录下 `ROOT/<name>/`，名称由用户命名。一次可创建多个。
- **项目定制化适配**：初始化时按实验类型与技术栈定制目录骨架、lint 指南与 .gitignore（见 `references/project-adaptation.md`），并针对已有代码项目做既有约定适配，不套用裸模板。- **tmux team**：可选。**转调 `agent-team` skill 实现**——本 skill 不自己实现团队协议。启用后按Step 3 执行 `adopt` 适配 + 动态调整，团队协作规范（角色、上下文契约、生命周期、会话恢复、上报通道、预算、行为记录）全部以 agent-team 为准。

## 标准文件骨架

每个实验是**独立的 git 项目**，目录固定包含基础骨架，并按类型追加目录：

```
ROOT/<name>/            # git init 的独立仓库
├── AGENTS.md      # agent 协作说明：实验目标、团队模式、团队布局、协作/开发（含 lint 指南）/commit 规范
├── README.md      # 实验概述：一句话说明 + 背景/动机
├── goals.md       # 目标清单：每条含验收标准（由 main 制定）
├── tasks.md       # 任务看板：任务分配、状态、负责人**角色**（main 维护）
├── notes.md       # 运行记录：时间戳条目，log 协作过程
├── results/       # 实验结果输出目录
├── logs/          # team 模式由 adopt 补齐管控文件（见下）
├── .agents/       # 实验内 skills
└── .gitignore     # 忽略缓存/临时文件（按技术栈追加条目）

# 按类型 (-t) 追加：
#   dev  → src/ tests/
#   data → data/ notebooks/
#   ml   → data/ models/ notebooks/
#   docs → docs/

# team 模式由 `teamctl.py adopt` 追加（幂等，非team 模式不需要）：
├── contracts/     # 每个角色的上下文契约 <role>.md（八段结构，agent-team 规范）
├── decisions.md   # 决策账本：为什么这么选（否决备选 + 影响 + 复议条件）
├── TEAM-MAPPING.md# init-exp → agent-team 命名映射草案（人工审校后合并进 AGENTS.md）
└── logs/
    ├── events.jsonl      # 结构化行为事件
    ├── inbox.jsonl       # worker → lead 上报队列（只向上，不横向）
    ├── attempts.jsonl    # 退回重试计数（渐进换手依据）
    ├── budget.json       # 预算额度（软超时/硬上限/团队总预算）
    ├── sessions.json     # 会话登记与 resume 命令
    ├── im-channel.json   # 人机通道配置（通常继承全局 ~/.workbuddy/agent-team/im.json）
    └── checkpoints/      # 生命周期检查点（L3 冷重建依据）
```

文件骨架由 `scripts/init_experiment.sh` 生成，已有文件不会覆盖。每个实验目录创建时自动 `git init`，成为独立仓库，用 git 管理全部文本文件与进展。**team 模式的额外文件由 Step 3 的 `adopt` 补齐**（详见 agent-team 的 `references/adopt-init-exp.md`）。

## 工作流程

### Step 1: 确认实验根目录

1. 询问用户实验根目录的绝对路径（如 `~/experiments`、`/data/lab`）。
2. 路径不存在则创建。确认后记为 `ROOT`。
3. 若用户只给了一个现有项目目录并说"在里面建实验"，则把 `ROOT` 定为该目录，实验直接建在 `ROOT/` 下。

### Step 2: 创建实验（项目定制化）

1. 询问实验名称。支持一次创建多个（逗号/空格分隔均可），或让用户逐步添加。
2. 命名规则：英文小写 + 连字符优先（如 `llm-eval-run1`）；若用户坚持用中文/空格，脚本会自动做安全化处理。
3. **询问本实验的目标**（如"验证 XX 是否可行"）：据此后续填写 AGENTS.md。若一次建多个实验，按实验逐个询问目标。
4. **收集项目画像（定制化适配）**——初始化不是套通用模板，先按 `references/project-adaptation.md` 确认三件事：
   - **实验类型 `-t`**：`lab`（通用实验，默认）/ `dev`（软件开发）/ `data`（数据分析）/ `ml`（模型训练）/ `docs`（调研文档）。可依据 Step 2.3 的目标推断，存疑则询问。
   - **技术栈 `-l`**：`python` / `node`（TS/JS）/ `go` / `rust` / `none`（无代码）。涉及编程开发时必须确认；纯实验默认 `python`，否则 `none`。
   - **是否已有代码**：若目标目录已存在代码，脚本只补缺不覆盖，初始化后须读取既有配置并按 `references/project-adaptation.md`「已有代码时的适配」修订 AGENTS.md。
5. 调用脚本（把画像参数传给脚本）：
   ```bash
   scripts/init_experiment.sh -t <type> -l <lang> "$ROOT" <name1> [name2 ...]
   # 例: scripts/init_experiment.sh -t dev -l python "$ROOT" web-api
   ```
   > 多个实验画像相同时可一次创建；画像不同则分批调用，或创建后逐目录手动补适配（见 project-adaptation.md）。
6. **填写每个实验的 `AGENTS.md`**：把用户在 Step 2.3 陈述的目标写入「目标 (Goal)」小节（每一条目标提炼成可验证的表述）。脚本已按 `-t/-l` 预置了对应目录约定与开发规范（lint 指南），其余协作/commit 规范保持不变。若用户要求 team 模式再单独生成 agent 文件（见 Step 3.0）。
7. **已有代码的项目**：脚本执行后不得结束——读取既有配置文件（pyproject.toml/package.json/go.mod/Cargo.toml 等）、目录结构与实际 lint 命令，按 `references/project-adaptation.md`「已有代码时的适配」把 AGENTS.md 的开发规范改写为该项目真实情况，缺失工具才用脚本默认值；检查是否已有 git 仓库（有则跳过 commit 步骤）。
8. **初始 commit**：对每个实验仓库执行首次提交，把骨架与 AGENTS.md 固化为起点：
   ```bash
   git -C "$ROOT/<name>" add -A && git -C "$ROOT/<name>" commit -m "init: 初始化 $name 实验骨架与 AGENTS.md"
   ```
   > 若 commit 因缺少 user.name/email 失败，告知用户先配置 git 全局身份。
9. 创建完成后，向用户列出每个新目录路径、采用的类型/技术栈与仓库状态。
### Step 3: 询问是否启用 team 模式并转调 agent-team

对每个**新建**的实验，逐个询问：

> "是否要为 `name` 创建 tmux team？"

- **否** → 跳过，直接进入 Step 4 的结果说明。
- **是** → **转调 `agent-team` skill**。本 skill 不再自己实现团队协作协议——角色、上下文契约、生命周期、会话恢复、上报通道、预算、行为记录统一以 agent-team 为准（能力覆盖对照见 agent-team 的 `references/adopt-init-exp.md`）。

**0. 执行 `adopt` 适配实验目录**（把 init-exp 已生成的目录补齐为完整团队）：

   ```bash
   # 在 agent-team skill 的 scripts 目录下执行
   scripts/teamctl.py --team <name> adopt \
     --exp-dir "$ROOT/<name>" --lead-alias main --session-name "exp-<name>"
   ```
   `adopt` 幂等地补齐 `logs/` 下的 events / inbox / attempts / sessions / budget / checkpoints 与 `contracts/` 目录，并生成 `TEAM-MAPPING.md` 命名映射草案。

**1. 动态调整实验内容**（adopt 只补文件、不做语义改写；这一步**不可跳过**，因为它需要理解实验目标与技术栈，脚本无从判断）。逐项完成：

   - **审校命名映射**：读 `TEAM-MAPPING.md`，把「本实验实际」列填好（`main` → lead 角色、`worker` → builder 角色、session 沿用 `exp-<name>`）。
   - **`tasks.md` 负责人列**：表头从「负责人(窗口)」改为「负责人(角色)」——角色名跨 session 稳定，窗口名可能变。
   - **补 `AGENTS.md` 团队小节**：加上指向 `decisions.md` / `contracts/` / `logs/` 的说明，补上**上报通道规则（只向上 escalate，不横向 peer）**、**本次实验的实际预算阈值**、**各角色实际用的 agent CLI（决定 reviewer 独立性档位）**。
   - **建 `decisions.md`**：init-exp 原骨架没有决策账本，需创建（adopt 已留位置，按 agent-team 的条目格式补写）。
   - **为每个角色写 `contracts/<role>.md`**：八段契约（Identity / Objective / Task / Do-Not-Touch / Deliverables / Inputs / Done Criteria / Stop Conditions）。main 的契约覆盖原 team-lead 职责（制定目标 → 分配任务 → 判定完成）**并追加第 9 段「向用户确认」**（见下）；worker 的契约**指路**到 `AGENTS.md` 的开发规范，**不整段复制**。
   - **确认人机通道（Team Leader ↔ 用户）**：见 Step 3.5。

**2. 询问 main 窗口运行哪个 agent**（候选见 `references/agent-guide.md`，默认 `opencode`）。按映射表取得启动命令，用户选择"其他"则直接询问命令。

**3. 询问 worker 窗口用哪个 agent**（可复用 main 的；不需要 worker 则只建 main 单窗口）。

**4. 创建 tmux session 与窗口，并在启动后立刻开 pipe**：

   ```bash
   tmux new-session -d -s exp-<name> -n main
   tmux send-keys -t exp-<name>:main "<main-cmd>" Enter
   tmux pipe-pane -t exp-<name>:main -o 'cat >> logs/main.pipe.log'   # ← 必须，init-exp 原流程缺此步
   ```
   > 各 agent CLI 的启动与 session 恢复命令见 agent-team 的 `references/agent-cli.md`。**不要擅自 attach**。

**5. 确认人机通道（Team Leader ↔ 用户）** —— 让main 在拿不准时能直接问你，不要自行发挥。**先查再配，幂等**：

   ```bash
   scripts/teamctl.py --team <name> im check     # ← 必须先跑
   ```

   | check 结果 | 动作 |
   |---|---|
   | 已配置且验证过 | **直接复用，不要重复问用户** |
   | 有全局配置（`~/.workbuddy/agent-team/im.json`） | 询问用户是否复用，**不要重新问一遍 webhook** |
   | 存在但未验证 | 跑 `im test`；失败则询问是否重配 |
   | 完全未配置 | 向用户确认五项：是否配置（默认是）/ 通道类型（飞书、企业微信、钉钉、其他、暂不配置——**问用户实际用哪个，不要猜**）/ 能力档位（默认 **L1**）/ **是否有可用的飞书自建应用**（仅当考虑 L2 时问）/ webhook URL（**必须用户提供，绝不凭空编造**）|

   ```bash
   scripts/teamctl.py --team <name> im init --channel feishu --tier L1 \
     --notify-cmd 'curl -s -X POST -H "Content-Type: application/json" -d @- "$FEISHU_WEBHOOK"' \
     --webhook-env FEISHU_WEBHOOK
   scripts/teamctl.py --team <name> im test    # 验证失败不算配置成功
   ```

   **L2 前提确认**：直接问用户「**你有没有已经建好的飞书自建应用？**」——不要问"要不要我帮你建"（建应用要在飞书开放平台手工操作，本 skill 做不了）。
   - **有** → 确认 `app_id`/`app_secret` 放哪（只记环境变量名）、消息权限是否已申请、接入方式（**推荐长连接**，可绕开公网穿透），然后登记意图：
     ```bash
     scripts/teamctl.py --team <name> im init --channel feishu --tier L2 \
       --notify-cmd 'curl -s -X POST -H "Content-Type: application/json" -d @- "$FEISHU_WEBHOOK"' \
       --webhook-env FEISHU_WEBHOOK --app-id-env FEISHU_APP_ID \
       --app-secret-env FEISHU_APP_SECRET --app-verify-mode longconn
     ```
   - **没有 / 不确定** → 建议留在 L1，如实说明 L2 的门槛（建应用 + 申请权限 + 处理公网回调）。

   **必须向用户说明能力边界**：群机器人 webhook **只能发不能收**——你在群里回复 main 收不到。默认推荐 **L1**（webhook 提问 + tmux attach 回答）。**L2 入向接收当前尚未实现**，即使登记了 L2，你回复仍需 `tmux attach`（`teamctl.py` 会在 check/status/ask 三处提示，不要说"可在飞书里直接回复"）。企业微信有群机器人 webhook，**个人微信没有合规方案**。用户选「暂不配置」则记 `channel: none`，main 在对话里直接问用户。

   把结论写进 `AGENTS.md` 的「人机通道」小节：通道类型、档位、已验证、ask-required 情形清单。详见 agent-team 的 `references/human-channel.md`。

**6. 登记会话与预算**：

   ```bash
   scripts/teamctl.py --team <name> session set --role main \
     --session-id <id> --resume-cmd "claude -r <id>" --cli <cli> --mode resident
   scripts/teamctl.py --team <name> budget set --per-task-min 60 --hard-cap-min 120 --total-min 600
   ```

**7. team commit**：把 `contracts/`、`decisions.md`、`TEAM-MAPPING.md` 与 AGENTS.md 的团队信息提交：
   ```bash
   git -C "$ROOT/<name>" add -A && git -C "$ROOT/<name>" commit -m "feat: 启用 team 模式并转调 agent-team，补齐契约/决策/预算/上报"
   ```

**8. 输出 session 名、窗口清单与 attach 命令。** **不要**擅自 attach（由用户决定何时进入）。

### Step 4: main 主导协作

main 窗口的 agent 是团队主导者。**通用协作协议统一以 agent-team 为准**，本 skill 不重复描述：

| 协作维度 | 规范位置（agent-team skill） |
| --- | --- |
| 角色职责与边界矩阵 | `references/org-model.md` |
| 上下文契约与信息传递 | `references/context-protocol.md` |
| 生命周期（常驻/用完即弃）、会话恢复 | `references/lifecycle.md` |
| 上报通道、预算熔断、重试换手 | `references/governance.md` |
| 行为记录与决策账本 | `references/observability.md` |

实验特有部分（目标验收、git 提交纪律、状态机细节）见 init-exp 本 skill 的 `references/workflow.md`。

main 按「制定目标 → 分配任务 → 核验产出 → 判定」循环推进：

1. main 写入 `goals.md`（每条目标含可验证的验收标准）。
2. main 在 `tasks.md` 分配任务，标注负责人**角色**（不是窗口名）。
3. worker 领取任务、更新状态、产出放入 `results/`，日志落 `logs/`。
4. main **实际打开 `results/` 产物**逐条核验验收标准，判定 `done` 或退回 `needs-revision`（不接受 agent 的文字自述作为完成依据）。
5. 判定 needs-revision 时登记重试计数并看换手建议：
   ```bash
   scripts/teamctl.py attempts bump --role <role> --task <T1> --reason "具体缺陷"
   scripts/teamctl.py attempts judge --task <T1>
   ```
   策略是渐进换手（≤3 次同角色可继续 / 4-6 次换角度 / ≥7 次换角色或拆任务），**不是 2 次即死**。
6. worker 卡住时用 `escalate` 向上上报（不横向问 peer），lead 用 `ask list` 处理待答队列。
7. main 需要用户拍板时用 `im ask` 提问（一次一件事、给 2-3 个选项、附背景与代价），**不得自行发挥**：
   ```bash
   scripts/teamctl.py --team <name> im ask --task <T1> --severity blocker \
     --question "..." --options "选项A|选项 B|选项 C" --background "..." --default "最保守的选项"
   ```
   用户答复后 `im answer --reply "..."` 并写进 `decisions.md`。
8. 每个重大/独立进展单独 commit。

## 脚本

| 脚本 | 归属 | 用途 |
|---|---|---|
| `scripts/init_experiment.sh` | 本skill | 创建 `ROOT/<name>/` 标准骨架、AGENTS.md 模板、`.agents/` 目录，并 `git init` 为独立仓库。支持 `-t <type>`（lab/dev/data/ml/docs）与 `-l <lang>`（python/node/go/rust/none）做项目定制化适配 |
| `scripts/teamctl.py` | **agent-team** | 团队运行时管控：`adopt` 适配实验目录为完整团队 / `im` 人机通道（check/init/test/ask/answer，Team Leader ↔ 用户）/ `escalate`+`ask` 上报通道 / `budget` 预算熔断 / `attempts` 重试换手 / `session` 会话登记与恢复 / `checkpoint` 检查点 / `record` 行为事件 / `status` 全景快照。**team 模式的全部管控都走这个脚本** |

> `scripts/setup_tmux_team.sh`（旧的布局脚本）已不再用于 team 模式——窗口创建与 pipe-pane 现在按 Step 3 的命令直接执行，便于在启动后立刻补上 pipe 与会话登记。

## 参考文档

本 skill 负责实验骨架与项目定制化，团队协作协议转调 agent-team。

- `references/agent-guide.md` — agent（opencode/pi/hermes/claude/自定义）命令映射。Step 3 需要。
- `references/workflow.md` — 实验特有的协作细节：目标验收、git 提交纪律、任务状态机。Step 4 需要。
- `references/project-adaptation.md` — 项目定制化适配指南：类型 × 技术栈的目录骨架、lint 指南与 .gitignore 追加清单。Step 2 需要。

**团队协作协议（转调 agent-team skill）**：

- `agent-team/references/adopt-init-exp.md` — 转调流程与能力覆盖对照、命名映射、动态调整清单。Step 3 需要。
- `agent-team/references/org-model.md` — 角色职责与边界矩阵、reviewer 独立性分级。
- `agent-team/references/context-protocol.md` — 上下文契约八段、黑板模式、上报通道约束。
- `agent-team/references/lifecycle.md` — 生命周期状态机、常驻/用完即弃判据、会话恢复三级降级。
- `agent-team/references/governance.md` — 上报通道、预算熔断、渐进式重试换手。
- `agent-team/references/human-channel.md` — 人机通道：IM 能力分级、幂等配置、main 向用户提问的纪律与必问清单。Step 3.5 / Step 4 需要。
- `agent-team/references/observability.md` — 行为记录三层、决策账本、checkpoint 规范。