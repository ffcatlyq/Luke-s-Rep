"""
Google Drive 批量清理工具。

基于 drive_scan.py 的扫描结果，按规则筛选待清理文件，
支持 dry-run 预览和实际执行两种模式。

用法：
    # 预览：列出 MD5 重复文件的副本（保留最早创建的那份）
    python3 drive_cleanup.py duplicates

    # 执行：移入回收站（可从回收站恢复）
    python3 drive_cleanup.py duplicates --execute

    # 预览：列出指定文件夹下所有文件
    python3 drive_cleanup.py folder <folder_name>

    # 执行：移入回收站
    python3 drive_cleanup.py folder <folder_name> --execute

    # 预览：列出超过指定大小的文件
    python3 drive_cleanup.py big --min-size 500MB

    # 预览：列出超过 N 天未修改的文件
    python3 drive_cleanup.py stale --days 730

安全机制：
    - 默认 dry-run，只列出不操作
    - --execute 模式将文件移入回收站（trash），不是永久删除
    - 回收站中的文件 30 天后自动永久删除，期间可手动恢复
    - 每次操作生成日志文件 /tmp/drive_cleanup_<timestamp>.log
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

from gw_client import get_drive_service

SCAN_PATH = "/tmp/drive_scan.json"


def load_scan():
    if not os.path.exists(SCAN_PATH):
        print(f"❌ 扫描结果不存在: {SCAN_PATH}")
        print("请先运行: python3 drive_scan.py scan")
        sys.exit(1)
    with open(SCAN_PATH, encoding="utf-8") as f:
        return json.load(f)


def _human_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _parse_size(size_str):
    """解析人类可读的大小字符串为字节数。"""
    size_str = size_str.strip().upper()
    # 长后缀优先匹配
    for suffix, mult in [("GB", 1024**3), ("MB", 1024**2), ("KB", 1024), ("B", 1)]:
        if size_str.endswith(suffix):
            return int(float(size_str[:-len(suffix)]) * mult)
    return int(size_str)


def _trash_files(file_ids, execute=False):
    """将文件移入回收站。返回成功数。"""
    if not execute:
        return 0

    drive = get_drive_service()
    success = 0
    errors = 0

    for i, fid in enumerate(file_ids):
        try:
            drive.files().update(fileId=fid, body={"trashed": True}).execute()
            success += 1
            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{len(file_ids)}", flush=True)
        except Exception as e:
            errors += 1
            print(f"  ❌ {fid}: {e}")

    return success


def _write_log(action, files, execute):
    """写操作日志。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"/tmp/drive_cleanup_{ts}.log"
    mode = "EXECUTE" if execute else "DRY-RUN"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# Drive Cleanup Log — {mode}\n")
        f.write(f"# Action: {action}\n")
        f.write(f"# Time: {datetime.now().isoformat()}\n")
        f.write(f"# Files: {len(files)}\n\n")
        for file in files:
            f.write(f"{file['id']}\t{file['name']}\t{file.get('path', '')}\n")

    print(f"  日志: {log_path}")


def cmd_duplicates(args):
    """清理 MD5 重复文件，保留每组中最早创建的那份。"""
    data = load_scan()
    files = data["files"]

    # 过滤掉文件夹和快捷方式
    skip = {"application/vnd.google-apps.folder", "application/vnd.google-apps.shortcut"}
    real_files = [f for f in files if f["mimeType"] not in skip]

    # 按 MD5 分组
    md5_groups = defaultdict(list)
    for f in real_files:
        md5 = f.get("md5Checksum")
        if md5:
            md5_groups[md5].append(f)

    dupes = {k: v for k, v in md5_groups.items() if len(v) > 1}

    to_delete = []
    total_saved = 0

    for md5, group in sorted(dupes.items(), key=lambda x: -int(x[1][0].get("size", 0))):
        # 保留最早创建的
        group.sort(key=lambda f: f.get("createdTime", f.get("modifiedTime", "")))
        keep = group[0]
        remove = group[1:]
        size = int(keep.get("size", 0))
        total_saved += size * len(remove)
        to_delete.extend(remove)

    print(f"MD5 重复文件分析:")
    print(f"  重复组数: {len(dupes)}")
    print(f"  待删除副本: {len(to_delete)}")
    print(f"  可释放空间: {_human_size(total_saved)}")
    print()

    if not to_delete:
        print("没有需要清理的重复文件。")
        return

    # 显示 TOP 20
    print("TOP 20 最大重复文件:")
    shown = []
    seen_md5 = set()
    for f in sorted(to_delete, key=lambda x: -int(x.get("size", 0))):
        md5 = f.get("md5Checksum")
        if md5 not in seen_md5:
            seen_md5.add(md5)
            shown.append(f)
            if len(shown) >= 20:
                break

    for f in shown:
        size = _human_size(int(f.get("size", 0)))
        print(f"  {size:>10}  {f['name'][:60]}  {f.get('path', '')[:40]}")

    print()
    _write_log("duplicates", to_delete, args.execute)

    if args.execute:
        print(f"开始移入回收站（{len(to_delete)} 个文件）...")
        success = _trash_files([f["id"] for f in to_delete], execute=True)
        print(f"\n✅ 完成: {success} 个文件已移入回收站")
        print("  可在 Google Drive 回收站中恢复（30 天内）")
    else:
        print(f"⚠️  DRY-RUN 模式，未执行任何操作。")
        print(f"   添加 --execute 参数执行清理。")


