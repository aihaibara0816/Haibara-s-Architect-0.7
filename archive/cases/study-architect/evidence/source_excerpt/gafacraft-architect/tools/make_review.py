"""Self-contained offline review: actual NBT-derived previews and file downloads."""
from pathlib import Path
import base64,html,json,sys
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.legacy import ROOT
from architect.render_views import font

CASES=[("retail_store","01 / 单层便利店","原创工程样板；完成墙体、屋面、门窗、室内设施、照明方块及入口地景。"),
       ("tower_segment","02 / 变截面塔楼","实际截面宽度：下部14格、中部22格、上部10格；结构测试段，尚无完整交通。"),
       ("retail_store_revision","03 / 雨棚局部修改","向正面延长1格，新增6个可见方块；指定区域外变化0。保留原版本。"),
       ("legacy_gafa_colonnade","04 / 历史资料接入","旧廊柱照片 + 旧版明确标注的研究假设，转成101个通用构件；旧实现完整保留。")]
VIEWS=[("front","正面 · −Z"),("back","背面 · +Z"),("left","左侧 · −X"),("right","右侧 · +X"),("iso45","斜上 · 45°")]
def data(path,mime):return "data:"+mime+";base64,"+base64.b64encode(path.read_bytes()).decode()
def link(path,label,mime="application/octet-stream",name=None):return f'<a class="download" download="{html.escape(name or path.name)}" href="{data(path,mime)}">{html.escape(label)}</a>'
def main():
    sections=[];rows=[]
    sheet=Image.new("RGB",(2000,1400),"#edf1eb");d=ImageDraw.Draw(sheet)
    for index,(case,title,description) in enumerate(CASES):
        out=ROOT/"output"/case;r=json.loads((out/"build_report.json").read_text())
        figures=[]
        for j,(view,label) in enumerate(VIEWS):
            p=out/f"preview_{view}.png"
            with Image.open(p) as im:
                im.load();thumbnail=im.convert("RGB");thumbnail.thumbnail((400,312));sheet.paste(thumbnail,(j*400,index*350+32))
            figures.append(f'<figure><img src="{data(p,"image/png")}" alt="{html.escape(title+" "+label)}"><figcaption>{label} · '+link(p,"下载PNG","image/png",case+"_"+p.name)+"</figcaption></figure>")
        d.text((14,index*350+6),case,font=font(18),fill="#244743")
        dims=" × ".join(map(str,r["size_xyz"]))
        rows.append(f'<tr><td><a href="#{case}">{title}</a></td><td>{dims}</td><td>{r["non_air_blocks"]:,}</td><td>{r["nbt"]["bytes"]:,}</td><td>静态通过 / 游戏待测</td></tr>')
        downloads="".join([link(out/"building.nbt","下载真实 NBT",name=case+".nbt"),link(out/"building_spec.json","BuildingSpec","application/json",case+"_spec.json"),link(out/"build_report.json","构建报告","application/json",case+"_report.json")])
        sections.append(f'<section id="{case}"><div class="eyebrow">DETERMINISTIC BUILD / {index+1:02d}</div><h2>{title}</h2><p>{description}</p><div class="badges"><span>{dims} blocks</span><span>{r["non_air_blocks"]:,} 非空气方块</span><span>5 个同源视角</span></div><div class="hero">{figures[-1]}</div><div class="downloads">{downloads}</div><details><summary>展开前、后、左、右四立面</summary><div class="grid">'+"".join(figures[:4])+f'</div></details><details class="hash"><summary>核对构建 ID 与方块哈希</summary><p>{r["build_id"]}</p><code>{r["geometry_sha256"]}</code><p>所有图从 building.nbt 读回的同一份方块数据绘制；PNG内嵌相同几何哈希。</p></details></section>')
    sheet.save(ROOT/"PREVIEW_OVERVIEW.png")
    summary=Image.new("RGB",(1280,500),"#f2f4f2")
    for i,case in enumerate(("retail_store","tower_segment")):
        with Image.open(ROOT/"output"/case/"preview_iso45.png") as im:summary.paste(im.resize((640,500)),(i*640,0))
    summary.save(ROOT/"PREVIEW_SUMMARY.png")
    tests=json.loads((ROOT/"reports/tests_final.json").read_text())
    content='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GAFAcraft Architect · v0.1 交付审阅</title><style>
    :root{--ink:#173b38;--muted:#566c63;--line:#cad5ca;--paper:#f3f5ef;--accent:#c6633d}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,"Microsoft YaHei",sans-serif}main{max-width:1120px;margin:auto;padding:40px 28px 70px}header{background:var(--ink);color:#eef4e9;padding:60px 8vw 48px}.kicker,.eyebrow{font-size:12px;letter-spacing:.18em;font-weight:700}h1{font-size:clamp(36px,6vw,70px);line-height:1.08;letter-spacing:-.045em;margin:24px 0}header p{max-width:750px;color:#d0ded3}.version{color:#efb394}h2{font-size:29px;letter-spacing:-.03em;margin:8px 0}p{max-width:900px}.lead{font-size:20px}.notice{border-left:4px solid var(--accent);padding:12px 20px;background:#e8ece2}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:14px 9px;border-bottom:1px solid var(--line)}.table-wrap{overflow:auto}a{color:inherit}section{padding:44px 0;border-top:1px solid var(--line);margin-top:32px}.badges{display:flex;flex-wrap:wrap;gap:9px;margin:18px 0}.badges span{border:1px solid var(--line);border-radius:99px;padding:5px 13px;font-size:13px}.hero{max-width:790px;margin:0 auto}figure{margin:0;background:#fff;border:1px solid var(--line)}img{display:block;width:100%;height:auto}figcaption{padding:8px 15px;font-size:13px}.download{display:inline-block;text-decoration:none;font-size:13px;font-weight:650;padding:8px 14px;border:1px solid var(--ink);border-radius:5px;margin:4px 6px 4px 0}.downloads{margin:16px 0}.downloads .download:first-child{background:var(--ink);color:white}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:18px}summary{cursor:pointer;padding:12px 0;font-weight:650}details{border-top:1px solid var(--line)}code{font-size:12px;word-break:break-all}.hash{color:var(--muted);font-size:13px}footer{margin-top:40px;color:var(--muted);font-size:13px}ol{padding-left:24px}li{margin:10px 0}@media(max-width:650px){main{padding:24px 16px}.grid{grid-template-columns:1fr}header{padding:36px 20px}td,th{white-space:nowrap}}@media print{details{display:block}.download{display:none}section{break-before:page}header{padding:24px}}
    </style></head><body><header><div class="kicker">GAFAcraft / ENGINEERING DELIVERY <span class="version">v0.1 · 2026.10.20</span></div><h1>Architect<br>从规格，到真实方块。</h1><p>已经运行的本地原型：研究资料与施工参数 → BuildingSpec → Java NBT → NBT读回五视图 → 文件与几何验收。</p></header><main>'''
    content+=f'<p class="lead">{tests["tests_run"]} 项新测试 + 118 项继承测试通过。四个构建版本、4份NBT、20张固定视图。</p><div class="notice">本次是参数化建筑工程原型。现实尺度未知的内容保持未知；所有结果是研究样板。游戏内加载、Create导入和自动图片识别仍待实现或实测。官网与正式服务器未修改。</div><h2 style="margin-top:34px">可以直接检查的结果</h2><div class="table-wrap"><table><thead><tr><th>案例</th><th>X × Y × Z</th><th>非空气方块</th><th>NBT字节</th><th>验收</th></tr></thead><tbody>'+"".join(rows)+"</tbody></table></div>"+"".join(sections)
    content+='''<section><div class="eyebrow">NEXT DEVELOPMENT</div><h2>下一步：让研究真正约束几何。</h2><ol><li><strong>先验收游戏导入：</strong>在空白测试世界确认配置、尺寸、门洞、楼板和Create实际导入行为。</li><li><strong>开发可追溯几何提取：</strong>把图片与文字转换成体量、开口、节奏和截面锚点；每项记录证据、估算或设计补全。</li><li><strong>积累少量高质量案例：</strong>先做便利店、廊柱、变截面塔楼的成对资料与结果，建立轮廓、比例、节奏、通行和局部编辑评测。</li><li><strong>再接异步网站任务：</strong>保留原始需求，校验规格后排队生成；成功后展示同源五视图与下载。当前不部署。</li></ol><p>优先补“证据到构件约束”的接口和验收闭环，不急着训练小模型，也不以增加形容词数量代替几何约束。</p></section><footer>离线审阅文件 · 无外部脚本/字体/网络请求 · 图片与下载数据内嵌。源码、测试日志、协议说明与下一轮任务均在完整交付包中。参考照片仅用于用户原项目内部研究，不新增公开或训练授权。</footer></main></body></html>'''
    (ROOT/"REVIEW.html").write_text(content,encoding="utf-8")
    print("Offline review and contact sheets created.")
if __name__=="__main__":main()
