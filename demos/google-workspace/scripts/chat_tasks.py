"""
Google Chat 任务抽取器 —— 从群消息里用 LLM 抽取「真任务」，去重后写入 Google Sheet。

与 chat_digest.py 的关系：
    chat_digest.py 拉消息 → 输出 markdown/json 摘要（人读）。
    chat_tasks.py  拉消息 → LLM 抽取 actionable 任务 → 写结构化 Sheet（追踪）。
两者共用 chat_digest 的拉取 + People API 解析逻辑（import 复用，不重写）。

抽取方式：
    LLM（默认）—— 调 demos/data-agent/lib/llm.py 的可插拔 backend
    （provider=galileo 走 Roche gateway / anthropic 走公网 / mock 离线）。
    模型判断「这条消息是不是一个需要某人去做的任务」，并抽出 title/owner/due，
    剔除闲聊（👌感谢确认、好的~）。这是相对老表 extracted_by=keyword 的改进。

去重：
    dedup_key = sha256(space_id + source_message_ts)[:16]。
    写表前先读已有 dedup_key，只 append 新任务 → 脚本幂等，反复跑不重复。

用法：
    # 抽取过去 7 天两个群的任务，写入新建的 Sheet
    python3 chat_tasks.py --since 7d --spaces AAQAJI8eMKw AAQAfOIdqx0

    # 复用已有 Sheet（增量追加，靠 dedup_key 去重）
    python3 chat_tasks.py --since 3d --sheet-id 1AbC...XyZ

    # 离线管道自测（不调 LLM、不写 Sheet）
    python3 chat_tasks.py --since 7d --provider mock --dry-run

凭证：
    Google：/tmp/google_token.json 或 GOOGLE_TOKEN_JSON（同 gw_client.py）
    LLM：   GALILEO_BEDROCK_API_KEY（provider=galileo）等，见 lib/llm.py
"""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

# 复用 chat_digest 的拉取 + 解析逻辑，不重写
from chat_digest import (
    DEFAULT_SPACES,
    fetch_messages,
    is_noise,
    parse_since,
    resolve_user_names,
)
from gw_client import get_chat_service, get_drive_service, get_sheets_service

# data-agent 的可插拔 LLM backend（SSOT，不在本文件重造）
_DATA_AGENT_LIB = os.path.join(
    os.path.dirname(__file__), "..", "..", "data-agent"
)
sys.path.insert(0, os.path.abspath(_DATA_AGENT_LIB))

# 新表的列 schema（沿用老表语义，去掉冗余列）
COLUMNS = [
    "task_id", "created_at", "source_message_ts", "source_space",
    "source_sender", "source_link", "title", "owner", "due",
    "priority", "status", "comments", "extracted_by", "dedup_key",
]

DEFAULT_SHEET_TITLE = "Chat Tasks Tracker (LLM)"
TAB_NAME = "Tasks"

# LLM 抽取的 system prompt —— 关键：明确「什么是任务、什么是闲聊」
EXTRACT_SYSTEM = """你是一个任务抽取助手。我会给你 Google Chat 群里一个对话线程的消息。
你的工作：判断这个线程里是否包含「需要某人去做的具体行动项（actionable task）」，如果有，抽取出来。

判定为任务的标准（必须满足）：
- 有明确的待办动作（提单、导入、审批、确认数据、填表、上传、跟进等）
- 隐含或明确有负责人

不是任务（直接跳过，不要抽）：
- 纯确认/寒暄：「好的」「收到」「感谢确认」「👌」「我晚上处理」
- 纯信息陈述/讨论，没有要某人做的动作
- 已经完成的事（「已经更新了」「已处理」）

输出严格的 JSON（不要 markdown 代码块包裹），格式：
{"tasks": [{"title": "<一句话任务描述，动词开头>", "owner": "<负责人名字，没有写 null>", "due": "<YYYY-MM-DD 或 null>", "priority": "<high|medium|low>"}]}

如果线程里没有任何任务，返回 {"tasks": []}。
owner 用消息里出现的人名（如被 @ 的人、被点名的人）。due 只在消息明确提到日期时才填，不要推测。"""


def thread_to_prompt(msgs: list[dict], user_map: dict) -> str:
    """把一个 thread 的消息列表渲染成 LLM 的 user prompt。"""
    lines = []
    for m in msgs:
        sid = m.get("sender", {}).get("name", "").replace("users/", "")
        name = user_map.get(sid, {}).get("name", f"User {sid[:8]}") if sid else "Unknown"
        text = (m.get("text", "") or "").strip()
        if text:
            lines.append(f"[{name}]: {text}")
    return "\n".join(lines)


def group_by_thread(messages: list[dict]) -> dict[str, list[dict]]:
    """按 thread 分组（chat_digest 的同名函数返回值结构略不同，这里用原始 msg）。"""
    from collections import defaultdict
    threads = defaultdict(list)
    for msg in messages:
        tid = msg.get("thread", {}).get("name", "no-thread")
        threads[tid].append(msg)
    for tmsgs in threads.values():
        tmsgs.sort(key=lambda m: m.get("createTime", ""))
    return dict(threads)


