"""Read-back geometry assertions. These are not Minecraft physics tests."""
from collections import deque, Counter
from .voxelizer import q,q3
from .geometry import box_cells

def check_geometry(scene,spec,generated):
    checks=[];s=spec["coordinates"]["blocks_per_metre"]
    for check in spec["acceptance"]["clear_air_boxes"]:
        hits=[p for p in box_cells(q3(check["min_m"],s),q3(check["max_m"],s)) if p in scene.blocks]
        checks.append({"check_id":check["check_id"],"passed":not hits,"occupied_cells":len(hits),"examples":hits[:8]})
    for check in spec["acceptance"]["walk_paths"]:
        start,end=q3(check["start_xyz_m"],s),q3(check["end_xyz_m"],s)
        headroom=q(check["headroom_m"],s)
        def walkable(p):
            x,y,z=p
            return (0<=x<scene.size[0] and 1<=y and y+headroom<=scene.size[1] and 0<=z<scene.size[2]
                    and (x,y-1,z) in scene.blocks and all((x,y+i,z) not in scene.blocks for i in range(headroom)))
        reached=set([start]) if walkable(start) else set()
        queue=deque(reached)
        while queue and end not in reached:
            x,y,z=queue.popleft()
            for p in [(x+1,y,z),(x-1,y,z),(x,y,z+1),(x,y,z-1)]:
                if p not in reached and walkable(p): reached.add(p);queue.append(p)
        checks.append({"check_id":check["check_id"],"passed":end in reached,"reachable_cells":len(reached),"headroom_blocks":headroom,"scope":"one-block-wide, flat, full-cube occupancy BFS; not game pathfinding"})
    for check in spec["acceptance"]["profile_relationships"]:
        # Measure final read-back blocks attributed to this component, not desired widths.
        cid=check["component_id"]
        rows={row["y"]:row for row in generated["profiles"].get(cid,[])}
        measured=[]
        for key in ["lower_y_m","middle_y_m","upper_y_m"]:
            y=q(check[key],s)
            positions=[p for p in scene.blocks if p[1]==y and scene.owners.get(p)==cid]
            measured.append(max(p[0] for p in positions)-min(p[0] for p in positions)+1 if positions else 0)
        passed=all(measured) and measured[1]>measured[0] and measured[1]>measured[2]
        checks.append({"check_id":cid+".profile_relation","passed":bool(passed),"widths_lower_middle_upper":measured,"expectation":check["expectation"]})
    return {"status":"pass" if all(c["passed"] for c in checks) else "fail","checks":checks,
            "material_counts":dict(sorted(Counter(scene.blocks.values()).items())),"limits":"Full-cube static geometry only. Floor labels do not prove reachability between levels; no player, light or Create test."}

