"""Read-only reference extraction. Source states are preserved; no HAF placement adapter."""
from pathlib import Path
import sys,json,hashlib
from inspect_build import load_build,Limits
from voxel_core import Scene,export_structure
EXPECTED='3727667d0add5244a7f5b1bcfdf2706da4c49e16ade743a4de254da15f5b62e6'
SPECS=[
 ('J01','roof_mast',[92,36,22,95,43,25],'天线状竖杆及侧向附件','roof_base','形态参考；用途推断为天线，不证明通信或避雷功能。'),
 ('J02','wall_equipment',[91,13,3,95,16,4],'外墙设备盒','wall_z_plus','铁块、梯子、活板门、拉杆的组合；可借作空调外机表达，原作者用途未核实。'),
 ('J03','roof_equipment_row',[91,32,17,101,35,20],'屋顶连排设施研究段','roof_base','连排箱体与细杆组合；不强行认定水箱、风机或太阳能设备。')]
def main():
 src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
 assert hashlib.sha256(src.read_bytes()).hexdigest()==EXPECTED,'source hash changed'
 b=load_build(src,Limits());rows=[]
 for id,name,bb,label,anchor,note in SPECS:
  lo=bb[:3];hi=bb[3:];size=tuple(v-u for u,v in zip(lo,hi));scene=Scene(size)
  for q,s in b.blocks.items():
   if all(u<=v<w for u,v,w in zip(lo,q,hi)):
    scene.set(tuple(v-u for u,v in zip(lo,q)),s,id)
  file=out/(id+'_'+name+'.nbt');export_structure(scene,file,data_version=3955,include_air=False)
  reread=load_build(file,Limits());assert reread.size==scene.size and reread.blocks==scene.blocks
  row={'id':id,'label':label,'file':file.name,'source_bbox_xyz_exclusive':bb,'size_xyz':list(size),'source_sha256':EXPECTED,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'blocks':len(scene.blocks),'states':len(set(scene.blocks.values())),'anchor':anchor,'note':note,'status':'extracted_reference','readback_state_match':True,'game_test':'pending','rotation_test':'pending','neighbor_update_test':'pending','air_policy':'omitted; do not overwrite occupied target cells without planning clearance','consumer':None}
  (out/(id+'_states.json')).write_text(json.dumps({'metadata':row,'blocks_xyz_state':[[*q,s] for q,s in sorted(scene.blocks.items())]},ensure_ascii=False,indent=2))
  rows.append(row)
 (out/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
