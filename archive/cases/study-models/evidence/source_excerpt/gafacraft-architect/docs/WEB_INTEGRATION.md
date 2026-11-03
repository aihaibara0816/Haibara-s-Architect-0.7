# gafacraft.cn 接入预研（未部署）

2026-10-20对`https://gafacraft.cn`做公开只读打开，返回不可访问；搜索`site:gafacraft.cn`未获得可用页面。因此**现有框架、服务器、登录、存储、部署入口均未知**。以下是与框架无关的接口建议，不是完成网站源码审查后的结论。没有修改站点、DNS、服务器或仓库。

## 建议的任务生命周期

`draft → researching → needs_review 或 spec_ready → queued → building → validating → succeeded / failed`。

提交时先保存原始一句话、图片文件引用及授权声明，再进行研究扩写。研究包与施工overlay分开存储；Spec校验通过才能入构建队列。服务端从可信配置补上世界和资源约束，不能由模型自行声明已验证环境。

## 建议接口（本轮未实现服务端）

| 接口 | 内容 |
|---|---|
| POST /api/architect/jobs | 原始输入、上传引用、比例偏好、研究或严格模式；返回job_id |
| GET /api/architect/jobs/{id} | 阶段、需要补充的信息、错误、当前revision |
| GET /api/architect/jobs/{id}/artifacts | 构建ID、Spec哈希、五张图、NBT、校验结果 |
| POST /api/architect/jobs/{id}/revisions | 用户修改要求、基准build_id；保留旧输出 |

每个构建worker只消费校验后的Spec，调用本项目Python管线，不接受模型生成的Python或shell。主Web进程不直接承担体素生成和PNG渲染；放入可超时、限内存的独立任务。

起始配额可先采用每任务最多8张图片、每张20MB、总80MB、像素总量限制，上传解码与EXIF清理后再使用；这些是工程建议，不是已验证的本站限制。根据真实负载设置用户每日配额、排队长度、最大运行时间和重试次数。当前引擎包围盒上限100万格不是公网服务的充分资源隔离。

产物访问关联所属用户，不对私有参考图默认公开。来源URL和授权状态跟随研究包；训练授权单独记录。用户删除任务时能定位原图、派生研究和输出；日志避免保存完整原图或密钥。

当可以读取站点仓库后，再决定复用现有框架增加`/architect`，还是用独立子站。需要的最小信息是仓库/构建配置、认证与存储方式、任务运行环境，而不是立刻开启正式部署。
