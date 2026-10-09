#!/usr/bin/env python3
"""teamctl.py - Agent 团队运行时管控工具

子命令
------
init       初始化事件流与团队配置（幂等）
record     记录一条行为化事件到 logs/events.jsonl
escalate   向上上报（worker → lead），写入待答问题队列并提醒 lead
ask        查看 / 回答上报队列（lead 侧处理 inbox）
session    登记 / 查看 / 恢复 agent 会话（logs/sessions.json）
checkpoint 写 / 查看 agent 检查点（logs/checkpoints/<role>-<task>.md）
budget     预算与熔断：设额度 / 记账 / 超限检查 / 空转检测
attempts   重试计数：登记退回 / 按策略判断是否该换手
im         人机通道：check 查配置 / init 配置 / test 验证 / ask 向用户提问 / answer 记录答复
status     团队全景快照（角色状态 + 任务统计 + 预算 + IM 通道 + 最近事件 + 待处理 block）
adopt      把既有实验目录适配为 agent-team 团队（供 init-exp team 模式转调）
team kill  归档并销毁团队（先出快照，再可选kill tmux session）

设计约束
--------
* 只依赖标准库，零第三方依赖。
* 所有写入都是追加语义，不覆盖既有记录。
* 失败即退出，不静默吞错——行为记录工具本身出错必须可见。
* 通道方向只允许自下而上（worker → lead）。横向 peer 通信一律不支持。
* webhook URL 只存环境变量名，不明文落盘（配置文件通常会进 git）。
* IM 配置是幂等的：已验证过的配置不重复询问用户。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
EVENTS_FILE = os.path.join("logs", "events.jsonl")
SESSIONS_FILE = os.path.join("logs", "sessions.json")
INBOX_FILE = os.path.join("logs", "inbox.jsonl")
BUDGET_FILE = os.path.join("logs", "budget.json")
ATTEMPTS_FILE = os.path.join("logs", "attempts.jsonl")
IM_FILE = os.path.join("logs", "im-channel.json")
CHECKPOINT_DIR = os.path.join("logs", "checkpoints")

# 全局 IM 配置：一台机器一个通道，各团队默认继承，避免重复配置
GLOBAL_IM = os.path.join(os.path.expanduser("~"), ".workbuddy", "agent-team", "im.json")

IM_TIERS = {
    "L0": "只发不收：群机器人 webhook（lead 能推送，用户回复 lead 收不到）",
    "L1": "出向 + tmux 入向（推荐默认）：webhook 提问，tmux attach 回答",
    "L2": "全双向：飞书自建应用 + 事件订阅（入向尚未实现，当前仍走 tmux 回答）",
}

# L2 入向接收尚未实现——配置会被记录，但必须如实告知用户不要误以为可用
L2_INBOUND_IMPLEMENTED = False

IM_CHANNELS = {
    "feishu": "飞书（群机器人 webhook；L2 需飞书自建应用）",
    "wecom": "企业微信（群机器人 webhook）",
    "dingtalk": "钉钉（群机器人 webhook）",
    "none": "不配置：lead 需要确认时直接在对话里问用户",
}

L2_VERIFY_MODES = {
    "longconn": "长连接（推荐）：SDK 主动建 websocket，无需公网回调地址",
    "callback": "事件回调：飞书 POST 到你的公网地址，需要内网穿透",
}


# ---------------------------------------------------------------- helpers

def now_iso() -> str:
    return datetime.now(CST).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    """生成带毫秒的短 ID，避免同一秒内多次调用产生重复 ID。"""
    return f"{prefix}{datetime.now(CST).strftime('%Y%m%d%H%M%S%f')[:-3]}"


def die(msg: str, code: int = 1):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def safe_name(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]", "-", name).strip("-")
    return s or "unnamed"


def find_team_dir(team: str, explicit: str | None = None) -> str:
    """定位团队目录。优先显式路径，否则从 cwd 向上查找含 TEAM.md 的目录。"""
    if explicit:
        if not os.path.isdir(explicit):
            die(f"目录不存在: {explicit}")
        return os.path.abspath(explicit)
    cur = os.path.abspath(team)
    if os.path.isdir(cur):
        return cur
    walk = os.path.abspath(team)
    for _ in range(6):
        walk = os.path.dirname(walk)
        if os.path.isfile(os.path.join(walk, "TEAM.md")):
            return walk
        if walk == "/":
            break
    die(f"找不到团队目录（未找到 TEAM.md）: {team}。用 --team-dir 指定绝对路径。")


def team_label(args) -> str:
    """团队标识：优先 --team，缺失时回退到目录名（避免记录里出现 None）。"""
    if getattr(args, "team", None):
        return getattr(args, "team")
    if getattr(args, "team_dir", None):
        return os.path.basename(os.path.abspath(args.team_dir))
    return "unknown"


def ensure_logs(team_dir: str):
    for sub in ("logs", CHECKPOINT_DIR, "results", "contracts"):
        os.makedirs(os.path.join(team_dir, sub), exist_ok=True)


def append_event(team_dir: str, ev: dict):
    """所有事件流的统一落盘入口。"""
    with open(os.path.join(team_dir, EVENTS_FILE), "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> list[dict]:
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"⚠️  跳过第 {i} 行损坏的事件记录", file=sys.stderr)
    return out


def write_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ---------------------------------------------------------------- cmd: init

def cmd_init(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    ensure_logs(team_dir)
    sessions_path = os.path.join(team_dir, SESSIONS_FILE)
    if not os.path.isfile(sessions_path):
        write_json(sessions_path, {
            "_comment": "agent-team 会话登记。resume_cmd 为原生恢复命令；缺失时走 L3 冷重建。",
            "team": team_label(args),
            "updated": now_iso(),
            "roles": {},
        })
        print(f"✅ 初始化会话登记: {sessions_path}")
    else:
        print(f"⏭  会话登记已存在: {sessions_path}")
    for path, label in ((EVENTS_FILE, "事件流"), (INBOX_FILE, "上报队列"), (ATTEMPTS_FILE, "重试计数")):
        full = os.path.join(team_dir, path)
        if not os.path.isfile(full):
            open(full, "a", encoding="utf-8").close()
            print(f"✅ 初始化{label}: {full}")
        else:
            print(f"⏭  {label}已存在: {full}")
    if not os.path.isfile(os.path.join(team_dir, BUDGET_FILE)):
        write_json(os.path.join(team_dir, BUDGET_FILE), {
            "_comment": ("预算额度。per_task_min 为单个任务的软超时分钟数（超过→agent 应 checkpoint 收摊）；"
                         "hard_cap_min 为单任务硬上限（超过→必须熔断上报）；"
                         "total_min 为团队总预算（超过→团队整体熔断）。"),
            "team": team_label(args),
            "per_task_min": 60,
            "hard_cap_min": 120,
            "total_min": 600,
            "roles": {},
        })
        print(f"✅ 初始化预算配置: {BUDGET_FILE}")
    print(f"   团队目录: {team_dir}")


# --------------------------------------------------------------- cmd: record

VALID_EVENTS = {
    "team_spawn", "task_assign", "task_start", "task_done", "needs_revision",
    "checkpoint", "block", "decision", "session_spawn", "session_retire",
    "session_resume", "review_verdict", "escalate", "escalation_answered",
    "budget_warn", "budget_stop", "role_handover", "task_progress",
    "im_verified", "im_ask", "im_answer",
}


def cmd_record(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    ensure_logs(team_dir)
    if args.event not in VALID_EVENTS:
        die(f"未知 event: {args.event}\n可选: {', '.join(sorted(VALID_EVENTS))}")

    summary = (args.summary or "").strip()
    if not summary:
        die("--summary 必填，且必须具体。禁止写「完成了任务」「搞定了」这类无信息量描述。")
    # 拦住常见的空洞描述
    hollow = {"done", "ok", "完成", "完成任务", "搞定", "进展顺利", "finished"}
    if summary.strip().lower() in hollow or len(summary) < 6:
        print(f"⚠️  summary 过短或空洞:「{summary}」——事件记录的价值全在这里", file=sys.stderr)

    ev = {
        "ts": now_iso(),
        "team": team_label(args),
        "role": args.role,
        "event": args.event,
        "task": args.task,
        "summary": summary,
    }
    if args.artifacts:
        ev["artifacts"] = [a.strip() for a in args.artifacts.split(",") if a.strip()]
    if args.elapsed_min is not None:
        ev["elapsed_min"] = args.elapsed_min

    path = os.path.join(team_dir, EVENTS_FILE)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(f"✅ 已记录 [{args.event}] {args.role}" + (f" / {args.task}" if args.task else ""))
    print(f"   → {path}")


# ------------------------------------------------------- cmd: escalate / ask
#
# 通道设计：只允许自下而上（worker → lead）。横向 peer 通信不支持——
# peer 间要信息必须经 lead 中转，否则会出现多源真相与互相覆盖。

LEAD_ROLES = {"lead", "main", "leader"}


def cmd_escalate(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    ensure_logs(team_dir)
    if args.role in LEAD_ROLES:
        die("lead 不需要上报（lead 是通道终点）。lead 的决策直接记 decision 事件。")
    if args.to.lower() not in LEAD_ROLES:
        die(f"不支持上报给「{args.to}」。通道只允许 worker → lead，横向 peer 通信不支持。")

    ev = {
        "ts": now_iso(),
        "team": team_label(args),
        "role": args.role,
        "event": "escalate",
        "task": args.task,
        "severity": args.severity,
        "summary": args.question,
        "tried": args.tried or "",
        "id": new_id("E"),
    }
    append_event(team_dir, ev)
    # inbox 单独一份，便于 lead 快速扫未答项
    with open(os.path.join(team_dir, INBOX_FILE), "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    icon = {"blocker": "🔴", "question": "🟡", "info": "⚪"}[args.severity]
    print(f"{icon} 已上报 lead: {ev['id']}  [{args.severity}] {args.task or '-'}")
    print(f"   问题: {args.question}")
    print(f"\n当前应当：")
    if args.severity == "blocker":
        print("   1. 立即停止当前任务，不要继续猜")
        print("   2. 写 checkpoint（teamctl.py checkpoint write）")
        print("   3. 退出 agent（保留 tmux 窗口），等 lead 答复")
    else:
        print("   1. 继续手头不依赖该答复的部分")
        print("   2. 不要横向找 peer 询问（不支持），也不要自行拍板")
    print(f"\nlead 查看: teamctl.py --team-dir<dir> ask --pending")
    print(f"lead 答复: teamctl.py --team-dir <dir> ask answer --id {ev['id']} --answer \"...\"")


def cmd_ask(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    ensure_logs(team_dir)
    inbox = read_jsonl(os.path.join(team_dir, INBOX_FILE))
    if not inbox:
        print("（上报队列为空）")
        return
    answered = set()
    for e in read_jsonl(os.path.join(team_dir, EVENTS_FILE)):
        if e.get("event") == "escalation_answered" and e.get("id"):
            answered.add(e["id"])

    if args.ask_cmd == "list":
        pending = [e for e in inbox if e.get("id") not in answered]
        if not pending:
            print(f"（无待答上报，共 {len(inbox)} 条历史）")
            return
        print(f"待答上报{len(pending)} 条（按严重度排序）\n")
        order = {"blocker": 0, "question": 1, "info": 2}
        for e in sorted(pending, key=lambda x: (order.get(x.get("severity", "info"), 3), x["ts"])):
            icon = {"blocker": "🔴", "question": "🟡", "info": "⚪"}[e.get("severity", "info")]
            print(f"{icon} {e['id']}  {e['ts'][11:19]}  {e.get('role')}  task={e.get('task') or '-'}")
            print(f"    问题: {e.get('summary')}")
            if e.get("tried"):
                print(f"    已试: {e['tried']}")
            print()
        print(f"答复: teamctl.py ask answer --id <id> --answer \"...\"")
    elif args.ask_cmd == "answer":
        target = next((e for e in inbox if e.get("id") == args.id), None)
        if not target:
            die(f"无此上报 id: {args.id}")
        rec = {
            "ts": now_iso(), "team": team_label(args), "role": args.role or "lead",
            "event": "escalation_answered", "task": target.get("task"),
            "id": args.id,
            "summary": f"答复 {args.id}: {args.answer}",
        }
        append_event(team_dir, rec)
        print(f"✅ 已答复 {args.id}（问询方: {target.get('role')}）")
        print(f"   {args.answer}")
        print("\n请把答复落进被问询角色的契约补充或notes.md——答复本身也必须可追溯。")


# --------------------------------------------------------------- cmd: budget

def load_budget(team_dir: str) -> dict:
    path = os.path.join(team_dir, BUDGET_FILE)
    if not os.path.isfile(path):
        die("预算未初始化，先跑: teamctl.py init")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_budget(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    ensure_logs(team_dir)
    events = read_jsonl(os.path.join(team_dir, EVENTS_FILE))

    if args.budget_cmd == "set":
        cfg = load_budget(team_dir)
        if args.per_task_min is not None:
            cfg["per_task_min"] = args.per_task_min
        if args.hard_cap_min is not None:
            cfg["hard_cap_min"] = args.hard_cap_min
        if args.total_min is not None:
            cfg["total_min"] = args.total_min
        if args.role:
            cfg.setdefault("roles", {})[args.role] = {
                "per_task_min": args.role_min if args.role_min is not None
                else cfg.get("per_task_min"),
            }
        cfg["updated"] = now_iso()
        write_json(os.path.join(team_dir, BUDGET_FILE), cfg)
        print(f"✅ 预算已更新 (写入 {BUDGET_FILE})")
        print(f"   单任务软超时: {cfg.get('per_task_min')} 分钟"
              + (f" | {args.role} 专属: {cfg['roles'][args.role]['per_task_min']} 分钟" if args.role else ""))
        print(f"   单任务硬上限: {cfg.get('hard_cap_min')} 分钟")
        print(f"   团队总预算  : {cfg.get('total_min')} 分钟")
        return

    # 以下为 spend / check 共用
    cfg = load_budget(team_dir)

    # 每个任务已消耗的分钟数（取该任务最后一条带 elapsed_min 的事件）
    task_minutes: dict[str, float] = {}
    for e in events:
        if e.get("task") and e.get("elapsed_min") is not None:
            task_minutes[e["task"]] = e["elapsed_min"]

    if args.budget_cmd == "spend":
        if not args.task:
            die("spend 需要 --task")
        # 取该任务最近一次 elapsed 作为累计耗时
        cur = task_minutes.get(args.task, 0.0)
        add = float(args.minutes)
        total = cur + add
        role_soft = (cfg.get("roles", {}).get(args.role, {}) or {}).get("per_task_min") or cfg.get("per_task_min")
        # 任务级累计耗时登事件（rollup）
        ev = {
            "ts": now_iso(), "team": team_label(args), "role": args.role,
            "event": "task_progress", "task": args.task,
            "summary": f"任务累计耗时 {total:.0f} 分钟（本次 +{add:.0f}）",
            "elapsed_min": total,
        }
        append_event(team_dir, ev)
        task_minutes[args.task] = total
        warn = ""
        if cfg.get("hard_cap_min") and total >= cfg["hard_cap_min"]:
            warn = f"\n🔴 已超硬上限 {cfg['hard_cap_min']} 分钟——必须立即 checkpoint 并上报熔断"
        elif role_soft and total >= role_soft:
            warn = f"\n🟡 已超软超时 {role_soft} 分钟——建议写 checkpoint 后收摊，别硬撑"
        print(f"⏱  task {args.task} 累计 {total:.0f} 分钟（软超时 {role_soft} / 硬上限 {cfg.get('hard_cap_min')}）{warn}")

    elif args.budget_cmd == "check":
        # 团队总预算：所有任务累计耗时之和
        total_spent = sum(task_minutes.values())
        team_cap = cfg.get("total_min")
        print("【预算检查】")
        if task_minutes:
            print("  任务耗时:")
            soft = cfg.get("per_task_min")
            for t, m in sorted(task_minutes.items(), key=lambda kv: -kv[1]):
                flag = ""
                if cfg.get("hard_cap_min") and m >= cfg["hard_cap_min"]:
                    flag = "  🔴 硬上限"
                elif soft and m >= soft:
                    flag = "  🟡 超软超时"
                print(f"    {t:<6} {m:>6.0f} 分钟{flag}")
        else:
            print("  （暂无耗时数据，用 budget spend 记账）")
        print(f"  团队合计: {total_spent:.0f} 分钟")
        if team_cap:
            pct = total_spent / team_cap * 100
            print(f"  团队预算: {total_spent:.0f}/{team_cap} 分钟（{pct:.0f}%）")
            if total_spent >= team_cap:
                print("  🔴 团队总预算耗尽——停止派新任务，向用户汇报后再继续")
            elif pct >= 80:
                print("  🟡 团队预算已用 80%——收紧派活，优先收尾高价值任务")

        # 空转检测：最近一条事件距今太久= 可能卡死
        if events:
            last = events[-1]["ts"]
            try:
                last_dt = datetime.fromisoformat(last)
                idle_min = (datetime.now(CST) - last_dt).total_seconds() / 60
            except ValueError:
                idle_min = 0
            print(f"  最后事件: {last[11:19]}（距今 {idle_min:.0f} 分钟）")
            if idle_min > 180:
                print("  🔴 超过 180 分钟无事件——疑似空转/卡死，用 capture-pane 核查对应窗口")


# -------------------------------------------------------------- cmd: attempts

def cmd_attempts(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    ensure_logs(team_dir)

    if args.attempts_cmd == "bump":
        if not args.task:
            die("bump 需要 --task")
        rec = {
            "ts": now_iso(), "team": team_label(args),
            "role": args.role, "task": args.task,
            "reason": args.reason or "",
        }
        with open(os.path.join(team_dir, ATTEMPTS_FILE), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"✅ 已登记一次退回: task={args.task} role={args.role}")
    elif args.attempts_cmd == "list":
        recs = read_jsonl(os.path.join(team_dir, ATTEMPTS_FILE))
        if not recs:
            print("（无退回记录）")
            return
        by_task: dict[str, list] = {}
        for r in recs:
            by_task.setdefault(r["task"], []).append(r)
        for t, rs in sorted(by_task.items(), key=lambda kv: -len(kv[1])):
            print(f"\n{t}·被退回 {len(rs)} 次")
            for r in rs:
                print(f"  {r['ts'][:16]}  {r.get('role', '?')}  {r.get('reason', '')[:50]}")
    elif args.attempts_cmd == "judge":
        recs = read_jsonl(os.path.join(team_dir, ATTEMPTS_FILE))
        n = sum(1 for r in recs if r["task"] == args.task)
        # 默认策略：3 次内允许同角色重试；第 4-6 次要求换角度/缩范围；>=7 建议换角色或拆任务。
        # 不采用「2 次即死」——太严会把可救的任务误杀。
        if n <= 3:
            verdict = f"✅ 同角色可继续（第 {n} 次退回，仍在 3 次容限内）"
            advise = "让同一角色按 needs-revision 的具体缺陷重做。若返工原因指向理解偏差，考虑在契约里补明确边界。"
        elif n <= 6:
            verdict = f"🟡 需换角度（第 {n} 次退回）：不要再让同角色原样重做"
            advise = ("优先：① 让lead 改写契约，把缺陷变成显式的 Do-Not-Touch/完成标准；"
                      "② 缩小任务范围再派；③ 补 checkpoint 让 agent 知道上次卡在哪。")
        else:
            verdict = f"🔴 强烈建议换角色或拆任务（已退回 {n} 次）"
            advise = ("同一角色反复失败通常不是执行问题而是任务定义/匹配问题。"
                      "应：① 换另一个角色（不同 CLI/模型更好）；② 把任务拆到更小；"
                      "③ 评估这个任务是否该做。必要时向用户汇报并取消。")
        print(f"Task {args.task}:退回 {n} 次")
        print(f"{verdict}")
        print(f"\n建议: {advise}")


# -------------------------------------------------------------- cmd: session

def load_sessions(team_dir: str) -> dict:
    path = os.path.join(team_dir, SESSIONS_FILE)
    if not os.path.isfile(path):
        die("会话登记尚未初始化，先跑: teamctl.py init")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sessions(team_dir: str, data: dict):
    data["updated"] = now_iso()
    write_json(os.path.join(team_dir, SESSIONS_FILE), data)


def cmd_session(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    ensure_logs(team_dir)

    if args.session_cmd == "set":
        data = load_sessions(team_dir)
        data.setdefault("roles", {})
        data["roles"][args.role] = {
            "session_id": args.session_id,
            "resume_cmd": args.resume_cmd or "",
            "cli": args.cli or "",
            "mode": args.mode or "",
            "registered": now_iso(),
        }
        save_sessions(team_dir, data)
        print(f"✅ 已登记会话: role={args.role} id={args.session_id}")
        if not args.resume_cmd:
            print("   ⚠️  未提供 --resume-cmd：会话丢失时只能走 L3 冷重建（读 checkpoint + 决策 + 产出）")

    elif args.session_cmd == "list":
        data = load_sessions(team_dir)
        roles = data.get("roles", {})
        if not roles:
            print("（暂无会话登记）")
            return
        # 角色名/会话 id 长度不定，中文按2 列宽计算会导致表格错位，
        # 因此用纵向键值输出而不是列对齐。
        for role, info in sorted(roles.items()):
            print(f"● {role}")
            print(f"    模式      : {info.get('mode') or '-'}")
            print(f"    agent CLI : {info.get('cli') or '-'}")
            print(f"    会话 id   : {info.get('session_id') or '-'}")
            print(f"    恢复命令  : {info.get('resume_cmd') or '（未登记，只能走 L3 冷重建）'}")
            print(f"    登记时间  : {info.get('registered') or '-'}")

    elif args.session_cmd == "resume":
        data = load_sessions(team_dir)
        info = data.get("roles", {}).get(args.role)
        if not info:
            die(f"角色 {args.role} 无会话登记。走 L3 冷重建：teamctl.py checkpoint show --role {args.role} --task <task>")
        level = "L1/L2"
        cmd = info.get("resume_cmd") or ""
        if not cmd:
            level = "L3"
        print(f"角色 {args.role} 会话: id={info.get('session_id', '-')} cli={info.get('cli', '-')}")
        if level == "L3":
            print("未登记恢复命令 → 只能走 L3 冷重建：")
            print(f"  scripts/teamctl.py checkpoint show --team {team_label(args)} --role {args.role} --task <task>")
            print("  然后按 context-protocol.md「上下文恢复时的重建顺序」重新投放契约。")
        else:
            print(f"恢复方式: {level}（原生resume）")
            print(f"在目标窗口执行:\n  {cmd}")
            sess = args.session_name or f"at-{team_dir.rstrip('/').split('/')[-1]}"
            print(f"  tmux send-keys -t {sess}:{args.role} \"{cmd}\" Enter")
            print("\n恢复后补登事件:")
            print(f"  scripts/teamctl.py record --team {team_label(args)} --role {args.role} --event session_resume --summary \"...\"")
        rec = {"ts": now_iso(), "team": team_label(args), "role": args.role,
               "event": "session_resume", "task": None, "summary": f"以 {level} 恢复会话"}
        with open(os.path.join(team_dir, EVENTS_FILE), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    elif args.session_cmd == "clear":
        data = load_sessions(team_dir)
        if args.role in data.get("roles", {}):
            del data["roles"][args.role]
            save_sessions(team_dir, data)
            print(f"✅ 已清除会话登记: {args.role}")
        else:
            print(f"角色 {args.role} 本来就没有会话登记")


# ----------------------------------------------------------- cmd: checkpoint

CKPT_SECTIONS = ("做到哪一步", "已确定的决策（不要推翻）", "下一步（恢复时从这里继续）", "待解决的疑问", "不要重做的部分")


def cmd_checkpoint(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    ensure_logs(team_dir)

    if args.ckpt_cmd == "write":
        if not args.file or not os.path.isfile(args.file):
            die("--file 指向的检查点文件不存在，请先按模板写好")
        role = safe_name(args.role)
        task = safe_name(args.task)
        dest_dir = os.path.join(team_dir, CHECKPOINT_DIR)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, f"{role}-{task}.md")
        with open(args.file, "r", encoding="utf-8") as f:
            body = f.read()
        missing = [s for s in CKPT_SECTIONS if s not in body]
        if missing:
            print(f"⚠️  checkpoint 缺少关键段落（冷重建会失效）: {', '.join(missing)}", file=sys.stderr)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(body)
        ev = {"ts": now_iso(), "team": team_label(args), "role": args.role, "event": "checkpoint",
              "task": args.task, "summary": f"写入 checkpoint: {os.path.relpath(dest, team_dir)}"}
        with open(os.path.join(team_dir, EVENTS_FILE), "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        print(f"✅ checkpoint 已落盘: {os.path.relpath(dest, team_dir)}")

    elif args.ckpt_cmd == "show":
        role = safe_name(args.role)
        if args.task:
            dest = os.path.join(team_dir, CHECKPOINT_DIR, f"{role}-{safe_name(args.task)}.md")
            if not os.path.isfile(dest):
                die(f"无checkpoint: {os.path.relpath(dest, team_dir)}")
            print(f"--- {os.path.relpath(dest, team_dir)} ---")
            with open(dest, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            d = os.path.join(team_dir, CHECKPOINT_DIR)
            files = sorted(x for x in os.listdir(d) if x.startswith(role + "-"))
            if not files:
                die(f"角色 {args.role} 无 checkpoint")
            for x in files:
                print(f"\n--- checkpoints/{x} ---")
                with open(os.path.join(d, x), "r", encoding="utf-8") as f:
                    print(f.read())

    elif args.ckpt_cmd == "coldstart":
        # 打印 L3 冷重建的投放指令
        role = args.role
        print(f"# L3 冷重建指令 · role={role}\n")
        print("你的上一个会话不可用，请从落盘信息恢复上下文：")
        print(f"1. 读 TEAM.md（位于 {team_dir}/TEAM.md）了解团队目标")
        print(f"2. 读 {team_dir}/decisions.md —— 不要推翻已有决策")
        ck_dir = os.path.join(team_dir, CHECKPOINT_DIR)
        if os.path.isdir(ck_dir):
            cks = sorted(x for x in os.listdir(ck_dir) if x.startswith(role + "-"))
            if cks:
                print(f"3. 读 {CHECKPOINT_DIR}/<最新一个> 了解你做到哪一步")
            else:
                print(f"3. ⚠️ 无 checkpoint（冷重建质量会明显下降，从第4 步开始）")
        print("4. 读 contracts/<role>.md 了解边界与完成标准")
        print(f"5. 检查 {team_dir}/results/ 确认哪些已产出，**不要重做已完成部分**")
        print("6. 读 tasks.md 自己那一行，确认任务状态")
        print("\n从 checkpoint 的「下一步」继续。若信息不足，停下上报 lead，不要自行猜测。")


# ---------------------------------------------------------------- cmd: status

COLUMN_ALIASES = {
    "id": {"id"},
    "task": {"任务", "task"},
    "role": {"负责人(角色)", "负责人", "负责人(窗口)", "role", "owner"},
    "goal": {"关联目标", "goal"},
    "mode": {"模式", "mode"},
    "status": {"状态", "status"},
    "done": {"完成标准", "done", "criteria"},
    "note": {"备注", "note"},
}


def parse_tasks(path: str) -> list[dict]:
    """按表头名解析 tasks.md，兼容不同列数的看板模板。

    不能按固定列下标解析：init-exp 的tasks.md 表头是
    `| ID | 任务 | 负责人(窗口) | 关联目标 | 状态 | 完成标准 | 备注 |`
    （7 列，无「模式」），agent-team 是 8 列。按名字找才能两者都work，
    也能容忍用户调整列顺序。
    """
    if not os.path.isfile(path):
        return []
    header: dict[str, int] = {}
    tasks: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s.startswith("|") or s.count("|") < 3:
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            raw_first = cells[0] if cells else ""
            first = raw_first.lower()
            # 表头行：把列名映射到下标
            if first in COLUMN_ALIASES["id"]:
                for i, c in enumerate(cells):
                    for key, names in COLUMN_ALIASES.items():
                        if c.lower() in names:
                            header[key] = i
                            break
                continue
            # 分隔行 |---|---|---
            if set("".join(cells)) <= set("-: "):
                continue
            # 任务行：ID 形如 T1 / T2（用原始大小写判断，不要用lower 后的）
            if not re.match(r"^T\d+$", raw_first):
                continue
            t = {"id": raw_first}
            for key, idx in header.items():
                t[key] = cells[idx] if idx < len(cells) else ""
            tasks.append(t)
    return tasks


def role_state(events: list[dict], role: str) -> str:
    """从事件流推断角色会话状态。

    注意：只有 session_spawn / session_retire / session_resume 这三个事件
    直接代表会话生命周期。team_spawn 与 task_start 也应视为该角色已上线，
    否则刚拉起团队就报 gone 会误导使用者。
    """
    st = "gone"
    for e in events:
        if e.get("role") != role:
            continue
        ev = e.get("event")
        if ev == "session_spawn":
            st = "working"
        elif ev == "session_retire":
            st = "parked"
        elif ev in ("task_done",):
            st = "idle"
        elif ev in ("task_start", "task_assign", "session_resume", "team_spawn"):
            st = "working"
        elif ev == "block":
            st = "blocked"
    return st


ICON = {"working": "🟢", "idle": "🟡", "parked": "⚪", "blocked": "🔴", "gone": "⚫"}


def cmd_status(args):
    team_dir = find_team_dir(team_label(args), args.team_dir)
    events = read_jsonl(os.path.join(team_dir, EVENTS_FILE))
    sessions = load_sessions(team_dir) if os.path.isfile(os.path.join(team_dir, SESSIONS_FILE)) else {"roles": {}}
    tasks = parse_tasks(os.path.join(team_dir, "tasks.md"))
    sess_name = args.session_name or f"at-{os.path.basename(team_dir.rstrip('/'))}"

    print(f"\n{'=' * 70}")
    print(f"  Agent 团队快照 · {team_label(args)}")
    print(f"  目录: {team_dir}")
    print(f"  时间: {now_iso()}")
    print(f"{'=' * 70}\n")

    # 任务统计
    if tasks:
        stat = {}
        for t in tasks:
            key = t.get("status") or "unknown"
            stat[key] = stat.get(key, 0) + 1
        print("【任务】" + "  ".join(f"{k}={v}" for k, v in sorted(stat.items())))
        for t in tasks:
            st = t.get("status", "")
            flag = ""
            if st == "needs-revision":
                flag = "  ← 需处理"
            elif st == "in_progress":
                flag = "  ← 进行中"
            print(f"  {t['id']:<5} {st:<15} {t.get('role', ''):<12} {t.get('task', '')[:34]}{flag}")
    else:
        print("【任务】tasks.md 中无任务行（或文件缺失）")

    # 角色状态
    print("\n【角色】")
    roles = set(sessions.get("roles", {}).keys())
    for t in tasks:
        r = t.get("role")
        if r and r not in ("-", "<role>"):
            roles.add(r)
    if not roles:
        print("（无角色登记）")
    for r in sorted(roles):
        info = sessions.get("roles", {}).get(r, {})
        st = role_state(events, r)
        print(f"  {ICON.get(st, '⚫')} {r:<14} {st:<9} mode={info.get('mode') or '-':<10} id={info.get('session_id') or '-'}")

    # tmux 窗口实际状态
    try:
        out = subprocess.run(["tmux", "list-windows", "-t", sess_name, "-F", "#{window_name}"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            wins = [w for w in out.stdout.strip().splitlines() if w]
            print(f"\n【tmux】session {sess_name} 窗口: {', '.join(wins)}")
        else:
            print(f"\n【tmux】session {sess_name} 不存在（团队可能已收摊）")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("\n【tmux】tmux 不可用或超时，跳过窗口检查")

    # 待处理 block
    blocks = [e for e in events if e.get("event") == "block"]
    if blocks:
        print(f"\n【待处理 block】{len(blocks)} 条")
        for e in blocks[-5:]:
            print(f"  {e['ts']}  {e.get('role', '?')} / {e.get('task', '-')}: {e.get('summary', '')[:60]}")

    # 待答上报
    inbox = read_jsonl(os.path.join(team_dir, INBOX_FILE)) if os.path.isfile(os.path.join(team_dir, INBOX_FILE)) else []
    answered = {e.get("id") for e in events if e.get("event") == "escalation_answered"}
    pending_esc = [e for e in inbox if e.get("id") not in answered]
    if pending_esc:
        print(f"\n【待答上报】{len(pending_esc)} 条（worker → lead）")
        for e in pending_esc[-5:]:
            icon = {"blocker": "🔴", "question": "🟡", "info": "⚪"}.get(e.get("severity", "info"), "⚪")
            print(f"  {icon} {e['id']}  {e.get('role')} / {e.get('task') or '-'}: {str(e.get('summary'))[:56]}")
        print(f"  处理: teamctl.py --team-dir <dir> ask --pending")
        if any(e.get("severity") == "blocker" for e in pending_esc):
            print("  ⚠️  含 blocker 级上报——对应 agent 很可能已停工等答复")

    # 预算
    if os.path.isfile(os.path.join(team_dir, BUDGET_FILE)):
        try:
            cfg = load_budget(team_dir)
            task_min: dict[str, float] = {}
            for e in events:
                if e.get("task") and e.get("elapsed_min") is not None:
                    task_min[e["task"]] = e["elapsed_min"]
            total_spent = sum(task_min.values())
            cap = cfg.get("total_min")
            print("\n【预算】")
            if task_min:
                over = [(t, m) for t, m in task_min.items()
                        if cfg.get("hard_cap_min") and m >= cfg["hard_cap_min"]]
                soft = cfg.get("per_task_min")
                for t, m in sorted(task_min.items(), key=lambda kv: -kv[1])[:5]:
                    flag = ""
                    if cfg.get("hard_cap_min") and m >= cfg["hard_cap_min"]:
                        flag = "  🔴超硬上限"
                    elif soft and m >= soft:
                        flag = "  🟡 超软超时"
                    print(f"  {t:<6} {m:>6.0f} 分钟{flag}")
            if cap:
                pct = total_spent / cap * 100
                print(f"  团队合计 {total_spent:.0f}/{cap} 分钟（{pct:.0f}%）")
                if total_spent >= cap:
                    print("  🔴 团队预算耗尽——停止派新任务，先向用户汇报")
                elif pct >= 80:
                    print("  🟡 预算已用 80%——收紧派活，优先收尾高价值任务")
            # 空转检测
            if events:
                try:
                    idle = (datetime.now(CST) - datetime.fromisoformat(events[-1]["ts"])).total_seconds() / 60
                    if idle > 180:
                        print(f"  🔴 最后事件距今 {idle:.0f} 分钟——疑似空转/卡死，用 capture-pane 核查")
                except ValueError:
                    pass
        except (SystemExit, json.JSONDecodeError):
            print("  ⚠️  预算配置损坏，请重新 teamctl.py budget set")

    # 人机通道
    cfg_im, im_source = load_im(team_dir)
    asks = [e for e in events if e.get("event") == "im_ask"]
    answered_ids = {e.get("id") for e in events if e.get("event") == "im_answer"}
    pending_im = [e for e in asks if e.get("id") not in answered_ids]
    print("\n【人机通道】")
    if cfg_im:
        ch = cfg_im.get("channel")
        verified = cfg_im.get("verified_at")
        print(f"  通道: {ch} / {cfg_im.get('tier')}({im_source})")
        print(f"  验证: {verified or '❌ 未验证'}")
    else:
        print("  通道: ❌ 未配置——lead 需在对话里直接问用户，不得自行发挥")
    if asks:
        print(f"  提问 {len(asks)} 次，未答 {len(pending_im)} 条")
    for e in pending_im:
        icon = {"blocker": "🔴", "question": "🟡", "info": "⚪"}.get(e.get("severity"), "⚪")
        ago = ""
        try:
            mins = (datetime.now(CST) - datetime.fromisoformat(e["ts"])).total_seconds() / 60
            ago = f"  已等 {mins:.0f} 分钟"
            if e.get("default") and e.get("auto_after_min") and mins >= e["auto_after_min"]:
                ago += f"  ⚠️ 已超 {e['auto_after_min']} 分钟，默认动作已生效或应生效: {e['default']}"
        except ValueError:
            pass
        print(f"  {icon} {e.get('id')}  task={e.get('task') or '-'}{ago}")
        print(f"      {str(e.get('summary'))[:56]}")
    if pending_im and any(e.get("severity") == "blocker" for e in pending_im):
        print("  ⚠️  含未答 blocker——相关任务应停着等用户，不要自行推进")

    # 反复退回的任务
    att_path = os.path.join(team_dir, ATTEMPTS_FILE)
    if os.path.isfile(att_path):
        recs = read_jsonl(att_path)
        cnt: dict[str, int] = {}
        for r in recs:
            cnt[r.get("task", "?")] = cnt.get(r.get("task", "?"), 0) + 1
        hot = {t: c for t, c in cnt.items() if c >= 4}
        if hot:
            print("\n【反复退回】(>=4 次，建议换角度或换角色)")
            for t, c in sorted(hot.items(), key=lambda kv: -kv[1]):
                print(f"  {t}: {c} 次    → attempts judge --task {t}")

    # 最近事件
    n = args.last
    if events:
        print(f"\n【最近 {n} 条事件】")
        for e in events[-n:]:
            art = f"  artifacts={e['artifacts']}" if e.get("artifacts") else ""
            print(f"  {e['ts'][11:19]}  {e.get('role', '?'):<12} {e.get('event', ''):<15} {str(e.get('task') or '-'):<5} {str(e.get('summary', ''))[:44]}{art}")
    else:
        print("\n【事件】事件流为空")

    # 产出物
    res_dir = os.path.join(team_dir, "results")
    files = [f for f in os.listdir(res_dir) if not f.startswith(".")] if os.path.isdir(res_dir) else []
    print(f"\n【产出物】results/ 共 {len(files)} 个")
    for f in sorted(files)[:10]:
        size = os.path.getsize(os.path.join(res_dir, f))
        print(f"  {f:<40} {size:>8} B")

    # checkpoint 覆盖
    ck_dir = os.path.join(team_dir, CHECKPOINT_DIR)
    if os.path.isdir(ck_dir):
        cks = [x for x in os.listdir(ck_dir) if x.endswith(".md")]
        print(f"\n【checkpoint】共 {len(cks)} 份")
    print()


# --------------------------------------------------------------- cmd: im
#
# 人机通道（Team Leader ↔ 用户）。
# 核心目的不是通知进度，而是把关键决策权交回用户，约束 lead 不自行发挥。
# 设计要点：
#   * 配置幂等——已验证过的通道不重复问用户（全局配置优先复用）
#   * webhook URL 只存环境变量名，不明文落盘
#   * 提问必须带选项、默认动作与超时策略，避免"开放式提问 + 静默自决"

def load_im(team_dir: str | None) -> tuple[dict | None, str]:
    """返回 (配置, 来源)。项目级优先，其次全局；都没有返回 (None, '')。"""
    if team_dir:
        p = os.path.join(team_dir, IM_FILE)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["_source"] = p
            return cfg, "project"
    if os.path.isfile(GLOBAL_IM):
        with open(GLOBAL_IM, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["_source"] = GLOBAL_IM
        return cfg, "global"
    return None, ""


def save_im(team_dir: str | None, cfg: dict, scope: str):
    if scope == "global":
        os.makedirs(os.path.dirname(GLOBAL_IM), exist_ok=True)
        path = GLOBAL_IM
    else:
        if not team_dir:
            die("项目级配置需要 --team-dir")
        ensure_logs(team_dir)
        path = os.path.join(team_dir, IM_FILE)
    cfg.pop("_source", None)
    cfg["updated"] = now_iso()
    write_json(path, cfg)
    return path


def send_notify(cfg: dict, title: str, body: str, dry_run: bool = False) -> bool:
    """执行通知命令。命令模板从 stdin 读消息体（便于用 @- 或curl --data-binary @-）。"""
    cmd_tpl = (cfg.get("notify_cmd") or "").strip()
    if not cmd_tpl:
        return False
    payload = f"{title}\n\n{body}" if title else body
    if dry_run:
        print("── dry run：不会真的发送 ──")
        print(f"命令: {cmd_tpl}")
        print("stdin:")
        print(payload)
        return True
    #环境变量名注入：把 webhook-env 指向的环境变量带进子进程
    env = os.environ.copy()
    wenv = cfg.get("webhook_env")
    if wenv:
        if wenv in os.environ:
            env[wenv] = os.environ[wenv]
        else:
            print(f"⚠️  环境变量 {wenv} 未设置——发送可能失败。"
                  f"请在 shell 中 export {wenv}=<webhook URL>，或改用其他注入方式。",
                  file=sys.stderr)
    try:
        r = subprocess.run(cmd_tpl, shell=True, input=payload, text=True,
                           capture_output=True, timeout=20, env=env)
    except subprocess.TimeoutExpired:
        print("❌ 通知命令超时（20s）", file=sys.stderr)
        return False
    if r.returncode != 0:
        print(f"❌ 通知命令失败 rc={r.returncode}: {(r.stderr or '').strip()[:200]}", file=sys.stderr)
        return False
    return True


def cmd_im(args):
    # 全局配置操作（global scope 的 init / check）不需要团队上下文
    if (args.team or args.team_dir) or args.scope == "project":
        team_dir = find_team_dir(team_label(args), args.team_dir)
    else:
        team_dir = None
    cfg, source = load_im(team_dir)

    if args.im_cmd == "check":
        print("【人机通道配置检查】\n")
        if not cfg:
            print("状态: ❌ 未配置")
            print("\n需要配置。请向用户确认（不要自行编造 webhook URL）：")
            print("  1. 是否配置 IM 通道        默认：是")
            print("  2. 通道类型                飞书 / 企业微信 / 钉钉 / 其他 / 暂不配置（问用户实际用哪个）")
            print("  3. 能力档位                L0 只发 / L1 加 tmux 入向（推荐） / L2 全双向")
            print("  4. webhook URL            由用户提供")
            print("\n配置命令:")
            print("  scripts/teamctl.py im init --channel <c> --tier <L0|L1|L2> \\")
            print("      --notify-cmd 'curl ... -d @- \"$ENV_NAME\"' --webhook-env ENV_NAME")
            return
        print(f"状态: ✅ 已配置（来源: {source}）")
        print(f"  通道      : {cfg.get('channel')}  ({IM_CHANNELS.get(cfg.get('channel'), '-')})")
        print(f"  档位      : {cfg.get('tier')}  {IM_TIERS.get(cfg.get('tier'), '')}")
        if cfg.get("tier") == "L2":
            _mode = cfg.get("app_verify_mode") or ""
            print(f"  飞书应用  : app_id=${cfg.get('app_id_env') or '未设置'}  "
                  f"app_secret=${cfg.get('app_secret_env') or '未设置'}")
            if _mode:
                print(f"  接入方式  : {_mode}  {L2_VERIFY_MODES.get(_mode, '')}")
            if not L2_INBOUND_IMPLEMENTED:
                print("  入向状态  : ⚠️ **尚未实现**——用户在飞书里的回复 lead 目前收不到")
                print("              请用 `tmux attach` 到 lead 窗口回答。L1 出向推送不受影响。")
        print(f"  webhook   : ${cfg.get('webhook_env')}  (只存变量名，明文不入库)")
        print(f"  tmux 会话 : {cfg.get('tmux_session') or '(未记录)'}")
        print(f"  验证时间  : {cfg.get('verified_at') or '❌ 未验证'}")
        if not cfg.get("verified_at"):
            print("\n⚠️  配置存在但未验证过。发送可能不可用，建议跑: teamctl.py im test")
            print("   验证失败则不算配置成功——请重新确认 webhook URL。")
        else:
            print("\n✅ 无需重复配置，直接复用。")

    elif args.im_cmd == "init":
        # 幂等保护分两级：
        #   已验证过的配置 → 无论如何都不覆盖（必须问用户 --force）
        #   存在但未验证 → 视为「配了没验成功」，允许补齐缺的字段（不重复问已填的）
        if cfg and cfg.get("verified_at"):
            print(f"✅ 已存在验证过的配置（来源: {source}），不重复配置。")
            print(f"   通道 {cfg.get('channel')} / 档位 {cfg.get('tier')} / ${cfg.get('webhook_env')}")
            print("   如需修改加 --force。")
            return
        if cfg:
            print(f"⚠️  已有未验证的配置（来源: {source}）。补齐缺的字段，不重复询问已填项。")
            print(f"   已有: 通道 {cfg.get('channel')} / 档位 {cfg.get('tier')}")
            if not args.channel:
                die("--channel 必填（已有配置未验证时需确认通道类型）")
            if args.channel != cfg.get("channel") and not args.force:
                print(f"   注意: 通道类型将从 {cfg.get('channel')} 改为 {args.channel}")
        ch = args.channel
        if ch not in IM_CHANNELS:
            die(f"未知 channel: {ch}。可选: {', '.join(IM_CHANNELS)}")
        if args.tier not in IM_TIERS:
            die(f"未知 tier: {args.tier}。可选: {', '.join(IM_TIERS)}")
        new = {
            "channel": ch,
            "tier": args.tier,
            "notify_cmd": args.notify_cmd or (cfg or {}).get("notify_cmd", ""),
            "webhook_env": args.webhook_env or (cfg or {}).get("webhook_env", ""),
            "tmux_session": args.tmux_session or (cfg or {}).get("tmux_session", ""),
            "note": "webhook 只存环境变量名。发送前需 export 对应变量。",
        }
        if ch == "none":
            new["notify_cmd"] = ""
            new["tier"] = "none"
            new["note"] = "未配置 IM。lead 需要确认时直接在对话里问用户，不得自行发挥。"
        # L2：登记飞书应用信息（只存环境变量名，凭证绝不入库）
        if args.tier == "L2":
            if ch != "feishu":
                print(f"⚠️  L2 全双向目前只实现了飞书自建应用路径（当前档位: {ch}），"
                      f"L2 入向不会生效。建议先跑 im init --channel feishu。\n")
            new["app_id_env"] = args.app_id_env or (cfg or {}).get("app_id_env", "")
            new["app_secret_env"] = args.app_secret_env or (cfg or {}).get("app_secret_env", "")
            new["app_verify_mode"] = args.app_verify_mode or (cfg or {}).get("app_verify_mode", "")
            missing = [n for n, v in (("--app-id-env", new["app_id_env"]),
                                      ("--app-secret-env", new["app_secret_env"])) if not v]
            if missing:
                print(f"⚠️  L2 需要飞书应用凭证的环境变量名，当前缺失: {', '.join(missing)}")
                print("   例: --app-id-env FEISHU_APP_ID --app-secret-env FEISHU_APP_SECRET")
                print("   同时确认应用已申请「接收用户单聊消息」权限——权限不足会静默收不到消息。")
            path = save_im(team_dir, new, args.scope)
            print(f"✅ 配置已写入: {path}")
            print(f"   通道 {ch} / 档位 L2")
            if not L2_INBOUND_IMPLEMENTED:
                print()
                print("⚠️  **L2 入向接收尚未实现**——配置已登记，但用户回复目前仍需 `tmux attach` 回答。")
                print("   实现后本提示会移除。在此之前不要对外宣称「可在飞书里直接回复」。")
                print("   L1 的出向推送（webhook 提问）不受影响，可正常使用。")
            if new.get("app_verify_mode") == "longconn":
                print("   推荐 longconn：无需公网回调地址，能绕开内网穿透这个最大障碍。")
            else:
                print("   提示：callback 模式需要公网可访问的回调地址与常驻的内网穿透隧道。")
            return
        path = save_im(team_dir, new, args.scope)
        print(f"✅ 配置已写入: {path}")
        print(f"   通道 {ch} / 档位 {new['tier']}")
        if ch != "none":
            if not new["notify_cmd"]:
                print("   ⚠️  未提供 --notify-cmd，通道不可用。用 im test 验证。")
            else:
                print("\n下一步:验证发送（验证失败不算配置成功）")
                print("  scripts/teamctl.py im test")
        else:
            print("   已记录为不配置。lead 需确认时会在对话里直接问你。")

    elif args.im_cmd == "test":
        if not cfg:
            die("未配置 IM 通道，先跑: teamctl.py im init")
        if cfg.get("channel") == "none":
            print("ℹ️  通道为 none，无需测试。")
            return
        print(f"测试发送（{cfg.get('channel')} / {cfg.get('tier')}）...\n")
        ok = send_notify(cfg,
                         title=f"[{team_label(args)}] IM 通道验证",
                         body=f"这是一条验证消息。看到即说明 lead 可以向你提问。\n时间：{now_iso()}",
                         dry_run=args.dry_run)
        if args.dry_run:
            return
        if not ok:
            print("\n❌ 验证失败。**不要标记为已配置**——请与用户确认 webhook URL 与环境变量。")
            sys.exit(1)
        cfg["verified_at"] = now_iso()
        save_im(team_dir, cfg, args.scope)
        append_event(team_dir, {
            "ts": now_iso(), "team": team_label(args), "role": "lead",
            "event": "im_verified", "task": None,
            "summary": f"IM 通道验证成功: {cfg.get('channel')} / {cfg.get('tier')}",
        })
        print("✅ 验证成功，已记verified_at。")

    elif args.im_cmd == "ask":
        if not cfg or cfg.get("channel") == "none":
            print("ℹ️  未配置 IM 通道。")
            print("   → 请在当前对话里直接向用户提问，**不要自行发挥**。")
            print("   → 提问要求：一次问一件事、给 2-3 个选项、附背景与代价。")
            print("   → 用户答复后用 im answer --reply \"...\" --by user 落盘。")
            return
        if not cfg.get("verified_at"):
            print("⚠️  通道未验证过，建议先跑 im test。（仍会继续发送，但可能失败）\n")
        mid = new_id("M")
        opts = [o for o in (args.options or "").split("|") if o.strip()]
        lines = [
            f"[{team_label(args)}] Team Leader 需要你确认",
            "",
            f"任务: {args.task or '-'}    严重度: {args.severity}",
            "",
            args.question,
        ]
        if opts:
            lines += ["", "选项（回复选项字母即可）:"]
            for i, o in enumerate(opts):
                # 允许用户写成 "A. xxx" 或直接 "xxx"，统一由脚本补字母，避免出现 "A. A. xxx"
                label = re.sub(r"^\s*[A-Za-z][.)]\s*", "", o.strip())
                lines.append(f"  {chr(65+i)}. {label}")
        if args.background:
            lines += ["", f"背景: {args.background}"]
        if args.tried:
            lines += [f"已试: {args.tried}"]
        if args.default:
            lines += ["", f"若 {args.auto_after_min} 分钟内无答复，默认执行: {args.default}",
                      "（该默认动作会记为 auto_resolved，不视为你已确认）"]
        else:
            lines += ["", "该问题为 blocker，我不等待也不会自行决定——会停在这里等你回复。"]
        body = "\n".join(lines)

        ok = send_notify(cfg, title="", body=body, dry_run=args.dry_run)
        if args.dry_run:
            return
        rec = {
            "ts": now_iso(), "team": team_label(args), "role": "lead",
            "event": "im_ask", "task": args.task,
            "id": mid, "severity": args.severity,
            "summary": args.question,
            "options": [re.sub(r"^\s*[A-Za-z][.)]\s*", "", o.strip()) for o in opts],
            "background": args.background or "",
            "default": args.default or "", "auto_after_min": args.auto_after_min,
            "delivered": bool(ok),
        }
        append_event(team_dir, rec)
        print(f"{'✅ 已发送' if ok else '⚠️  发送失败（事件已记录，可重发）'} · id={mid}")
        print(f"   任务 {args.task or '-'} · {args.severity}")
        if cfg.get("tier") == "L2" and not L2_INBOUND_IMPLEMENTED:
            sess = cfg.get("tmux_session")
            print("\n   ℹ️  L2 入向尚未实现——用户请用 tmux 回答:"
                  + (f"  tmux attach -t {sess}" if sess else "  tmux attach 到 lead 窗口"))
        if args.severity == "blocker":
            print("\n   blocker 级：停下等用户答复，**不要自行决定**。")
            print("   答复后: teamctl.py im answer --id %s --reply \"...\" --by user" % mid)
        else:
            print("\n   非 blocker：继续做**不依赖该答复**的部分，挂起任务标 awaiting_user。")
        print("   答复必须落盘 decisions.md —— 否则 lead 冷重启会重新讨论同一问题。")

    elif args.im_cmd == "answer":
        events = read_jsonl(os.path.join(team_dir, EVENTS_FILE))
        target = None
        if args.id:
            target = next((e for e in events if e.get("event") == "im_ask" and e.get("id") == args.id), None)
            if not target:
                die(f"无此提问 id: {args.id}。用 teamctl.py im status 看未答列表。")
        else:
            target = next((e for e in reversed(events)
                           if e.get("event") == "im_ask" and not e.get("answered")), None)
            if not target:
                die("无未答提问")
        rec = {
            "ts": now_iso(), "team": team_label(args), "role": "lead",
            "event": "im_answer", "task": target.get("task"),
            "id": target.get("id"), "summary": f"用户答复: {args.reply}",
            "by": args.by,
        }
        append_event(team_dir, rec)
        print(f"✅ 已记录答复（{target.get('id')}）")
        print(f"   {args.reply}")
        print("\n必须再做两件事:")
        print(f"   1. 写进 decisions.md（D<next>）：决策内容 + 用户选择的理由 + 影响")
        print(f"   2. 若与原契约冲突，更新 contracts/<role>.md 的 Do-Not-Touch / Done Criteria")

    elif args.im_cmd == "status":
        if not team_dir:
            die("需要 --team 或 --team-dir")
        events = read_jsonl(os.path.join(team_dir, EVENTS_FILE))
        asks = [e for e in events if e.get("event") == "im_ask"]
        answered = {e.get("id") for e in events if e.get("event") == "im_answer"}
        pending = [e for e in asks if e.get("id") not in answered]
        print("【人机通道】")
        if cfg:
            print(f"  配置: {cfg.get('channel')} / {cfg.get('tier')}  ({source})")
            print(f"  验证: {cfg.get('verified_at') or '❌未验证'}")
            if cfg.get("tier") == "L2" and not L2_INBOUND_IMPLEMENTED:
                print("  入向: ⚠️ L2 入向尚未实现——用户回复请走 tmux，不要等飞书消息")
        else:
            print("  配置: ❌ 未配置（lead 需在对话里直接问用户）")
        print(f"  提问总数: {len(asks)}   未答:{len(pending)}")
        for e in pending:
            ago = ""
            try:
                mins = (datetime.now(CST) - datetime.fromisoformat(e["ts"])).total_seconds() / 60
                ago = f"  已等 {mins:.0f} 分钟"
            except ValueError:
                pass
            sev = {"blocker": "🔴", "question": "🟡", "info": "⚪"}.get(e.get("severity"), "⚪")
            print(f"  {sev} {e.get('id')}  {e['ts'][11:19]}  task={e.get('task') or '-'}{ago}")
            print(f"      {str(e.get('summary'))[:56]}")
            if e.get("default"):
                print(f"      默认动作（超时后）: {e['default']}")
        if pending and any(e.get("severity") == "blocker" for e in pending):
            print("\n  ⚠️  含未答 blocker——lead 应该停着等，不要继续推进相关任务。")


# --------------------------------------------------------------- cmd: adopt

def cmd_adopt(args):
    """把 init-exp 建好的实验目录适配为 agent-team 团队。

    场景：init-exp 的 team 模式转调 agent-team。init-exp 已生成
    AGENTS.md / goals.md / tasks.md / notes.md / results / logs，
    但缺契约、预算、上报通道。adopt 负责补齐并做命名对齐。
    """
    exp_dir = os.path.abspath(args.exp_dir)
    if not os.path.isdir(exp_dir):
        die(f"实验目录不存在: {exp_dir}")
    has_agents = os.path.isfile(os.path.join(exp_dir, "AGENTS.md"))
    has_tasks = os.path.isfile(os.path.join(exp_dir, "tasks.md"))
    if not (has_agents and has_tasks):
        die("看起来不是 init-exp 实验目录（缺 AGENTS.md 或 tasks.md）。"
            "非实验目录请改用 create_team.sh 生成 agent-team 骨架。")

    ensure_logs(exp_dir)

    # 1. 事件流 / inbox / attempts / budget
    for path, label in ((EVENTS_FILE, "事件流"), (INBOX_FILE, "上报队列"), (ATTEMPTS_FILE, "重试计数")):
        full = os.path.join(exp_dir, path)
        if os.path.isfile(full):
            print(f"⏭  {label}已存在: {path}")
        else:
            open(full, "a", encoding="utf-8").close()
            print(f"✅ 补充{label}: {path}")

    sess_path = os.path.join(exp_dir, SESSIONS_FILE)
    if os.path.isfile(sess_path):
        print(f"⏭  会话登记已存在: {SESSIONS_FILE}")
    else:
        write_json(sess_path, {
            "_comment": "agent-team 会话登记（由 init-exp team 模式经 adopt 生成）。",
            "team": team_label(args), "updated": now_iso(), "roles": {},
        })
        print(f"✅ 补充会话登记: {SESSIONS_FILE}")

    budget_path = os.path.join(exp_dir, BUDGET_FILE)
    if os.path.isfile(budget_path):
        print(f"⏭  预算配置已存在: {BUDGET_FILE}")
    else:
        write_json(budget_path, {
            "_comment": ("预算额度。per_task_min 单任务软超时（超过→checkpoint 收摊）；"
                         "hard_cap_min 单任务硬上限（超过→必须熔断上报）；total_min 团队总预算。"),
            "team": team_label(args),
            "per_task_min": args.per_task_min,
            "hard_cap_min": args.hard_cap_min,
            "total_min": args.total_min,
            "roles": {},
        })
        print(f"✅ 补充预算配置: {BUDGET_FILE}")

    # 2. 契约目录
    contracts = os.path.join(exp_dir, "contracts")
    os.makedirs(contracts, exist_ok=True)
    print(f"✅ 确认契约目录: contracts/")

    # 3. 生成 init-exp → agent-team 的命名映射草案，交由调用方（lead/agent）人工审校
    mapping_path = os.path.join(exp_dir, "TEAM-MAPPING.md")
    draft = f"""# init-exp → agent-team 命名映射（待人工审校）

