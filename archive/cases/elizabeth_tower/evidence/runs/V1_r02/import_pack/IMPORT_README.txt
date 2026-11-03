大本钟 · 伊丽莎白塔 / HAF 0.2 / V1_r02

首选文件：Elizabeth_Tower_HAF_V1.schem（Sponge v3，DataVersion 3955，Java 1.21.1 格式目标）。
另有完整稀疏 NBT 和 3 个每个不超过 256 KiB 的 NBT 模块。
包围盒 X×Y×Z：100 × 200 × 96。
比例 2 格/米。地坪相对工程原点 Y=3，建筑地上起点 Y=4。
对默认 -64..319 的世界高度，整个包围盒原点 Y 要在 -64..120；这是静态高度核算，不是游戏导入验收。

在空白测试区域使用支持 Sponge v3 的 WorldEdit/兼容工具。
将 schem 放入你的工具配置的 schematics 目录，然后：
  //schem load Elizabeth_Tower_HAF_V1.schem
  //paste -n
先查看选择框位置，再决定 //paste；需要跳过空气时使用 //paste -a。
本文件以局部包围盒最小角为参考点。不同工具对原点的处理应先在测试区核验。
在已有建筑上使用 -a 不会清除原有方块，窗洞与内院可能被旧方块填住。
使用默认 //paste 会包含空气、覆盖包围盒内的既有内容。

完整 NBT 与模块 NBT 都省略空气，不会替你清空原场地。
模块放置：工程原点 + module_offsets.csv 的 offset_xyz，禁止各自居中。
256 KiB 仅是本项目分包约束，不代表满足原版结构方块的尺寸限制；NBT 需兼容导入工具。
没有实体、箱子物品、红石时钟或动态喷泉。

materials.csv 按物品 ID 合并数量；blockstates.csv 保留半砖/楼梯/玻璃片/墙等状态。
原版没有彩色光传播；荧石与海晶灯体现材质差异，预览的光晕不等于游戏实际照明。

已完成：NBT 回读、schem 回读、模块按坐标拼回的全量方块与状态一致性。
尚未完成：Minecraft 导入、碰撞/行走、真实夜间亮度、服务器性能与游戏内视觉验收。

WorldEdit 官方说明：https://worldedit.enginehub.org/en/latest/usage/clipboard/
Sponge v3：https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-3.md

范围：192 格钟楼、四面钟盘、钟室、塔内楼梯候选与截断的邻接翼楼。邻翼用于连接关系测试，不是完整威斯敏斯特宫。
