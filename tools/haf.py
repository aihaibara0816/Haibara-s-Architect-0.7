"""Haibara's Architect 0.7 CLI. Model output is data, never a shell command."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path(os.environ.get("HAF_ENGINE_ROOT", ROOT)).resolve()
sys.path.insert(0, str(ENGINE))
import hafusion
if str(ROOT / "hafusion") not in hafusion.__path__:
    hafusion.__path__.insert(0, str(ROOT / "hafusion"))
from hafusion.workflow06 import VERSION, case_command, dispatch_call, import_proposal, load_json, validate_request, verify_run, write_run
from hafusion.habitat07 import compile_scene, build_scene, verify_scene, dispatch_scene, RECIPES
from hafusion.archive07 import catalog, find_case, export_case, verify_case, isolated_room, knowledge


def main(argv=None):
    parser = argparse.ArgumentParser(description="Haibara's Architect 0.7 research, scene recipes and controlled workflow")
    parser.add_argument("--version", action="version", version="Haibara's Architect 0.7.0 (planning compatibility " + VERSION + ")")
    subs = parser.add_subparsers(dest="command", required=True)
    validate = subs.add_parser("validate", help="validate an explicit request without writing files")
    validate.add_argument("request", type=Path)
    plan = subs.add_parser("plan", help="create a new immutable planning run")
    plan.add_argument("request", type=Path)
    plan.add_argument("--runs-root", type=Path, required=True)
    plan.add_argument("--run", required=True)
    demo = subs.add_parser("demo", help="run the bundled small library planning example; no NBT")
    demo.add_argument("--runs-root", type=Path, required=True)
    demo.add_argument("--run", default="demo-001")
    verify = subs.add_parser("verify", help="recheck artifact hashes and replay planning validation")
    verify.add_argument("--runs-root", type=Path, required=True)
    verify.add_argument("--run", required=True)
    proposal = subs.add_parser("import-proposal", help="validate model-proposed modules in a new revision")
    proposal.add_argument("proposal", type=Path)
    proposal.add_argument("--runs-root", type=Path, required=True)
    proposal.add_argument("--parent", required=True)
    proposal.add_argument("--run", required=True)
    dispatch = subs.add_parser("dispatch", help="handle one model-neutral tool-call JSON; host binds paths and parent")
    dispatch.add_argument("call", type=Path)
    dispatch.add_argument("--runs-root", type=Path, required=True)
    dispatch.add_argument("--parent", required=True)
    case = subs.add_parser("build-case", help="show a registered legacy build command; explicit --execute runs it")
    case.add_argument("--case", required=True)
    case.add_argument("--run", required=True)
    case.add_argument("--execute", action="store_true")
    archive=subs.add_parser('archive',help='list/show/verify/export curated research cases')
    archive.add_argument('action',choices=['list','show','verify','export'])
    archive.add_argument('--case')
    archive.add_argument('--category')
    archive.add_argument('--destination',type=Path)
    guide=subs.add_parser('workflow',help='show complete stages or one reusable knowledge domain')
    guide.add_argument('--domain')
    skills=subs.add_parser('skill',help='inspect repository skill rules; does not install a personal skill')
    skills.add_argument('action',choices=['list','show'])
    skills.add_argument('--name')
    recipes=subs.add_parser('recipes',help='list bounded implemented 0.7 geometry recipes')
    for command in ['scene-plan','scene-build']:
        p=subs.add_parser(command,help='compile or explicitly generate a 0.7 scene request')
        p.add_argument('request',type=Path)
        if command=='scene-build':
            p.add_argument('--runs-root',type=Path,required=True);p.add_argument('--run',required=True)
    p=subs.add_parser('scene-verify',help='replay scene recipe checks and exact NBT readback')
    p.add_argument('--runs-root',type=Path,required=True);p.add_argument('--run',required=True)
    p=subs.add_parser('scene-dispatch',help='validate model additions against a host-bound scene; build only with --execute')
    p.add_argument('call',type=Path);p.add_argument('--base-request',type=Path,required=True)
    p.add_argument('--runs-root',type=Path,required=True);p.add_argument('--run',required=True);p.add_argument('--execute',action='store_true')
    p=subs.add_parser('build-study',help='run a recovered case in a fresh isolated project')
    p.add_argument('--case',choices=['room06'],required=True)
    p.add_argument('--runs-root',type=Path,required=True);p.add_argument('--run',required=True);p.add_argument('--seed',type=int,default=1145)
    args = parser.parse_args(argv)
    try:
        if args.command == 'archive':
            if args.action=='list':
                result=[{k:c[k] for k in ['id','name','category','version','buildability']} for c in catalog()['entries'] if not args.category or c['category']==args.category]
            elif args.action=='verify':
                result=verify_case(args.case) if args.case else [verify_case(c['id']) for c in catalog()['entries']]
            else:
                if not args.case:raise ValueError('--case required')
                if args.action=='show':result=find_case(args.case)
                else:
                    if not args.destination:raise ValueError('--destination required')
                    result=export_case(args.case,args.destination)
        elif args.command == 'workflow':result=knowledge(args.domain)
        elif args.command == 'skill':
            if args.action=='list':result=[{'name':d['id'],'scope':d['scope'],'installation':'repository rules; personal installation separate'} for d in knowledge()['domains']]
            else:
                if not args.name:raise ValueError('--name required')
                result=knowledge(args.name)
        elif args.command == 'recipes':result=RECIPES
        elif args.command == 'scene-plan':result=compile_scene(load_json(args.request))[1]
        elif args.command == 'scene-build':result=build_scene(load_json(args.request),args.runs_root,args.run)
        elif args.command == 'scene-verify':result=verify_scene(args.runs_root,args.run)
        elif args.command == 'scene-dispatch':result=dispatch_scene(load_json(args.call),load_json(args.base_request),args.runs_root,args.run,args.execute)
        elif args.command == 'build-study':result=isolated_room(args.runs_root,args.run,args.seed)
        elif args.command == "validate":
            result = validate_request(load_json(args.request))
        elif args.command in ("plan", "demo"):
            source = ROOT / "examples" / "workflow06" / "library-request.json" if args.command == "demo" else args.request
            result = write_run(load_json(source), args.runs_root, args.run)
        elif args.command == "verify":
            result = verify_run(args.runs_root, args.run)
        elif args.command == "import-proposal":
            result = import_proposal(args.runs_root, args.parent, args.run, load_json(args.proposal))
        elif args.command == "dispatch":
            result = dispatch_call(load_json(args.call), args.runs_root, args.parent)
        else:
            command = case_command(ENGINE, args.case, args.run)
            if args.execute:
                return subprocess.run(command, cwd=ENGINE, shell=False).returncode
            result = {"command_argv": command, "execute": False,
                      "note": "Registered case adapter only; this does not consume an arbitrary workflow plan. Add --execute to run."}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
