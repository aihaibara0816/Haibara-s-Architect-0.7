"""Bounded, addressable variation plans; this module does not place blocks."""
from __future__ import annotations

import hashlib
import json

ALGORITHM = "haf-addressed-choice-sha256-v1"


class VariationError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def require(condition, message):
    if not condition:
        raise VariationError(message)


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def box(value):
    require(isinstance(value, list) and len(value) == 6 and all(integer(v) for v in value),
            "bounds_xyz requires six integers")
    require(all(value[i] < value[i + 3] for i in range(3)), "bounds_xyz must have positive volume")
    return value


def inside(a, b):
    return all(b[i] <= a[i] and a[i + 3] <= b[i + 3] for i in range(3))


def overlaps(a, b):
    return all(a[i] < b[i + 3] and b[i] < a[i + 3] for i in range(3))


def identifier(value, field):
    require(isinstance(value, str) and value and value == value.strip() and len(value) <= 160
            and not any(ord(char) < 32 for char in value), field + " must be a nonempty stable ID without edge whitespace/control characters")
    return value


def is_locked(component_id, locked):
    return any(component_id == p or component_id.startswith(p + ".") for p in locked)


def choose(seed, channel_id, channel_seed, component_id, choices):
    address = [ALGORITHM, seed, channel_id, channel_seed, component_id]
    digest = hashlib.sha256(canonical(address)).hexdigest()
    # Integer weights avoid float-dependent ordering or global RNG state.
    total = sum(c["weight"] for c in choices)
    ticket = int(digest, 16) % total
    for option in sorted(choices, key=lambda c: c["id"]):
        ticket -= option["weight"]
        if ticket < 0:
            return option["id"], digest
    raise AssertionError("unreachable weighted choice")


def compile_variation(spec):
    require(isinstance(spec, dict), "variation must be an object")
    require(set(spec) <= {"schema_version", "seed", "channels", "targets", "editable_regions", "keepouts", "locked_component_ids"},
            "unknown variation field; no commands or executable expressions are accepted")
    require(spec.get("schema_version") == "0.6", "explicit variation schema_version 0.6 required")
    seed = spec.get("seed")
    require(integer(seed), "seed must be an integer")
    require(isinstance(spec.get("editable_regions"), list), "editable_regions must be a list")
    regions = [box(b) for b in spec["editable_regions"]]
    require(regions, "explicit editable_regions required")
    require(isinstance(spec.get("keepouts", []), list), "keepouts must be a list")
    keepouts = [box(b) for b in spec.get("keepouts", [])]
    locked = spec.get("locked_component_ids", [])
    require(isinstance(locked, list), "locked_component_ids must be a list")
    for p in locked:
        identifier(p, "locked_component_id")
    require(len(locked) == len(set(locked)), "duplicate locked component ID")
    channels = {}
    require(isinstance(spec.get("channels"), list), "channels must be a list")
    for channel in spec["channels"]:
        require(isinstance(channel, dict) and set(channel) <= {"id", "seed", "choices"}, "invalid channel fields")
        cid = identifier(channel.get("id"), "channel.id")
        require(cid not in channels, "duplicate channel ID: " + cid)
        cseed = channel.get("seed", 0)
        require(integer(cseed), "channel seed must be an integer")
        require(isinstance(channel.get("choices"), list) and channel["choices"], "channel choices required")
        choices, seen = [], set()
        for choice in channel["choices"]:
            require(isinstance(choice, dict) and set(choice) <= {"id", "weight"}, "choice must contain only id and optional weight")
            oid = identifier(choice.get("id"), "choice.id")
            weight = choice.get("weight", 1)
            require(oid not in seen, "duplicate choice ID")
            require(integer(weight) and 1 <= weight <= 1000000, "weight must be an integer in 1..1000000")
            seen.add(oid)
            choices.append({"id": oid, "weight": weight})
        channels[cid] = {"seed": cseed, "choices": choices}
    require(channels, "at least one channel required")
    require(isinstance(spec.get("targets"), list), "targets must be a list")
    targets, seen, entries = [], set(), []
    for target in spec["targets"]:
        require(isinstance(target, dict) and set(target) <= {"component_id", "bounds_xyz", "channels", "frozen", "existing_choices"}, "invalid target fields")
        tid = identifier(target.get("component_id"), "component_id")
        require(tid not in seen, "duplicate component ID: " + tid)
        seen.add(tid)
        bb = box(target.get("bounds_xyz"))
        require(any(inside(bb, r) for r in regions), "target outside editable regions: " + tid)
        require(not any(overlaps(bb, k) for k in keepouts), "target intersects keepout: " + tid)
        require(not any(overlaps(bb, previous["bounds_xyz"]) for previous in targets), "variation target bounds overlap: " + tid)
        selected_channels = target.get("channels")
        require(isinstance(selected_channels, list) and selected_channels and all(isinstance(c, str) for c in selected_channels), "target channels must be nonempty IDs")
        require(len(selected_channels) == len(set(selected_channels)), "duplicate target channel")
        require(set(selected_channels) <= set(channels), "target refers to unknown channel")
        frozen = target.get("frozen", False)
        require(isinstance(frozen, bool), "frozen must be boolean")
        existing = target.get("existing_choices", {})
        require(isinstance(existing, dict) and set(existing) <= set(selected_channels), "existing_choices must refer to target channels")
        for c, value in existing.items():
            identifier(value, "existing choice")
        frozen = frozen or is_locked(tid, locked)
        if frozen:
            require(set(existing) == set(selected_channels), "frozen target needs an existing choice for every channel: " + tid)
        targets.append(target)
        for cid in sorted(selected_channels):
            if frozen:
                value, address_hash = existing[cid], None
            else:
                ch = channels[cid]
                value, address_hash = choose(seed, cid, ch["seed"], tid, ch["choices"])
            entries.append({"component_id": tid, "channel": cid, "choice_id": value,
                            "bounds_xyz": list(bb), "status": "frozen_existing" if frozen else "planned_choice",
                            "address_sha256": address_hash})
    entries.sort(key=lambda e: (e["component_id"], e["channel"]))
    return {"schema_version": "0.6", "algorithm": ALGORITHM, "seed": seed,
            "entries": entries, "choice_plan_sha256": hashlib.sha256(canonical(entries)).hexdigest(),
            "status": "planned_not_generated", "generated_geometry": False, "game_status": "pending",
            "limits": ["Choice IDs are semantic labels, not arbitrary executable code or automatic material bindings",
                       "Bounds and keepouts are caller-provided; no terrain survey or collision simulation is performed",
                       "This planner does not change positions, openings, floors or silhouettes",
                       "Choice probability uses integer hash modulo total weight; it is not a cryptographic lottery"]}
