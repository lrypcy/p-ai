# 生命周期与工作模式

## 生命周期状态机

```
                    ┌──────────────────────────┐
                    │                          │
  spawn ──► active ──► checkpoint ──► retire ──► dormant ──► resume ──┘
              │                       │
              │◄────── block ─────────┘
              │       （卡住）
              │
              └─► needs-revision（产出被否，退回重做）
```

| 状态 | 含义 | 上下文是否在 | 下一步 |
| --- | --- | --- | --- |
| `spawn` | 刚拉起，投放契约中 | 是（空） | active |
| `active` | 正在执行任务 | 是 | checkpoint / block / retire |
| `checkpoint` | 写完检查点，准备退或准备挂起 | 是 | retire |
| `retire` | 退出 agent，tmux 窗口留作 shell | 否（已退） | dormant |
| `dormant` | 休眠，会话 id 已登记，等恢复 | 否 | resume |
| `resume` | 恢复会话，重新投契约 | 是 | active |
| `block` | 卡住，已标注原因 | 是 | lead 决定接手/拆分/取消 |
| `needs-revision` | 产出未过验收 | 可能已退 | 重新 spawn 或 resume 重做 |

## 两种工作模式的判据

### `resident`（长连接）

agent 进程持续存活，保持工作状态。会话常驻内存，上下文连续。

**满足以下任一才用 resident：**

1. **该 agent 是决策中枢**。lead 需要持续掌握全局、随时被打断追问。中断一个 resident 只需要等它回话；中断 ephemeral 需要重新 spawn + 重新投契约 + 重建上下文。
2. **连续任务共享大上下文，重读成本 >> 保活成本**。例：同一份 5000 页文档、同一块复杂代码库，第二个任务接着第一个做。如果重读只需 5 分钟且 agent spawn 只要 30 秒，就该用 ephemeral。
3. **需要保持外部连接/进程**。训练进程、dev server、watch 循环、数据库连接、tmux 里的长跑任务。**这类必须 resident**——session 恢复救不了被 kill 掉的训练进程。
4. **任务是"守着"**。等CI 跑完、等实验出结果、等上游 agent 交付。这类 agent 大部分时间空闲，但必须在线。
5. **交互式密集、需频繁追问**。用户会随时向它提问（典型的 lead）。

**resident 的代价（必须正视）：**

- 上下文窗口会被无休止的对话历史填满，注意力被稀释。长时间常驻的 agent 质量会下降
- 进程内存持续占用
- 常常处于空闲状态却仍在烧 token（如果 agent CLI 空闲时轮询 API 的话）
- 会话一旦损坏，影响面是全量历史

**resident 的强制纪律：**

- 至少每完成一个任务写一次 checkpoint
- 关键结论必须落盘，不依赖会话历史（见"context-protocol.md" 的第3 条原则）
- 定期把决策补进 `decisions.md`

### `ephemeral`（用完即弃）

agent 完成任务就退出，需要时再拉起。默认模式。

**满足以下任一即可用 ephemeral：**

1. **任务边界清晰、一次性**。典型："查清 X API 怎么用"、"把这段翻译成 Rust"、"跑一次基准测试"。这是最主流的情况。
2. **上下文是"任务包"而非"累积知识"**。agent 只需要一个任务的相关信息，不需要"我们之前讨论过什么"。任务包可以完整写在契约里，重建成本≈0。
3. **只需要产出物，不需要连续性**。agent 的价值就是 `results/` 里那个文件，它记不记得过程无所谓。
4. **探索性/发散性工作**。10 个方向各探一轮，结果确定后再深入。保持 10 个 agent 常驻毫无意义。
5. **需要大规模并行 fan-out**。10 个 agent 各查一次，用完即关；常驻 10 个窗口既占资源又难管理。

**ephemeral 的代价：**

- 每次 spawn 都要重新投契约、重新说明背景
- 会话无法携带"上个任务的经验"——所以**跨任务的经验必须落盘**，否则丢了

### 中间态：`checkpoint-then-retire`（推荐默认）

不是所有场景都能干净地二选一。默认采用这个：

agent 干活 → 写 checkpoint → 登事件 → 退出 agent 进程 → **tmux 窗口留着当 shell**。

好处：agent 进程随时可退（释放内存与上下文），窗口与目录结构保持不变（随时可重启），恢复只需一条命令，且窗口还在可以随手 `tail` 输出看当时发生了什么。

### 判定流程

```
这个 agent 是决策中枢吗？              ──是──► resident
这个任务需要保持外部进程/连接吗？      ──是──► resident
下一个任务紧接着就要用同一份大上下文吗？──是──► resident
它会被频繁打断追问吗？                ──是──► resident
        │否
        ▼
任务能完整写成一个契约吗？              ──是──► ephemeral
        │否
        ▼
考虑 checkpoint-then-retire
```

**默认 ephemeral**。选resident 必须在 `TEAM.md` 的 roster 表里写明理由——没有理由的常驻就是浪费。

## 会话恢复

### 三级降级

会话恢复能力因 agent CLI 而异（见 `agent-cli.md`）。统一按三级降级处理，**永远准备好走第 3 级**：

| 级别 | 方式 | 恢复程度 | 前置条件 |
| --- | --- | --- | --- |
| L1 原生 resume | `claude -r <session_id>` | 完整（含全部历史对话） | 会话 id 已登记、CLI 支持 |
| L2 快速续跑 | `claude -c` | 继续最近一次会话（不指定 id） | CLI 支持 |
| L3 冷重建 | 读 checkpoint + 决策 + 产出，重新投契约 | 只有"做到哪一步"，无历史细节 | 之前写好了落盘物|