> 由 `teamctl.py adopt` 生成。init-exp 的 team 模式转调 agent-team 后，
> 需人工确认下表，并按实际窗口/角色补全。

| 概念 | init-exp 原称| agent-team 规范 | 本实验实际 |
|------|--------------|-----------------|-----------|
| 主导者 | main 窗口 | `lead` 角色 | {args.lead_alias} |
| 执行者 | worker 窗口 | `builder` 角色 | 待填 |
| 目标 | `goals.md` | TEAM.md「目标」 + goals.md 引用 | 沿用 goals.md |
| 看板 | `tasks.md` | `tasks.md`（负责人列填角色名，非窗口名） | 沿用 |
| 协作说明 | `AGENTS.md` | TEAM.md | 需在AGENTS.md 中加引用 |
| session前缀 | `exp-` | `at-` | {args.session_name or 'exp-<name>'} |

## adopt 补齐的内容

- `logs/events.jsonl` — 结构化行为事件流
- `logs/inbox.jsonl` — worker→lead 上报队列（只允许向上）
- `logs/attempts.jsonl` — 退回重试计数
- `logs/budget.json` — 预算额度（软超时/硬上限/团队总预算）
- `logs/checkpoints/` — 生命周期检查点
- `contracts/` — 上下文契约目录（需 lead 为每个角色撰写）
- `logs/sessions.json` — 会话登记与 resume 命令

