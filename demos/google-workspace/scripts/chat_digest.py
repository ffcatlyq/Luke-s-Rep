"""
Google Chat 消息摘要工具。

从指定 Space 拉取消息，按 thread 分组，输出结构化 Markdown 或 JSON。
支持群组消息和私信（DM）。

用法：
    # 过去 24 小时的消息（默认 CDE Community）
    python3 chat_digest.py --since 24h

    # 过去 7 天，指定 space
    python3 chat_digest.py --since 7d --spaces AAQAJI8eMKw AAQAfOIdqx0

    # 从指定日期开始
    python3 chat_digest.py --since 2026-04-20

    # 关键词过滤
    python3 chat_digest.py --since 3d --keywords automation,training,cost

    # 查看与某人的私信
    python3 chat_digest.py --dm calixto.harada@roche.com --since 3d

    # 连同图片等附件一起下载到目录
    python3 chat_digest.py --dm calixto.harada@roche.com --download-attachments /tmp/imgs

    # 输出 JSON
    python3 chat_digest.py --since 24h --format json --output /tmp/digest.json

    # 输出 Markdown 到文件
    python3 chat_digest.py --since 7d --output /tmp/digest.md
"""
import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from googleapiclient.http import MediaIoBaseDownload

from gw_client import get_chat_service, get_people_service

# 默认关注的 Space
DEFAULT_SPACES = {
    "AAQAJI8eMKw": "CDE Community",
    "AAQA5x-JPxc": "Build CLI",
    "AAQAfOIdqx0": "CD2-AI-Hackathon",
}


