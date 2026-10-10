#!/usr/bin/env bash
#
# create_team.sh - 生成 Agent 团队目录骨架
#
# Usage:
#   create_team.sh -n <team-name> -r <root> [-l <gradient>] [-m <resident-roles>] [-s <sessions-name>]
#
# Arguments:
#   -n  团队名（英文小写 + 连字符，会做安全化处理）
#   -r  团队工作目录的绝对路径（不存在会创建）
#   -l  规模梯度: solo | duo | squad | council   （默认 duo）
#   -m  常驻角色列表（逗号分隔）例: lead,builder-a
#       未列出的角色按 ephemeral 处理
#   -s  tmux session 名（默认 at-<team-name>）
#
# Example:
#   create_team.sh -n refactor -r ~/projects -l squad -m lead,builder-a
#
# 说明:
#   - 已有文件不会覆盖，可重复执行以补齐缺失文件
#   - 生成骨架后自动 git init 为独立仓库
#   - 不创建 tmux session（按需单独创建，见 agent-cli.md）

set -euo pipefail

usage() {
  echo "用法: create_team.sh -n <team-name> -r <root> [-l <gradient>] [-m <resident-roles>] [-s <session-name>]" >&2
  echo "  gradient: solo | duo | squad | council  (默认 duo)" >&2
  echo "  resident: 常驻角色，逗号分隔（默认 lead）" >&2
  exit 1
}

TEAM_NAME=""
ROOT=""
GRADIENT="duo"
RESIDENT="lead"
SESSION_NAME=""

while getopts "n:r:l:m:s:h" opt; do
  case "$opt" in
    n) TEAM_NAME="$OPTARG" ;;
    r) ROOT="$OPTARG" ;;
    l) GRADIENT="$OPTARG" ;;
    m) RESIDENT="$OPTARG" ;;
    s) SESSION_NAME="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done

[ -n "$TEAM_NAME" ] && [ -n "$ROOT" ] || usage

case "$GRADIENT" in
  solo|duo|squad|council) ;;
  *) echo "❌ 未知 gradient: $GRADIENT (可选 solo|duo|squad|council)" >&2; exit 1 ;;
esac

# ---------- 安全化团队名 ----------
SAFE_NAME=$(echo "$TEAM_NAME" | tr 'A-Z ' 'a-z-' | sed 's/[^a-z0-9-]//g; s/-\{2,\}/-/g; s/^-//; s/-$//')
[ -n "$SAFE_NAME" ] || { echo "❌ 团队名安全化后为空，请换一个名字" >&2; exit 1; }
SESSION_NAME="${SESSION_NAME:-at-$SAFE_NAME}"

TEAM_DIR="$ROOT/$SAFE_NAME"
mkdir -p "$TEAM_DIR"

# ---------- 目录骨架 ----------
mkdir -p "$TEAM_DIR/contracts" "$TEAM_DIR/results" "$TEAM_DIR/logs/checkpoints" "$TEAM_DIR/.agents"

# ---------- 写文件（不覆盖已有内容） ----------
write_if_absent() {
  local path="$1"
  [ -e "$path" ] && { echo "  ⏭  已存在，跳过: ${path#$TEAM_DIR/}"; return 0; }
  cat > "$path"
  echo "  ✅ 写入: ${path#$TEAM_DIR/}"
}

echo ""
echo "📁 初始化 Agent 团队: $SAFE_NAME"
echo "   目录: $TEAM_DIR"
echo "   梯度: $GRADIENT   常驻角色: $RESIDENT"
echo "   tmux session 名: $SESSION_NAME"
echo ""

