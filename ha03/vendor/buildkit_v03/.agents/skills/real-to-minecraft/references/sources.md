# 查阅来源与适用范围

查阅日期：2026-10-16。以下是本规范引用的公开来源，不是具体建筑的完整研究资料库。技术版本会变化；实际执行须以目标环境为准。本文和模板是原创流程设计，不复制来源图纸或照片。

**S1 — OpenAI：Build skills。** 用于确认SKILL.md、name/description、scripts/references/assets与按需加载的组织方式。本包为指令型Skill，不包含部署或安装操作。
`https://learn.chatgpt.com/docs/build-skills`

**S2 — KPF：CTF Finance Centre。** 设计方项目页，公布530米高度。只用于环境预检示例，不代表获得完整楼层/施工资料。
`https://www.kpf.com/project/ctf-finance-centre`

**S3 — 广州市档案馆：广州中山纪念堂建筑设计图纸：方寸之间，咫尺匠心。** 页面说明设计图纸保存及数字化情况并展示部分材料；不等于完整图纸已公开下载。
`https://www.gzdaj.gov.cn/gzdt/gnxw/content/post_256825.html`

**S4 — OpenCV：Basic concepts of the homography explained with code。** 平面单应性、透视校正的适用几何背景，不是整栋建筑的自动米制测量。
`https://docs.opencv.org/4.13.0/d9/dab/tutorial_homography.html`

**S5 — 百度地图开放平台：坐标系说明。** 不同来源坐标不可不加处理地叠加。
`https://lbsyun.baidu.com/skins/MySkin/resources/iframs/coordinate.html`

**S6 — COLMAP：Tutorial。** SfM/MVS过程，以及重叠、视差、纹理、反射、光照的采集条件；本包未执行摄影测量。
`https://colmap.github.io/tutorial.html`

**S7 — Create：Loading a Schematic。** 结构.nbt导入工作流；当前整合包兼容性仍需实测。
`https://github.com/Creators-of-Create/Create/wiki/Loading-a-Schematic`

**S8 — Create：CSchematics.java，mc1.21.1/dev分支。** 说明蓝图上传大小可由配置约束。它是移动的开发分支，不是用户服务器已验证的配置。
`https://raw.githubusercontent.com/Creators-of-Create/Create/mc1.21.1/dev/src/main/java/com/simibubi/create/infrastructure/config/CSchematics.java`

**S9 — Create：Printing a Schematic。** 蓝图大炮的施工条件、替换模式与加载问题。
`https://github.com/Creators-of-Create/Create/wiki/Printing-a-Schematic`

**S10 — Mojang：Caves & Cliffs: Part II out today on Java。** 官方记录主世界建筑范围扩展到384格。仅用作原版基线，项目须确认实际维度。
`https://www.minecraft.net/en-us/article/caves---cliffs--part-ii-out-today-java`

**S11 — OpenAI：skill-creator。** 参考精简入口、分离支持材料、将易出错重复任务交给可靠脚本的设计原则。
`https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md`


## v0.2 本次新增查阅（2026-10-16）

下列为本轮实际打开的公开资料。S1—S11沿用v0.1来源记录，不表示本轮全部重新验证。

**S12 — OpenAI：Function calling。** 模型提供调用参数，宿主执行工具并返回结果的多步骤流程。用于说明工具编排架构，不用于证明任何第三方站点的后台。
`https://developers.openai.com/api/docs/guides/function-calling`

**S13 — OpenAI：Images and vision。** 模型可接收图像进行分析。用于设计“实际模型渲染→视觉检查”的接口，不证明本站已经实现。
`https://developers.openai.com/api/docs/guides/images-vision`

**S14 — SpongePowered：Schematic Specification v2。** 本工具Sponge格式检测与方块容器解析的依据。
`https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-2.md`

**S15 — SpongePowered：Schematic Specification v3。** 记录Width/Height/Length、Blocks/Palette/Data、varint和xyz线性排列。工具只实现方块子集，非完整认证。
`https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-3.md`

**S16 — PrismarineJS：prismarine-nbt。** 公共NBT解析器资料，可作为后续独立实现交叉验证候选；本轮未安装、未调用此库。
`https://github.com/PrismarineJS/prismarine-nbt`
