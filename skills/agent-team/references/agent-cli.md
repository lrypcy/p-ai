# Agent CLI 命令与恢复能力

## 命令映射表

拉起 agent 窗口时需要用户指定用哪个 CLI。**不确定的命令直接问用户，不要猜**——猜错会导致窗口启动失败，浪费一整个准备工作。

| 用户选择 | 启动命令 | 备注 |
| --- | --- | --- |
| `claude` | `claude` | Claude Code，session 恢复能力最完整 |
| `codex` | `codex` | OpenAI Codex CLI |
| `opencode` | `opencode --prompt "ulw"` | **主 agent 默认**：ulw 是提示词关键词，详见下节 |
| `pi` | `pi` | 用户自装 agent CLI |
| `hermes` | `hermes` | 用户自装 agent CLI |
| 其他 | 询问用户完整命令 | 不要猜 |

## 主 agent 默认模式：goal / ulw

**主 agent（lead / main）默认用 goal 模式；opencode 下用 `ulw` 关键词激活。**

### 为什么这是默认

goal 模式的语义与本skill 对 lead 的职责定义**高度契合**：

| goal 模式的行为 | 与 lead 职责的对应 |
| --- | --- |
| **只接收目标，不接收步骤计划**（"Goal, not plan"） | lead 的职责就是从用户目标出发自行拆解，不是执行用户给的步骤清单 |
| 目标含编号步骤时，作为**一个原子任务的子阶段**一次做完，不跨轮拆分 | 对应"目标的验收标准逐条落地"，而非拆成多轮 |
| **探索预算充足**（5~15 分钟静默探索是正常的） | 对应 lead 开团前要问清交付物与完成标准 |
| **根因偏好**（追至少两层，不做症状修复） | 对应"实际打开产出核验，不接受表面完成" |
| **要求完整交付**（"简化版/PoC 之后再说"不算交付） | 对应 Done Criteria 必须逐条可核验 |
| 遇到真阻塞才返回并说明 | 对应 escalate 上报 lead 的 Stop Conditions |
| **最少状态更新，专注结果而非过程播报** | 与本 skill 的行为记录哲学一致：不刷屏，只记里程碑 |

最关键的一点：**lead 的本质就是"给目标、让它自己想办法"**。如果给 lead 喂一份详细步骤清单，它就退化成一个执行器，反而削弱 lead 的价值。

### opencode 的具体用法

**`ulw`（`ultrawork`）是提示词关键词，不是独立的 agent 名或子命令。** 官方提示原文：

> Include **ultrawork** (or **ulw**) in your prompt.
> All features work like magic — parallel agents, background tasks, deep exploration, and relentless execution until completion.

`ulw` 会同时开启并行 agent、后台任务、深度探索与持续执行到底。对 lead 来说这正好匹配"派活给多个 worker + 持续推进到完成"。

```bash
# 主 agent 默认启动方式
tmux send-keys -t at-<team>:lead 'opencode --prompt "ulw"' Enter

# worker 用默认模式即可（ulw 是给 lead 的，别给 worker 用）
tmux send-keys -t at-<team>:builder-a 'opencode' Enter
```

**若 `--prompt` 参数在你的 opencode 版本上不生效**（版本差异），有两个回退方式，按优先级尝试：

```bash
# 方式A：交互式首句注入（最稳，不依赖参数）
tmux send-keys -t at-<team>:lead 'opencode' Enter
sleep 2
tmux send-keys -t at-<team>:lead 'ulw: 按 contracts/lead.md 主导本次任务' Enter

# 方式B：配置文件默认值（~/.config/opencode/agent.json）
# 见下方"CLI 版本差异"一节
```

**不要把 `ulw` 当成 agent 名拼进 `--agent`**，那会报找不到 agent。`goal` 是 orchestrator 内部的类目名（DEEP category），用户侧通过 `ulw` 关键词触发。

### 哪些角色用 goal 模式

| 角色 | 默认模式 | 理由 |
| --- | --- | --- |
| **lead / main** | **goal（opencode 用 `ulw`）** | 需要从目标自行拆解、跨任务保持全局|
| builder | 默认模式 | 契约已经把步骤写清楚了，不需要再让 agent 自己规划 |
| reviewer | 默认模式 | 验收标准明确 |
| researcher | 默认（探索密集时可加 `ulw`） | 默认够用；若任务是"广撒网找线索"可加 |

**结论：`ulw` 只给 lead。** worker 用默认模式即可——契约已经把"做什么"说清楚了，再叠加"自己想办法"可能导致它偏离契约边界（尤其是 Do-Not-Touch）。

### goal 模式与本 skill 的两条冲突点

goal 模式有两个默认行为**与本skill 的规则相冲突**，遇到时以本 skill 为准：

| goal 模式默认 | 冲突点 | 本 skill 的做法 |
| --- | --- | --- |
| "If the goal is unclear, make reasonable assumptions and proceed" | 与**不得自行发挥**直接冲突 | 契约 Stop Conditions 与 `im ask` 优先于goal 的默认假设。**契约里必须写明"遇到未覆盖的不确定点用 escalate 上报，不要自行假设"**，否则 goal 模式会真的自己假设 |
| 目标含编号步骤时"一次做完，不跨轮拆分" | 与**预算熔断**可能冲突 | `budget check` 的软/硬阈值优先——超时就 checkpoint 收摊，不要为了"做完"而烧穿预算 |

**因此用 goal 模式时，lead 的契约里必须包含 Stop Conditions 与上报指令**，这不是可选项。参见 `context-protocol.md` 的契约第 8 段与第 9 段。

### 与团队生命周期的配合

goal 模式的"relentless execution until completion"与本 skill 的**预算熔断**是一对张力。配合方式：

