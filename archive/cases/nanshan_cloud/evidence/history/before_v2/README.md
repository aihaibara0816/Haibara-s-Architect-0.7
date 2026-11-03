# 南山云科技大厦 · HAF V1

交付基线：V1_r04；引擎 HAF 0.2.0；案例适配器 nanshan-cloud-0.1.1。
约 1 格/米，最高塔体 235 格；局部包围盒 140 × 244 × 140。
最终非空气方块：395,735；NBT SHA256：79497dd9b86ec1371c4da62259c5707a63ce403fb7fe4b312b3df4bec4793da8。

这是深圳留仙洞万科云城六期 1 栋的图片研究案例，不是韩国南山塔。
本轮覆盖三组错位塔体、四组阶梯状平台、两种幕墙、屋顶设备区、架空柱廊、部分二层通道、入口与局部景观。没有采用 SU / 其他三维模型。
相对塔高、平面深度、后部平台和场地取照片近似；不含地下、周边楼群和拟建连廊。

## 复现

在工程根目录运行（Python 3.12、numpy、Pillow）：

```sh
python3 tools/agent.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/render_building_case.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/package_building_case.py --case nanshan_cloud --run MY_NEW_RUN
python3 cases/nanshan_cloud/src/validate_case.py
```

生成无需联网。Linux 离线预览另需 EGL/Mesa。验证脚本固定比较已存的 V1_r04 / V1_replay，并核对已存最终预览。更改代码后要用新 run，不能覆盖历史。

## 研究与可修改位置

- `params.json`：坐标、塔高、相对尺寸、层高、种子、玻璃和肋条。
- `src/build_case.py`：特定建筑的阶梯外形、底部、屋顶、灯位规则；部分坐标仍是案例常量，没有虚构完全参数化。
- `research/images.json`：22 条候选索引，下载/查看/采用状态不同；不是 22 张全部经过验证的有效参考。
- `research/component_evidence.json`：构件证据、消费代码、冲突与待核实项。
- `history/revision_log.json`：r01 至 r04 自检与修改原因。
- `review/feedback_template.json`：用户反馈入口，尚未填写。
- `validation/acceptance.json`：独立读回与几何检查，不是写实度评分。

玻璃采用连续立面算法；`windows.json` 的空列表表示未使用独立窗洞登记器，并不表示没有窗。`interiors.json` 是程序化窗后空间记录，不能当作真实房间数。
后侧围护已生成，但不等于后侧形态已准确验证。预览来自实际 NBT，未加载 Minecraft 资源包纹理，未进入游戏。
