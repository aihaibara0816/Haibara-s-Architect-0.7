"""Concept-only triangle program. Original accepted railway is read-only."""
from pathlib import Path
import json,sys,math,hashlib
import numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'deps'),str(P/'src')]
import nbtlib as n
from link_geometry import read_connection
R=P/'runs/B03S1';B=P/'runs/B03';m=json.loads((R/'manifest.json').read_text());s=json.loads((B/'spec.json').read_text());f=n.load(B/'GuangzhouEast_Complete.nbt');off=np.array(s['variants'][0]['origin_in_station_coordinates'])
railpts=[];ground_obstacles=[]
for e in f['blocks']:
 state=f['palette'][int(e['state'])];p=np.array(e['pos'],int)+off
 if str(state['Name'])=='create:track':
  railpts.append(p+[.5,0,.5])
  for co in e.get('nbt',{}).get('Connections',[]):
   if co['Primary']:railpts.extend(read_connection(p,co,501))
 if 1<=p[1]<=7 and str(state['Name'])not in ['minecraft:air','create:fake_track']:ground_obstacles.append(p)
railpts=np.array(railpts);tree=cKDTree(railpts[:,[0,2]])
def rect(x0,z0,x1,z1):return [[x0,z0],[x1,z0],[x1,z1],[x0,z1]]
def inside(p,poly):
 x,z=p;yes=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes
zones=[
 {'id':'A','name':'松湖铁路运维大院','polygon':rect(170,92,270,232),'color':'#c7d8e2','program':['工务、电务办公','培训教室与设备试验室','小尺度连廊与维修工坊'],'height_blocks_suggested':[16,28],'character':'4–6 层办公配 1–2 层工坊；不再复制一座大列车所。','why':'靠近车站一侧，承担铁路日常管理与人员服务。'},
 {'id':'B','name':'轨道装备制造工坊','polygon':rect(315,180,440,290),'color':'#d4cfbb','program':['电控柜装配、机件加工','机械动力展示流水线','小型库房与装卸院'],'height_blocks_suggested':[10,18],'character':'两三栋有高差的厂房，管线、料台与设备院穿插。','why':'三角地较完整的腹部，最适合安排规则厂房和生产流线。'},
 {'id':'C','name':'备件库与工务料场','polygon':rect(170,286,260,405),'color':'#d4d8c6','program':['工具及备件库','轨枕、钢材、线缆盘堆场','叉车及工程车辆停放'],'height_blocks_suggested':[6,12],'character':'库房加大面积硬质操作场，不用草坪填空。','why':'连接办公大院和南侧作业区，方便调拨材料。'},
 {'id':'D','name':'乘务服务与公共食堂','polygon':rect(315,92,395,140),'color':'#e5d3bb','program':['公共食堂','乘务休息与换班','便利店和小型服务厅'],'height_blocks_suggested':[8,16],'character':'2–3 层公共建筑，门前留铺装小广场。','why':'放在北侧入口附近，服务园区人员，也能与城市联系。'},
 {'id':'E','name':'低位能源与水务设备区','polygon':rect(495,92,565,155),'color':'#cbd8d1','program':['小型配电房','泵房及消防储水罐','冷却、压缩空气设备'],'height_blocks_suggested':[4,10],'character':'低矮设备成组排列；围栏、检修路和石质铺地。','why':'利用东侧边角，靠内部道路维护；具体容量和线路以后再定。'},
 {'id':'F','name':'南端长料与工程车辆场','polygon':[[170,442],[260,442],[200,550],[170,550]],'color':'#e0cbb9','program':['长料、预制构件临时存放','小型工程车辆与拖车','未来建设备用场地'],'height_blocks_suggested':[0,6],'character':'顺着尖角收窄，以露天堆场和低棚为主。','why':'尖端不硬塞大楼，留出转弯、维护和后续调整空间。'}]
