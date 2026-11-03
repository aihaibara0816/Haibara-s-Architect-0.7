"""Guangzhou CTF case adapter. Reviewed 2D evidence -> explicit shape -> HAF/NBT.
Not a general automatic photo-to-building or model-fusion implementation.
"""
from pathlib import Path
import sys,json,math,hashlib,argparse
from collections import Counter
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1]
sys.path[:0]=[str(HAF),str(HAF/'support')]
from hafusion.cache import Stages
from hafusion.lighting import room_lighting,unit
from hafusion.facade import skin_cell,NORMALS
from vendor.voxel_core import Scene,export_structure
from vendor.inspect_build import load_build,inspect,bbox,Limits
from detail_lab import states
M=states.make

def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inside(x,z,poly):
 hit=False;j=len(poly)-1
 for i,(ax,az) in enumerate(poly):
  bx,bz=poly[j]
  if ((az>z)!=(bz>z)) and x<(bx-ax)*(z-az)/(bz-az)+ax:hit=not hit
  j=i
 return hit

class Cells:
 def __init__(self,prefix):self.cells={};self.prefix=prefix
 def put(self,x,y,z,s,owner):self.cells[(int(x),int(y),int(z))]=(s,self.prefix+'.'+owner)
 def box(self,lo,hi,s,owner):
  for x in range(lo[0],hi[0]):
   for y in range(lo[1],hi[1]):
    for z in range(lo[2],hi[2]):self.put(x,y,z,s,owner)
 def out(self):return {'cells':[[*p,s,o] for p,(s,o) in sorted(self.cells.items())]}

def shape(p):
 f,t=p['frame'],p['tower'];cx,cz=f['center_xz'];scale=f['scale_blocks_per_m'];g=f['grade_y'];rows=[]
 for x in range(f['size_xyz'][0]):
  for z in range(f['size_xyz'][2]):
   mx,mz=(x+.5-cx)/scale,(z+.5-cz)/scale
   if not inside(mx,mz,t['office_polygon']):continue
   zone='office';height=t['transition_metres'][0]*scale+t['terrace_slope_blocks']*mz/32
   if inside(mx,mz,t['residential_polygon']):zone='residential';height=t['transition_metres'][1]*scale-t['terrace_slope_blocks']*mz/32
   if inside(mx,mz,t['hotel_polygon']):zone='hotel';height=t['transition_metres'][2]*scale+t['terrace_slope_blocks']*mx/32
   if inside(mx,mz,t['crown_polygon']):
    zone='crown';height=t['crown_low_height_blocks']+(t['crown_high_height_blocks']-t['crown_low_height_blocks'])*(mz+32)/64
   rows.append([x,z,g+min(265,math.ceil(height))-1,zone])
 return {'columns':rows,'source':'manually traced KPF plan boundaries; height field with nonconcentric setbacks'}

def masks(model):
 h={(x,z):top for x,z,top,zone in model['columns']}
 return h,{y:{q for q,v in h.items() if v>=y} for y in range(2,267)}

def site(p):
 g=Cells('site');ground=p['site']['ground'];sx,sy,sz=p['frame']['size_xyz']
 for x in range(5,sx-5):
  for z in range(4,sz-5):
   if x<10 and (z<13 or z>88):continue
   mat='polished_andesite' if x%12==0 or z%12==0 else 'smooth_stone'
   g.put(x,ground-1,z,M(mat),'paving')
 for x,z in p['site']['trees']:
  for xx in range(x-3,x+4):
   for zz in range(z-3,z+4):
    edge=xx in [x-3,x+3] or zz in [z-3,z+3];g.put(xx,ground,zz,M('smooth_quartz_slab' if edge else 'moss_block'),'planter')
  g.box((x,ground+1,z),(x+1,ground+6,z+1),M('oak_log'),'tree.trunk')
  for xx in range(x-3,x+4):
   for yy in range(ground+4,ground+9):
    for zz in range(z-3,z+4):
     if ((xx-x)/3.4)**2+((yy-ground-6)/2.8)**2+((zz-z)/3.4)**2<1:g.put(xx,yy,zz,M('oak_leaves'),'tree.leaves')
  g.box((x-3,ground+1,z+4),(x+3,ground+2,z+5),M('dark_oak_slab'),'bench')
 # Shallow approach and low steps; no invented subterranean rooms.
 for x in range(25,56):
  for z in range(81,84):g.put(x,ground,z,M('smooth_quartz_slab'),'entry_steps')
 for x,z in [(25,84),(55,84),(14,52),(70,52),(22,6),(58,6)]:g.put(x,ground+1,z,M('end_rod'),'path_light')
 return g.out()

