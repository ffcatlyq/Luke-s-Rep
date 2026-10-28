# Meeting Transcribe — 本地音频监听 + 离线转写 + 双语 minutes

捕获 Windows 系统音频（任何会议工具：Google Meet、Teams、Zoom）→ 本地 faster-whisper 离线转写 → Calendar/People 上下文增强 → 双语 meeting minutes。

**全程本地，不出本机。** 适合 C3 数据敏感会议。

## 使用须知

本工具用于个人在自己参与的会议中让 AI agent 接管上下文（自动转写、人物识别、议题归纳），不是通用会议记录系统。

**音频处理边界**

- 抓取的 wav chunks 临时落 `C:\temp\meeting-audio\`，转写完成后应当立即清理（见 Step 5）
- 默认不留存原始音频；如需归档音频，由你自己决定存放位置并自己负责
- transcript 与 minutes 默认落本地 `/tmp/` 或私 repo `$WORKDOCS_PATH/`；不要进 hub innersource 或任何 inner-source / public 仓库

**适用场景**

- 你参与且有合理上下文捕获理由的内部会议（讨论会、答疑会、培训），参会人理解或同意 AI 辅助
- C2 数据等级、C3 视场景而定（参考你部门和数据合规要求）

**不适用场景**

- 主持人或参会人明确声明"不录制 / 不留存"的会议
- 法务、合规、HR 一对一、薪酬/绩效等高敏场景
- 第三方（客户、监管、外部审计）会议
- 大多数跨境会议（CBDT 流程未走通时不要在境外 attendees 在场的会议跑本工具）

**责任分担**

工具本身不向外部任何服务（OpenAI / Galileo / 第三方云）发送音频或 transcript。但**抓取行为、保留时长、分发范围是用户的决定**——Roche 数据分类政策、参会人 consent、跨境合规由你自己确保。本工具不替你做合规判断。

## 架构

```
Windows host                          WSL2 + Claude Code
─────────────────                     ────────────────────────────────
[Meet/Teams/Zoom 音频] → 扬声器
                       ↓ WASAPI loopback (capture.py)
                       ↓ 30s WAV chunks
                C:\temp\meeting-audio\ ─────→ transcribe.py (faster-whisper int8)
                                                     ↓
                                              /tmp/meeting-transcript.md
[你的麦克风] → mic                                   (with frontmatter)
            ↓ PyAudio (capture-mic.py)
            ↓ 30s WAV chunks
   C:\temp\meeting-audio-mic\ ─────────→ transcribe.py --watch-mic
                                                     ↓
                                          /tmp/meeting-transcript-mic.md
                                                     ↓
                                       merge-transcripts.py (按 timestamp 交错)
                                                     ↓
                                       /tmp/meeting-transcript-merged.md
                                       ([loopback] / [mic] 标签 = 2-class diarization)
                                                     ↓
                                              /meeting-minutes
                                       (Calendar event matching + People API
                                        title/manager 增强 + 双语 minutes)
                                                     ↓
                                       /tmp/meeting-transcript-merged-minutes.md
```

## 完整流程（4 步）

### Step 0（可选）— 会前 prep

会议开始前用 [meeting-prep skill](../../.claude/skills/meeting-prep/SKILL.md)：

```
/meeting-prep                           # 列出今天没开始的会议
/meeting-prep <event_id>                # 指定会议
/meeting-prep "title fragment"          # 模糊匹配
```

输出落 `/tmp/meeting-prep-<event_id>.md`：议程 + 参会人简介 + 相关 doc + 最近 14 天邮件 thread 摘要 + 建议关注问题。

### Step 1 — Windows 端起 capture

打开 PowerShell（**不**是 WSL），跑：

```powershell
# 终端 A：抓扬声器输出（其他人说话）
& "C:\Program Files\Python312\python.exe" "\\wsl.localhost\Ubuntu\home\<sam>\projects\silicon-hitchhiker\demos\meeting-transcribe\scripts\capture.py"

# 终端 B：抓麦克风（你自己说话）
& "C:\Program Files\Python312\python.exe" "\\wsl.localhost\Ubuntu\home\<sam>\projects\silicon-hitchhiker\demos\meeting-transcribe\scripts\capture-mic.py"
```

会议中两个终端同时跑。Ctrl+C 停止。

**列 mic 设备**（如果默认 mic 不对，比如戴耳机时）：

```powershell
& "C:\Program Files\Python312\python.exe" "...\capture-mic.py" --list
& "C:\Program Files\Python312\python.exe" "...\capture-mic.py" --device-index 7
```

### Step 2 — WSL 端起 transcribe

```bash
# 终端 A：转写 loopback
python3 ~/projects/silicon-hitchhiker/demos/meeting-transcribe/scripts/transcribe.py

