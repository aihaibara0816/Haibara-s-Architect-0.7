# 广州周大福金融中心 / HAF V1

本案例用于把 HAF 从深圳报业大厦的横向幕墙扩展到广州东塔的竖向幕墙。它是显式参数与人工研究驱动的案例适配器，不是任意建筑自动重建模型。

最终输出：`runs/V1/building.nbt`；主塔地面以上265格，统一0.5格/米。场景80×269×92，地面顶面Y+2，塔冠最高面Y+267。目标Java1.21.1；游戏内验收未进行。`release.json` 记录最终哈希。

## 重现

在 HAF 根目录执行：

```bash
python3 tools/agent.py --case guangzhou_ctf --run MY_REPLAY
python3 cases/guangzhou_ctf/review/render_case.py --run MY_REPLAY
PYTHONPATH=support/deps python3 -m unittest discover -s tests -v
```

run 必须使用新名称，历史 NBT 不覆写。建造仅使用Python标准库及打包的HAF代码；预览使用Pillow、NumPy与EGL/Mesa。源包带公共依赖与字体；没有依赖临时资料路径或网络下载来重建方块。

## 可修改位置

| 内容 | 文件或字段 |
| --- | --- |
| 统一尺度、坐标和包围盒 | `research/parameters.json` / `frame` |
| 各层级平面、标高与斜顶 | 同上 / `tower` |
| 竖梃材质、模数、玻璃 | 同上 / `facade`，公共 `hafusion/facade.py` |
| 裙楼和连桥 | 同上 / `podium` |
| 窗后深度、半砖楼板 | 同上 / `interior` |
| 随机灯光 | 同上 / `lighting`，公共 `hafusion/lighting.py` |
| 图片到实际代码的对应 | `research/evidence_regions.json` |
| 反馈与失败修订 | `research/feedback_log.json`、`history/` |
| 固定相机 | `review/render_case.py` |

材料及导入说明见 `deliverables/`。完整NBT约496KiB；部分导入工具限制256KiB，本案另提供40个各轴不超过32格的手动模板，独立回读后精确拼合。模板没有显式空气，不负责清空旧建筑。

## 本轮经验

- 竖梃与玻璃分层，闪长岩墙柱仅半格宽；转角用玻璃填片补齐。
- 直墙样板不足以证明量化弧面成立，必须检查台阶转角和凹槽。
- 连续的窗后背板随平面内缩；内部不是实测房间，也不保证1:2净高可走。
- 灯槽在随机亮暗前分配；不能盖掉结构或触发相邻玻璃片连接变化。
- 本案例固定随机数命名空间 `room-lighting-0.2`；公共模块保留旧调用的 `room-lighting-0.1` 默认流。辅助代码版本更新不会重新抽样旧房间。
- 公共 Scene 通过显式参数支持最多2,000,000格包围体积，默认仍1,000,000；reader相应使用显式Limits。此处实际非空气格位约17.6万。
- 原深圳报业大厦V2可按更新公共代码原样重现，375份旧案例文件校验未变。

## 限制

公开 KPF 平面和剖面按设计参考使用，未证实为现状竣工图。地理北向未标定；模数、斜面和层高作网格量化。裙楼范围及地景为估算；未复原完整商业综合体、地库或邻楼。图片记录不限数量；整理34条记录并标记重复，不宣称34个独立角度，也没有训练视觉模型。

参数中的 `crown_accents` 仅提出灯位候选；最终无碰撞筛选没有接受塔冠专用灯槽，实际数量为0。LPA外梃与顶部线光仍待实现；当前夜景以窗后和裙楼灯光为主。

预览来源为最终NBT回读，但不包含游戏资源包纹理和完整原版光照、碰撞、邻接更新。技术通过、人工视觉判断、用户认可与游戏验收是不同状态。