def podium(p):
 g=Cells('podium');pp=p['podium'];poly=pp['polygon'];grade=p['frame']['grade_y'];top=pp['top_y'];mask={(x,z) for x in range(84) for z in range(45) if inside(x+.5,z+.5,poly)}
 for x,z in mask:
  edge=any((x+dx,z+dz) not in mask for dx,dz in NORMALS.values())
  for y in [grade,7,12,18,top]:
   atrium=30<x<48 and 17<z<30 and y<top
   if not atrium:g.put(x,y,z,M('smooth_stone_slab',type='top'),'floor')
  if not edge:continue
  for y in range(grade+1,top):
   lower=y<pp['upper_glass_y'];mat=M('gray_stained_glass_pane')
   if lower and (x+z)%4!=0:mat=M('yellow_terracotta') if (x+z)%3 else M('dark_oak_planks')
   if lower and y in [7,12,17]:mat=M('gray_stained_glass_pane')
   g.put(x,y,z,mat,'warm_skin' if lower else 'upper_glass')
   for side,(dx,dz) in NORMALS.items():
    if (x+dx,z+dz) in mask:continue
    u=x if dz else z
    if u%2==0:
     if lower:g.put(x+dx,y,z+dz,M('oak_trapdoor',open=True,facing={'north':'south','south':'north','east':'west','west':'east'}[side]),'bronze_louver')
     else:g.put(x+dx,y,z+dz,M('diorite_wall'),'upper_fin')
  if (x+z)%2==0:g.put(x,top,z,M('smooth_quartz_slab',type='top'),'coping')
 # Atrium skylight with explicit structural grid, not solid luminous roof.
 for x in range(30,49):
  for z in range(17,31):g.put(x,top,z,M('smooth_quartz_slab' if x%4==0 or z%4==0 else 'glass'),'atrium_roof')
 for x in [29,49]:g.box((x,grade,16),(x+1,top,32),M('smooth_quartz'),'atrium_side')
 # Glazed tower link and layered soffit, observed in A238172/173.
 x0,y0,z0,x1,y1,z1=pp['bridge_box']
 for x in range(x0,x1):
  for z in range(z0,z1):
   g.put(x,y0,z,M('smooth_quartz_slab',type='top'),'bridge.floor');g.put(x,y1,z,M('smooth_quartz_slab'),'bridge.ceiling')
   if (z-z0)%3==0:g.put(x,y0-1,z,M('dark_oak_trapdoor',half='top'),'bridge.soffit')
 for x in [x0,x1-1]:
  for y in range(y0+1,y1):
   for z in range(z0,z1):g.put(x,y,z,M('diorite_wall' if z%3==0 else 'glass_pane'),'bridge.skin')
 for x,z in [(25,12),(55,15),(20,32),(58,35),(31,38),(43,10)]:
  for y in [5,10,16,23]:g.put(x,y,z,M('glowstone' if (x+y)%2 else 'sea_lantern'),'light')
 return g.out()

def floor_schedule():
 # Heights read from the published design section; quantization is explicit.
 m=[0,6.25,12.5,19,25,31]
 for start,n,step in [(35.5,16,4.5),(119.5,16,4.5),(211,13,4.5),(283.5,10,4.5),(342,11,3.5),(385.5,12,3.5),(446.8,11,3.7)]:m.extend(start+i*step for i in range(n))
 m.extend([108,192,206.5,274.5,324.5,338.5,377.5,382,424,431,440,487.5,489.4,494.6,499.75])
 return sorted(set(2+int(math.floor(v*.5+.5)) for v in m if v<500))

def is_mechanical(y,p):
 height=(y-p['frame']['grade_y'])/p['frame']['scale_blocks_per_m']
 return any(lo<=height<hi for lo,hi in p['tower']['mechanical_bands_m'])

