"""Self-contained offline review tied to final NBT hashes, plus a technical preview sheet."""
from pathlib import Path
import sys,json,hashlib,base64,io,html,zipfile
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1];R=ROOT/'runs'/RUN;D=ROOT/'delivery';P=ROOT/'review/previews'
D.mkdir(exist_ok=True)
names={'Qilou01':'三栋组合','Grocery':'和顺杂货','Apothecary':'济安药铺','Teahouse':'榕荫茶楼'}
programs={
 'Qilou01':'三栋原创广式骑楼小样，相通的前廊接到茶楼侧廊；总尺寸 76 × 40 × 52 格。平铺测试底座，尚未扩展为完整街区。',
 'Grocery':'两层杂货铺：首层陈列、结账、备货与厨房；楼上卧室、盥洗、起居和餐桌。窄小货架、木墙裙、靠窗长座与床组分别服务经营和住家。',
 'Apothecary':'三层药铺：一层药柜、称量、咨询与等候；二层库存、分装和账房；三层居住与餐厨。立面以凹阳台、浅色柱式和栏杆区别于相邻店屋。',
 'Teahouse':'三层转角茶楼：一层茶座、备餐与清洗；二层多组茶桌、窗边长座与服务柜；三层住家、厨房、餐桌和书柜。双面骑楼廊、退切转角与圆窗形成街角识别。'}
forms={'Grocery':'朴素两层 / 面宽 15 格','Apothecary':'凹阳台三层 / 面宽 17 格','Teahouse':'退切转角三层 / 面宽 23 格'}
floortext={'Grocery':['陈列 · 结账 · 备货 · 厨房','卧室 · 盥洗 · 起居 · 餐桌'],'Apothecary':['药柜 · 咨询 · 等候 · 称量','库存 · 分装 · 账房','卧室 · 厨房 · 起居 · 阳台'],'Teahouse':['茶座 · 后厨 · 茶具服务','散座 · 长座 · 茶具柜','卧室 · 餐厨 · 起居 · 阅读']}
def read(p):return json.loads(p.read_text())
sp=read(R/'Qilou01_spec.json');a=read(R/'audit.json');wc=read(R/'world_check.json');rp=read(R/'repro_check.json')
sha=hashlib.sha256((R/'Qilou01.nbt').read_bytes()).hexdigest()
assert a['pass'] and wc['mismatches']==0 and all(rp['identical_replay'].values()) and not rp['scope_violations']
assert sha==sp['source_nbt_sha256']==wc['source_nbt_sha256']==rp['source_nbt_sha256']
dirs={'FR':'前右','FL':'前左','BL':'后左','BR':'后右','F':'正面','R':'右侧','B':'背面','L':'左侧'}
shots={'top':'屋顶俯视','street':'沿街近看','corner':'转角近看','arcade':'檐下通廊','ground_plan':'首层去顶平面','section':'剖面轴测','front':'门面近看','exploded':'分层展开','inside':'首层店内','service':'后勤 / 工作区','upper':'二层使用空间','bedroom':'住家 / 卧室'}
def label(k):
 k=k.removesuffix('_night')
 if k.startswith('exterior_'):return dirs[k.split('_')[1]]+'轴测'
 if k.startswith('elevation_'):return dirs[k.split('_')[1]]+'立面'
 if k.startswith('plan_'):return str(int(k[-1])+1)+'层去顶平面'
 if k.startswith('layer_'):return str(int(k[-1])+1)+'层独立轴测'
 return shots[k]
def data_image(p,width=1440,quality=84):
 im=Image.open(p).convert('RGB');im.thumbnail((width,width),Image.Resampling.LANCZOS);out=io.BytesIO();im.save(out,format='WEBP',quality=quality)
 return 'data:image/webp;base64,'+base64.b64encode(out.getvalue()).decode()
