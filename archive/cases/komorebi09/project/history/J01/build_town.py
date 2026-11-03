"""Komorebi09: 18 authored shops/homes, public routes and grouped low planting."""
from pathlib import Path
import sys,json,random,hashlib,gzip,io,copy,math,argparse,collections
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import town_states,modules
from detail_lab import states as S
from vendor.voxel_core import Scene,export_structure,parse_state,state
import nbtlib as n
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--seed',type=int,default=1145);a=ap.parse_args();R=ROOT/'runs'/a.run;R.mkdir(parents=True,exist_ok=False)
size=(184,24,120);scene=Scene(size);bes={};entities=[];buildings=[];plant_records=[];trees=[];route=set();footprints=set();lights=[]
def rng(id):return random.Random(int(hashlib.sha256(f'komorebi09.1|{a.seed}|{id}'.encode()).hexdigest()[:16],16))
def p(x,y,z,name,owner,**pr):
 st=S.make(name,**{k:str(v).lower()for k,v in pr.items()})if not name.startswith('minecraft:')else name
 scene.set((int(x),int(y),int(z)),st,owner);bes.pop((int(x),int(y),int(z)),None)
def ground(x,z,mat,owner='site.path'):
 p(x,2,z,mat,owner)
def rect(x0,z0,x1,z1,mat,owner='site.path'):
 for x in range(x0,x1):
  for z in range(z0,z1):ground(x,z,mat,owner);route.add((x,z))
for x in range(184):
 for z in range(120):
  p(x,0,z,'dirt','site.foundation');p(x,1,z,'dirt','site.foundation');p(x,2,z,'grass_block','site.ground')
# Main asphalt street with both pavements, and a narrower stone lane by the canal.
rect(2,35,158,48,'smooth_stone');rect(2,38,158,45,'gray_concrete')
for x in range(2,158):
 ground(x,37,'polished_andesite');ground(x,45,'polished_andesite')
rect(2,81,158,88,'stone_bricks');rect(2,82,158,87,'polished_andesite')
# Continuous north-south passages, each kept fully clear to the top of a standing player.
for x0,x1 in [(27,30),(51,54),(77,81),(103,106),(128,131)]:rect(x0,5,x1,116,'smooth_stone')
rect(2,5,5,116,'stone_bricks');rect(155,5,158,116,'stone_bricks');rect(2,113,158,116,'stone_bricks')
# A meandering creek along the eastern edge; a quiet bank walk opens toward it.
rect(159,5,162,116,'stone_bricks');rect(178,5,181,116,'stone_bricks')
bridges=[];water_cells=set()
for z in range(3,117):
 center=168+int(round(1.8*math.sin(z/17)+.7*math.sin(z/7)))
 half=2+(1 if 48<z<72 else 0)
 for x in range(center-half,center+half+1):
  p(x,1,z,'water','site.water',level=0);p(x,2,z,'air','site.channel_clear');water_cells.add((x,z))
 for x in [center-half-1,center+half+1]:
  if z%7 in [0,1,2]:ground(x,z,'stone_bricks','site.bank_stone')
# Solid end caps and bed. The bridge keeps the street/footpath level and leaves water underneath.
for z in [2,117]:
 for x in range(162,175):p(x,1,z,'stone_bricks','site.water_end')
for z0,z1,mat in [(39,44,'stone_bricks'),(84,87,'oak_planks')]:
 rect(158,z0,181,z1,mat,'site.bridge');bridges.append([158,z0,181,z1])
 for x in range(162,178):
  for z in [z0,z1-1]:p(x,3,z,'oak_fence'if mat=='oak_planks'else'spruce_fence','site.bridge_rail')
