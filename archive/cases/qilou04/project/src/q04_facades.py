"""Q04 revision: whole-building colour, finished roof edges, and connected large arcades."""
import copy,math,random
import nbtlib as n
import qilou_core as C,qilou_recipes as R
from prototype_base import Study
from detail_lab import states as S

PALETTES={
 'gray':dict(label='水灰',wall='light_gray_concrete',trim='smooth_quartz'),
 'ivory':dict(label='灰白',wall='white_concrete',trim='smooth_stone'),
 'cream':dict(label='米黄',wall='smooth_sandstone',trim='smooth_quartz'),
 'rose':dict(label='浅粉赭',wall='white_terracotta',trim='smooth_quartz'),
 'ochre':dict(label='暖黄',wall='yellow_terracotta',trim='smooth_quartz'),
 'mint':dict(label='淡青绿',wall='weathered_cut_copper',trim='smooth_quartz'),
 'brick':dict(label='砖红',wall='bricks',trim='smooth_sandstone')}
CHOICES={
 'N01':('gray','flat'), 'N02':('cream','gable'), 'N03':('ivory','flat'),
 'N05':('rose','terrace'), 'N06':('gray','gable'), 'N07':('cream','flat'), 'N08':('ochre','hip'),
 'S01':('gray','flat'), 'S02':('mint','terrace'), 'S03':('rose','gable'),
 'S04':('cream','flat'), 'S07':('ivory','flat'), 'S08':('brick','hip')}

def move(m,dx):
 def p(v):return [v[0]+dx,v[1],v[2]]
 m.blocks={(x+dx,y,z):s for (x,y,z),s in m.blocks.items()};m.owners={(x+dx,y,z):s for (x,y,z),s in m.owners.items()};m.bes={(x+dx,y,z):s for (x,y,z),s in m.bes.items()}
 m.entry=p(m.entry);m.rear_entry=p(m.rear_entry)if m.rear_entry else None
 for r in m.rooms:r['bounds'][0]+=dx;r['bounds'][3]+=dx
 for r in m.uses:r['pos']=p(r['pos'])
 for r in m.lights:
  for k in ['position','support']:r[k]=p(r[k])
 for r in m.doors:
  for k in ['pos','lintel']:r[k]=p(r[k])
 for r in m.groups:
  if 'bounds_xyz'in r:r['bounds_xyz'][0]+=dx;r['bounds_xyz'][3]+=dx
  if 'use_points'in r:r['use_points']=[p(q)for q in r['use_points']]
 m.stair_paths=[[p(q)for q in line]for line in m.stair_paths]
 for r in m.stair_runs:r['path']=[p(q)for q in r['path']]
 m.upper_starts={k:[q[0]+dx,q[1]]for k,q in m.upper_starts.items()}
 for r in m.variation:r['position']=p(r['position'])
 for e in m.entities:e['TileX']=n.Int(int(e['TileX'])+dx);e['Pos'][0]=n.Double(float(e['Pos'][0])+dx)

