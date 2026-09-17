[README_1.md](https://github.com/user-attachments/files/32314449/README_1.md)
# xfoil-lowre-validation

**Validating XFOIL against UIUC wind tunnel data at the Reynolds numbers a Formula SAE wing actually runs at.**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR-USERNAME/xfoil-lowre-validation/blob/main/notebooks/ncrit_and_transition.ipynb)

<!-- replace YOUR-USERNAME above before pushing -->

---

## What this is

XFOIL is the tool nearly every Formula SAE team uses to pick an airfoil. Its published validations sit at Reynolds numbers five to twenty times higher than an FSAE wing ever sees. This repository asks where it stops being trustworthy, and answers with wind tunnel data rather than opinion.

The comparison is against Selig & McGranahan's UIUC low-speed measurements of three airfoils — E387, FX 63-137 and SD2030 — from Re = 100,000 to 500,000, each tested clean and with a zigzag boundary-layer trip at the leading edge. Comparing the *same* airfoil in the *same* tunnel with and without a trip isolates one question — what does forcing transition do to drag — and cancels most systematic error on both sides.

An FSAE element of 250 mm chord at 15 m/s runs at Re ≈ 250,000. That is the number this repository is about.

## Results

**With transition forced, XFOIL has no free parameter.** It predicts drag to within ~2% at Re = 350,000 and is off by 5–23% at Re = 100,000. This is the only comparison here that nobody can tune, and it is the one to design against.

**With transition free, the low-Reynolds-number answer belongs to `Ncrit`, not to the airfoil.** Sweeping Ncrit from 7 to 13 — a range the tunnel's own stated turbulence intensity of "less than 0.1%" permits entirely — moves the predicted effect of tripping by 23 to 67 percentage points at Re = 100,000 and reverses its sign on all three airfoils. Every airfoil crosses the measured value somewhere inside that range. The spread collapses to 3–6 points by Re = 500,000.

**Ncrit is not measuring the tunnel.** Fitting the Ncrit that reproduces measured clean drag gives 7.4 ± 0.7 everywhere for the SD2030, a monotonic slide from 12.7 to 5.6 for the FX 63-137, and nothing at all for the E387 above Re = 300,000. Three airfoils in one tunnel cannot disagree about that tunnel's turbulence level. It is a fitting parameter.

**The predicted trip penalty is manufactured on the lower surface.** XFOIL at Ncrit = 9 predicts laminar flow to the trailing edge there, so the trip buys nothing and pays full turbulent skin friction. Tripping the *upper* surface moves transition forward by more than half a chord and changes drag by under 1%, because bubble elimination and added friction cancel. Raise Ncrit and the bubble grows until the upper trip becomes a large net saving — which is what the tunnel measures.

**Lift is predicted worse than drag, in the dangerous direction.** XFOIL over-predicts CL,max by 3.6–13.3% on every airfoil at every Reynolds number tested, and stalls the S1223 four degrees early (13° against a measured 17°).

**And lift matters more.** Propagating the measured errors through a quasi-steady lap simulator: a 20% drag error costs 2.2 s over a 22 km endurance; a 20% lift error costs 12.6 s. The ratio is 5.6, because an autocross car is cornering-limited nearly everywhere. Most of this study is about drag, which is the less important quantity — it was chosen because it is the better-measured one.

## Running it

XFOIL is a Debian package, so there is no compiling:

```bash
apt-get install -y xfoil
pip install aerosandbox numpy matplotlib
```

The notebook runs end to end in about 75 seconds on a free Colab instance, roughly 280 XFOIL solves. Open it with the badge above.

## Three things the code does that are easy to get wrong

**Convergence screening.** XFOIL prints a lift and a drag whether or not it converged. Harvesting the last printed value — the obvious way to script it — silently collects solutions that burned through the iteration limit with a large residual. One such point returned Cd = 0.119 against a measured 0.032 and, on its own, reversed the sign of a headline result. `strict=True` rejects any solve that hits the iteration cap or leaves rms above 1e-4.