gallery={};catalog=[]
for g in names:
 group=P/(RUN+'_'+g);recs=read(group/'views_full.json');gsha=hashlib.sha256((R/(g+'.nbt')).read_bytes()).hexdigest();gallery[g]={}
 report=next(q for q in a['reports'] if q['group']==g);assert report['source_nbt_sha256']==gsha and not report['errors']
 for rec in recs:
  f=group/rec['image'];assert rec['source_nbt_sha256']==gsha and hashlib.sha256(f.read_bytes()).hexdigest()==rec['sha256']
  k=rec['camera']['id'];gallery[g][k]={'src':data_image(f),'label':label(k),'source_nbt_sha256':gsha,'camera':rec['camera']}
 catalog.append({'group':g,'source_nbt_sha256':gsha,'views':len(recs),'model_metadata':read(group/'scene/scene.json')})
# Keep the final world as one portable, directly playable download.
world=D/'Qilou01_World_1.21.1.zip';worlddir=D/('Qilou01_World_'+RUN)
assert (worlddir/'level.dat').exists()
with zipfile.ZipFile(world,'w',zipfile.ZIP_DEFLATED)as z:
 for f in sorted(worlddir.rglob('*')):
  if f.is_file():z.write(f,'Qilou01_World/'+str(f.relative_to(worlddir)))
spatial={'schema':'qilou-authored-sample-1','mainline':'HAF 0.4','run':RUN,'case':sp,'buildings':[read(R/(g+'_spec.json')) for g in names if g!='Qilou01'],'coordinate_note':'X east, Y up, Z south; blocks and endpoints as recorded in each module; floor_block_y is the support block; floor_y is foot level.','original_design':True,'measured_replica':False,'game':'pending','world':wc}
(D/'Qilou01_Spatial.json').write_text(json.dumps(spatial,ensure_ascii=False,indent=2))
files={g+'.nbt':base64.b64encode((R/(g+'.nbt')).read_bytes()).decode()for g in names}
for f in [world,D/'Qilou01_Spatial.json']:files[f.name]=base64.b64encode(f.read_bytes()).decode()
cards=''
for i,g in enumerate(list(names)[1:],1):
 dl=''.join('<dt>'+str(j)+' 层</dt><dd>'+v+'</dd>'for j,v in enumerate(floortext[g],1))
 cards+='<article class="card"><img loading="lazy" src="'+gallery[g]['exterior_FR']['src']+'" alt="'+names[g]+'模型"><div class="cardbody"><span class="tag">0'+str(i)+' / '+forms[g]+'</span><h3>'+names[g]+'</h3><dl>'+dl+'</dl><p>'+programs[g]+'</p><button data-building="'+g+'">进入这栋查看 ↗</button></div></article>'
article='https://www.lw.gov.cn/zzzs/bmdt/content/post_10956036.html'
news='https://huacheng.gz-cmc.com/pages/2026/03/16/d242879e6adb40bf90236b9f31e644d6.html'
refinfo=[('enning_street','E01 · 恩宁路街段','摄影：李宁 / 来源：荔湾区规划资源分局',article,'底层柱廊与上层屋面、山花之间的街景关系。'),('enning_140','E02 · 恩宁路 140 号','图源署名：自摄 / 荔湾区规划资源分局',article,'凹阳台、栏杆、浅色柱式和顶部装饰。'),('arcade','E03 · 骑楼街门夜景','摄影：陈明辉 / 来源：荔湾区规划资源分局',article,'廊柱、街门与门头；节庆装饰不用于常态归纳。'),('fuxing_interior','E04 · 富兴茶居室内','摄影：吴多 / 来源：广州日报新花城',news,'座席组、服务空间、暖光与小植物。')]
refs='';evidence=[]
srcmeta=read(ROOT/'research/reference_images/sources.json')
for key,title,credit,url,observation in refinfo:
 p=ROOT/'research/reference_images'/(key+('.jpg' if key=='fuxing_interior' else '.png'))
 refs+='<figure><a href="'+url+'" target="_blank" rel="noopener"><img loading="lazy" src="'+data_image(p,800,84)+'" alt="'+title+'参考照片"></a><figcaption><strong>'+title+'</strong>'+observation+'<br>'+credit+'</figcaption></figure>'
 meta=next(x for x in srcmeta if x['id']==key);assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
 evidence.append({'id':title.split(' · ')[0],'title':title,'source_page':url,'source_image':meta['url'],'credit':credit,'file':'reference_images/'+p.name,'sha256':meta['sha256'],'actual_visual_review':True,'observation':observation})
