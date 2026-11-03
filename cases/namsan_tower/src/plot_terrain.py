"""A source-data figure, not a synthetic aerial photograph."""
from pathlib import Path
import sys,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from build_case import Builder
CASE=Path(__file__).resolve().parents[1]

def main():
    b=Builder(json.loads((CASE/'params.json').read_text()));b.prepare_site()
    fig,ax=plt.subplots(1,2,figsize=(14,6.7),layout='constrained')
    fig.patch.set_facecolor('#f3f2ed')
    for a in ax:a.set_facecolor('#f3f2ed')
    raw=np.array([q['elevation'] for q in json.loads((CASE/'research/terrain/dem_grid.json').read_text())['points']]).reshape(11,11)
    i=ax[0].imshow(raw,extent=(0,320,320,0),cmap='terrain',interpolation='nearest',vmin=180,vmax=270)
    ax[0].set_title('Retrieved SRTM samples\n11 x 11 grid, 32 m spacing (native resolution ~30 m)',loc='left',fontsize=12)
    fig.colorbar(i,ax=ax[0],shrink=.7,label='Elevation returned by source (m)')
    ax[1].imshow(b.grade,extent=(0,320,320,0),cmap='terrain',vmin=4,vmax=94)
    for key,t in b.tags.items():
        if not t.get('highway') or t.get('area')=='yes':continue
        ps=b.ways[key];ax[1].plot([p[0] for p in ps],[p[1] for p in ps],color='#50657a',lw=.65,alpha=.8)
    for mask,col in [(b.podium,'#e8d4ac'),(b.upper,'#f5f0df'),(b.lower,'#ced6d5'),(b.wood,'#b6906c')]:
        ov=np.zeros((*mask.shape,4));from matplotlib.colors import to_rgba;ov[mask]=to_rgba(col)
        ax[1].imshow(ov,extent=(0,320,320,0))
    ax[1].set_title('Authored block terrain + mapped site\nTerraces corrected locally; forest not individually surveyed',loc='left',fontsize=12)
    labels=[('Tower',(160,176),(173,217)),('Pavilion',(110,124),(20,130)),('Beacon',(99,80),(145,66)),('Cablecar upper station',(84,38),(113,20))]
    for title,pt,txt in labels:
        ax[1].scatter(*pt,s=16,c='#9e4135');ax[1].annotate(title,pt,txt,fontsize=8,color='#202d27',arrowprops={'arrowstyle':'-','color':'#5e6560','lw':.8})
    for a in ax:
        a.set_xlim(0,320);a.set_ylim(320,0);a.set_xlabel('X east (m)');a.set_ylabel('Z south (m)')
        a.annotate('N',xy=(298,15),xytext=(298,48),ha='center',weight='bold',arrowprops={'arrowstyle':'-|>','color':'#162e26'})
    fig.suptitle('NAMSAN / Terrain evidence and local interpretation',x=.025,ha='left',fontsize=18,weight='bold')
    fig.text(.025,-.025,'SRTM via OpenTopoData | Map data: OpenStreetMap contributors, ODbL | HAF 0.2, 2026-10-23\nPlatform heights are interpreted from photographs, not extracted from a fine survey.',fontsize=8,color='#4b5a52')
    out=CASE/'review/terrain_evidence.png';fig.savefig(out,dpi=155,bbox_inches='tight');plt.close(fig)

if __name__=='__main__':main()
