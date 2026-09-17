"""Fit the Ncrit that best reproduces the measured CLEAN drag, per airfoil per Re.
If one value works everywhere, Ncrit is a property of the tunnel.
If it drifts, Ncrit is absorbing model error."""
import sys, json, numpy as np, subprocess, re
sys.path.insert(0,"/root/aero")
from parse_v4 import read_v4
RMS=re.compile(r"^\s*(\d+)\s+rms:\s*([-\d.E+]+)",re.M)
RES=re.compile(r"a =\s*([-\d.]+)\s+CL =\s*([-\d.]+).*?CD =\s*([\d.]+)",re.S)
def run(dat,alpha,Re,ncrit=9,iters=300):
    cmds=(f"PLOP\nG F\n\nLOAD {dat}\nAF\nOPER\nVPAR\nN {ncrit}\n\n"
          f"VISC {Re}\nITER {iters}\nALFA {alpha}\n\nQUIT\n")
    try: o=subprocess.run(["xfoil"],input=cmds,capture_output=True,text=True,timeout=30).stdout
    except subprocess.TimeoutExpired: return None
    it=RMS.findall(o); h=RES.findall(o)
    if not h or not it or int(it[-1][0])>=iters or abs(float(it[-1][1]))>1e-4: return None
    return float(h[-1][2])
CASES={"E387":("e387_c_drg","/tmp/xf/e387.dat"),
       "FX 63-137":("fx63137_c_drg","/tmp/xf/fx63137.dat"),
       "SD2030":("sd2030_c_drg","/tmp/xf/sd2030_239.dat")}
def nom(Re):
    for t in (100000,150000,200000,250000,300000,350000,500000):
        if abs(Re-t)/t<0.06: return t
    return int(round(Re,-4))
def ic(rows,a):
    A=np.array([r["alpha"] for r in rows]);C=np.array([r["cd"] for r in rows]);o=np.argsort(A)
    return float(np.interp(a,A[o],C[o])) if A.min()<=a<=A.max() else None
AL=[0.,2.,4.,6.,8.]; GRID=list(range(5,15))
out={}
print(f"{'airfoil':<11}{'Re':>8}{'n':>3}{'best Ncrit':>12}{'err there':>11}{'err at N=9':>12}")
for name,(cf,dat) in CASES.items():
    C={nom(b["Re"]):b for b in read_v4(f"/root/aero/uiuc/{cf}.txt") if len(b["rows"])>5}
    out[name]={}
    for Re in sorted(C):
        ex=[ic(C[Re]["rows"],a) for a in AL]
        curve={}
        for nc in GRID:
            xs=[run(dat,a,Re,ncrit=nc) for a in AL]
            k=[i for i in range(len(AL)) if xs[i] and ex[i]]
            if len(k)<3: continue
            e=np.array([ex[i] for i in k]); x=np.array([xs[i] for i in k])
            curve[nc]=(float(100*np.mean((x-e)/e)), len(k))
        if not curve: continue
        # best = Ncrit whose mean signed error is closest to zero, refined by linear interp
        ncs=sorted(curve); errs=[curve[n][0] for n in ncs]
        best=None
        for i in range(len(ncs)-1):
            if errs[i]*errs[i+1]<=0:
                f=abs(errs[i])/(abs(errs[i])+abs(errs[i+1]))
                best=ncs[i]+f*(ncs[i+1]-ncs[i]); break
        if best is None:
            best=ncs[int(np.argmin(np.abs(errs)))]
            tag=" (no zero crossing; nearest)"
        else: tag=""
        e9=curve.get(9,(float('nan'),0))[0]
        out[name][Re]=dict(best=float(best),err9=e9,curve={str(k):v for k,v in curve.items()})
        print(f"{name:<11}{Re/1000:>7.0f}k{curve[ncs[0]][1]:>3}{best:>12.1f}{0.0:>10.1f}%{e9:>+11.1f}%{tag}")
json.dump(out,open("/root/aero/ncrit_calib.json","w"),indent=1)
