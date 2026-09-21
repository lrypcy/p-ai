---
name: init-exp
description: 初始化并管理规范化个人实验（experiments），支持基于 tmux 的多 agent 团队协作。当用户想要：创建/初始化新实验（创建实验、初始化实验、新建实验、实验目录）、确认实验根目录并把实验直接建在根目录下（实验根目录）、为实验搭建标准文件骨架（目标/任务/笔记/结果）、初始化时针对项目做定制化适配（定制、技术栈、python/node/go/rust、lint、实验类型）、启动 tmux team 并创建命名窗口（tmux team、tmux session、多窗口协作、团队模式）、用 main agent（opencode/pi/hermes/claude 等）作为主导分配任务并判定完成情况（分配任务、制定目标、完成判定、main 主导）时使用。Also use when the user asks to scaffold a lab experiment layout, spin up a tmux-based agent team where the main window runs an agent CLI, or run a main-led collaboration loop with goal-setting and task verification.
---

# init-exp

创建规范化实验，并可选启动 tmux 多 agent 团队协作，由 main 窗口的 agent 主导目标制定、任务分配与完成判定。

## 核心概念

- **实验根目录 `ROOT`**：所有实验的顶层目录。开始前必须与用户确认（不可猜测）。
- **实验目录**：直接创建在根目录下 `ROOT/<name>/`，名称由用户命名。一次可创建多个。
- **项目定制化适配**：初始化时按实验类型与技术栈定制目录骨架、lint 指南与 .gitignore（见 `references/project-adaptation.md`），并针对已有代码项目做既有约定适配，不套用裸模板。
- **tmux team**：可选。每个实验可分配一个独立 tmux session，窗口命名合理，其中 `main` 窗口用于运行主 agent。

## 标准文件骨架

每个实验是**独立的 git 项目**，目录固定包含基础骨架，并按类型追加目录：

```
ROOT/<name>/            # git init 的独立仓库
├── AGENTS.md      # agent 协作说明：实验目标、团队模式、团队布局、协作/开发（含 lint 指南）/commit 规范
├── README.md      # 实验概述：一句话说明 + 背景/动机
├── goals.md       # 目标清单：每条含验收标准（由 main 制定）
├── tasks.md       # 任务看板：任务分配、状态、负责人窗口（main 维护）
├── notes.md       # 运行记录：时间戳条目，log 协作过程
├── results/       # 实验结果输出目录
├── logs/          # 运行日志目录（worker 输出落盘位置）
├── .agents/       # 实验内 skills（team 模式含 team-lead/ 标准 skill，见目录内 README）
└── .gitignore     # 忽略缓存/临时文件（按技术栈追加条目）

# 按类型 (-t) 追加：
#   dev  → src/ tests/
#   data → data/ notebooks/
#   ml   → data/ models/ notebooks/
#   docs → docs/
```

文件骨架由 `scripts/init_experiment.sh` 生成，已有文件不会覆盖。每个实验目录创建时自动 `git init`，成为独立仓库，用 git 管理全部文本文件与进展。

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

### Step 3: 询问是否启用 team 模式并创建 tmux team

对每个**新建**的实验，逐个询问：

> "是否要为 `name` 创建 tmux team？"

- **否** → 跳过，直接进入 Step 4 的结果说明。
- **是** → 执行：

