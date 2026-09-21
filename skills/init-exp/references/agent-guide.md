# Agent 命令映射与窗口角色

## Agent 命令映射表

创建 tmux team 时，main/worker 窗口需要用户指定运行哪个 agent。以下为常见 agent 的启动命令映射：

| 用户选择 | 启动命令 | 备注 |
|---|---|---|
| `opencode` | `opencode` | 默认主 agent |
| `pi` | `pi` | 用户自装 agent CLI |
| `hermes` | `hermes` | 用户自装 agent CLI |
| `claude` | `claude` | Claude Code |
| `codex` | `codex` | OpenAI Codex |
| 其他 | 询问用户完整命令 | 不要猜，直接向用户要命令 |

> 若用户说出某个名字但不确定其启动命令，优先让用户自行确认，避免凭空猜测导致窗口启动失败。

## 窗口角色

| 窗口 | 角色 | 运行内容 |
|---|---|---|
| `main` | **主导者** | main agent（opencode/pi/hermes...）。制定目标、分配任务、核验结果、判定完成。 |
| `worker` | 执行者 | 执行 agent（可与 main 相同或不同）。领取任务、执行、更新 tasks.md、产出到 `results/` 与 `logs/`。 |
| `logs` | 观察者 | shell，`tail -f` 观察实验日志。 |
| `monitor` | 观察者 | `top` 等资源监控。 |

## tmux 常用操作

```bash
tmux attach -t exp-<name>          # 进入 session
tmux detach                        # 退出（Ctrl+b 后按 d）
tmux list-windows -t exp-<name>    # 查看窗口列表
tmux select-window -t exp-<name>:worker   # 切到 worker 窗口
tmux kill-session -t exp-<name>    # 销毁整个 team
```

## 会话命名约定

- session 名 = `exp-<子实验名>`（子实验名做安全化处理，空格/斜杠转为连字符）。
- 一个实验一个独立 session，不与其他实验混用。