roads=[{'id':'gate','name':'北侧城市接口（待接市政路）','path':[[424,16],[424,150],[286,150],[286,410]],'width':10},
{'id':'east_service','name':'设备支路','path':[[424,150],[480,150],[480,124],[495,124]],'width':8},
{'id':'workshop','name':'工坊装卸入口','path':[[286,166],[370,166],[370,180]],'width':8},
{'id':'west_service','name':'运维与库区入口','path':[[286,260],[220,260],[220,286]],'width':8},
{'id':'south_yard','name':'南端作业支路','path':[[286,410],[215,410],[215,456]],'width':8}]
usable=[[160,72],[622,72],[640,112],[160,592]]
checks=[]
for z in zones:
 poly=z['polygon'];lo=np.min(poly,axis=0);hi=np.max(poly,axis=0);pts=[[x,q]for x in np.arange(lo[0]+.5,hi[0],2)for q in np.arange(lo[1]+.5,hi[1],2)if inside((x,q),poly)]
 assert all(inside(p,usable)for p in pts),z['id']
 d,_=tree.query(pts);assert d.min()>12,(z['id'],d.min())
 hits=[p.tolist()for p in ground_obstacles if inside((p[0]+.5,p[2]+.5),poly)]
 assert not hits,(z['id'],hits[:5])
 z['sampled_min_rail_center_distance_blocks']=round(float(d.min()),2);z['proposed_only']=True
 checks.append({'zone':z['id'],'inside_proposal_boundary':True,'no_existing_low_level_block_overlap':True,'sample_spacing_blocks':2,'min_rail_center_distance':z['sampled_min_rail_center_distance_blocks']})
# Ground-level corridor test uses proposed finished floor Y=1 and a six-block
# clearance envelope. It is not a surveyed terrain or a road built in the NBT.
def segdist(p,a,b):
 p,a,b=np.array(p,float),np.array(a,float),np.array(b,float);d=b-a;t=np.clip(np.dot(p-a,d)/np.dot(d,d),0,1);return float(np.linalg.norm(p-(a+t*d)))
roadchecks=[]
for road in roads:
 hits=[p.tolist()for p in ground_obstacles if 2<=p[1]<=7 and min(segdist([p[0]+.5,p[2]+.5],a,b)for a,b in zip(road['path'],road['path'][1:]))<road['width']/2+.71]
 assert not hits,(road['id'],hits[:5])
 roadchecks.append({'road':road['id'],'proposed_floor_y':1,'tested_clearance_y':[2,7],'existing_railway_block_obstructions':0})
proposal={'design_brief':{'name':'广州东三角地·铁路服务与轻制造片区','status':'proposed_only','units':'Minecraft blocks; not a surveyed city plan','coordinates':{'X':'east','Z':'south','Y':'up'},'hard_constraints':['B03 rail positions, curves and piers frozen','No extra track junction added','No buildings inside railway corridor','Paving dominates operational yards; greenery only in small planned pockets'],'assumptions':['Actual city roads and terrain have not been provided','Proposed flat road floor Y=1 relative to original station blueprint origin','Only campus program and parcels proposed; facades, rooms and real capacity are undecided']},'spatial_spec':{'proposal_boundary':usable,'zones':zones,'roads':roads,'north_gateway':[424,1,16],'future_city_connection':'north of E-W high-level main, beyond the current model; alignment pending city plan','greenery':'entrance shade, small courtyards and boundary planting; no continuous lawn carpet','open_land':'Areas outside parcels remain available for streets, yards and later city decisions; they are not automatically parks.'},'facade_spec':{'status':'not_designed','direction':'Modern railway compound, low workshops and utility yards; no uniform glass office park'},'validation':{'parcel_samples':checks,'road_clearance_samples':roadchecks,'scope':'Planar parcel samples and the proposed low-level road corridor against existing final B03 block geometry only. No terrain survey, building design, traffic simulation or game check.'}}
(R/'triangle_proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2));print(json.dumps({'zones':checks,'roads':roadchecks},ensure_ascii=False))
