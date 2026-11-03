from pathlib import Path
import json,sys,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]/'runs'/sys.argv[1]
a=np.asarray(json.loads((R/'heightmap_before.json').read_text()));b=a.copy();t=json.loads((R/'terrain_audit.json').read_text())
for q in t['delta']:b[q['z'],q['x']]=q['after']
d=b-a; fig,ax=plt.subplots(1,3,figsize=(15,4.7),layout='constrained')
for i,(m,title)in enumerate([(a,'Frozen terrain'),(b,'Finished ground'),(d,'Fill (+) / cut (-)')]):
 im=ax[i].imshow(m,cmap='terrain'if i<2 else'RdBu_r',vmin=0 if i<2 else-6,vmax=45 if i<2 else 6,origin='upper');ax[i].set_title(title,fontsize=13);ax[i].set_xlabel('X / blocks');ax[i].set_ylabel('Z / blocks (north at top)');fig.colorbar(im,ax=ax[i],shrink=.78,label='height / blocks'if i<2 else'delta / blocks')
fig.savefig(R/'terrain_comparison.png',dpi=150);plt.close(fig)
