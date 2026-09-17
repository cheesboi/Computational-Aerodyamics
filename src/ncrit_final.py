"""Ncrit sweep at every Reynolds number, with two screens.

Screen 1 (residual):  reject a point XFOIL did not converge.
Screen 2 (physics):   the TRIPPED drag must be independent of Ncrit, because XTR
                      bypasses the e^N model.  A tripped point that moves with Ncrit
                      converged to the wrong branch, and no residual test can catch
                      that.  Reject the angle outright.
Only angles that survive BOTH screens at ALL Ncrit values are used, so every column
of the sweep is averaged over an identical set of angles.
"""
import sys, json, numpy as np, subprocess, re
sys.path.insert(0,"/root/aero")
from parse_v4 import read_v4
RMS=re.compile(r"^\s*(\d+)\s+rms:\s*([-\d.E+]+)",re.M)
RES=re.compile(r"a =\s*([-\d.]+)\s+CL =\s*([-\d.]+).*?CD =\s*([\d.]+)",re.S)
def run(dat,alpha,Re,ncrit=9,xtr=None,iters=300):
    vpar=f"N {ncrit}\n"+(f"XTR {xtr[0]} {xtr[1]}\n" if xtr else "")
    cmds=f"PLOP\nG F\n\nLOAD {dat}\nAF\nOPER\nVPAR\n{vpar}\nVISC {Re}\nITER {iters}\nALFA {alpha}\n\nQUIT\n"
    try: o=subprocess.run(["xfoil"],input=cmds,capture_output=True,text=True,timeout=30).stdout
    except subprocess.TimeoutExpired: return None
    it=RMS.findall(o); h=RES.findall(o)
    if not h or not it or int(it[-1][0])>=iters or abs(float(it[-1][1]))>1e-4: return None
    return float(h[-1][2])
CASES={"E387":("e387_c_drg","e387_tf_drg","/tmp/xf/e387.dat"),
       "FX 63-137":("fx63137_c_drg","fx63137_tf_drg","/tmp/xf/fx63137.dat"),
       "SD2030":("sd2030_c_drg","sd2030_tf_drg","/tmp/xf/sd2030_239.dat")}
def nom(Re):
    for t in (100000,150000,200000,250000,300000,350000,500000):
        if abs(Re-t)/t<0.06: return t
    return int(round(Re,-4))
def ic(rows,a):
    A=np.array([r["alpha"] for r in rows]);C=np.array([r["cd"] for r in rows]);o=np.argsort(A)
    return float(np.interp(a,A[o],C[o])) if A.min()<=a<=A.max() else None
AL=[0.,2.,4.,6.,8.]; NC=(7,9,11,13); TOL=0.10
out={}; rejected=[]
for name,(cf,tf,dat) in CASES.items():
    C={nom(b["Re"]):b for b in read_v4(f"/root/aero/uiuc/{cf}.txt") if len(b["rows"])>5}
    T={nom(b["Re"]):b for b in read_v4(f"/root/aero/uiuc/{tf}.txt") if len(b["rows"])>5}
    out[name]={}
    for Re in sorted(set(C)&set(T)):
        good=[]
        grid={}
        for a in AL:
            ec=ic(C[Re]["rows"],a); et=ic(T[Re]["rows"],a)
            cs=[run(dat,a,Re,ncrit=n) for n in NC]
            ts=[run(dat,a,Re,ncrit=n,xtr=(0.02,0.05)) for n in NC]
            if ec is None or et is None or any(x is None for x in cs+ts):
                rejected.append((name,Re,a,"non-convergence")); continue
            if (max(ts)-min(ts))/np.mean(ts) > TOL:
                rejected.append((name,Re,a,f"tripped drag moved with Ncrit by "
                                           f"{100*(max(ts)-min(ts))/np.mean(ts):.0f}%")); continue
            good.append(a); grid[a]=(ec,et,cs,ts)
        if not good: continue
        ec=np.array([grid[a][0] for a in good]); et=np.array([grid[a][1] for a in good])
        ex=float(100*np.mean((et-ec)/ec))
        vals={}
        for j,n in enumerate(NC):
            c=np.array([grid[a][2][j] for a in good]); t=np.array([grid[a][3][j] for a in good])
            vals[n]=float(100*np.mean((t-c)/c))
        v=list(vals.values())
        out[name][Re]=dict(exp=ex,vals=vals,n=len(good),spread=max(v)-min(v),
                           crosses=bool(min(v)<=ex<=max(v)))
print("ANGLES REJECTED")
for r in rejected: print(f"   {r[0]:<11} Re={r[1]:>7,}  alpha={r[2]:+.0f}   {r[3]}")
print(f"   total {len(rejected)}\n")
print(f"{'airfoil':<11}{'Re':>8}{'n':>3}{'measured':>10}" + "".join(f"{'N='+str(n):>9}" for n in NC)
      + f"{'spread':>9}{'reachable?':>12}")
for name,d in out.items():
    for Re,v in d.items():
        print(f"{name:<11}{Re/1000:>7.0f}k{v['n']:>3}{v['exp']:>+9.1f}%" +
              "".join(f"{v['vals'][n]:>+8.1f}%" for n in NC) +
              f"{v['spread']:>8.1f}{('YES' if v['crosses'] else 'no'):>12}")
json.dump(out,open("/root/aero/ncrit_final.json","w"),indent=1)
print("\nmax observed tripped-drag movement across Ncrit, by accepted angle:")
print(f"   tolerance used: {100*TOL:.0f}%")
