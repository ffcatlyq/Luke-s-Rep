"""ASR 转写的 LLM 校对——修同音字、专名、明显误识、标点,不改语义。

通用:任何来源的 ASR 文本(bilibili / xiaohongshu / meeting / 微信语音)都能喂进来。
四渡赤水那类专名密集口播是典型场景(四都赤水→四渡赤水、遵义→钻翼、滇军→巅军)。

设计:
- 长文本按行边界分块(默认 ~2500 字/块),逐块过 Galileo chat,降低单次 token 压力、保质量。
- 上下文(标题/领域/术语表)放 **system prompt**,不混进正文,避免被模型当内容回显。
- 变更日志用字符级 difflib 在本地算(确定性,不靠模型自陈),只列真实替换,
  忽略换行/标点重排噪音——模型偶尔会把短行重排成通顺段落,不该算成"改动"。
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from .galileo import DEFAULT_CHAT_MODEL, chat_complete

_SYSTEM = """你是中文语音转写(ASR)校对员。用户消息是一段自动转写的文本,含同音字错误、\
专有名词误识、标点缺失。你的唯一任务是修正这些明显错误,输出校对后的文本。

铁律:
1. 只修「同音/近音误识、专有名词、明显错别字、缺失或错误的标点」。
2. 不改变原意,不润色,不增删内容,不翻译,不做摘要。
3. 尽量保持原有分行;若某行以时间戳前缀(形如 [12:34])开头,必须原样保留该前缀且不与相邻行合并。
4. 拿不准的地方保持原样,不要臆造。
5. 只输出校对后的文本本身,不要复述背景信息、不要任何解释、前后缀或代码块标记。"""

# 判断一处 diff 是否"实质"用的忽略字符集(纯换行/空白/标点重排不算改动)
_IGNORE = set(" \t\r\n。，、；：！？「」『』“”‘’()（）—…·.,;:!?\"'-")


@dataclass
class Change:
    before: str
    after: str


@dataclass
class CorrectionResult:
    corrected: str
    changes: list[Change] = field(default_factory=list)

    def change_log_md(self) -> str:
        if not self.changes:
            return "(无实质变更)"
        rows = ["| # | 原文 | 校对后 |", "|---|---|---|"]
        for i, c in enumerate(self.changes, 1):
            b = c.before.replace("|", "\\|").replace("\n", " ") or "(空)"
            a = c.after.replace("|", "\\|").replace("\n", " ") or "(删除)"
            rows.append(f"| {i} | {b} | {a} |")
        return "\n".join(rows)


def _build_context(title: str | None, domain: str | None, glossary: str | None) -> str:
    parts = []
    if title:
        parts.append(f"内容标题:{title}")
    if domain:
        parts.append(f"领域/主题:{domain}(该领域专名请按此背景校正)")
    if glossary:
        parts.append(f"术语表(出现即以下列写法为准):{glossary}")
    return "\n".join(parts)


def _system_prompt(context: str) -> str:
    if context:
        return _SYSTEM + "\n\n背景信息(仅供你校对时参考,不要输出这些行):\n" + context
    return _SYSTEM


def _chunks(text: str, chunk_chars: int) -> list[str]:
    """按行边界切块,每块不超过 chunk_chars(单行超长也自成一块)。"""
    out: list[str] = []
    cur: list[str] = []
    size = 0
    for line in text.split("\n"):
        if cur and size + len(line) + 1 > chunk_chars:
            out.append("\n".join(cur))
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    if cur:
        out.append("\n".join(cur))
    return out


def _correct_chunk(chunk: str, system: str, model: str) -> str:
    out = chat_complete(
        [{"role": "system", "content": system}, {"role": "user", "content": chunk}],
        model=model,
        temperature=0.0,
        max_tokens=min(8192, len(chunk) * 3 + 512),
    )
    out = out.strip()
    # 去掉模型偶尔套的代码块围栏
    if out.startswith("```"):
        out = out.split("\n", 1)[-1].rsplit("```", 1)[0].strip("\n")
    # 逐行去尾随空白(模型常给中文行补 markdown 换行用的尾空格)
    return "\n".join(line.rstrip() for line in out.split("\n"))


def _is_substantive(before: str, after: str) -> bool:
    """滤掉纯换行/空白/标点重排——把两边的忽略字符去掉后仍不同才算实质改动。"""
    b = "".join(ch for ch in before if ch not in _IGNORE)
    a = "".join(ch for ch in after if ch not in _IGNORE)
    return b != a and (b or a)


def _diff_changes(original: str, corrected: str) -> list[Change]:
    """字符级 diff,抽出真实替换/增删段(before→after),忽略重排噪音。

    比逐行 diff 稳:模型把短行重排成段落时,行级 diff 会整片误报,字符级只抓真正变的子串。
    """
    sm = difflib.SequenceMatcher(a=original, b=corrected, autojunk=False)
    changes: list[Change] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        before = original[i1:i2]
        after = corrected[j1:j2]
        if _is_substantive(before, after):
            changes.append(Change(before=before.strip(), after=after.strip()))
    return changes


def correct_transcript(
    text: str,
    *,
    title: str | None = None,
    domain: str | None = None,
    glossary: str | None = None,
    model: str = DEFAULT_CHAT_MODEL,
    chunk_chars: int = 2500,
) -> CorrectionResult:
    """校对整段 ASR 文本,返回 {corrected, changes}。"""
    system = _system_prompt(_build_context(title, domain, glossary))
    corrected_chunks = [_correct_chunk(c, system, model) for c in _chunks(text, chunk_chars)]
    corrected = "\n".join(corrected_chunks)
    changes = _diff_changes(text, corrected)
    return CorrectionResult(corrected=corrected, changes=changes)
