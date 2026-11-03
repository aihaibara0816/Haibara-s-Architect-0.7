from pathlib import Path
import sys,json,math,random,hashlib,base64,zipfile,html
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

ROOT=Path(__file__).resolve().parent
ENGINE=ROOT.parent/'RuralHAF'
sys.path[:0]=[str(ENGINE),str(ENGINE/'support')]
import rural_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
OUT=ROOT/'delivery';OUT.mkdir(exist_ok=True)
SOURCE=ENGINE/'cases/rural/runs/V4/building.nbt'
original=json.loads((ENGINE/'cases/rural/input/design.json').read_text())
source_houses={x['id']:x for x in original['buildings']}
source_entries={x['house']:x['xyz'] for x in json.loads((ENGINE/'cases/rural/input/entries.json').read_text())}
fontpath=ENGINE/'support/fonts/NotoSansCJKsc-Regular.otf'
fonts={}
def font(n):
 if n not in fonts:fonts[n]=ImageFont.truetype(str(fontpath),n)
 return fonts[n]

from layout_data import source_houses,houses,fields,roads,channels,greenhouses,packing,checks,spec,ARCHIVE,rotate
fail=checks['failures']

# Diagram renderer: new authored site plan + exact topmost block colors of existing house footprints.
S=6;MW,MD=320*S,288*S
rng=random.Random(102913)
noise=np.random.default_rng(102913).integers(-4,5,size=(288,320,1))
grass=np.clip(np.array([158,178,116])+noise,0,255).astype('uint8')
im=Image.fromarray(grass).resize((MW,MD),Image.Resampling.NEAREST).convert('RGBA');dr=ImageDraw.Draw(im)
def px(p):return tuple(round(v*S) for v in p)
def rect(p,fill,outline=None,width=1):dr.rectangle(px(p),fill=fill,outline=outline,width=width)
def line(p,fill,width):dr.line([px(v) for v in p],fill=fill,width=max(1,round(width*S)),joint='curve')
def maptext(p,txt,size=19,fill='#334334',bg=None):
 xy=px(p);ft=font(size);bb=dr.textbbox((0,0),txt,font=ft);tw=bb[2]-bb[0];th=bb[3]-bb[1]
 if bg:dr.rounded_rectangle((xy[0]-tw/2-8,xy[1]-th/2-7,xy[0]+tw/2+8,xy[1]+th/2+7),radius=5,fill=bg)
 dr.text(xy,txt,font=ft,fill=fill,anchor='mm')

# Clear soil banks enclose every field; texture and growing stage vary by contiguous field, not pixel noise.
for idx,f in enumerate(fields):
 a,b,c,d=f['bounds'];crop=f['crop'];vertical=f['rows']=='N'
 rect((a,b,c,d),'#a18b5e','#657641',2)
 pal={'wheat':('#b8a24b','#cfb953','#8a8244'),'green':('#668b42','#83a551','#51763b'),'fallow':('#987f59','#aa9269','#82704d'),'facility':('#a8ad8a','#a8ad8a','#a8ad8a'),'nursery':('#a6ac85','#a6ac85','#a6ac85')}[crop]
 rect((a+1.3,b+1.3,c-1.3,d-1.3),pal[0])
 start,end=(a+2,c-1.4) if vertical else (b+2,d-1.4)
 for rr,v in enumerate(np.arange(start,end,1.7) if crop not in ['facility','nursery'] else []):
  pts=[(v,b+1.5),(v,d-1.5)] if vertical else [(a+1.5,v),(c-1.5,v)]
  line(pts,pal[1] if rr%2 else pal[2],.48)
 # Irrigation strip spacing is a diagrammatic suggestion, not a hydrated-block simulation.
 for v in (np.arange(start+7,end,9) if crop not in ['facility','nursery'] else []):
  pts=[(v,b+1.5),(v,d-1.5)] if vertical else [(a+1.5,v),(c-1.5,v)]
  line(pts,'#839c8b',.38)
 # A field access opening connects to the bordering bank.
 gatex=(a+c)/2;rect((gatex-1.8,d-.7,gatex+1.8,d+.7),'#ac976d')

