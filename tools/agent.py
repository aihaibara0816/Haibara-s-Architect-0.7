"""Explicit HAF case entry. Does not guess geometry or alter a game world."""
from pathlib import Path
import argparse,json,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from hafusion import __version__
if __name__=='__main__':
    config=json.loads((ROOT/'agent_config.json').read_text(encoding="utf-8"))
    ap=argparse.ArgumentParser(description='HAF 0.4 mainline build and review entry')
    ap.add_argument('--version',action='version',version='HAF '+__version__)
    ap.add_argument('--catalog',action='store_true',help='Print the read-only capabilities/control catalog; does not generate a building')
    ap.add_argument('--list-cases',action='store_true',help='Print case registry without generating')
    ap.add_argument('--review',action='store_true',help='Read-only final-NBT sample and view checks')
    ap.add_argument('--handoff',type=Path,help='Validate design handoff and emit a plan; never generate NBT')
    ap.add_argument('--out',type=Path,help='Write handoff plan to a new file')
    ap.add_argument('--case',choices=sorted(config['cases']),default=config['default_case'])
    ap.add_argument('--run')
    ap.add_argument('--params',type=Path)
    a=ap.parse_args()
    if sum([a.catalog,a.list_cases,a.review,bool(a.handoff)])>1:ap.error('choose one read-only action')
    if a.handoff:
        if a.run or a.params or '--case' in sys.argv:ap.error('--handoff cannot be combined with case/build arguments')
        from hafusion.design_handoff import compile_handoff,HandoffError
        try:
            plan=compile_handoff(json.loads(a.handoff.read_text(encoding="utf-8")))
            result=json.dumps(plan,ensure_ascii=False,indent=2)+'\n'
            if a.out:
                with a.out.open('x',encoding='utf-8') as f:f.write(result)
            else:print(result,end='')
        except (HandoffError,ValueError,OSError) as e:ap.error(str(e))
        raise SystemExit(0)
    if a.out:ap.error('--out requires --handoff')
    if a.list_cases:
        if a.run or a.params:ap.error('--list-cases does not accept build arguments')
        print((ROOT/config['case_registry']).read_text(encoding="utf-8"));raise SystemExit(0)
    if a.catalog:
        if a.run or a.params:ap.error('--catalog cannot be combined with build arguments')
        print((ROOT/config['control_catalog']).read_text(encoding="utf-8"))
        raise SystemExit(0)
    if not a.run:ap.error('--run is required for generation')
    if Path(a.run).name!=a.run or a.run in ['.','..']:
        ap.error('--run must be a single new directory name')
    if a.review:
        if a.params:ap.error('--review consumes the stored run, not replacement parameters')
        raise SystemExit(subprocess.run([sys.executable,str(ROOT/'tools/review_case.py'),'--case',a.case,'--run',a.run],cwd=ROOT).returncode)
    if (ROOT/'cases'/a.case/'runs'/a.run).exists():ap.error('existing run is immutable; choose a new run name')
    if a.case=='civic_center' and a.params:ap.error('Civic R16 is a fixed-baseline revision adapter; --params is not supported')
    command=[sys.executable,str(ROOT/config['cases'][a.case]),'--run',a.run]
    if a.params:command += ['--params',str(a.params.resolve())]
    raise SystemExit(subprocess.run(command,cwd=ROOT).returncode)
