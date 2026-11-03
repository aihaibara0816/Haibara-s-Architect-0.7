"""Real Canton cache / cold rebuild / material-only integration experiment."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from hafusion.pipeline import build
from common import dump
def main(prefix):
    baseline=json.loads((ROOT/'runs/V6_r02/build_report.json').read_text())
    warm=build(prefix+'_warm')
    cold=build(prefix+'_cold',cache_root=ROOT/('cache_'+prefix))
    # Glass -> glass fixture, preserving shape and every frozen site surface.
    changed=build(prefix+'_material',material_overrides={'minecraft:cyan_stained_glass':'minecraft:light_blue_stained_glass'})
    checks={'warm_all_stages_hit':not warm['cache']['rebuilt'],
            'warm_nbt_identical':warm['nbt']['sha256']==baseline['nbt']['sha256'],
            'cold_replay_nbt_identical':cold['nbt']['sha256']==baseline['nbt']['sha256'],
            'material_only_geometry_cached':all(not n.startswith('geometry.') for n in changed['cache']['rebuilt']),
            'material_only_occupancy_identical':changed['occupancy_sha256']==baseline['occupancy_sha256'],
            'material_only_ownership_identical':changed['ownership_sha256']==baseline['ownership_sha256'],
            'material_only_changes_nbt':changed['nbt']['sha256']!=baseline['nbt']['sha256']}
    dump(ROOT/'reports'/('replay_'+prefix+'.json'),{'checks':checks,'baseline':baseline['nbt']['sha256'],
         'warm':warm['cache'],'cold':cold['cache'],'material':changed['cache'],
         'material_run_is_test_only':'Not the delivered V6. Main palette remains the V5 palette.'})
    assert all(checks.values()),checks
    print(json.dumps(checks),flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--prefix',required=True);main(p.parse_args().prefix)
