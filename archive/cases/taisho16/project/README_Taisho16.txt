木漏日溪谷 / Taisho16 / HAF 0.4 / V09

320 x 92 x 288 blocks. 18 principal buildings + forest lookout pavilion.
Java 1.21.1 (DataVersion 3955), vanilla block IDs, authored terrain.
A continuous descending creek passes from the upper forest through the settlement.
Two 7-block main streets, a nominal 5-block west loop and 3-block branches are reserved before building placement.
The rejected Clock module is retired. Hall replaces it as an occupied public meeting, reading and information building.
17 independent building NBTs retain byte-identical T15 building/interior geometry. Their rotated scene placements are new.

Deliverables
- delivery/Taisho16.html: self-contained viewer with day/night, four directions, districts, individual buildings, interior/floor/section/layer views and embedded NBT/world downloads.
- delivery/Taisho16_World_1.21.1.zip: extract the enclosed folder into .minecraft/saves.
- runs/V09: final structures, exact-source checks, spatial records and terrain/road diagrams.
- input/selected_layout.json: frozen placement result from the bounded candidate search; not an arbitrary-terrain solution.
- src/build_valley.py, valley_terrain.py, valley_types.py: case generator and recipes.

Reproduction
Install requirements.txt; use Python with the provided src/support on its search path.
Run python src/build_valley.py NEW_RUN 151145 from this project.
The generator accepts an alternate seed but a general alternate-seed city solver is not claimed.
The explicit scene budget is increased to 12 million cells. Large terrain NBT is written in a bounded-memory stream.
The development-only resume_valley.py requires a scratch checkpoint not included in this distribution; build_valley.py is the reproducible entry point.
Run src/audit_quarter.py RUN Taisho16, then export_quarter_world.py RUN DESTINATION.
Official Minecraft client assets are not redistributed. Restore them using src/fetch_vanilla_assets.py and assets/vanilla_source.json before rendering.

Limits
All previews are offline approximations from final NBT, not Minecraft screenshots. The client has not been run.
Doors treated as operable/open for approximate path tests; client collision, lighting and waterfall updates require in-game review.
Exterior map boundaries meet a flat test-world margin. This is not unlimited vanilla forest world generation.
T07 is used for landscape relationships and reference comparison; this is not its directly enlarged terrain.
The clocktower tutorial page was readable but playback remained buffering. No tutorial footage or construction steps are claimed as studied.
T15's prior geometry pass does not override the user's aesthetic rejection. T16 aesthetics remain pending user review.