## 仍需人工完成

1. 为每个角色写 `contracts/<role>.md`（八段结构，见 agent-team 的 context-protocol.md）
2. 在 `AGENTS.md` 加一节指向 `decisions.md` / `logs/`，并把「负责人(窗口)」语义改成「负责人(角色)」
3. 团队脚本入口统一用 agent-team 的 `scripts/teamctl.py`
4. 把 init-exp 内嵌的 team-lead skill 内容收敛为指向 agent-team 的契约+ 生命周期规范
"""
    if os.path.isfile(mapping_path):
        print(f"⏭  映射草案已存在，未覆盖: TEAM-MAPPING.md")
    else:
        with open(mapping_path, "w", encoding="utf-8") as f:
            f.write(draft)
        print(f"✅ 生成命名映射草案: TEAM-MAPPING.md（请人工审校后合并进 AGENTS.md）")

    print(f"\n✅ adopt 完成: {exp_dir}")
    print("\n下一步（由调用方 agent 执行，不是脚本）:")
    print("  1. 读 TEAM-MAPPING.md，把命名映射人工合并进 AGENTS.md")
    print("  2. 为每个角色撰写 contracts/<role>.md（八段契约）")
    print("  3. 在 tasks.md 的「负责人」列填角色名而非窗口名")
    print("  4. 拉起 agent 后立刻 teamctl.py session set 登记会话")
    print("  5. 事件与会话规范以 agent-team 的 observability.md / lifecycle.md 为准")

    # IM 通道：只检查不配置。已配置则复用，未配置则提示确认。
    im_cfg, im_src = load_im(exp_dir)
    print()
    if im_cfg:
        print(f"✅ 人机通道已配置（{im_src}: {im_cfg.get('channel')} / {im_cfg.get('tier')}）——直接复用，不要重复配置")
    else:
        print("ℹ️  人机通道未配置。**需向用户确认**（不要自行编造 webhook URL）：")
        print("      teamctl.py im init --channel <feishu|wecom|dingtalk|none> --tier <L0|L1|L2> ...")
        print("      已配置过全局通道的话，可先跑 teamctl.py im check 看能否复用")


# --------------------------------------------------------------- cmd: team

def cmd_team(args):
    if args.team_cmd != "kill":
        die(f"未知 team 子命令: {args.team_cmd}")

    team_dir = find_team_dir(team_label(args), args.team_dir)
    sess_name = args.session_name or f"at-{os.path.basename(team_dir.rstrip('/'))}"

    # 1. 先出快照
    print("收摊前快照：")
    old = argparse.Namespace(team=args.team, team_dir=args.team_dir,
                             session_name=args.session_name, last=30)
    cmd_status(old)

    if not args.yes:
        print(f"⚠️  即将结束团队 {team_label(args)}（session: {sess_name}）")
        ans = input("确认？输入yes 继续: ").strip().lower()
        if ans != "yes":
            print("已取消。团队保持原状。")
            return

    # 2. 归档会话与checkpoint
    events = read_jsonl(os.path.join(team_dir, EVENTS_FILE))
    archive = os.path.join(team_dir, "logs", "archive")
    os.makedirs(archive, exist_ok=True)
    ts = datetime.now(CST).strftime("%Y%m%d-%H%M%S")
    if events:
        final = os.path.join(archive, f"events-{ts}.jsonl")
        with open(final, "w", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"✅ 事件流归档: {os.path.relpath(final, team_dir)}（{len(events)} 条）")

    # 3. tmux session 处理
    if args.kill_session:
        try:
            r = subprocess.run(["tmux", "has-session", "-t", sess_name],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                subprocess.run(["tmux", "kill-session", "-t", sess_name], timeout=10)
                print(f"✅ 已销毁 tmux session: {sess_name}")
            else:
                print(f"⏭  tmux session 不存在，跳过: {sess_name}")
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"⚠️  tmux 操作失败（{e}），请手动处理: tmux kill-session -t {sess_name}")
    else:
        print(f"ℹ️  未 kill tmux session（--kill-session 才销毁）。手动: tmux kill-session -t {sess_name}")

    print(f"\n✅ 团队 {team_label(args)} 已收摊。请补齐 decisions.md 的「为什么」，并向用户汇报遗留项。")


# ------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(
        prog="teamctl.py",
        description="Agent 团队运行时管控：事件记录 / 会话登记 / checkpoint / 团队快照",
    )
    p.add_argument("--team", help="团队名或团队目录名（可省略；用了 --team-dir 时自动取目录名）")
    p.add_argument("--team-dir", help="团队目录绝对路径（显式指定，避免向上查找歧义）")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("init", help="初始化事件流、上报队列、预算与会话登记").set_defaults(func=cmd_init)

    r = sub.add_parser("record", help="记录一条行为事件")
    r.add_argument("--role", required=True)
    r.add_argument("--event", required=True)
    r.add_argument("--task")
    r.add_argument("--summary", required=True)
    r.add_argument("--artifacts", help="逗号分隔的产出路径")
    r.add_argument("--elapsed-min", type=int)
    r.set_defaults(func=cmd_record)

    esc = sub.add_parser("escalate", help="向上级（lead）上报疑问/阻塞——通道只允许自下而上")
    esc.add_argument("--role", required=True, help="上报者（worker/builder 等，不能是 lead）")
    esc.add_argument("--to", default="lead", help="接收者，只能是 lead（默认 lead）")
    esc.add_argument("--task")
    esc.add_argument("--severity", choices=["blocker", "question", "info"], default="question",
                     help="blocker=必须停下等答复；question=继续做不依赖的部分；info=知会")
    esc.add_argument("--question", required=True, help="具体问题/阻塞点，要能独立理解")
    esc.add_argument("--tried", help="已尝试过什么（避免 lead 重复建议）")
    esc.set_defaults(func=cmd_escalate)

    ask = sub.add_parser("ask", help="lead 侧查看/答复上报队列")
    aks = ask.add_subparsers(dest="ask_cmd", required=True)
    akl = aks.add_parser("list"); akl.add_argument("--pending", action="store_true", help="只看未答（默认行为）")
    aka = aks.add_parser("answer"); aka.add_argument("--id", required=True)
    aka.add_argument("--answer", required=True); aka.add_argument("--role", default="lead")
    ask.set_defaults(func=cmd_ask)

    bud = sub.add_parser("budget", help="预算与熔断：设额度 / 记账 / 检查")
    bus = bud.add_subparsers(dest="budget_cmd", required=True)
    bs = bus.add_parser("set"); bs.add_argument("--per-task-min", type=int, help="单任务软超时分钟")
    bs.add_argument("--hard-cap-min", type=int, help="单任务硬上限分钟")
    bs.add_argument("--total-min", type=int, help="团队总预算分钟")
    bs.add_argument("--role"); bs.add_argument("--role-min", type=int, help="该角色专属软超时")
    bsp = bus.add_parser("spend"); bsp.add_argument("--role", required=True)
    bsp.add_argument("--task", required=True); bsp.add_argument("--minutes", type=float, required=True)
    bus.add_parser("check")
    bud.set_defaults(func=cmd_budget)

    att = sub.add_parser("attempts", help="退回重试计数与换手判断")
    ats = att.add_subparsers(dest="attempts_cmd", required=True)
    atb = ats.add_parser("bump"); atb.add_argument("--role", required=True)
    atb.add_argument("--task", required=True); atb.add_argument("--reason", help="退回原因/缺陷")
    ats.add_parser("list")
    atj = ats.add_parser("judge"); atj.add_argument("--task", required=True)
    att.set_defaults(func=cmd_attempts)

    s = sub.add_parser("session", help="会话登记 / 查看 / 恢复")
    ss = s.add_subparsers(dest="session_cmd", required=True)
    ss1 = ss.add_parser("set"); ss1.add_argument("--role", required=True)
    ss1.add_argument("--session-id", required=True); ss1.add_argument("--resume-cmd")
    ss1.add_argument("--cli"); ss1.add_argument("--mode")
    ss2 = ss.add_parser("list"); ss2.add_argument("--role", nargs="?")
    ss3 = ss.add_parser("resume"); ss3.add_argument("--role", required=True); ss3.add_argument("--session-name")
    ss4 = ss.add_parser("clear"); ss4.add_argument("--role", required=True)
    s.set_defaults(func=cmd_session)

    c = sub.add_parser("checkpoint", help="写 / 看 checkpoint 与冷重建指令")
    cs = c.add_subparsers(dest="ckpt_cmd", required=True)
    cw = cs.add_parser("write"); cw.add_argument("--role", required=True)
    cw.add_argument("--task", required=True); cw.add_argument("--file", required=True)
    cw.show = cs.add_parser("show"); cw.show.add_argument("--role", required=True)
    cw.show.add_argument("--task")
    cs.add_parser("coldstart").add_argument("--role", required=True)
    c.set_defaults(func=cmd_checkpoint)

    st = sub.add_parser("status", help="团队全景快照")
    st.add_argument("--last", type=int, default=10, help="显示最近 N 条事件（默认 10）")
    st.add_argument("--session-name")
    st.set_defaults(func=cmd_status)

    im = sub.add_parser("im", help="人机通道：check 查配置 / init 配置 / test 验证 / ask 提问 / answer 答复")
    im.add_argument("--scope", choices=["project", "global"], default="global",
                    help="配置作用域：global=本机所有团队复用（默认，推荐）/ project=仅本团队")
    ims = im.add_subparsers(dest="im_cmd", required=True)

    ic = ims.add_parser("check", help="检查是否已配置（幂等判断，勿重复配置）")
    ic = ims.add_parser("init", help="配置 IM 通道")
    ic.add_argument("--channel", required=True, choices=list(IM_CHANNELS))
    ic.add_argument("--tier", default="L1", choices=list(IM_TIERS))
    ic.add_argument("--notify-cmd", help="发送命令模板，从 stdin 读消息体，如 'curl -s -d @- \"$FEISHU_WEBHOOK\"'")
    ic.add_argument("--webhook-env", help="webhook URL 的环境变量名（只存变量名，不明文入库）")
    ic.add_argument("--tmux-session", help="L1/L2 档的 tmux session 名，供用户 attach 回答")
    ic.add_argument("--app-id-env", help="L2：飞书应用 app_id 的环境变量名（只存变量名，不入库）")
    ic.add_argument("--app-secret-env", help="L2：飞书应用 app_secret 的环境变量名（只存变量名，不入库）")
    ic.add_argument("--app-verify-mode", choices=list(L2_VERIFY_MODES),
                    help="L2：事件订阅接入方式（推荐 longconn，无需公网回调地址）")
    ic.add_argument("--force", action="store_true", help="已有配置时强制覆盖")

    it = ims.add_parser("test", help="发一条验证消息并标记 verified_at")
    it.add_argument("--dry-run", action="store_true", help="只显示将要发送的内容与命令")

    ia = ims.add_parser("ask", help="lead 向用户提问（带选项与默认动作）")
    ia.add_argument("--task")
    ia.add_argument("--severity", choices=["blocker", "question", "info"], default="blocker")
    ia.add_argument("--question", required=True)
    ia.add_argument("--options", help="选项，用 | 分隔，如 'A. 重构到插件层|B. 硬加到主文件|C. 先硬上再重构'")
    ia.add_argument("--background", help="背景，让用户无需翻上下文即可判断")
    ia.add_argument("--tried", help="已试过什么")
    ia.add_argument("--default", help="超时后的默认动作（必须是最保守的解释）")
    ia.add_argument("--auto-after-min", type=int, default=120, help="超时分钟数（默认 120）")
    ia.add_argument("--dry-run", action="store_true")

    ian = ims.add_parser("answer", help="记录用户答复（并提醒落盘 decisions.md）")
    ian.add_argument("--id", help="提问 id；省略则取最近一条未答")
    ian.add_argument("--reply", required=True)
    ian.add_argument("--by", default="user")

    ims.add_parser("status", help="查看通道状态与未答提问")
    im.set_defaults(func=cmd_im)

    ad = sub.add_parser("adopt", help="把 init-exp 实验目录适配为 agent-team 团队（补契约/预算/上报通道）")
    ad.add_argument("--exp-dir", required=True, help="init-exp 生成的实验目录绝对路径")
    ad.add_argument("--lead-alias", default="main", help="本实验主导者的实际窗口/角色名（默认 main）")
    ad.add_argument("--session-name", help="tmux session 名（默认 exp-<name>）")
    ad.add_argument("--per-task-min", type=int, default=60)
    ad.add_argument("--hard-cap-min", type=int, default=120)
    ad.add_argument("--total-min", type=int, default=600)
    ad.set_defaults(func=cmd_adopt)

    t = sub.add_parser("team", help="团队级操作")
    ts = t.add_subparsers(dest="team_cmd", required=True)
    tk = ts.add_parser("kill"); tk.add_argument("--kill-session", action="store_true")
    tk.add_argument("--yes", action="store_true"); tk.add_argument("--session-name")
    t.set_defaults(func=cmd_team)

    args = p.parse_args()
    # im init --scope global 是全局配置，不需要指定团队目录。
    # im check 在无团队上下文时也可用于查看全局配置。
    global_only = (args.cmd == "im"
                   and getattr(args, "im_cmd", None) in ("init", "check")
                   and not args.team and not args.team_dir)
    if not args.team and not args.team_dir and not global_only:
        p.error("需要 --team <名字> 或 --team-dir <路径>")
    if not hasattr(args, "func"):
        p.error("需要指定子命令")
    args.func(args)


if __name__ == "__main__":
    main()