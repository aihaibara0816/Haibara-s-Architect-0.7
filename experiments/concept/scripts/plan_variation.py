#!/usr/bin/env python3
"""Assign bounded material variation to authored facade panels; no geometry generation."""
import argparse
import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ALGORITHM = "haa-facade-variation/0.1"
SYSTEMS = {"solid", "slit", "ribbon", "glazed", "screen", "loggia"}
GLAZED = {"slit", "ribbon", "glazed", "screen", "loggia"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bounded(value, label, low=0.0, high=1.0):
    require(isinstance(value, (int, float)) and not isinstance(value, bool), label + " must be numeric")
    require(math.isfinite(value) and low <= value <= high, f"{label} outside {low}..{high}")
    return float(value)


def random01(seed, *keys):
    raw = json.dumps([seed, *keys], ensure_ascii=False, separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") / 2**64


def weather_intensity(parameters):
    age = bounded(parameters.get("age_years", 0), "age_years", 0, 1000)
    maintenance = bounded(parameters.get("maintenance", 0.9), "maintenance")
    exposure = bounded(parameters.get("exposure", 0.5), "exposure")
    renovation = parameters.get("years_since_renovation")
    if renovation is not None:
        age = min(age, bounded(renovation, "years_since_renovation", 0, 1000))
    override = parameters.get("weather_override")
    if override is not None:
        return bounded(override, "weather_override")
    return min(age / 80, 1) * (0.2 + 0.8 * (1 - maintenance)) * (0.6 + 0.4 * exposure)


def unique(items, label):
    result = {}
    for item in items:
        require(isinstance(item, dict), label + " entry must be an object")
        key = item.get("id")
        require(isinstance(key, str) and bool(key), label + " needs a nonempty id")
        require(key not in result, label + " duplicate id: " + key)
        result[key] = item
    return result


def plan(spec):
    require(spec.get("schema") == "HAA_facade_authoring/0.1", "unsupported schema")
    seed = spec.get("seed", 20261026)
    require(isinstance(seed, (str, int)) and not isinstance(seed, bool), "seed must be integer or string")
    parameters = spec.get("parameters", {})
    ratio = bounded(parameters.get("glass_accent_ratio", 0.06), "glass_accent_ratio", 0, 0.25)
    planter_density = bounded(parameters.get("planter_density", 0.35), "planter_density")
    intensity = weather_intensity(parameters)
    regions = unique(spec.get("regions", []), "regions")
    panels = unique(spec.get("panels", []), "panels")
    candidates = unique(spec.get("planter_candidates", []), "planter_candidates")
    require(regions and panels, "authored regions and panels are required")
    for rid, region in regions.items():
        palette = region.get("glass_palette", {})
        require(isinstance(palette.get("primary"), str) and palette["primary"], rid + " primary glass missing")
        accents = palette.get("accents", [])
        require(isinstance(accents, list) and all(isinstance(a, str) and a for a in accents), rid + " invalid accents")
        require(palette["primary"] not in accents, rid + " accent duplicates primary")
        if "glass_accent_ratio" in region:
            bounded(region["glass_accent_ratio"], rid + " ratio", 0, 0.25)
    for pid, panel in panels.items():
        require(panel.get("region_id") in regions, pid + " unknown region")
        require(panel.get("system") in SYSTEMS, pid + " unknown system")
        require(panel.get("face") in {"S", "E", "N", "W"}, pid + " invalid face")
        require(isinstance(panel.get("component_id"), str) and panel["component_id"], pid + " missing component")
        for axis in ["floor", "bay"]:
            require(isinstance(panel.get(axis), int) and not isinstance(panel[axis], bool), pid + " invalid " + axis)
        bounded(panel.get("exposure", 0.5), pid + " exposure")
    accent_ids = set()
    region_stats = []
    for rid in sorted(regions):
        region = regions[rid]
        eligible = [p for p in panels.values() if p["region_id"] == rid and p["system"] in GLAZED and not p.get("protected", False)]
        region_ratio = region.get("glass_accent_ratio", ratio)
        target = math.floor(len(eligible) * region_ratio) if region["glass_palette"].get("accents") else 0
        # Stable cluster order encourages adjacent groups up to three bays.
        ranked = sorted(eligible, key=lambda p: (
            random01(seed, "glass-cluster", rid, p["face"], p["floor"], p["bay"] // 3),
            random01(seed, "glass-member", p["id"]), p["id"]))
        accent_ids.update(p["id"] for p in ranked[:target])
        region_stats.append({"region_id": rid, "eligible_glass_panels": len(eligible), "accent_panels": target,
                             "actual_accent_ratio": target / len(eligible) if eligible else 0})
    assignments = []
    for pid in sorted(panels):
        panel = panels[pid]
        rid = panel["region_id"]
        palette = regions[rid]["glass_palette"]
        material = palette["primary"] if panel["system"] in GLAZED else None
        if pid in accent_ids:
            accents = palette["accents"]
            index = int(random01(seed, "glass-tone", rid, panel["face"], panel["floor"], panel["bay"] // 3) * len(accents))
            material = accents[index]
        cluster = random01(seed, "wall-cluster", rid, panel["face"], panel["floor"] // 2, panel["bay"] // 3)
        local = random01(seed, "wall-local", pid)
        level = intensity * (0.4 + 0.6 * panel.get("exposure", 0.5)) * (0.45 + 0.45 * cluster + 0.1 * local)
        if panel.get("protected", False) or not panel.get("allow_weather", True):
            level = 0
        result = copy.deepcopy(panel)
        result.update({"glass_material": material, "glass_is_accent": pid in accent_ids,
                       "weather_level": round(level, 6),
                       "weather_hint": "surface-mask-required" if level > 0 else "none"})
        assignments.append(result)
    planters = []
    for cid in sorted(candidates):
        candidate = candidates[cid]
        # This checks authored declarations, not geometric support or collision.
        eligible = (bool(candidate.get("support_ref")) and candidate.get("support_confirmed") is True
                    and candidate.get("clear_of_routes") is True and not candidate.get("protected", False))
        group = candidate.get("group_id", cid)
        selected = eligible and random01(seed, "planter-group", group) < planter_density
        planters.append({**copy.deepcopy(candidate), "eligible": eligible, "selected": selected,
                         "vegetation_variant": int(random01(seed, "foliage", cid) * 3) if selected else None})
    canonical = copy.deepcopy(spec)
    for key in ["regions", "panels", "planter_candidates"]:
        canonical[key] = sorted(canonical.get(key, []), key=lambda p: p["id"])
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"schema": "HAA_facade_variation/0.1", "algorithm": ALGORITHM, "seed": seed,
            "authoring_spec_sha256": digest, "parameters": parameters,
            "effective_weather_intensity": round(intensity, 6), "panels": assignments, "planters": planters,
            "summary": {"systems": dict(sorted(Counter(p["system"] for p in assignments).items())),
                        "regions": region_stats, "selected_planter_candidates": sum(p["selected"] for p in planters)},
            "status": "proposed_material_assignment",
            "limits": ["authored facade geometry required", "planter geometry needs separate verification",
                       "weathering needs spatial masks", "not an HAF adapter or game check"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = plan(json.loads(args.input.read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out), "panels": len(result["panels"]),
                      "weather_intensity": result["effective_weather_intensity"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
