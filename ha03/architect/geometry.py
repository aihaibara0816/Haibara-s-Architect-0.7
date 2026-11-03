"""Ordered, bounded primitives. No prompts, eval, network, or implicit design."""
import math
from .legacy import core
from .voxelizer import q, q3, quantized_box

def inside_polygon(x, z, vertices):
    inside = False
    for (ax, az), (bx, bz) in zip(vertices, vertices[1:] + vertices[:1]):
        if (az > z) != (bz > z):
            edge_x = (bx - ax) * (z - az) / (bz - az) + ax
            if x < edge_x:
                inside = not inside
    return inside

def box_cells(lo, hi):
    for y in range(lo[1], hi[1]):
        for z in range(lo[2], hi[2]):
            for x in range(lo[0], hi[0]):
                yield x, y, z

def profile_at(params, height):
    sections = params["sections"]
    for a, b in zip(sections, sections[1:]):
        if a["y_m"] <= height < b["y_m"]:
            t = 0 if params["interpolation"] == "step" else (height - a["y_m"]) / (b["y_m"] - a["y_m"])
            return {key: a[key] + (b[key] - a[key]) * t for key in ("cx_m", "cz_m", "width_m", "depth_m")}
    return {key: sections[-1][key] for key in ("cx_m", "cz_m", "width_m", "depth_m")}

def generate(spec):
    scale = spec["coordinates"]["blocks_per_metre"]
    scene = core.Scene(tuple(spec["coordinates"]["size_blocks"]))
    materials = spec["materials"]
    components, profiles, quantization = [], {}, []
    changed_total = 0
    overlaps = {}
    work_budget = spec["environment"]["budgets"]["max_cell_visits"]

    def put(p, comp, material):
        nonlocal changed_total
        changed_total += 1
        if changed_total > work_budget:
            raise ValueError("Cell-operation budget exceeded")
        # Keep ownership for targeted subtraction and later revision reports.
        if comp["operation"] == "subtract":
            if scene.owners.get(p) in comp["targets"]:
                scene.set(p, core.AIR, comp["component_id"])
        else:
            prior=scene.owners.get(p)
            if prior is not None and prior!=comp["component_id"]:
                pair=(prior,comp["component_id"]);overlaps[pair]=overlaps.get(pair,0)+1
            scene.set(p, materials[material]["block_state"], comp["component_id"])

    for comp in spec["components"]:
        params, kind = comp["parameters"], comp["kind"]
        before = len(scene.blocks)
        cid = comp["component_id"]
        if kind == "box":
            lo, hi = quantized_box(params["min_m"], params["max_m"], scale)
            for pos in box_cells(lo, hi):
                put(pos, comp, comp["material"])
            quantization.append({"component_id": cid, "input_min_m": params["min_m"], "input_max_m": params["max_m"], "min_blocks": lo, "max_blocks_exclusive": hi,
                                 "max_endpoint_error_m": max(abs(a / scale - b) for a,b in zip((*lo,*hi),(*params["min_m"],*params["max_m"])))})
        elif kind == "polygon_prism":
            vertices = [[q(x, scale), q(z, scale)] for x, z in params["vertices_xz_m"]]
            if len({tuple(v) for v in vertices}) != len(vertices):
                raise ValueError(f"{cid}: polygon vertices collapse on block grid")
            y0, y1 = q(params["y_min_m"], scale), q(params["y_max_m"], scale)
            count = 0
            for z in range(min(v[1] for v in vertices), max(v[1] for v in vertices)):
                for x in range(min(v[0] for v in vertices), max(v[0] for v in vertices)):
                    if inside_polygon(x+.5, z+.5, vertices):
                        for y in range(y0, y1):
                            put((x,y,z), comp, comp["material"])
                            count += 1
            if not count:
                raise ValueError(f"{cid}: polygon vanished after voxelization")
        elif kind == "profile_shell":
            sections = params["sections"]
            y0, y1 = q(sections[0]["y_m"], scale), q(sections[-1]["y_m"], scale)
            wall = q(params["wall_thickness_m"], scale)
            floor_thickness = q(params["floor_thickness_m"], scale)
            floor_ys = {y for m in params["floor_levels_m"] for y in range(q(m,scale), q(m,scale)+floor_thickness)}
            if params["cap_top"]:
                floor_ys.update(range(y1 - floor_thickness, y1))
            rows = []
            for y in range(y0, y1):
                p = profile_at(params, (y+.5)/scale)
                x0 = q(p["cx_m"] - p["width_m"]/2, scale)
                x1 = q(p["cx_m"] + p["width_m"]/2, scale)
                z0 = q(p["cz_m"] - p["depth_m"]/2, scale)
                z1 = q(p["cz_m"] + p["depth_m"]/2, scale)
                width, depth = x1-x0, z1-z0
                if min(width,depth) <= 2*wall:
                    raise ValueError(f"{cid}: wall consumes interior at layer {y}")
                ring = []
                for z in range(z0,z1):
                    for x in range(x0,x1):
                        if params["section_shape"] == "rectangle":
                            outer = True
                            inner = x0+wall <= x < x1-wall and z0+wall <= z < z1-wall
                        else:
                            dx, dz = x+.5-(x0+x1)/2, z+.5-(z0+z1)/2
                            outer = (dx/(width/2))**2+(dz/(depth/2))**2 <= 1
                            inner = (dx/(width/2-wall))**2+(dz/(depth/2-wall))**2 <= 1
                        if not outer:
                            continue
                        if y in floor_ys:
                            mat = params["floor_material"]
                        elif not inner:
                            mat = comp["material"]
                            pitch = q(params["mullion_pitch_m"], scale)
                            if pitch and (x % pitch == 0 or z % pitch == 0):
                                mat = params["mullion_material"]
                        else:
                            continue
                        put((x,y,z), comp, mat)
                        ring.append((x,z))
                rows.append({"y": y, "width_blocks": max(v[0] for v in ring)-min(v[0] for v in ring)+1,
                             "depth_blocks": max(v[1] for v in ring)-min(v[1] for v in ring)+1,
                             "floor": y in floor_ys})
            profiles[cid] = rows
        else:
            raise ValueError(f"Unsupported geometry: {kind}")
        components.append({"component_id":cid,"kind":kind,"net_block_change":len(scene.blocks)-before})
    if not scene.blocks:
        raise ValueError("Empty result")
    if len(scene.blocks) > spec["environment"]["budgets"]["max_non_air_blocks"]:
        raise ValueError("Non-air block budget exceeded")
    if spec.get("schema_version")=="0.2" and spec["assembly"]["overlap_policy"]=="reject_undeclared":
        allowed={(x["earlier"],x["later"]) for x in spec["assembly"]["allowed_overlaps"]}
        unexpected=set(overlaps)-allowed
        if unexpected:raise ValueError("Undeclared component overlaps: "+str(sorted(unexpected)))
    return scene, {"overlaps":[{"earlier":a,"later":b,"cell_writes":n} for (a,b),n in sorted(overlaps.items())],"events": components, "profiles": profiles, "quantization": quantization, "cell_visits": changed_total}