programs=[('machiya','日和小食'),('single','茶と菓子'),('single','八百屋'),('machiya','古本と茶'),('single','花屋'),('compact','住家・青葉'),('single','干物店'),('compact','小さな宿'),('single','木工房'),('compact','仕立屋'),('machiya','米と雑貨'),('compact','住家・白壁'),('machiya','路地の酒場'),('compact','住家・木窓'),('single','文庫'),('single','木葉湯'),('compact','住家・庭先'),('single','陶器店')]
centers=[15,40,65,94,119,144]
# Stable authored lot offsets, not a regular array of identical boxes.
offsets=[0,1,-1,0,-1,1,1,0,-1,1,0,-1,0,-1,1,0,1,0]
for i,(family,program)in enumerate(programs):
 id=f'B{i+1:02d}';row,col=divmod(i,6);rot=0 if row==0 else 2
 if family=='machiya':m=modules.machiya(id,program,a.seed,i%4)
 elif family=='compact':m=modules.compact(id,program,a.seed,i%3)
 else:
  m=modules.single(id,program,a.seed,w=18 if program=='木葉湯'else(17 if i%2 else 16),d=19 if program=='木葉湯'else(18 if i%2 else 17),variant=i)
 x0=centers[col]-m.w//2+offsets[i];z0=36-(m.d-1)if row==0 else(48+(i%2)if row==1 else 88+(i%3==1))
 def transform(q,continuous=False):
  x,y,z=q
  if rot==2:x,z=m.w-(0 if continuous else 1)-x,m.d-(0 if continuous else 1)-z
  return [x+x0,y,z+z0]
 def strot(st):
  name,pr=parse_state(st)
  if rot==0:return st
  turn={'north':'south','south':'north','east':'west','west':'east'};pp={turn.get(k,k):turn.get(v,v)if k=='facing'else v for k,v in pr.items()}
  return state(name,**pp)
 for q,st in m.blocks.items():
  qq=tuple(transform(q));old=scene.owners.get(qq,'')
  assert not old.startswith('B'),(id,qq,old)
  scene.set(qq,strot(st),id+'.building');footprints.add((qq[0],qq[2]))
 for q,be in m.bes.items():bes[tuple(transform(q))]=copy.deepcopy(be)
 for en in m.entities:
  en=copy.deepcopy(en);pos=transform(list(map(float,en['Pos'])),True);en['Pos']=n.List[n.Double](map(n.Double,pos));anchor=transform([int(en[k])for k in ['TileX','TileY','TileZ']])
  for key,value in zip(['TileX','TileY','TileZ'],anchor):en[key]=n.Int(value)
  if rot:en['facing']=n.Byte((int(en['facing'])+2)%4);en['Rotation'][0]=n.Float((float(en['Rotation'][0])+180)%360)
  entities.append(en)
 us=[{**u,'pos':transform(u['pos'])}for u in m.uses];ds=[{**d,'pos':transform(d['pos']),'lintel':transform(d['lintel']),'facing':({'north':'south','south':'north','east':'west','west':'east'}[d['facing']]if rot else d['facing'])}for d in m.doors]
 ls=[{**l,'position':transform(l['position']),'support':transform(l['support'])}for l in m.lights];lights+=ls
 entry=transform(m.entry);ex,ey,ez=entry;roadz=36 if row==0 else 46 if row==1 else 85
 # Approach is ground-level, full three-block width; preserve all modeled thresholds.
 for x in range(ex-1,ex+2):
  for z in range(min(ez,roadz),max(ez,roadz)+1):
   if (x,2,z)not in scene.blocks or scene.owners.get((x,2,z),'').startswith('site'):ground(x,z,'polished_andesite')
   route.add((x,z))
 # Keep the original module's rear-door/courtyard routes on firm footing.
 for u in us:
  x,y,z=u['pos']
  if u['floor_block_y']==2 and scene.owners.get((x,2,z),'').startswith('site'):ground(x,z,'smooth_stone')
 starts={'2':[ex,ez]}
 if family=='machiya':starts['7']=transform([6,8,14])[::2]
 elif family=='compact':starts['7']=transform([3,8,9])[::2]
 buildings.append({'id':id,'name':program,'family':family,'floors':m.levels,'module_size':[m.w,24,m.d],'origin':[x0,0,z0],'rotation':rot*90,'bounds':[x0,0,z0,x0+m.w,24,z0+m.d],'entry':entry,'road_target':[ex,3,roadz],'floor_starts':starts,'use_points':us,'doors':ds,'lights':ls,'stairs':[[transform(p,True)for p in path]for path in m.stair_paths],'program_status':'authored interior, offline checks pending; not game verified'})
