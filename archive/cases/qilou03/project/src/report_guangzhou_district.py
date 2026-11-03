"""Portable review with real final-NBT images, downloads, a plan map and provenance."""
from pathlib import Path
import sys,json,hashlib,base64,io,html,zipfile
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1];R=ROOT/'runs'/RUN;D=ROOT/'delivery';P=ROOT/'review/previews'
D.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
sp=read(R/'Qilou03_spec.json');a=read(R/'audit.json');wc=read(R/'world_check.json');rp=read(R/'repro_check.json')
names={'Qilou03':'檐下榕里 · 完整街区',**{b['id']:b['name']for b in sp['buildings']}}
floortext={
 'Post':['邮务柜台 · 写信等候 · 分拣备货','邮务办公 · 账房 · 档案'],
 'Apothecary':['药柜 · 咨询等候 · 称量','库存 · 分装 · 账房','住家 · 餐厨 · 阳台'],
 'Grain':['粮油陈列 · 计量 · 收银 · 库存','卧室 · 盥洗 · 起居 · 餐厨'],
 'Bookshop':['选书书架 · 展示 · 结账','藏书 · 阅览桌 · 窗边长座'],
 'Barber':['镜台理发位 · 等候 · 清洗','卧室 · 盥洗 · 起居 · 餐厨'],
 'Hardware':['五金陈列 · 零件 · 维修工作台','卧室 · 盥洗 · 起居 · 餐厨'],
 'Teahouse':['茶座 · 备餐 · 后厨清洗','散座 · 长座 · 茶具柜','卧室 · 餐厨 · 起居 · 阅读'],
 'Textile':['布匹陈列 · 裁剪 · 结账 · 库存','卧室 · 盥洗 · 起居 · 餐厨'],
 'Grocery':['杂货陈列 · 结账 · 备货 · 厨房','卧室 · 盥洗 · 起居 · 餐桌'],
 'Inn':['前台 · 等候 · 早餐后厨','两间客房 · 公共起居 · 盥洗','两间客房 · 公共起居 · 盥洗'],
 'Clinic':['挂号等候 · 咨询 · 清洗','休息床位 · 屏风 · 值班','卧室 · 餐厨 · 起居'],
 'Bakery':['糕点展示 · 小座席 · 烘焙备料','卧室 · 盥洗 · 起居 · 餐厨']}
for b in sp['buildings']:
 if b['family']=='village':
  p=b['program'];ground={'cafe':'点餐 · 茶座 · 后厨','retail':'货架 · 结账 · 备货','repair':'维修台 · 零件 · 收件','noodles':'面馆座席 · 配餐 · 后厨','laundry':'洗衣机组 · 折叠台 · 清洗','florist':'盆栽陈列 · 花艺台 · 包装','library':'社区阅览 · 藏书 · 共享长座','tailor':'布料 · 裁剪台 · 收件','home':'邻里共享起居 · 阅读 · 收纳'}[p]
  floors=['卧室 · 盥洗 · 餐厨 · 沙发起居'+(' · 阳台'if b['kind']=='balcony'else' · 窗边阅读') for _ in range(b['levels']-1)]
  floortext[b['id']]=[ground]+floors
programs={'Qilou03':'28 栋原创建筑：12 栋两至三层骑楼、16 栋四至六层城中村楼；244 × 58 × 216 格。主街、十字支路、丁字支路与后巷贯通。先从主街近景看两侧门面，再切换单栋与室内。'}
for b in sp['buildings']:programs[b['id']]=b['name']+'：'+'；'.join(str(i+1)+'层 '+v for i,v in enumerate(floortext[b['id']]))+'。'
sha=hashlib.sha256((R/'Qilou03.nbt').read_bytes()).hexdigest()
assert a['pass']and wc['mismatches']==0 and all(rp['identical_replay'].values())and not rp['scope_violations']
assert sha==sp['source_nbt_sha256']==wc['source_nbt_sha256']==rp['source_nbt_sha256']
dirs={'FR':'前右','FL':'前左','BL':'后左','BR':'后右','F':'正面','R':'右侧','B':'背面','L':'左侧'}
compass={'FR':'东南','FL':'西南','BL':'西北','BR':'东北','F':'南面','R':'东面','B':'北面','L':'西面'}
shots={'top':'屋顶俯视','street':'主街向东','arcade':'檐下通廊','section':'剖面轴测','front':'门面近看','exploded':'分层展开','inside':'首层店内','service':'后勤 / 工作区','upper':'二层使用空间','bedroom':'住家 / 客房','upper_back':'楼上后部 / 藏书档案','turn':'廊下转弯','corner_SE':'客栈斜切角','corner_SW':'冰室斜切角','corner_NE':'茶楼斜切角','corner_NW':'邮局斜切角','courtyard':'口袋绿地','lane':'城中村窄巷','district_south':'南侧骑楼与住宅','district_north':'北侧街段放大','district_court':'中央街口放大','street_reverse':'主街向西','crossroad':'十字路口','mixed':'骑楼与城中村交接'}
def label(k,g):
 k=k.removesuffix('_night');ds=compass if g=='Qilou03'else dirs
 if k.startswith('exterior_'):return ds[k.split('_')[1]]+'轴测'
 if k.startswith('elevation_'):return ds[k.split('_')[1]]+'立面'
 if k.startswith('plan_'):return str(int(k[-1])+1)+'层去顶平面'
 if k.startswith('layer_'):return str(int(k[-1])+1)+'层独立轴测'
 return shots[k]
