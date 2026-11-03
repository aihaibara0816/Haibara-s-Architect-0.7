from pathlib import Path
import json,io,base64,hashlib,html,zipfile,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];RUN=sys.argv[1]if len(sys.argv)>1 else'V09';R=ROOT/'runs'/RUN;D=ROOT/'delivery';P=ROOT/'review/previews';D.mkdir(exist_ok=True)
terrain=json.loads((R/'terrain_audit.json').read_text());
sp=json.loads((R/'spec.json').read_text());a=json.loads((R/'Taisho16_audit.json').read_text());wc=json.loads((R/'world_check.json').read_text());rp=json.loads((R/'repro_check.json').read_text());brief=json.loads((ROOT/'research/design_brief_16.json').read_text())
assert not a['errors']and wc['mismatches']==0 and all(rp['identical_replay'].values())and not rp['scope_violations']
sha=hashlib.sha256((R/'Taisho16.nbt').read_bytes()).hexdigest();assert sha==sp['source_nbt_sha256']==a['source_nbt_sha256']==wc['source_nbt_sha256']
names={'Bookshop':'青葉書肆','Textile':'紺屋呉服店','Library':'櫻坂文庫','School':'櫻坂尋常学校','Clinic':'白川診療所','Sake':'松葉酒舗','Tea':'山茶屋','Photo':'光映写真師の家','Pharmacy':'白鷺薬局','Inn':'松風館','Florist':'花便り','Residence':'山手私宅','Bakery':'麦穂パン店','Post':'坂道郵便局','Workshop':'青木工房','Bath':'松の湯','Hall':'溪橋会所','Station':'櫻坂駅','Taisho16':'完整街区'}
programs={
 'Bookshop':'铜板门面书店；选书、结账、包装、二层阅读编辑与店主床组。',
 'Textile':'布料店；布匹陈列、裁衣工作台、等候，二层工作与生活。',
 'Library':'L 形公共文库带阅读翼；两层藏书、选书与阅读，铜绿色屋面和浅色檐口。',
 'School':'T 形学校带侧翼教室；两层教室、黑板、讲台、成组课桌与班级书架，中央山墙和前庭。',
 'Clinic':'诊所；一层接待、等候、洗手与药柜，二层四张病床及护理空间。',
 'Sake':'L 形酒铺与储存侧翼；桶装储存、柜台、品饮桌与街边货物。',
 'Tea':'小茶食店；点餐、糕点陈列、座席、后厨与收纳。',
 'Photo':'照相馆；等候、相册桌、背景墙与相机造型，二层工作与床。',
 'Pharmacy':'转角药局；展示、调配、服务与药柜，二层账房、库存和休息。',
 'Inn':'和洋旅馆；前台、茶歇、餐桌、后厨、盥洗，二层客房和阳台。',
 'Florist':'L 形花店与低矮种植间；高低花盆组、展示架、包花工作桌与门前植物。',
 'Residence':'L 形私宅带卧室侧翼与院界；厨房、餐桌、起居，二层私密卧室和生活收纳。',
 'Bakery':'面包房；烤炉、清洗、糕点柜台、小座席和砖烟囱。',
 'Post':'邮便局；服务、信件台、分拣桶柜、等候及楼上值班休息。',
 'Workshop':'T 形加长工房带装配翼；工具收纳、工作台、装配台、木料，屋顶采光体。',
 'Bath':'L 形公共浴场带布草后勤；更衣柜、长凳、分隔门、浴池和清洗位，独立烟囱。',
 'Hall':'公共会所；集会长桌、阅读书架、导览柜台、茶水清洗、储物与休憩座席。',
 'Station':'地方车站；售票、候车座席、站务、后侧雨棚站台与短轨道。'}
