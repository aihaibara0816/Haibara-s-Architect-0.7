"""Authored irregular parcels plus independent, bounded seeded massing channels."""
import random,copy,hashlib
W,D,H=356,250,84
BASE_SEED=311148
def rng(seed,id,channel):return random.Random(f'{seed}/{id}/{channel}')
LOTS=[
 ('A1',15,18,18,31,7,0,'home','rear_cut',4),
 ('A2',40,10,35,24,4,1,'home','compound',3),
 ('A3',82,15,22,47,11,0,'home','rear_cut',5),
 ('A4',116,9,40,25,3,2,'home','front_cut',5),
 ('A5',169,15,28,36,6,1,'home','rect',0),
 ('B1',14,59,41,24,3,3,'restaurant','rear_cut',5),
 ('B2',62,49,18,33,6,2,'home','rect',0),
 ('B3',111,44,30,40,5,0,'home','compound',4),
 ('B4',147,56,22,28,4,3,'repair','front_cut',4),
 ('B5',179,64,20,19,2,2,'tea','rear_cut',4),
 ('C1',13,144,24,32,6,0,'grocery','front_cut',5),
 ('C2',44,181,36,25,3,2,'home','rear_cut',5),
 ('C3',42,215,24,24,7,1,'home','rect',0),
 ('C4',88,187,19,48,8,0,'home','rect',0),
 ('C5',116,181,42,24,4,3,'home','rear_cut',5),
 ('C6',115,216,28,23,2,1,'home','compound',3),
 ('C7',153,213,20,28,6,2,'home','front_cut',4),
 ('C8',167,181,35,23,5,0,'laundry','rear_cut',4),
 ('C9',182,214,24,28,4,3,'home','rect',0),
 ('D1',233,16,24,36,7,1,'repair','rear_cut',5),
 ('D2',265,10,38,25,4,2,'home','front_cut',4),
 ('D3',311,19,28,45,6,0,'home','rear_cut',5),
 ('D4',233,62,20,46,5,0,'grocery','front_cut',4),
 ('D5',262,46,35,26,8,1,'home','rect',0),
 ('D6',266,82,38,29,3,2,'restaurant','rear_cut',5),
 ('D7',311,77,29,34,5,3,'barber','front_cut',4),
 ('E1',232,149,33,25,6,0,'grocery','rear_cut',5),
 ('E2',276,146,22,47,12,0,'home','front_cut',4),
 ('E3',306,151,39,30,4,3,'restaurant','rear_cut',5),
 ('E4',232,185,32,47,4,1,'home','compound',4),
 ('E5',274,205,24,32,3,2,'tea','rear_cut',4),
 ('E6',308,194,34,44,8,0,'home','rear_cut',5),
]
LABEL={'A1':'榕北窄宅','A2':'横巷凹院楼','A3':'深进出租楼','A4':'三层旧宅','A5':'北街合住楼','B1':'榕背食坊','B2':'夹缝小楼','B3':'折角合院','B4':'巷口维修铺','B5':'老榕茶座','C1':'西口杂货楼','C2':'南巷横宅','C3':'七层窄宅','C4':'深巷高楼','C5':'横向连住楼','C6':'低矮旧院','C7':'补建出租楼','C8':'南巷洗衣铺','C9':'转巷旧楼','D1':'过街修理铺','D2':'榕东长屋','D3':'东口住商楼','D4':'东里便利店','D5':'东街高宅','D6':'街坊肠粉铺','D7':'转巷理发室','E1':'路边批发铺','E2':'长进深合住楼','E3':'东南食坊','E4':'凹院连住楼','E5':'旧巷茶座','E6':'东南高楼'}
def plan(seed=BASE_SEED):
 out=[]
 for i,(id,x,z,w,d,f,rot,ground,shape,cut) in enumerate(LOTS):
  from q04_activity import NEW_GROUND
  ground=NEW_GROUND.get(id,ground)
  # Baseline widths are deliberately heterogeneous; seeded envelopes cannot reach neighbours.
  if seed!=BASE_SEED:
   w=max(18,w-rng(seed,id,'width').randint(0,2));d=max(18,d-rng(seed,id,'depth').randint(0,2))
   x+=rng(seed,id,'setback').randint(0,1);z+=rng(seed,id,'setback_z').randint(0,1)
   if id not in ['A3','E2']:f=max(2,min(8,f+rng(seed,id,'height').choice([-1,0,1])))
  palettes=['sand','ivory','ochre','rose','gray','mint','ivory','sand','rose','ochre','gray','rose','sand','mint','ivory','brick','gray','sand','rose','ochre','ivory','sand','gray','mint','rose','ivory','sand','ivory','brick','sand','ochre','gray']
  pal=palettes[i]if seed==BASE_SEED else rng(seed,id,'whole_building_palette').choice(palettes)
  t=dict(id=id,name=LABEL[id],x=x,z=z,w=w,d=d,floors=f,rotation=rot,ground=ground,shape=shape,cut=cut,base_y=3,palette=pal,maintenance=.35+.5*rng(seed,id,'maintenance').random(),balcony=i%4!=2,street_role='frontage' if ground!='home' else 'inner',extra_shop_entry=False,corner_shop=False)
  if shape=='compound':
   LW,LD=(w,d) if rot%2==0 else (d,w)
   t['edge_recesses']=[dict(face='right',start=14,end=min(LD-4,20),depth=3),dict(face='rear_right',depth=cut)]
  out.append(t)
 return dict(size_xyz=[W,H,D],seed=seed,buildings=out,lighting={'override_reason':'生活区按住户选择亮灯；门厅和公共楼梯独立照明。'},site={'boundary_xz':[[0,0],[W,0],[W,D],[0,D]]})
