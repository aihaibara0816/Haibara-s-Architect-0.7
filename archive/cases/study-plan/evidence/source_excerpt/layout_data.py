from pathlib import Path
import json,math,heapq,collections
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
ENGINE=ROOT.parent/'RuralHAF'
SOURCE=ENGINE/'cases/rural/runs/V4/building.nbt'
ARCHIVE=ENGINE/'cases/rural/runs/V0_18_superseded/building.nbt'
source_houses={h['id']:dict(h,source_set='V4',source_id=h['id']) for h in json.loads((ENGINE/'cases/rural/input/design.json').read_text())['buildings']}
archive_meta={h['id']:h for h in json.loads((ARCHIVE.parent/'params_used.json').read_text())['buildings']}
for newid,oldid in [('R14','R05'),('R15','R09'),('R16','R15'),('R17','R16')]:
 source_houses[newid]=dict(archive_meta[oldid],id=newid,source_set='archive',source_id=oldid)
source_houses['R18']=dict(source_houses['R09'],id='R18',source_id='R09',design_status='roof template placeholder; facade variation to be designed')

def rotate(x,z,w,d,k):
 for _ in range(k):x,z,w,d=d-1-z,x,d,w
 return x,z

# 8 near the village center, 4 transitional homes, 6 outer homes among the fields.
records=[
 ('R01',116,110,0,'core'),('R02',144,108,0,'core'),('R03',166,107,0,'core'),
 ('R04',173,72,0,'transition'),('R05',113,141,0,'core'),('R06',137,141,3,'core'),
 ('R07',159,142,2,'core'),('R08',214,111,0,'transition'),('R09',187,141,0,'core'),
 ('R10',109,176,0,'core'),('R11',143,180,0,'transition'),('R12',178,177,0,'transition'),
 ('R13',66,149,1,'outer'),('R14',74,88,0,'outer'),('R15',104,70,0,'outer'),
 ('R16',240,180,1,'outer'),('R17',70,221,1,'outer'),('R18',185,238,0,'outer')]
houses=[]
for ident,x,z,k,group in records:
 old=source_houses[ident];w,d=(old['d'],old['w']) if k%2 else (old['w'],old['d']);rot=(old['rotation']+k)%4
 lw,ld=(old['d'],old['w']) if old['rotation']%2 else (old['w'],old['d'])
 ex,ez=rotate(7,-1,lw,ld,old['rotation']);ex,ez=rotate(ex,ez,old['w'],old['d'],k)
 entry=[x+ex+.5,z+ez+.5];face=['N','E','S','W'][rot]
 houses.append(dict(old,id=ident,x=x,z=z,w=w,d=d,rotation=rot,rotation_delta=k,source_x=old['x'],source_z=old['z'],front=face,entry=entry,gate=entry,plot=[x-1,z-1,x+w+1,z+d+1],group=group))

field_data=[
 (12,12,63,107,'green','N'),(70,12,158,58,'wheat','E'),(165,12,230,60,'green','E'),
 (237,12,308,88,'wheat','N'),(12,116,60,132,'green','E'),(12,188,58,276,'wheat','N'),
 (98,220,129,276,'green','N'),(245,95,308,138,'facility','N'),(264,151,308,211,'green','N'),
 (238,218,308,276,'nursery','E'),(128,69,165,97,'green','E'),(68,180,103,207,'fallow','E'),
 (140,213,174,227,'green','E'),(140,239,174,276,'wheat','N'),(180,263,228,276,'green','E'),
 (217,155,235,198,'green','N'),(12,141,60,180,'green','E')]
