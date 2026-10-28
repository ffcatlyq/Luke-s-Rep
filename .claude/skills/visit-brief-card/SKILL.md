---
name: visit-brief-card
description: 给客户/KOL 拜访做一张高级商务风的「拜访信息卡」一页海报(PNG)。输入专家姓名 + 拜访时间/地点 + 拜访目的 + 拜访人员,自动从 Drive 找专家简介(含照片)、查当日天气,套罗氏蓝模板渲染成图并上传 Drive output。当用户说"做张拜访信息卡""拜访准备""visit brief""帮我准备拜访 XX 主任""行前沟通卡""拜访海报"时触发,即便没说"卡"字,只要是为一次线下客户拜访准备一页纸背景资料,都用本 skill。
---

# Visit Brief Card — 拜访信息卡

## 定位

一线/区域市场去拜访 KOL 前,手机上看一眼就知道:去见谁、几点在哪、目的是什么、谁一起去、当天天气。产出一张竖版海报 PNG(罗氏蓝商务风),存到 Drive output 文件夹。

参考视觉:浅蓝→青绿渐变头部 + 医院楼群插画 + 丝带式栏目标题 + 橙色高亮时间。栏目顺序固定:拜访信息 → 专家简介 → 拜访目的 → 拜访人员 → 出行提示。

## 核心原则:不杜撰

专家简介、职称、学术任职**一律以 Drive 里的专家简介文件为准**。用户没给、文件里也没有的字段(集合时间、详细地址、下一站、论文/研究方向…)**不要编造**,直接省略该项。天气是预报值,脚注注明"仅供参考"。这与部门合规红线一致(见 AGENTS.md 第 5 节)。

## 需要用户提供的最小输入

- 专家姓名(用于 Drive 检索简介)
- 拜访时间(日期可选,默认取最近的工作日;上午/下午影响天气时段)
- 地点(医院/院区)+ 具体位置(楼层/科室)
- 拜访目的(1–3 条)
- 拜访人员名单

缺关键项(时间/地点/目的)时**先在正文里列编号问题问全**(遵循 AGENTS.md 4.3,不用弹窗),再动手。

## 工作流(6 步)

### Step 1 — 找专家简介 + 提取照片

在 Drive 搜专家姓名,优先 `.pptx`/`.docx` 简介文件:

```bash
cd demos/google-workspace/scripts
python3 - <<'PY'
from gw_client import get_drive_service
svc=get_drive_service()
for q in ["name contains '姓名'","fullText contains '姓名'"]:
    r=svc.files().list(q=q+" and trashed=false",
        fields="files(id,name,mimeType,modifiedTime)", pageSize=20,
        includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
    for f in r.get("files",[]): print(f["id"], f["name"], f["mimeType"])
PY
```

下载 pptx,用 python-pptx 抽文字(职称/任职逐条)和图片(`shape.shape_type==13`,存最大那张作证件照)。若无 `pptx` 模块先 `pip install python-pptx -q`。照片不用手动压缩——`build_card.py` 会自动缩放+base64 内嵌。

若 Drive 找不到简介:如实告诉用户,问是否手动提供任职信息或跳过简介栏。

### Step 2 — 查当日天气

用 wttr.in 取目标城市(从医院所在地推断)当日、对应时段(上午看 9–12 点,下午看 13–16 点)的温度/体感/降水概率/风/湿度:

```bash
curl -s "https://wttr.in/<City>?format=j1" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for day in d['weather']:
    if day['date'].endswith('-MM-DD'):  # 换成目标日期
        for h in day['hourly']:
            if h['time'] in ('900','1000','1200'):  # 上午;下午用 1300/1400/1500
                print(h['time'],h['tempC'],h['FeelsLikeC'],h['weatherDesc'][0]['value'],h['precipMM'],h['chanceofrain'],h['windspeedKmph'],h['humidity'])
"
```

有降水就在出行提示加"建议备伞"。天气非承重信息,取不到就省略天气卡、脚注说明。

### Step 3 — 组装 config JSON

按 `assets/template.html` 的占位符写一个 config(全部字段见 `scripts/build_card.py` 顶部 docstring)。要点:
- `time` 用橙色高亮,填纯时间如 `"14:00"`。
- `purpose_title` 普通拜访用"拜访目的";若用户强调是"专家需求",用"专家需求 · 拜访目的"。
- `wx_desc` / `expert_hosp` 允许内嵌 `<br>` `<b>`;其余字段脚本会做 HTML 转义,直接写纯文本。
- `footer` 固定含数据来源 + `⚠️ 内部拜访准备,请勿外发`。

### Step 4 — 渲染 PNG

```bash
cd .claude/skills/visit-brief-card
python3 scripts/build_card.py \
  --config /tmp/card.json \
  --template assets/template.html \
  --photo /tmp/expert.jpg \
  --out /workspaces/<repo>/outputs/<姓名>拜访准备.png
```

脚本用 Playwright `chromium-headless-shell` 截全页图(800px 宽,2x 清晰度)。页面过长会告警。

### Step 5 — 自检

`view` 生成的 PNG,确认:照片是本人证件照、时间/地点/目的正确、无占位符残留(`{{...}}`)、无文字溢出。有错回 Step 3 改 config 重渲染。

### Step 6 — 上传 Drive output

传到用户配置的 output 文件夹(`profile.local.yaml` 的 `outputs.drive_folder_id`;当前为 `1-F5ff_eb3v2IHux1_VPlIzQ3OeH4NA6O`)。同名文件用 `files().update` 覆盖、新的用 `files().create`。给用户回 webViewLink。

## 多专家批量

用户一次给多位专家(如一天几场拜访)时,对每位跑一遍 Step 1–6,人员名单/日期若相同可复用,只换姓名/时间/地点/目的。分别命名 `<姓名>拜访准备.png`。

## 依赖

`python-pptx`、`Pillow`、`playwright`(chromium-headless-shell 已装)、Drive API(`demos/google-workspace/scripts/gw_client.py`)。缺 pptx 时 `pip install python-pptx -q`。
