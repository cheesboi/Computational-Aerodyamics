import sys, json, numpy as np
sys.path.insert(0,"/root/aero"); sys.path.insert(0,"/tmp/xf")
from parse_v4 import read_v4
from trip2 import xfoil_point
CASES={"E387":("e387_c_drg","e387_tf_drg","/tmp/xf/e387.dat"),
       "FX 63-137":("fx63137_c_drg","fx63137_tf_drg","/tmp/xf/fx63137.dat"),
       "SD2030":("sd2030_c_drg","sd2030_tf_drg","/tmp/xf/sd2030_239.dat")}
GRID=[-2.,0.,2.,4.,6.,8.,10.]
def nom(Re):
    for t in (100000,150000,200000,250000,300000,350000,450000,500000):
        if abs(Re-t)/t<0.06: return t
    return int(round(Re,-4))
def ic(rows,a):
    A=np.array([r["alpha"] for r in rows]);C=np.array([r["cd"] for r in rows]);o=np.argsort(A)
    return float(np.interp(a,A[o],C[o])) if A.min()<=a<=A.max() else None
raw={}
for name,(cf,tf,dat) in CASES.items():
    C={nom(b["Re"]):b for b in read_v4(f"/root/aero/uiuc/{cf}.txt") if len(b["rows"])>5}
    T={nom(b["Re"]):b for b in read_v4(f"/root/aero/uiuc/{tf}.txt") if len(b["rows"])>5}
    raw[name]={}
    for Re in sorted(set(C)&set(T)):
        rows=[]
        for a in GRID:
            ec=ic(C[Re]["rows"],a); et=ic(T[Re]["rows"],a)
            f=xfoil_point(dat,a,Re); g=xfoil_point(dat,a,Re,xtr=(0.02,0.05))
            rows.append({"alpha":a,"exp_clean":ec,"exp_trip":et,
                         "xf_clean":f[1] if f else None,"xf_trip":g[1] if g else None,
                         "ok": ec is not None and et is not None and bool(f) and bool(g)})
        raw[name][str(Re)]=rows
json.dump(raw,open("/root/aero/rung4_raw.json","w"),indent=1)
print("saved", sum(len(v) for v in raw.values()), "Re blocks")