def cmd_folder(args):
    """清理指定文件夹下的所有文件。"""
    data = load_scan()
    files = data["files"]

    folder_name = args.folder_name
    matched = [
        f for f in files
        if f.get("path", "").startswith(f"/{folder_name}")
        and f["mimeType"] != "application/vnd.google-apps.folder"
        and f["mimeType"] != "application/vnd.google-apps.shortcut"
    ]

    total_size = sum(int(f.get("size", 0)) for f in matched)

    print(f"文件夹 '{folder_name}' 分析:")
    print(f"  文件数: {len(matched)}")
    print(f"  总大小: {_human_size(total_size)}")
    print()

    if not matched:
        print("未找到匹配的文件。")
        return

    _write_log(f"folder:{folder_name}", matched, args.execute)

    if args.execute:
        print(f"开始移入回收站（{len(matched)} 个文件）...")
        success = _trash_files([f["id"] for f in matched], execute=True)
        print(f"\n✅ 完成: {success} 个文件已移入回收站")
    else:
        print(f"⚠️  DRY-RUN 模式，未执行任何操作。")
        print(f"   添加 --execute 参数执行清理。")


def cmd_big(args):
    """列出超过指定大小的文件。"""
    data = load_scan()
    files = data["files"]

    min_size = _parse_size(args.min_size)
    skip = {"application/vnd.google-apps.folder", "application/vnd.google-apps.shortcut"}

    big_files = [
        f for f in files
        if f["mimeType"] not in skip
        and int(f.get("size", 0)) >= min_size
    ]
    big_files.sort(key=lambda f: -int(f.get("size", 0)))

    total_size = sum(int(f.get("size", 0)) for f in big_files)

    print(f"大文件分析（>= {args.min_size}）:")
    print(f"  文件数: {len(big_files)}")
    print(f"  总大小: {_human_size(total_size)}")
    print()

    for f in big_files[:30]:
        size = _human_size(int(f.get("size", 0)))
        modified = f.get("modifiedTime", "")[:10]
        print(f"  {size:>10}  {modified}  {f['name'][:50]}  {f.get('path', '')[:30]}")

    if len(big_files) > 30:
        print(f"  ...（还有 {len(big_files) - 30} 个文件）")

    print()
    _write_log(f"big:{args.min_size}", big_files, args.execute)

    if args.execute:
        print(f"开始移入回收站（{len(big_files)} 个文件）...")
        success = _trash_files([f["id"] for f in big_files], execute=True)
        print(f"\n✅ 完成: {success} 个文件已移入回收站")
    else:
        print(f"⚠️  DRY-RUN 模式，未执行任何操作。")


def cmd_stale(args):
    """列出超过 N 天未修改的文件。"""
    data = load_scan()
    files = data["files"]

    now = datetime.now()
    skip = {"application/vnd.google-apps.folder", "application/vnd.google-apps.shortcut"}

    stale = []
    for f in files:
        if f["mimeType"] in skip:
            continue
        modified = f.get("modifiedTime", "")
        if not modified:
            stale.append(f)
            continue
        try:
            mod_date = datetime.fromisoformat(modified.replace("Z", "+00:00")).replace(tzinfo=None)
            if (now - mod_date).days >= args.days:
                stale.append(f)
        except (ValueError, TypeError):
            stale.append(f)

    total_size = sum(int(f.get("size", 0)) for f in stale)

    print(f"过期文件分析（>= {args.days} 天未修改）:")
    print(f"  文件数: {len(stale)}")
    print(f"  总大小: {_human_size(total_size)}")
    print()

    _write_log(f"stale:{args.days}d", stale, args.execute)

    if args.execute:
        print(f"开始移入回收站（{len(stale)} 个文件）...")
        success = _trash_files([f["id"] for f in stale], execute=True)
        print(f"\n✅ 完成: {success} 个文件已移入回收站")
    else:
        print(f"⚠️  DRY-RUN 模式，未执行任何操作。")


def main():
    parser = argparse.ArgumentParser(description="Google Drive 批量清理工具")
    sub = parser.add_subparsers(dest="command")

    p_dup = sub.add_parser("duplicates", help="清理 MD5 重复文件副本")
    p_dup.add_argument("--execute", action="store_true", help="实际执行（移入回收站）")

    p_folder = sub.add_parser("folder", help="清理指定文件夹")
    p_folder.add_argument("folder_name", help="文件夹名称（匹配路径前缀）")
    p_folder.add_argument("--execute", action="store_true")

    p_big = sub.add_parser("big", help="清理大文件")
    p_big.add_argument("--min-size", default="500MB", help="最小文件大小（默认 500MB）")
    p_big.add_argument("--execute", action="store_true")

    p_stale = sub.add_parser("stale", help="清理长期未修改的文件")
    p_stale.add_argument("--days", type=int, default=730, help="未修改天数阈值（默认 730）")
    p_stale.add_argument("--execute", action="store_true")

    args = parser.parse_args()

    if args.command == "duplicates":
        cmd_duplicates(args)
    elif args.command == "folder":
        cmd_folder(args)
    elif args.command == "big":
        cmd_big(args)
    elif args.command == "stale":
        cmd_stale(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
