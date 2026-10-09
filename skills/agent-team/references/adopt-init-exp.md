# init-exp team 模式 → agent-team 转调

## 为什么转调

`init-exp` 负责**实验目录骨架 + 项目定制化**（类型 × 技术栈 × lint 规范），`agent-team` 负责**团队协作治理**（角色、契约、生命周期、会话恢复、上报、预算、行为记录）。

两者原本各自实现了 team 协作，导致能力重复且不一致。**现在 `init-exp` 的 team 模式一律转调 `agent-team`**，不自己实现团队协议。

## 能力覆盖对照：init-exp 需要什么、agent-team 是否覆盖

| init-exp team 模式需要的能力 | agent-team 覆盖 | 位置 |
| --- | --- | --- |
| main 窗口作为主导者 | ✅ `lead` 角色 | org-model.md |
| 制定目标（goals.md） | ✅ 沿用 `goals.md`，TEAM.md 引用 | SKILL.md Step 1 |
| 分配任务、维护 tasks.md | ✅ tasks.md + task_assign/task_start 事件 | observability.md |
| 多窗口（main/worker） | ✅ 多角色多窗口 | org-model.md |
| worker 领取并执行任务 | ✅ 上下文契约八段 | context-protocol.md |
| main 核验结果判 done / needs-revision | ✅ 完成判定看产出 | SKILL.md 原则 6 |
| 产出放results/、日志放 logs/ | ✅ 同 | observability.md |
| git 提交纪律 | ✅ 同 | observability.md |
| **上下文契约**（init-exp 原本没有） | ✅ 八段契约 | context-protocol.md |
| **生命周期（resident/ephemeral）**（原本没有） | ✅ 完整 | lifecycle.md |
| **会话恢复**（原本没有） | ✅ 三级降级 | lifecycle.md |
| **上报通道**（原本没有） | ✅ 只向上 escalate | governance.md |
| **预算熔断**（原本没有） | ✅ 三级阈值 | governance.md |
| **重试换手**（原本没有） | ✅ 渐进三级 | governance.md |
| 结构化行为记录（原本只有 notes.md） | ✅ 三层 | observability.md |

**结论：agent-team 完全覆盖 init-exp team 模式所需能力，且额外提供 6 项原本缺失的治理能力。**

## 转调流程

### 1. init-exp 侧（照旧建实验骨架）

```bash
scripts/init_experiment.sh -t dev -l python "$ROOT" <exp-name>
```

产出的目录含`AGENTS.md` / `goals.md` / `tasks.md` / `notes.md` / `results/` / `logs/` / `.agents/`。

### 2. 判断要不要启用 team 模式

短任务、单agent 能做完的**不要开 team**（init-exp 的 solo 模式）。开team 的判据见 init-exp SKILL.md Step 3。

### 3. 执行 adopt 适配

```bash
# 从 agent-team skill 目录执行
scripts/teamctl.py --team <exp-name> adopt \
  --exp-dir "$ROOT/<exp-name>" \
  --lead-alias main \
  --session-name "exp-<exp-name>"
```

`adopt` **幂等**：缺什么补什么，已存在的一律跳过。可重复执行。

它做四件事：
1. 补齐 `logs/` 下的五个管控文件（events / inbox / attempts / sessions / budget）与 `checkpoints/`
2. 确保 `contracts/` 目录存在
3. 按参数初始化预算额度
4. 生成 `TEAM-MAPPING.md` 命名映射草案

### 4. 动态调整内容（**这一步不能跳过**）

adopt 只补文件，**不做语义改写**。以下调整必须由调用方agent 显式完成——因为它们需要理解实验的具体目标与技术栈，脚本无从判断。

#### 4.1 审校命名映射

读 `TEAM-MAPPING.md`，按实际窗口/角色填「本实验实际」列。常见映射：

