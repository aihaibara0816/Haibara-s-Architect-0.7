# 图片下载、离线 HTML 与导出

在产出建筑资料册时读取。默认替用户完成有限参考图片下载；取得的原文件直接内嵌和导出，来源页保留作出处。不要逐站抓全量图片，不开展训练采集，不绕过登录、付费、防盗链或访问限制。

## 1. 准备显式图片清单

复制 `references/download-manifest-template.json` 为任务内的 `images.json`。每张有用的推荐图、候选图、设计参考单独记录。例：

```json
{
  "title": "指定建筑参考资料",
  "images": [
    {
      "image_id": "img-001",
      "title": "主体正面",
      "local_path": "/absolute/path/img-001.jpg",
      "image_url": "https://example.invalid/replace-with-actual-image.jpg",
      "source_page_url": "https://example.invalid/replace-with-actual-page",
      "verification_status": "大图已查看；方向未核实",
      "selection_status": "selected",
      "photographer": null,
      "license": null
    }
  ]
}
```

示例网址仅说明结构，不能写进真实交付。`image_url` 必须来自实际发现的图片链接，不能猜高分辨率后缀。`local_path` 存在时优先复用，避免重复下载；没有本地文件时省略它并填写真实 `image_url`。来源已确认但没有图片直链时保留来源页面，不伪造可下载资产。

- `image_id` 沿用报告/packet/提示词身份；不是推荐顺序编号。
- `selection_status` 为 `selected`、`candidate`、`design_reference`。真实照片与效果图、模型、AI图在正文中明确分组；效果图使用 `design_reference`，不能进入实景四槽。
- 单体的 `selected` 优先主体多视角与关键构件。纯地景、配楼、周边区域默认使用 `candidate` 并说明仅供补充；即使清晰且已下载，也不能自动补入主体图缺口。只有第⑤节说明本轮必需用途并正式入选时才设 `selected`。明确告知生成时按第⑤节图ID/顺序上传，全部图片ZIP是资料归档，不是建议把里面所有图交给模型。
- `verification_status` 由实际操作填写，脚本原样保留。文件下载成功和像素解析成功不代表模型已经看过图。实际查看后更新此字段，再重新打包。
- `photographer`、`license` 未知为 `null`。公开可取图不等于可训练或可任意再许可；导出保留署名和现有许可。
- 所有图片的原始拍摄方向、版本、拍摄日期及质量限制继续放在十节报告中。打包不自动补齐这些字段。

## 2. 下载、复用、嵌入

```bash
python3 scripts/bundle_reference_images.py \
  --report /absolute/path/report-draft.html \
  --manifest /absolute/path/images.json \
  --output /absolute/path/report.html \
  --assets-dir /absolute/path/reference-assets
```

依赖 Python 3 和 Pillow（仅核验文件类型与尺寸，不编辑图像）。现有报告的内嵌图片按原字节匹配并添加下载入口；新报告可用 `<img src="ref-image:img-001" alt="主体正面">` 占位，成功后替换为 data URI。未在正文出现但已取得的图片进入折叠素材区，不增加第十一节。

下载仅对清单中的 HTTP(S) 图片执行普通公开请求。拒绝把 HTML 登录页当图片；失败要留下具体原因，继续处理其余条目。不要用自制/AI替代图覆盖失败项。保持原字节，不重编码、裁切、放大或移除水印。需要编辑时遵循环境图像编辑规则，另设派生图 ID。

脚本产出：

1. 自包含 `report.html`，已取得图片离线可见；每图有带稳定文件名的下载按钮。
2. HTML 内的“下载全部已收录图片（ZIP）”，推荐、候选、设计参考分目录，含 `sources.json`。无需外站请求或第三方 JS 库。
3. `report.assets.json`，记录取得与失败状态、实际像素、校验和、来源及现有核验状态，用于任务核对；它不是完整 `packet.json`。

独立 ZIP 不默认额外交付，避免用户多管理文件。确有需求时从 HTML 中同一 ZIP 导出，不能重新改写图片身份或许可。

## 3. 验收与降级

- 数清“已收录 N 张”与“最终推荐 M/4”各自含义，绝不混写。四图不足仍留空，候选下载成功不构成补位。
- 断开网络后，图片仍应存在；已收录图片的显示、单图和 ZIP 下载不依赖外链。原始来源链接允许联网，功能定位仅为溯源。
- 解码单图及 ZIP 的数据，比较与下载原文件的字节/哈希、像素、MIME、文件扩展名；核对 ID、上传顺序、候选分组和水印。
- 无图片成功时不显示可点击的假下载；正文照常保留十节、提示词和失败说明。文件过大时优先移除重复候选并保留推荐图，不静默降清晰度；如必须拆册，标明每册图片范围。
- 本地检查通过不保证内置预览器允许下载。若其限制按钮操作，告知用户保存 HTML 后用浏览器打开即可从同一文件导出；有实际阻碍时可另交付独立 ZIP。
- 交付时保存到环境持久文件机制；更新既有报告要保留文件身份和并发版本保护。报告中不得残留临时工作区路径，未解析的图片占位不得伪装成已内嵌。