# Small street spaces: benches and low planting pockets, away from main approaches.
for x,z in [(7,73),(35,74),(61,74),(91,75),(115,74),(145,74),(8,8),(92,8)]:
 if any((xx,z)in footprints for xx in range(x,x+3)):continue
 for xx in range(x,x+3):
  ground(xx,z,'stone_bricks');p(xx,3,z,'oak_slab','site.bench',type='top');p(xx,4,z,'brown_carpet','site.bench_soft')
for x,z in [(7,36),(31,46),(56,36),(82,46),(108,36),(153,46),(9,82),(33,86),(58,82),(84,86),(110,82),(151,86),(78,8),(78,110)]:
 # Single-sided modest timber lantern posts.
 for y in range(3,7):p(x,y,z,'spruce_fence','site.lamp_post')
 p(x,7,z,'oak_slab','site.lamp_cap',type='bottom');p(x+1,6,z,'stripped_oak_log','site.lamp_arm',axis='x');p(x+1,5,z,'lantern','site.lamp',hanging=True)
 lights.append({'position':[x+1,5,z],'support':[x+1,6,z]})
# Tree locations are selected only in sufficiently large unoccupied ground pockets.
def groundfree(x,z,margin=0):
 if not(5<=x<179 and 5<=z<113):return False
 for dx in range(-margin,margin+1):
  for dz in range(-margin,margin+1):
   if(x+dx,z+dz)in route or(x+dx,z+dz)in footprints:return False
 return scene.blocks.get((x,2,z))=='minecraft:grass_block[snowy=false]' and scene.blocks.get((x,3,z),'minecraft:air')=='minecraft:air'
rr=rng('trees');candidates=[(x,z)for z in range(7,112,4)for x in range(7,179,4)if groundfree(x,z,2)];rr.shuffle(candidates)
for x,z in candidates:
 if len(trees)>=32:break
 if any((x-t['x'])**2+(z-t['z'])**2<36 for t in trees):continue
 h=rr.choice([5,6,7]);r=rr.choice([2,2,3]);kind='cherry_leaves'if len(trees)%7==0 else'oak_leaves'
 for y in range(3,3+h):p(x,y,z,'oak_log','plant.tree.trunk',axis='y')
 for yy in range(3+h-3,3+h+2):
  for xx in range(x-r,x+r+1):
   for zz in range(z-r,z+r+1):
    if ((xx-x)/(r+.3))**2+((zz-z)/(r+.3))**2+((yy-(3+h-1))/2.6)**2<=1 and (xx,yy,zz)not in scene.blocks:p(xx,yy,zz,kind,'plant.tree.canopy')
 trees.append({'id':f'T{len(trees)+1:02d}','x':x,'z':z,'height':h,'radius':r,'leaves':kind})
# Low layers: stable patch centres, soft patch falloff, then contextual species selection.
patches=[]
for z in range(6,114,9):
 for x in range(6,179,10):
  r=rng(f'patch/{x}/{z}');patches.append({'id':f'P{x}_{z}','x':x+r.randint(-3,3),'z':z+r.randint(-3,3),'radius':r.randint(3,7),'flower':r.choice(['poppy','oxeye_daisy','dandelion','cornflower','azure_bluet'])})
