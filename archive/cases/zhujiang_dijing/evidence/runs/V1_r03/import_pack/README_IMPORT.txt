Zhujiang Dijing HAF V1 / final V1_r03

Representative lakeside residential group plus garden; interpreted layout, not surveyed site plan.
Scene size X/Y/Z = 232/104/190 blocks. Local east +X, north -Z; geographic bearing not measured.

Choose ONE import method:
1. Sponge v3 .schem: explicit air, importer may clear all volume cells.
2. Full sparse structure .nbt: writes only listed blocks; does not clear old blocks.
3. Eight sparse .nbt modules: place each minimum corner at common origin + module_offsets.csv offsets, no rotation.
Do not overlay methods. Module byte sizes <=256 KiB do not guarantee importer compatibility.
DataVersion 3955. Requires Java block states including green glass panes, slabs, stairs, walls, leaves, water level 0.
Ground surface local Y=3. Check minimum world Y <= origin Y and origin Y+104 <= world top exclusive bound.

Offline NBT/readback and exact module assembly passed. Game import, collision, fluid updates and lighting remain PENDING.
Full building interior/circulation is not reconstructed; rooms are window-back furnishing alcoves.
Materials.csv lists block IDs and counts; blockstates.csv lists exact states.
