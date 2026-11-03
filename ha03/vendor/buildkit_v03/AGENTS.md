# Haibara BuildKit — 工作入口

先读 STATE.md、README.md、.agents/skills/real-to-minecraft/SKILL.md 和当前项目 parameters.json。

本目录已有真正可运行生成器和 NBT，不要退回只写计划。基线为 runs/gafa_admin_v002。核心命令：`python build.py --run 新名字`。核心工具在 tools/；项目专用几何在 tools/gafa_colonnade.py。网络搜索和模型决策由当前宿主执行，生成脚本不连接 API。

所有目前尺寸均为研究试值。photos → assumptions → generator → NBT readback → preview → inspect/diff 是当前执行路径，不代表精准测绘或任意建筑自动生成已完成。保留真实 dimensions.json 的未知值，不反写为实测数据。

常规代码修订自主进行，输出到新 run；不改正式世界、服务器或模型凭证。禁止发送/索要 API Key、Cookie 或 Pro 会话令牌来伪造免费 API。不能越过额度或工具权限。

交付实际 NBT、同源预览、参数和报告；有游戏访问才进行游戏验收，否则 pending。保持方块状态与预览支持范围一致，未知模组不得凭空编 ID。复杂几何应添加独立适配器，不把广美三开间参数推广到所有建筑。

查看器按高度截取同一模型，不是推理/施工次数证据。源程序重跑速度不等于完整 AI 设计时长。
