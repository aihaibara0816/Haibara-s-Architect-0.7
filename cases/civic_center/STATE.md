# Civic V0.3.3 / flush ceiling and complete forecourt

Current: `runs/v03_r16_ceiling_landscape`. 168775 non-air blocks, size 144 x 78 x 120. NBT SHA-256 5facdc6ad0ba108d9ff34c7e83d284836e449f10ab4786e277e3633bc8a84b9c.

Latest feedback: cubic lamps must be recessed; modern separators have upper floor plus lower ceiling/light layer; 1–9 floors should illuminate all functional spaces with material warmth differences. Redesign the whole forecourt as landscape architecture. User provided two garden tutorial links. Previous V0.3 windows and interior zoning remain protected.

`revise_ceiling_landscape.py` consumes immutable R13. Adds 30683 ceiling cells beneath existing upper floor/roof slabs, retaining upper finished levels; reduces ordinary clear height by one block (0.5 design metre). 192 edge/landing light cells are relocated into existing support slabs. Stair shafts, outdoor bridge/passage and perimeter reveals are exceptions. Atrium retains missing F2 slab; actual high ceiling becomes Y21 below slab Y22. All 39 functional spaces have light sources; 1867 total emissive blocks. Vanilla material colors do not create colored light propagation.

R13 two raised rectangular planters and bollards replaced with a whole forecourt inside X60..139, Z58..115: entrance gathering plaza, five connected routes, bamboo ribbon, three trees, clustered shrubs, wood pergola, 207-cell contained pond and viewing apron/seating. 22 native bamboo stalks. Inset paving/pond lights and thin pergola end rods. No fish entities. Explicit public paths remain clear at their full declared widths.

R14 failed: remaining drops, pane-arm diffs, pergola/path conflict and a validation approach point incorrectly placed in the pond. R15 fixed lights and refined shore/paving but still put one post into the gathering area. R16 corrected that interface. All immutable runs and their checks retained. Total 17 outputs: one massing, one facade sample, fifteen complete versions. 5 external panes changed connection arms relative to R13; coordinates/materials unchanged. 7 existing interior floor finish cells became same-size inset lights; furniture and visual columns remain unchanged.

23 base + 15 interior + 12 ceiling/landscape checks pass. Conservative grid preview nonzero floor samples are 98.0–99.8%; not real game light/lux or a spawn-safety certificate. 35 current fixed views, seven floor plans, three section images including a paired two-layer ceiling cut, seven cropped NBT samples. Core code unchanged in this revision; prior 39 executable tests / three unavailable old fixture tests remain historical evidence. Browser tests are recorded separately.

Video evidence: titles, authors and description/chapter metadata from public watch pages. Browser playback buffered and storyboard images were unavailable; no frames or complete viewing claimed. Source summary is review/source-video-evidence.json. Current garden is newly designed from the requested themes, not a copied tutorial layout.

Architect workflow rule version 0.3.1 saved separately: modern two-layer flush lights; medieval one-layer/lantern option; 1–9-floor all-functional-light default, explicit real-reference/user exceptions; full landscape planning and evidence discipline. Consumer support must be checked per case.

Still pending: actual Java1.21.1 / NeoForge21.1.244 import, vanilla bamboo/water/light/collision behavior and user aesthetic acceptance. Static elevators. Sparse NBT does not clear untouched air; use clear site. Suggested origin Y64, maximum242. 2 blocks/design metre; model north -Z, east +X. 75 groups /401 source window rectangles /113 ledges (87 planted),181 thin-gap quantization merges; 51 visual columns and142 furniture/partition groups. No structural engineering or model training claim.