def list_spaces():
    """列出用户加入的所有 Space，用于动态订阅。"""
    chat = get_chat_service()
    all_spaces = []
    page_token = None

    while True:
        resp = chat.spaces().list(pageSize=100, pageToken=page_token).execute()
        all_spaces.extend(resp.get("spaces", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    print(f"{'ID':<20} {'Type':<18} {'Name'}")
    print("-" * 70)
    for s in all_spaces:
        sid = s["name"].replace("spaces/", "")
        stype = s.get("spaceType", "")
        name = s.get("displayName", "(DM)")
        marker = " ⭐" if sid in DEFAULT_SPACES else ""
        print(f"{sid:<20} {stype:<18} {name}{marker}")
    print(f"\n共 {len(all_spaces)} 个 Space（⭐ = 已订阅）")
    print(f"\n添加订阅: python3 chat_digest.py --spaces {' '.join(DEFAULT_SPACES)} <新ID>")


def parse_since(since_str: str) -> datetime:
    """解析 --since 参数为 UTC datetime。

    支持格式：
    - 相对时间：24h, 3d, 1w
    - 绝对日期：2026-04-20
    - ISO 时间戳：2026-04-20T08:00:00
    """
    now = datetime.now(timezone.utc)

    # 相对时间
    match = re.match(r"^(\d+)(h|d|w)$", since_str)
    if match:
        value, unit = int(match.group(1)), match.group(2)
        delta = {"h": timedelta(hours=value), "d": timedelta(days=value), "w": timedelta(weeks=value)}
        return now - delta[unit]

    # 绝对日期/时间
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(since_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    print(f"❌ 无法解析时间参数: {since_str}")
    print("   支持格式: 24h, 3d, 1w, 2026-04-20, 2026-04-20T08:00:00")
    sys.exit(1)


def fetch_messages(chat, space_id: str, since: datetime) -> list[dict]:
    """从指定 space 拉取 since 之后的所有消息。"""
    space_name = f"spaces/{space_id}"
    all_messages = []
    page_token = None

    # Chat API filter 支持 createTime 过滤
    time_filter = f'createTime > "{since.strftime("%Y-%m-%dT%H:%M:%SZ")}"'

    while True:
        try:
            resp = chat.spaces().messages().list(
                parent=space_name,
                pageSize=100,
                filter=time_filter,
                pageToken=page_token,
            ).execute()
        except Exception as e:
            # filter 不支持时回退到全量拉取 + 手动过滤
            if "filter" in str(e).lower() or "400" in str(e):
                return _fetch_messages_fallback(chat, space_name, since)
            raise

        msgs = resp.get("messages", [])
        all_messages.extend(msgs)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return all_messages


def _fetch_messages_fallback(chat, space_name: str, since: datetime) -> list[dict]:
    """回退方案：拉取全部消息后手动按时间过滤。"""
    all_messages = []
    page_token = None

    for _ in range(20):  # 最多 2000 条
        resp = chat.spaces().messages().list(
            parent=space_name,
            pageSize=100,
            orderBy="createTime desc",
            pageToken=page_token,
        ).execute()
        msgs = resp.get("messages", [])

        for msg in msgs:
            created = msg.get("createTime", "")
            if created:
                msg_time = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if msg_time >= since:
                    all_messages.append(msg)
                else:
                    # 消息按时间倒序，遇到早于 since 的就停止
                    return all_messages

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return all_messages


def group_by_thread(messages: list[dict]) -> dict[str, list[dict]]:
    """按 thread 分组消息，保持时间顺序。"""
    threads = defaultdict(list)
    for msg in messages:
        thread_name = msg.get("thread", {}).get("name", "no-thread")
        threads[thread_name].append(msg)

    # 每个 thread 内按时间排序
    for thread_msgs in threads.values():
        thread_msgs.sort(key=lambda m: m.get("createTime", ""))

    return dict(threads)


def filter_by_keywords(messages: list[dict], keywords: list[str]) -> list[dict]:
    """按关键词过滤消息（匹配任一关键词即保留）。"""
    if not keywords:
        return messages

    keywords_lower = [k.lower() for k in keywords]
    filtered = []
    for msg in messages:
        text = (msg.get("text", "") or "").lower()
        if any(k in text for k in keywords_lower):
            filtered.append(msg)
    return filtered


def is_noise(msg: dict) -> bool:
    """过滤系统消息和纯 emoji/短回复。"""
    text = msg.get("text", "") or ""
    # 有附件的消息永远保留(哪怕无文本)——纯附件消息(文件/图/zip)是内容不是噪音。
    # 早期只按 text 判噪音,把纯附件消息误删,--download-attachments 漏下载(2026-07 维卫 zip 踩过)。
    if msg.get("attachment"):
        return False
    # 纯空白
    if not text.strip():
        return True
    # 纯 emoji（少于 5 个字符且无字母数字）
    if len(text.strip()) < 5 and not re.search(r"[a-zA-Z0-9\u4e00-\u9fff]", text):
        return True
    return False


def resolve_user_names(user_ids: set[str]) -> dict[str, dict]:
    """批量调 People API 解析 user ID → {name, email}。

    Chat API messages.list 只返回 users/<21位数字ID> 和 type，不返回 displayName。
    需要走 People API 的 directory scope 才能拿到姓名/邮箱。

    user_ids: 形如 {"109521539836131342522", ...} 的纯 ID 集合
    返回: {"109521539836131342522": {"name": "Silicon Hitchhiker", "email": "..."}, ...}
    """
    if not user_ids:
        return {}

    people = get_people_service()
    resolved: dict[str, dict] = {}
    ids = list(user_ids)

    # getBatchGet 一次最多 200 个 resource
    for i in range(0, len(ids), 50):
        batch = ids[i : i + 50]
        resource_names = [f"people/{uid}" for uid in batch]
        try:
            resp = people.people().getBatchGet(
                resourceNames=resource_names,
                personFields="names,emailAddresses",
            ).execute()
        except Exception as e:
            print(f"⚠️  People API getBatchGet failed: {str(e)[:200]}", file=sys.stderr)
            return resolved

        for entry in resp.get("responses", []):
            person = entry.get("person", {})
            uid = person.get("resourceName", "").replace("people/", "")
            if not uid:
                # requested 字段在错误时还有
                requested = entry.get("requestedResourceName", "")
                uid = requested.replace("people/", "")
            names = person.get("names", [])
            emails = person.get("emailAddresses", [])
            display = names[0].get("displayName") if names else None
            email = emails[0].get("value") if emails else None
            resolved[uid] = {
                "name": display or f"User {uid[:8]}",
                "email": email or "",
            }

    return resolved


def fetch_read_states(chat, space_ids: list[str]) -> dict[str, str]:
    """拉取每个 space 的 lastReadTime。返回 {space_id: lastReadTime ISO 字符串}。"""
    states: dict[str, str] = {}
    for sid in space_ids:
        try:
            resp = chat.users().spaces().getSpaceReadState(
                name=f"users/me/spaces/{sid}/spaceReadState"
            ).execute()
            states[sid] = resp.get("lastReadTime", "")
        except Exception as e:
            print(f"⚠️  spaceReadState({sid}) failed: {str(e)[:150]}", file=sys.stderr)
            states[sid] = ""
    return states


def format_message(msg: dict, user_map: dict[str, dict] | None = None) -> dict:
    """提取消息的关键字段。

    user_map: resolve_user_names() 的输出，用于把 sender ID 解析为人名。
    """
    sender_obj = msg.get("sender", {})
    sender_id = sender_obj.get("name", "").replace("users/", "")
    sender_name = sender_obj.get("displayName")  # Chat API 一般不返回，留作兜底
    if not sender_name and user_map and sender_id in user_map:
        sender_name = user_map[sender_id]["name"]
    if not sender_name:
        sender_name = f"User {sender_id[:8]}" if sender_id else "Unknown"

    attachments = [
        {
            "name": a.get("contentName") or "attachment",
            "type": a.get("contentType") or "",
            "ref": a.get("attachmentDataRef", {}).get("resourceName"),
        }
        for a in (msg.get("attachment") or [])
    ]

    return {
        "sender": sender_name,
        "sender_id": sender_id,
        "msg_id": msg.get("name", "").split("/")[-1],
        "time": msg.get("createTime", "")[:19],
        "text": msg.get("text", "") or "",
        "thread": msg.get("thread", {}).get("name", ""),
        "attachments": attachments,
    }


def download_attachment(chat, ref: str, dest: str) -> None:
    """下载单个 Chat 附件（media API）到 dest 路径。"""
    req = chat.media().download_media(resourceName=ref)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    with open(dest, "wb") as f:
        f.write(buf.getvalue())


def download_space_attachments(chat, space_data: dict[str, dict], out_dir: str) -> int:
    """遍历已格式化的 space_data，把带 ref 的附件落盘，并回填 local 路径。"""
    os.makedirs(out_dir, exist_ok=True)
    count = 0
    for info in space_data.values():
        for msgs in info["threads"].values():
            for msg in msgs:
                for att in msg.get("attachments", []):
                    ref = att.get("ref")
                    if not ref:
                        continue
                    fname = f"{msg.get('msg_id', 'msg')}_{att['name']}"
                    dest = os.path.join(out_dir, fname)
                    try:
                        download_attachment(chat, ref, dest)
                        att["local"] = dest
                        count += 1
                    except Exception as e:
                        print(f"⚠️  附件下载失败 {att['name']}: {e}", file=sys.stderr)
    return count


def to_markdown(space_data: dict[str, dict]) -> str:
    """将分组后的消息转为 Markdown 格式。"""
    lines = []
    lines.append("# Google Chat Digest\n")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    for space_id, info in space_data.items():
        space_name = info["display_name"]
        threads = info["threads"]
        msg_count = info["message_count"]
        last_read = info.get("last_read_time", "")

        lines.append(f"## {space_name} ({msg_count} messages)\n")
        if last_read:
            lines.append(f"_Last read: {last_read[:19]} UTC_\n")

        if not threads:
            lines.append("_No messages in this period._\n")
            continue

        for thread_id, msgs in threads.items():
            # 用第一条消息的前 80 字符作为 thread 标题
            first_text = msgs[0]["text"][:80].replace("\n", " ")
            lines.append(f"### 💬 {first_text}...\n")

            for msg in msgs:
                sender = msg["sender"]
                time = msg["time"][11:16] if len(msg["time"]) >= 16 else msg["time"]
                date = msg["time"][:10]
                text = msg["text"].strip()
                unread_marker = " 🆕" if msg.get("unread") else ""
                # 缩进多行文本
                text_lines = text.split("\n")
                formatted = text_lines[0]
                if len(text_lines) > 1:
                    formatted += "\n" + "\n".join(f"  {l}" for l in text_lines[1:5])
                    if len(text_lines) > 5:
                        formatted += f"\n  _...({len(text_lines) - 5} more lines)_"

                lines.append(f"- **[{date} {time}] {sender}**{unread_marker}: {formatted}\n")

                for att in msg.get("attachments", []):
                    loc = att.get("local")
                    label = f"`{loc}`" if loc else att["name"]
                    lines.append(f"  - 📎 {label}\n")

            lines.append("")

    return "\n".join(lines)


def to_json(space_data: dict[str, dict]) -> str:
    """将分组后的消息转为 JSON 格式。"""
    return json.dumps(space_data, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Google Chat 消息摘要工具")
    parser.add_argument(
        "--list-spaces",
        action="store_true",
        help="列出所有可订阅的 Space（用于发现 Space ID）",
    )
    parser.add_argument(
        "--since",
        default="24h",
        help="时间范围: 24h, 3d, 1w, 或日期 2026-04-20 (默认: 24h)",
    )
    parser.add_argument(
        "--dm",
        help="通过邮箱查看与某人的私信 (如: calixto.harada@roche.com)",
    )
    parser.add_argument(
        "--spaces",
        nargs="*",
        help="Space ID 列表 (默认: CDE Community + CD2-AI-Hackathon)",
    )
    parser.add_argument(
        "--keywords",
        help="逗号分隔的关键词过滤 (如: automation,training,cost)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="输出格式 (默认: markdown)",
    )
    parser.add_argument(
        "--output",
        help="输出文件路径 (默认: stdout)",
    )
    parser.add_argument(
        "--no-filter-noise",
        action="store_true",
        help="不过滤系统消息和纯 emoji",
    )
    parser.add_argument(
        "--show-readstate",
        action="store_true",
        help="标记每条消息是否已读（基于 spaceReadState.lastReadTime）",
    )
    parser.add_argument(
        "--no-resolve-names",
        action="store_true",
        help="不调 People API 解析 sender 名字（用于跳过权限不足的环境）",
    )
    parser.add_argument(
        "--download-attachments",
        metavar="DIR",
        help="把消息附件（图片等）下载到指定目录，输出里标注本地路径",
    )

    args = parser.parse_args()

    if args.list_spaces:
        list_spaces()
        return

    # 解析参数
    since = parse_since(args.since)
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []

    chat = get_chat_service()

    # DM 模式：通过邮箱直接定位私信
    if args.dm:
        email = args.dm
        print(f"📡 查找与 {email} 的私信...", file=sys.stderr)
        try:
            dm = chat.spaces().findDirectMessage(name=f"users/{email}").execute()
        except Exception as e:
            print(f"❌ 找不到与 {email} 的私信: {e}", file=sys.stderr)
            sys.exit(1)

        space_id = dm["name"].replace("spaces/", "")
        spaces = {space_id: f"DM with {email}"}
        print(f"   Space: {dm['name']}", file=sys.stderr)
    else:
        spaces = {}
        if args.spaces:
            for sid in args.spaces:
                spaces[sid] = DEFAULT_SPACES.get(sid, sid)
        else:
            spaces = DEFAULT_SPACES.copy()

    print(f"📡 拉取消息: since={since.strftime('%Y-%m-%d %H:%M UTC')}", file=sys.stderr)
    print(f"   Spaces: {', '.join(spaces.values())}", file=sys.stderr)
    if keywords:
        print(f"   Keywords: {', '.join(keywords)}", file=sys.stderr)

    # 拉取已读时间（用于标记 unread）
    read_states: dict[str, str] = {}
    if args.show_readstate:
        print("📡 拉取 spaceReadState...", file=sys.stderr)
        read_states = fetch_read_states(chat, list(spaces.keys()))

    # 拉取消息
    raw_per_space: dict[str, list[dict]] = {}
    all_sender_ids: set[str] = set()

    for space_id, display_name in spaces.items():
        print(f"   Fetching {display_name}...", file=sys.stderr, end=" ")
        messages = fetch_messages(chat, space_id, since)
        print(f"{len(messages)} raw messages", file=sys.stderr)

        if not args.no_filter_noise:
            messages = [m for m in messages if not is_noise(m)]

        if keywords:
            messages = filter_by_keywords(messages, keywords)

        raw_per_space[space_id] = messages

        for m in messages:
            sid = m.get("sender", {}).get("name", "").replace("users/", "")
            if sid:
                all_sender_ids.add(sid)

    # 批量解析 sender ID → 姓名
    user_map: dict[str, dict] = {}
    if not args.no_resolve_names and all_sender_ids:
        print(f"📡 解析 {len(all_sender_ids)} 个 sender 姓名 (People API)...", file=sys.stderr)
        user_map = resolve_user_names(all_sender_ids)
        resolved_cnt = sum(1 for v in user_map.values() if not v["name"].startswith("User "))
        print(f"   解析成功: {resolved_cnt}/{len(all_sender_ids)}", file=sys.stderr)

    # 格式化 + 标记已读
    space_data = {}
    total_messages = 0

    for space_id, display_name in spaces.items():
        messages = raw_per_space[space_id]
        formatted = [format_message(m, user_map) for m in messages]

        # 已读标记：createTime > lastReadTime → unread
        last_read = read_states.get(space_id, "")
        if args.show_readstate:
            for f in formatted:
                f["unread"] = bool(last_read) and f["time"] > last_read[:19]

        threads_raw = defaultdict(list)
        for msg in formatted:
            threads_raw[msg["thread"]].append(msg)

        threads_sorted = dict(
            sorted(threads_raw.items(), key=lambda x: x[1][0]["time"] if x[1] else "")
        )

        space_data[space_id] = {
            "display_name": display_name,
            "message_count": len(formatted),
            "last_read_time": last_read,
            "threads": threads_sorted,
        }
        total_messages += len(formatted)

    print(f"✅ Total: {total_messages} messages in {len(space_data)} spaces", file=sys.stderr)

    # 下载附件（可选）
    if args.download_attachments:
        print(f"📎 下载附件到 {args.download_attachments}...", file=sys.stderr)
        n = download_space_attachments(chat, space_data, args.download_attachments)
        print(f"   已下载 {n} 个附件", file=sys.stderr)

    # 输出
    if args.format == "markdown":
        output = to_markdown(space_data)
    else:
        output = to_json(space_data)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"📄 Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
