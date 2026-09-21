#!/usr/bin/env bash
#
# init_experiment.sh - 在指定根目录下创建规范化实验目录骨架（含项目定制化适配）
#
# Usage:
#   init_experiment.sh [-t <type>] [-l <lang>] <root-dir> <experiment-name> [more-names...]
#
# Examples:
#   init_experiment.sh ~/lab llm-eval-run1
#   init_experiment.sh -t dev -l python ~/lab my-rest-api
#   init_experiment.sh -t ml -l python ~/lab bert-finetune
#
# 类型 (-t): lab(默认) | dev | data | ml | docs
#   按类型追加目录：dev→src tests；data→data notebooks；ml→data models notebooks；docs→docs
# 技术栈 (-l): python | node | go | rust | none
#   按技术栈定制：AGENTS.md 开发规范中的 lint 指南 + .gitignore 追加条目
#
# 创建结构：
#   <root-dir>/<name>/
#   ├── AGENTS.md     # agent 协作说明（main 后续按用户目标填写）
#   ├── README.md
#   ├── goals.md
#   ├── tasks.md
#   ├── notes.md
#   ├── results/
#   ├── logs/
#   ├── .agents/      # 实验内 skills（team 模式写 team-lead/ SKILL.md）
#   └── .gitignore
#
# 每个实验目录会初始化为独立 git 项目（git init）。
# 已存在的文件不会被覆盖；目录已存在时仅补缺；已有代码的项目不受 -t/-l 影响。

set -euo pipefail

# ---------- 参数 ----------
TYPE="lab"
LANG="none"
while getopts "t:l:" opt; do
  case "$opt" in
    t) TYPE="$OPTARG" ;;
    l) LANG="$OPTARG" ;;
    *) echo "用法: init_experiment.sh [-t type] [-l lang] <root-dir> <experiment-name> [more-names...]" >&2; exit 1 ;;
  esac
done
shift $((OPTIND - 1))

ROOT="${1:-}"
if [ -n "$ROOT" ]; then shift; fi
NAMES=("$@")

if [ -z "$ROOT" ] || [ "${#NAMES[@]}" -eq 0 ]; then
  echo "用法: init_experiment.sh [-t type] [-l lang] <root-dir> <experiment-name> [more-names...]" >&2
  exit 1
fi

# ---------- 定制化适配：类型/技术栈 → 骨架与规范 ----------
case "$TYPE" in
  lab|dev|data|ml|docs) ;;
  *) echo "⚠️  未知类型 '$TYPE'（lab/dev/data/ml/docs），按 lab 处理" >&2; TYPE="lab" ;;
esac

case "$LANG" in
  python|node|go|rust|none) ;;
  *) echo "⚠️  未知技术栈 '$LANG'（python/node/go/rust/none），按 none 处理" >&2; LANG="none" ;;
esac

# 类型 → 附加目录
case "$TYPE" in
  dev)  EXTRA_DIRS="src tests" ;;
  data) EXTRA_DIRS="data notebooks" ;;
  ml)   EXTRA_DIRS="data models notebooks" ;;
  docs) EXTRA_DIRS="docs" ;;
  *)    EXTRA_DIRS="" ;;
esac

# 类型 → 结构说明行（README/AGENTS.md 的目录清单）
case "$TYPE" in
  dev)  EXTRA_STRUCTURE=$'- \`src/\`      源码\n- \`tests/\`    测试' ;;
  data) EXTRA_STRUCTURE=$'- \`data/\`     数据集\n- \`notebooks/\` 分析 notebook' ;;
  ml)   EXTRA_STRUCTURE=$'- \`data/\`     数据集\n- \`models/\`   模型产物\n- \`notebooks/\` 训练/分析记录' ;;
  docs) EXTRA_STRUCTURE=$'- \`docs/\`     调研笔记、参考资料' ;;
  *)    EXTRA_STRUCTURE="" ;;
esac

# 技术栈 → .gitignore 追加
GITIGNORE_EXTRA=""
case "$LANG" in
  python) GITIGNORE_EXTRA=".venv/
venv/
.ruff_cache/
.pytest_cache/
dist/
build/
*.egg-info/" ;;
  node) GITIGNORE_EXTRA="node_modules/
.next/
dist/
*.tsbuildinfo" ;;
  go)    GITIGNORE_EXTRA="bin/" ;;
  rust)  GITIGNORE_EXTRA="target/" ;;
esac

