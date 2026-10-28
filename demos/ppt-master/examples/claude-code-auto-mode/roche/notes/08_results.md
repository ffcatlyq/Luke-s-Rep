串起来看 settings.local.json 的一生:老容器里放行规则在,approve/merge 自动过——你看到的'auto-mode 自己就批了'。US→EU 搬家,这文件 gitignored + 每容器独立 + 没跑迁移,丢了,于是全被拦。加回 local setting,approve 一次过、#307 merged。教训:'老容器能、新容器不能'几乎总是本地配置没跟过来,不是记忆坏了、也不是 GitHub 改了。搬家记得带它。

要点:老容器→搬家丢→加回;教训
时长:1:05
