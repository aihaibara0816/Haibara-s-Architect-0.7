"""Create 6.0.10 Bezier reconstruction, kept independent of the authoring code."""
import math
import numpy as np

def controls(starts, axes):
    a,b=np.asarray(starts,float); u,v=np.asarray(axes,float)
    u=u/np.linalg.norm(u);v=v/np.linalg.norm(v)
    angle=(math.atan2(-v[2],-v[0])-math.atan2(u[2],u[0]))%(2*math.pi)
    angle=min(angle,2*math.pi-angle)
    h=np.linalg.norm(b-a)/3
    if angle<1e-5:
        forward=abs(np.dot(b-a,u));side=abs(np.dot(b-a,np.cross(u,[0,1,0])))
        lo,hi=sorted((forward,side))
        if lo>1.2 and 1<hi/lo<3:h=hi-lo
    else:
        c1=np.cross(u,[0,1,0])[[0,2]];c2=np.cross(v,[0,1,0])[[0,2]]
        mat=np.stack([c1,-c2],axis=1)
        if abs(np.linalg.det(mat))>1e-8:
            radius=abs(np.linalg.solve(mat,(b-a)[[0,2]])[1])
            h=radius*4/3*math.tan(angle/4)
            if h==0:h=1
    return np.array([a,a+u*h,b+v*h,b])

def sample(starts,axes,n=601):
    a,c,d,b=controls(starts,axes);t=np.linspace(0,1,n)[:,None]
    return (1-t)**3*a+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*b

def read_connection(pos,co,n=601):
    starts=np.array([q['V'] for q in co['Starts']],float)+np.array(pos)
    axes=np.array([q['V'] for q in co['Axes']],float)
    return sample(starts,axes,n)

def stats(starts,axes):
    c=controls(starts,axes);t=np.linspace(.00001,.99999,1501)[:,None]
    v=3*(1-t)**2*(c[1]-c[0])+6*(1-t)*t*(c[2]-c[1])+3*t*t*(c[3]-c[2])
    a=6*(1-t)*(c[2]-2*c[1]+c[0])+6*t*(c[3]-2*c[2]+c[1])
    speed=np.linalg.norm(v[:,[0,2]],axis=1);k=np.abs(v[:,0]*a[:,2]-v[:,2]*a[:,0])/speed**3
    return {'horizontal_min_radius':float(1/k.max()) if k.max()>1e-8 else None,'max_grade_percent':float(np.max(abs(v[:,1])/speed)*100),'length':float(np.linalg.norm(np.diff(sample(starts,axes),axis=0),axis=1).sum())}