- `budget spend` 定期记账，超软超时即写 checkpoint 收摊——**让agent 自己收摊**，而不是硬撑到目标完成
- lead 收摊后即可恢复（`session resume` 或 checkpoint-then-retire），目标不会因为收摊而丢失

## CLI 版本差异

**各CLI 的参数会随版本变化，文档里的命令必须以实际安装版本为准。** 首次在某CLI 上建团队时，先确认一次：

```bash
<cli> --help              # 看是否支持 --prompt / --session / --continue
<cli> --version           # 记录版本，便于回溯行为差异
```

确认后把该CLI 的实际命令补进本文件的映射表。

以 opencode 为例，本机环境实测：`oh-my-openagent` 插件（`~/.config/opencode/opencode.json` 的 `plugin` 字段）提供 `goal` 类目与 `ulw` 关键词。若用户未安装该插件，`ulw` 无效，需先确认插件状态再承诺这个默认行为。

## 会话恢复能力对照

各CLI 的 session 恢复命令差异很大，**使用前必须确认当前 CLI 的实际行为**（CLI 版本迭代会改参数）。

| CLI | 恢复指定会话 | 继续最近会话 | 说明 |
| --- | --- | --- | --- |
| `claude` | `claude -r <session-id>` / `claude --resume` | `claude -c` / `--continue` | 会话 id 在 `~/.claude/projects/` 下可见 |
| `codex` | `codex resume <id>` | `codex resume --last` | 会话 id 在 `~/.codex/sessions/` |
| `opencode` | `opencode --session <id>` | `opencode --continue` | 参数以实际版本为准 |
| `pi` / `hermes` / 其他 | **待确认** | **待确认** | 询问用户具体命令 |

> **重要**：如果某个 CLI 不支持原生恢复（或会话已损坏），直接走 L3 冷重建——读 checkpoint + 决策 + 产出，重新投契约。这条路必须始终可行。

## 会话 id 的获取

不同 CLI 暴露会话 id 的方式不同。常见位置：

| CLI | 会话存储位置 |
| --- | --- |
| `claude` | `~/.claude/projects/<路径转义>/<session-id>.jsonl` |
| `codex` | `~/.codex/sessions/` 下的文件 |
| `opencode` | 取决于版本，需确认 |

**通用兜底**：拿不到 id 时，不要在终端里反复尝试猜测或翻目录——直接问用户"这个 agent 的会话 id 你知道吗"，或直接走 L3。

## 上下文窗口差异

团队设计时必须知道各 agent 的上下文容量，否则会出现"契约+产出超出上下文"。

| CLI 类型 | 典型上下文窗口 | 对契约的影响 |
| --- | --- | --- |
| 主流商业 CLI | 约 200K token | 契约 + 产出留足余量；L3 重建可以放心塞更多文件 |
| 本地小模型 CLI | 8K~32K token | 契约必须精简，Inputs段最多给 2~3 个文件，超出部分拆任务 |
| agent 子进程（CLI 内再起 agent） | 通常继承或更小 | 不要在子进程里再派活 |

**实用规则**：不确定时按最小容量设计契约。宁可分两次派任务，也不要一次塞满。

## tmux 操作速查

```bash
# 会话
tmux new-session -d -s at-<team> -n <role>      # 建窗口（不attach）
tmux attach -t at-<team>                          # 进入
tmux detach                                       # 退出（Ctrl+b 后按d）
tmux list-windows -t at-<team>                    # 窗口列表
tmux list-windows -t at-<team> -F '#W'           # 只输出窗口名
tmux kill-window -t at-<team>:<role>#  关单个角色窗口
tmux kill-session -t at-<team>                    # 销毁整个团队

# 落盘窗口输出（行为记录用，见 observability.md）
tmux pipe-pane -t at-<team>:<role> -o 'cat >> logs/<role>.pipe.log'

# 启动agent（主 agent 用 goal 模式，见上文「主 agent 默认模式」）
tmux send-keys -t at-<team>:lead 'opencode --prompt "ulw"' Enter
tmux send-keys -t at-<team>:builder-a 'opencode' Enter

# 向已在运行的 agent 发送指令（谨慎：可能打断它的推理）
tmux send-keys -t at-<team>:<role> "<指令文本>" Enter

# 查看窗口当前输出（诊断 agent 是否卡住）
tmux capture-pane -t at-<team>:<role> -p -S -50
```

**命名约定**：session 名 = `at-<team-name>`（agent team 前缀，与 init-exp 的 `exp-` 区分），窗口名 = 角色名（`lead`/`builder-a`/`reviewer`）。

**`capture-pane` 是诊断卡住的利器**：agent 报 block 时，先 `capture-pane` 看它最后说了什么、卡在哪一步，再决定怎么处理。

## 混合 CLI 团队

一个团队里不同角色可以用不同 CLI。典型组合：

| 角色 | 常用 CLI | 模式 | 理由 |
| --- | --- | --- | --- |
| lead | 交互式最强的（claude / opencode） | **goal（opencode 用 `ulw`）** | 需要频繁追问 + 从目标自行拆解 |
| builder | 同 lead 或任选 | 默认 | 能力够即可，契约已明确步骤 |
| researcher | 可选带搜索/web 的 CLI | 默认 | 调研需要检索能力 |
| reviewer | 与 builder **不同的 CLI**（若可能） | 默认 | 避免同模型的系统性盲区 |

最后一条是可选的优化项：不同模型、不同上下文实现往往能发现对方发现不了的问题。在做重要验收时可以试，但不要强制要求。

**模式约定的最小原则**：**lead 用 goal，其他角色用默认**。给 worker 叠加 goal/ulw 会让它偏离契约边界（Do-Not-Touch 失效风险），得不偿失。