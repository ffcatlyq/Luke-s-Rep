---
theme: default
title: PRESENTATION_TITLE
highlighter: shiki
transition: slide-left
mdc: true
---

<!-- Slide 1: Cover -->

<div style="flex:1; display:flex; flex-direction:column; justify-content:center; align-items:center;">

<div style="text-align:center; margin-bottom:1.5em;">
  <div style="font-size:1.8em; font-weight:700; color:var(--text); letter-spacing:0.08em;">MAIN_TITLE</div>
  <div style="font-size:1.1em; color:var(--green); margin-top:0.4em; font-style:italic;">SUBTITLE</div>
</div>

<Terminal title="init.sh" style="max-width:75%; width:100%;" bodyStyle="padding:1.6em 2em; line-height:2.2;">
  <div class="line"><span class="prompt">$</span> <span class="cmd">echo "TOPIC"</span></div>
  <div class="line"><span class="output">DESCRIPTION</span></div>
  <div class="line"><span class="prompt">$</span> <span class="cursor-blink">_</span></div>
</Terminal>

<div style="text-align:center; margin-top:2em; font-size:0.78em; color:var(--text-dim);">
  ORGANIZATION · AUTHOR · 2025
</div>

</div>

---

<!-- Slide 2: Content page template -->

## Page Title

<div style="flex:1; display:flex; flex-direction:column; gap:0.8em;">

<!-- Content goes here. Use components: Terminal, Card, Divider, Footnote -->
<!-- See slidev-authoring skill: LAYOUT_RULES.md for layout rules, themes/<name>/theme.md for theme rules -->

</div>

<Footnote :push="true">Source or summary text</Footnote>
