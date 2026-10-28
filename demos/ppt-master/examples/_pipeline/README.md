# _pipeline — Roche exemplar复现工具(SSOT)

所有exemplar共用的生产脚本。放这里而非每个example各拷一份(SSOT / 奥卡姆)。
三个脚本对应制作一份Roche版deck的三类"非手写"产物；SVG本体仍由agent逐页手写
(ppt-master主管线规定：主agent逐页手写SVG,禁脚本批量生成)。

| 脚本 | 作用 | 何时用 |
|---|---|---|
| `render_formula.py` | LaTeX公式 → Roche Blue透明PNG(matplotlib / Computer Modern) | 块级数学公式(通用字体排不规范) |
| `gen_cover_image.py` | Galileo Azure gpt-image → 氛围/装饰配图 | 封面蓝图氛围等"氛围类"图(默认关) |
| `render_preview.py` | SVG → PNG预览(cairosvg, unsafe=True) | 手写完SVG后快速视觉校对 |
| `embed_fonts.py` | 把Roche字体嵌入pptx(OOXML post-process) | **默认不用**:实测PowerPoint拒装(子集+完整都报"一般错误");仅供参考 / 非-PPT阅读器测试 |

## 依赖

```
pip install matplotlib cairosvg Pillow          # 预览 + 公式
# 生图无额外 pip(纯 stdlib urllib);需 GALILEO_ENDPOINT + GALILEO_AZURE_API_KEY 环境变量
```

> 安全：`GALILEO_AZURE_API_KEY` 是**按项目申请的凭据**(有归属 + 配额),**只放环境变量**
> (Ona Secret / `~/.bashrc`),绝不硬编码进脚本、绝不commit。分享/开源本demo只带脚本不带
> key,fork的人 `export` 自己的。`gen_cover_image.py` 只 `os.environ` 读，已确认全仓无明文key。

字体(cairosvg预览要本地装，woff2→ttf):

```python
from fontTools.ttLib import TTFont           # pip install fonttools brotli
import os
src="assets/roche-brand/fonts"; dst=os.path.expanduser("~/.local/share/fonts/roche")
os.makedirs(dst,exist_ok=True)
for fam,ws in {"roche-sans":["Light","Regular","Medium","Bold"],
               "roche-serif":["Light","Regular"]}.items():
    for w in ws:
        f=TTFont(f"{src}/{fam}/Roche{ 'Sans' if fam=='roche-sans' else 'Serif' }-{w}.woff2")
        f.flavor=None; f.save(f"{dst}/Roche{'Sans' if fam=='roche-sans' else 'Serif'}-{w}.ttf")
# 然后 fc-cache -f ~/.local/share/fonts/roche
```

## cairosvg四个坑(踩过，务必知道)

1. **`unsafe=True` 必开**——否则外部 `<image>`(logo / cover_bg / 公式图)静默不渲染(白块)。
2. **字体不做per-glyph回退**——字体栈第一个存在的字体整段套用，缺字形=空心圈(tofu)。
   纯拉丁行 `Roche Sans` 首位；含CJK行 `Noto Sans CJK SC` 首位。
3. **字重只认normal/bold**——`font-weight:300` 不是Light!真Light用独立family名
   `'Roche Sans Light'`(同理 `'Roche Sans Medium'` / `'Roche Serif Light'`)。
4. **`text-anchor="middle"` + 变字体/baseline-shift的tspan会算错宽度**→文字甩偏。
   居中文本只用"改颜色"的tspan;要上下标/换字体的行用 `text-anchor="start"` 手动定x。

Roche Sans缺 `→`(其余 `√ · — × ÷ ² ≤` 都有):需要箭头把它单独包进mono `<tspan>`
(Consolas/DejaVu mono有，预览 + pptx双端渲),或改连字符记号(表头 `EN-DE`)。

## 完整管线(一份deck)

> 引擎(svg_to_pptx等)**不vendor进hub**,新容器里没有。先跑
> [`.claude/skills/pptx-authoring/scripts/setup-engine.sh`](../../../../.claude/skills/pptx-authoring/scripts/setup-engine.sh)
> 装回来(sparse + float最新 + 冒烟测),它装到 `$HOME/ppt-master`。

```bash
bash .claude/skills/pptx-authoring/scripts/setup-engine.sh   # 装/更新引擎 + 冒烟测
cd ~/ppt-master && source .venv/bin/activate
PROJ=projects/<name>_ppt169_<date>
python3 skills/ppt-master/scripts/project_manager.py init <name> --format ppt169
# 主 agent 逐页手写 svg_output/*.svg;公式/氛围图先用本目录脚本产出、SVG 里 <image> 引用
# notes/ 放逐页 NN_*.md 演讲备注;animations.json 放动画配置(可 animation_config.py scaffold)
python3 skills/ppt-master/scripts/svg_quality_checker.py $PROJ   # Roche Sans 非默认字体的 WARN 属预期
python3 skills/ppt-master/scripts/animation_config.py validate $PROJ   # 校验 animations.json group id 对得上
python3 skills/ppt-master/scripts/finalize_svg.py $PROJ          # 嵌图 + 圆角 rect→path
python3 skills/ppt-master/scripts/svg_to_pptx.py $PROJ           # native 默认;自动挂 animations.json + notes/
python3 examples/_pipeline/render_preview.py --in $PROJ/svg_final --out $PROJ/preview
# 字体:不嵌(实测 PowerPoint 拒装程序化嵌入,子集+完整都报"一般错误")。导出即成品,罗氏机器有 Roche Sans 优雅回退。
```

> **导出命令随上游漂移**:老版用 `svg_to_pptx.py ... --only native`,**新版已移除 `--only`**(native是默认)。
> 我们float到最新，所以别照抄旧flag——以 `setup-engine.sh` 的冒烟测 + `svg_to_pptx.py --help` 为准。

可编辑性验证：pptx每页slide XML应有真 `<a:t>` 文本run + `<a:custGeom>`/`<a:prstGeom>` 矢量形状 +
logo `<p:pic>`(非整页图片版);带动画的每页有 `<p:timing>`,备注在 `ppt/notesSlides/`。字体不嵌(`ppt/fonts/` 空)。
