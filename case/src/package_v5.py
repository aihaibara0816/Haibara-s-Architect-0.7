"""Package actual final NBT views, materials and a source-bound feedback record."""
from pathlib import Path
import json,html,base64,io,hashlib,shutil
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
from fontTools import subset
from fontTools.varLib.instancer import instantiateVariableFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables';RUN=ROOT/'runs/V5_r02';V=ROOT/'views'
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def data(p,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def e(s):return html.escape(str(s))
report=json.loads((RUN/'build_report.json').read_text());materials=json.loads((RUN/'materials.json').read_text())
assert report['status']=='pass'
names={'dirt':'泥土','stone_bricks':'石砖','moss_block':'苔藓块','iron_bars':'铁栏杆','diorite_wall':'闪长岩墙','polished_deepslate':'磨制深板岩','smooth_stone':'平滑石','smooth_stone_slab':'平滑石台阶','smooth_quartz':'平滑石英块','cyan_stained_glass':'青色染色玻璃','gray_concrete':'灰色混凝土','light_gray_concrete':'淡灰色混凝土','gray_stained_glass':'灰色染色玻璃','smooth_quartz_slab':'平滑石英台阶','light_blue_stained_glass':'淡蓝色染色玻璃','oak_leaves':'橡树树叶','water':'水源','polished_blackstone':'磨制黑石','white_concrete':'白色混凝土','sea_lantern':'海晶灯','iron_block':'铁块','oak_log':'橡木原木','red_concrete':'红色混凝土','shroomlight':'菌光体'}
CSS='''*{box-sizing:border-box}body{margin:0;background:#f2f1ea;color:#203c40;font:16px/1.85 ReviewSans,system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:42px 26px}h1{font-size:38px;line-height:1.3}h2{font-size:25px;border-top:1px solid #bcc8c2;padding-top:28px;margin-top:38px}h3{font-size:20px}a{color:#176a76}small{display:block;font-size:12px;overflow-wrap:anywhere;color:#5b716f}table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #c9d2c8;text-align:left;vertical-align:top}th{background:#dfe8df}figure{margin:24px 0;padding:18px;background:white}figure img{display:block;max-height:780px;max-width:100%;margin:auto}pre{white-space:pre-wrap;background:#e1e8df;padding:22px;font:inherit}.note{background:#e1e9de;padding:18px;border-left:4px solid #697c61}.warn{background:#f3e5d2;padding:18px;border-left:4px solid #aa7649}.gafa-bundle-image-tools small{font-family:ReviewSans,system-ui,sans-serif!important}@media(max-width:600px){main{padding:24px 14px}h1{font-size:28px}td,th{padding:6px;font-size:13px}}'''

def font_subset(text):
    target=V/'assets/ReviewSans.ttf'
    original=ROOT.parent/'canton-component-study-v01/render_assets/NotoSansSC.ttf'
    if original.exists():
        font=subset.load_font(str(original),subset.Options());sub=subset.Subsetter();sub.populate(text=text);sub.subset(font)
        font=instantiateVariableFont(font,{'wght':400},inplace=True);font.save(target)
        font.flavor='woff';font.save(V/'assets/ReviewSans.woff')
    if not target.exists():raise FileNotFoundError('Need views/assets/ReviewSans.ttf or original NotoSansSC.ttf')
    return '@font-face{font-family:ReviewSans;src:url('+data(V/'assets/ReviewSans.woff','font/woff')+') format("woff");font-weight:100 900;font-style:normal}'

def material_table():
    rows=[]
    for m in materials['materials']:
        name=names.get(m['block'].split(':')[1],m['block']);stack='水源体积，非水桶数' if m['full_stacks'] is None else f'{m["full_stacks"]} 组 + {m["remainder"]} 个'
        rows.append(f'<tr><td>{name}<small>{m["block"]}</small></td><td>{m["count"]:,}</td><td>{stack}</td></tr>')
    return '<table><thead><tr><th>材料</th><th>数量</th><th>64 个一组</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'

def main():
    OUT.mkdir(exist_ok=True);views=json.loads((V/'views.json').read_text());records=json.loads((V/'render_report.json').read_text());assert len(views)==len(records)==12
    template=(V/'src/gallery_template.html').read_text()
    research=(ROOT/'reports/research_draft.html').read_text()
    words=template+research+''.join(o['title']+o['desc'] for o in views)+''.join(names.values())+'GAFAcraft CANTON 280 V5 r02 118,566 blocks NBT 方块回读 示意材质与光照 非游戏截图 材料清单 成品放置量 水源体积 非水桶数 组 个 原图已收录下载全部图片文件来源获准版权保留'
    # Include visible strings injected later by the materials and original-image bundler.
    words+=Path(__file__).read_text()+(ROOT/'tools/bundle_reference_images.py').read_text()
    fcss=font_subset(words)
    def font(n):return ImageFont.truetype(str(V/'assets/ReviewSans.ttf'),n)
    rows=[]
    for v,r in zip(views,records):
        assert r['geometry_sha256']==report['geometry_sha256'] and r['camera']==v
        im=Image.open(V/'raw'/f'{v["id"]}.png').convert('RGB');w,h=im.size
        plate=Image.new('RGB',(w,h+190),'#122731' if v.get('night') else '#eef0e8');plate.paste(im,(0,108));d=ImageDraw.Draw(plate);ink='#e8eee3' if v.get('night') else '#23474b'
        d.text((34,12),'GAFAcraft / CANTON 280 / V5',font=font(24),fill=ink);d.text((34,47),v['title'],font=font(38),fill=ink)
        d.text((w-195,49),v['id'][:2]+' / 12',font=font(28),fill=ink)
        d.text((34,h+121),v['desc'],font=font(24),fill=ink);d.text((34,h+157),'V5_r02 · NBT 方块回读 · 示意材质与光照 · 非游戏截图',font=font(20),fill=ink)
        path=OUT/('V5_'+v['id']+'.png');info=PngImagePlugin.PngInfo();info.add_text('geometry_sha256',report['geometry_sha256']);info.add_text('camera',json.dumps(v,ensure_ascii=False))
        buf=io.BytesIO();plate.save(buf,format='PNG',pnginfo=info,optimize=True);blob=buf.getvalue();Image.open(io.BytesIO(blob)).verify()
        assert path.write_bytes(blob)==len(blob)
        Image.open(path).verify()
        thumb=plate.copy();thumb.thumbnail((420,420));buf=io.BytesIO();thumb.save(buf,format='JPEG',quality=82)
        rows.append({**v,'filename':path.name,'data':data(path),'thumbnail':'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()})
    gallery=template.replace('__FONT_CSS__',fcss).replace('__DATA__',json.dumps(rows,ensure_ascii=False).replace('</','<\\/')).replace('__GEOMETRY__',report['geometry_sha256']).replace('__NBT__',report['nbt']['sha256'])
    (OUT/'广州塔_V5_全景细节与反馈.html').write_text(gallery)
    material_html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>广州塔 V5 材料清单</title><style>'+fcss+CSS+'</style><main><h1>广州塔 V5｜材料清单</h1><p>最终 NBT 共 '+f'{materials["non_air_total"]:,} 个非空气单元；固体材料 {materials["solid_item_total"]:,} 个，水源 {materials["non_air_total"]-materials["solid_item_total"]} 单元。'+'</p><p>统计为成品方块放置量，未含原料合成、工具、损耗和脚手架。墙／栏杆连接状态合并到物品；水源数量不等于水桶需求。</p>'+material_table()+'<p>完整 NBT 与分块二选一，不重复放置。灯源、水流和碰撞尚待游戏验证。</p><small>NBT SHA256 '+report['nbt']['sha256']+'</small></main></html>'
    (OUT/'广州塔_V5_材料清单.html').write_text(material_html)
    lines=['广州塔 V5｜最终 NBT 材料清单','成品放置量；不是合成原料。水源单元不是水桶数量。','材料\t方块 ID\t数量\t64 个一组']
    for m in materials['materials']:
        stack='水源体积' if m['full_stacks'] is None else f'{m["full_stacks"]} 组 + {m["remainder"]} 个'
        lines.append(f'{names.get(m["block"].split(":")[1],m["block"])}\t{m["block"]}\t{m["count"]}\t{stack}')
    (OUT/'广州塔_V5_材料清单.txt').write_text('\n'.join(lines)+'\n')
    shutil.copy2(RUN/'materials.json',OUT/'广州塔_V5_材料清单.json')
    shutil.copy2(RUN/'canton280_plaza_v5.nbt',OUT/'GAFAcraft_Canton280_V5.nbt')
    # The ten-section report is bundled separately with original reference bytes.
    (ROOT/'reports/research_font.html').write_text(research.replace('__FONT_CSS__',fcss).replace('__CSS__',CSS).replace('__MATERIALS__',material_table()))
    dump(V/'view_manifest.json',{'build_id':'V5_r02','geometry_sha256':report['geometry_sha256'],'source_nbt_sha256':report['nbt']['sha256'],'views':[{'file':r['filename'],'sha256':sha(OUT/r['filename']),'camera':{k:v for k,v in r.items() if k not in ['data','thumbnail','filename']}} for r in rows]})
    dump(ROOT/'feedback/feedback_template.json',{'schema':'gafacraft-feedback-0.2','build_id':'V5_r02','geometry_sha256':report['geometry_sha256'],'component_id':None,'preview_id':None,'reference':None,'action':'adjust','feedback':'','status':'user_review_pending'})
    print(json.dumps({'views':len(rows),'geometry':report['geometry_sha256'],'materials':len(materials['materials'])}))

if __name__=='__main__':main()
