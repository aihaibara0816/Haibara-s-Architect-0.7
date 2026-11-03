"""Rebuild the review, materials, exact section diagram and downloadable parts."""
from pathlib import Path
import sys,json,hashlib,base64,html,shutil,zipfile,math
from collections import Counter
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from hafusion.bootstrap import CASE
from common import inspect_build,parse_state
from member_shapes import block_parts
from hafusion.qa import circulation

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def data(p,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def font(n,bold=False):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',n)

def main():
    out=ROOT/'deliverables';out.mkdir(exist_ok=True);run=ROOT/'runs/V6_r02';report=read(run/'build_report.json');validation=read(run/'validation.json');layout=read(run/'geometry_layout.json')
    nbtpaths={'V5':CASE/'runs/V5_r02/canton280_plaza_v5.nbt','V6':run/'GAFAcraft_Canton280_V6.nbt'}
    blocks={k:inspect_build.load_build(v,inspect_build.Limits(cells=16_000_000)).blocks for k,v in nbtpaths.items()}
    rows5=read(CASE/'runs/V5_r02/blocks.json')['blocks'];rows6=read(run/'blocks.json')['blocks']
    owners={k:{tuple(r[:3]):r[4] for r in rows} for k,rows in [('V5',rows5),('V6',rows6)]}
    same={}
    for name,prefix in [('outer_columns','frame.column.'),('outer_braces','frame.brace.'),('crown','crown.'),('mast','antenna')]:
        before={q:blocks['V5'][q] for q,o in owners['V5'].items() if o.startswith(prefix)};after={q:blocks['V6'][q] for q,o in owners['V6'].items() if o.startswith(prefix)}
        same[name]={'position_delta':len(before.keys()^after.keys()),'state_delta':sum(before.get(q)!=after.get(q) for q in before.keys()|after.keys())}
    ring_audit={}
    for label in ['V5','V6']:
        rr=[]
        for r in layout['rings']:
            qs={tuple([q[0]+36,q[1],q[2]+12]) for q in r['path']}
            rr.append({'id':r['id'],'missing_cells':sum(q not in blocks[label] for q in qs),'core_contacts':sum(owners[label].get(q)=='core' for q in qs)})
        ring_audit[label]={'missing_cells':sum(r['missing_cells'] for r in rr),'core_contact_cells':sum(r['core_contacts'] for r in rr),
                            'unobstructed_complete_paths':sum(r['missing_cells']==0 and r['core_contacts']==0 for r in rr),'paths':rr}
    lights={k:sum(parse_state(s)[0] in ['minecraft:sea_lantern','minecraft:shroomlight'] for s in bs.values()) for k,bs in blocks.items()}
    target6=validation['details']['circulation']['targets'];v5targets=[(t['id'],*t['feet_xyz']) for t in target6];v5targets[2]=('core_entry',64,2,42)
    route5=circulation(blocks['V5'],[128,282,232],v5targets)
    metrics={'same_coordinate_frame':True,'same_scale_and_cameras':True,'V5':{'non_air':len(blocks['V5']),'lights':lights['V5'],'ring_paths':ring_audit['V5'],'circulation':route5},
             'V6':{'non_air':len(blocks['V6']),'lights':lights['V6'],'ring_paths':ring_audit['V6'],'circulation':validation['details']['circulation']},
             'protected_components':same,'site_frozen':validation['checks']['site_states_and_ownership_frozen'],
             'difference':{k:v for k,v in validation['details']['difference'].items() if k!='changed_rows'},'core_estimated_shift':[1,-2],
             'meaning':'Engineering checks on the same source corpus. Not a new accuracy benchmark or blinded aesthetic score.'}
    (ROOT/'reports/comparison_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
    # Large side-by-side overview, retaining native rendered pixels.
    pairs=[]
    for label in ['V5','V6']:
        im=Image.open(ROOT/'previews'/label/'01_Whole_Day.png').convert('RGB');pairs.append(im)
    w,h=pairs[0].size;board=Image.new('RGB',(w*2+120,h+230),'#102b30');d=ImageDraw.Draw(board)
    for i,label in enumerate(['V5','V6']):
        x=40+i*(w+40);d.text((x,28),label+(' / preserved baseline' if i==0 else ' / HAFusion 0.1'),font=font(46,True),fill='white');d.text((x,89),f'{len(blocks[label]):,} blocks | tower 280 | exact NBT readback',font=font(28),fill='#b7d9cf');board.paste(pairs[i],(x,145))
    d.text((40,h+175),'Same cameras, scale and palette. Core clearance changed; plaza and sloped crown retained. Not in-game screenshots.',font=font(27),fill='#c5d7d8')
    board.save(out/'HAFusion_V5_V6_横向全景对比.png')
    # Exact top section diagram: colors identify component ownership, not material.
    fig=Image.new('RGB',(2280,1220),'#f3f6f5');d=ImageDraw.Draw(fig);d.text((40,24),'Y = 123 / actual NBT section',font=font(38,True),fill='#153b3e')
    colors={'core':'#bd6b54','ring':'#248c8c','column':'#324a60','brace':'#7b90a3','other':'#b7c4c5'}
    for i,label in enumerate(['V5','V6']):
        ox=70+i*1120;oz=170;step=39;minx,maxx,minz,maxz=54,79,29,50
        d.text((ox,90),label+(' / core [28.5, 28.5]' if i==0 else ' / core [29.5, 26.5] (estimated)'),font=font(26,True),fill='#153b3e')
        for x in range(minx,maxx+1):
          for z in range(minz,maxz+1):
            px,pz=ox+(x-minx)*step,oz+(z-minz)*step;d.rectangle((px,pz,px+step,pz+step),outline='#dae2e1')
            q=(x,123,z);st=blocks[label].get(q)
            if not st:continue
            own=owners[label][q];kind='core' if own=='core' or own=='lighting.core' else 'ring' if own.startswith('frame.ring') else 'column' if own.startswith('frame.column') else 'brace' if own.startswith('frame.brace') else 'other'
            for a,b,c,e,f,g in block_parts(st):d.rectangle((px+a*step,pz+c*step,px+e*step,pz+g*step),fill=colors[kind])
        d.text((ox,1065),'Ring/core overlaps: '+str(ring_audit[label]['core_contact_cells'])+' (all 46 levels)',font=font(24),fill='#38585b')
    for i,(name,color) in enumerate(colors.items()):
        x=60+i*400;d.rectangle((x,1140,x+30,1170),fill=color);d.text((x+42,1139),name,font=font(24),fill='#23484b')
    fig.save(out/'HAFusion_V5_V6_塔腰剖面对比.png')
    shutil.copy2(nbtpaths['V6'],out/'GAFAcraft_Canton280_V6.nbt')
    mats=read(run/'materials.json');lines=['广州塔 V6_r02 / HAFusion 0.1 材料清单','统计源：最终 NBT 独立回读；成品方块数量，不是合成原料。',f'非空气单元：{mats["non_air_total"]:,}；实际发光方块：{lights["V6"]}。','水源单元数量不等于水桶数量。','']
    for name,count in sorted(mats['blocks'].items(),key=lambda x:-x[1]):lines.append(f'{name}\t{count:,}\t'+('水源单元' if name=='minecraft:water' else f'{count//64} 组 + {count%64}'))
    (out/'广州塔_V6_材料与放置说明.txt').write_text('\n'.join(lines)+'\n\n放置：整体 128×282×232；若世界上界为 320，原点 Y≤38，并同时检查世界下界。首层行走面=原点+2，上层平台=原点+7。完整 NBT 与 9 个分块二选一。完整文件约 352 KiB，可能超过导入器 256 KiB 默认限制，届时使用分块。稀疏 NBT 不清除旧块，请在独立净空区测试。DataVersion=3955；游戏版本、注册表、碰撞、灯光和水更新尚未实测。\n')
    with zipfile.ZipFile(out/'广州塔_V6_分块与材料.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in sorted((run/'modules').glob('*.nbt')):z.write(f,'modules/'+f.name)
        for f in ['placement_manifest.json','materials.json']:z.write(run/f,f)
        z.write(out/'广州塔_V6_材料与放置说明.txt','材料与放置说明.txt')
    replay=read(ROOT/'reports/replay_validation.json')
    sections=[]
    views=read(ROOT/'configs/comparison_views.json')
    for v in views:
        imgs=''.join('<figure><b>'+label+'</b><a href="'+data(ROOT/'previews'/label/(v['id']+'.png'))+'" download="'+label+'_'+v['id']+'.png"><img loading="lazy" src="'+data(ROOT/'previews'/label/(v['id']+'.png'))+'"></a></figure>' for label in ['V5','V6'])
        sections.append('<section id="'+v['id']+'"><h2>'+html.escape(v['title'])+'</h2><p>'+html.escape(v.get('desc','相同相机；来自各自最终 NBT。'))+'</p><div class="pair">'+imgs+'</div><details><summary>相机与显示截断参数</summary><pre>'+html.escape(json.dumps(v,ensure_ascii=False,indent=2))+'</pre></details></section>')
    checks=''.join('<tr><td>'+html.escape(k)+'</td><td>'+('通过' if v else '未通过')+'</td></tr>' for k,v in report['checks'].items())
    table=''.join('<tr><td>'+a+'</td><td>'+str(b)+'</td><td>'+str(c)+'</td></tr>' for a,b,c in [
       ('塔体高度 / 整体尺寸','280 / 128×282×232','280 / 128×282×232'),('非空气方块',118566,118930),('实际发光方块',lights['V5'],lights['V6']),
       ('规划环梁路径缺失单元',ring_audit['V5']['missing_cells'],ring_audit['V6']['missing_cells']),('规划环梁路径与核心筒同格',ring_audit['V5']['core_contact_cells'],ring_audit['V6']['core_contact_cells']),
       ('完整且不占用核心筒的规划环路径',ring_audit['V5']['unobstructed_complete_paths'],ring_audit['V6']['unobstructed_complete_paths']),('核心筒中心（塔局部 X/Z）','28.5 / 28.5','29.5 / 26.5，估算'),
       ('广场 / 塔冠 / 天线','V5 原样','方块状态保持；广场归属亦保持'),('游戏内验收','待测','待测')])
    feedbackmeta={'run_id':'V6_r02','nbt_sha256':report['nbt']['sha256'],'engine':'HAFusion 0.1','reference_baseline_sha256':sha(nbtpaths['V5'])}
    doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HAFusion 0.1 · V5 / V6 对照</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf3f2;color:#17383e;font:16px/1.85 system-ui,"Microsoft YaHei",sans-serif}header{padding:45px 5vw;background:#123c40;color:white}header p{max-width:1000px;color:#cce0dd}h1{font-size:38px;margin:6px 0}main{max-width:1540px;margin:auto;padding:28px}section{background:white;padding:28px;margin:24px 0;border-radius:10px}h2{font-size:24px;margin-top:0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0;min-width:0}figure b{display:block;background:#214b4e;color:white;padding:8px 15px}img{width:100%;display:block}a{color:#16847b}table{border-collapse:collapse;width:100%;font-size:15px}td,th{border:1px solid #cddedb;padding:10px;text-align:left}th{background:#e4eeeb}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eff4f3;padding:18px;font-size:12px}.note{border-left:4px solid #ce9b52;padding:12px 20px;background:#fff4df}nav{position:sticky;top:0;background:#e2edebee;padding:12px 5vw;z-index:5;display:flex;flex-wrap:wrap;gap:20px}input,textarea,select{width:100%;font:inherit;padding:10px;border:1px solid #a9c1bd;border-radius:6px}textarea{min-height:110px}button{font:inherit;background:#176f67;color:white;border:0;border-radius:6px;padding:10px 20px;cursor:pointer}label{display:block;margin:12px 0}li{margin:8px 0}@media(max-width:800px){main{padding:10px}section{padding:16px}.pair{gap:5px}h1{font-size:28px}table{font-size:12px}}
</style><header><small>HAIBARA’S ARCHITECT / HAFUSION 0.1 / V6_r02</small><h1>让融合结果可以追溯、复跑和比较。</h1><p>保留 V5 与 HA0.3 原始工程，新增独立 HAFusion 工程。此次主要变化在核心筒、环梁接口和随动灯位；塔身外轮廓、斜塔冠、天线与广场保持对照基线。</p></header><nav><a href="#result">结果与差异</a><a href="#fusion">开源融合</a><a href="#01_Whole_Day">全景</a><a href="#14_Section">剖切</a><a href="#10_Whole_Night">夜景</a><a href="#checks">验证</a><a href="#feedback">反馈</a></nav><main>
<section id="result"><h2>先看这版到底改变了什么</h2><p>外框架沿用审核过的 SKP 空间走势。旧核心筒是早期固定试值，与塔腰外框架发生挤碰。HAFusion 在 ±3 格范围内搜索满足环梁/外框架/竖井约束的竖直轴线，选择位移最小的可行候选：X +1、Z −2 格。核心筒半径、3×3 竖井、塔高与总体尺度未缩放。灯位随核心筒定位，首层入口随之衔接。</p><p class="note"><b>这不是实测核心筒位置。</b> 照片支持“外部骨架与内部核心分离”的关系；具体偏移来自方块尺度下的几何可行性。它仍然是待实景校准的候选方案，不能把减少冲突写成“还原度提升”。</p><table><tr><th>同一检查口径</th><th>V5</th><th>V6</th></tr>'''+table+'''</table><p>环梁“闭合”指规划路径在最终方块中连续存在，可与柱/斜撑共用连接单元；不代表每道环是独立构件网格，更不代表结构工程验算。46 道等距、水平环的历史近似仍未恢复真实倾角和变间距。</p><img src="'''+data(out/'HAFusion_V5_V6_塔腰剖面对比.png')+'''"><p>剖面图按最终 NBT 的实际方块形状绘制。颜色仅区分构件归属；主预览沿用相同材质色表。</p></section>
<section id="fusion"><h2>HAFusion 0.1 接入了哪些开源机制</h2><table><tr><th>来源</th><th>实际采用</th><th>在本次 V6 中的作用与边界</th></tr>
<tr><td><a href="https://github.com/GaborWnuk/PlanCraft/tree/b0746140cf378d7e03b16887ef64ff9d99991f86">PlanCraft / MIT</a></td><td>原样复用 Grid、reachable、配对检查；保留 LICENSE。</td><td>对最终 NBT 的首层/平台进行 6 个目标的静态通行检查，两版均通过。外部测试地坪仅用于起点播种，不写入 NBT。不是游戏碰撞验收。其小房子编译器也再次完成现有 NBT 桥接，未拿来整体重建广州塔。</td></tr>
<tr><td><a href="https://github.com/louis-e/arnis/tree/a889f68637a18b540816fc41007a7972f7d547b4">Arnis</a></td><td>学习显式来源取舍、版本化缓存和失败回退；本地独立实现。</td><td>资料/参数/代码/坐标/年代共同参与缓存键；保留候选和估算状态。本包没有把 Arnis 整个引擎接入，也没有 GIS 或街景模型推理。</td></tr>
<tr><td><a href="https://github.com/LucasDower/ObjToSchematic/tree/b611b52c7a87cad99127908598bab019fe9e7c3f">ObjToSchematic</a></td><td>学习几何与材质分阶段；本地独立实现。</td><td>真实 V6 具有几何阶段缓存和独立材质阶段；材质替换须保持方块几何形状。几何依赖仍偏保守，不宣称任意构件都只重算自身。</td></tr>
<tr><td>HA0.3 / BuildKit</td><td>原参数协议、模型资产、NBT writer、独立 reader 保留。</td><td>BuildingSpec 参数适配器通过原 schema 测试；广州塔仍走明确的案例网格适配器，未伪装成 BuildingSpec 已通用支持任意网格。</td></tr></table><p>VGGT / Ω、自动像素分割、自动照片配准和通用审美模型均未接入。本次没有新增已安装 Skill；HAFusion 是可本地复跑的独立工程。</p></section>
'''+''.join(sections)+'''
<section id="checks"><h2>实际验证与保留的失败记录</h2><p>HAFusion 10 项单元/集成测试通过；原 HA0.3 核心与升级两组共 77 项测试通过。原始资产 639 个文件哈希复核无变化。未重新执行全套模型格式测试，不能沿用历史 244 项计数充作本轮结果。</p><p>本轮 21 个缓存阶段：热缓存全部命中；全新缓存重建与最终 NBT 字节一致；仅替换玻璃材料时几何阶段全部命中，纯占用与构件归属哈希不变。导出、独立回读与 QA 每次重新执行。第一次广泛替换灰色混凝土触及冻结广场，正确被守卫拦截，失败日志保留。</p><table><tr><th>最终 V6 检查</th><th>结果</th></tr>'''+checks+'''</table><p>本次 318 方块的 PlanCraft 小房子桥接再次通过；只是互通夹具，不是新的真实建筑案例。模型读取依赖没有重新安装，V6 复用原 SKP 对应的已校验归一化资产。</p><details><summary>缓存重建证据</summary><pre>'''+html.escape(json.dumps(replay['checks'],ensure_ascii=False,indent=2))+'''</pre></details><p class="note">尚待游戏内检查：目标版本注册表、实际碰撞与通行、流体更新、灯光和导入器行为。图片是 NBT 几何预览，不是 Minecraft 截图。当前外框架仍有阶梯感，核心筒与场地尺寸仍是研究试值，审美评价等待你的反馈。</p></section>
<section><h2>文件与放置</h2><p>完整 NBT 与 9 个分块二选一。整体 128×282×232，塔体 280 格。若世界最高 Y 排他上界为 320，放置原点 Y 不超过 38，并同时核对最低 Y。稀疏 NBT 不会清除 V5 的旧方块，应在独立净空测试区对比。</p><p><a download="GAFAcraft_Canton280_V6.nbt" href="'''+data(out/'GAFAcraft_Canton280_V6.nbt','application/octet-stream')+'''">下载完整 V6 NBT</a> · <a download="广州塔_V6_分块与材料.zip" href="'''+data(out/'广州塔_V6_分块与材料.zip','application/zip')+'''">下载 9 个分块与材料</a> · <a download="广州塔_V6_材料与放置说明.txt" href="'''+data(out/'广州塔_V6_材料与放置说明.txt','text/plain;charset=utf-8')+'''">材料与放置说明</a></p><p>原始归档：V5 原始工程（原始归档未随本公开包提供） · HA0.3 原始工程（原始归档未随本公开包提供）。HAFusion 完整工程 ZIP 另外提供，并含这两个归档的原字节备份。</p><pre>V5 NBT SHA256: '''+sha(nbtpaths['V5'])+'''\nV6 NBT SHA256: '''+sha(nbtpaths['V6'])+'''</pre></section>
<section id="feedback"><h2>下一轮反馈入口</h2><p>记录构件、视角和想改的地方，导出 JSON 后交给下一轮处理。此页面仅保存反馈，不会自动修改建筑。</p><label>构件<select id="component"><option>core</option><option>frame.rings</option><option>frame.columns</option><option>program</option><option>crown</option><option>podium</option><option>landscape</option><option>lighting.core</option></select></label><label>观察视角<select id="view">'''+''.join('<option value="'+v['id']+'">'+html.escape(v['title'])+'</option>' for v in views)+'''</select></label><label>目前的问题<textarea id="observed" placeholder="例如：塔腰仍然太密，或核心筒位置看起来偏了"></textarea></label><label>希望达到的效果<textarea id="expected"></textarea></label><button id="export">导出本轮反馈 JSON</button><p id="feedbackStatus"></p></section></main><script>
const meta='''+json.dumps(feedbackmeta)+''';document.getElementById('export').onclick=()=>{const row={...meta,component_id:document.getElementById('component').value,view_id:document.getElementById('view').value,observed:document.getElementById('observed').value,expected:document.getElementById('expected').value,created_at:new Date().toISOString(),status:'unreviewed'};const url=URL.createObjectURL(new Blob([JSON.stringify(row,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='HAFusion_V6_feedback.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);document.getElementById('feedbackStatus').textContent='已导出反馈；建筑没有被修改。';};
</script></html>'''
    (out/'HAFusion_V5_V6_对照与反馈.html').write_text(doc)
    (ROOT/'reports/review_manifest.json').write_text(json.dumps({'final_run':'V6_r02','source_nbt':report['nbt'],'files':{f.name:{'bytes':f.stat().st_size,'sha256':sha(f)} for f in out.iterdir() if f.is_file()}},ensure_ascii=False,indent=2))
    print(json.dumps({'deliverables':[(f.name,f.stat().st_size) for f in out.iterdir() if f.is_file()],'ring_audit':{k:{kk:vv for kk,vv in v.items() if kk!='paths'} for k,v in ring_audit.items()}},ensure_ascii=False))

if __name__=='__main__':main()
