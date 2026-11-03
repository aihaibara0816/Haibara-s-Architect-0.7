"""Run retained and upgrade suites, saving every process log and exit code."""
import argparse,json,subprocess,sys,time,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cases=[('architect',[sys.executable,'tools/run_tests.py'],ROOT),('reference_legacy',[sys.executable,'scripts/selftest.py'],ROOT/'vendor/building_reference'),('reference_box',[sys.executable,'scripts/selftest_reference.py'],ROOT/'vendor/building_reference'),('reference_bundle',[sys.executable,'scripts/selftest_bundle.py'],ROOT/'vendor/building_reference'),('buildkit',[sys.executable,'-m','unittest','discover','-s','tests','-v'],ROOT/'vendor/buildkit_v03'),('inspector',[sys.executable,'-m','unittest','discover','-s','.agents/skills/real-to-minecraft/tests','-v'],ROOT/'vendor/buildkit_v03')]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='reports/v03_tests');args=ap.parse_args()
    dest=ROOT/args.out;dest.mkdir(exist_ok=True);records=[]
    for name,cmd,cwd in cases:
        start=time.monotonic();r=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (dest/(name+'.txt')).write_text(r.stdout)
        counts=re.findall(r'Ran (\d+) tests? in',r.stdout)
        rec={'suite':name,'command':cmd,'cwd':str(cwd.relative_to(ROOT)),'exit_code':r.returncode,'tests':int(counts[-1]) if counts else None,'seconds':round(time.monotonic()-start,3),'log':name+'.txt'}
        records.append(rec);print(json.dumps(rec),flush=True)
    result={'status':'pass' if all(x['exit_code']==0 for x in records) else 'fail','suites':records,'total_tests':sum(x['tests'] or 0 for x in records),'scope':'Engine regression, model reader fixtures and protocol checks; real Canton format comparisons separately recorded. No Minecraft or physical-fidelity evaluation.'}
    (dest/'summary.json').write_text(json.dumps(result,indent=2));return result['status']!='pass'
if __name__=='__main__':raise SystemExit(main())
