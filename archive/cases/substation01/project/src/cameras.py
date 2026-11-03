from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];R=P/'runs'/sys.argv[1];views=[]
def cam(id,eye,target,span=130,w=1600,h=1100,**kw):
 v=dict(id=id,width=w,height=h,ortho=True,spanX=span,spanZ=span*h/w,eye=eye,target=target,sun_day=[.6,.9,.8],concept=False);v.update(kw);views.append(v)
for n,dx,dz in [('SE',245,245),('SW',-245,245),('NW',-245,-245),('NE',245,-245)]:
 for night in [False,True]:cam(('night_' if night else 'day_')+n,[128+dx,355,120+dz],[128,8,120],390,1800,1400,night=night)
cam('top',[128,650,120],[128,0,120],276,1600,1600)
cam('transformer',[194,76,160],[141,15,122],100,1800,1400,bounds=[121,101,160,142])
cam('transformer_section',[166,25,165],[141,12,123],50,1600,1200,bounds=[123,120,158,127],cutY=25)
cam('switchyard',[279,95,173],[208,12,95],140,1800,1400,bounds=[174,35,256,146])
cam('incoming',[1,92,192],[56,20,94],185,1800,1400,bounds=[0,25,112,150])
cam('services',[192,79,238],[134,10,159],218,1800,1100,bounds=[39,147,236,174])
cam('control',[107,61,271],[68,14,202],98,1600,1300,bounds=[38,182,96,227])
cam('control_night',[107,61,271],[68,14,202],98,1600,1300,bounds=[38,182,96,227],night=True)
for name,b,fy in [('control_F1',[39,184,95,223],7),('control_F2',[39,184,95,223],13),('mv_plan',[111,184,195,223],7),('workshop_plan',[203,184,237,223],7)]:
 x,z,X,Z=b;cx=(x+X)/2;cz=(z+Z)/2;span=max(X-x+8,(Z-z+8)*1600/1150);cam(name,[cx,250,cz],[cx,0,cz],span,1600,1150,minY=fy-1,cutY=fy+4,bounds=b)
cam('control_exploded',[131,94,291],[67,20,204],110,1600,1400,bounds=[38,183,96,224],minY=6,cutY=20,explode_floors=[6,12,18],explode_gap=9)
cam('control_section',[109,40,266],[67,13,202],79,1600,1100,bounds=[39,199,95,208],cutY=21)
cam('cable_trench',[125,23,180],[109,5,156],31,1500,1000,bounds=[105,147,113,165],cutY=9)
for n,eye,span in [('south',[128,27,700],275),('north',[128,27,-450],275),('west',[-450,27,120],258),('east',[750,27,120],258)]:cam('elevation_'+n,eye,[128,27,120],span,1800,550)
views.append(dict(id='control_inside',width=1600,height=1000,ortho=False,fov=80,eye=[89,9,215],target=[77,9,190],sun_day=[.6,.9,.8],concept=False))
views.append(dict(id='mv_inside',width=1600,height=1000,ortho=False,fov=80,eye=[116,9,199],target=[183,9,199],sun_day=[.6,.9,.8],concept=False))
(R/'cameras.json').write_text(json.dumps(views,indent=2))
for i in range(0,len(views),3):(R/f'camera_batch_{i//3}.json').write_text(json.dumps(views[i:i+3],indent=2))
print(len(views))