def make_dedup_key(space_id: str, message_ts: str) -> str:
    """dedup_key = sha256(space_id + message_ts)[:16]，幂等去重用。"""
    raw = f"{space_id}|{message_ts}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def extract_tasks_from_threads(threads, space_id, space_name, user_map, backend):
    """对每个 thread 调 LLM 抽取任务，返回行 dict 列表。"""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for tid, msgs in threads.items():
        if not msgs:
            continue
        prompt = thread_to_prompt(msgs, user_map)
        if not prompt.strip():
            continue
        raw = _complete_with_retry(backend, prompt, tid)
        if raw is None:
            continue

        tasks = _parse_llm_json(raw)
        if not tasks:
            continue

        first = msgs[0]
        msg_ts = first.get("createTime", "")
        sender_id = first.get("sender", {}).get("name", "").replace("users/", "")
        sender_name = user_map.get(sender_id, {}).get("name", sender_id) if sender_id else ""
        # source_link: 取 thread 第一条消息的 chat 链接
        msg_name = first.get("name", "")  # spaces/X/messages/Y
        link = _build_chat_link(msg_name)
        dkey = make_dedup_key(space_id, msg_ts)

        for t in tasks:
            rows.append({
                "task_id": "",  # 写表时按行号补
                "created_at": now,
                "source_message_ts": msg_ts,
                "source_space": space_name,
                "source_sender": sender_name,
                "source_link": link,
                "title": t.get("title", "").strip(),
                "owner": (t.get("owner") or "").strip() if t.get("owner") not in (None, "null") else "",
                "due": (t.get("due") or "").strip() if t.get("due") not in (None, "null") else "",
                "priority": t.get("priority", "medium"),
                "status": "open",
                "comments": "",
                "extracted_by": f"llm:{backend.name}",
                "dedup_key": dkey,
            })
    return rows


def _complete_with_retry(backend, prompt: str, tid: str, max_retries: int = 5):
    """调 LLM，遇 429 限流指数退避重试。返回原始文本，彻底失败返回 None。"""
    delay = 2.0
    for attempt in range(max_retries):
        try:
            return backend.complete(system=EXTRACT_SYSTEM, user=prompt)
        except Exception as e:
            msg = str(e)
            is_429 = "429" in msg or "rate limit" in msg.lower()
            if is_429 and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # 2 → 4 → 8 → 16s
                continue
            print(f"⚠️  LLM 抽取失败 (thread {tid[:24]}): {msg[:100]}", file=sys.stderr)
            return None
    return None


def _parse_llm_json(raw: str) -> list[dict]:
    """从 LLM 输出里抠出 tasks 数组，容忍 markdown 代码块包裹。"""
    s = raw.strip()
    if s.startswith("```"):
        # 去掉 ```json ... ``` 包裹
        s = s.split("```", 2)[1] if "```" in s[3:] else s
        s = s.lstrip("json").strip()
        if s.endswith("```"):
            s = s[:-3].strip()
    try:
        data = json.loads(s)
        return data.get("tasks", []) if isinstance(data, dict) else []
    except (ValueError, AttributeError):
        return []


def _build_chat_link(msg_name: str) -> str:
    """spaces/AAA/messages/BBB.CCC → chat.google.com 深链。"""
    if not msg_name:
        return ""
    parts = msg_name.split("/")
    if len(parts) >= 4:
        space, msg = parts[1], parts[3]
        return f"https://chat.google.com/room/{space}/{msg}"
    return ""


# ── Sheet I/O ──────────────────────────────────────────────

def get_or_create_sheet(sheets, drive, sheet_id: str | None, title: str):
    """返回 (sheet_id, 已有 dedup_key 集合)。sheet_id 为 None 时新建。"""
    if sheet_id:
        existing = _read_existing_dedup_keys(sheets, sheet_id)
        return sheet_id, existing

    # 新建 spreadsheet + 写表头
    body = {"properties": {"title": title}, "sheets": [{"properties": {"title": TAB_NAME}}]}
    created = sheets.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    new_id = created["spreadsheetId"]
    sheets.spreadsheets().values().update(
        spreadsheetId=new_id,
        range=f"{TAB_NAME}!A1",
        valueInputOption="RAW",
        body={"values": [COLUMNS]},
    ).execute()
    return new_id, set()


def _read_existing_dedup_keys(sheets, sheet_id: str) -> set[str]:
    """读已有表的 dedup_key 列，用于增量去重。"""
    try:
        resp = sheets.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=f"{TAB_NAME}!A1:Z"
        ).execute()
    except Exception as e:
        print(f"⚠️  读已有表失败: {str(e)[:120]}", file=sys.stderr)
        return set()
    vals = resp.get("values", [])
    if not vals:
        return set()
    header = vals[0]
    if "dedup_key" not in header:
        return set()
    idx = header.index("dedup_key")
    return {row[idx] for row in vals[1:] if len(row) > idx and row[idx]}


