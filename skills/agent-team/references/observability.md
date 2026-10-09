# 行为记录规范

## 为什么需要

多 agent 团队出问题时，事后能回答的唯一问题来自记录：

- 这个产出是谁做的、什么时候做的、依据什么决策？
- 这个文件谁改的？为什么改？
- 某个 agent 为什么卡住了？它试过什么？
- 团队实际花在了哪里？

没有记录的团队在问题出现时只能靠猜。没有记录也没有 checkpoint 的 agent，等于**上下文只能靠运气恢复**。

## 三层记录

| 层 | 记录什么 | 落点| 粒度 | 谁写 |
| --- | --- | --- | --- | --- |
| **L1 管道原始输出** | 窗口里agent 说的每一个字 | `logs/<role>.pipe.log` | 原始、不加工 | tmux pipe-pane 自动 |
| **L2 结构化事件** | 谁、何时、做了什么、结果 | `logs/events.jsonl` | 半结构化 | agent 主动 + lead 登记 |
| **L3 决策账本** | 为什么这么选 | `decisions.md` | 人类可读 | lead（决策时刻） |

三层不可互相替代：L1 完整但难读，L2 可查询但不完整，L3 信息密度最高但只覆盖决策点。

## L1：tmux pipe-pane 原始输出

**拉起每个 agent 窗口后立刻开pipe**：

```bash
tmux pipe-pane -t at-<team>:<role> -o 'cat >> logs/<role>.pipe.log'
```

之后 agent 在窗口里的一切输出都会追加到 `logs/<role>.pipe.log`，agent 退出也不会丢。

用途：

- **事后诊断**：agent 退休后，想知道它当时到底干了什么、报错在第几行
- **卡住时诊断**：`tail -50 logs/<role>.pipe.log` 比 `capture-pane` 更完整（包含已滚出屏幕的历史）
- **会话丢失时补档**：L3 冷重建时，如果 agent 忘了自己做过什么，先读自己的 pipe log

注意：pipe 日志会很大，长任务完成后建议压缩或按轮次切分（如 `gzip` 或改名为 `T1.pipe.log`）。

## L2：事件流（events.jsonl）

JSON Lines，一行一个事件，追加写入。便于 `grep` / `jq` 查询。

### 事件 schema

```json
{
  "ts": "2026-10-10T03:20:11+08:00",
  "team": "at-refactor",
  "role": "builder-a",
  "event": "task_done",
  "task": "T3",
  "summary": "为 /api/search 增加分页参数，pytest 3 passed",
  "artifacts": ["src/api/search.py", "tests/test_search.py", "results/T3-report.md"],
  "elapsed_min": 23
}
```

`summary` 是**必填且要具体**。禁止写"完成了任务"、"搞定了"、"进展顺利"这类无信息量的描述。好的 summary 让人不看产出就知道发生了什么。

### 事件类型

| event | 何时记 | 关键字段 |
| --- | --- | --- |
| `team_spawn` | 团队拉起 | team、roles、cli_map |
| `task_assign` | lead 派活 | task、role、mode |
| `task_start` | agent 开始干活 | task |
| `task_done` | agent 产出完成 | task、summary、artifacts |
| `needs_revision` | lead 判定不通过 | task、summary（缺陷描述）|
| `checkpoint` | agent 写检查点 | task、summary（下一步） |
| `block` | agent 卡住 | task、summary（卡点、已试过什么） |
| `decision` | lead 做出决策 | task、summary（决策内容） |
| `session_spawn` | agent 窗口拉起 | role、cli、session_id |
| `session_retire` | agent 退出 | role、reason |
| `session_resume` | 会话恢复 | role、level（L1/L2/L3） |
| `review_verdict` | reviewer 结论 | task、verdict（pass/needs_revision）、summary |

### 记录命令

```bash
scripts/teamctl.py record --team <name> --role builder-a \
  --event task_done --task T3 \
  --summary "为 /api/search 增加分页参数，pytest 3 passed" \
  --artifacts "src/api/search.py,tests/test_search.py,results/T3-report.md"
```

**lead 与 agent 都要记**：

- **agent 记**自己任务的起止、卡点、checkpoint
- **lead 记**派活、验收结论、决策

不要指望 agent 自发记。lead 在派活时就把"完成后请运行teamctl.py record"写进契约的 Deliverables 段。

## L3：决策账本（decisions.md）

**这是团队最值钱、也最容易空着的一份文件。** 它记录"为什么"，而不只是"做了什么"——后者在 `notes.md` 里已经有了。

### 条目格式

```markdown
## D3 · 分页参数命名固定为 page / page_size
- 时间：2026-10-10
- 决策人：lead
- 相关：T3、builder-a
- 背景：前端需要两个参数控制页码和每页条数，命名有3 种候选
- 选择：page / page_size（不用 offset / limit，理由：与前端已约定的 query 名一致）
- 否决的备选：offset/limit（语义正确但与前端冲突）、skip/take（歧义，take 可理解为数量）
- 影响：builder-a 直接实现；后续 API 新增分页一律沿用
- 复议条件：若前端 API 变更，可重新讨论
```

### 什么时候必须记

- 任务分配（谁做什么）
- 方案选型（为什么选A 不选 B）
- 契约变更（改了 agent 的边界或完成标准）
- 验收判断（为什么判pass / 判 needs-revision）
- 模式决策（为什么某个 agent 走 resident）

### 写法要求

- **写否决的备选和理由**——只写"选了 A"的信息量为零
- **写影响范围**——谁受影响、后续是否沿用
- **写复议条件**——什么情况下这个决策该被重新审视
- 决策变更**追加**新条目，不改旧条目（保留决策演化史）