**An invariant check, because the residual test is not sufficient.** Forcing transition with `XTR` bypasses the amplification model, so tripped drag *must* be independent of Ncrit. One point converged cleanly to a tripped drag half the size of the same quantity at every other Ncrit. No tolerance can catch that; only the invariant can.

**Panel count.** Database coordinates are often too coarse. The stock 97-panel FX 63-137 gives a Re = 100,000 drag error of **+16.9%**; the same airfoil at 239 panels gives **−9.5%**. Same airfoil, same conditions, opposite conclusion. Everything here repanels to 120 points per surface, and panel convergence is verified per airfoil.

## Layout

```
notebooks/
  ncrit_and_transition.ipynb   Ncrit sensitivity + transition decomposition, Colab-ready
src/
  parse_v4.py                  UIUC .DRG reader (variable spanwise column count)
  parse_lft.py                 UIUC .LFT reader, splits up/down alpha sweeps
  xfoil_driver.py              one point per subprocess, both screening stages
  rung4_raw.py                 full sweep, dumps raw JSON
  tables.py                    window sensitivity, overlap test
  ncrit_final.py               Ncrit sweep at every Reynolds number
  ncrit_calib.py               Ncrit fitted to measured clean drag
  lift_val.py                  CL,max and lift-slope comparison
  laptime.py                   error magnitudes through the lap simulator
  lapsim.py                    quasi-steady lap simulator
data/                          NOT included — see below
docs/
  methods_and_results.pdf      the full write-up, 22 pages
```

Raw JSON of every accepted and rejected point is written alongside the results, so tables rebuild without re-running XFOIL and a different averaging window or acceptance rule can be applied to the same numbers.

## Data

**The wind tunnel data is not in this repository.** It belongs to Selig et al. and is published in *Summary of Low-Speed Airfoil Data* (SoarTech Publications) and NREL/SR-500-34515. Download the files yourself from the [UIUC Airfoil Data Site](https://m-selig.ae.illinois.edu/ads.html) and put them in `data/`. Redistributing someone else's dataset because it happens to be publicly posted is not the same as being allowed to, and the license is not mine to assume.

Files needed: `*_c_drg` and `*_tf_drg` (clean and tripped drag) for E387, FX 63-137 and SD2030; `*_c_lft` for SD2030; `S1223.LFT`.

## What this does not establish

- **One facility.** Every measurement is from the same tunnel, wake rake, model builder and reduction program. Volume 1 §2.5 compares the E387 across NASA Langley LTPT, Delft, Stuttgart and UIUC: three agree within a few percent at Re = 100,000 while the fourth is 30% off, and at Re = 200,000 the spread is ~25%. The low-Reynolds findings survive that comfortably. The few-percent agreements at high Reynolds number do not mean what they look like.
- **Geometry mismatch.** Selig records that the UIUC E387 model was "slightly decambered and warped at the trailing edge." XFOIL here runs nominal database coordinates. For that airfoil the two sides are different shapes.
- **Transition location is computed, never measured.** The claim that XFOIL's laminar lower surface is wrong is inference. Oil-flow visualisation would settle it; these files record only lift, drag and moment.
- **Ncrit is bounded, not located.** Finding the right value needs a measurement of the tunnel's turbulence intensity, not the upper bound the documentation gives.
- **The lap simulator is quasi-steady** — no weight transfer, no tyre thermal model, no driver. The lift-to-drag sensitivity ratio is far more trustworthy than the absolute seconds.

## References

- Selig, Guglielmo, Broeren & Giguère, *Summary of Low-Speed Airfoil Data, Volume 1*, SoarTech Publications, 1995. §2.1, §2.4, §2.5.
- Selig & McGranahan, *Wind Tunnel Aerodynamic Tests of Six Airfoils for Use on Small Wind Turbines*, NREL/SR-500-34515, 2004. Also AIAA 2004-1188.
- Drela, *XFOIL: An Analysis and Design System for Low Reynolds Number Airfoils*, Springer, 1989.
- Mack, *Transition and Laminar Instability*, NASA JPL 77-15, 1977. Source of the Ncrit–turbulence correlation.

---

Independent study, not affiliated with UIUC or with the authors of the data.
