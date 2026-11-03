from pathlib import Path
import json,gzip,argparse,hashlib
C=Path(__file__).resolve().parents[1]
def main(run):
 r=C/'runs'/run;p=json.loads((r/'params_used.json').read_text());o=json.loads(gzip.decompress((r/'component_ownership.json.gz').read_bytes()));names=o['owner_names'];actual={}
 for t in p['towers']:
  points=[v[:3] for v in o['xyz_owner'] if names[v[3]]==t['id']+'.shell.facade']
  actual[t['id']]={'x':min(v[0] for v in points),'z':min(v[2] for v in points)}
 steps={row:[actual[row+str(i+1)]['z']-actual[row+str(i)]['z'] for i in [1,2]] for row in ['A','B']}
 gap=[actual['A'+str(i)]['z']-actual['B'+str(i)]['z'] for i in [1,2,3]]
 xsteps={row:[actual[row+str(i+1)]['x']-actual[row+str(i)]['x'] for i in [1,2]] for row in ['A','B']}
 checks=[{'id':'NBT_facade_origins_step_north_10','status':'pass' if all(v==[-10,-10] for v in steps.values()) else 'fail','origins':actual,'z_steps':steps},{'id':'NBT_rows_parallel_same_depth_gap','status':'pass' if len(set(gap))==1 and xsteps['A']==xsteps['B']==[50,50] else 'fail','row_gaps':gap,'x_steps':xsteps}]
 out={'source_nbt_sha256':hashlib.sha256((r/'building.nbt').read_bytes()).hexdigest(),'checks':checks,'passed':all(c['status']=='pass' for c in checks)};(r/'layout_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);main(ap.parse_args().run)
