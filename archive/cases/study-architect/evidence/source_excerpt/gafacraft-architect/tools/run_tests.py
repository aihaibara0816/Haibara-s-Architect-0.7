"""Run meaningful unit/integration tests and save human/machine reports."""
from pathlib import Path
import datetime,io,json,platform,sys,time,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.legacy import ROOT

def main():
    stream=io.StringIO();start=time.perf_counter()
    suite=unittest.defaultTestLoader.discover(str(ROOT/"tests"))
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    elapsed=time.perf_counter()-start
    (ROOT/"reports/tests_final.txt").write_text(stream.getvalue(),encoding="utf-8")
    report={"timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"python":sys.version,"platform":platform.platform(),"command":"python tools/run_tests.py","tests_run":result.testsRun,"failures":[{"test":str(t),"traceback":trace} for t,trace in result.failures],"errors":[{"test":str(t),"traceback":trace} for t,trace in result.errors],"skipped":[str(x) for x in result.skipped],"elapsed_seconds":round(elapsed,3),"status":"pass" if result.wasSuccessful() else "fail"}
    (ROOT/"reports/tests_final.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(stream.getvalue());print(json.dumps(report,ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1
if __name__=="__main__":raise SystemExit(main())
