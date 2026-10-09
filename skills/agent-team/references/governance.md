# 治理：上报通道、预算熔断、重试换手

本文覆盖团队的**过程治理**三件事：信息怎么向上流通、钱怎么花不超、反复失败时怎么换手。

---

## 一、上报通道（只允许向上）

### 设计：单向树，不允许横向

```
        ┌─────────────────────────────┐
        │          lead               │  ← 通道终点
        └──────────┬──────────────────┘
        ┌──────────┼──────────┐
     builder-a  builder-b  researcher   ← 只能向上 escalate
```

**peer 之间不能直接通信。** 这不是功能缺失，是刻意设计：

| 如果允许横向 | 后果 |
| --- | --- |
| 两个 peer 同时改一个文件 | 互相覆盖，且没有单一裁决者 |
| peer A 告诉 peer B 一个未经lead 确认的约定 | 约定扩散到全团队但无人负责 |
| 拓扑复杂度 | N 个 agent 全连通是 O(N²) 条通道，N=6 就是 15 条 |

**peer 需要 peer 的信息时，走 lead 中转**：peer  escalate → lead 判断 → lead 决定是回答自己、还是改契约、还是派新任务给另一个 peer。

### 三个严重度

| severity | 含义 | agent 该怎么做 |
| --- | --- | --- |
| `blocker` | 不可能自行决定，影响正确性 | **立即停**，写 checkpoint，退出 agent 等答复 |
| `question` | 可以先干别的，但这个结论影响后续 | 继续做**不依赖该答复**的部分，不要自行拍板 |
| `info` | 知会 lead，不阻塞 | 继续干活，lead 看到后自行判断要不要处理 |

选错严重度的代价：`blocker` 滥用会让 agent 频繁停摆等答复（吞吐下降）；`question` 用成 blocker 会让本可并行的任务被串行化。

### 用法

```bash
# agent 上报
scripts/teamctl.py escalate --role builder-a --task T1 --severity blocker \
  --question "page_size 上限截断应返回 100 条还是报 400？契约未定义" \
  --tried "查了 docs/api-design.md，没有语义说明"

# lead 看待答队列（按严重度排序）
scripts/teamctl.py ask list

# lead 答复
scripts/teamctl.py ask answer --id E1791574523 --answer "返回 100 条，不报错。契约已更新。"
```

**`--tried` 必须填**：它让 lead 知道 agent 已经排除过哪些可能，避免给出 agent 自己已经验证过的无效建议。

**答复本身必须落盘**：`ask answer` 会记事件，但 lead 还要把结论写进被问询角色的契约补充或 `decisions.md`——否则答复只存在于 lead 的会话里，下一个冷重建的 agent 拿不到。

### 与黑板模式的关系

上报通道**不替代**黑板：

- 黑板（`results/`、`decisions.md`）传的是**结论与产出**，用于跨任务传递
- 上报通道传的是**过程中的疑问与阻塞**，用于同一时刻的交互

区别在于：黑板是异步持久（结论永久有效），上报是同步（答复解决后即失效，但事件记录保留）。

---

## 二、预算与熔断

### 三级阈值

| 阈值 | 默认 | 触发后的动作 |
| --- | --- | --- |
| **软超时** `per_task_min` | 60 分钟 | 建议写 checkpoint 后收摊（checkpoint-then-retire），别硬撑 |
| **硬上限** `hard_cap_min` | 120 分钟 | **必须立即 checkpoint 并上报熔断**，不得继续 |
| **团队总预算** `total_min` | 600 分钟 | 停止派新任务，先向用户汇报 |

软超时是"该收摊了"的提醒，硬上限是"必须停"的强约束。区别在于：软超时收摊后 agent 可恢复；硬上限触发的是熔断，需要 lead 重新评估任务是否值得继续。

### 按角色差异化

不同角色的任务耗时天然不同。给慢角色（如做基准测试的 researcher）单独放宽：

```bash
scripts/teamctl.py budget set --role researcher --role-min 180
```

### 用法

```bash
# 配置
scripts/teamctl.py budget set --per-task-min 60 --hard-cap-min 120 --total-min 600

# 任务过程中记账（agent 自行按节奏调用）
scripts/teamctl.py budget spend --role builder-a --task T1 --minutes 25

# 团队视角检查
scripts/teamctl.py budget check
```

记账的`elapsed_min` 是**该任务的累计耗时**（脚本自动 rollup，同一任务多次 spend 会累加），不是本次增量。

### 空转检测

`budget check` 与 `status` 都会检测：**最近一条事件距今超过 180 分钟** → 判定疑似空转/卡死。

卡死的 agent 在持续消耗 token 但零产出。这是最隐蔽的预算杀手——没有 block 事件、没有错误、就是不动了。检测到后的处置：

