# 项目定制化适配指南

初始化实验不是套通用模板，而是要**针对具体项目画像做定制适配**。本指南定义类型 × 技术栈的适配矩阵，供初始化的 main/主 agent 使用。

## 适配输入（项目画像）

初始化时必须向用户收集以下信息（缺省用默认值，但涉及编程开发时必须确认技术栈）：

| 画像维度 | 取值 | 默认 |
|---|---|---|
| 实验类型 `-t` | `lab`（通用实验）/ `dev`（软件开发）/ `data`（数据分析）/ `ml`（模型训练）/ `docs`（调研文档） | `lab` |
| 技术栈 `-l` | `python` / `node`（TS/JS）/ `go` / `rust` / `none`（无代码） | `python`（type=dev/data/ml 时）、`none`（否则） |
| 是否已有代码 | 空目录 / 已有项目文件 | 空目录 |

## 类型 × 技术栈 → 目录骨架

基础骨架固定包含：`AGENTS.md` `README.md` `goals.md` `tasks.md` `notes.md` `results/` `logs/` `.agents/`。按类型追加：

| 类型 | 追加目录（相对实验根） | 典型用途 |
|---|---|---|
| `lab` | （无） | 通用验证实验 |
| `dev` | `src/` `tests/` | 源码与测试分离 |
| `data` | `data/` `notebooks/` | 数据集、分析 notebook |
| `ml` | `data/` `models/` `notebooks/` | 数据集、模型产物、训练记录 |
| `docs` | `docs/` | 调研笔记、参考资料 |

## 技术栈 → lint 指南（写入 AGENTS.md「开发规范」）

| 技术栈 | Lint 指南 |
|---|---|
| `python` | ruff（`ruff check` + `ruff format --check`）+ 基于 pyright 的类型检查（pyproject.toml 或 ruff.toml） |
| `node` | biome（`biome check`）或 eslint + prettier |
| `go` | gofumpt（`gofumpt -l .`）+ golangci-lint（.golangci.yml） |
| `rust` | rustfmt（`cargo fmt --check`）+ clippy（`cargo clippy -- -D warnings`） |
| `none` | 通用 lint 指南（存在配置则遵循） |

对应 `.gitignore` 追加条目：

| 技术栈 | .gitignore 追加 |
|---|---|
| `python` | `.venv/` `venv/` `.ruff_cache/` `.pytest_cache/` `dist/` `build/` `*.egg-info/` |
| `node` | `node_modules/` `.next/` `dist/` `*.tsbuildinfo` |
| `go` | `bin/` |
| `rust` | `target/` |
| `none` | （无追加） |

## 已有代码时的适配

若目标实验目录已存在代码，**不要覆盖**任何既有文件，脚本只补缺。初始化后 main 必须：

1. 读取既有配置文件（`pyproject.toml`/`package.json`/`go.mod`/`Cargo.toml`/editorconfig 等）与目录结构。
2. 以既有配置与 `.agent` 约定为准，把 AGENTS.md 的「开发规范」改写为该项目实际的 lint/typecheck 命令。
3. 检查是否已有 git 仓库：有则跳过 `git init`；无则初始化。
4. 把发现的既有约定在 `notes.md` 记录一笔，供团队后续遵循。

## 调用方式

```bash
# 通用实验，默认
scripts/init_experiment.sh "$ROOT" <name>

# 显式指定类型 + 技术栈
scripts/init_experiment.sh -t dev -l python "$ROOT" <name>
scripts/init_experiment.sh -t ml -l python "$ROOT" <name>
scripts/init_experiment.sh -t docs -l node "$ROOT" <name>
```

> 一次创建多个实验时也可带选项（`-t/-l` 作用于名单内全部实验）；若各实验画像不同，则分批调用或事后对单个实验手动补适配（修订 AGENTS.md 与 .gitignore）。