for ch in channels:
 line(ch,'#768761',2.1);line(ch,'#6b9695',1.2);line(ch,'#a9bfac',.23)
# Small shared hardstanding; dispersed homes keep only a narrow threshold.
rect((112,162,130,172),'#c9c4af','#aaa795',1)
rect((114,164,120,168),'#c3af61')
rect((123,166,130,171),'#8a9da0','#687a79',1)
for f in fields:
 if f['crop'] not in ['facility','nursery']:
  a,b,c,d=f['bounds'];maptext(((a+c)/2,(b+d)/2),f['id'],18,'#f7f5e9','#596a43ba')
for h in houses:
 a,b,c,d=h['plot'];rect((a,b,c,d),'#c2bba8' if h['kind']=='old' else '#c7c5b7')
 if h['kind'] in ['frame','brick','hybrid']:
  line([(a,b),(a+5,b)],'#9d7959',.35)
  for j in range(3):rect((a+j*1.5+.2,b+.2,a+j*1.5+1.2,b+.8),'#a76e4e')
# The same route data supplies BOTH visible paving and connectivity validation.
road_colors={'main':'#c8c6b9','lane':'#c9c4af','farm':'#b8a77c','service':'#c5c1a6','access':'#c7c3af'}
for r in roads:
 line(r['path'],'#a3a18c',r['width']+.6)
 line(r['path'],road_colors[r['kind']],r['width'])


# Greenhouse roofs: thin film gradient, repeated frame ribs, rolled/open side strips.
for g in greenhouses:
 a,b,c,d=g['bounds'];rect((a+.7,b+1,c+.7,d+1),'#6d775e')
 if g['kind']=='film':
  rect((a,b,c,d),'#a0b5a4','#718c7e',2)
  for xx in np.arange(a+.5,c-.4,.5):
   u=(xx-a)/(c-a);light=math.sin(math.pi*u)
   col=tuple(round(v+light*k) for v,k in zip((169,188,171),(57,49,61)))
   line([(xx,b+.5),(xx,d-.5)],col,.55)
  for zz in range(int(b)+2,int(d),4):line([(a+.25,zz),(c-.25,zz)],'#829f93',.23)
  line([((a+c)/2,b),((a+c)/2,d)],'#eff4e7',.45)
  for xx in [a+.5,c-.5]:line([(xx,b+.5),(xx,d-.5)],'#749c82',.45)
  rect(((a+c)/2-1,d-.4,(a+c)/2+1,d+.7),'#6a9278')
  line([((a+c)/2,d),((a+c)/2,d+.5)],'#c7c3a6',2)
 else:
  rect((a,b,c,d),'#657b61','#465b48',2)
  for xx in np.arange(a+.5,c,.7):line([(xx,b+.4),(xx,d-.4)],'#829475',.12)
  for zz in np.arange(b+.5,d,.7):line([(a+.4,zz),(c-.4,zz)],'#3e5847',.10)
  for xx in np.arange(a,c+1,6):line([(xx,b),(xx,d)],'#b0b6a3',.23)
  for zz in np.arange(b,d+1,6):line([(a,zz),(c,zz)],'#a6af9c',.23)
 maptext(((a+c)/2,(b+d)/2),g['id'],17,'#f7f7e8','#526c62cd')
for g in packing:
 a,b,c,d=g['bounds']
 if g['kind']=='open_sorting_shelter':
  rect((a+1,b+1,c+1,d+1),'#687b60');rect((a,b,c,d),'#77979a','#4b6c6b',2)
  for xx in np.arange(a,c,1):line([(xx,b),(xx,d)],'#a5b6ac',.15)
 else:
  rect((a,b,c,d),'#aaa994')
  dr.ellipse(px((a+1,b+1,c-1,d-1)),fill='#799da5',outline='#ced7c9',width=2)