tags={'Bookshop':'铜板看板','Library':'公共文化','School':'公共教育','Clinic':'医疗配套','Sake':'商贸仓储','Tea':'低层小店','Photo':'窄面街屋','Pharmacy':'转角店面','Inn':'中型旅馆','Florist':'低层小店','Residence':'日常居住','Bakery':'生产餐饮','Post':'公共服务','Workshop':'小型生产','Bath':'公共生活','Hall':'公共集会','Station':'交通配套','Textile':'两层街屋'}
dirs={'SE':'东南','SW':'西南','NW':'西北','NE':'东北','FR':'前右','FL':'前左','BL':'后左','BR':'后右','F':'正面','R':'右侧','B':'背面','L':'左侧','S':'南面','E':'东面','N':'北面','W':'西面'}
shot={'mountain':'林中亭与鸟居','river':'河岸与砂砾浅滩','yard':'私宅侧后院','upper_street':'上街沿坡近看','slope_west':'林中鸟居与下坡','school_court':'学校入口前庭','lower_street':'下街近看','clock_square':'溪桥会所前','station_front':'车站门面','bridge_arrival':'桥上看溪谷','side_lane':'连接巷道','hero':'街区全景','top':'总平面','inside':'一层室内','upper_inside':'二层室内','front':'门面近看','platform':'站台','section':'剖切','layer_ground':'一层独立轴测','layer_roof':'屋顶独立轴测'}
def label(g,k):
 night=k.endswith('_night');v=k[:-6]if night else k
 if v.startswith('district_'):
  parts=v.split('_');n={'west':'山脚街屋与院落','school':'学校与文库组团','station':'溪桥会所与车站'}[parts[1]]+' · '+dirs[parts[2]]
 elif v.startswith(('overview_','exterior_','elevation_')):n=names[g]+' · '+dirs[v.split('_')[1]]+('轴测'if not v.startswith('elevation')else'立面')
 elif v.startswith('plan_'):n=names[g]+' · '+str(int(v[-1])+1)+'层去顶平面'
 else:n=names[g]+' · '+shot.get(v,v)
 return n
def image(path,w=1100,q=79):
 im=Image.open(path).convert('RGB');im.thumbnail((w,w),Image.Resampling.LANCZOS);b=io.BytesIO();im.save(b,format='WEBP',quality=q);return'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
gallery={};catalog=[]
for g in ['Taisho16']+[b['id']for b in sp['buildings']]:
 group=P/(RUN+'_'+g);recs=json.loads((group/'views_full.json').read_text());gsha=hashlib.sha256((R/(g+'.nbt')).read_bytes()).hexdigest();gallery[g]={}
 for rec in recs:
  assert rec['source_nbt_sha256']==gsha
  f=group/rec['image'];assert hashlib.sha256(f.read_bytes()).hexdigest()==rec['sha256'];k=rec['camera']['id']
  close=any(t in k for t in ['inside','front','platform','street','court','square','arrival','lane'])
  gallery[g][k]={'src':image(f,w=1400 if close else 1100,q=82 if close else 79),'label':label(g,k),'camera':rec['camera'],'source_nbt_sha256':gsha}
 catalog.append({'group':g,'source_nbt_sha256':gsha,'views':len(recs)})
world=D/'Taisho16_World_1.21.1.zip'
with zipfile.ZipFile(world,'w',zipfile.ZIP_DEFLATED)as z:
 for f in sorted((D/('Taisho16_World_'+RUN)).rglob('*')):
  if f.is_file():z.write(f,'Taisho16_World/'+str(f.relative_to(D/('Taisho16_World_'+RUN))))
files={g+'.nbt':base64.b64encode((R/(g+'.nbt')).read_bytes()).decode()for g in gallery}
files['Terrain_Input.nbt']=base64.b64encode((R/'Terrain_Input.nbt').read_bytes()).decode();files['Material_Recipes.json']=base64.b64encode((ROOT/'research/recipe_catalog_16.json').read_bytes()).decode()
files[world.name]=base64.b64encode(world.read_bytes()).decode();files['Taisho16_Spatial.json']=base64.b64encode((R/'spec.json').read_bytes()).decode();files['Presentation_Standard_v1.json']=base64.b64encode((ROOT/'research/presentation_standard_v1.json').read_bytes()).decode()
meta={'case':'Taisho16','run':RUN,'buildings':[]};cards='';rows=''
for i,b in enumerate(sp['buildings'],1):
 g=b['id'];aa=json.loads((R/(g+'_audit.json')).read_text());assert not aa['errors'];q=[b['entry_world'][j]+wc['world_offset'][j]for j in range(3)]
 meta['buildings'].append({'id':g,'name':names[g],'program':programs[g],'index':i,'floors':b['floors'],'world_entry':q,'size':b['size']})
 cards+='<article><img loading="lazy" src="'+gallery[g]['exterior_FR']['src']+'" alt="'+names[g]+'前右轴测"><span class="tag">'+str(i).zfill(2)+'</span><span class="tag">'+tags[g]+'</span><span class="tag">'+str(len(b['floors']))+'层使用空间</span><h3>'+names[g]+'</h3><p class="program">'+programs[g]+'</p><button data-building="'+g+'">查看这栋建筑 ↗</button></article>'
 rows+='<tr><td>'+str(i).zfill(2)+' '+names[g]+'</td><td>'+programs[g]+'</td><td>'+', '.join(map(str,q))+'</td><td><button data-file="'+g+'.nbt">NBT</button></td></tr>'
