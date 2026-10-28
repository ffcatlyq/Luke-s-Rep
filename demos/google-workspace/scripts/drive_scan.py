"""
Google Drive 全量扫描 + 治理分析工具。

用法：
    # 全量扫描并保存元信息
    python3 drive_scan.py scan

    # 基于扫描结果生成治理报告
    python3 drive_scan.py report

扫描结果保存在 /tmp/drive_scan.json，报告输出到 /tmp/drive_report.md。
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

from gw_client import get_drive_service

SCAN_PATH = "/tmp/drive_scan.json"
REPORT_PATH = "/tmp/drive_report.md"

# Google Workspace 原生类型（无 size 字段，不占存储配额）
GOOGLE_NATIVE_TYPES = {
    "application/vnd.google-apps.document",
    "application/vnd.google-apps.spreadsheet",
    "application/vnd.google-apps.presentation",
    "application/vnd.google-apps.form",
    "application/vnd.google-apps.drawing",
    "application/vnd.google-apps.script",
    "application/vnd.google-apps.site",
    "application/vnd.google-apps.map",
    "application/vnd.google-apps.jam",
}

SKIP_TYPES = {
    "application/vnd.google-apps.folder",
    "application/vnd.google-apps.shortcut",
}


def scan_all_files():
    """全量扫描 Drive，采集所有文件的元信息。"""
    drive = get_drive_service()
    all_files = []
    page_token = None
    page = 0

    print("开始全量扫描 Google Drive...")

    while True:
        page += 1
        results = drive.files().list(
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType, size, "
                   "modifiedTime, createdTime, parents, trashed, "
                   "shared, ownedByMe, md5Checksum)",
            q="trashed = false",
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        files = results.get("files", [])
        all_files.extend(files)
        print(f"  第 {page} 页: +{len(files)} 个文件（累计 {len(all_files)}）")

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    # 构建文件夹路径映射
    print("构建文件夹路径映射...")
    folder_map = {}
    for f in all_files:
        if f["mimeType"] == "application/vnd.google-apps.folder":
            folder_map[f["id"]] = f

    def get_path(file_obj, depth=0):
        if depth > 20:
            return "..."
        parents = file_obj.get("parents", [])
        if not parents:
            return ""
        parent_id = parents[0]
        if parent_id in folder_map:
            parent_path = get_path(folder_map[parent_id], depth + 1)
            return f"{parent_path}/{folder_map[parent_id]['name']}"
        return ""

    # 为每个文件添加路径
    for f in all_files:
        f["path"] = get_path(f)

    scan_data = {
        "scan_time": datetime.now().isoformat(),
        "total_files": len(all_files),
        "files": all_files,
    }

    with open(SCAN_PATH, "w", encoding="utf-8") as out:
        json.dump(scan_data, out, ensure_ascii=False, indent=2)

    print(f"\n✅ 扫描完成: {len(all_files)} 个文件")
    print(f"   结果保存到 {SCAN_PATH}")
    return scan_data


def load_scan():
    """加载扫描结果。"""
    if not os.path.exists(SCAN_PATH):
        print(f"❌ 扫描结果不存在: {SCAN_PATH}")
        print("请先运行: python3 drive_scan.py scan")
        sys.exit(1)
    with open(SCAN_PATH, encoding="utf-8") as f:
        return json.load(f)


def generate_report():
    """基于扫描结果生成治理报告。"""
    data = load_scan()
    files = data["files"]
    scan_time = data["scan_time"]

    # 过滤掉文件夹和快捷方式
    real_files = [f for f in files if f["mimeType"] not in SKIP_TYPES]
    folders = [f for f in files if f["mimeType"] == "application/vnd.google-apps.folder"]

    lines = []
    lines.append("# Google Drive 治理报告")
    lines.append("")
    lines.append(f"> 扫描时间: {scan_time}")
    lines.append(f"> 总项目数: {len(files)}（文件 {len(real_files)} + 文件夹 {len(folders)}）")
    lines.append("")

    # === 1. 存储占用分析 ===
    lines.append("## 1. 存储占用分析")
    lines.append("")

    # 按类型统计
    type_stats = defaultdict(lambda: {"count": 0, "size": 0})
    for f in real_files:
        mime = f["mimeType"]
        size = int(f.get("size", 0))
        type_stats[mime]["count"] += 1
        type_stats[mime]["size"] += size

    # 按大小排序
    sorted_types = sorted(type_stats.items(), key=lambda x: -x[1]["size"])

    lines.append("### 按文件类型")
    lines.append("")
    lines.append("| 类型 | 数量 | 大小 | 占比 |")
    lines.append("|------|------|------|------|")

    total_size = sum(s["size"] for s in type_stats.values())
    for mime, stats in sorted_types:
        pct = (stats["size"] / total_size * 100) if total_size > 0 else 0
        lines.append(
            f"| {_short_mime(mime)} | {stats['count']} | "
            f"{_human_size(stats['size'])} | {pct:.1f}% |"
        )

    # Google 原生文件不占配额
    native_count = sum(1 for f in real_files if f["mimeType"] in GOOGLE_NATIVE_TYPES)
    lines.append("")
    lines.append(f"**实际占用存储配额**: {_human_size(total_size)}")
    lines.append(f"（Google 原生文件 {native_count} 个不占配额）")
    lines.append("")

    # === 2. 大文件 TOP 20 ===
    lines.append("## 2. 大文件 TOP 20")
    lines.append("")
    lines.append("| 文件名 | 大小 | 类型 | 路径 | 最后修改 |")
    lines.append("|--------|------|------|------|----------|")

    big_files = sorted(real_files, key=lambda f: -int(f.get("size", 0)))[:20]
    for f in big_files:
        name = f["name"][:50]
        size = _human_size(int(f.get("size", 0)))
        mime = _short_mime(f["mimeType"])
        path = f.get("path", "")[:40]
        modified = f.get("modifiedTime", "")[:10]
        lines.append(f"| {name} | {size} | {mime} | {path} | {modified} |")

    lines.append("")

    # === 3. 重复文件检测 ===
    lines.append("## 3. 重复文件检测")
    lines.append("")

    # 3a. MD5 完全重复
    md5_groups = defaultdict(list)
    for f in real_files:
        md5 = f.get("md5Checksum")
        if md5:
            md5_groups[md5].append(f)

    md5_dupes = {k: v for k, v in md5_groups.items() if len(v) > 1}

    if md5_dupes:
        lines.append(f"### 内容完全相同（MD5 匹配）: {len(md5_dupes)} 组")
        lines.append("")
        lines.append("| 文件名 | 大小 | 路径 | 副本数 |")
        lines.append("|--------|------|------|--------|")

        wasted = 0
        for md5, group in sorted(md5_dupes.items(), key=lambda x: -int(x[1][0].get("size", 0))):
            size = int(group[0].get("size", 0))
            wasted += size * (len(group) - 1)
            names = set(f["name"] for f in group)
            paths = [f.get("path", "") for f in group]
            lines.append(
                f"| {', '.join(names)[:50]} | {_human_size(size)} | "
                f"{'; '.join(p[:30] for p in paths)} | {len(group)} |"
            )

        lines.append("")
        lines.append(f"**重复文件浪费存储**: {_human_size(wasted)}")
    else:
        lines.append("未检测到 MD5 完全重复的文件。")

    lines.append("")

    # 3b. 同名文件
    name_groups = defaultdict(list)
    for f in real_files:
        name_groups[f["name"]].append(f)

    name_dupes = {k: v for k, v in name_groups.items() if len(v) > 1}

    if name_dupes:
        lines.append(f"### 同名文件: {len(name_dupes)} 组")
        lines.append("")
        lines.append("| 文件名 | 副本数 | 类型 | 路径 |")
        lines.append("|--------|--------|------|------|")

        for name, group in sorted(name_dupes.items(), key=lambda x: -len(x[1]))[:30]:
            types = set(_short_mime(f["mimeType"]) for f in group)
            paths = [f.get("path", "")[:30] for f in group]
            lines.append(
                f"| {name[:50]} | {len(group)} | "
                f"{', '.join(types)} | {'; '.join(paths)} |"
            )

    lines.append("")

    # === 4. 按文件夹统计 ===
    lines.append("## 4. 按文件夹统计")
    lines.append("")

    folder_stats = defaultdict(lambda: {"count": 0, "size": 0})
    for f in real_files:
        path = f.get("path", "")
        # 取第一级文件夹
        parts = path.strip("/").split("/")
        top_folder = parts[0] if parts[0] else "(根目录)"
        folder_stats[top_folder]["count"] += 1
        folder_stats[top_folder]["size"] += int(f.get("size", 0))

    lines.append("| 文件夹 | 文件数 | 大小 |")
    lines.append("|--------|--------|------|")

    for folder, stats in sorted(folder_stats.items(), key=lambda x: -x[1]["size"]):
        lines.append(
            f"| {folder} | {stats['count']} | {_human_size(stats['size'])} |"
        )

    lines.append("")

    # === 5. 时间分布 ===
    lines.append("## 5. 文件活跃度分析")
    lines.append("")

    now = datetime.now()
    age_buckets = {"<30天": 0, "1-6个月": 0, "6-12个月": 0, "1-2年": 0, ">2年": 0}

    for f in real_files:
        modified = f.get("modifiedTime", "")
        if not modified:
            age_buckets[">2年"] += 1
            continue
        try:
            mod_date = datetime.fromisoformat(modified.replace("Z", "+00:00")).replace(tzinfo=None)
            days = (now - mod_date).days
            if days < 30:
                age_buckets["<30天"] += 1
            elif days < 180:
                age_buckets["1-6个月"] += 1
            elif days < 365:
                age_buckets["6-12个月"] += 1
            elif days < 730:
                age_buckets["1-2年"] += 1
            else:
                age_buckets[">2年"] += 1
        except (ValueError, TypeError):
            age_buckets[">2年"] += 1

    lines.append("| 最后修改时间 | 文件数 | 占比 |")
    lines.append("|-------------|--------|------|")

    for bucket, count in age_buckets.items():
        pct = count / len(real_files) * 100 if real_files else 0
        lines.append(f"| {bucket} | {count} | {pct:.1f}% |")

    lines.append("")

    # === 6. 迁移建议 ===
    lines.append("## 6. 迁移建议")
    lines.append("")
    lines.append("### 分类标准")
    lines.append("")
    lines.append("| 分类 | 标准 | 建议操作 |")
    lines.append("|------|------|----------|")
    lines.append("| 活跃 | 近 6 个月修改过 | 迁移到 OneDrive |")
    lines.append("| 归档 | 6 个月-2 年未修改 | 迁移到 OneDrive 归档文件夹 |")
    lines.append("| 冷数据 | 超过 2 年未修改 | 评估后决定删除或归档 |")
    lines.append("| 重复 | MD5 相同的副本 | 保留一份，删除其余 |")
    lines.append("| 自动生成 | Meet Recordings/Transcript、Chrome 保存 | 评估后批量删除 |")
    lines.append("")

    active = age_buckets["<30天"] + age_buckets["1-6个月"]
    archive = age_buckets["6-12个月"] + age_buckets["1-2年"]
    cold = age_buckets[">2年"]

    lines.append(f"### 预估分布")
    lines.append("")
    lines.append(f"- **活跃文件**: {active} 个（{active/len(real_files)*100:.0f}%）→ 迁移")
    lines.append(f"- **归档文件**: {archive} 个（{archive/len(real_files)*100:.0f}%）→ 归档或删除")
    lines.append(f"- **冷数据**: {cold} 个（{cold/len(real_files)*100:.0f}%）→ 评估删除")
    if md5_dupes:
        lines.append(f"- **重复文件**: {sum(len(g) - 1 for g in md5_dupes.values())} 个副本 → 删除")
    lines.append("")

    report = "\n".join(lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as out:
        out.write(report)

    print(f"✅ 报告已生成: {REPORT_PATH}")
    print(f"   文件总数: {len(real_files)}")
    print(f"   存储占用: {_human_size(total_size)}")
    if md5_dupes:
        print(f"   重复文件组: {len(md5_dupes)}")
    print(f"   活跃文件: {active} | 归档: {archive} | 冷数据: {cold}")

    return report


def _short_mime(mime):
    """缩短 MIME 类型显示。"""
    short = {
        "application/vnd.google-apps.document": "Google Doc",
        "application/vnd.google-apps.spreadsheet": "Google Sheet",
        "application/vnd.google-apps.presentation": "Google Slides",
        "application/vnd.google-apps.form": "Google Form",
        "application/vnd.google-apps.script": "Apps Script",
        "application/vnd.google-apps.drawing": "Google Drawing",
        "application/vnd.google-apps.site": "Google Site",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
        "application/msword": "Word (旧)",
        "application/vnd.ms-powerpoint": "PPT (旧)",
        "application/pdf": "PDF",
        "application/zip": "ZIP",
        "application/json": "JSON",
        "application/octet-stream": "二进制",
        "text/plain": "文本",
        "text/csv": "CSV",
        "text/markdown": "Markdown",
        "text/html": "HTML",
        "text/x-sql": "SQL",
        "image/png": "PNG",
        "image/jpeg": "JPEG",
        "video/mp4": "MP4",
        "video/quicktime": "MOV",
    }
    return short.get(mime, mime.split("/")[-1][:20])


def _human_size(size_bytes):
    """将字节数转为人类可读格式。"""
    if size_bytes == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(description="Google Drive 全量扫描与治理分析")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scan", help="全量扫描 Drive 文件元信息")
    sub.add_parser("report", help="基于扫描结果生成治理报告")

    args = parser.parse_args()

    if args.command == "scan":
        scan_all_files()
    elif args.command == "report":
        generate_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
