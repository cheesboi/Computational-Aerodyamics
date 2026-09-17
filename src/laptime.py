"""What do the measured XFOIL errors cost in seconds?

The validation says XFOIL's drag can be wrong by a known amount and its CLmax is
over-predicted by a known amount.  A designer who believes XFOIL therefore builds a
car whose true aero differs from the assumed aero.  This propagates those errors
through the quasi-steady lap simulator and reports the consequence in lap time and
endurance energy, which is the unit a team actually cares about.
"""
import sys
sys.path.insert(0,"/root/aero")
from s5 import simulate

CLA, CDA, M = 3.5, 1.3, 320.0
base = simulate(CLA=CLA, CDA=CDA, m=M)
laps = 22000/base["total"]

print(f"Reference aero car:  CL.A {CLA}, CD.A {CDA}, {M:.0f} kg")
print(f"  lap {base['T']:.3f} s   vmax {base['vmax']:.1f} m/s   {base['E_kWh']:.4f} kWh/lap")
print(f"  22 km endurance = {laps:.1f} laps\n")

print("EFFECT OF A DRAG ERROR  (designer assumed CD.A; truth is higher/lower)")
print(f"{'drag error':>12}{'true CD.A':>11}{'lap (s)':>10}{'delta lap':>11}"
      f"{'endurance delta':>18}{'energy':>10}")
for e in (-20,-12.5,-5,0,5,12.5,20,25):
    r = simulate(CLA=CLA, CDA=CDA*(1+e/100), m=M)
    d = r["T"]-base["T"]
    print(f"{e:>+11.1f}%{CDA*(1+e/100):>11.3f}{r['T']:>10.3f}{d:>+11.3f}"
          f"{d*laps:>+17.2f}s{100*(r['E_kWh']-base['E_kWh'])/base['E_kWh']:>+9.1f}%")

print("\nEFFECT OF A DOWNFORCE ERROR  (XFOIL over-predicts CLmax by 3.6 to 13.3%)")
print(f"{'CL error':>12}{'true CL.A':>11}{'lap (s)':>10}{'delta lap':>11}{'endurance delta':>18}")
for e in (0,-3.6,-8.7,-9.5,-12.1,-13.3):
    r = simulate(CLA=CLA*(1+e/100), CDA=CDA, m=M)
    d = r["T"]-base["T"]
    print(f"{e:>+11.1f}%{CLA*(1+e/100):>11.3f}{r['T']:>10.3f}{d:>+11.3f}{d*laps:>+17.2f}s")

print("\nBOTH AT ONCE -- the realistic case at FSAE Reynolds number")
print("  XFOIL under-predicts tripped drag by ~5% and over-predicts CLmax by ~9%")
r = simulate(CLA=CLA*0.91, CDA=CDA*1.05, m=M)
d = r["T"]-base["T"]
print(f"  lap {r['T']:.3f} s  ({d:+.3f} s/lap)   endurance {d*laps:+.2f} s over {laps:.0f} laps")
print("\n  and the same at the low-Reynolds-number error magnitudes (Re = 100,000):")
r2 = simulate(CLA=CLA*0.91, CDA=CDA*1.23, m=M)
d2 = r2["T"]-base["T"]
print(f"  lap {r2['T']:.3f} s  ({d2:+.3f} s/lap)   endurance {d2*laps:+.2f} s over {laps:.0f} laps")