maptext((276,140),'薄膜拱棚 / 棚前装运',17,'#3c594b','#e3e2cd')
maptext((273,224),'遮阳育苗棚',18,'#3c594b','#daddc2')
maptext((251,272),'分拣雨棚',16,'#3c594b','#dedec4')
maptext((290,272),'水罐',15,'#3c594b','#dedec4')


# Tree groups follow irrigation edges and the village entry, leaving farming access and gates clear.
def tree(x,z,r=2.3):
 sx,sz=px((x,z));rr=r*S
 dr.ellipse((sx-rr+4,sz-rr+6,sx+rr+7,sz+rr+9),fill='#526b445c')
 for ox,oz,scale,col in [(.4,.3,1.0,'#4d7042'),(-.4,-.2,.88,'#638246'),(-.5,-.6,.63,'#789553')]:
  cx=sx+ox*S;cy=sz+oz*S;v=rr*scale
  dr.rounded_rectangle((cx-v,cy-v,cx+v,cy+v),radius=max(2,int(v*.4)),fill=col)
for x in [22,37,53,78,97,119,143,166,193,219,243,264]:tree(x,3.7,rng.uniform(1.7,2.4))
for z in [23,42,70,93,121,168,187,218,245,270]:tree(3.9,z,rng.uniform(1.8,2.5))
for x,z,r in [(122,165,1.5),(99,93,1.7),(91,152,1.6),(213,96,1.7),(210,213,2),(96,252,1.5),(178,258,1.7)]:tree(x,z,r)
for x in [76,92,117,145,164,188,220,239,266,293]:tree(x,285,rng.uniform(1.7,2.2))

# Read the real V4 structure. Roof colors are an approximate orthographic state-box depiction.
b=load_build(SOURCE,Limits(cells=40_000_000,nodes=16_000_000));B=b.blocks
source_blocks={'V4':B,'archive':load_build(ARCHIVE,Limits(cells=40_000_000,nodes=16_000_000)).blocks}
heightmap=np.zeros((288,320),np.int16);colors={}
for h in houses:
 old=source_houses[h['id']];B=source_blocks[h['source_set']];k=h['rotation_delta'];x0,z0=old['x'],old['z']
 for xx in range(-1,old['w']+1):
  for zz in range(-1,old['d']+1):
   found=next(((yy,B[(x0+xx,yy,z0+zz)]) for yy in range(47,old['base']+2,-1) if (x0+xx,yy,z0+zz) in B),None)
   if not found:continue
   yy,st=found;rx,rz=rotate(xx,zz,old['w'],old['d'],k);nx,nz=h['x']+rx,h['z']+rz
   heightmap[nz,nx]=yy-old['base'];colors[nx,nz]=tuple(states.color(st))
shadow=Image.new('RGBA',im.size);sd=ImageDraw.Draw(shadow)
for (x,z),col in colors.items():
 hh=heightmap[z,x]
 for off in range(1,int(hh*.34)+1):sd.rectangle(px((x+off*.65,z+off,x+1+off*.65,z+1+off)),fill=(42,55,42,65))
shadow=shadow.filter(ImageFilter.GaussianBlur(1.2));im=Image.alpha_composite(im,shadow);dr=ImageDraw.Draw(im)
for (x,z),col in colors.items():
 hh=heightmap[z,x];shade=1.04
 if heightmap[z,max(0,x-1)]>hh or heightmap[max(0,z-1),x]>hh:shade=.82
 cc=tuple(max(0,min(255,round(v*shade))) for v in col)
 rect((x,z,x+1,z+1),cc)
 # Fine block joints retain a Minecraft-like scale without simulating game textures.
 if (x+z)%3==0:line([(x,z),(x+1,z)],tuple(max(0,v-9) for v in cc),.08)

