"""Three bounded photograph-led studies. Exterior evidence + explicitly adapted interiors.
Not measured replicas, arbitrary planners, or model training. All coordinates are block units.
"""
from pathlib import Path
import sys,json,hashlib,math,random,copy,io,gzip,uuid
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import nbtlib as n,taisho_states
from modules import Module
from detail_lab import states as S
from vendor.voxel_core import Scene,state,parse_state,export_structure
class Study(Module):
 def __init__(self,id,w,d,levels,name):
  super().__init__(id,w,d,levels,name,1145);self.rooms=[];self.owners={};self.floors=[2+5*i for i in range(levels)];self.entry=[w//2,3,d-3];self.source=[]
 def p(self,x,y,z,st,owner='detail',**pr):
  super().p(x,y,z,st,owner,**pr)
  if (x,y,z)in self.blocks:self.owners[x,y,z]=self.id+'.'+owner
  else:self.owners.pop((x,y,z),None)
 def room(self,id,name,x,z,X,Z,f=2,capacity=2,source='adapted'):
  self.rooms.append({'id':self.id+'.'+id,'name':name,'bounds':[x,f+1,z,X,f+5,Z],'floor_y':f+1,'capacity':capacity,'evidence':source})
 def shell_rect(self,x,z,X,Z,f=2,top=7,wall='white_terracotta',floor='oak_planks',owner='shell'):
  self.box((x,f,z),(X,f+1,Z),floor,owner+'.floor');self.box((x,top,z),(X,top+1,Z),'birch_planks',owner+'.ceiling')
  for lo,hi in [((x,f+1,z),(X,top,z+1)),((x,f+1,Z-1),(X,top,Z)),((x,f+1,z),(x+1,top,Z)),((X-1,f+1,z),(X,top,Z))]:self.box(lo,hi,wall,owner+'.wall')
 def opening(self,axis,const,start,end,y=4,h=2,frame='smooth_quartz',sill=True):
  # A window has mullions, a transom and a sill in its own wall plane.
  for t in range(start,end):
   x,z=(t,const)if axis=='x'else(const,t)
   for yy in range(y,y+h):self.p(x,yy,z,'white_stained_glass_pane','window.glass')
   if sill:self.p(x,y-1,z,frame,'window.sill')
   self.p(x,y+h,z,frame,'window.head')
  for t in range(start,end,4):
   x,z=(t,const)if axis=='x'else(const,t)
   for yy in range(y,y+h):self.p(x,yy,z,frame,'window.mullion')
 def passage(self,x,z,X,Z,f=2):self.box((x,f+1,z),(X,f+3,Z),'air')
 def hip(self,x,z,X,Z,y,material='deepslate_tile',step=2):
  for xx in range(x,X):
   for zz in range(z,Z):
    t=min(xx-x,X-1-xx,zz-z,Z-1-zz);self.p(xx,y+t//step,zz,material+'_slab','roof',type='top'if t%step>=step/2 else'bottom')
 def gable(self,x,z,X,Z,y,material='spruce',wall='spruce_planks'):
  for xx in range(x,X):
   for zz in range(z,Z):
    t=min(zz-z,Z-1-zz);self.p(xx,y+t//2,zz,material+'_slab','roof',type='top'if t%2 else'bottom')
    if xx in[x+1,X-2]:
     for yy in range(y,y+t//2):self.p(xx,yy,zz,wall,'roof.gable')
 def picture(self,x,y,z,face='south',variant='kebab'):
  d=S.DIRS[face];q=[x,y,z];u=uuid.uuid5(uuid.NAMESPACE_URL,f'taisho11/{self.id}/{q}/{face}')
  ui=[int.from_bytes(u.bytes[j:j+4],'big',signed=True)for j in range(0,16,4)]
  self.entities.append(n.Compound({'id':n.String('minecraft:painting'),'variant':n.String('minecraft:'+variant),'facing':n.Byte(['south','west','north','east'].index(face)),'TileX':n.Int(x),'TileY':n.Int(y),'TileZ':n.Int(z),'Pos':n.List[n.Double]([n.Double(q[i]+.5-d[i]*.46875)for i in range(3)]),'Motion':n.List[n.Double]([n.Double(0)]*3),'Rotation':n.List[n.Float]([n.Float(0)]*2),'UUID':n.IntArray(ui)}))
 def sofa2(self,x,z,f=2,w=3):
  for xx in range(x,x+w):
   self.p(xx,f+1,z,'spruce_slab','sofa.seat',type='bottom');self.p(xx,f+1,z+1,'brown_wool','sofa.back');self.p(xx,f+2,z+1,'brown_carpet','sofa.soft')
  for xx,face in[(x-1,'west'),(x+w,'east')]:self.p(xx,f+1,z,'spruce_trapdoor','sofa.arm',facing=face,open=True)
 def tatami(self,x,z,X,Z,f=2):
  for xx in range(x,X):
   for zz in range(z,Z):self.p(xx,f,zz,'green_terracotta'if (xx-x)%3==0 else'birch_planks','tatami')
 def ceiling_lamp(self,x,z,y=6):self.lamp(x,y,z)
 def ground(self):
  self.box((0,0,0),(self.w,2,self.d),'dirt','site');self.box((0,2,0),(self.w,3,self.d),'grass_block','site')
 def stats(self):return {'id':self.id,'name':self.program,'size':[self.w,28,self.d],'floors':self.floors,'entry':self.entry,'rooms':self.rooms,'uses':self.uses,'doors':self.doors,'lights':self.lights,'stairs':self.stair_paths,'groups':self.groups,'sources':self.source}
