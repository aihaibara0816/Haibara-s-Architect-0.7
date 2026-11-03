# Civic V0.3.2 / lighting and bamboo garden revision

Current: `runs/v03_r13_lighting`. NBT SHA-256 1e8b8c4516b8d0e0b26c0fc343de9faf18d0b296c2de850fdf5ca34889a96fb4; 138018 non-air blocks in 144 x 78 x 120. Fourteen immutable outputs total (one massing, one facade sample, twelve complete versions). R10 interior organization is retained.

Latest user feedback: lighting too sparse and entrance bamboo garden missing. `revise_lighting_garden.py` consumes R10, keeps all 241 prior emissive blocks and adds fixed ambient, corridor, landing, atrium, bridge, terrace and garden lighting. Final 1857 emissive blocks / 791 added fixture groups. Some new lighting is flush in existing floor/slab/core-wall blocks; their solid geometry is unchanged. All R10 window states, ledges, screens, stairs, furniture and visual columns are exact.

Two raised bamboo planters sit outside the ground-floor footprint, with benches, moss, white flowers and low garden lamps. 29 native minecraft:bamboo stalks, heights 5–9 blocks; stop-growth tips. Official Java 1.21.1 client model stem dimensions are recorded in input/bamboo_reference. Foliage is simplified only in the offline preview; NBT uses real vanilla states.

R11 failed: west planter occupied source circulation cells. R12 moved planting into the forecourt; preview still showed dark stairwell corners. R13 added inset core-wall lights and F1 corner fixtures. Source and failure results retained. No mutation of original V0.3 handoff.

23 base + 15 interior + 11 lighting/garden checks pass. 39 executable core tests pass; three older checks cannot run in this compact source snapshot (research_lab and historical CTF model fixtures absent). Independent floor sampling in the conservative preview lightfield improves from 21.4–52.9% nonzero to 98.0–99.8%; this is not actual game lighting or lux. 31 final views, seven floor plans, two sections and seven cropped sample NBTs. Real game import/material/lighting checks and user aesthetic approval remain pending.

Previous context: 75 frozen window groups, 401 source rectangles, 113 ledges / 87 planted. Source +Z north maps to model -Z north. Two blocks per design metre. Sparse NBT does not clear existing air. Suggested origin Y64. 51 visual columns / 142 furniture groups retained from R10, not structural engineering. Elevator shafts and doors remain static. No new photo reconstruction or AI model training.