| init-exp | agent-team | 说明 |
| --- | --- | --- |
| `main` 窗口 | `lead` 角色 | 直接沿用；adopt 的 `--lead-alias main` 就是这个 |
| `worker` 窗口 | `builder` 角色 | 职责是执行则填 builder；兼调研则填 researcher |
| `goals.md` | 沿用 | 不改文件，但要在 AGENTS.md 里声明它是目标唯一来源 |
| `tasks.md` 负责人列填**窗口名** | 填**角色名** | 关键改动：角色名跨 session 稳定，窗口名可能变 |
| `exp-<name>` session | 沿用 `exp-<name>` | agent-team 默认 `at-` 前缀是给独立团队用的；init-exp 实验沿用 `exp-` 更一致 |
| `AGENTS.md` | 增补 TEAM.md 的职能 | AGENTS.md 是 init-exp 的既有文件，不必改名，但要补上缺失的治理小节 |

#### 4.2 把映射合并进 AGENTS.md

在 init-exp 生成的 AGENTS.md「团队模式」小节里补上：

- **指向 `decisions.md`**（原init-exp 只有 goals/tasks/notes，缺决策账本）
- **指向 `contracts/`**（每个角色的八段契约）
- **指向 `logs/`**（events / inbox / budget / sessions / checkpoints 各是干什么的）
- **上报通道规则**（只向上 escalate，不横向）
- **预算阈值**（本次实验实际值，不是默认值）
- **reviewer 独立性档位**（本次各角色实际用哪个 CLI）

#### 4.3 为每个角色写契约

adopt 只建目录不写内容。**必须为每个实际角色写 `contracts/<role>.md`**，八段结构见 context-protocol.md。

沿用 init-exp 约定时注意：
- main 的契约要覆盖原 `team-lead` skill 的职责（制定目标 → 分配任务 → 判定完成）
- worker 的契约要覆盖原实验的开发规范（lint 指南在 AGENTS.md 里，指路过去）
- **不要把 AGENTS.md 的开发规范整段复制进契约**，只给路径：`见 AGENTS.md「开发规范」节`

#### 4.4 确认 tasks.md 的负责人列语义

init-exp 模板里是 `负责人(窗口)`，agent-team 是 `负责人(角色)`。选一：

- **推荐**：把表头改成 `负责人(角色)`，因为角色名稳定（窗口可能被关掉重建）
- 如果坚持填窗口名，则必须保证窗口名与角色名一一对应且不改变，否则 `status` 的角色状态推断会失准

### 5. 拉起 team 与后续

按 agent-team 的 SKILL.md Step 5~7 走。init-exp 原本用 `setup_tmux_team.sh` 建布局（minimal/standard/full），改用 agent-team 的方式：

```bash
tmux new-session -d -s exp-<name> -n main
tmux send-keys -t exp-<name>:main "<main-cmd>" Enter
tmux pipe-pane -t exp-<name>:main -o 'cat >> logs/main.pipe.log'
```

**`pipe-pane` 是 init-exp 原来没有的一步，必须补上**——它是 L1 行为记录的前提。

## init-exp 侧的改造要点

改`init-exp/SKILL.md` Step 3：

- 保留：询问是否启用 team、询问 main/worker 用哪个 agent、选择布局
- **删除**：内嵌的 team-lead skill 全文生成（收敛为指向 agent-team 契约）
- **新增**：执行 `teamctl.py adopt`
- **新增**：调用 agent-team 的动态调整清单（命名映射审校 + AGENTS.md 补节+ 写契约）
- **改写**：Step 4 的协作循环引用 agent-team 的 lifecycle.md / governance.md，不重复描述

## 冲突与遗留

| 问题 | 处理 |
| --- | --- |
| init-exp 的 `.agents/team-lead/` skill 还留着 | 建议收敛为一份只含"指向 agent-team 的契约与生命周期规范"的短 skill，不再重复协议正文 |
| init-exp 的 `setup_tmux_team.sh` 的 `logs`/`monitor` 观察窗口 | 保留（它们是观察者，非 agent），但要说明行为记录统一走 `logs/<role>.pipe.log` |
| init-exp 的 `workflow.md` 与 agent-team 的 `lifecycle.md` 有重叠 | init-exp 的 `workflow.md` 保留实验特有的状态机与 git 纪律细节，通用生命周期部分改为引用 |
| 老实验（已建好、无管控文件） |跑一次 `adopt` 即可接入，不需要重建 |