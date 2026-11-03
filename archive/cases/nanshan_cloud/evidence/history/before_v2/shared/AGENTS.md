# HAF 0.2 主线约定

用户于 2026-10-23 明确：HAF 是后续建筑 Agent 的核心；细节学习、练习与生成均积累在此。HA0.3 保留历史源码，不再维护第二条并行新建路线。

- 当前入口：`python3 tools/agent.py --case <registered_case> --run NEW_RUN`。已注册 `shenzhen_press`、`guangzhou_ctf`、`namsan_tower`。
- 不改写历史 run 或 baseline。参数优先在案例 `research/parameters.json`；通用功能进入 `hafusion/`，具体建筑的几何留在案例目录。
- `learning/` 记录证据、实际消费者、失败案例与验收，不能把研究笔记或程序化规则称为训练后的模型。
- 研究图数量不限。六图是外部建筑 AI 资料包的另一个用途。
- 预览从最终 NBT 独立读回；固定尺度、手性和相机进行版本比较。技术通过不代替视觉或 Minecraft 验收。
- 改进立面细节之前先守住建筑形态、空洞、部件前后关系；背面缺图时明确估算，不能漏建围护。
- 新灯光使用稳定房间 ID 和种子。海晶灯与荧石混合、占用分区、真实灯位共同决定效果；不以增加灯数当作质量分数。
- 大范围更换 workflow 先形成可审阅方案并取得用户确认。案例调整和现有 HAF 能力改进按已授权任务继续。
- 验证：`PYTHONPATH=support/deps python3 -m unittest discover -s tests -v`；案例校验见其 README。
- 尚未连接 Minecraft 游戏、网站、自动施工。不得把离线预览描述为游戏截图。
- 南山案例参数在 `cases/namsan_tower/params.json`，交付基线为 `V1_r02`。地形使用保存的 SRTM 与 OSM；细部高差、植被和隐藏室内仍是解释性近似。`SiteScene` 独立限制占用方块和包围体积，不放宽原 BuildKit Scene 的安全上限。

- 用 `--version` 与只读 `--catalog` 核对当前能力；catalog 是控制索引，不是自动执行的配置。夜景分别研究固定外部灯光、室内/窗灯和高层航空障碍灯。局部样板接入整栋前，检查尺度、净空与消费者。

- 伦敦 V1 新增 `elizabeth_tower` 与 `buckingham_palace`，均 2 格/米；参数在各案例 `params.json`。古典细部由 `hafusion/classical.py` 消费，几何解释仍由各案例负责。大本钟仅带截断邻翼；白金汉宫保留地图内院及侧翼，室内与雕塑有明确简化。

- 南山云科技大厦案例 `nanshan_cloud`：约 1 格/米，三组错位塔体与四组阶梯状浅色平台。坐标/平面为图片解释，未声称实测或 SU 融合；原有案例不改写。
