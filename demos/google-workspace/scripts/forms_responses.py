"""
Google Forms 工具：读取 form 结构与回复。

用法：
    # 显示 form 结构（题目+选项）
    python3 forms_responses.py info <form_id_or_url>

    # 列出回复（默认 Markdown）
    python3 forms_responses.py responses <form_id_or_url>

    # JSON 输出
    python3 forms_responses.py responses <form_id_or_url> --format json

    # 写入文件
    python3 forms_responses.py responses <form_id_or_url> --output /tmp/responses.md

    # 限制条数
    python3 forms_responses.py responses <form_id_or_url> --limit 50
"""
import argparse
import json
import re
import sys
from datetime import datetime

from gw_client import get_forms_service


def extract_form_id(s: str) -> str:
    """从 URL 或裸 ID 中抽出 Form ID。"""
    m = re.search(r"/forms/d/(?:e/)?([a-zA-Z0-9_-]{20,})", s)
    if m:
        return m.group(1)
    return s.strip()


def get_form(form_id: str) -> dict:
    return get_forms_service().forms().get(formId=form_id).execute()


def list_responses(form_id: str, limit: int = None) -> list:
    """分页拉取所有回复。"""
    service = get_forms_service()
    out = []
    page_token = None
    while True:
        kwargs = {"formId": form_id, "pageSize": 5000}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = service.forms().responses().list(**kwargs).execute()
        out.extend(resp.get("responses", []))
        if limit and len(out) >= limit:
            return out[:limit]
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return out


def build_question_map(form: dict) -> dict:
    """questionId → {title, type, options}。"""
    qmap = {}
    for item in form.get("items", []):
        qi = item.get("questionItem", {}).get("question")
        if not qi:
            # group/grid 情况先简化处理
            continue
        qid = qi.get("questionId")
        title = item.get("title", "")
        qtype = "text"
        options = None
        if "choiceQuestion" in qi:
            cq = qi["choiceQuestion"]
            qtype = cq.get("type", "RADIO").lower()
            options = [o.get("value") for o in cq.get("options", [])]
        elif "scaleQuestion" in qi:
            qtype = "scale"
        elif "dateQuestion" in qi:
            qtype = "date"
        elif "fileUploadQuestion" in qi:
            qtype = "file"
        qmap[qid] = {"title": title, "type": qtype, "options": options}
    return qmap


def render_info(form: dict) -> str:
    info = form.get("info", {})
    lines = [f"# {info.get('title', '(untitled)')}"]
    if info.get("description"):
        lines.append("")
        lines.append(info["description"])
    lines.append("")
    lines.append(f"- Form ID: `{form.get('formId')}`")
    lines.append(f"- Responder URI: {form.get('responderUri', 'N/A')}")
    lines.append(f"- Linked Sheet: {form.get('linkedSheetId', 'N/A')}")
    lines.append("")
    lines.append("## Questions")
    qmap = build_question_map(form)
    for i, (qid, q) in enumerate(qmap.items(), 1):
        lines.append(f"\n### {i}. {q['title']}")
        lines.append(f"- Type: `{q['type']}`")
        lines.append(f"- ID: `{qid}`")
        if q["options"]:
            lines.append("- Options:")
            for opt in q["options"]:
                lines.append(f"  - {opt}")
    return "\n".join(lines)


def render_responses_md(form: dict, responses: list) -> str:
    qmap = build_question_map(form)
    info = form.get("info", {})
    lines = [f"# {info.get('title', '(untitled)')} — Responses"]
    lines.append(f"\nTotal: **{len(responses)}** responses\n")

    for r in responses:
        ts = r.get("createTime", "")[:19].replace("T", " ")
        rid = r.get("responseId", "")
        email = r.get("respondentEmail", "")
        header = f"## [{ts}] {email or rid}"
        lines.append(f"\n{header}")
        answers = r.get("answers", {})
        for qid, ans in answers.items():
            q = qmap.get(qid, {"title": qid})
            ta = ans.get("textAnswers", {}).get("answers", [])
            values = [a.get("value", "") for a in ta]
            file_uploads = ans.get("fileUploadAnswers", {}).get("answers", [])
            if file_uploads:
                values = [f"📎 {f.get('fileName', '')} ({f.get('fileId', '')})" for f in file_uploads]
            value_str = " / ".join(values) if values else "(empty)"
            lines.append(f"- **{q['title']}**: {value_str}")
    return "\n".join(lines)


def cmd_info(args):
    form_id = extract_form_id(args.form)
    form = get_form(form_id)
    if args.format == "json":
        out = json.dumps(form, indent=2, ensure_ascii=False)
    else:
        out = render_info(form)
    _write(out, args.output)


def cmd_responses(args):
    form_id = extract_form_id(args.form)
    form = get_form(form_id)
    responses = list_responses(form_id, limit=args.limit)
    if args.format == "json":
        out = json.dumps({
            "form": {"id": form.get("formId"), "title": form.get("info", {}).get("title")},
            "count": len(responses),
            "responses": responses,
        }, indent=2, ensure_ascii=False)
    else:
        out = render_responses_md(form, responses)
    _write(out, args.output)


def _write(content: str, output: str | None):
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 写入 {output} ({len(content)} chars)")
    else:
        print(content)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("info", help="显示 form 结构")
    pi.add_argument("form", help="Form ID 或 URL")
    pi.add_argument("--format", choices=["md", "json"], default="md")
    pi.add_argument("--output", help="输出到文件，省略则打印到 stdout")
    pi.set_defaults(func=cmd_info)

    pr = sub.add_parser("responses", help="列出回复")
    pr.add_argument("form", help="Form ID 或 URL")
    pr.add_argument("--limit", type=int, help="最多拉取多少条")
    pr.add_argument("--format", choices=["md", "json"], default="md")
    pr.add_argument("--output", help="输出到文件，省略则打印到 stdout")
    pr.set_defaults(func=cmd_responses)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
