# 工业设施与铁路场景

适用：厂房、储罐、筒仓、高炉、公辅、管廊、动车所和联络线。这是仓库可复用工作规则；个人技能安装状态见主 README。

## 输入

- 生产类型与运行/停产/再利用状态
- 设备身份和物料流向
- 接口标高、截面、支撑和净空
- Create/原版版本与实际功能边界

## 执行规则

1. 厂房、设备、连接系统分层；按行业选择公辅，不给每家厂复制同一清单。
2. 固定顶罐、外浮顶罐、球罐、筒仓与煤气柜分开；外形相似不能交换功能。
3. 高炉保留主炉、框架、配套炉与上料斜线；不能压成一座实心锈塔。
4. 管廊、输送廊、铁路各自记录起终点、连接高度与通行净空，不能悬空或穿过封墙。
5. 场景和轨道几何、Create连接、实际行车分别验收；装饰轨道不能写成可运营线路。
6. 本版本厂房/管廊/固定顶罐为新原创类型试样；不冒充既有Guanggang/Factory/Depot/Substation工程的全部重建。

## 消费入口

- `hafusion/habitat07.py:workshop-bay`
- `hafusion/habitat07.py:pipe-rack`
- `hafusion/habitat07.py:fixed-roof-tank`
- `tools/haf.py archive show --case guangzhou-east`

## 案例与验收

案例：`industrial-atlas`、`guangzhou-east`、`southeast-link`。

- 设备轮廓与行业一致
- 柱网、采光、装卸门与硬地
- 接口连续、承托、跨路高度
- 铁路纵坡/曲线/模组连接与游戏验证

## 当前边界

- 未实现：真实工程设计和安全规范认证
- 未实现：完整生产系统或列车调度模拟
- 未实现：全部外部工业工程生成器的自动恢复

通过 `python -X utf8 tools/haf.py skill show --name industrial` 读取同源机器可读规则。

