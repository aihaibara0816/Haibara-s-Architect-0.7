# Source revisions remain explicit; construction retains structural frames.
from pathlib import Path
p=Path(__file__).with_name('build.py');s=p.read_text()
s=s.replace("# Household yard detail kept away from entry and stair routes.","""# Household yard detail kept away from entry and stair routes.
 # Unequal side courts: a low wall, open gate, lean-to roof and work bench.
 if kind in ['old','finished']:
  for aa in range(-3,LW+3):
   if aa not in range(5,11):put(aa,g+1,-5,'bricks' if kind=='old' else 'smooth_sandstone','court.wall')
  if int(tid[1:])%2==0:
   for aa in range(-3,2):
    for cc in range(LD-4,LD+2):put(aa,g+4,cc,M('dark_oak_slab',type='bottom'),'shed.roof')
   for aa in [-3,1]:
    for cc in [LD-4,LD+1]:box(aa,cc,aa+1,cc+1,g+1,g+4,'oak_log','shed.post')
   box(-2,LD-3,1,LD,g+1,g+2,'oak_planks','shed.workbench')
""")
s=s.replace("# Shade trees at irregular corners", """# Replace ornamental lawn gaps with working ground and irregular kitchen gardens.
for zz in range(58,250):
 for xx in range(44,266):
  if not village[zz,xx] or blocked[zz,xx] or (xx,zz) in roads:continue
  gg=int(ground[zz,xx]);near=min((max(t['x']-xx,0,xx-t['x']-t['w'])**2+max(t['z']-zz,0,zz-t['z']-t['d'])**2)**.5 for t in houses)
  if near<10:
   b.put(xx,gg,zz,'coarse_dirt' if (xx+2*zz)%13 else 'gravel','court.workground')
  elif ((xx-217)/23)**2+((zz-196)/29)**2<1 or ((xx-218)/24)**2+((zz-81)/16)**2<1:
   if (xx+zz//10)%8==0:b.put(xx,gg,zz,'water','garden.irrigation')
   elif xx%3!=0:b.put(xx,gg,zz,'farmland','garden.soil');b.put(xx,gg+1,zz,M('carrots',age=7),'garden.crop')
# Shade trees at irregular corners""")
s=s.replace("out=save_run(C,'V1'","out=save_run(C,'V2'")
p.write_text(s)