# 终端 B：转写 mic（独立 watch dir + output）
python3 ~/projects/silicon-hitchhiker/demos/meeting-transcribe/scripts/transcribe.py \
    --watch-dir /mnt/c/temp/meeting-audio-mic \
    --output /tmp/meeting-transcript-mic.md \
    --source local-mic
```

模型默认 `small`（~500MB，首次自动下载），中英混合 OK，CPU 上 ~5-8x realtime。

**transcript 自带 YAML frontmatter**：

```yaml
---
date: 2026-05-26
start_time: 2026-05-26T11:00:00+08:00
end_time: 2026-05-26T11:18:30+08:00     # 每 chunk 完后 in-place 更新
timezone: Asia/Shanghai
source: local-loopback
model: small-int8
---
```

frontmatter 是后续 Calendar matching 的依据——别手工删。

切换模型 / 语言：

```bash
python3 transcribe.py --model medium      # 更准，CPU 上 ~1x realtime
python3 transcribe.py --lang zh           # 强制中文（auto detect 偶尔翻车时用）
python3 transcribe.py --timezone UTC      # 默认 Asia/Shanghai
```

**真实会议建议直接 `--output` 到持久路径**：

默认 `/tmp/meeting-transcript.md` 重启会丢、转完容易忘记搬。会议开始时就指定持久路径：

```bash
python3 transcribe.py \
    --output $WORKDOCS_PATH/meetings/2026-05-26-<title>.md
```

`$WORKDOCS_PATH` 指向 private repo（独立 git，不推到 hub innersource；`echo $WORKDOCS_PATH` 拿真值）。后续 `/meeting-minutes` 默认按 transcript 同目录写 `<title>-minutes.md`，自动跟着持久化。

### Step 3 — 合并 loopback + mic transcripts

会议结束后：

```bash
python3 ~/projects/silicon-hitchhiker/demos/meeting-transcribe/scripts/merge-transcripts.py \
    --loopback /tmp/meeting-transcript.md \
    --mic /tmp/meeting-transcript-mic.md \
    --output /tmp/meeting-transcript-merged.md