subs={'ROADMAP':image(R/'road_plan.png',w=1600,q=88),'T07':image(ROOT/'input/T07_reference.png',w=1100,q=85),'UNCHANGED':str(round(100*terrain['unchanged_columns']/(320*288),1)),'TERRAIN':image(R/'terrain_comparison.png',w=1800,q=88),'PROTECTED':str(terrain['protected_columns']),'CUT':str(terrain['cut_blocks']),'FILL':str(terrain['fill_blocks']),'CHERRY':str(sum(t[2]=='cherry' for t in terrain['trees'])),'SPRUCE':str(sum(t[2]=='spruce' for t in terrain['trees'])),'RUN':RUN,'VIEWCOUNT':str(sum(len(v)for v in gallery.values())),'CARDS':cards,'TOP':gallery['Taisho16']['top']['src'],'ROOMROWS':rows,'SPAWN':' '.join(map(str,wc['spawn'])),'ENTRIES':str(len(a['entries'])),'USES':str(a['use_points']),'STAIRS':str(len(a['stair_checks'])),'CELLS':format(wc['checked_cells'],','),'MISMATCHES':str(wc['mismatches']),'BES':str(wc['block_entities']),'PAINTINGS':str(wc['entities']),'LAYOUTCHANGES':str(len(rp['layout_changes'])),'CHANGES':format(rp['changed_cells'],','),'LONG':html.escape(brief['long_prompt']),'SHORT':html.escape(brief['short_prompt']),'HASH':sha,'GALLERY':json.dumps(gallery,ensure_ascii=False,separators=(',',':')),'META':json.dumps(meta,ensure_ascii=False,separators=(',',':')),'FILES':json.dumps(files,separators=(',',':')),'SCRIPT':(ROOT/'assets/viewer_v1.js').read_text()}
out=(ROOT/'assets/quarter_report.html').read_text()
for k,v in subs.items():out=out.replace('@@'+k+'@@',v)
assert '@@'not in out
(D/'Taisho16.html').write_text(out,encoding='utf-8');(R/'gallery_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
# Cover uses closer district and street views, with the whole layout secondary.
preview=Image.new('RGB',(1800,1240),'#e9eee4');draw=ImageDraw.Draw(preview)
def paste(g,k,box):
 im=Image.open(P/(RUN+'_'+g)/(k+'.png')).convert('RGB');im.thumbnail((box[2],box[3]));preview.paste(im,(box[0]+(box[2]-im.width)//2,box[1]+(box[3]-im.height)//2))
paste('Taisho16','overview_SE',(0,60,1200,855));paste('Taisho16','mountain',(1200,60,600,425));paste('Taisho16','river',(1200,490,600,425));paste('Taisho16','district_west_SE',(0,920,600,310));paste('Taisho16','clock_square_night',(600,920,600,310));paste('Taisho16','bridge_arrival',(1200,920,600,310))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',28);draw.text((24,15),'TAISHO16 / FOREST VALLEY / KOMOREBI',fill='#244b3b',font=font);preview.save(D/'Taisho16_Preview.png')
print(json.dumps({'html_bytes':(D/'Taisho16.html').stat().st_size,'views':sum(len(v)for v in gallery.values()),'downloads':len(files),'world_bytes':world.stat().st_size}))