def data_image(p,width=1200,quality=81):
 cache=ROOT/'review/webp_cache';cache.mkdir(exist_ok=True)
 raw=p.read_bytes();key=hashlib.sha256(raw+f'/{width}/{quality}'.encode()).hexdigest();cp=cache/(key+'.webp')
 if not cp.exists():
  im=Image.open(io.BytesIO(raw)).convert('RGB');im.thumbnail((width,width),Image.Resampling.LANCZOS);out=io.BytesIO();im.save(out,format='WEBP',quality=quality);cp.write_bytes(out.getvalue())
 return 'data:image/webp;base64,'+base64.b64encode(cp.read_bytes()).decode()
# Independent thumbnail conversions in a bounded pool; all provenance checks below remain unchanged.
from concurrent.futures import ThreadPoolExecutor
jobs=[]
for g in names:
 for rr in read(P/(RUN+'_'+g)/'views_full.json'):jobs.append((P/(RUN+'_'+g)/rr['image'],1440 if g=='Qilou03' else 1000,81 if g=='Qilou03' else 78))
with ThreadPoolExecutor(max_workers=6)as pool:list(pool.map(lambda job:data_image(*job),jobs))
gallery={};catalog=[]
for g in names:
 group=P/(RUN+'_'+g);recs=read(group/'views_full.json');gsha=hashlib.sha256((R/(g+'.nbt')).read_bytes()).hexdigest();gallery[g]={}
 report=next(q for q in a['reports']if q['group']==g);assert report['source_nbt_sha256']==gsha and not report['errors']
 for rec in recs:
  f=group/rec['image'];assert rec['source_nbt_sha256']==gsha and hashlib.sha256(f.read_bytes()).hexdigest()==rec['sha256']
  k=rec['camera']['id'];gallery[g][k]={'src':data_image(f,1440 if g=='Qilou03' else 1000,81 if g=='Qilou03' else 78),'label':label(k,g),'source_nbt_sha256':gsha,'camera':rec['camera']}
 meta=read(group/'scene/scene.json');assert meta.get('texture_grid_max')in[2,4,6]
 catalog.append({'group':g,'source_nbt_sha256':gsha,'views':len(recs),'model_metadata':meta})
world=D/'Qilou03_World_1.21.1.zip';worlddir=D/('Qilou03_World_'+RUN)
assert (worlddir/'level.dat').exists()
with zipfile.ZipFile(world,'w',zipfile.ZIP_DEFLATED)as z:
 for f in sorted(worlddir.rglob('*')):
  if f.is_file():z.write(f,'Qilou03_World/'+str(f.relative_to(worlddir)))
spatial={'schema':'guangzhou-authored-streets-1','mainline':'HAF 0.4','run':RUN,'case':sp,'buildings':[read(R/(g+'_spec.json'))for g in names if g!='Qilou03'],'coordinate_note':'X east, Y up, Z south. Each local model faces south and is rotated by placement.turn quarter-turns clockwise. floor_block_y is the support block, floor_y the foot level.','original_design':True,'measured_replica':False,'game':'pending','world':wc}
(D/'Qilou03_Spatial.json').write_text(json.dumps(spatial,ensure_ascii=False,indent=2))
files={g+'.nbt':base64.b64encode((R/(g+'.nbt')).read_bytes()).decode()for g in names}
for f in[world,D/'Qilou03_Spatial.json']:files[f.name]=base64.b64encode(f.read_bytes()).decode()
forms={b['id']:('骑楼斜切角'if b['kind']=='corner'else'骑楼凹阳台'if b['kind']=='classical'else'沿街骑楼'if b['family']=='qilou'else'住家阳台型'if b['kind']=='balcony'else'住家斜切角'if b['kind']=='splay'else'住家窗笼型')+' / '+str(b['levels'])+' 层 / 面宽 '+str(b['w'])+' 格'for b in sp['buildings']}
cards='';mapkey=''
for i,b in enumerate(sp['buildings'],1):
 g=b['id'];dl=''.join('<dt>'+str(j)+' 层</dt><dd>'+v+'</dd>'for j,v in enumerate(floortext[g],1))
 cards+='<article class="card"><img loading="lazy" src="'+gallery[g]['exterior_FR']['src']+'" alt="'+names[g]+'模型"><div class="cardbody"><span class="tag">'+str(i).zfill(2)+' / '+forms[g]+'</span><h3>'+names[g]+'</h3><dl>'+dl+'</dl><button data-building="'+g+'">查看外观与室内 ↗</button></div></article>'
 mapkey+='<button data-building="'+g+'">'+str(i).zfill(2)+' '+names[g]+(' <span class="corner-badge">↱</span>'if b['kind']=='corner'else'')+'</button>'
