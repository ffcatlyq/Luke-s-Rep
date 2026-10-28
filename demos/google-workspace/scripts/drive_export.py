"""
Google Drive 文件夹遍历 + 文档内容提取工具。

用法：
    # 列出 Drive 根目录
    python3 drive_export.py list

    # 列出指定文件夹
    python3 drive_export.py list <folder_id>

    # 递归显示文件夹树（默认 3 层）
    python3 drive_export.py tree <folder_id> [--depth 5]

    # 导出单个文件内容
    python3 drive_export.py export <file_id>

    # 批量导出文件夹下所有文档到本地目录
    python3 drive_export.py batch <folder_id> [--output ./export] [--depth 3]

支持的文件类型：
    - Google Docs → Markdown（通过纯文本导出）
    - Google Sheets → JSON（每个 sheet 的二维数组）
    - Google Slides → 逐页文本
    - 纯文本/Markdown/CSV/JSON → 原始内容
    - 其他（PDF、图片等）→ 仅输出元信息
"""
import argparse
import json
import os
import sys

from gw_client import get_drive_service, get_docs_service, get_sheets_service

# Google Workspace MIME 类型映射
MIME_GOOGLE_DOC = "application/vnd.google-apps.document"
MIME_GOOGLE_SHEET = "application/vnd.google-apps.spreadsheet"
MIME_GOOGLE_SLIDES = "application/vnd.google-apps.presentation"
MIME_GOOGLE_FOLDER = "application/vnd.google-apps.folder"

# 可直接下载的文本类型
TEXT_MIMES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/html",
    "application/json",
    "application/xml",
}


def list_files(folder_id="root"):
    """列出文件夹下的文件和子文件夹。"""
    drive = get_drive_service()
    query = f"'{folder_id}' in parents and trashed = false"
    results = (
        drive.files()
        .list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, modifiedTime, size)",
            orderBy="folder,name",
        )
        .execute()
    )
    files = results.get("files", [])

    if not files:
        print("（空文件夹）")
        return files

    for f in files:
        icon = "📁" if f["mimeType"] == MIME_GOOGLE_FOLDER else "📄"
        size = f.get("size", "")
        size_str = f"  ({_human_size(int(size))})" if size else ""
        print(f"  {icon} {f['name']}{size_str}")
        print(f"     ID: {f['id']}  Type: {f['mimeType']}")

    print(f"\n共 {len(files)} 个项目")
    return files


def tree(folder_id="root", depth=3, prefix="", current_depth=0):
    """递归显示文件夹树。"""
    if current_depth >= depth:
        return

    drive = get_drive_service()
    query = f"'{folder_id}' in parents and trashed = false"
    results = (
        drive.files()
        .list(
            q=query,
            pageSize=200,
            fields="files(id, name, mimeType)",
            orderBy="folder,name",
        )
        .execute()
    )
    files = results.get("files", [])

    for i, f in enumerate(files):
        is_last = i == len(files) - 1
        connector = "└── " if is_last else "├── "
        icon = "📁" if f["mimeType"] == MIME_GOOGLE_FOLDER else "📄"
        print(f"{prefix}{connector}{icon} {f['name']}")

        if f["mimeType"] == MIME_GOOGLE_FOLDER:
            extension = "    " if is_last else "│   "
            tree(f["id"], depth, prefix + extension, current_depth + 1)


def export_file(file_id, quiet=False):
    """导出单个文件的内容，返回 (filename, content, mime_type)。"""
    drive = get_drive_service()
    meta = drive.files().get(fileId=file_id, fields="id,name,mimeType").execute()
    name = meta["name"]
    mime = meta["mimeType"]

    if mime == MIME_GOOGLE_DOC:
        content = _export_google_doc(file_id)
    elif mime == MIME_GOOGLE_SHEET:
        content = _export_google_sheet(file_id, name)
    elif mime == MIME_GOOGLE_SLIDES:
        content = _export_google_slides(file_id)
    elif mime in TEXT_MIMES or mime.startswith("text/"):
        content = drive.files().get_media(fileId=file_id).execute().decode("utf-8")
    else:
        content = f"[不支持的文件类型: {mime}]\n文件名: {name}\nID: {file_id}"

    if not quiet:
        print(f"--- {name} ({mime}) ---")
        print(content)
        print()

    return name, content, mime


