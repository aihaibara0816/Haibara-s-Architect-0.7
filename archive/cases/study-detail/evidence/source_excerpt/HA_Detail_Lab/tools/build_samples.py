#!/usr/bin/env python3
"""Generate isolated paired NBT experiments; never writes original HA assets."""
import sys,json,hashlib,csv,argparse,shutil
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from detail_lab.builders import build,control
from detail_lab.states import family,validate
from detail_lab.mesh import write_mesh,cameras
from vendor.voxel_core import Scene,export_structure
from vendor.inspect_build import load_build

def save_json(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def export_checked(scene,path):
    record=export_structure(scene,path,data_version=3955,include_air=True)
    decoded=load_build(path);nonair={p:s for p,s in decoded.blocks.items() if family(s)!='air'}
    assert decoded.size==scene.size and nonair==scene.blocks,'Round-trip mismatch'
    for s in decoded.palette:validate(s)
    record['independent_readback']='PASS';return record,decoded

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',default='r01');ap.add_argument('--no-mesh',action='store_true');args=ap.parse_args()
    if not args.run.replace('_','').replace('-','').isalnum():raise ValueError('Simple run ID required')
    out=ROOT/'runs'/args.run;out.mkdir(parents=True,exist_ok=False)
    configs=json.loads((ROOT/'configs/samples.json').read_text());save_json(out/'configs_used.json',configs)
    (out/'assets').mkdir();shutil.copyfile(ROOT/'assets/render_shader_reference.html',out/'assets/render_shader_reference.html')
    manifest={'run':args.run,'version':'0.1.0','target':'Java 1.21.1','data_version':3955,'comparison':'A = same occupied cells / architectural partial states replaced with full blocks; B = detail states. Not old HA0.3 versus HAFusion.','game_validation':'PENDING','samples':[]}
    gallery=Scene((168,40,68));placements=[]
    for index,c in enumerate(configs):
        detailed=build(c);ablation=control(detailed);changed=sum(ablation.blocks[p]!=s for p,s in detailed.blocks.items())
        assert changed>0 and ablation.blocks.keys()==detailed.blocks.keys()
        item={**c,'changed_state_cells':changed,'occupied_cells_identical':True,'variants':{},'intentional_replacements':detailed.events}
        save_json(out/'cameras'/(c['id']+'.json'),cameras(detailed.size,c['id']))
        for tag,scene in [('A',ablation),('B',detailed)]:
            label=c['id']+'_'+tag;path=out/'nbt'/(label+'.nbt');rec,decoded=export_checked(scene,path)
            counts=Counter(scene.blocks.values());base=Counter()
            for state,n in counts.items():base[state.split('[')[0]]+=n
            rec.update({'components':len(set(scene.owners.values())),'state_count':len(counts),'partial_cells':sum(n for s,n in counts.items() if family(s) not in ['cube','air','leaves','flower']), 'base_material_counts':dict(base.most_common()),'state_material_counts':dict(counts.most_common())})
            if not args.no_mesh:rec['preview']=write_mesh(decoded,path,out/'previews'/label/'scene')
            item['variants'][tag]=rec
            with (out/'nbt'/(label+'_materials.csv')).open('w',newline='') as f:
                writer=csv.writer(f);writer.writerow(['block_state','placed_cells']);writer.writerows(counts.most_common())
            save_json(out/'components'/(label+'.json'),{'owners':[[*p,scene.owners[p]] for p in sorted(scene.blocks)],'note':'Ownership sidecar; Java structure NBT itself does not store component IDs.'})
        dx=(index%4)*42+3;dz=(index//4)*34+3
        for (x,y,z),s in detailed.blocks.items():gallery.set((x+dx,y,z+dz),s,detailed.owners[(x,y,z)])
        placements.append({'id':c['id'],'origin_xyz':[dx,0,dz],'size_xyz':list(detailed.size)})
        manifest['samples'].append(item);print(c['id'],len(detailed.blocks),'changed',changed,flush=True)
    manifest['gallery'],_=export_checked(gallery,out/'nbt/detail_gallery_B.nbt')
    manifest['gallery']['placements']=placements
    save_json(out/'components/detail_gallery_B.json',{'owners':[[*p,gallery.owners[p]] for p in sorted(gallery.blocks)]})
    save_json(out/'manifest.json',manifest)
    print(out,flush=True)
if __name__=='__main__':main()