# A layout diagram from actual placement records; it is not a survey drawing.
parts=['<svg class="block-map" viewBox="0 0 244 216" role="img" aria-label="檐下榕里建筑布局，可点击建筑"><rect width="244" height="216" fill="#e4e5da"/>']
for rr in sp['roads']:
 x,z,X,Z=rr['bounds'];parts.append(f'<rect x="{x}" y="{z}" width="{X-x}" height="{Z-z}" fill="#8f9a96"/>')
for al in sp['alleys']:
 x,z,X,Z=al['bounds'];parts.append(f'<rect x="{x}" y="{z}" width="{X-x}" height="{Z-z}" fill="#bdc7b8"/>')
parts.append('<rect x="198" y="169" width="42" height="38" fill="#a3b694"/>')
for x,z in sp['arcade_cells']:parts.append(f'<rect x="{x}" y="{z}" width="1.03" height="1.03" fill="#fff5d8"/>')
for i,b in enumerate(sp['buildings'],1):
 w=b['w'];pts=[(0,3),(w,3),(w,22),(16,29),(0,29)]if b['kind']=='corner'else[(0,3),(w,3),(w,23),(w-6,29),(0,29)]if b['kind']=='splay'else[(0,3),(w,3),(w,29),(0,29)]
 def xy(x,z):
  W,D=w,33
  for k in range(b['turn']):x,z=D-z,x;W,D=D,W
  return x+b['origin'][0],z+b['origin'][2]
 pts=[xy(x,z)for x,z in pts];cx,cz=xy(w/2,15)
 col={'Post':'#b68269','Bookshop':'#d9cfb5','Inn':'#cfac9b','Teahouse':'#d8bc82'}.get(b['id'],'#eee1c5'if b['family']=='qilou'else'#b2c2bb')
 parts.append('<g data-building="'+b['id']+'" tabindex="0" role="button" aria-label="查看'+b['name']+'"><title>'+b['name']+'</title><polygon points="'+' '.join(str(x)+','+str(z)for x,z in pts)+'" fill="'+col+'" stroke="#617768" stroke-width=".55"/><text x="'+str(cx)+'" y="'+str(cz)+'" text-anchor="middle" dominant-baseline="middle" font-size="4.5" fill="#254537">'+str(i).zfill(2)+'</text></g>')
for t in sp['trees']:
 x,_,z=t['anchor'];parts.append(f'<circle cx="{x}" cy="{z}" r="2.5" fill="#6d8b60"/>')
parts.append('<text x="76" y="112" text-anchor="middle" font-size="3.5" fill="#fff">主街 · 东西贯通</text><text x="218" y="214" text-anchor="middle" font-size="3.5" fill="#46614b">口袋绿地</text><text x="238" y="8" font-size="5" text-anchor="middle" fill="#254537">北↑</text></svg>')
maphtml=''.join(parts)
article='https://www.lw.gov.cn/zzzs/bmdt/content/post_10956036.html';news='https://huacheng.gz-cmc.com/pages/2026/03/16/d242879e6adb40bf90236b9f31e644d6.html'
refinfo=[('enning_street','E01 · 恩宁路街段','摄影：李宁 / 荔湾区规划资源分局',article,'柱廊连续，上层立面有所变化。'),('enning_140','E02 · 恩宁路 140 号','图源署名：自摄 / 荔湾区规划资源分局',article,'凹阳台、栏杆、柱式与顶部装饰。'),('arcade','E03 · 骑楼街门夜景','摄影：陈明辉 / 荔湾区规划资源分局',article,'廊柱、街门与门头层次。'),('fuxing_interior','E04 · 富兴茶居室内','摄影：吴多 / 广州日报新花城',news,'座席组、服务、灯光和植物。')]
refs='';evidence=[];srcmeta=read(ROOT/'research/reference_images/sources.json')
for key,title,credit,url,observation in refinfo:
 p=ROOT/'research/reference_images'/(key+('.jpg'if key=='fuxing_interior'else'.png'))
 refs+='<figure><a href="'+url+'" target="_blank" rel="noopener"><img loading="lazy" src="'+data_image(p,800,82)+'" alt="'+title+'参考照片"></a><figcaption><strong>'+title+'</strong>'+observation+'<br>'+credit+'</figcaption></figure>'
 meta=next(x for x in srcmeta if x['id']==key);assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
 evidence.append({'id':title.split(' · ')[0],'title':title,'source_page':url,'source_image':meta['url'],'credit':credit,'file':'reference_images/'+p.name,'sha256':meta['sha256'],'visual_review_origin':'Qilou01; same verified image bytes reused','observation':observation})