for x in range(5,179):
 for z in range(5,113):
  if not groundfree(x,z):continue
  near=min(patches,key=lambda c:((x-c['x'])**2+(z-c['z'])**2)/(c['radius']**2));dist=math.hypot(x-near['x'],z-near['z'])/near['radius'];r=rng(f'ground/{x}/{z}')
  wallnear=any((x+dx,z+dz)in footprints for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
  density=.10+.43*max(0,1-dist*.55)+(.12 if wallnear else 0)
  if r.random()>density:continue
  shade=any((x-t['x'])**2+(z-t['z'])**2<(t['radius']+1)**2 for t in trees)
  flower=near['flower'];name=r.choices(['fern'if shade else'short_grass',flower,'large_fern'if shade else'tall_grass'],weights=[73,21,6])[0]
  if name in ['large_fern','tall_grass']:
   if scene.blocks.get((x,4,z),'minecraft:air')!='minecraft:air':name='short_grass'
   else:p(x,4,z,name,'plant.ground.'+near['id'],half='upper')
  p(x,3,z,name,'plant.ground.'+near['id'],**({'half':'lower'}if name in ['large_fern','tall_grass']else{}));plant_records.append({'anchor':[x,3,z],'kind':name,'patch':near['id'],'context':'shade'if shade else'wall'if wallnear else'meadow'})
# Low shrubs are sparse; unlike grass, their collision footprint is protected from paths.
for j in range(70):
 r=rng('shrub/'+str(j));x=r.randrange(6,179);z=r.randrange(6,113)
 if not groundfree(x,z,1):continue
 for dx,dz in [(0,0),(1,0),(0,1)]:
  if scene.blocks.get((x+dx,3,z+dz),'minecraft:air')=='minecraft:air':p(x+dx,3,z+dz,'azalea_leaves','plant.shrub')
# Canonical pane/fence connection fields are resolved against the completed town.
S.connect(scene)
for st in set(scene.blocks.values()):S.validate(st)
# All retained block entities must match their final underlying state.
for q,be in bes.items():
 name,_=parse_state(scene.blocks[q]);expected='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:banner'if name.endswith('_wall_banner')else'minecraft:bed'if name.endswith('_bed')else name
 assert str(be['id'])==expected,(q,name,str(be['id']))
base=R/'base.nbt';export_structure(scene,base,include_air=False);f=n.load(base)
f['entities']=n.List[n.Compound]([n.Compound({'pos':copy.deepcopy(en['Pos']),'blockPos':n.List[n.Int]([en[k]for k in['TileX','TileY','TileZ']]),'nbt':en})for en in entities])
for e in f['blocks']:
 q=tuple(map(int,e['pos']))
 if q in bes:e['nbt']=bes[q]
buf=io.BytesIO();f.write(buf);out=R/'Komorebi09.nbt';temp=out.with_suffix('.tmp');temp.write_bytes(gzip.compress(buf.getvalue(),mtime=0));temp.replace(out);base.unlink()
sp={'case_id':'Komorebi09','title':'木漏日町 · 十八栋日式小街区','run':a.run,'mainline':'HAF 0.4','algorithm':'komorebi09.1','seed':a.seed,'size_xyz':size,'ground_floor_block':2,'coordinates':'+X east, +Z south','buildings':buildings,'route_cells':sorted(route),'trees':trees,'groundcover':plant_records,'patches':patches,'bridges':bridges,'water_cells':sorted(water_cells),'lights':lights,'non_air':len(scene.blocks),'block_entities':len(bes),'paintings':len(entities),'source_nbt_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'design_brief':{'route':'original design using accepted Machiya08 M08 and two new bounded families','hard_constraints':['18 enclosed buildings','enterable furnished ground floors','upper floors furnished with beds where present','old Japanese street vocabulary','grouped grass and flowers; no path planting'],'families':{'large_shop_house':4,'compact_two_storey':6,'single_storey_specialty':8},'layout':'main shop street, side alleys, meandering creek at east side with bank walks and two bridges; staggered fronts and mixed eaves','reference':'previous Freedom observation record reused; no new video viewing this turn'},'randomness':{'fixed':['lots','programs','doorways','stairs','room layout','street lights','roads','bridges'],'variable':['tree selection in safe pockets','tree height and canopy radius','groundcover patch centres','grass/flower species and local density','potted species'],'seed_scope':'stable named groups; planting variation only, not arbitrary layout generation'},'status':{'geometry':'pending','game':'pending','aesthetic':'pending'},'limitations':['offline preview is not a Minecraft screenshot','furniture seats, tubs and display props are decorative vanilla constructions','some shop entrances show open trading state without closure','NBT is sparse; use supplied world or clear whole bounding box before structure paste','source room layouts are authored family adaptations, not 18 entirely unrelated algorithms']}
(R/'spec.json').write_text(json.dumps(sp,ensure_ascii=False,indent=2));(R/'owners.json').write_text(json.dumps({','.join(map(str,q)):v for q,v in scene.owners.items()}));print(json.dumps({k:sp[k]for k in ['run','non_air','block_entities','paintings','source_nbt_sha256']})+' trees='+str(len(trees))+' groundcover='+str(len(plant_records)),flush=True)