status={'finished':('#3d7478','成宅'),'old':('#8a704b','旧宅'),'frame':('#b56848','框架'),'brick':('#b56848','砌筑'),'hybrid':('#b56848','续建')}
for h in houses:
 cx=h['x']+h['w']/2;cz=h['z']+h['d']/2
 co,lab=status[h['kind']];maptext((cx,cz),h['id'],19,'#ffffff',co)
 gx,gz=h['entry'];co='#3f6255'
 dr.ellipse(px((gx-.55,gz-.55,gx+.55,gz+.55)),fill=co)
maptext((160,135),'村 路',17,'#5b6259','#d4d1c3')
maptext((117,170),'共用空地',13,'#5b6259','#d3ccba')


im.convert('RGB').save(ROOT/'plan_map.png')

# A separate network view shows every rendered road and every checked door.
net=Image.new('RGB',(1280,1152),'#eff0e4');nd=ImageDraw.Draw(net)
for f in fields:
 nd.rectangle(tuple(round(v*4) for v in f['bounds']),fill='#dfe5ce',outline='#c5cfb7',width=1)
for h in houses:
 nd.rectangle((h['x']*4,h['z']*4,(h['x']+h['w'])*4,(h['z']+h['d'])*4),fill='#a7b1a3')
for r in roads:
 nd.line([(round(x*4),round(z*4)) for x,z in r['path']],fill='#376e64' if r['kind']=='main' else '#67928a',width=max(2,round(r['width']*3)),joint='curve')
for h in houses:
 x,z=h['entry'];nd.ellipse((x*4-4,z*4-4,x*4+4,z*4+4),fill='#c56540')
for g in greenhouses:
 a,b,c,d=g['bounds'];nd.rectangle((a*4,b*4,c*4,d*4),fill='#b7d4d1',outline='#56897f',width=2)
net.save(ROOT/'road_network.png')
CW,CH=2640,2160;board=Image.new('RGB',(CW,CH),'#f4f1e8');bd=ImageDraw.Draw(board)
ink='#253e35';muted='#647267'
bd.text((75,48),'田埂里',font=font(64),fill=ink)
bd.text((350,66),'18 栋 · 中间成组，田边散开 · P3',font=font(40),fill=ink)
bd.text((79,140),'8 栋村心 + 4 栋过渡 + 6 栋田边  /  保留 6 座农业棚  /  北朝上  /  320 × 288 格',font=font(26),fill=muted)
OX,OY=75,225;board.paste(im.convert('RGB'),(OX,OY));bd.rectangle((OX,OY,OX+MW,OY+MD),outline='#a1ad92',width=2)
def btxt(x,y,t,n=27,c=ink):bd.text((x,y),t,font=font(n),fill=c)
sx=2050;btxt(sx,228,'村落由密到疏',32)
bd.line((sx,290,2560,290),fill='#c8cabb',width=2)
for yy,num,title,lines in [
 (323,'01','村心保留街巷感',['8 栋围着主路成组，','4 栋在外侧形成过渡。','保留小门坪和高低差。']),
 (535,'02','田边零散落户',['6 栋分散在田边与路口，','单户、两户小组穿插菜地。','门前不再围成宽院。']),
 (747,'03','道路接成一张网',['主路、支巷与田间路闭合衔接。','18 / 18 户入口可达主路；','6 座大棚和配套区全部接入。'])]:
 btxt(sx,yy,num,24,'#a39777');btxt(sx+52,yy-5,title,31)
 for j,t in enumerate(lines):btxt(sx,yy+54+j*38,t,25,muted)
