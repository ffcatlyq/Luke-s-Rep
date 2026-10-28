"""Galileo(Portkey 后端)薄客户端——转写场景需要的两个面:chat 与 audio。

零 SDK 依赖(纯 urllib),与 demos/portkey/scripts/portkey_client.py 同风格。认证
统一走 `x-portkey-api-key` 头(不是 bearer),与 demos/data-agent/lib/llm.py 同门。
这里单列一份是因为「音频转写(multipart /audio/transcriptions)」这一面前两者都没有。

env:
  GALILEO_ENDPOINT       网关地址,默认 US(https://us.aigw.galileo.roche.com/v1)
  GALILEO_AZURE_API_KEY  Azure provider key(chat 校对默认用它——2026-07 实测 gpt-4o 通)
  GALILEO_BEDROCK_API_KEY / GALILEO_GCP_API_KEY  其它 provider,按需

实测(2026-07-08):chat 可用;/audio/transcriptions 上 whisper-001 / gpt-4o-transcribe*
返 DeploymentNotFound——STT 模型在目录里但**未在本 workspace 部署**。故 transcribe_audio()
命中未部署会抛 GalileoSTTNotProvisioned,带申请指引;chat_complete() 今天即可用。
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid

DEFAULT_ENDPOINT = "https://us.aigw.galileo.roche.com/v1"
# chat 校对默认模型:本会话实测通过的 Azure 部署
DEFAULT_CHAT_MODEL = "gpt-4o-2024-11-20"
# STT 首选(开通后即用);未部署时 transcribe_audio 会抛清晰错误
DEFAULT_STT_MODEL = "gpt-4o-transcribe"


class GalileoError(RuntimeError):
    """Galileo 调用的一般性错误(HTTP 非 2xx、网关不可达等)。"""


class GalileoSTTNotProvisioned(GalileoError):
    """Galileo 目录里有 STT 模型,但当前 workspace/虚拟 key 上未部署。

    这不是代码 bug——需要 Galileo 团队在 workspace 部署一个转写 deployment
    (whisper / gpt-4o-transcribe),开通后 transcribe_audio 直接生效。
    申请路径见 demos/transcribe/README.md「Galileo STT 开通」节。
    """


def _endpoint() -> str:
    return os.environ.get("GALILEO_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")


def _key(provider: str = "azure") -> str:
    env = {
        "azure": "GALILEO_AZURE_API_KEY",
        "bedrock": "GALILEO_BEDROCK_API_KEY",
        "gcp": "GALILEO_GCP_API_KEY",
    }.get(provider, "GALILEO_AZURE_API_KEY")
    k = os.environ.get(env)
    if not k:
        raise GalileoError(
            f"{env} 未设置。需连 RCN + 从 Portkey 控制台取 key,"
            "见 docs/guide/galileo-gateway-guide.md"
        )
    return k


def chat_complete(
    messages: list[dict],
    *,
    model: str = DEFAULT_CHAT_MODEL,
    provider: str = "azure",
    temperature: float = 0.0,
    max_tokens: int = 4096,
    timeout: int = 120,
) -> str:
    """调 /chat/completions,返回首条 message 的文本内容。"""
    url = f"{_endpoint()}/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "x-portkey-api-key": _key(provider),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise GalileoError(f"chat HTTP {e.code}: {e.read().decode()[:400]}") from e
    except urllib.error.URLError as e:
        raise GalileoError(f"网关不可达(需连 RCN):{e}") from e
    return data["choices"][0]["message"]["content"] or ""


def _multipart(fields: dict[str, str], file_field: str, file_path: str) -> tuple[bytes, str]:
    """手搓 multipart/form-data(避免引 requests 依赖)。返回 (body, content_type)。"""
    boundary = f"----galileo{uuid.uuid4().hex}"
    crlf = b"\r\n"
    buf = bytearray()
    for name, value in fields.items():
        buf += b"--" + boundary.encode() + crlf
        buf += f'Content-Disposition: form-data; name="{name}"'.encode() + crlf + crlf
        buf += str(value).encode() + crlf
    with open(file_path, "rb") as f:
        payload = f.read()
    filename = os.path.basename(file_path)
    buf += b"--" + boundary.encode() + crlf
    buf += (
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"'.encode()
        + crlf
    )
    buf += b"Content-Type: application/octet-stream" + crlf + crlf
    buf += payload + crlf
    buf += b"--" + boundary.encode() + b"--" + crlf
    return bytes(buf), f"multipart/form-data; boundary={boundary}"


def transcribe_audio(
    audio_path: str,
    *,
    model: str = DEFAULT_STT_MODEL,
    provider: str = "azure",
    language: str | None = "zh",
    timeout: int = 300,
) -> str:
    """调 /audio/transcriptions 转写音频文件,返回文本。

    未部署时抛 GalileoSTTNotProvisioned(带申请指引),调用方可据此降级到本地 ASR。
    Whisper API 单文件上限 25MB;更长音频调用方需先切分。
    """
    url = f"{_endpoint()}/audio/transcriptions"
    fields = {"model": model}
    if language:
        fields["language"] = language
    body, content_type = _multipart(fields, "file", audio_path)
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"x-portkey-api-key": _key(provider), "Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:500]
        if e.code == 404 and "DeploymentNotFound" in detail:
            raise GalileoSTTNotProvisioned(
                f"Galileo 上模型 '{model}' 未部署(DeploymentNotFound)。"
                "STT 模型在目录里但需 Galileo 团队在本 workspace 部署后才能用——"
                "见 demos/transcribe/README.md「Galileo STT 开通」。"
                "当前请用本地 faster-whisper 后端(--backend local-whisper)。"
            ) from e
        raise GalileoError(f"transcribe HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise GalileoError(f"网关不可达(需连 RCN):{e}") from e
    # OpenAI 转写响应:{"text": "..."}
    return data.get("text", "") if isinstance(data, dict) else str(data)
