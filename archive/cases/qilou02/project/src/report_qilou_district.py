"""Portable review with real final-NBT images, downloads, a plan map and provenance."""
from pathlib import Path
import sys,json,hashlib,base64,io,html,zipfile
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1];R=ROOT/'runs'/RUN;D=ROOT/'delivery';P=ROOT/'review/previews'
D.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
sp=read(R/'Qilou02_spec.json');a=read(R/'audit.json');wc=read(R/'world_check.json');rp=read(R/'repro_check.json')
names={'Qilou02':'四角里 · 完整街区',**{b['id']:b['name']for b in sp['buildings']}}
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
programs={'Qilou02':'12 栋原创骑楼组成一个四角街坊，四条穿巷通往内院。144 × 44 × 144 格；8 栋两层、4 栋三层。日夜景、转角近景、单栋室内与剖切可分别切换。'}
for b in sp['buildings']:programs[b['id']]=b['name']+'：'+'；'.join(str(i+1)+'层 '+v for i,v in enumerate(floortext[b['id']]))+'。'
sha=hashlib.sha256((R/'Qilou02.nbt').read_bytes()).hexdigest()
assert a['pass']and wc['mismatches']==0 and all(rp['identical_replay'].values())and not rp['scope_violations']
assert sha==sp['source_nbt_sha256']==wc['source_nbt_sha256']==rp['source_nbt_sha256']
dirs={'FR':'前右','FL':'前左','BL':'后左','BR':'后右','F':'正面','R':'右侧','B':'背面','L':'左侧'}
compass={'FR':'东南','FL':'西南','BL':'西北','BR':'东北','F':'南面','R':'东面','B':'北面','L':'西面'}
shots={'top':'屋顶俯视','street':'沿街近看','arcade':'檐下通廊','section':'剖面轴测','front':'门面近看','exploded':'分层展开','inside':'首层店内','service':'后勤 / 工作区','upper':'二层使用空间','bedroom':'住家 / 客房','upper_back':'楼上后部 / 藏书档案','turn':'廊下转弯','corner_SE':'东南 · 茶楼转角','corner_SW':'西南 · 客栈转角','corner_NE':'东北 · 书局转角','corner_NW':'西北 · 邮局转角','courtyard':'树荫内院','lane':'南侧穿巷','district_south':'南侧街段放大','district_north':'北侧街段放大','district_court':'内院局部放大'}
def label(k,g):
 k=k.removesuffix('_night');ds=compass if g=='Qilou02'else dirs
 if k.startswith('exterior_'):return ds[k.split('_')[1]]+'轴测'
 if k.startswith('elevation_'):return ds[k.split('_')[1]]+'立面'
 if k.startswith('plan_'):return str(int(k[-1])+1)+'层去顶平面'
 if k.startswith('layer_'):return str(int(k[-1])+1)+'层独立轴测'
 return shots[k]
def data_image(p,width=1200,quality=81):
 im=Image.open(p).convert('RGB');im.thumbnail((width,width),Image.Resampling.LANCZOS);out=io.BytesIO();im.save(out,format='WEBP',quality=quality)
 return 'data:image/webp;base64,'+base64.b64encode(out.getvalue()).decode()
gallery={};catalog=[]
for g in names:
 group=P/(RUN+'_'+g);recs=read(group/'views_full.json');gsha=hashlib.sha256((R/(g+'.nbt')).read_bytes()).hexdigest();gallery[g]={}
 report=next(q for q in a['reports']if q['group']==g);assert report['source_nbt_sha256']==gsha and not report['errors']
 for rec in recs:
  f=group/rec['image'];assert rec['source_nbt_sha256']==gsha and hashlib.sha256(f.read_bytes()).hexdigest()==rec['sha256']
  k=rec['camera']['id'];gallery[g][k]={'src':data_image(f),'label':label(k,g),'source_nbt_sha256':gsha,'camera':rec['camera']}
 meta=read(group/'scene/scene.json');assert meta.get('texture_grid_max')in[4,6]
 catalog.append({'group':g,'source_nbt_sha256':gsha,'views':len(recs),'model_metadata':meta})
world=D/'Qilou02_World_1.21.1.zip';worlddir=D/('Qilou02_World_'+RUN)
assert (worlddir/'level.dat').exists()
with zipfile.ZipFile(world,'w',zipfile.ZIP_DEFLATED)as z:
 for f in sorted(worlddir.rglob('*')):
  if f.is_file():z.write(f,'Qilou02_World/'+str(f.relative_to(worlddir)))
