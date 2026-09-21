#!/usr/bin/env bash
#
# setup_tmux_team.sh - 为实验创建独立 tmux session 与命名窗口团队
#
# Usage:
#   setup_tmux_team.sh <session-name> <layout> <main-command> [worker-command]
#
# layout:
#   minimal   -> 只有 main
#   standard  -> main + worker          (默认)
#   full      -> main + worker + logs + monitor
#
# Example:
#   setup_tmux_team.sh exp-llm-eval standard "opencode" "pi"
#
# 说明:
#   - 若同名 session 已存在会先清理再重建。
#   - main/worker 窗口运行用户指定的 agent 命令 (opencode/pi/hermes/claude 等)。
#   - logs 窗口为 shell，预置 tail -f 日志提示；monitor 窗口运行 top。
#   - 脚本不会自动 attach，端到端验证后打印 attach 提示。

set -euo pipefail

usage() {
  echo "用法: setup_tmux_team.sh <session-name> <layout> <main-command> [worker-command]" >&2
  echo "  layout: minimal | standard | full (默认 standard)" >&2
  exit 1
}

SESSION="${1:-}"
LAYOUT="${2:-standard}"
MAIN_CMD="${3:-}"
WORKER_CMD="${4:-}"

[ -n "$SESSION" ] && [ -n "$MAIN_CMD" ] || usage
case "$LAYOUT" in
  minimal|standard|full) ;;
  *) echo "未知 layout: $LAYOUT" >&2; usage ;;
esac
[ "$LAYOUT" = "minimal" ] && WORKER_CMD=""

if ! command -v tmux >/dev/null 2>&1; then
  echo "❌ 未找到 tmux，请先安装 (brew install tmux)。" >&2
  exit 1
fi

# ---------- 清理已存在 session ----------
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "♻️  清理已存在的 session: $SESSION"
  tmux kill-session -t "$SESSION"
fi

# ---------- 创建 main 窗口 (session 首个窗口) ----------
tmux new-session -d -s "$SESSION" -n main
tmux send-keys -t "$SESSION:main" "$MAIN_CMD" Enter
echo "窗口  main      -> $MAIN_CMD"

# ---------- worker ----------
if [ "$LAYOUT" = "standard" ] || [ "$LAYOUT" = "full" ]; then
  tmux new-window -t "$SESSION" -n worker
  tmux send-keys -t "$SESSION:worker" "$WORKER_CMD" Enter
  echo "窗口  worker    -> $WORKER_CMD"
fi

# ---------- logs & monitor (full) ----------
if [ "$LAYOUT" = "full" ]; then
  tmux new-window -t "$SESSION" -n logs
  tmux send-keys -t "$SESSION:logs" "echo 'logs 窗口: tail -f 观察实验日志'; ls -d logs 2>/dev/null || mkdir -p logs" Enter
  echo "窗口  logs      -> shell (日志观察)"

  tmux new-window -t "$SESSION" -n monitor
  tmux send-keys -t "$SESSION:monitor" "top" Enter
  echo "窗口  monitor   -> top (资源监控)"
fi

# ---------- 回到 main 并输出信息 ----------
tmux select-window -t "$SESSION:main"

echo ""
echo "✅ tmux team 就绪: session=$SESSION layout=$LAYOUT"
echo "   窗口: $(tmux list-windows -t "$SESSION" -F '#'W | paste -sd ',' -)"
echo "   进入: tmux attach -t $SESSION"