brief={'case_id':'Qilou01','run':RUN,'scope':'3 connected authored Cantonese arcade shop-house prototypes; no full scene and no measured replica','reference_records':evidence,'programs':programs,'facade_recipes':forms,'primary_sources':[article,news,'https://ghzyj.gz.gov.cn/gzlpc/ywpd_mcbh_mcgg/201901/11f083c3d8b243df8921d6622ec0ad1d/files/59d5ee0b0c0c40a185c881940730aee8.pdf'],'implementation_mapping':[{'evidence':'E01/E03','decision':'Four-block front arcade and side arcade, integrated shop sign, clear doorway','code':'build_qilou.py:build_shell / assembly arcade_paths','validation':'audit_qilou.py: entire arcade bounds and three reachable entrances'},{'evidence':'E02','decision':'Recessed balconies and separated column/parapet layers on Apothecary','code':'build_qilou.py:build_shell classical branch','validation':'four elevations, front close-up, balcony use points'},{'evidence':'E04','decision':'Authored tea-room groups, service sideboard and kitchen separate from guest area','code':'build_qilou.py:teahouse / interior_finish','validation':'Tea ground and upper plan, use points, interior views'}],'scope_notes':['Uses the established HAF 0.4 workflow; case version Qilou01 is not a new universal engine version.','Seeds change plant species only; three building/facade/furniture recipes are authored.','15/17/23-block widths are playability experiments, not measured historic frontage.','No actual client gameplay, medical use or historical business identity claimed.','Image rendering uses actual NBT and local official assets with recorded approximations.']}
(ROOT/'research/design_brief_qilou01.json').write_text(json.dumps(brief,ensure_ascii=False,indent=2))
(R/'gallery_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
data={'names':names,'programs':programs,'gallery':gallery,'files':files}
subs={'VIEWCOUNT':str(sum(len(x)for x in gallery.values())),'CARDS':cards,'REFS':refs,'CELLS':format(wc['checked_cells'],','),'VARIATION':str(rp['changed_cells']),'SPAWN':' / '.join(map(str,wc['spawn'])),'DATA':json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'),'SCRIPT':(ROOT/'assets/qilou_viewer.js').read_text()}
out=(ROOT/'assets/qilou_report.html').read_text().replace('Q03',RUN)
for key,val in subs.items():out=out.replace('@@'+key+'@@',val)
assert '@@' not in out
(D/'Qilou01.html').write_text(out,encoding='utf-8')
# Exact-render montage, without generative changes or invented furniture.
im=Image.new('RGB',(1800,1440),'#f4efe5');dr=ImageDraw.Draw(im)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ft=ImageFont.truetype(font,34);sm=ImageFont.truetype(font,19)
dr.text((34,24),'QILOU 01 / XI GUAN ARCADE STUDIES',font=ft,fill='#203c33')
dr.text((36,75),'3 connected prototypes  /  Java 1.21.1  /  NBT-derived previews',font=sm,fill='#67736a')
def paste(g,k,box,label):
 x,y,w,h=box;pic=Image.open(P/(RUN+'_'+g)/(k+'.png')).convert('RGB');pic.thumbnail((w,h-34),Image.Resampling.LANCZOS)
 im.paste(pic,(x+(w-pic.width)//2,y));dr.text((x+10,y+h-29),label,font=sm,fill='#203c33')
paste('Qilou01','exterior_FR',(15,122,1180,870),'01  CONTINUOUS ARCADE / DISTINCT UPPER FACADES')
paste('Qilou01','arcade',(1210,122,575,435),'02  CLEAR COVERED WALKWAY')
paste('Teahouse','upper',(1210,575,575,417),'03  TEA ROOM / TABLES + SERVICE')
paste('Grocery','inside',(15,1010,575,405),'04  GROCERY / STOCK + COUNTER')
paste('Apothecary','front',(612,1010,575,405),'05  RECESSED BALCONY')
paste('Teahouse','inside_night',(1210,1010,575,405),'06  TEA HOUSE / NIGHT')
im.save(D/'Qilou01_Preview.png')
print(json.dumps({'run':RUN,'views':sum(len(x)for x in gallery.values()),'html_bytes':(D/'Qilou01.html').stat().st_size,'world_bytes':world.stat().st_size,'downloads':list(files)},ensure_ascii=False))
