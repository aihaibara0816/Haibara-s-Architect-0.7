from pathlib import Path
import json,sys
P=Path(__file__).resolve().parents[1];R=P/'runs'/sys.argv[1]
views=[]
def ortho(id,eye,target,span=130,width=1600,height=1100,**kw):
 v=dict(id=id,width=width,height=height,ortho=True,spanX=span,spanZ=span*height/width,eye=eye,target=target,sun_day=[.6,.9,.8],concept=False);v.update(kw);views.append(v)
for n,dx,dz in [('SE',310,310),('SW',-310,310),('NW',-310,-310),('NE',310,-310)]:
 for night in [False,True]:ortho(('night_' if night else 'day_')+n,[224+dx,280,168+dz],[224,3,168],582,1800,1250,night=night)
ortho('top',[224,600,168],[224,0,168],475,1800,1450)
ortho('production_cut',[255,150,310],[121,5,176],230,1800,1200,cutY=13,bounds=[29,141,212,209])
views.append(dict(id='production_inside',width=1600,height=1000,ortho=False,fov=78,eye=[201,8,153],target=[55,8,172],sun_day=[.6,.9,.8],concept=False))
ortho('process_detail',[420,140,190],[288,20,69],170,bounds=[242,29,334,113])
ortho('tank_detail',[491,105,169],[383,14,65],135,bounds=[349,26,420,112])
ortho('rawyard_detail',[225,110,192],[117,8,69],225,bounds=[28,28,205,113])
ortho('warehouse_cut',[485,110,309],[378,5,180],125,cutY=15,bounds=[337,140,420,226])
for n,foot in [(1,4),(2,12)]:ortho('canteen_F'+str(n),[189,200,282],[189,0,282],97,1600,1100,minY=foot-1,cutY=foot+5,bounds=[146,254,232,309])
ortho('canteen_cut',[282,101,380],[190,6,282],132,cutY=9,bounds=[146,254,232,309])
ortho('dorm_F2',[280,200,283],[280,0,283],42,1000,1800,minY=11,cutY=17,bounds=[267,252,294,314])
ortho('dorm_room',[289,44,297],[273,4.5,280],21,1400,1100,minY=3,cutY=6,bounds=[268,276,278,285])
ortho('office_section',[172,116,384],[80,28,278],161,1600,1250,cutX=101,bounds=[31,248,129,311])
for n,foot in [(1,4),(4,28),(8,60)]:ortho('office_F'+str(n),[79,200,278],[79,0,278],111,1600,1100,minY=foot-1,cutY=foot+5,bounds=[31,248,129,311])
ortho('office_exploded',[215,180,414],[80,58,278],211,1400,1600,bounds=[31,248,129,311],explode_floors=[0,10,18,26,34,42,50,58,66],explode_gap=7)
ortho('bridge_detail',[400,170,410],[230,7,230],300,1600,1100,cutY=17,bounds=[110,201,352,257])
for n,eye,span in [('front',[224,34,700],480),('back',[224,34,-400],480),('left',[-400,34,168],365),('right',[800,34,168],365)]:ortho('elevation_'+n,eye,[224,34,168],span,1800,600)
(R/'cameras.json').write_text(json.dumps(views,indent=2))
for i in range(0,len(views),3):(R/f'camera_batch_{i//3}.json').write_text(json.dumps(views[i:i+3],indent=2))
print('cameras',len(views))
