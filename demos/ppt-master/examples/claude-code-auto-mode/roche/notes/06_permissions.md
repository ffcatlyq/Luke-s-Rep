怎么把自主权给回来?三级权限:默认问、放行规则自动过、硬护栏永远拦。放行规则写在 settings.local.json 的 allow 里,加上 gh pr merge、approve 那条 curl,就不再逐条弹窗。关键性质记住:这文件 gitignored + 每容器独立,不进 git、不随 clone 走——这是下一段故事的伏笔。

要点:放行规则+文件关键性质伏笔
时长:1:05