def append_rows(sheets, sheet_id: str, rows: list[dict], start_task_n: int):
    """把新行 append 到表尾，task_id 顺序编号。"""
    values = []
    for i, r in enumerate(rows):
        r["task_id"] = f"t-{start_task_n + i:04d}"
        values.append([r.get(c, "") for c in COLUMNS])
    sheets.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{TAB_NAME}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()


def _count_existing_rows(sheets, sheet_id: str) -> int:
    """已有数据行数（不含表头），用于 task_id 续号。"""
    try:
        resp = sheets.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=f"{TAB_NAME}!A1:A"
        ).execute()
        return max(0, len(resp.get("values", [])) - 1)
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser(description="Google Chat 任务抽取器（LLM → Sheet）")
    parser.add_argument("--since", default="7d", help="时间范围: 24h, 3d, 7d, 2026-06-01 (默认 7d)")
    parser.add_argument("--spaces", nargs="*", help="Space ID 列表 (默认 chat_digest 的 DEFAULT_SPACES)")
    parser.add_argument("--sheet-id", help="复用已有 Sheet（增量追加）；不给则新建")
    parser.add_argument("--sheet-title", default=DEFAULT_SHEET_TITLE, help="新建 Sheet 的标题")
    parser.add_argument("--provider", default="galileo",
                        help="LLM provider: galileo(默认) | anthropic | mock")
    parser.add_argument("--model", help="覆盖默认模型")
    parser.add_argument("--dry-run", action="store_true", help="只抽取不写 Sheet，打印结果")
    args = parser.parse_args()

    since = parse_since(args.since)
    spaces = {}
    if args.spaces:
        for sid in args.spaces:
            spaces[sid] = DEFAULT_SPACES.get(sid, sid)
    else:
        spaces = DEFAULT_SPACES.copy()

    print(f"📡 拉取消息 since={since.strftime('%Y-%m-%d %H:%M UTC')}", file=sys.stderr)
    print(f"   Spaces: {', '.join(spaces.values())}", file=sys.stderr)

    from lib.llm import get_backend  # demos/data-agent/lib/llm.py（已 sys.path 注入 data-agent 根）
    backend = get_backend(provider=args.provider, model=args.model)
    print(f"🤖 LLM backend: {backend.name} (model={getattr(backend, 'model', 'n/a')})", file=sys.stderr)

    chat = get_chat_service()

    # 拉取 + 解析人名
    all_rows = []
    all_sender_ids: set[str] = set()
    per_space_threads = {}
    for space_id, space_name in spaces.items():
        msgs = fetch_messages(chat, space_id, since)
        msgs = [m for m in msgs if not is_noise(m)]
        threads = group_by_thread(msgs)
        per_space_threads[(space_id, space_name)] = threads
        print(f"   {space_name}: {len(msgs)} msgs / {len(threads)} threads", file=sys.stderr)
        for m in msgs:
            sid = m.get("sender", {}).get("name", "").replace("users/", "")
            if sid:
                all_sender_ids.add(sid)

    print(f"📡 解析 {len(all_sender_ids)} 个 sender 姓名 (People API)...", file=sys.stderr)
    user_map = resolve_user_names(all_sender_ids)

    # LLM 抽取
    for (space_id, space_name), threads in per_space_threads.items():
        rows = extract_tasks_from_threads(threads, space_id, space_name, user_map, backend)
        all_rows.extend(rows)

    print(f"✅ 抽取到 {len(all_rows)} 个候选任务", file=sys.stderr)

    if args.dry_run:
        for r in all_rows:
            print(f"  [{r['priority']:6s}] {r['title']}  (owner={r['owner'] or '?'}, due={r['due'] or '?'}, by={r['source_space']})")
        print(f"\n(dry-run: 未写 Sheet)", file=sys.stderr)
        return

    # 写 Sheet
    sheets = get_sheets_service()
    drive = get_drive_service()
    sheet_id, existing_keys = get_or_create_sheet(sheets, drive, args.sheet_id, args.sheet_title)

    # 去重
    fresh = [r for r in all_rows if r["dedup_key"] not in existing_keys]
    # 同批内也去重（同一 thread 多任务 dedup_key 相同，靠 title 二次区分）
    seen = set()
    deduped = []
    for r in fresh:
        k = (r["dedup_key"], r["title"])
        if k not in seen:
            seen.add(k)
            deduped.append(r)

    skipped = len(all_rows) - len(deduped)
    if not deduped:
        print(f"✅ 没有新任务（{skipped} 个已存在/重复，已跳过）", file=sys.stderr)
        _print_sheet_url(sheet_id)
        return

    start_n = _count_existing_rows(sheets, sheet_id) + 1
    append_rows(sheets, sheet_id, deduped, start_n)
    print(f"✅ 写入 {len(deduped)} 个新任务（跳过 {skipped} 个重复）", file=sys.stderr)
    _print_sheet_url(sheet_id)


def _print_sheet_url(sheet_id: str):
    print(f"🔗 https://docs.google.com/spreadsheets/d/{sheet_id}/edit", file=sys.stderr)


if __name__ == "__main__":
    main()