# 技术栈 → AGENTS.md 开发规范（lint 指南）
case "$LANG" in
  python) LANG_POSS="python 的"
          LANG_COMM="python 的"
          LANG_LINT_GUIDE='默认 lint/类型检查工具链：ruff（ruff check + ruff format）与基于 pyright 的严格类型检查（配置见 pyproject.toml 的 [tool.ruff]/[tool.pyright]，或独立 ruff.toml/pyrightconfig.json）。每次改动后、提交前必须运行 ruff check、ruff format --check 与 pyright 并确认全部通过。禁止用 # noqa / # type: ignore 掩盖真实问题；确需放行须给出理由并记入 notes.md。' ;;
  node) LANG_POSS="node/typescript 的"
          LANG_COMM="node/typescript 的"
          LANG_LINT_GUIDE='默认 lint/format 工具链：biome（biome.json；运行 biome check）或 eslint + prettier。提交前必须运行 biome check（或 eslint .）与类型检查（tsc --noEmit）并确认通过。禁止用 @ts-ignore / eslint-disable 掩盖真实问题；确需放行须给出理由并记入 notes.md。' ;;
  go)   LANG_POSS="go 的"
          LANG_COMM="go 的"
          LANG_LINT_GUIDE='默认 format/lint：gofumpt 与 golangci-lint（配置 .golangci.yml）。提交前必须运行 gofumpt -l . 与 golangci-lint run 并确认通过。' ;;
  rust) LANG_POSS="rust 的"
          LANG_COMM="rust 的"
          LANG_LINT_GUIDE='默认 format/lint：rustfmt（cargo fmt --check）与 clippy（cargo clippy -- -D warnings）。提交前必须运行并确认通过。' ;;
  *)    LANG_POSS=""
          LANG_COMM="该语言的"
          LANG_LINT_GUIDE='存在 lint 配置（ruff/eslint/biome/golangci-lint/clippy 等）时，必须遵循对应 lint 指南：开发前先查看 lint 配置文件（.ruff.toml/.eslintrc*/.biome.json/golangci.yml/pyproject.toml 的 lint 段等）理解规则与启用/禁用项；新代码必须满足 lint 规则的通过标准（包括格式、未使用变量/导入、类型错误等）；提交前运行项目声明的 lint / typecheck / format 校验命令并确认通过。禁止为通过 lint 使用不规范的逃逸手段（盲目 # noqa/@ts-ignore/eslint-disable），确需放行须给出理由并记入 notes.md。' ;;
esac

sanitize() {
  # 安全化实验名：非字母数字统一转连字符，连续连字符折叠，去除首尾连字符
  echo "$1" | tr -c 'a-zA-Z0-9' '-' | sed 's/--*/-/g' | sed 's/^-*//; s/-*$//'
}

# ---------- 根目录 ----------
mkdir -p "$ROOT"
ROOT="$(cd "$ROOT" && pwd)"