**0. 创建 team-lead 标准 skill 到 `.agents/`**：team 模式把团队协作固化为**标准 skill**（`SKILL.md` + 可选 references/），main 启动后加载即获得主导能力：

   1. 在 `$ROOT/<name>/.agents/team-lead/SKILL.md` 写入 skill（标准 frontmatter：`name` + `description`）：
      ```markdown
      ---
      name: team-lead
      description: 实验团队主导 skill。main 窗口加载后获得完整主导能力：依据用户目标制定目标、分配任务、判定完成。触发词：制定目标、分配任务、判定完成、团队协作。
      ---

      # team-lead - 团队主导

      你是本实验团队的主导者。目标见 `AGENTS.md`「目标」与 `goals.md`。

      ## 职责
      - 依据用户目标在 `goals.md` 制定可验证的目标与验收标准。
      - 在 `tasks.md` 分配任务，标注负责人窗口（worker 等）。
      - 核验 `results/` 产出，判定任务 done 或退回 needs-revision。
      - 每个重大/独立进展单独 commit（commit message 说明进展）。

      ## 协作协议
      - 目标 / 任务 / 笔记 / 结果全部通过 `goals.md` / `tasks.md` / `notes.md` / `results/` 传递。
      - 每个目标必须可验证；完成标准写在 tasks.md。
      - 完成判定依据 goals.md 验收标准实际核验，不凭主观感觉。

      ## 开发规范
      - 涉及编程语言开发时**必须遵循典型开发规范**及项目既有工程约定（先读配置文件与现有代码再动手）。
      - 存在 lint 配置（ruff/eslint/biome/golangci-lint/clippy/pyright 等）时**必须遵循 lint 指南**：新代码满足规则、提交前运行 lint/typecheck 校验并确认通过。
      - **禁止用逃逸手段掩盖 lint 问题**（盲目 noqa/@ts-ignore/eslint-disable 等）；确需放行须给出理由并记入 notes.md。
      ```
      若需细化协议，可在 `.agents/team-lead/references/` 下补充子文档，并在 SKILL.md 中引用。
      并同步把「已启用 team 模式 + 团队 skill 位于 `.agents/team-lead/`」回填到 `AGENTS.md` 的「团队模式」小结与「团队布局」表的实际窗口/agent 列。
   2. worker（可选）：若 worker 窗口执行者需要独立 skill，用同样方式建 `.agents/<role>/SKILL.md`；否则 worker 直接复用 main 的 agent CLI（如 `pi`、`hermes`）。

1. 询问 **main 窗口运行哪个 agent**（候选见 `references/agent-guide.md`，默认 `opencode`）。按映射表取得启动命令，用户选择"其他"则直接询问命令。
2. 询问 **worker 窗口用哪个 agent**（可复用 main 的，默认可复用；不需要 worker 则选 `minimal` 布局）。
3. 选择布局（见下表，默认 `standard`）：
   - `minimal`：仅 main
   - `standard`：main + worker
   - `full`：main + worker + logs + monitor
4. session 名固定为 `exp-<name>`（name 做安全化处理）。
5. 调用脚本：
   ```bash
   scripts/setup_tmux_team.sh "exp-<name>" <layout> "<main-cmd>" "<worker-cmd>"
   ```
   > main 窗口的启动命令建议让 main 启动后加载刚生成的 team-lead skill（例如 opencode 中 `skill` 工具加载 `.agents/team-lead`），使 main 一进来就具备团队主导职责。
6. **team commit**：把 `.agents/` 与 AGENTS.md 的团队信息提交：
   ```bash
   git -C "$ROOT/<name>" add -A && git -C "$ROOT/<name>" commit -m "feat: 启用 team 模式，添加 .agents/team-lead 团队协作 skill"
   ```
7. 输出 session 名、窗口清单与 attach 命令。**不要**擅自 attach（由用户决定何时进入）。

### Step 4: main 主导协作

main 窗口的 agent 是团队主导者。启动后按 `references/workflow.md` 执行完整的「制定目标 → 分配任务 → 完成判定」循环：

1. main 写入 `goals.md`（含验收标准）。
2. main 在 `tasks.md` 分配任务，标注负责人窗口（如 `worker`）。
3. worker 等窗口领取任务、执行、更新状态、产出放入 `results/` 与 `logs/`。
4. main 依据验收标准核验 `results/`，判定 `done` 或退回 `needs-revision`。

协作细节、tasks.md 格式与状态机见 `references/workflow.md`。

## 脚本

| 脚本 | 用途 |
|---|---|
| `scripts/init_experiment.sh` | 创建 `ROOT/<name>/` 标准骨架、AGENTS.md 模板、`.agents/` 目录，并 `git init` 为独立仓库。支持 `-t <type>`（lab/dev/data/ml/docs）与 `-l <lang>`（python/node/go/rust/none）做项目定制化适配 |
| `scripts/setup_tmux_team.sh` | 创建独立 tmux session，按布局建命名窗口并启动 agent |

## 参考文档

- `references/agent-guide.md` — agent（opencode/pi/hermes/claude/自定义）命令映射与窗口角色说明。Step 3 需要。
- `references/workflow.md` — main 主导协作协议：目标制定、任务分配、完成判定的完整流程与文件格式。Step 4 需要。
- `references/project-adaptation.md` — 项目定制化适配指南：类型 × 技术栈的目录骨架、lint 指南与 .gitignore 追加清单，及已有代码场景的适配流程。Step 2 需要。