spatial={'schema':'qilou-authored-block-1','mainline':'HAF 0.4','run':RUN,'case':sp,'buildings':[read(R/(g+'_spec.json'))for g in names if g!='Qilou02'],'coordinate_note':'X east, Y up, Z south. Each local model faces south and is rotated by placement.turn quarter-turns clockwise. floor_block_y is the support block, floor_y the foot level.','original_design':True,'measured_replica':False,'game':'pending','world':wc}
(D/'Qilou02_Spatial.json').write_text(json.dumps(spatial,ensure_ascii=False,indent=2))
files={g+'.nbt':base64.b64encode((R/(g+'.nbt')).read_bytes()).decode()for g in names}
for f in[world,D/'Qilou02_Spatial.json']:files[f.name]=base64.b64encode(f.read_bytes()).decode()
forms={b['id']:('双面转角'if b['kind']=='corner'else'凹阳台'if b['kind']=='classical'else'沿街店屋')+' / '+str(b['levels'])+' 层 / 面宽 '+str(b['w'])+' 格'for b in sp['buildings']}
cards='';mapkey=''
for i,b in enumerate(sp['buildings'],1):
 g=b['id'];dl=''.join('<dt>'+str(j)+' 层</dt><dd>'+v+'</dd>'for j,v in enumerate(floortext[g],1))
 cards+='<article class="card"><img loading="lazy" src="'+gallery[g]['exterior_FR']['src']+'" alt="'+names[g]+'模型"><div class="cardbody"><span class="tag">'+str(i).zfill(2)+' / '+forms[g]+'</span><h3>'+names[g]+'</h3><dl>'+dl+'</dl><button data-building="'+g+'">查看外观与室内 ↗</button></div></article>'
 mapkey+='<button data-building="'+g+'">'+str(i).zfill(2)+' '+names[g]+(' <span class="corner-badge">↱</span>'if b['kind']=='corner'else'')+'</button>'
# Schematic polygons follow the authored lot dimensions; this is not a survey drawing.
parts=['<svg class="block-map" viewBox="0 0 144 144" role="img" aria-label="四角里建筑布局，可点击建筑"><rect width="144" height="144" fill="#e4e5da"/>']
for x,z,w,d in[(9,0,12,144),(122,0,12,144),(0,9,144,12),(0,122,144,12)]:parts.append(f'<rect x="{x}" y="{z}" width="{w}" height="{d}" fill="#bdc3bc"/>')
for x,z in sp['arcade_cells']:parts.append(f'<rect x="{x}" y="{z}" width="1.02" height="1.02" fill="#fcf8e8"/>')
for al in sp['alleys']:
 x,z,X,Z=al['bounds'];parts.append(f'<rect x="{x}" y="{z}" width="{X-x}" height="{Z-z}" fill="#c9cdbf"/>')
parts.append('<rect x="54" y="54" width="34" height="34" fill="#dde3cf"/>')
for i,b in enumerate(sp['buildings'],1):
 w=b['w'];pts=[(0,3),(w,3),(w,26),(20,29),(0,29)]if b['kind']=='corner'else[(0,3),(w,3),(w,29),(0,29)]
 def xy(x,z):
  W,D=w,33
  for k in range(b['turn']):x,z=D-z,x;W,D=D,W
  return x+b['origin'][0],z+b['origin'][2]
 pts=[xy(x,z)for x,z in pts];cx,cz=xy(w/2,15)
 col={'Post':'#b68269','Bookshop':'#c4c6b0','Inn':'#cfac9b','Teahouse':'#d8bc82'}.get(b['id'],'#eee5ce')
 parts.append('<g data-building="'+b['id']+'" tabindex="0" role="button" aria-label="查看'+b['name']+'"><title>'+b['name']+'</title><polygon points="'+' '.join(str(x)+','+str(z)for x,z in pts)+'" fill="'+col+'" stroke="#617768" stroke-width=".45"/><text x="'+str(cx)+'" y="'+str(cz)+'" text-anchor="middle" dominant-baseline="middle" font-size="4" fill="#254537">'+str(i).zfill(2)+'</text></g>')
for t in sp['trees']:
 x,_,z=t['anchor'];parts.append(f'<circle cx="{x}" cy="{z}" r="2.1" fill="#7e9675"/>')
parts.append('<text x="71" y="70" text-anchor="middle" font-size="3.6" fill="#46614b">共享内院</text><text x="71" y="75" text-anchor="middle" font-size="2.6" fill="#63755e">四条穿巷连通</text><text x="139" y="7" font-size="4" text-anchor="middle" fill="#254537">北↑</text><text x="72" y="141" text-anchor="middle" font-size="3" fill="#63755e">出生点 · 面向北侧进入南街</text></svg>')
maphtml=''.join(parts)
article='https://www.lw.gov.cn/zzzs/bmdt/content/post_10956036.html';news='https://huacheng.gz-cmc.com/pages/2026/03/16/d242879e6adb40bf90236b9f31e644d6.html'
refinfo=[('enning_street','E01 · 恩宁路街段','摄影：李宁 / 荔湾区规划资源分局',article,'柱廊连续，上层立面有所变化。'),('enning_140','E02 · 恩宁路 140 号','图源署名：自摄 / 荔湾区规划资源分局',article,'凹阳台、栏杆、柱式与顶部装饰。'),('arcade','E03 · 骑楼街门夜景','摄影：陈明辉 / 荔湾区规划资源分局',article,'廊柱、街门与门头层次。'),('fuxing_interior','E04 · 富兴茶居室内','摄影：吴多 / 广州日报新花城',news,'座席组、服务、灯光和植物。')]
refs='';evidence=[];srcmeta=read(ROOT/'research/reference_images/sources.json')
for key,title,credit,url,observation in refinfo:
 p=ROOT/'research/reference_images'/(key+('.jpg'if key=='fuxing_interior'else'.png'))
 refs+='<figure><a href="'+url+'" target="_blank" rel="noopener"><img loading="lazy" src="'+data_image(p,800,82)+'" alt="'+title+'参考照片"></a><figcaption><strong>'+title+'</strong>'+observation+'<br>'+credit+'</figcaption></figure>'
 meta=next(x for x in srcmeta if x['id']==key);assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
 evidence.append({'id':title.split(' · ')[0],'title':title,'source_page':url,'source_image':meta['url'],'credit':credit,'file':'reference_images/'+p.name,'sha256':meta['sha256'],'visual_review_origin':'Qilou01; same verified image bytes reused','observation':observation})
