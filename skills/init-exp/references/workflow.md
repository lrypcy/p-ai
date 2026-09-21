# main 主导协作协议

main 窗口的 agent 是整个实验团队的**主导者**。本协议定义 main 如何制定目标、分配任务、判定完成。main 按「计划 → 执行 → 核验」循环推进，直到所有目标达成。

## 角色分工

- **main（主导者）**：加载实验内 `.agents/team-lead/` skill 获得主导职责。编辑 `goals.md` 与 `tasks.md`；分配任务给其他窗口；核验 `results/`、更新任务状态、判定完成或退回。
- **worker（执行者）**：从 `tasks.md` 领取任务；执行并把产出写入 `results/`；日志写入 `logs/`；完成后更新 `tasks.md` 状态为 `in_progress`/`done`。
- **logs / monitor（观察者）**：不执行任务，观察运行状态，异常时在 `notes.md` 记录。

协同靠共享文件系统：窗口之间不直接互相打字，任务与状态全部通过 `goals.md` / `tasks.md` / `notes.md` / `results/` 传递。团队模式与 skill 文件说明见实验内 `AGENTS.md` 与 `.agents/` 目录。

## 循环流程

### 1. 制定目标

main 在 `goals.md` 中写入目标。**每条目标必须包含可验证的验收标准**：

```markdown
## G1: <目标简述>

- 状态: open
- 验收标准:
  - [ ] <可验证的条件 1>
  - [ ] <可验证的条件 2>
```

### 2. 分配任务

main 在 `tasks.md` 中为每个目标拆解任务，标注负责人窗口与关联目标：

```markdown
| ID | 任务 | 负责人(窗口) | 关联目标 | 状态 | 完成标准 | 备注 |
|----|------|--------------|----------|------|----------|------|
| T1 | <任务> | worker | G1 | pending | <可验证标准> | |
```

分配后向对应窗口广播任务（可在该窗口运行 `cat tasks.md` 提示其领取）。

### 3. 执行

worker 领取任务后更新状态为 `in_progress`，执行，产出放入 `results/`。完成后：

1. 更新 `tasks.md` 对应行状态 → `done`。
2. 在 `notes.md` 追加一条记录（时间戳 + 窗口名 + 做了什么 + 结果摘要）。
3. 向 main 反馈（在窗口打印完成信息即可）。

### 4. 完成判定（main）

main 依据 `tasks.md` 中的**完成标准**与 `goals.md` 的**验收标准**核验 actual 产出：

- **满足** → 状态保持 `done`；若是目标最后一个任务，把 `goals.md` 中该目标状态改为 `done`，勾选验收标准。
- **不满足** → 状态改为 `needs-revision`，在备注写明缺陷与期望，退回给负责人窗口。
- 全部目标 `done` → 在 README 或 notes.md 汇总结果，宣告实验完成。

**涉及代码的核验补充**：凡任务产出涉及编程开发，main 除功能核验外还必须验收工程规范：

1. **开发规范**：代码遵循所使用语言/框架的典型工程实践，并沿用项目既有约定。
2. **Lint 通过**：运行项目声明的 lint / typecheck / format 校验命令并确认通过（无显式命令则运行对应 linter CLI，如 ruff、eslint、biome、golangci-lint、clippy）。
3. **无逃逸手段**：检查是否存在掩盖 lint 问题的 `# noqa`、`@ts-ignore`、`eslint-disable` 等；存在时必须能在备注给出站得住脚的理由。
4. 任一不满足 → 判定 `needs-revision` 并明确列出规范缺陷。

### 5. 复盘（可选）

实验收尾时，main 在 `notes.md` 末尾写入：结论、踩坑、可复用经验。

## Git 提交纪律

每个实验目录都是**独立 git 仓库**，文本文件与进展全部用 git 管理。**重大进展或独立进展必须单独 commit**，禁止把多个不相关进展混在一个 commit 里。

- **什么算一个 commit**：每个独立/可验证的进展单元。例如：
  - 一份目标/任务设定（goals/tasks 更新）
  - 一次实验运行的完整结果（某轮跑通、某组参数结果产出）
  - 一个独立结论/分析
  - 对既有结果的一次修正
- **何时必须 commit**：所有执行者完成一个任务、main 判定一个目标达成、产生一版可复现的结果时。
- **commit message 规范**：一句话说明该进展（动词开头 + 对象），如：
  - `run: 完成 baseline 首次运行，结果写入 results/`
  - `goal: G2 达成，验收标准全部通过`
  - `fix: 修正数据预处理漏样本问题`
- **执行规则**：
  1. main 完成目标设定后即 commit（goals.md/tasks.md/AGENTS.md 变更）。
  2. worker 完成任务并确认产出落盘后，commit 自己的成果；若共用同一仓库则先 `git pull`/`git fetch` 再提交（避免覆盖他人）。
  3. main 判定目标达成同 commit，保证每个里程碑可回退、可追溯。

> 若执行者无法 commit（如权限/冲突），把待提交变更留在工作区并在 `notes.md` 说明，由 main 统一提交。

## 状态机

```
pending ──► in_progress ──► done
                ▲              │
                └── needs-revision ◄──┘
```

## 冲突与异常

- 多 worker 并发时，**一个任务同一时刻只允许一个负责人窗口**。
- 发现任务被重复领取：后领取者主动释放，状态回 pending。
- 任务长时间卡住 `in_progress`：main 在备注标注卡住原因，决定接手、拆分或取消。
- 环境问题（命令缺失、权限、网络）：负责人先在 `notes.md` 记录，再尝试自行解决或向 main 报告。