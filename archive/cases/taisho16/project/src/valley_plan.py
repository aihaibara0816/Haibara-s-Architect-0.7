from pathlib import Path
import sys,json,collections,hashlib
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path(__file__).resolve().parents[1]/'runs'/sys.argv[1];sp=json.loads((R/'spec.json').read_text());t=json.loads((R/'terrain_audit.json').read_text());hm=np.asarray(json.loads((R/'heightmap_before.json').read_text()))
fig,ax=plt.subplots(figsize=(14,12));ax.imshow(hm,cmap='Greens',alpha=.42,vmin=0,vmax=65)
wet=sp['river_water_columns'];ax.scatter([p[0]for p in wet],[p[1]for p in wet],s=1,c='#388da1',rasterized=True)
for r in sp['routes']:
 p=np.asarray(r['cells']);main=r.get('hierarchy')=='main';ax.plot(p[:,0],p[:,1],color='#c08d32'if main else'#89958b',lw=4 if main else 1.4,zorder=3)
for i,b in enumerate(sp['buildings'],1):
 x,y,z=b['origin'];w,h,d=b['size'];w,d=(d,w)if b['rotation']%180 else(w,d);ax.add_patch(Rectangle((x,z),w,d,facecolor='#f2e2bc',edgecolor='#604d36',lw=1.3,zorder=4));ax.text(x+w/2,z+d/2,f'{i:02d}\n'+b['id'],ha='center',va='center',fontsize=9,zorder=5)
ax.set_title('T16 / CONTINUOUS MAIN ROADS + CENTRAL CREEK',fontsize=18,pad=15);ax.set_xlabel('X / east');ax.set_ylabel('Z / south');ax.set_xlim(0,320);ax.set_ylim(288,0);fig.tight_layout();fig.savefig(R/'road_plan.png',dpi=130);plt.close(fig)