bd.line((sx,977,2560,977),fill='#c8cabb',width=2)
btxt(sx,1007,'路网核对 · 无孤立路段',28)
net_small=net.copy();net_small.thumbnail((510,459));board.paste(net_small,(sx,1060))
bd.rectangle((sx,1060,sx+net_small.width,1060+net_small.height),outline='#b8bea9',width=2)
btxt(sx,1540,'绿色为道路，橙点为住宅入口。',22,muted)
for xx,co,lab in [(sx,'#3d7478','成宅 9'),(sx+176,'#8a704b','旧宅 5'),(sx+346,'#b56848','施工 4')]:
 bd.rounded_rectangle((xx,1604,xx+22,1626),radius=3,fill=co);btxt(xx+32,1594,lab,23)
nx,ny=sx+42,1705;bd.polygon([(nx,ny),(nx-17,ny+59),(nx,ny+44),(nx+17,ny+59)],fill=ink)
btxt(nx-13,ny-45,'N',30);btxt(sx+100,1674,'主图比例 · Minecraft 格',25)
barx=sx+100;bary=1741
for i in range(4):bd.rectangle((barx+i*60,bary,barx+(i+1)*60,bary+13),fill=ink if i%2==0 else '#dadccd',outline=ink,width=1)
for i,t in enumerate(['0','10','20','30','40 格']):btxt(barx+i*60-4,bary+22,t,18,muted)
bd.line((75,1998,2560,1998),fill='#c8cabb',width=2)
btxt(75,2030,'已检查平面路网连通、18 户入口与农业设施接入；道路按同一份坐标绘制。',27)
btxt(75,2075,'布局草案，尚未写入存档；建筑使用现有 / 历史草案屋顶，R18 为房型占位，非游戏截图。',24,muted)
board.save(OUT/'Tiangengli_18_Top_Plan_P3.png',optimize=True)