def _export_google_doc(file_id):
    """导出 Google Docs 为纯文本。"""
    drive = get_drive_service()
    return (
        drive.files()
        .export(fileId=file_id, mimeType="text/plain")
        .execute()
        .decode("utf-8")
    )


def _export_google_sheet(file_id, name):
    """导出 Google Sheets 为 JSON。"""
    sheets = get_sheets_service()
    meta = sheets.spreadsheets().get(spreadsheetId=file_id).execute()
    sheet_names = [s["properties"]["title"] for s in meta.get("sheets", [])]

    result = {}
    for sheet_name in sheet_names:
        data = (
            sheets.spreadsheets()
            .values()
            .get(spreadsheetId=file_id, range=sheet_name)
            .execute()
        )
        result[sheet_name] = data.get("values", [])

    return json.dumps(result, ensure_ascii=False, indent=2)


def _export_google_slides(file_id):
    """导出 Google Slides 为逐页文本。"""
    drive = get_drive_service()
    return (
        drive.files()
        .export(fileId=file_id, mimeType="text/plain")
        .execute()
        .decode("utf-8")
    )


def batch_export(folder_id, output_dir="./export", depth=3, current_depth=0, rel_path=""):
    """批量导出文件夹下所有文档到本地目录。"""
    if current_depth >= depth:
        return

    os.makedirs(os.path.join(output_dir, rel_path), exist_ok=True)

    drive = get_drive_service()
    query = f"'{folder_id}' in parents and trashed = false"
    results = (
        drive.files()
        .list(
            q=query,
            pageSize=200,
            fields="files(id, name, mimeType)",
            orderBy="folder,name",
        )
        .execute()
    )
    files = results.get("files", [])
    exported = 0

    for f in files:
        if f["mimeType"] == MIME_GOOGLE_FOLDER:
            sub_path = os.path.join(rel_path, _safe_filename(f["name"]))
            batch_export(f["id"], output_dir, depth, current_depth + 1, sub_path)
            continue

        try:
            name, content, mime = export_file(f["id"], quiet=True)
            ext = _get_extension(mime)
            safe_name = _safe_filename(name)
            if not safe_name.endswith(ext):
                safe_name += ext
            filepath = os.path.join(output_dir, rel_path, safe_name)
            with open(filepath, "w", encoding="utf-8") as out:
                out.write(content)
            print(f"  ✅ {os.path.join(rel_path, safe_name)}")
            exported += 1
        except Exception as e:
            print(f"  ❌ {f['name']}: {e}")

    if current_depth == 0:
        print(f"\n共导出 {exported} 个文件到 {output_dir}")


def _safe_filename(name):
    """将文件名中的特殊字符替换为下划线。"""
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, '_')
    return name


def _get_extension(mime):
    """根据 MIME 类型返回文件扩展名。"""
    ext_map = {
        MIME_GOOGLE_DOC: ".txt",
        MIME_GOOGLE_SHEET: ".json",
        MIME_GOOGLE_SLIDES: ".txt",
        "text/plain": ".txt",
        "text/markdown": ".md",
        "text/csv": ".csv",
        "text/html": ".html",
        "application/json": ".json",
    }
    return ext_map.get(mime, ".txt")


def _human_size(size_bytes):
    """将字节数转为人类可读格式。"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.0f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def main():
    parser = argparse.ArgumentParser(description="Google Drive 文件遍历与导出工具")
    sub = parser.add_subparsers(dest="command")

    # list
    p_list = sub.add_parser("list", help="列出文件夹下的文件")
    p_list.add_argument("folder_id", nargs="?", default="root")

    # tree
    p_tree = sub.add_parser("tree", help="递归显示文件夹树")
    p_tree.add_argument("folder_id", nargs="?", default="root")
    p_tree.add_argument("--depth", type=int, default=3)

    # export
    p_export = sub.add_parser("export", help="导出单个文件内容")
    p_export.add_argument("file_id")

    # batch
    p_batch = sub.add_parser("batch", help="批量导出文件夹下所有文档")
    p_batch.add_argument("folder_id")
    p_batch.add_argument("--output", default="./export")
    p_batch.add_argument("--depth", type=int, default=3)

    args = parser.parse_args()

    if args.command == "list":
        list_files(args.folder_id)
    elif args.command == "tree":
        print(f"📁 (root: {args.folder_id})")
        tree(args.folder_id, args.depth)
    elif args.command == "export":
        export_file(args.file_id)
    elif args.command == "batch":
        batch_export(args.folder_id, args.output, args.depth)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
