"""M04 authored first-floor refit. Keep M03 shell, upper floor and stairs fixed."""
import uuid
import nbtlib as n

def refit(c):
 p,box,bes,B=c['p'],c['box'],c['bes'],c['B']
 pot,use,sign=c['pot'],c['use'],c['sign']
 K=c['K'];entities=[];paintings=[]
 def barrel(x,y,z,face,id):
  p(x,y,z,'barrel','refit.'+id,facing=face,open=False)
  bes[x,y,z]=n.Compound({'id':n.String('minecraft:barrel'),'Items':n.List[n.Compound]([])})
 def bottles(x,y,z,id,count=2):
  p(x,y,z,'sea_pickle','refit.'+id,pickles=count,waterlogged=False)
 def painting(x,y,z,face,variant,id):
  # All canvases are 1 x 1: anchor is the occupied air cell adjacent to its wall.
  vec={'south':(0,0,1),'west':(-1,0,0),'north':(0,0,-1),'east':(1,0,0)}[face]
  pos=[q+.5-v*.46875 for q,v in zip((x,y,z),vec)]
  uid=uuid.uuid5(uuid.NAMESPACE_URL,'haf/machiya08/'+id)
  ints=[int.from_bytes(uid.bytes[i:i+4],'big',signed=True)for i in range(0,16,4)]
  data=n.Compound({'id':n.String('minecraft:painting'),'variant':n.String('minecraft:'+variant),'facing':n.Byte(['south','west','north','east'].index(face)),
   'TileX':n.Int(x),'TileY':n.Int(y),'TileZ':n.Int(z),'Pos':n.List[n.Double](map(n.Double,pos)),
   'Motion':n.List[n.Double]([n.Double(0)]*3),'Rotation':n.List[n.Float]([n.Float({'south':0,'west':90,'north':180,'east':270}[face]),n.Float(0)]),
   'UUID':n.IntArray(ints),'Invulnerable':n.Byte(0),'FallDistance':n.Float(0),'Fire':n.Short(-1),'Air':n.Short(300),'OnGround':n.Byte(0),'PortalCooldown':n.Int(0)})
  entities.append(n.Compound({'pos':n.List[n.Double](map(n.Double,pos)),'blockPos':n.List[n.Int](map(n.Int,(x,y,z))),'nbt':data}))
  paintings.append({'id':id,'variant':'minecraft:'+variant,'anchor':[x,y,z],'facing':face,'support':[q-v for q,v in zip((x,y,z),vec)],'size':[1,1]})

 # Landing edge storage: staggered stack, lower under-stair pair, clear stair run.
 for x,y,z in [(11,3,9),(12,3,9),(11,4,9)]:barrel(x,y,z,'south','landing_stock')
 pot(12,4,9,'landing.stock')
 for y in [3,4]:barrel(12,y,15,'west','under_stair')
 use('G.landing_stock',11,2,10)
 use('G.under_stair_stock',11,2,16)
 painting(12,4,11,'west','wasteland','landing_picture')

 # West four-place booth: upholstered wall bench, narrow table, two framed chairs.
 box((8,3,18),(13,5,22),'air','refit.west_clear')
 # The existing entrance barrel and plant are deliberately restored at their original location.
 for z in [19,20]:
  p(8,3,z,'white_wool','refit.booth.back');p(8,4,z,'light_gray_carpet','refit.booth.back_trim')
  p(9,3,z,'quartz_slab','refit.booth.seat',type='bottom')
  K.table(10,z,1,1,'refit.booth.table','oak');K.chair(12,z,'west','spruce','refit.booth.chair')
 for z,face in [(18,'north'),(21,'south')]:p(9,3,z,'dark_oak_trapdoor','refit.booth.arm',open=True,facing=face)
 p(10,4,19,'flower_pot','refit.booth.cup');p(10,4,20,'white_candle','refit.booth.candle',candles=2,lit=False)
 barrel(12,3,21,'west','entry.shoes');pot(12,4,21,'entry.shoes')
 painting(8,5,20,'east','plant','booth_picture')
 # Small wall shelf and explicit support brackets, set above the booth end.
 for x in [8,9,10]:p(x,4,18,'oak_slab','refit.booth.shelf',type='top')
 bottles(8,5,18,'booth.bottles',3);p(10,5,18,'flower_pot','refit.booth.cup_shelf')
 for x in [8,10]:p(x,3,18,'oak_trapdoor','refit.booth.shelf_bracket',open=True,facing='south')

 # East four-place table faces two pairs of seats, with a shared wall-side back.
 box((19,3,19),(23,5,22),'air','refit.east_clear')
 K.table(20,20,2,1,'refit.east.table','oak')
 for x in [20,21]:
  K.chair(x,19,'south','spruce','refit.east.north_seat')
  K.chair(x,21,'north','spruce','refit.east.south_seat')
 p(20,4,20,'flower_pot','refit.east.cup');p(21,4,20,'white_candle','refit.east.candles',candles=1,lit=False)
 for x in [19,22]:p(x,3,21,'dark_oak_trapdoor','refit.east.arm',facing='west'if x==19 else'east',open=True)

 # Back bar: closed storage, small menu panels and a real painting above the serving surface.
 for x in [14,15,16]:
  barrel(x,4,13,'south','backbar.closed');p(x,5,13,'spruce_planks','refit.backbar.backing')
 sign(14,5,14,'south',['焼き魚','おつまみ','',''],'refit.menu.left')
 sign(16,5,14,'south',['お茶','本日の酒','',''],'refit.menu.right')
 painting(15,5,14,'south','kebab','bar_picture')
 p(15,4,14,'sea_pickle','refit.bar.bottle_group',pickles=2,waterlogged=False)
 bottles(18,4,14,'bar.return_bottles',3);p(18,4,17,'flower_pot','refit.return_cup')
 # Service drawers flank the WC approach rather than occupying its central doorway.
 for x in [20,22]:barrel(x,3,13,'south','service.sideboard')
 bottles(20,4,13,'service.drinks',4);p(22,4,13,'white_carpet','refit.service.folded_linen')
 use('G.drinks',20,2,14);use('G.return_linen',22,2,14)

 # Actual kitchen work/storage strips; central preparation and rear-door route remain free.
 for z in [10,11,12]:
  if z==10:p(14,3,z,'oak_stairs','refit.kitchen.prep_end',facing='west',half='top')
  else:barrel(14,3,z,'east','kitchen.ingredients')
  p(14,4,z,'oak_slab','refit.kitchen.wall_shelf',type='top')
 bottles(14,5,10,'kitchen.condiments',2);p(14,5,11,'flower_pot','refit.kitchen.crock');pot(14,5,12,'kitchen.herb')
 for z in [10,11,12]:barrel(18,3,z,'west','kitchen.pantry')
 p(18,4,10,'white_carpet','refit.kitchen.linen');bottles(18,4,11,'kitchen.oil',2)
 p(18,4,12,'flower_pot','refit.kitchen.bowl')
 use('G.prep_strip',15,2,11);use('G.pantry_strip',17,2,11)
 # Low skirting and a modest runner make the service route legible without changing the shell.
 for z in [14,15,16]:p(13,3,z,'spruce_planks','refit.core.wainscot')
 for z in [18,19,20,21]:p(16,3,z,'brown_carpet','refit.entry.runner')
 for x in [14,15,16,17]:p(x,3,18,'brown_carpet','refit.cross.runner')
 for u in c['uses']:
  if u['id']=='G.table_west':u['pos']=[11,3,20]
  if u['id']=='G.table_east':u['pos']=[22,3,20]
 # Remove the duplicate plant record after restoring the entrance group.
 ids=set();c['plants'][:]=[v for v in reversed(c['plants'])if not(v['id']in ids or ids.add(v['id']))][::-1]
 c['paintings']=paintings;c['art_entities']=entities
 c['refit_groups']=[
  {'id':'landing_stock','name':'楼道库存与楼梯下木桶','purpose':'备货、临时储物','approaches':['G.landing_stock','G.under_stair_stock']},
  {'id':'west_booth','name':'西侧四人卡座与壁架','purpose':'靠墙聚餐、墙画端景','approaches':['G.table_west']},
  {'id':'east_table','name':'东侧四人桌组','purpose':'临窗就餐','approaches':['G.table_east']},
  {'id':'backbar','name':'吧台菜单、墙画、储酒与杯具','purpose':'点单、取物、出餐','approaches':['G.counter','G.bar_storage']},
  {'id':'service','name':'两侧备餐柜与回收布巾','purpose':'酒水、布巾、餐具备取','approaches':['G.drinks','G.return_linen']},
  {'id':'kitchen','name':'厨房两侧工作带与壁架','purpose':'烹饪、清洗、备餐、储藏','approaches':['G.prep_strip','G.pantry_strip']}]
