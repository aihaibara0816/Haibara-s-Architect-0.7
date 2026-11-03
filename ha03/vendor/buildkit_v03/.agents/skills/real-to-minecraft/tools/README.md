# 图纸检查与差分工具

运行环境：Python 3.10+标准库。无需登录、API key、联网或Minecraft。输入只读；`--out`只能创建新文件，不能覆盖已有内容。

```sh
python tools/inspect_build.py building.nbt --out report.json
python tools/inspect_build.py before.schem --compare after.schem --roi 0 0 0 20 10 20 --out diff.json
python -m unittest discover -s tests -v
```

ROI为包含两端的局部坐标 x0 y0 z0 x1 y1 z1，不是自动从提示词识别的区域。没有ROI时仍可列出变化包围盒。不同输入格式仅在两者局部坐标确实一致时有可比性。

## 范围

可解析大端未压缩/gzip NBT的基础tag，在语义层支持Java结构NBT单palette、Sponge v2/v3方块容器。Sponge线性排列按 `x + z * width + y * width * length` 读回。尺寸、索引、重复坐标、非空气方块、材料与Y分布做部分检查。

不支持多palette模板、Bedrock/little endian、旧MCEdit .schematic、Litematica、region .mca、ZIP/world目录、zlib压缩等；遇到未知格式拒绝，不改扩展名。

## 安全与资源

默认输入最大32MiB，解压最大64MiB，包围盒/条目最多1,000,000格，NBT嵌套64层，节点预算8,000,000。大文件会被拒绝，可在可信文件和足够内存下用`--max-cells`调整体积限制；其他限制仍生效。解析可能占用明显多于原文件的内存。建议仍在无账号、无生产世界挂载的受控环境运行不可信图纸。

工具不执行NBT中包含的内容。但“解析成功”不说明命令方块、实体、标牌数据或目标存档放置一定安全；不要直接将未知下载物放入正式服。

## 输出解释

- `structural_subset_check: pass`只代表已实现的字段/坐标/数据检查通过，不是完整格式认证。
- `usable_nonempty_sample:false`表示没有发现非空气/非structure_void方块，不能作为建筑样板交付。
- `local_listed_blockstates_sha256`只含局部坐标和规范化方块状态；不含offset、实体、方块实体载荷、生物群系或其他元数据。
- `non_air_blocks_by_y`包含玻璃/装饰等，不代表实心承重层、地板或真实楼层。
- 差分将不存在的条目与显式air区分；visible差分忽略air/structure_void，但不模拟光照/碰撞。
- 差分不对齐/旋转；位置、朝向、包围盒变化应先检查。变化局限在目标区不证明后台采用增量生成算法。
- `game_validation`永远保留pending；此工具从未运行Minecraft。

## 测试情况

31项合成输入测试通过，见`reports/unit_tests.txt`。覆盖gzip、格式分支、轴顺序、varint、大小预算、空图纸、坏坐标/索引、差分和只读保护。合成fixture编码器只为测试构造小型字节串，**不是生产级建筑导出器**。未用第三方网站成品、广美样板或真实Minecraft导出的文件执行回归，尚需追加这些兼容性测试。
