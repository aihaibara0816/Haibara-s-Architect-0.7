# Haibara BuildKit v0.3 — 广美柱廊可运行原型

**先查看：解压后双击 `preview.html`。直接测试：使用同目录的 `gafa_admin_colonnade.nbt`。**

本包从 v0.2 的规则与检查器继续开发，已经实际生成局部建筑、输出结构 NBT、读回比对、生成离线三维预览和六个视角截图。它不是只有提示词的交接包，也不是任意建筑名的一键生成服务。

## 当前产物

- 广州美术学院大学城校区行政楼外柱廊的**尺度待校准研究样板**，三个开间、两排柱列、红色墙面、浅坡梁格屋盖、外楼梯、平台和局部地坪。
- 包围盒 X×Y×Z：22×20×34；非空气方块 3,774；最终 NBT 36,887 字节。
- 候选目标：Java 1.21.1 / Create 结构 NBT。方块均使用 `minecraft:` 命名空间，不含实体、方块实体或命令方块。当前目标游戏注册表及导入行为未实测。
- `runs/gafa_admin_v002/` 为本次最终版本；`v001` 为修订前版本。v002 修正了楼梯、平台局部半砖组合，共 40 个方块状态发生变化，约定楼梯区域之外变化为零。
- 图像来自**读回导出的 NBT 后形成的同一几何数据**。预览使用示意颜色、近似栏杆模型和 CPU 深度缓冲渲染，不是 Minecraft 材质、光影、碰撞或游戏截图。

## 怎么使用

### 1. 只看小样

解压整个压缩包，再打开 `preview.html`，无需启动服务器、安装依赖、登录或提供 API Key。支持旋转、缩放、六个固定视角与按 Y 高度切片播放。该播放不是 AI 调用历史；真正的四个生成阶段在 `runs/gafa_admin_v002/stages/` 中各自保存了 NBT。

本会话已在 Chromium 中载入 HTML 文本并测试渲染。运行环境的 file:// 访问受管理策略限制，因此没有把直接 file:// 打开称为已测试；普通本地浏览器应能打开自包含 HTML，但仍以你的设备结果为准。浏览器无法运行脚本时，直接查看 `preview.png` 或 `runs/gafa_admin_v002/previews/`。

### 2. 游戏测试

**文件在整个包围盒中包含显式空气。只在空白测试世界/空地导入；不要覆盖正式建筑。**

找到当前游戏实例实际的 `schematics` 目录，将 `gafa_admin_colonnade.nbt` 放入其中；使用 Create 蓝图桌和空蓝图加载，先定位预览，再在创造模式测试放置。具体界面以你的 Create 版本为准。根目录不要误选成另一个启动器实例。

局部模型地坪上表面是 Y=2。世界放置坐标尚未确定，不自动修改任何存档、服务器或资源包。整合包版本、方块状态、半砖通行、栏杆碰撞、光照和蓝图施工均需要游戏实测。

Create 文档：
- https://github.com/Creators-of-Create/Create/wiki/Loading-a-Schematic
- https://github.com/Creators-of-Create/Create/wiki/Printing-a-Schematic

### 3. 重新生成

核心生成和 HTML 输出仅依赖 Python 3.10+ 标准库。Windows 在项目根目录运行：

```powershell
py -3 build.py --run gafa_admin_v003
```

其他系统或使用 `python` 命令的环境：

```bash
python build.py --run gafa_admin_v003
```

新版本在 `runs/gafa_admin_v003/`。已经存在的 run 名会被拒绝，防止覆盖此前成果。

```bash
python -m unittest discover -s tests -v
python tools/inspect_build.py runs/gafa_admin_v002/gafa_admin_colonnade.nbt
```

可选截图脚本需要额外的 Playwright Python 包和 Chromium；缺少它们不妨碍生成 NBT 和打开 HTML：

```bash
python tools/capture_previews.py runs/gafa_admin_v003 --browser /path/to/chromium
```

### 4. 交给 Codex 继续开发

在本地 Codex 中打开包含 `AGENTS.md` 的本目录，采用 **Sign in with ChatGPT** 登录方式使用你的现有套餐，不需要把 API Key、Cookie 或访问令牌交给本包。让 Codex 先读取 `STATE.md`，然后直接修改参数或项目适配器、运行程序和测试。

示例任务：

> 读取 AGENTS.md 和 STATE.md，以 gafa_admin_v002 为基线继续。先查看真实参考图及同源预览，改进柱子的表达和梁格关系，不擅自改变比例。生成新 run，执行测试与局部差分，报告具体修改。没有游戏访问时保持游戏验收 pending。不要重新从零制作启动包，也不要调用另付费的 API。

官方说明核对于 2026-10-16：
- Codex 套餐使用与额度：https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- ChatGPT 登录与 API Key 计费的区别：https://developers.openai.com/codex/auth
- 本地 CLI：https://developers.openai.com/codex/cli
- Skill 组织：https://developers.openai.com/codex/skills

**Pro 不是无限 API 余额。** 通过 ChatGPT 登录 Codex 使用相应套餐额度；API Key 调用按 API 规则另计。生成器和查看器自身没有网络或模型调用；编写、查资料和修改时的 ChatGPT/Codex 用量仍由账户计量。本包未测算订阅成本，也不宣称比第三方某次生成更便宜。

## 重要限制

尺寸都来自独立保存的研究试值，不是实测。暂定柱距 8m、柱径 2m、屋盖高位 18（局部 Y）、平台顶面 6（局部 Y），不能宣传成已经准确复原了广美。两米柱径在当前方块网格中变成 2×2 方柱；不是圆柱。连续红墙、窗洞位置、屋顶背面和构造也包含研究性补全。没有复原办公室或整栋楼。

当前只有 `gafa_colonnade` 一个项目适配器。更换成中山纪念堂、周大福中心，需要 AI/开发者基于新资料增加适配器或构件算法；不能只改项目名称就得到对应建筑。通用层已提供方块写入、方盒、体素圆柱、累计轴线量化、结构 NBT 输出、部分格式检查和基本形状预览。复杂屋面、玻璃透明、模组自定义几何、摄影测量、自动联网、AI 服务接入、实际游戏控制仍未实现。

本轮完成 28 个新增单元/样板测试及 31 个继承检查器测试；这些不是“59 栋建筑通过”或 Minecraft 兼容性认证。详见 `reports/`。
