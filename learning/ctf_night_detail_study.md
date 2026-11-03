# CTF V1 feedback: night patterns and fine components, 2026-10-23

Case study: `cases/guangzhou_ctf/experiments/detail_v2`.
This is local rule/geometry work, not model training and not an accepted full V2.

## Evidence and consumers

- User U01: roof edges; U02: night scheme. Two additional LPA photos viewed, recorded under `research/detail_study_v2/night_sources.json`. Use LPA01 for upper vertical accents / transverse warm segment, LPA02 for future podium refinement; do not copy neighbouring IFC rings.
- `study.py`: three facade samples share 24 furnished units and seed. Walls preserve pale terracotta character but are thick; bars look thinner/darker, with simplified preview geometry; hybrid remains candidate.
- `hafusion/interiors.py`: room-ID deterministic furnishing choices; one-cell clearance excludes two-cell leaf planters; not real interior reconstruction. Actual local scenes validate collision-free placement.
- `night_study.py`: V1 geometry with fixed lamps on trial +Z/-X working faces. One horizontal row at Y101 (198m, explicitly provisional); upper vertical accents. No changes to random room lighting or roof. 306 changed cells; exact diff excludes glazing/fins changes.
- Initial r00 was rejected because 13 pane connections changed. New horizontal-adjacency guard protects neighbouring panes. Rejected artifact is retained as evidence, excluded from delivery NBT sample pack.
- `support/detail_lab/shading.py` + `support/vendor/render_egl.py`: old shader flattened all emission to the same pale hue. Material policy retains glowstone/sea-lantern surface colours, legacy policy still callable. Scalar block-light propagation remains approximate; no RGB light or blinking claim.
- `states.py`, `mesh.py`: bookshelf, anvil, redstone torch support for samples. Anvil elements checked against official 1.21.1 template. Iron bars remain simplified opaque state boxes, not game alpha textures.

## Results and limits

23 core tests passed. Every sample exported and read back exactly; 29 preserved V1 asset hashes unchanged. Four directional day/night views and four full-crown views use fixed scale and target. Report and plates use actual NBT-derived renders, no generated illustration substitutes.

Night visual review: warmer band is readable; upper lighting has interruptions, and current window lights/scalar spill remain too competitive. Do not call this as-built lighting fidelity achieved. Podium source is now stronger but podium geometry/lighting was not refined here.

A 3×3 beacon casing means roughly 6m width at this 1:2 representation. A 1×1 recessed red cap is the more restrained candidate; redstone torch is smaller but weak in distant views. Locations are trial positions, not confirmed obstruction-light placements. Red glass does not establish coloured radiance or a flashing circuit.

Roof geometry unchanged: actual crown top rows range Y261–266. ±X views expose the slope, ±Z less so; multi-view renders do not establish real slope accuracy. Warehouse candidates return 403; Sketchfab public metadata/thumbnail obtained, authorised download endpoint returns 401. No mesh has been imported or fused.

## Replay

Use the archive's requirements and support deps; see existing README. Core checks: `PYTHONPATH=support/deps python3 -m unittest discover -s tests -v`.

Existing generated runs are immutable. To build afresh, copy the project to a fresh directory and move only the copied study `runs/` and `review/previews/` aside; keep original `cases/guangzhou_ctf/runs/V1/building.nbt` and `review/assets/render_shader_reference.html`. Then run `python cases/guangzhou_ctf/experiments/detail_v2/study.py`, followed by `night_study.py`. For report rebuilding, `python .../package_study.py`. It needs preserved V1 previews and source images. The packaging script writes only the study deliverables.

Next acceptance: obtain verified roof/model geometry, calibrate actual north, identify rear lighting, refine crown line continuity without touching panes, compare in Minecraft Java 1.21.1 with declared resource pack/shader, then decide which components to incorporate. Preserve V1 until user feedback on the study.