```bash
tmux capture-pane -t at-<team>:<role> -p -S -50# 看它最后停在哪
```

常见原因：agent 在等一个永不结束的交互式命令；agent 的某个工具调用挂住了。

### 熔断后的标准动作

硬上限触发后，lead 按此顺序处理：

1. agent 写 checkpoint（**这是强制的**，否则熔断等于丢弃上下文）
2. agent 退出，窗口留作 shell
3. lead 读 checkpoint，判断：是任务定义有问题？还是这个 agent 不适合做？还是要拆？
4. 决定降预算继续 / 改契约重派 / 换角色 / 取消并上报用户

**不允许的做法**：熔断后不写 checkpoint 直接重开agent。那样会丢掉全部中间状态，回到"从零开始"的原点。

---

## 三、重试与换手（渐进式，不搞2 次就死）

### 为什么不用「2 次失败即停」

2 次容限会**误杀可救的任务**。实际情况：

- 前 1~2 次失败常常是 agent 对边界理解不清 → 补契约就能救
- 中间几次失败往往是任务范围太大 → 拆小就能救
- 后期反复失败才是匹配问题 → 换角色

一刀切在 2 处砍掉会把大量本可救的任务判死，用户会看到"AI 动不动就放弃"。

### 三级渐进策略

| 累计退回次数 | 判定 | 处置 |
| --- | --- | --- |
| ≤ 3 | ✅ 同角色可继续 | 按 needs-revision 的具体缺陷重做。若缺陷指向理解偏差，在契约里补明确边界 |
| 4~ 6 | 🟡 需换角度 | **不要再让同角色原样重做**。① lead 改写契约，把缺陷变成显式的 Do-Not-Touch / 完成标准；② 缩小任务范围再派；③ 补 checkpoint 让 agent 知道上次卡在哪 |
| ≥ 7 | 🔴 强烈建议换角色或拆任务 | 同角色反复失败通常是**任务定义/匹配**问题，不是执行问题。① 换另一个角色（不同 CLI/模型更好）；② 拆到更小；③ 评估这个任务是否该做 |

上限参考值**可到 10 次**，但**总时长仍受预算约束**：一个 30 分钟软超时的任务退回 7 次已经烧掉 210 分钟，多半已触发团队预算告警。**次数与时间双重约束，次数宽松、时间严格。**

### 用法

```bash
# lead 判定 needs-revision 时登记
scripts/teamctl.py attempts bump --role builder-a --task T3 --reason "分页参数名与前端不一致"

# 查看某任务的退回历史与换手建议
scripts/teamctl.py attempts judge --task T3
scripts/teamctl.py attempts list

# status 里会自动标出 >=4 次的任务
```

### 换手时优先换什么

按性价比排序：

1. **换契约表述**（最便宜）——把 needs-revision 的缺陷直接写进 Stop Conditions 或 Done Criteria
2. **换任务粒度**——拆小，降低单次失败面
3. **换 checkpoint**——让 agent 知道上次卡在哪，避免原地打转
4. **换角色**——不同 CLI / 不同模型，跳出系统性盲区
5. **换目标**——承认这个任务不该做，向用户汇报并取消

**注意**：换角色只在第 4 级才考虑。绝大多数"反复失败"是前三级问题（契约不清 / 范围太大 / 缺上下文），换角色只是掩盖症状。

---

## 四、block 的标准处置

block 事件（agent 卡住）与上报通道的 `blocker` 级escalate 是同一件事的两个记录面：agent 主动登block 事件，同时 escalate 上报。

lead 收到 block 后的四选一（与 `lifecycle.md` 的 block 处理一致）：

| 处置 | 适用 |
| --- | --- |
| **接手** | lead 自己处理（通常是低成本小事） |
| **拆分** | 卡住的部分拆成更小的任务重新派 |
| **改契约** | Stop Conditions 里的不确定性已被裁定 → 更新契约后继续 |
| **取消** | 该任务不再需要 → 标cancelled 并说明影响 |

**不要让 agent 反复重试卡住的事**——每重试一次就往会话里灌无用上下文，加速污染。配合预算的软超时一起用：卡住超过软超时即 checkpoint 收摊，等 lead 答复，而不是硬撑到硬上限。

### 常见 block 成因与首选处置

| 成因 | 首选处置 |
| --- | --- |
| 契约未定义的语义（上限截断返回还是报错） | 改契约（lead 裁定） |
| 与其他 agent 的产出冲突 | 拆分（划清文件边界） |
| 依赖缺失 / 环境坏 | 接手（lead 修环境） |
| 任务范围过大 | 拆分（拆到单次能完成） |
| 需要超出授权的决策 | 改契约（lead 授权或明确禁止） |
| 目标本身不合理 | 取消（上报用户） |