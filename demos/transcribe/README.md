# transcribe — 音频转写 + LLM校对(Galileo合规)

ASR转写常出同音字、专名误识（四渡赤水的口播ASR出「四都赤水」「遵义→钻翼」「滇军→巅军」「陈赓→陈根」）。本demo提供两段式底座：**转写**（可插拔后端）+ **LLM校对**（Galileo内部网关纠错），并作为三处ASR的共享核心SSOT。

```
音频 ──[Stage 1 转写]──> 原始文本 ──[Stage 2 校对]──> 干净文本 + 变更日志
        backend:                        Galileo LLM(gpt-4o)
        - local-whisper(现役)            术语表 + 领域上下文
        - galileo-stt(未部署,开通即切)
```

与 `demos/meeting-transcribe/`（会议实时采集管线）的区别：本demo是通用底座——任何来源的ASR文本（bilibili / 小红书 / 会议 / 微信语音）都能喂进Stage 2校对。

## 校对分两层——默认让agent自己校对

Stage 2（校对）有两条路，**社区用户默认走第一条**：

1. **agent inline（默认，零凭据）**：人在Claude Code / agent会话里时，转写文本已在上下文，**让agent直接按校对铁律改**，不必调任何LLM API、不必有Galileo账号、不必连RCN。方法论见 `transcript-cleanup` skill。人人有cc，这是最普适的路。
2. **程序化后端（headless/批量）**：只在**没有agent在场**时才需要——脚本流水线、cron、`extract --correct` 一条命令、要确定性变更日志。这条走 `correct.py` 调Galileo LLM。下面的CLI用法都属于这一层。

本demo的脚本（correct.py / transcribe.py）= 第二层的实现。第一层不需要代码，是skill里的方法论。

## 目录

| 路径 | 作用 |
|------|------|
| `lib/asr_core.py` | 共享ASR核心：模型加载（`load_whisper_model`）+ 单文件转写（`transcribe_media_file`）+ yt-dlp助手。bilibili/xhs/meeting三处复用 |
| `lib/galileo.py` | Galileo薄客户端：`chat_complete`（校对用）+ `transcribe_audio`（STT,未部署会抛 `GalileoSTTNotProvisioned`） |
| `lib/correct.py` | LLM校对：`correct_transcript(text, title=, domain=, glossary=)` → 干净文本 + difflib变更日志 |
| `scripts/correct_transcript.py` | 校对CLI（文件/stdin,后端无关） |
| `scripts/transcribe.py` | 转写CLI（本地文件，`--backend`,`--correct` 串联） |

## 用法

> 以下CLI都是**第二层(headless/批量)**。人在会话里让agent直接校对即可，用不到这些。

### 只校对（headless）

任何ASR文本喂进来：

```bash
python3 scripts/correct_transcript.py asr.txt \
  --domain "长征/中国近代军事史" \
  --glossary "四渡赤水,遵义,遵义会议,滇军,黔军,湘军,薛岳,上官云相,陈赓,叙永" \
  -o clean.txt --log changes.md
```

- `--glossary` 给正确写法，模型出现即以此为准；`--domain` 给领域背景。
- 变更日志是difflib本地算的（确定性，不靠模型自陈）。
- 校对铁律（写进prompt）:只修同音/专名/明显误识/标点，不改语义、不增删、不翻译、拿不准保持原样。

### 转写 + 校对一条龙

```bash
# 本地音频文件
python3 scripts/transcribe.py audio.m4a --correct --domain "长征"

# 平台视频走各自 demo 的 extract 脚本（带 --correct 透传）
cd ../bilibili && python3 scripts/extract_subtitle.py <BV> --force-asr --correct --domain "长征"
cd ../xiaohongshu && python3 scripts/extract_subtitle.py <链接> --correct --domain "美妆"
```

## 环境

- **校对(第一层)**：人在agent会话里，agent直接校对，**无任何依赖**。这是默认。
- **校对(第二层，程序化)**：`correct.py` / `extract --correct` 才需要Galileo——连RCN,`GALILEO_ENDPOINT` + `GALILEO_AZURE_API_KEY`。详见 [docs/guide/galileo-gateway-guide.md](../../docs/guide/galileo-gateway-guide.md)。默认走Azure `gpt-4o-2024-11-20`（实测通）。
- **本地转写**（local-whisper）:`pip install faster-whisper yt-dlp`。首次下模型medium ~1.5GB / large-v3 ~3GB,缓存到 `~/.cache/huggingface/`。
  - **HF模型下载**:留 `HF_ENDPOINT` 不设 = 直连huggingface.co（Ona/AWS容器实测正常）。build-cli中国网络若直连慢，再 `export HF_ENDPOINT=https://hf-mirror.com`。旧代码把mirror设成默认反而是Ona上的坑，已移除。

## Galileo STT开通（Stage 1走Galileo的前置）

2026-07-08实测：Galileo `/models` 目录里有 `whisper-001` / `gpt-4o-transcribe-2025-03-20` / `gpt-4o-mini-transcribe`,但 `/audio/transcriptions` 上全返 `DeploymentNotFound`——**模型在目录里，但未在本workspace/虚拟key上部署**。`gpt-4o-audio-preview` 的chat deployment存在但拒绝 `input_audio` 内容块。

所以当前唯一可用的转写后端是**本地faster-whisper**。要启用 `--backend galileo-stt`:

1. 走Galileo Full access / ServiceNow,请求在workspace部署一个转写deployment（`gpt-4o-transcribe` 或 `whisper`）。
2. 开通后，`lib/galileo.py` 的 `transcribe_audio` 直接生效，`transcribe.py --backend galileo-stt --model <部署名>` 即用。

在此之前，`--backend galileo-stt` 会给出清晰的 `GalileoSTTNotProvisioned` 指引，不会静默失败。

## 合规与数据敏感度

- Galileo是Roche认可的**内部**AI网关，把转写文本发给它做校对符合C3/C4闭环——**不出Roche边界**。
- 公开视频（bilibili/小红书）转写是公开内容；会议/微信语音转写可能含C3/C4,校对走Galileo内部闭环即可，**不要外发到公网LLM**。
- 同网关不同面：路由config管理见 `demos/portkey/`,chat backend抽象见 `demos/data-agent/lib/llm.py`,本demo补的是「音频转写 + 校对」这一面。

## Follow-up

- **ollama本地校对后端**：第二层校对目前只有Galileo。给「既没Galileo账号、又要headless(脚本/cron)」的窄场景加一个 `--llm-backend ollama` 走本地开源模型(Qwen/Llama,OpenAI兼容接口),即可全本地无凭据。绝大多数社区用户走第一层(agent inline)已覆盖，故优先级低。
- **Galileo STT开通**：见上「Galileo STT开通」节。
