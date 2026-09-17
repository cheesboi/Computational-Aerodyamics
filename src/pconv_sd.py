import sys, numpy as np
sys.path.insert(0,"/root/aero"); sys.path.insert(0,"/tmp/xf")
from trip import xfoil_point
import aerosandbox as asb

# build coordinate files at several panel densities
for n in (40, 60, 90, 120, 160):
    a = asb.Airfoil('sd2030').repanel(n_points_per_side=n)
    with open(f"/tmp/xf/sd_{n}.dat","w") as f:
        f.write("SD2030\n")
        for x,y in a.coordinates: f.write(f"{x:.6f} {y:.6f}\n")

Re = 100000
print(f"SD2030, Re = {Re:,}  --  panel convergence of the TRIP EFFECT")
print(f"{'pts/side':>9} {'total':>6} {'XF free':>9} {'XF trip':>9} {'trip effect':>13}")
for n in (40, 60, 90, 120, 160):
    dat=f"/tmp/xf/sd_{n}.dat"
    xc,xt=[],[]
    for a in (0.,2.,4.,6.,8.):
        f=xfoil_point(dat,a,Re); g=xfoil_point(dat,a,Re,xtr=(0.02,0.05))
        if not f or not g: continue
        xc.append(f[1]); xt.append(g[1])
    if not xc: print(f"{n:>9} {2*n-1:>6}   XFOIL FAILED"); continue
    xc,xt=np.array(xc),np.array(xt)
    print(f"{n:>9} {2*n-1:>6} {xc.mean():>9.5f} {xt.mean():>9.5f} {100*np.mean((xt-xc)/xc):>+12.1f}%")
