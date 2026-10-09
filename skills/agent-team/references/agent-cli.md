# Agent CLI 命令与恢复能力

## 命令映射表

拉起 agent 窗口时需要用户指定用哪个 CLI。**不确定的命令直接问用户，不要猜**——猜错会导致窗口启动失败，浪费一整个准备工作。

| 用户选择 | 启动命令 | 备注 |
| --- | --- | --- |
| `claude` | `claude` | Claude Code，session 恢复能力最完整 |
| `codex` | `codex` | OpenAI Codex CLI |
| `opencode` | `opencode` | 原init-exp 的默认 main agent |
| `pi` | `pi` | 用户自装 agent CLI |
| `hermes` | `hermes` | 用户自装 agent CLI |
| 其他 | 询问用户完整命令 | 不要猜 |

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

# 启动agent
tmux send-keys -t at-<team>:<role> "claude" Enter

# 向已在运行的 agent 发送指令（谨慎：可能打断它的推理）
tmux send-keys -t at-<team>:<role> "<指令文本>" Enter

# 查看窗口当前输出（诊断 agent 是否卡住）
tmux capture-pane -t at-<team>:<role> -p -S -50
```

**命名约定**：session 名 = `at-<team-name>`（agent team 前缀，与 init-exp 的 `exp-` 区分），窗口名 = 角色名（`lead`/`builder-a`/`reviewer`）。

**`capture-pane` 是诊断卡住的利器**：agent 报 block 时，先 `capture-pane` 看它最后说了什么、卡在哪一步，再决定怎么处理。

## 混合 CLI 团队

一个团队里不同角色可以用不同 CLI。典型组合：

| 角色 | 常用 CLI | 理由 |
| --- | --- | --- |
| lead | 交互式最强的（claude / opencode） | 需要频繁追问 |
| builder | 同 lead 或任选 | 能力够即可 |
| researcher | 可选带搜索/web 的 CLI | 调研需要检索能力 |
| reviewer | 与 builder **不同的 CLI**（若可能） | 避免同模型的系统性盲区 |

最后一条是可选的优化项：不同模型、不同上下文实现往往能发现对方发现不了的问题。在做重要验收时可以试，但不要强制要求。