**L3 必须总是可行。** 这不是降级方案，这是设计的锚点——正因为 L3 总是可行，L1/L2 失败才是可接受的损失，而不是灾难。

所以**checkpoint 是强制动作**。没有 checkpoint 的 ephemeral agent，等于没有生命周期管理。

### 会话登记

拉起 agent 后**立刻**登记会话 id，否则丢了就只能走 L3：

```bash
scripts/teamctl.py session set --team <name> --role builder-a \
  --session-id <id> --resume-cmd "claude -r <id>"
```

登记信息落盘在 `logs/sessions.json`，随时可查每个 agent 的会话 id 与恢复命令。

### 恢复流程

```bash
# L1/L2：恢复原生会话
scripts/teamctl.py session resume --team <name> --role builder-a
# → 打印出要执行的 resume 命令，并在目标 tmux 窗口执行

# L3：冷重建
scripts/teamctl.py checkpoint show --team <name> --role builder-a --task T3
# → 打印该agent 的 checkpoint 内容 + 需要重读的文件清单
```

冷重建时投放的指令模板：

> 你的上一个会话不可用，请从落盘信息恢复上下文：
> 1. 读 `TEAM.md` 了解团队目标
> 2. 读 `decisions.md`，不要推翻已有决策
> 3. 读 `logs/checkpoints/builder-a-T3.md` 了解你做到哪一步
> 4. 读 `contracts/builder-a.md` 了解边界与完成标准
> 5. 检查 `results/` 确认哪些已产出，**不要重做已完成部分**
> 6. 从 checkpoint 的"下一步"继续

第 5 条是关键——不明确它，agent 会重新做一遍已经做完的工作。

## Retire 与 tmux 窗口

**agent 进程退出 ≠ tmux 窗口关闭。** 这是两个独立的生命周期。

| 层 | retire 时| 说明 |
| --- | --- | --- |
| agent 进程 | 退出 | 释放内存与上下文 |
| 会话记录 | 保留 | `logs/sessions.json`，供 L1/L2 恢复 |
| checkpoint | 保留 | `logs/checkpoints/`，供 L3 恢复 |
| 事件记录 | 保留 | `logs/events.jsonl` |
| tmux 窗口 | **保留**（转成 shell） | 随时 `tail` 看历史输出、随手重启 agent |
| 产出文件 | 保留 | `results/`、`notes.md`、`decisions.md` |

保留窗口的好处：目录结构稳定（`at-<team>:<role>` 永远指向同一个角色）、历史输出可查、恢复是一条命令而不是一套流程。

**何时才真关窗口**：整个团队收摊时（`teamctl.py team kill`），或某个角色确定不再使用（lead 在 `TEAM.md` 里划掉该角色）。

## Block 与异常处理

agent 卡住时（判不出、撞契约冲突、依赖缺失、环境坏），正确做法是**停下上报，不是硬猜**：

1. agent 在 `notes.md` 追加条目：时间戳 + 角色 + 卡在哪 + 已试过什么
2. agent 登事件：`teamctl.py record --role <role> --event block --task T3 --summary "..."`
3. agent **向上 escalate**：`teamctl.py escalate --role <role> --task T3 --severity blocker --question "..." --tried "..."`
   （只找lead，不横向找 peer；详见 `governance.md`）
4. lead 处理队列：`teamctl.py ask list`，然后四选一：
   - **接手**：lead 自己处理（通常是低成本的小事）
   - **拆分**：把卡住的部分拆成更小的任务重新派
   - **改契约**：Stop Conditions 里列出的不确定性已被 lead 裁定 → 更新契约后继续
   - **取消**：该任务不再需要 → 标cancelled 并说明影响

**不要让 agent 反复重试卡住的事**——每重试一次就往会话里灌无用上下文，加速污染。配合预算的软超时一起用：卡住超过软超时即 checkpoint 收摊等答复，不要硬撑到硬上限。完整的 block 成因与首选处置对照表见 `governance.md`。

**反复退回的处理**用重试计数机制，不用"2 次即死"的一刀切：

## 状态机：任务级 vs 会话级

任务状态与会话状态是两套独立的状态机，不要混用。

**任务状态**（记在 `tasks.md`）：

```
pending ──► in_progress ──► done
                 ▲              │
                 └── needs-revision ◄──┘
```

**会话状态**（记在 `logs/sessions.json` 与事件流）：

```
spawned ──► working ──► idle ──► parked(窗口留 shell) ──► resumed ──► working
                                    │
                                    └──► gone (tmux 窗口也关了)
```

一个任务可以在同一个会话里完成多次（长连接 agent 连续接活），也可以一个会话只做一个任务（ephemeral）——**不要假设一对一**。

## 预算熔断对生命周期的影响

生命周期不是纯时间驱动，还要受**预算**约束（详见 `governance.md`）：

| 预算状态 | 生命周期动作 |
| --- | --- |
| 正常 | 按契约推进 |
| 超软超时（`per_task_min`） | 写 checkpoint → retire（checkpoint-then-retire），**不要硬撑** |
| 超硬上限（`hard_cap_min`） | 强制 checkpoint → retire → escalate 上报熔断，等 lead 重新评估 |
| 团队预算 80% | lead 收紧派活，优先收尾高价值任务 |
| 团队预算耗尽 | 停止派新任务，向用户汇报后再继续 |
| 180 分钟无事件 | 判定疑似空转/卡死 → `capture-pane` 核查窗口 |

**熔断时 checkpoint 是强制的**。没有 checkpoint 的熔断等于丢弃全部上下文，agent 只能从零重来——这是最坏的处置方式。