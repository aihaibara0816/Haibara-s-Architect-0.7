"""Sparse NBT and exact 32-cell template assembly, with per-state materials."""
from pathlib import Path
import sys,json,csv,hashlib,zipfile,shutil
from collections import Counter,defaultdict
CASE=Path(__file__).resolve().parents[1];HAF=CASE.parents[1];sys.path.insert(0,str(HAF/'support'))
from vendor.inspect_build import load_build,Limits
from vendor.voxel_core import Scene,export_structure,parse_state
DEST=CASE/'deliverables';STEM='Guangzhou_CTF_HAF_V1'
def main():
 DEST.mkdir(exist_ok=True);nbt=CASE/'runs/V1/building.nbt';b=load_build(nbt,Limits(cells=2_000_000));shutil.copyfile(nbt,DEST/(STEM+'.nbt'))
 for name,counts in [('Materials',Counter(parse_state(s)[0] for s in b.blocks.values())),('Blockstates',Counter(b.blocks.values()))]:
  with (DEST/(STEM+'_'+name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(['block_id' if name=='Materials' else 'blockstate','placed_cells','stacks_64','remainder']);w.writerows([s,n,n//64,n%64] for s,n in sorted(counts.items()))
 buckets=defaultdict(dict)
 for (x,y,z),s in b.blocks.items():buckets[(x//32*32,y//32*32,z//32*32)][(x%32,y%32,z%32)]=s
 placements=[];assembled={}
 for origin,cells in sorted(buckets.items()):
  scene=Scene(tuple(min(32,b.size[i]-origin[i]) for i in range(3)))
  for q,s in cells.items():scene.set(q,s,'tile')
  name='v1/c_'+'_'.join(map(str,origin));path=CASE/'game_templates'/(name+'.nbt');meta=export_structure(scene,path,3955,False);r=load_build(path);assert r.blocks==cells
  for q,s in r.blocks.items():
   p=tuple(q[i]+origin[i] for i in range(3));assert p not in assembled;assembled[p]=s
  placements.append({'template':'hafctf:'+name,'origin':origin,'file':str(path.relative_to(CASE)),'nbt':meta})
 assert assembled==b.blocks
 install='''广州周大福金融中心 / HAF V1
目标 Minecraft Java 1.21.1，DataVersion 3955；尚未游戏内验收。
完整 NBT 场景：80 × 269 × 92（X/Y/Z）；1:2 比例。
场地地坪顶面为原点 Y+2，主塔最高面为原点 Y+267，地面以上265格。
请在空白测试区域导入；世界上界320时建议原点 Y≤50。
完整 NBT 大于256KiB，不适合有256KiB导入限制的工具；可使用本包分片。
Java_1.21.1.zip 放进测试世界 datapacks，执行 /reload 后，在选定原点执行 /function hafctf:v1。
分片各轴不超过32格，已回读后精确拼合核对。无 load/tick 自动运行功能。
这些模板不含显式空气，不能清除旧建筑残块。完整NBT与分片二选一。
示意正面为+Z，实际地理北向未标定。玻璃连接、墙柱邻接更新、光照、碰撞仍需游戏测试。
材料CSV统计已放置格位，保留墙、半砖、玻璃片等独立ID；并非合成配方或净采购单。
室内是窗后层次补全，1:2楼层净高没有普遍可行走保证。
'''
 (DEST/'IMPORT_AND_MATERIALS.txt').write_text(install)
 pack=DEST/(STEM+'_Java_1.21.1.zip')
 with zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('pack.mcmeta',json.dumps({'pack':{'pack_format':48,'description':'HAF CTF V1; manual templates; game test pending'}}))
  cmds=[]
  for row in placements:
   name=row['template'].split(':',1)[1];z.write(CASE/row['file'],'data/hafctf/structure/'+name+'.nbt');cmds.append('place template '+row['template']+' '+' '.join('~'+str(v) for v in row['origin']))
  z.writestr('data/hafctf/function/v1.mcfunction','\n'.join(cmds)+'\n');z.writestr('INSTALL.txt',install)
 report={'target_version':'Java 1.21.1','full_nbt_sha256':hashlib.sha256(nbt.read_bytes()).hexdigest(),'template_count':len(placements),'exact_reassembly':True,'world_test':'not run','placements':placements}
 (CASE/'validation/template_reassembly.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('Exact reassembly',len(placements),'templates',len(assembled),'cells')
if __name__=='__main__':main()
