import json, numpy as np
R=json.load(open("/root/aero/rung4_raw.json"))
WINDOWS=[(0,4),(0,8),(2,8),(0,10),(-2,8),(4,10)]
def sel(rows,lo,hi):
    return [r for r in rows if r["ok"] and lo-1e-6<=r["alpha"]<=hi+1e-6]
def mr(rows,num,den):  # mean of per-alpha ratios, %
    v=[100*(r[num]-r[den])/r[den] for r in rows]
    return float(np.mean(v)) if v else None

def stats(name,Re,fn):
    rows_all=R[name][str(Re)]
    vals=[fn(sel(rows_all,lo,hi)) for lo,hi in WINDOWS]
    vals=[v for v in vals if v is not None]
    base=fn(sel(rows_all,0,8))
    return base,min(vals),max(vals)

print("TABLE 1 -- clean-configuration drag, XFOIL vs wind tunnel")
print("            (mean of per-angle percentage errors; base window 0-8 deg)")
print(f"{'airfoil':<11}{'Re':>8}{'n':>4}{'error':>9}{'range over 6 windows':>26}{'Selig 95% CI':>15}")
for name in R:
    for Re in sorted(R[name],key=int):
        n=len(sel(R[name][Re],0,8))
        b,lo,hi=stats(name,int(Re),lambda s: mr(s,"xf_clean","exp_clean"))
        ci=3.0 if int(Re)<1.5e5 else 1.5
        print(f"{name:<11}{int(Re)/1000:>7.0f}k{n:>4}{b:>+8.1f}%{f'[{lo:+.1f}, {hi:+.1f}]':>26}{f'+/-{ci}%':>15}")

print("\nTABLE 2 -- tripped-configuration drag, XFOIL vs wind tunnel")
print(f"{'airfoil':<11}{'Re':>8}{'n':>4}{'error':>9}{'range over 6 windows':>26}")
for name in R:
    for Re in sorted(R[name],key=int):
        n=len(sel(R[name][Re],0,8))
        b,lo,hi=stats(name,int(Re),lambda s: mr(s,"xf_trip","exp_trip"))
        print(f"{name:<11}{int(Re)/1000:>7.0f}k{n:>4}{b:>+8.1f}%{f'[{lo:+.1f}, {hi:+.1f}]':>26}")

print("\nTABLE 3 -- effect of the trip on drag: experiment vs XFOIL")
print(f"{'airfoil':<11}{'Re':>8}{'n':>4}{'exp (0-8)':>11}{'exp range':>20}{'XF (0-8)':>10}{'XF range':>20}{'':>3}")
for name in R:
    for Re in sorted(R[name],key=int):
        n=len(sel(R[name][Re],0,8))
        eb,el,eh=stats(name,int(Re),lambda s: mr(s,"exp_trip","exp_clean"))
        xb,xl,xh=stats(name,int(Re),lambda s: mr(s,"xf_trip","xf_clean"))
        sep = eh<xl or xh<el
        print(f"{name:<11}{int(Re)/1000:>7.0f}k{n:>4}{eb:>+10.1f}%{f'[{el:+.1f}, {eh:+.1f}]':>20}"
              f"{xb:>+9.1f}%{f'[{xl:+.1f}, {xh:+.1f}]':>20}{'  *' if sep else ''}")
print("\n  * = the two ranges do not overlap")
