# 南山云科技大厦 · HAF V2

当前交付 V2_r01；原版 V1_r04 及其源码快照保留。
本轮只调整露台范围、分组轮廓与附着灯带，不改变主塔高宽。
正面最大玻璃宽度 64 → 50 格；相对主塔外挑 8 → 5 格，压边另占 1 格。
上部三行等宽 26 格，下部四行向下加宽。四组标高不变。

## 复现

Python 3.12、numpy、Pillow；预览需 Linux EGL/Mesa。

```sh
python3 tools/agent.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/render_building_case.py --case nanshan_cloud --run MY_NEW_RUN
python3 tools/package_building_case.py --case nanshan_cloud --run MY_NEW_RUN --name Nanshan_Cloud_Custom
python3 cases/nanshan_cloud/src/validate_v2.py
```

渲染入口默认补全东南、西南、东北、西北四个 45 度方向的日夜图。
内部以不超过三张一批的子进程限制内存；可用 --reuse-mesh --only 查看局部。
--only 只是局部预览，不等于完整交付。--output-label 可在另一目录渲染历史 NBT。
模型坐标：东 +X，北 -Z；实际地理北向待核实。

## 参数和反馈

params.json 的 cascades.profiles 分别控制 front/right/inner 的宽度、深度。
research/v2_feedback.json 保存本轮意见、采用值、输出哈希和实际消费代码。
review/feedback_template_v2.json 为下一轮空白反馈入口；HTML 支持填写与导出。
validation/v2 保存独立读回、四面验证、逐方块差分和交互检查。
history/before_v2 保留修改前的案例及共享文件；V1_r04 文件哈希不变。
旧 src/validate_case.py 仅校验原 V1，当前版本请运行 validate_v2.py。
旧 V1 的报告/文档打包脚本保留作历史，不应用来改写当前交付。

本案例采用图片解释，无 SU；后侧平台、第三塔高度、真实平面和室内均有近似。
预览是最终 NBT 几何，未加载游戏资源包纹理；Minecraft 试放和邻接更新待测。
不要把离线技术通过当作照片级还原度验收或神经模型训练完成。