# ---------- 骨架模板 ----------
write_skeleton() {
  local dir="$1" name="$2"

  mkdir -p "$dir/results" "$dir/logs" "$dir/.agents"
  for extra in $EXTRA_DIRS; do
    mkdir -p "$dir/$extra"
  done

  if [ ! -f "$dir/README.md" ]; then
    cat > "$dir/README.md" <<EOF
# $name

## 一句话说明

（实验目的）

## 背景 / 动机

（为什么做这个实验）

## 结构

- \`goals.md\`  目标与验收标准（main 制定）
- \`tasks.md\`  任务看板（main 分配，各窗口更新状态）
- \`notes.md\`  运行记录
- \`results/\`  结果输出
- \`logs/\`     运行日志
$EXTRA_STRUCTURE
EOF
  fi

  if [ ! -f "$dir/goals.md" ]; then
    cat > "$dir/goals.md" <<'EOF'
# 目标 (Goals)

> 由 main agent 制定。每条目标必须包含**可验证的验收标准**。

## G1: <目标简述>

- 状态: open
- 验收标准:
  - [ ] <可验证的条件 1>
  - [ ] <可验证的条件 2>
EOF
  fi

  if [ ! -f "$dir/tasks.md" ]; then
    cat > "$dir/tasks.md" <<'EOF'
# 任务看板 (Tasks)

> main 分配任务，各窗口更新状态。
> 状态机: pending → in_progress → done | needs-revision

| ID | 任务 | 负责人(窗口) | 关联目标 | 状态 | 完成标准 | 备注 |
|----|------|--------------|----------|------|----------|------|
| T1 | <任务> | worker | G1 | pending | <可验证> | |
EOF
  fi

  if [ ! -f "$dir/notes.md" ]; then
    cat > "$dir/notes.md" <<'EOF'
# 运行记录 (Notes)

<!-- MMDD HH:MM [窗口名] 记录内容 -->
EOF
  fi

  if [ ! -f "$dir/AGENTS.md" ]; then
    cat > "$dir/AGENTS.md" <<EOF
# $name 实验 - Agent 协作说明

> 本实验是独立 agent 项目（类型: $TYPE，技术栈: ${LANG:-none}）。main 窗口的 agent 是主导者。初始化时由 main 依据用户目标填写本文件。

## 目标 (Goal)

- **实验要验证/达成什么**：<由用户目标填入>
- **预期产出**：<可交付的结果>

## 目录约定

- \`AGENTS.md\` 本文件：agent 协作说明、目标与团队/流程说明
- \`.agents/\`  实验内 skills 目录（team 模式含 \`.agents/team-lead/\` 标准 skill，详见该目录 README）
- \`goals.md\`  目标与验收标准（main 制定）
- \`tasks.md\`  任务看板（main 分配，各窗口更新状态）
- \`notes.md\`  运行记录
- \`results/\`  结果输出
- \`logs/\`     运行日志
$EXTRA_STRUCTURE

## 团队模式

若本实验启用 team 模式（main 主导 + 多窗口协作）：

- 团队协作以**标准 skill** 固化于 **\`.agents/team-lead/\`**（\`SKILL.md\` + 可选 references/），main 窗口启动后加载该 skill，即获得主导者职责（制定目标 → 分配任务 → 判定完成）。
- 窗口布局与各窗口实际运行的 agent 见下方"团队布局"表。
- 若未启用 team 模式，本实验由单个 agent 直接操作，忽略 .agents/team-lead/。

## 团队布局 (tmux team)

| 窗口 | 角色 | 运行 agent | 职责 |
|------|------|-----------|------|
| main | 主导者 | opencode/pi/hermes... | 制定目标、分配任务、核验结果、判定完成 |
| worker | 执行者 | ... | 领取任务、执行、产出结果 |

> 窗口清单与各窗口实际运行的 agent 由实验启动时确定并回填。

## 协作规范

1. 目标见本文件"目标"与 \`goals.md\`，每条目标必须有可验证的验收标准。
2. main 在 \`tasks.md\` 分配任务，标注负责人窗口；执行者领取后更新状态。
3. 执行者产出写入 \`results/\`，运行日志写入 \`logs/\`，完成后更新 \`tasks.md\`。
4. main 依据验收标准核验结果，判定 done 或退回 needs-revision。

## 开发规范

涉及编程语言开发时，**必须遵循典型开发规范**：

- **通用规范**：遵守 ${LANG_POSS}典型工程实践——项目结构、命名约定、错误处理、模块边界、测试组织等。先读项目既有配置（配置文件/pyproject/package.json/go.mod 等）与目录结构，沿用已确立的约定。
- **Lint 指南**：${LANG_LINT_GUIDE}
- 若项目未配置 lint、空白起步：采用 ${LANG_COMM}社区公认的默认配置（如 ruff/black、biome/eslint recommended），并保持与已有代码一致。

## Git 规范

- 本目录是独立 git 项目，所有文本文件与进展用 git 管理。
- **重大进展或独立进展必须单独 commit**，commit message 说明进展内容。
EOF
  fi

  if [ ! -f "$dir/.agents/README.md" ]; then
    cat > "$dir/.agents/README.md" <<EOF
# .agents - 本实验的 skills 目录

本目录存放本实验专用的 **skills**（标准 skill 结构：\`<skill-name>/SKILL.md\` + 可选 references/ scripts/ assets/）。

- \`team-lead/\`  团队协作 skill：由 main 主导，制定目标、分配任务、判定完成。仅在需要 team 模式时创建（见 \`../AGENTS.md\`「团队模式」）。

main 窗口启动后加载对应 skill（如 \`team-lead\`）即可获得对应能力。
详细协作协议见 \`../AGENTS.md\` 。
EOF
    echo "   · .agents/ 已创建"
  fi

  if [ ! -f "$dir/.gitignore" ]; then
    cat > "$dir/.gitignore" <<EOF
.DS_Store
__pycache__/
*.pyc
*.pyo
TAGS
$GITIGNORE_EXTRA
EOF
  fi

  if [ ! -d "$dir/.git" ]; then
    git -C "$dir" init -q 2>/dev/null || git --git-dir="$dir/.git" init -q
    echo "   · git 已初始化"
  fi

  echo "✅ 实验目录: $dir (类型: $TYPE / 技术栈: $LANG)"
}

# ---------- 创建 ----------
for raw in "${NAMES[@]}"; do
  name="$(sanitize "$raw")"
  if [ -z "$name" ]; then
    echo "⚠️  跳过无效名称: '$raw'" >&2
    continue
  fi
  write_skeleton "$ROOT/$name" "$name"
done

echo ""
echo "📂 实验根目录: $ROOT"