# Roche适配指南

把上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 接进Roche环境：锁Galileo、去第三方relay、用hub的Roche Blue SSOT做品牌。上游本身的完整用法看它的 [Getting Started](https://github.com/hugohe3/ppt-master/blob/main/docs/getting-started.md),本文只补Roche侧的差异。

## 安装：让CC认识这个skill

上游是标准Python项目(3.10+)。**关键：光clone下来CC不会自动加载这个skill**——得让CC「认识」它。两种装法，推荐plugin。

### 装法A — plugin安装(推荐，CC自动加载)

ppt-master上游自带 `.claude-plugin` 声明(顶层 `marketplace.json` + `skills/.claude-plugin/plugin.json`),可直接装成build-cli / Claude Code插件：

```bash
/plugin marketplace add hugohe3/ppt-master
/plugin install ppt-master
```

装完CC自动加载SKILL.md,你说「做个deck」就触发。之后在插件目录跑一次 `pip install -r requirements.txt`(post-processing脚本要用)。这跟hub自己发的slidev / google-workspace两个plugin是同一套机制。

### 装法B — git clone(手动，适合改上游 / 离线pin版本)

```bash
git clone https://github.com/hugohe3/ppt-master.git ~/ppt-master
cd ~/ppt-master && git checkout <想 pin 的 tag/SHA>   # 别跟 main HEAD,pin 一个验证过的版本
pip install -r requirements.txt
```

clone到hub之外的目录(agent cwd不进git repo,见demos/CONVENTIONS.md §3)。**clone方式下让CC用到skill**:把CC的cwd开在该repo,或symlink `skills/ppt-master` 进你的 `.claude/skills/`。Ona / build-cli都适用，差别只在文件系统落点。**不vendor进hub**——上游是SSOT,hub只放这层Roche适配。

> **依赖很轻**:最小路径(markdown源 + 手写SVG → pptx)只需 `python-pptx` + `cairosvg`(或 `svglib`)+ `Pillow`,**不需要LibreOffice**——svg_to_pptx直接转原生DrawingML形状。生图 / 音频 / 爬网那批重依赖(google-genai / curl_cffi / edge-tts)用不到就不装，攻击面更小。

## 模型：三类，都收敛到Galileo(或默认关)

ppt-master会碰三类模型，罗氏用法各有归处：

**1. 驱动LLM(推理 / 排版思考)—— 已经是Galileo。** ppt-master不自己调LLM,用的是你IDE agent的模型；在hub = Claude Code走Galileo。**什么都不用额外配**。这是唯一「必需」的模型，已天然合规。

**2. 生图(可选，默认关，但走Galileo已合规)。** `image_gen.py` 直接调外部图像API。**默认关闭**——上游推荐直连 `gpt-image-2` 会把内容 / 提示发OpenAI(非Galileo通道)是数据出境红线。**但Galileo本身提供全套图像模型**,把生图指向Galileo就是合规通道：

```bash
IMAGE_BACKEND=openai
OPENAI_BASE_URL=https://us.aigw.galileo.roche.com/v1
OPENAI_API_KEY=<你的 GALILEO_AZURE_API_KEY>       # Azure 系模型用 Azure key
OPENAI_MODEL=gpt-image-1-mini-2025-10-06           # 或 gpt-image-2-2026-04-21;必须带完整版本号
```

**已实弹验证(2026-07-07)**:`GET /models` 返回180个模型含 `gpt-image-2`;`POST /images/generations`(Azure key + 上述带版本号的model)HTTP 200真出图。Galileo目录里图像模型：Azure `dall-e-3 / gpt-image-1/1.5/2`、Bedrock `stability.sd3-5-large / stable-image-core|ultra`、Vertex `imagen-4.0` + **Gemini家族原生生图 `gemini-3-pro-image-preview` / `gemini-3.1-flash-image-preview`(nano-banana)**。坑：裸 `gpt-image-1-mini` 报unknown model,**Azure ID必须带日期版本号**。用的是用户自己的Galileo key(非CC harness token,不算挪用)。

> **授权是per-key/integration粒度——目录列出 ≠ 你的key能调。** 实测：Azure key调gpt-image **成功**;但GCP key调Gemini生图 / Imagen返 **HTTP 412「not allowed for this integration」**。所以**今天能用的生图 = Azure gpt-image**;想用Gemini(nano-banana)/ Imagen要走Galileo access给GCP集成把这几个图像模型加进白名单(申请动作，非技术不通)。

所以生图默认关是**质量 / 成本 / 生成物审查**的取舍，不再是数据出境硬阻塞。用本地素材配图始终安全。

**3. TTS旁白(可选)。** `notes_to_audio.py` 支持edge / elevenlabs / minimax / qwen / cosyvoice——**都不是Galileo,Galileo也不提供TTS**。默认的edge-tts会把讲稿发微软edge端点(数据出境点)。罗氏用法：旁白是可选功能，**默认跳过**;真要旁白走Roche授权的本地 / 合规TTS,别用默认edge。

**红线**:上游README顶部那堆sponsor的API relay(PackyCode / APIKEY.FUN / RunAPI,号称官方价7-10%)是广告、**不在代码路径**;把Roche内容经这些非授权中转 = 数据出境红线，无视。

## 品牌：从hub Roche Blue SSOT派生spec

不去Software Center下载外部 .pptx模板——Roche Blue在hub已经codify过(`assets/roche-brand/tokens` 官方token + `slidev/themes/roche-blue`)。用脚本从这套SSOT派生一份品牌spec:

```bash
python3 scripts/build_roche_brand_spec.py > ~/ppt-master/projects/<你的项目>/roche-blue-brand-spec.md
```

token变了重跑即可，spec自动跟上(SSOT派生，不双写)。spec里有：官方主色 `#0B41CD`、语义色、中性色、字体栈(Roche Sans Light标题)、logo路径、Roche排版取向。

### 两条模板路径

ppt-master有两种"跟随品牌"的方式(见上游 [Templates Guide](https://github.com/hugohe3/ppt-master/blob/main/docs/templates-guide.md)),按投入选：

**路径A — free design + 品牌spec(推荐，低投入)**

generation时把 `roche-blue-brand-spec.md` 一起给AI,让它按这份spec的配色/字体/logo自由排版。不需要预先做模板bundle,最省事。

```
你: 用 roche-blue-brand-spec.md 的品牌规范,把 sources/report.pdf 做成 deck
```

**路径B — create-template品牌bundle(想要固定版式复用时)**

ppt-master的create-template要一个真 `.pptx` 作输入，解析成可复用bundle(layout SVG + design_spec.md + 提取的theme色/字/图)。步骤：

1. 先做一个Roche Blue seed `.pptx`——目前手动：在PowerPoint / LibreOffice里按 `roche-blue-brand-spec.md` 建母版(主色 `#0B41CD`、Roche Sans、放蓝色logo),存成 `roche-blue-seed.pptx`
2. 跑上游 `/create-template roche-blue-seed.pptx` 生成bundle
3. generation时用bundle目录路径：`Make a deck from sources/report.pdf with template <bundle 目录>`

> **实测结论(2026-07)**:路径A(free design + 品牌spec)已实测复刻内部deck两页(swiss-minimal数据密集风、零AI图),产物是真原生可编辑pptx,**够用且最省事**。路径B的seed `.pptx` 只有「要跨deck复用固定版式」才需要，手动做即可——原本设想的「python-pptx从token自动生成seed」经实测**没必要**(直接手写SVG→原生pptx这条路更顺)。

## 本地预览(可选：生成前先渲染看看)

想在出pptx前先看页面效果，用cairosvg把SVG渲染成PNG。四个坑：

- **logo / 外部图片不渲染**:cairosvg默认禁止加载SVG引用的本地文件(安全策略，防恶意SVG读任意文件),`<image href="...logo.png">` 会被静默跳过(不报错、图不出)。修法：渲染时传 `unsafe=True`——`cairosvg.svg2png(url=..., write_to=..., unsafe=True)`。只影响预览；最终pptx由finalize_svg嵌图，不受影响。
- **中文渲染成空心圈(tofu)**:cairosvg用cairo toy font API,不做跨字体per-glyph回退——字体栈第一个是Roche Sans(无中文字形)就整段tofu。修法：含中文的 `<text>` 元素把CJK字体(`Noto Sans CJK SC`)放**字体栈首位**,纯拉丁(标题 / 数字 / 英文)才Roche Sans首位。注：这只影响预览；最终pptx里PowerPoint自己会per-glyph回退，Roche Sans + 中文混排没问题。
- **Roche Sans预览要ttf**:assets里是woff2,cairosvg / fontconfig认ttf——`pip install fonttools brotli` 后把woff2转ttf装进 `~/.local/share/fonts` 再 `fc-cache -f`。系统还需装好CJK字体(`Noto Sans CJK SC`)。
- **特殊符号也会tofu**:Greek(σ Σ)、Unicode下标(ᵢ)、floor括号(⌊⌋)、ŷ 等字符在Roche Sans / Noto里可能缺失，渲成空心圈。修法：①含Greek的行用Noto优先(Noto有希腊字母)②下标用 `<tspan baseline-shift="sub" font-size="9">i</tspan>` 别用Unicode下标字符 ③floor / ŷ 等生僻符spell out(`floor(...)`、"预测")。注：下标数字 ₁₂₃(U+2081)反而正常，画神经网络图时常踩。

## 残留风险速记

- 模型只走Galileo,relay一律不用
- AI生图默认关(取舍非硬阻塞):要生图走Galileo(`GALILEO_AZURE_API_KEY` + 带版本号model),别直连OpenAI
- 敏感/内部deck自用，生成物别外发；HCP/患者/临床数据需CCCA
- **Roche字体外发许可**:嵌入Roche Sans的 .pptx发外部，需对方自备Roche字体(否则回退系统sans);字体文件本身别随 .pptx转发给外部方

完整四维判级见 [compliance-catalog.md](../../../docs/topic/compliance-catalog.md) 的ppt-master行。