brief={'case_id':'Qilou03','run':RUN,'parent_case':'Qilou02; Rongyinli V4 is a shape reference only','scope':'28 authored mixed Cantonese arcade and urban-village buildings connected by main streets and alleys','evidence':evidence,'decisions':[{'evidence':'E01 plus user street photo','decision':'Continuous two-sided street walls and eye-level long views','code':'build_guangzhou_district.py: CONFIG and roads','validation':'main street east/west and network reach'},{'evidence':'Rongyinli V4 actual world slice at Y81','decision':'Broader diagonal corners, carried through floor and parapet','code':'build_guangzhou_district.py: chamfer and village','validation':'four corners and floor plans'},{'evidence':'E04 and prior programme cases','decision':'Programme-specific shops and dwellings with beds, sofas, kitchens and planting','code':'qilou_recipes.py and modern_shop','validation':'per-floor function points, stairs, interiors'}],'view_contract':{'overall':'four equal day/night orthographic views','building':'four elevations, plans, section, exploded floors and interiors','street':'main street both ways, intersection, 4 corners, arcade, alley, mixed edge'},'scope_notes':['Original design, not a measured replica.','Authored topology and building massing; only declared component and planting choices are seeded.','No Minecraft client execution.','No general urban planner or model-weight training.']}
(ROOT/'research/design_brief_qilou03.json').write_text(json.dumps(brief,ensure_ascii=False,indent=2))
(R/'gallery_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
data={'names':names,'programs':programs,'gallery':gallery,'files':files}
uses=sum(len(x['uses'])for x in a['reports']if x['group']!='Qilou03')
subs={'RUN':RUN,'USES':str(uses),'STAIRS':str(sum(len(q['stairs'])for q in a['reports']if q['group']!='Qilou03')),'VIEWCOUNT':str(sum(len(x)for x in gallery.values())),'MAP':maphtml,'MAPKEY':mapkey,'CARDS':cards,'REFS':refs,'CELLS':format(wc['checked_cells'],','),'VARIATION':str(rp['changed_cells']),'SPAWN':' / '.join(map(str,wc['spawn'])),'DATA':json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'),'SCRIPT':(ROOT/'assets/guangzhou_viewer.js').read_text()}
out=(ROOT/'assets/guangzhou_report.html').read_text()
for k,v in subs.items():out=out.replace('@@'+k+'@@',v)
assert '@@'not in out
(D/'Qilou03.html').write_text(out,encoding='utf-8')
# Montage uses exact model renders, with the street view as the main image.
im=Image.new('RGB',(2200,1660),'#f4efe5');dr=ImageDraw.Draw(im);font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';ft=ImageFont.truetype(font,40);sm=ImageFont.truetype(font,22)
dr.text((35,25),'QILOU 03 / GUANGZHOU STREETS',font=ft,fill='#203c33');dr.text((37,85),'28 buildings  /  6 chamfered corners  /  arcades + urban village  /  Java 1.21.1',font=sm,fill='#67736a')
def paste(g,k,box,label):
 x,y,w,h=box;pic=Image.open(P/(RUN+'_'+g)/(k+'.png')).convert('RGB');pic.thumbnail((w,h-38),Image.Resampling.LANCZOS);im.paste(pic,(x+(w-pic.width)//2,y));dr.text((x+10,y+h-32),label,font=sm,fill='#203c33')
paste('Qilou03','street',(15,140,1430,1030),'01  MAIN STREET / CONTINUOUS FRONTAGES')
paste('Qilou03','corner_NW',(1460,140,725,510),'02  CHAMFERED POST OFFICE')
paste('Qilou03','lane',(1460,665,725,505),'03  NARROW RESIDENTIAL ALLEY')
paste('Qilou03','exterior_FR',(15,1185,950,460),'04  OPEN STREET NETWORK')
paste('V02','upper',(980,1185,590,460),'05  HOME / LIVING AND KITCHEN')
paste('Teahouse','inside',(1580,1185,605,460),'06  TEA HOUSE / DINING')
im.save(D/'Qilou03_Preview.png')
print(json.dumps({'run':RUN,'views':sum(len(x)for x in gallery.values()),'uses':uses,'html_bytes':(D/'Qilou03.html').stat().st_size,'world_bytes':world.stat().st_size,'downloads':list(files)},ensure_ascii=False))
