# HAF 主线约定

用户于 2026-10-23 明确：HAF 是后续建筑 Agent 的核心；细节学习、练习与生成均积累在此。HA0.3 保留历史源码，不再维护第二条并行新建路线。

- 当前入口：`python3 tools/agent.py --case shenzhen_press --run NEW_RUN`。
- 不改写历史 run 或 baseline。参数优先在案例 `research/parameters.json`；通用功能进入 `hafusion/`，具体建筑的几何留在案例目录。
- `learning/` 记录证据、实际消费者、失败案例与验收，不能把研究笔记或程序化规则称为训练后的模型。
- 研究图数量不限。六图是外部建筑 AI 资料包的另一个用途。
- 预览从最终 NBT 独立读回；固定尺度、手性和相机进行版本比较。技术通过不代替视觉或 Minecraft 验收。
- 改进立面细节之前先守住建筑形态、空洞、部件前后关系；背面缺图时明确估算，不能漏建围护。
- 新灯光使用稳定房间 ID 和种子。海晶灯与荧石混合、占用分区、真实灯位共同决定效果；不以增加灯数当作质量分数。
- 大范围更换 workflow 先形成可审阅方案并取得用户确认。案例调整和现有 HAF 能力改进按已授权任务继续。
- 验证：`PYTHONPATH=support/deps python3 -m unittest discover -s tests -v`；案例校验见其 README。
- 尚未连接 Minecraft 游戏、网站、自动施工。不得把离线预览描述为游戏截图。