def interior(p,model):
 g=Cells('interior');h,mask=masks(model);floors=floor_schedule();rooms=[];depth=p['interior']['depth_blocks'];slab=M(p['interior']['floor_slab'],type='top')
 for i,y in enumerate(floors[:-1]):
  y1=floors[i+1];active=mask[y];inner={q for q in active if all((q[0]+dx,q[1]+dz) in active for dx,dz in NORMALS.values())}
  for x,z in inner:g.put(x,y,z,slab,'floor')
  if y<8 or is_mechanical(y+1,p) or y>=249:continue
  for side,(dx,dz) in NORMALS.items():
   us=sorted(set(x if dz else z for x,z in active))
   for u in us[2:-2:p['interior']['room_bay_blocks']]:
    vals=[z if dz else x for x,z in active if (x if dz else z)==u]
    if not vals:continue
    v=min(vals) if dx+dz<0 else max(vals);x,z=(u,v) if dz else (v,u)
    rx,rz=x-dx*depth,z-dz*depth
    if (rx,rz) not in inner:continue
    rid=f'floor.{y:03d}.{side}.bay.{u:03d}';row={'id':rid,'floor_y':y,'ceiling_y':y1,'side':side,'glass':[x,z],'back':[rx,rz],'zone':'office' if y<171 else 'residential' if y<225 else 'hotel','confidence':'synthetic window-back space'}
    rooms.append(row)
    for yy in range(y+1,y1):
     for du in [-1,0,1]:
      xx,zz=(rx+du,rz) if dz else (rx,rz+du)
      if (xx,zz) in inner:g.put(xx,yy,zz,M('gray_concrete'),rid+'.back')
    if unit(16,rid,'furniture')<.45:
     g.put(x-dx*4,y+1,z-dz*4,M('dark_oak_slab',type='bottom'),rid+'.desk')
 # A central core is retained as depth backing, not an all-solid tower fill.
 for y in range(3,250):
  active=mask[y]
  for x in range(34,46):
   for z in range(57,71):
    if (x,z) in active and (x in [34,45] or z in [57,70]):g.put(x,y,z,M('light_gray_concrete'),'core')
 out=g.out();out['rooms']=rooms;out['floor_ys']=floors;return out

def facade(p,model):
 g=Cells('facade');h,mask=masks(model);fp=p['facade'];grade=p['frame']['grade_y']
 for y in range(grade,267):
  active=mask[y]
  for x,z in active:
   sides=[side for side,(dx,dz) in NORMALS.items() if (x+dx,z+dz) not in active]
   if not sides:continue
   # Two shallow lobby portals. No missing rear envelope.
   entrance=y<grade+4 and (side_unused:=('south' in sides and 37<=x<=42 or 'north' in sides and 35<=x<=40))
   if entrance:continue
   glass='gray_stained_glass_pane';mech=is_mechanical(y,p)
   for side in sides:
    rows=skin_cell(x,y,z,side,pitch=fp['pitch_blocks'],phase=fp['phase'],glass=glass,fin=fp['fin'],fin_enabled=y>=grade+fp['lobby_clear_height'],component='facade.'+side)
    for xx,yy,zz,s,own in rows:
     # Never push a fin inside another tower tier.
     if own.endswith('.fins') and (xx,zz) in active:continue
     g.cells[(xx,yy,zz)]=(s,own)
    if mech and y%2==0:
     dx,dz=NORMALS[side];g.put(x-dx,y,z-dz,M('iron_trapdoor',half='top'),'mechanical_reveal')
   if y==grade+fp['lobby_clear_height']:
    for side in sides:
     if (x if side in ['north','south'] else z)%4==0:
      for yy in range(grade,y):g.put(x,yy,z,M('smooth_quartz'),'lobby_pier')
 # Thin entry hood with a recessed ceiling grid.
 for x in range(35,45):
  for z in range(79,83):g.put(x,grade+4,z,M('smooth_quartz_slab',type='top'),'entry_hood')
 for x in [36,39,42]:
  for z in range(79,83):g.put(x,grade+3,z,M('iron_trapdoor',half='top'),'entry_soffit')
 return g.out()

def roofs(p,model):
 g=Cells('roofs');h={ (x,z):top for x,z,top,zone in model['columns']}
 for x,z,top,zone in model['columns']:
  g.put(x,top,z,M('smooth_quartz_slab' if zone=='crown' else 'smooth_stone_slab',type='top'),'crown' if zone=='crown' else zone+'.terrace')
  # Small landscape pockets on setback terraces, no generic balcony rings.
  if zone!='crown' and (x+2*z)%7<2 and all(h.get((x+dx,z+dz),-100)<=top+1 for dx,dz in NORMALS.values()):g.put(x,top,z,M('moss_block'),zone+'.planter')
  # Explicit sloping coping: different heights are resolved cell by cell.
  if any(h.get((x+dx,z+dz),-100)<top-2 for dx,dz in NORMALS.values()):
   if zone!='crown':g.put(x,top+1,z,M('gray_stained_glass_pane'),zone+'.balustrade')
 return g.out()

