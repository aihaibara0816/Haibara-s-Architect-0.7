"""T16 terrain study: elongated, branching ridge and continuous descending central stream.
Authored terrain inspired by T07 relationships; not a scaled copy or vanilla worldgen.
"""
import math
W,H,D=320,92,288
CONTROL=[(20,67,26),(45,88,23),(76,120,18),(112,151,13),(151,168,9),(188,153,7),(223,184,5),(252,206,4),(288,198,4)]
def lerp(z,index):
 for a,b in zip(CONTROL,CONTROL[1:]):
  if z<=b[0]:
   t=max(0,min(1,(z-a[0])/(b[0]-a[0])));t=t*t*(3-2*t)
   return a[index]+(b[index]-a[index])*t
 return CONTROL[-1][index]
def river(z):return round(lerp(z,1)+1.4*math.sin(z*.11))
def riverlevel(z):return round(lerp(z,2))
def riverwidth(z):return 3+round(min(3,(z-20)/65)+.7*math.sin(z*.069))
def natural(x,z):
 # Long north ridge, interrupted by the creek; two west-facing spurs and
 # a lower eastern shoulder. No radial rings or settlement-wide terraces.
 north=25+9*math.sin(x*.024)+5*math.sin(x*.081)
 ridge=(25+6*math.sin(x*.031+.7))*math.exp(-((z-north)/(39+7*math.sin(x*.029)))**2)
 spur=14*math.exp(-((x-(35+.27*z+7*math.sin(z*.039)))/32)**2)*math.exp(-((z-80)/74)**2)
 east=7*math.exp(-((x-279)/43)**2-((z-119)/87)**2)
 h=7+max(0,(160-z)*.075)+ridge+spur+east+1.8*math.sin(x*.033+z*.017)+1.1*math.sin(z*.055-x*.023)+.7*math.sin(x*.17)*math.cos(z*.13)
 if z>=20:
  d=abs(x-river(z));rw=riverwidth(z);level=riverlevel(z)
  if d<=rw:return level-2
  if d<rw+21:
   t=max(0,min(1,(d-rw-1)/20));h=(level+1)*(1-t)+h*t
 return max(4,round(h))