def large(id,wall):
 configs={r['id']:r for r in R.CONFIG}
 keys=['Bookshop','Bookshop']if id=='N03'else['Post','Grain']if id=='S01'else['Bakery','Hardware','Textile']
 levels=2 if id=='S01'else 3
 total=sum(configs[k]['w']for k in keys);name='清和书局大楼'if id=='N03'else'惠民邮政大楼'if id=='S01'else'德兴百货联铺'
 m=Study(id,total,33,levels,name);m.floors=[2,9,15][:levels];m.h=36;m.kind='large';m.variation=[];m.upper_starts={};m.stair_runs=[];m.rear_entry=None;m.extra_entries=[];m.source=[]
 cursor=0
 for j,k in enumerate(keys):
  r=copy.deepcopy(configs[k]);r.update(levels=levels,kind='plain',wall=wall)
  a=R.shop(r)
  if levels==3:R.home(a,15)
  a=R.decorate(a,r)
  if k=='Post':
   # The original corner shop entered at x=10; the enlarged plain frontage enters at x=11.
   # Move the waiting bench clear of that real doorway, including its arms and soft back.
   for q in list(a.blocks):
    if q[1]in[3,4]and q[0]in range(10,16)and q[2]in[21,22]and'bench.'in a.owners.get(q,''):a.p(*q,'air','post.entry_clear')
   C.bench(a,15,21,2,4,'green')
  for field in ['uses','doors','groups','rooms']:
   for item in getattr(a,field):
    for key in ['id','component_id','room_id']:
     if key in item:item[key]=id+'.wing'+str(j)+'.'+item[key]
  move(a,cursor)
  for q,s in a.blocks.items():m.blocks[q]=s;m.owners[q]=a.owners.get(q,id)
  m.bes.update(a.bes);m.entities+=a.entities
  for field in ['uses','doors','lights','stair_paths','groups','rooms','variation','stair_runs']:getattr(m,field).extend(getattr(a,field))
  if j==0:m.entry=a.entry;m.rear_entry=a.rear_entry;m.upper_starts=a.upper_starts
  else:
   m.extra_entries.append(a.entry)
   if a.rear_entry:m.extra_entries.append(a.rear_entry)
   # Remove both partition skins; upper lounges connect, each wing keeps its own stair.
   for f in m.floors:
    for x in [cursor-1,cursor]:
     for z in [21,22]:
      for y in range(f+1,f+5):m.p(x,y,z,'air','large.open_connection')
  cursor+=a.w
 # A single long entablature, larger central entrance marker and full structural pier rhythm.
 for x in sorted(set([0,total-1]+list(range(7,total-2,7)))):
  m.p(x,3,28,'polished_andesite','large.column.base')
  for y in range(4,8):m.p(x,y,28,'quartz_pillar','large.column',axis='y')
  m.p(x,8,28,'chiseled_quartz_block','large.capital')
 for x in range(total):
  for y in [9,15,21][:levels]:m.p(x,y,29,'quartz_slab','large.continuous.cornice',type='top')
 m.sign(total//2,14 if levels==2 else 20,29,'south',[name,'书籍・阅览'if id=='N03'else'邮务・日常'if id=='S01'else'糕点・日用・布匹','创作案例',''])
 return m,dict(name=name,kind='large',program='books'if id=='N03'else'mail'if id=='S01'else'department',levels=levels,w=total,merged_bays=len(keys))

def finish(m,id):
 color,roof=CHOICES[id]
 if C.SEED!=311148:
  color=random.Random(f'{C.SEED}/{id}/whole_palette').choice(list(PALETTES))
  if id not in['N03','S01','S04']:roof=random.Random(f'{C.SEED}/{id}/roof_type').choice(['flat','terrace','gable','hip'])
 p=PALETTES[color];wall=p['wall'];top=15 if m.levels==2 else 21
 # Colour by functional ownership; leave furniture and internal partitions intact.
 for q,s in list(m.blocks.items()):
  o=m.owners.get(q,'');name=s.split('[')[0].split(':')[-1]
  exterior=any(k in o for k in ['front.wall','rear.wall','side.wall','party.wall','chamfer.wall','parapet.wall','two_storey.parapet'])
  if exterior and name in ['white_concrete','light_gray_concrete','white_terracotta','smooth_sandstone','bricks','yellow_terracotta','weathered_cut_copper']:m.blocks[q]=S.make(wall)
  if 'window'in o and 'cyan_stained_glass'in s:m.blocks[q]=s.replace('cyan_stained_glass','gray_stained_glass')
  if 'floor_or_ceiling'in o and q[0]in[0,m.w-1]:m.blocks[q]=S.make('smooth_stone')
 # Remove inherited repeated ridges/parapets and rebuild a complete fifth facade.
 for q in list(m.blocks):
  if q[1]>top and any(v in m.owners.get(q,'')for v in ['roof','parapet','coping','relief']):m.p(*q,'air','roof.reset')
  elif q[1]>=top and 'rear.roof'in m.owners.get(q,''):m.p(*q,'air','roof.reset')
 footprint={(x,z)for x in range(m.w)for z in range(3,29)if m.kind!='corner' or x+z<=44}
 for x,z in footprint:m.p(x,top,z,'smooth_stone','roof.complete_deck')
 if roof in ['flat','terrace']:
  for x,z in footprint:
   edge=any((x+dx,z+dz)not in footprint for dx,dz in[(1,0),(-1,0),(0,1),(0,-1)])
   if edge:
    for y in [top+1,top+2]:m.p(x,y,z,wall,'roof.parapet')
    m.p(x,top+3,z,'smooth_stone_slab','roof.coping',type='bottom')
  if id in ['N03','S04']:
   for x in range(m.w//2-4,m.w//2+5):
    m.p(x,top+3,28,wall,'roof.central_marker');m.p(x,top+4,28,'quartz_slab','roof.marker_cap',type='bottom')
  # Skylights occupy the roof, with a solid curb, not an open slot at the street edge.
  for x0 in range(6,m.w-5,15):
   for x in range(x0,x0+4):
    for z in range(9,13):m.p(x,top+1,z,'gray_stained_glass'if x not in[x0,x0+3]and z not in[9,12]else'smooth_stone','roof.skylight')
  if roof=='terrace':
   for x in range(5,m.w-3):
    m.p(x,top+1,23,'dark_oak_slab','roof.terrace_bench',type='bottom')
   for x in [4,m.w-3]:m.barrel(x,top+1,20);m.pot(x,top+2,20)
 elif roof=='gable':
  for x,z in footprint:
   inset=min(x,m.w-1-x);h=top+1+inset//3
   m.p(x,h,z,'deepslate_tile_slab','roof.full_gable',type='top'if inset%3 else'bottom')
   if z in[3,28]or x in[0,m.w-1]:
    for y in range(top+1,h):m.p(x,y,z,wall,'roof.closed_fascia')
 else:
  for x,z in footprint:
   inset=min(x,m.w-1-x,z-3,28-z,max(0,(44-x-z)//2)if m.kind=='corner'else 99);h=top+1+inset//2
   m.p(x,h,z,'brick_slab'if id=='S08'else'deepslate_tile_slab','roof.complete_hip',type='top'if inset%2 else'bottom')
 # One-row eave is a finished cornice only. No uncovered six-block front roof strip.
 for x in range(m.w):
  if (x,28)in footprint:m.p(x,top,29,'quartz_slab','roof.edge_finish',type='top')
 m.facade_revision=dict(palette=color,palette_label=p['label'],wall=wall,roof=roof,roof_label={'flat':'平顶女儿墙','terrace':'平顶与露台','gable':'完整坡顶','hip':'收边四坡顶'}[roof],covered_front_strip=True)
 return m.facade_revision
