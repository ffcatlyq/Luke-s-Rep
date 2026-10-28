# 原版对照(original-reference)

[`preview/`](preview/) 是ppt-master上游example `attention_is_all_you_need` 对应六页的
**缩小PNG预览**,仅供和Roche版对照看差异。

**这里不放上游的大SVG / 大原图**(避免vendor上游 + 膨胀innersource)。原版完整配方
(16页SVG、design_spec、spec_lock、images/)在clone的上游repo里：

```
~/ppt-master/examples/ppt169_attention_is_all_you_need/
```

## 原版口径(与Roche版的差异见上级 [`../README.md`](../README.md) 对照表)

- 主题：navy / cool-corporate(深海军蓝),白底学术极简
- 主色：`#1A365D`(primary)+ `#3182CE`(accent)
- 字体：Georgia衬线标题 + Arial/Microsoft YaHei正文
- 公式：codecogs LaTeX渲染PNG(mixed policy:块公式渲图、行内小数学留text)
- 图：封面 / 序列演化 / 正弦波用AI生成蓝图氛围；架构 / Fig2嵌论文原图

对照页：01 cover · 02 why-it-matters · 05 architecture · 07 scaled-dot-product ·
12 complexity-table · 14 results。