# Standalone study retains P2 as the comparison and exposes a road-only view.
def uri(path,mime):return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
new=uri(OUT/'Tiangengli_18_Top_Plan_P3.png','image/png')
old=uri(ROOT.parent/'rural_plan_v2/delivery/Tiangengli_13_Top_Plan_P2.png','image/png')
network=uri(ROOT/'road_network.png','image/png')
doc="""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>田埂里 · 18栋疏密布局 P3</title><style>body{margin:0;background:#f4f1e8;color:#253e35;font:17px/1.8 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:25px}h1{font-size:32px}p{max-width:1080px}button,a.btn{padding:10px 15px;border:1px solid #a8b19c;background:#fffdf5;color:#253e35;border-radius:6px;font:inherit;cursor:pointer;text-decoration:none}button.on{background:#355e4e;color:white}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}.frame{overflow:auto;max-height:85vh;background:#e0e3d4;border:1px solid #bfc5af}img{display:block;width:100%}img.zoom{width:2640px;max-width:none}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:25px 0}.card{background:#faf8f0;padding:22px;border-radius:8px}h2{font-size:23px;margin-top:0}.note{color:#677568;font-size:15px}details{margin:25px 0;padding:18px;border:1px solid #c5cdb9;border-radius:8px}table{border-collapse:collapse;width:100%;max-width:1050px}td,th{padding:8px 12px;text-align:left;border-bottom:1px solid #ccd3c2}@media(max-width:850px){.cards{grid-template-columns:1fr}main{padding:16px}}</style><main><p class="note">田埂里布局研究 · P3 · 18栋</p><h1>中间成组，田边散开，村路相连</h1><p>把上一版集中挤在一起的房屋拆成由密到疏的几组：8 栋留在村心，4 栋在外侧过渡，6 栋散到田边与路口。住宅总数增至 18 栋；保持门前小块硬地、田块直边和 6 座农业棚。主路、村内回路、外围支路与田间路统一绘制和核对。</p><div class="toolbar"><button id="b3" class="on" onclick="show(3)">P3 · 18栋新布局</button><button id="b4" onclick="show(4)">只看连通路网</button><button id="b2" onclick="show(2)">对照 P2 · 13栋密集版</button><button onclick="document.getElementById('map').classList.toggle('zoom')">原尺寸 / 适应宽度</button><a class="btn" id="download" download="Tiangengli_18_Top_Plan_P3.png">下载俯视图</a></div><div class="frame"><img id="map" alt="田埂里18栋俯视方案"></div><div class="cards"><section class="card"><h2>疏密有层次</h2>村心 8 栋：R01、R02、R03、R05、R06、R07、R09、R10。过渡 4 栋：R04、R08、R11、R12。田边 6 栋：R13–R18。外围保留单户、两户小组与田地之间的空隙。</section><section class="card"><h2>路网已经接通</h2>所有绘制的道路表面属于同一个连通区域。18 / 18 户入口可到主路，6 / 6 座农业棚及分拣雨棚、水罐均可达。主要支路两端接回既有路网；宅门和农业设施只保留必要的短接入道。</section><section class="card"><h2>田间设施继续保留</h2>4 座薄膜拱棚、2 座遮阳育苗棚，加上棚前装运路、分拣雨棚和水罐。新增住宅与田间道路共同调整田块边界，农田仍围绕村落分布。</section></div><details open><summary>路网检查范围</summary><p>按 1/4 格分辨率对实际绘制的路面做连通检查，未发现孤立道路像素。另核对完整公路宽度没有穿入房屋主体或露地田块。入口短接入道从各栋实际转向后的入口坐标接到道路；农业作业道路允许进入对应设施地块。</p><p>这是二维布局核对，不等同于 Minecraft 中已验证的台阶、高差、雨棚净高或玩家碰撞。尚未改写世界存档。</p></details><details><summary>建筑来源与新增数量</summary><p>R01–R13 沿用现有方案的房型。R14–R17 恢复历史18栋草案中的4个房型，R18 暂借 R09 的屋顶投影作为新位置的体量占位，后续应另做立面差异。18 栋中包含 9 栋成宅、5 栋旧宅、4 栋施工状态建筑；农业棚与分拣棚不计入住宅数量。</p><p>外围零散不等于每户一个宽院；这版仍以小门坪、窄接入道、菜地和房间之间的自然空隙表达边缘地带。</p></details><p class="note">正俯视比例草案，非游戏截图。新增房屋细节与所有道路高差尚待实际建造。</p></main><script>const plans={2:'__P2__',3:'__P3__',4:'__NET__'};function show(v){document.getElementById('map').src=plans[v];[2,3,4].forEach(i=>document.getElementById('b'+i).classList.toggle('on',i===v))}document.getElementById('download').href=plans[3];show(3)</script></html>"""
doc=doc.replace('__P2__',old).replace('__P3__',new).replace('__NET__',network)
(OUT/'Tiangengli_18_Layout_Study_P3.html').write_text(doc)
with zipfile.ZipFile(OUT/'Tiangengli_18_Plan_Source_P3.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in [ROOT/'layout_spec.json',ROOT/'connectivity_checks.json',ROOT/'layout_data.py',ROOT/'make_plan.py',ROOT/'plan_map.png',ROOT/'road_network.png']:z.write(p,p.name)
 z.write(ARCHIVE,'case_sources/archived_building.nbt');z.write(ARCHIVE.parent/'params_used.json','case_sources/archived_params.json')
 z.writestr('说明.txt','P3 布局与路网数据，不是世界存档。复跑需要 Rural13_Project.zip 的 RuralHAF 工程与 V4，Pillow、NumPy；历史4栋的NBT和参数已附case_sources，放回 RuralHAF/cases/rural/runs/V0_18_superseded/building.nbt和params_used.json。对照页另需要P2俯视图。R18为已有房型占位。')
print(json.dumps({'houses':len(houses),'roads_connected':checks['road_components']==1,'reachable_doors':len(checks['reachable_houses']),'outputs':[dict(file=p.name,bytes=p.stat().st_size) for p in OUT.iterdir()]},ensure_ascii=False))