brief={'case_id':'Qilou02','run':RUN,'parent_case':'Qilou01','scope':'Twelve authored Cantonese arcade buildings, four turning corners, four passages and one shared court','reference_records':evidence,'programs':programs,'facade_recipes':forms,'spatial_contract':'delivery/Qilou02_Spatial.json','seed_scope':sp['variation_scope'],'implementation_mapping':[{'evidence':'E01/E03','decision':'Four connected turning corners, clear public arcade and covered passage mouths','code':'build_qilou_district.py: CONFIG / arcade / assembly / alleys','validation':'arcade connectivity, entry reachability, street and corner views'},{'evidence':'E02','decision':'Separate upper facade recipes, stepped cornices, recessed balcony and grouped shutters','code':'qilou_core.py:build_shell; build_qilou_district.py:decorate','validation':'four elevations and close views'},{'evidence':'E04','decision':'Program-specific reception, reading, retail, workshop, kitchen and dwelling arrangements','code':'build_qilou_district.py:shop','validation':'per-floor approximate reach, stairs, plans, interiors'}],'view_contract':{'overall':'four equal orthographic day/night views','building':'four elevations, plans, section and exploded floors','detail':'street, all corners, arcade turn, alley, court and indoor eye-level views'},'scope_notes':['Original design, not a measured replica.','Case adapter only; no generic floorplan generator or model-weight training.','No Minecraft client execution.','Physical furniture and lighting retain recorded preview approximations.']}
(ROOT/'research/design_brief_qilou02.json').write_text(json.dumps(brief,ensure_ascii=False,indent=2))
(R/'gallery_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
data={'names':names,'programs':programs,'gallery':gallery,'files':files}
uses=sum(len(x['uses'])for x in a['reports']if x['group']!='Qilou02')
subs={'RUN':RUN,'USES':str(uses),'VIEWCOUNT':str(sum(len(x)for x in gallery.values())),'MAP':maphtml,'MAPKEY':mapkey,'CARDS':cards,'REFS':refs,'CELLS':format(wc['checked_cells'],','),'VARIATION':str(rp['changed_cells']),'SPAWN':' / '.join(map(str,wc['spawn'])),'DATA':json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'),'SCRIPT':(ROOT/'assets/qilou_district_viewer.js').read_text()}
out=(ROOT/'assets/qilou_district_report.html').read_text()
for k,v in subs.items():out=out.replace('@@'+k+'@@',v)
assert '@@'not in out
(D/'Qilou02.html').write_text(out,encoding='utf-8')
# Montage of exact model renders; no generative edits.
im=Image.new('RGB',(2200,1590),'#f4efe5');dr=ImageDraw.Draw(im);font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';ft=ImageFont.truetype(font,39);sm=ImageFont.truetype(font,22)
dr.text((35,25),'QILOU 02 / FOUR CORNERS, ONE CONNECTED BLOCK',font=ft,fill='#203c33');dr.text((37,84),'12 buildings  /  4 turning arcades  /  shared courtyard  /  Java 1.21.1',font=sm,fill='#67736a')
def paste(g,k,box,label):
 x,y,w,h=box;pic=Image.open(P/(RUN+'_'+g)/(k+'.png')).convert('RGB');pic.thumbnail((w,h-38),Image.Resampling.LANCZOS);im.paste(pic,(x+(w-pic.width)//2,y));dr.text((x+10,y+h-32),label,font=sm,fill='#203c33')
paste('Qilou02','exterior_FR',(15,135,1430,1000),'01  TWELVE PROGRAMMES / CONTINUOUS COVERED WALK')
paste('Qilou02','corner_SE',(1460,135,725,490),'02  TURNING TEA HOUSE')
paste('Qilou02','courtyard',(1460,645,725,490),'03  SHADED SHARED COURT')
paste('Qilou02','arcade',(15,1150,710,420),'04  UNDER THE ARCADE')
paste('Bookshop','upper',(745,1150,710,420),'05  READING / BOOK STORAGE')
paste('Inn','inside',(1475,1150,710,420),'06  INN / RECEPTION')
im.save(D/'Qilou02_Preview.png')
print(json.dumps({'run':RUN,'views':sum(len(x)for x in gallery.values()),'uses':uses,'html_bytes':(D/'Qilou02.html').stat().st_size,'world_bytes':world.stat().st_size,'downloads':list(files)},ensure_ascii=False))