write_if_absent "$TEAM_DIR/.gitignore" <<'EOF'
# agent-team 行为记录中的原始管道输出（体积大、可再生，不入版本库）
logs/*.pipe.log
logs/*.pipe.log.*

# 通用忽略
.DS_Store
__pycache__/
*.pyc
EOF

write_if_absent "$TEAM_DIR/tasks.md" <<'EOF'
# 任务看板

> 唯一写入者：lead。验收标准必须可核验（命令 / 文件事实）。
> 任务行的 ID 必须形如 T1、T2（teamctl.py status 依此解析）；示例行请替换后再用。

## 目标

## G1: <目标简述>

- 状态: open
- 验收标准:
  - [ ] <可验证的条件 1>
  - [ ] <可验证的条件 2>

## 任务

| ID | 任务 | 负责人(角色) | 关联目标 | 模式 | 状态 | 完成标准 | 产出 |
|----|------|--------------|----------|------|------|----------|------|
| <ID> | <任务> | <role> | G1 | ephemeral | pending | <可核验标准> | results/... |

## 状态机

```
pending ──► in_progress ──► done
                 ▲              │
                 └── needs-revision ◄──┘
```
EOF

write_if_absent "$TEAM_DIR/decisions.md" <<'EOF'
# 决策账本

> 唯一写入者：lead。记录**为什么**，不只是**做了什么**。
> 每条必须写：背景 / 选择 / 否决的备选与理由 / 影响范围 / 复议条件。
> 决策变更追加新条目，不修改旧条目。

## 条目模板

```markdown
## D<n> · <决策标题>
- 时间：YYYY-MM-DD HH:MM
- 决策人：lead
- 相关：<任务号、角色>
- 背景：<面对什么问题，有哪些候选>
- 选择：<最终方案>
- 否决的备选：<方案 X —— 为什么不用>
- 影响：<谁受影响，后续是否沿用>
- 复议条件：<什么情况下该重新审视>
```
EOF

write_if_absent "$TEAM_DIR/notes.md" <<'EOF'
# 协作流水

> 规则：只追加，不改他人行。

- YYYY-MM-DD HH:MM | lead | 团队初始化
EOF

write_if_absent "$TEAM_DIR/TEAM.md" <<EOF
# 团队章程 · $SAFE_NAME

> 本文件由 lead 维护。L1 常驻上下文要求：团队目标段不超过 50 行，全文不超过 200 行。
> 超出的细节移入 \`contracts/\` 或 \`decisions.md\`。

## 1. 目标（团队最终要交付什么）

<!-- 填写：一份可验证的交付物描述。交付物不清楚不要开团。 -->

## 2. 完成标准（怎么算做完了）

<!-- 逐条可核验。例：pytest -q 全绿；results/report.md 含指定章节；某命令退出码 0 -->

## 3. 角色 roster

| 角色 | 职责 | 模式 | 常驻理由 / 用完即弃理由 | 契约 |
|------|------|------|----------------------|------|
| lead | 主导者：定目标、分配、验收、汇报 | resident | 决策中枢，需持续掌握全局 | contracts/lead.md |
| <role> | <职责> | ephemeral | 任务边界清晰，一次性 | contracts/<role>.md |

> 常驻角色必须写明理由；没有理由的常驻就是浪费。

## 4. 职责边界矩阵

| 角色 | 可改文件 | 可做决策 | 禁止 | 报告给 |
|------|----------|----------|------|--------|
| lead | 全部 | 任务分配、验收、方案终裁 | 直接大规模改实现代码 | 用户 |
| <role> | <路径> | <范围> | <禁止项> | lead |

## 5. 协作协议

- **单写者原则**：tasks.md / decisions.md 只有 lead 写；contracts/\`<role>\`.md 只有 lead 写；results/\`<task>\` 只有对应 agent 写；notes.md 全员只追加。
- **传递单位是「产出 + 指针」**，不是对话历史。下游读上游写在文件里的结论，不读上游的思考过程。
- **上游没写产出 = 任务未完成**。下游不得自行补做上游任务，应停下上报 lead。
- **完成判定看产出**：lead 实际打开 \`results/\` 里的产物逐条核对 Done Criteria，不接受口头/文字"我做好了"。
- **冲突即停**：两个 agent 想改同一文件 → 立即停下上报 lead。

## 6. 上下文与生命周期

- 每个 agent 启动时读：\`TEAM.md\` 本文件 + \`contracts/<role>.md\`。其余按契约的 Inputs 段按需读。
- **默认 ephemeral**（checkpoint-then-retire）；resident 必须在本文件 roster 里写明理由。
- retire = 退出 agent 进程，**保留 tmux 窗口转作shell**、保留会话记录、保留 checkpoint 与产出。
- 会话恢复三级降级：原生 resume → 快速续跑 → **冷重建（读 checkpoint + 决策 + 产出，重新投契约）**。第3 级必须始终可行。
- 会话登记：拉起 agent 后立刻执行
  \`\`\`bash
  scripts/teamctl.py session set --team $SAFE_NAME --role <role> --session-id <id> --resume-cmd "claude -r <id>"
  \`\`\`

## 7. 窗口布局

- tmux session：\`$SESSION_NAME\`
- 窗口名 = 角色名

| 窗口 | 角色 | agent CLI | 模式 | 落地输出 |
|------|------|-----------|------|----------|
| lead | 主导者 | <cli> | **goal**（opencode: \`ulw\`） | logs/lead.pipe.log |
| <role> | <role> | <cli> | 默认 | logs/<role>.pipe.log |

> **模式约定**：lead 用 goal 模式——该模式「只接收目标、不接收步骤计划」，与 lead 从目标自行拆解的职责契合。opencode 下用提示词关键词 \`ulw\` 激活（\`opencode --prompt "ulw"\`）。**不要给 worker 加 ulw**：契约已把步骤写清，再让 agent 自行规划会偏离 Do-Not-Touch 边界。
>
> ⚠️ goal 模式默认「目标不清就自行假设」，与本 skill 的「不得自行发挥」冲突——**lead 契约的 Stop Conditions 与「向用户确认」段为强制项**，必须显式压制该默认行为。

拉起命令：
\`\`\`bash
tmux new-session -d -s $SESSION_NAME -n lead
tmux send-keys -t $SESSION_NAME:lead 'opencode --prompt "ulw"' Enter
tmux pipe-pane -t $SESSION_NAME:lead -o 'cat >> logs/lead.pipe.log'
\`\`\`

> 若 \`--prompt\` 参数在你的 opencode 版本不生效，改用交互式注入：启动后向 lead 窗口发送
> \`ulw: 按 contracts/lead.md 主导本次任务\`。详见 agent-team 的 \`references/agent-cli.md\`。

> 不擅自attach；把 \`tmux attach -t $SESSION_NAME\` 交给用户决定。

## 8. 行为记录

- **L1 原始输出**：每个窗口开 pipe-pane，落 \`logs/<role>.pipe.log\`
- **L2 结构化事件**：\`logs/events.jsonl\`，用 \`teamctl.py record\` 写入，summary 必须具体
- **L3 决策账本**：\`decisions.md\`，记录为什么
- **Checkpoint**：\`logs/checkpoints/<role>-<task>.md\`，retire 前强制写
- **Git**：每个独立/可验证进展单独 commit，message用「动词 + 对象」

## 9. 人机通道（Team Leader ↔ 用户）

- 通道：\`im_channel: 待配置\`（用 \`teamctl.py im init\` 配置；**已配置则直接复用，勿重复配置**）
- 规则：lead 遇到 ask-required 情形（契约未定义的语义、超出授权的决策、不可逆操作、>=7 次重试、目标本身不合理）**必须向用户确认，不得自行发挥**
- 约束：一次问一件事、给 2-3 个选项、附背景与代价；blocker 级停下等答复
- 详见 agent-team skill 的 \`references/human-channel.md\`

## 10. 收摊清单

- [ ] 全部 Done Criteria 已逐条核验
- [ ] decisions.md 补齐"为什么"（备选与否决理由）
- [ ] needs-revision 与 block 任务已清零或明确记为遗留
- [ ] \`teamctl.py im status\` 无未答的 blocker 提问
- [ ] \`teamctl.py status\` 输出已复核
- [ ] 团队快照已保存
- [ ] 向用户汇报：交付物路径、各角色产出、遗留项、未验证项
EOF

write_if_absent "$TEAM_DIR/contracts/README.md" <<'EOF'
# 上下文契约目录

每个角色一份契约 `<role>.md`，由 lead 撰写、lead 维护（唯一写入者）。
agent 启动时读自己的契约，不读别人的。

八段结构（详见 ../references/context-protocol.md）：

1. Identity        你是谁、代号、职责范围
2. Objective       本轮目标（引用 tasks.md 任务号）
3. Task            具体做什么、边界在哪
4. Do-Not-Touch    禁止修改的文件/目录、禁止决策的领域
5. Deliverables    产出落到哪个路径、什么格式、命名规范
6. Inputs          上游产出在哪、该读哪些文件（给路径，不给全文）
7. Done Criteria   可验证的完成标准
8. Stop Conditions 什么情况必须停下上报

撰写自查：
- 契约里没有大段代码/日志粘贴（只给路径）
- Do-Not-Touch 不为空
- Done Criteria 每条能用命令或文件事实验证
- Stop Conditions 至少覆盖一类不确定性
- 契约总长 < 100 行
EOF

# ---------- git init ----------
cd "$TEAM_DIR"
if [ -d .git ]; then
  echo "  ⏭  已是 git 仓库，跳过 init"
else
  git init -q
  echo "  ✅ git init"
fi

echo ""
echo "✅ 团队骨架就绪"
echo "   目录:   $TEAM_DIR"
echo "   session: $SESSION_NAME（尚未创建 tmux session）"
echo ""
echo "   下一步:"
echo "     1. 填TEAM.md 的目标 / 完成标准 / roster / 边界矩阵"
echo "     2. 为每个角色写 contracts/<role>.md"
echo "     3. 按 agent-cli.md 拉起 tmux session 与 agent 窗口"
echo "     4. 记录事件: scripts/teamctl.py record --team $SAFE_NAME --role lead --event team_spawn --summary \"...\""
echo ""
echo "   进入: tmux new-session -d -s $SESSION_NAME -n <role>"