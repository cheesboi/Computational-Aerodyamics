"""Lift validation: XFOIL vs UIUC, CLmax and lift-curve slope."""
import sys, json, numpy as np, subprocess, re
sys.path.insert(0,"/root/aero")
from parse_lft import read_lft
RMS=re.compile(r"^\s*(\d+)\s+rms:\s*([-\d.E+]+)",re.M)
RES=re.compile(r"a =\s*([-\d.]+)\s+CL =\s*([-\d.]+).*?CD =\s*([\d.]+)",re.S)
def run(dat,alpha,Re,ncrit=9,iters=400):
    cmds=(f"PLOP\nG F\n\nLOAD {dat}\nAF\nOPER\nVPAR\nN {ncrit}\n\n"
          f"VISC {Re}\nITER {iters}\nALFA {alpha}\n\nQUIT\n")
    try: o=subprocess.run(["xfoil"],input=cmds,capture_output=True,text=True,timeout=35).stdout
    except subprocess.TimeoutExpired: return None
    it=RMS.findall(o); h=RES.findall(o)
    if not h or not it or int(it[-1][0])>=iters or abs(float(it[-1][1]))>1e-4: return None
    return float(h[-1][1])

def clmax_phys(A,L,drop=0.05):
    """Peak CL before the first collapse. A naive max() picks up post-stall solutions
    XFOIL reports but does not physically resolve."""
    peak=-9e9; best=None
    for a,cl in zip(A,L):
        if cl is None: continue
        if peak>0.2 and cl<peak*(1-drop): break
        if cl>peak: peak=cl; best=(float(a),float(cl))
    return best

def slope(A,L,lo=-2,hi=6):
    A=np.asarray(A,float); L=np.asarray(L,float)
    m=(A>=lo)&(A<=hi)&np.isfinite(L)
    return float(np.polyfit(A[m],L[m],1)[0]) if m.sum()>=3 else float("nan")

CASES={"S1223":("/root/aero/uiuc/S1223.LFT","/tmp/xf/s1223.dat"),
       "SD2030":("/root/aero/uiuc/sd2030_c_lft.txt","/tmp/xf/sd2030_239.dat")}
out={}
for name,(lft,dat) in CASES.items():
    print("="*98); print(name); print("="*98)
    print(f"{'Re':>8}{'n up':>6}{'exp CLmax':>11}{'@alpha':>8}{'XF CLmax':>10}{'@alpha':>8}"
          f"{'CLmax err':>11}{'stall angle':>13}{'slope exp':>11}{'slope XF':>10}{'err':>8}")
    out[name]={}
    for b in read_lft(lft):
        Re=int(b["Re"]); au,cu=b["up"]
        if len(au)<8: continue
        eb=clmax_phys(au,cu)
        se=slope(au,cu)
        XA=list(np.arange(-4,24.1,1.0)); XL=[run(dat,float(a),Re) for a in XA]
        pa=[a for a,c in zip(XA,XL) if c is not None]; pc=[c for c in XL if c is not None]
        if not pa or not eb: print(f"{Re:>8}   incomplete"); continue
        xb=clmax_phys(pa,pc); sx=slope(pa,pc)
        out[name][Re]=dict(exp=eb,xf=xb,slope_exp=se,slope_xf=sx,n_up=len(au))
        print(f"{Re:>8}{len(au):>6}{eb[1]:>11.3f}{eb[0]:>8.2f}{xb[1]:>10.3f}{xb[0]:>8.2f}"
              f"{100*(xb[1]-eb[1])/eb[1]:>+10.1f}%{xb[0]-eb[0]:>+12.2f}°"
              f"{se:>11.4f}{sx:>10.4f}{100*(sx-se)/se:>+7.1f}%")
json.dump(out,open("/root/aero/lift_val.json","w"),indent=1)
