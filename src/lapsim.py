import numpy as np
rho, g, mu0, n_ = 1.225, 9.81, 1.4, 0.15
P = 80e3
TRACK=[('straight',75.,None),('corner',23.6,15.),('straight',40.,None),('corner',31.4,10.),
 ('straight',60.,None),('corner',39.3,25.),('straight',50.,None),('corner',25.1,8.),
 ('straight',90.,None),('corner',47.1,30.),('straight',40.,None),('corner',37.7,12.)]

def build(ds=0.5):
    S,R=[],[]; pos=0.
    for k,L,r in TRACK:
        ns=max(int(round(L/ds)),1)
        for i in range(ns): S.append(pos); R.append(r); pos+=L/ns
    return np.array(S),R,pos

def simulate(CLA=3.5, CDA=1.3, m=300.0, ds_target=0.5):
    S,R,total = build(ds_target); ds = total/len(S); W = m*g
    DF = lambda v: 0.5*rho*v*v*CLA
    DR = lambda v: 0.5*rho*v*v*CDA
    mu = lambda v: mu0*((W+DF(v))/W)**(-n_)
    f2 = lambda v,Rr: mu(v)*(W+DF(v))/m - v*v/Rr
    def cs(Rr, v0=15., tol=1e-10, it=100):
        if Rr is None: return 1e4
        v=v0
        for _ in range(it):
            h=1e-6; d=(f2(v+h,Rr)-f2(v-h,Rr))/(2*h)
            if d==0: return None
            st=f2(v,Rr)/d; v-=st
            if abs(st)<tol: return v
        return None
    vl = np.array([cs(r) for r in R])
    at = lambda v: mu(v)*(W+DF(v))/m
    aa = lambda v: min(at(v), P/(m*max(v,.5))) - DR(v)/m
    ab = lambda v: at(v) + DR(v)/m
    start=int(np.argmin(vl)); order=np.roll(np.arange(len(S)),-start)
    v=vl.copy()
    for k in range(1,len(order)):
        i,j=order[k-1],order[k]; v[j]=min(v[j],(v[i]**2+2*aa(v[i])*ds)**.5)
    for k in range(len(order)-1,0,-1):
        j,i=order[k],order[k-1]; v[i]=min(v[i],(v[j]**2+2*ab(v[j])*ds)**.5)
    T = np.sum(ds/v)
    # tractive energy (no regen)
    a_act = np.zeros_like(v)
    for k in range(len(order)):
        i,j = order[k], order[(k+1)%len(order)]
        a_act[i] = (v[j]**2 - v[i]**2)/(2*ds)
    F_trac = np.maximum(0.0, m*a_act + DR(v))
    E = np.sum(F_trac*ds)
    return dict(T=T, v=v, S=S, total=total, vmax=v.max(), E_kWh=E/3.6e6, ds=ds)

if __name__ == "__main__":
    base = simulate(CLA=0.0, CDA=0.8, m=300.0)
    aero = simulate(CLA=3.5, CDA=1.3, m=320.0)
    aero_nomass = simulate(CLA=3.5, CDA=1.3, m=300.0)
    print(f"{'config':<28}{'lap (s)':>10}{'vmax':>9}{'E/lap (kWh)':>14}")
    for nm,r in [('no aero, 300 kg',base),('aero, 320 kg',aero),('aero, 300 kg (no mass pen.)',aero_nomass)]:
        print(f'{nm:<28}{r["T"]:>10.3f}{r["vmax"]:>9.2f}{r["E_kWh"]:>14.5f}')
    print()
    print(f'gain (honest, +20 kg): {base["T"]-aero["T"]:+.3f} s  ({100*(base["T"]-aero["T"])/base["T"]:.2f}%)')
    print(f'mass penalty alone   : {aero["T"]-aero_nomass["T"]:+.3f} s')
    print(f'energy penalty       : {100*(aero["E_kWh"]-base["E_kWh"])/base["E_kWh"]:+.1f}%')
    print()
    print('22 km endurance:')
    laps = 22000/base['total']
    print(f'  {laps:.1f} laps of this track')
    print(f'  no aero: {base["E_kWh"]*laps:.2f} kWh   aero: {aero["E_kWh"]*laps:.2f} kWh')