```

merged transcript 按 timestamp 交错，每段标 `[loopback]`（其他人）或 `[mic]`（你）——**自然实现 2-class diarization**。

### Step 4 — 出双语 minutes

```
/meeting-minutes /tmp/meeting-transcript-merged.md
```

Skill 自动：

1. 读 frontmatter 拿 start/end/timezone
2. 调 [Calendar.events.list](scripts/find-meeting.py) 找匹配 event
3. 调 [build-context.py](scripts/build-context.py) 拉 attendees title + manager
4. 读 attached docs 当 prior context（截 5KB）
5. 过滤 transcript 里 "不要记录" / "口头说" markers
6. 在 Claude Code 内综合生成中英并排 minutes（不调外部 LLM）
7. 写 `/tmp/meeting-transcript-merged-minutes.md`

完整 skill 文档：[meeting-minutes/SKILL.md](../../.claude/skills/meeting-minutes/SKILL.md)。

只有 loopback 没 mic 也能跑（不要 Step 3，Step 4 直接读 `/tmp/meeting-transcript.md`），但缺你自己发言。

### Step 5（强制）— 清理音频

minutes 出完之后，立即清理 wav chunks。转写完成后 wav 失去价值（transcript 已经覆盖内容），留着只增加泄露面：

```bash
# 在 WSL 跑（路径是 Windows 文件夹，从 WSL 也能直接删）
rm -f /mnt/c/temp/meeting-audio/*.wav
rm -f /mnt/c/temp/meeting-audio-mic/*.wav
```

或 Windows PowerShell：

```powershell
Remove-Item C:\temp\meeting-audio\*.wav
Remove-Item C:\temp\meeting-audio-mic\*.wav
```

养成"会后立即清理 wav"的习惯。如果你确有归档音频的合理理由（事后复核、合规留痕），主动转移到加密路径并自行管理保留期限——不要让 wav 滞留在 `C:\temp\` 默认目录。

## 不录云端

- **faster-whisper** = CTranslate2 backend，纯本地推理
- **Claude Code（minutes 生成）** 走 build-cli 内置 token 预算，调用走 Roche 合规边界内
- **不调 OpenAI / Galileo / 任何外部 API**

## 敏感内容自动过滤

转写后的 transcript 里如果出现下列 markers，meeting-minutes skill 会把后续讨论段从 minutes 里剔除：

- "不要记录" / "这条不要记"
- "口头讲一下" / "我们口头讨论一下"
- "不要在大群里说" / "private 一下"
- "敏感的话" / "不该说的"

但 transcript 本身仍保留原话——所以 transcript 文件本身的存放位置要按敏感程度处理（C3 → 私 repo `$WORKDOCS_PATH/`，不要进 hub）。详见 [chat-reply skill 敏感内容章节](../../.claude/skills/chat-reply/SKILL.md)。

合规口径详见 README 顶部"使用须知"。

## 已知限制

- **延迟**：每个 chunk 30s 录满后才转写，再几秒处理，transcript 比实际滞后 35-40s
- **多人混说一段**：whisper 把一个 30s window 当成连续段处理，**多人重叠说话会合并成一坨**。merge 后的 [loopback]/[mic] 区分能解 50%；剩下要靠后处理或人工
- **中英混合**：`small` 模型 OK，`medium` 更准但 CPU 慢
- **AppLocker**：Roche 工作机如果 Python 路径白名单限制，capture 跑不起来。参考 [demos/wechat-cli/README.md](../wechat-cli/README.md) 的 admin temporary access 申请流程
- **PyAudio Windows 安装**：`pip install pyaudio pyaudiowpatch` 走 wheel，不需要编译工具链；如果 wheel 装不上检查 Python 是不是 32-bit / 路径问题
- **耳机 mic 选错**：Bluetooth 耳机时默认 input device 可能不是耳机麦。先 `capture-mic.py --list` 看设备，再 `--device-index N` 手选

## 故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `capture.py` 报 `no WASAPI loopback devices` | pyaudiowpatch 装错版本 / Windows 不支持 | `pip uninstall pyaudio && pip install pyaudiowpatch` |
| `transcribe.py` 报 huggingface DNS 错 | Roche 网络挡 huggingface.co | 脚本已默认走 `HF_ENDPOINT=https://hf-mirror.com`，如果还挡先 ping `hf-mirror.com` |
| `transcribe.py` 第一次启动慢 | 模型首次下载 | 等 ~108s（small）/ ~5min（medium），后续秒起 |
| transcript 没 frontmatter | 你跑的是旧 transcribe.py | 拉最新代码或手工加 frontmatter |
| `/meeting-minutes` 找不到 Calendar event | 私会 / event 没建 / 时间偏 | skill 自动降级到 `--attendees` 手指定，或 `--no-calendar` 强跳 |
| 麦没声 | 设备索引错 | `capture-mic.py --list` 列设备，看 `(default)` 那个；不对就 `--device-index N` |

## 提速

- 用更小的 chunk（10s）减延迟，但 wav 文件多
- 上 GPU（如果有 NVIDIA），`--device cuda`（compute_type 自动 float16），速度 10x+
- 用 whisper.cpp 替代 faster-whisper（CPU 更快但需要装编译工具链）

## 文件

| 路径 | 用途 |
|---|---|
| [scripts/capture.py](scripts/capture.py) | Windows WASAPI loopback capture（其他人声音） |
| [scripts/capture-mic.py](scripts/capture-mic.py) | Windows mic capture（你自己声音） |
| [scripts/transcribe.py](scripts/transcribe.py) | WSL faster-whisper 转写循环 |
| [scripts/merge-transcripts.py](scripts/merge-transcripts.py) | 合并 loopback + mic transcript |
| [scripts/find-meeting.py](scripts/find-meeting.py) | Calendar event 时间窗匹配 |
| [scripts/build-context.py](scripts/build-context.py) | Calendar event + attendees + docs JSON 上下文 |
| [.claude/skills/meeting-minutes/](../../.claude/skills/meeting-minutes/SKILL.md) | transcript → 双语 minutes skill |
| [.claude/skills/meeting-prep/](../../.claude/skills/meeting-prep/SKILL.md) | event_id → 会前 brief skill |
