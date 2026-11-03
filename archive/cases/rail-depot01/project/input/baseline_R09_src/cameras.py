from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];R=P/'runs'/sys.argv[1];views=[]
def cam(id,eye,target,span=130,w=1600,h=1100,**kw):
 v=dict(id=id,width=w,height=h,ortho=True,spanX=span,spanZ=span*h/w,eye=eye,target=target,sun_day=[.6,.9,.8],concept=False);v.update(kw);views.append(v)
for n,dx,dz in [('SE',330,330),('SW',-330,330),('NW',-330,-330),('NE',330,-330)]:
 for night in [False,True]:cam(('night_' if night else 'day_')+n,[240+dx,360,120+dz],[240,7,120],590,1800,1200,night=night)
cam('top',[240,650,120],[240,0,120],500,1800,1000)
cam('throat',[74,172,292],[204,7,92],242,1800,1200,bounds=[109,36,306,144],cutY=16)
cam('throat_full',[-90,205,315],[150,7,91],345,1800,1100,bounds=[0,25,306,146],cutY=28)
cam('neck_detail',[-20,80,181],[69,7,91],155,1600,1000,bounds=[0,68,140,114],cutY=20)
cam('utility_detail',[40,97,173],[116,9,48],210,1800,1000,bounds=[30,25,196,67])
cam('testline_detail',[20,82,72],[110,9,164],195,1800,1000,bounds=[33,158,184,171.99],cutY=28)
cam('facade_detail',[185,123,329],[112,40,196],180,1600,1500,bounds=[60,171,180,222])
cam('grade_section',[150,35,181],[150,5,100],100,1800,750,bounds=[146,62,154,143],cutY=18)
cam('maintenance_cut',[508,115,225],[365,7,110],205,1800,1100,cutY=17,bounds=[304,92,454,132])
cam('pit_detail',[348,12,100],[318,8,100],18,1600,1100,bounds=[312,94,321,107],cutX=320,cutY=15)
views.append(dict(id='maintenance_inside',width=1800,height=1100,ortho=False,fov=78,eye=[306,10,118],target=[440,10,109],sun_day=[.6,.9,.8],concept=False))
cam('stabling_cut',[505,130,155],[365,9,62],205,1800,1100,cutY=14,bounds=[304,36,454,88])
cam('wash_detail',[426,70,225],[327,10,139],135,1600,1100,bounds=[297,131,408,149])
cam('bridge_detail',[329,103,228],[261,12,92],155,1600,1100,bounds=[248,36,270,145])
cam('tower_section',[160,113,302],[84,51,195],145,1300,1700,cutX=91,bounds=[63,173,105,218])
cam('tower_exploded',[175,166,306],[84,74,195],205,1300,1800,bounds=[63,173,105,218],explode_floors=[6+i*6 for i in range(16)],explode_gap=3)
for n,fy in [(1,7),(2,13),(4,25),(15,91)]:cam('tower_F'+str(n),[84,250,195],[84,0,195],54,1300,1300,minY=fy-1,cutY=fy+4,bounds=[63,173,105,217])
for id,b,fy in [('dispatch_plan',[206,161,246,188],13),('research_plan',[120,176,178,216],13),('canteen_F1',[204,195,258,226],7),('canteen_F2',[204,195,258,226],13),('dorm_F1',[282,195,350,226],7),('dorm_F2',[282,195,350,226],13)]:
 x,z,X,Z=b;cx=(x+X)/2;cz=(z+Z)/2;cam(id,[cx,250,cz],[cx,0,cz],(X-x)+8,1500,950,minY=fy-1,cutY=fy+4,bounds=b)
for n,eye,span in [('south',[240,52,700],500),('north',[240,52,-450],500),('west',[-450,52,120],265),('east',[930,52,120],265)]:cam('elevation_'+n,eye,[240,52,120],span,1800,650 if span==500 else 1050)
(R/'cameras.json').write_text(json.dumps(views,indent=2))
for i in range(0,len(views),3):(R/f'camera_batch_{i//3}.json').write_text(json.dumps(views[i:i+3],indent=2))
print(len(views))