fields=[dict(id=f'F{i+1:02}',bounds=list(p[:4]),crop=p[4],rows=p[5]) for i,p in enumerate(field_data)]
def road(i,k,w,p):return dict(id=i,kind=k,width=w,path=p)
roads=[
 road('main','main',5,[[0,136],[93,136],[103,135],[215,135],[226,143],[320,143]]),
 road('village_loop','lane',3.5,[[87,136],[87,174],[134,174],[134,205],[212,205],[212,135]]),
 road('core_cross_w','lane',3,[[134,135],[134,174]]),
 road('core_cross_e','lane',2.5,[[184.5,135],[184.5,174],[134,174]]),
 road('north_link','lane',3,[[0,110],[103,110],[103,135]]),
 road('north_farm_loop','farm',3,[[65,110],[65,64],[232,64],[232,91],[314,91],[314,143]]),
 road('north_local','lane',3,[[103,110],[103,100],[232,100],[232,91]]),
 road('east_local','lane',3,[[209,100],[209,135]]),
 road('west_lower_loop','lane',3.5,[[87,174],[64,174],[64,215],[107,215],[107,205],[134,205]]),
 road('south_loop','lane',3.5,[[134,205],[134,232],[232,232],[232,205],[212,205]]),
 road('east_field_loop','farm',3,[[232,205],[260,205],[260,143]]),
 road('south_farm','farm',3,[[0,281],[232,281],[232,232]]),
 road('west_south_link','farm',3,[[64,215],[64,281]]),
 road('south_mid_link','farm',3,[[134,232],[134,281]]),
 road('greenhouse_loading','service',3,[[247,135],[304,135],[304,143]]),
 road('nursery_front','service',3,[[232,254],[305,254]]),
 road('nursery_back','service',2.5,[[232,270],[305,270],[305,254]]),
]
channels=[[[7,7],[312,7],[312,88]],[[7,184],[58,184]],[[314,151],[314,278]],[[7,285],[314,285]],[[61,188],[61,278]],[[161,10],[161,60]]]
greenhouses=[dict(id=f'G{i+1:02}',bounds=[249+i*14,100,258+i*14,132],kind='film',ridge_height=5,rollup_sides=True) for i in range(4)]
greenhouses += [dict(id='G05',bounds=[243,230,269,249],kind='shade',ridge_height=4),dict(id='G06',bounds=[276,230,302,249],kind='shade',ridge_height=4)]
packing=[dict(id='A01',bounds=[245,260,259,267],kind='open_sorting_shelter'),dict(id='A02',bounds=[285,259,291,266],kind='water_tank_pad')]

def boxof(h):return [h['x'],h['z'],h['x']+h['w'],h['z']+h['d']]
def intersects(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
fail=[]
for i,h in enumerate(houses):
 for q in houses[:i]:
  if intersects(boxof(h),boxof(q)):fail.append(['house_overlap',h['id'],q['id']])
 for f in fields:
  if intersects(h['plot'],f['bounds']):fail.append(['plot_field_overlap',h['id'],f['id']])

# Route every door along free ground to the actual road mask. No visual-only spur lines.
K=2;W,D=320*K,288*K
obs=Image.new('1',(W,D));od=ImageDraw.Draw(obs)
for h in houses:
 a,b,c,d=boxof(h);od.rectangle((int(a*K),int(b*K),int(c*K)-1,int(d*K)-1),fill=1)
for f in fields:
 if f['crop'] not in ['facility','nursery']:
  a,b,c,d=f['bounds'];od.rectangle((a*K,b*K,c*K-1,d*K-1),fill=1)
blocked=np.array(obs)
def roadmask(rs,k):
 im=Image.new('1',(320*k,288*k));dr=ImageDraw.Draw(im)
 for r in rs:dr.line([(round(x*k),round(z*k)) for x,z in r['path']],fill=1,width=max(1,round(r['width']*k)),joint='curve')
 return np.array(im)
target=roadmask(roads,K)
def simplify(path):
 if len(path)<3:return path
 out=[path[0]]
 for a,b,c in zip(path,path[1:],path[2:]):
  if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):out.append(b)
 out.append(path[-1]);return out