## notes.md：协作流水

逐条追加的时间戳记录，用于还原时间线。

```markdown
- 2026-10-10 03:20 | lead | 分配 T3 给 builder-a（ephemeral 模式），契约见 contracts/builder-a.md
- 2026-10-10 03:41 | builder-a | T3 完成，pytest 3 passed，产出见 results/T3-report.md
- 2026-10-10 03:45 | reviewer | T3 核验通过。补充：page_size 上限行为与契约一致
- 2026-10-10 04:02 | lead | D3 决策：分页参数固定 page/page_size
```

**只追加，不改他人行。** 这是 `notes.md` 唯一的写入规则。

## Checkpoint 规范

checkpoint 是 L3 冷重建的唯一依据，必须结构化。

落盘在 `logs/checkpoints/<role>-<task>.md`：

```markdown
# Checkpoint · builder-a · T3

- 时间：2026-10-10 03:40
- 会话 id：a1b2c3d4（若已登记；未登记则写"未登记"）

## 做到哪一步
已完成：`src/api/search.py` 的 page/page_size 参数实现
已完成：`tests/test_search.py` 三个用例（默认分页 / 显式页码 / 上限截断）
未开始：跑pytest 验证、写 `results/T3-report.md`

## 已确定的决策（不要推翻）
- 参数命名 page/page_size（见 decisions.md D3）
- page_size 上限 100

## 下一步（恢复时从这里继续）
1. 运行 `pytest -q tests/test_search.py`
2. 若全绿，写 results/T3-report.md（含验证方式段）
3. 登事件 task_done 并上报 lead

## 待解决的疑问
- 上限截断是返回 100 条还是报 400？已按返回截断实现，若 lead 判定应报错需改。

## 不要重做的部分
-三个测试用例已写好，不要重新写
```

关键段落是**"已确定的决策（不要推翻）"**和**"不要重做的部分"**——没有这两段，冷重建的 agent 会推翻已有决策或重复劳动。

写入命令：

```bash
scripts/teamctl.py checkpoint write --team <name> --role builder-a --task T3 --file <path>
```

## Git 纪律

团队目录是独立 git 仓库，文本文件与进展全部用 git 管理。**每个独立/可验证的进展单元单独commit**，禁止把不相关进展混进一次提交。

算一个 commit 的粒度：

- 一次目标/任务设定（tasks.md / contracts 变更）
- 一次实验运行的完整结果
- 一个独立结论/分析
- 对既有结果的一次修正

commit message 用「动词开头 + 对象」：

```
run: 完成 baseline 首次运行，结果写入 results/
goal: G2 达成，验收标准全部通过
fix: 修正数据预处理漏样本问题
dec: D3 分页参数固定 page/page_size
```

**协作纪律**：共用同一仓库时，先 `git pull`/`git fetch` 再提交，避免覆盖他人。无法 commit 的（权限/冲突）把变更留在工作区并在 `notes.md` 说明，由 lead 统一提交。

**不要提交 `logs/*.pipe.log`**（体积大、可再生），但要提交 `logs/events.jsonl`、`logs/checkpoints/`、`logs/sessions.json`——这些是决策依据。`.gitignore` 里要写明：

```
logs/*.pipe.log
logs/*.pipe.log.*
```

## 团队全景快照

`teamctl.py status` 输出。用于快速掌握团队状态、判断是否可以收摊：

- 各角色当前状态（working / idle / parked / gone）
- 任务看板统计（pending / in_progress / done / needs-revision）
- 最近 N 条事件
- 已登记的会话 id 与恢复命令
- 待处理 block

**收摊前必须跑一次并逐项核验**，尤其是 needs-revision 与 block 两项。

## 反面模式清单

| 反面模式 | 后果 | 正确做法 |
| --- | --- | --- |
| 不开 pipe-pane | agent 退出后无法追溯 | 拉起窗口立刻开 pipe |
| agent 只在对话里汇报 | 进程一退信息全丢 | 强制写 `results/` + 登事件 |
| decisions.md 只写"做了什么" | 决策理由丢失，无法复议 | 写清备选与否决理由 |
| lead 不实际核验产出就判 done | 质量崩盘 | 打开 `results/` 逐条对 Done Criteria |
| builder 自评 | 系统性放过自己的问题 | reviewer 独立验收（最低档：reviewer ≠ builder） |
| 契约里粘贴大段代码 | 上下文膨胀 + 内容过期 | 只给路径 |
| 缺 checkpoint 就 retire | 会话丢了只能从头来 | checkpoint 是 retire 的前置动作 |
| 所有 agent 都常驻 | 上下文稀释 + 资源浪费 | 默认 ephemeral，resident 需要理由 |
| 两个 agent 改同一文件 | 冲突、丢改动 | 契约写 Do-Not-Touch，上报 lead |
| **agent 横向找 peer 问东问西** | 多源真相、互相覆盖 | 只向上 escalate，由 lead 中转 |
| **无限重试卡住的任务** | 会话被无用上下文灌满 | escalate 上报 + checkpoint 收摊，等 lead 裁定 |
| **无预算约束放任跑** | 空转烧钱、无限返工 | 设软超时/硬上限/团队总预算，定期 `budget check` |
| **2 次失败就判死** | 误杀本可救的任务 | 渐进换手（≤3 继续 / 4-6 换角度 / ≥7 换角色） |
| **adopt 后跳过动态调整** | 语义错位，团队按错的约定跑 | 审校映射、改表头、补 AGENTS.md、写契约 |