def lighting(p,interior_data,model):
 g=Cells('lighting');room_records=[];h,_=masks(model);seed=p['lighting']['seed']
 for room in interior_data['rooms']:
  rid=room['id'];lp=room_lighting(seed,str(room['floor_y']),rid,room['zone']+'.'+room['side'],p['lighting']['activity']);dx,dz=NORMALS[room['side']];x,z=room['glass'];y=room['ceiling_y']-1;d=2+lp['depth']%2
  xx,zz=x-dx*d,z-dz*d
  lamp=[]
  if lp['lit'] and h.get((xx,zz),0)>y:
   g.put(xx,y,zz,M(lp['material']),rid+'.lamp');lamp=[xx,y,zz]
  room_records.append({**room,'lighting':lp,'lamp_position':lamp})
 if p['lighting']['crown_accents']:
  for x,z,top,zone in model['columns']:
   if zone=='crown' and x%4==0 and z%2==0 and any(h.get((x+dx,z+dz),0)<top-3 for dx,dz in NORMALS.values()):g.put(x,top-1,z,M('end_rod'),'crown_accent')
 out=g.out();out['rooms']=room_records;return out

def run(runid,p):
 scene=Scene(tuple(p['frame']['size_xyz']),max_cells=2_000_000)
 out=CASE/'runs'/runid
 if out.exists():raise ValueError('Use a fresh run; historical output is immutable')
 out.mkdir(parents=True)
 code_files=[Path(__file__),HAF/'hafusion/facade.py',HAF/'hafusion/lighting.py',HAF/'support/detail_lab/states.py']
 code_hash=hashlib.sha256(''.join(sha(q) for q in code_files).encode()).hexdigest()
 st=Stages(CASE/'cache',{'frame_id':p['frame']['id'],'units':'block','target_epoch':'2026-10-study','source_hash':sha(CASE/'input/manifest.json')},code_hash)
 common={'frame':p['frame'],'tower':p['tower']}
 model=st.run('shape',common,{},lambda:shape(p))
 a=st.run('site',{**common,'site':p['site']},{},lambda:site(p))
 b=st.run('podium',{**common,'podium':p['podium']},{},lambda:podium(p))
 c=st.run('interior',{**common,'interior':p['interior']},{'shape':'shape'},lambda:interior(p,model))
 d=st.run('facade',{**common,'facade':p['facade']},{'shape':'shape'},lambda:facade(p,model))
 e=st.run('roofs',common,{'shape':'shape'},lambda:roofs(p,model))
 f=st.run('lighting',p['lighting'],{'interior':'interior','shape':'shape'},lambda:lighting(p,c,model))
 overlap=Counter()
 for data in [a,b,c,d,e,f]:
  for x,y,z,s,owner in data['cells']:
   pos=(x,y,z)
   if pos in scene.blocks:overlap[(scene.owners[pos].split('.')[0],owner.split('.')[0])]+=1
   scene.set(pos,s,owner)
 states.connect(scene)
 for s in set(scene.blocks.values()):states.validate(s)
 meta=export_structure(scene,out/'building.nbt',3955,False);read=load_build(out/'building.nbt',Limits(cells=2_000_000));assert read.blocks==scene.blocks and read.size==scene.size
 groups={}
 for pos,owner in scene.owners.items():groups.setdefault(owner,[]).append(pos)
 dump(out/'components.json',{o:{'blocks':len(q),'bbox':bbox(q)} for o,q in groups.items()})
 dump(out/'blocks.json',{'size_xyz':list(scene.size),'blocks':[[*q,s,scene.owners[q]] for q,s in sorted(scene.blocks.items())]})
 dump(out/'rooms.json',f['rooms']);dump(out/'shape.json',model);dump(out/'floor_schedule.json',c['floor_ys']);dump(out/'params_used.json',p);dump(out/'cache_report.json',st.summary());dump(out/'inspection.json',inspect(read))
 dump(out/'build_report.json',{'route':'HAF','case_version':p['case_version'],'nbt':meta,'nbt_readback_exact_match':True,'source_code_sha256':code_hash,'input_manifest_sha256':sha(CASE/'input/manifest.json'),'room_count':len(f['rooms']),'lit_rooms':sum(bool(r['lamp_position']) for r in f['rooms']),'stage_count':7,'overlaps':[{'earlier':a,'later':b,'cells':n} for (a,b),n in overlap.items()],'world_test':'not run','automatic_image_interpretation':False,'model_input':None,'review_status':'requires visual/user review','limitations':['Published design plans are not an as-built survey','Facade modules and storey spacing quantized at 1:2','Diorite wall is a material approximation, without resource-pack texture preview','Window-back interior is synthetic and not generally walkable','Podium/site extent estimated; below grade excluded','No geographic north calibration or game runtime acceptance']})
 print(json.dumps({'nbt':meta,'rooms':len(f['rooms']),'cache_hits':st.summary()['hits']},ensure_ascii=False),flush=True);return out

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path,default=CASE/'research/parameters.json');a=ap.parse_args();run(a.run,json.loads(a.params.read_text()))