def route_entry(h):
 start=tuple(round(v*K) for v in h['entry']);queue=collections.deque([start]);prev={start:None};end=None
 while queue:
  x,z=queue.popleft()
  if target[z,x]:end=(x,z);break
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   p=(x+dx,z+dz);xx,zz=p
   if not(0<=xx<W and 0<=zz<D) or p in prev or blocked[zz,xx]:continue
   prev[p]=(x,z);queue.append(p)
 if end is None:raise ValueError(('unreachable_door',h['id']))
 path=[];p=end
 while p is not None:path.append([p[0]/K,p[1]/K]);p=prev[p]
 path=simplify(path[::-1]);h['access_path']=path;return road('door_'+h['id'],'access',1.5,path)
for h in houses:roads.append(route_entry(h))
# All six greenhouse doors and both agricultural support facilities join the same graph.
service_entries=[]
for g in greenhouses:
 a,b,c,d=g['bounds'];pt=[(a+c)/2,d+.5];to=135 if g['kind']=='film' else 254
 roads.append(road('door_'+g['id'],'access',2,[pt,[pt[0],to]]));service_entries.append((g['id'],pt))
for g in packing:
 a,b,c,d=g['bounds'];pt=[(a+c)/2,d+.5];roads.append(road('door_'+g['id'],'access',2,[pt,[pt[0],270]]));service_entries.append((g['id'],pt))

# Check full public-road widths against bodies and crop parcels at quarter-block resolution.
CK=4;public_mask=roadmask([r for r in roads if r['kind'] not in ['access','service']],CK)
for ident,p in [(h['id'],boxof(h)) for h in houses]+[(f['id'],f['bounds']) for f in fields if f['crop'] not in ['facility','nursery']]:
 a,b,c,d=[round(v*CK) for v in p]
 if public_mask[b+1:d,a+1:c].any():fail.append(['road_obstruction',ident])
# Flood-fill the entire drawn road surface, not only center-line vertices.
surface=roadmask(roads,CK);visited=np.zeros_like(surface);q=collections.deque([(0,136*CK)]);visited[136*CK,0]=1
while q:
 x,z=q.popleft()
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  xx,zz=x+dx,z+dz
  if 0<=xx<320*CK and 0<=zz<288*CK and surface[zz,xx] and not visited[zz,xx]:visited[zz,xx]=1;q.append((xx,zz))
unconnected=int(np.count_nonzero(surface & ~visited))
reachable=[h['id'] for h in houses if visited[round(h['entry'][1]*CK),round(h['entry'][0]*CK)]]
service_reachable=[ident for ident,p in service_entries if visited[round(p[1]*CK),round(p[0]*CK)]]
if unconnected:fail.append(['disconnected_road_pixels',unconnected])
if len(reachable)!=18:fail.append(['door_reachability',len(reachable)])
if len(service_reachable)!=8:fail.append(['agricultural_reachability',len(service_reachable)])
checks=dict(houses=18,group_counts=dict(collections.Counter(h['group'] for h in houses)),road_components=1 if not unconnected else 'multiple',disconnected_surface_pixels=unconnected,reachable_houses=reachable,reachable_agricultural_facilities=service_reachable,failures=fail,scope='2D quarter-block road-surface connectivity and public-road clearance; no game collision claim')
(ROOT/'connectivity_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
assert not fail,fail
spec={'design_brief':{'case_id':'Tiangengli_18_layout','version':'P3','status':'proposed','scope':'Layout study only','hard_constraints':['18 residential buildings','compact center and scattered outskirts','retain six greenhouses','all road surfaces connected to the main road']},'spatial_spec':{'units':'block','coordinates':{'north':'-Z','east':'+X','up':'+Y'},'site':[320,288],'houses':houses,'fields':fields,'roads':roads,'channels':channels,'greenhouses':greenhouses,'agricultural_auxiliaries':packing},'facade_spec':{'existing':'R01–R13 retain V4 roof projection','restored':'R14–R17 use four archived draft houses','new':'R18 uses the existing R09 roof as a layout placeholder; detailed facade to be differentiated'},'validation':checks,'game_checked':False,'engine_consumed':False}
(ROOT/'layout_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2))
if __name__=='__main__':print(json.dumps(checks,ensure_ascii=False))
