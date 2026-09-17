# Data

**The wind tunnel measurements are not in this repository.**

They are the work of Selig et al., published in *Summary of Low-Speed Airfoil Data*
(SoarTech Publications) and NREL/SR-500-34515. They are publicly posted, which is not
the same as being licensed for redistribution, so this repository links to the source
rather than copying it.

Download them from the [UIUC Airfoil Data Site](https://m-selig.ae.illinois.edu/ads.html)
and place them in this folder.

## Files this study uses

From **Volume 4** (the six NREL airfoils):

| file | what it is |
|---|---|
| `e387_c_drg.txt` | E387, clean, drag |
| `e387_tf_drg.txt` | E387, zigzag trip type F, drag |
| `fx63137_c_drg.txt` | FX 63-137, clean, drag |
| `fx63137_tf_drg.txt` | FX 63-137, tripped, drag |
| `sd2030_c_drg.txt` | SD2030, clean, drag |
| `sd2030_tf_drg.txt` | SD2030, tripped, drag |
| `sd2030_c_lft.txt` | SD2030, clean, lift — for the CL,max comparison |

From **Volume 2**:

| file | what it is |
|---|---|
| `S1223.LFT` | S1223 lift — the high-lift airfoil FSAE teams actually use |

## Format notes, learned the hard way

- `.DRG` files have a **variable number of spanwise columns** between blocks. A fixed-width
  parser will silently mis-read some of them. `src/parse_v4.py` handles this.
- `.LFT` files contain an **up-sweep and a down-sweep** in one block, concatenated. The
  turning point is where alpha stops increasing. Using the whole block as one polar mixes
  hysteresis branches and produces a meaningless CL,max.
- Some blocks have **21 or 33 points** rather than a full 61-point sweep. These went through
  a different reduction: their Cm range is ~0.004 where full sweeps of the same airfoil show
  0.05 to 0.2. Pitching moment from those blocks is not usable, and they are excluded.
- `sh3055_tf_drg.txt`, the block labelled Re = 181,773, has **two rows byte-identical** to
  rows in its own Re = 100,002 block, and an unexplained alpha gap. It is excluded.

## Airfoils that could not be used

- **SH3055** — has clean and tripped drag, but its coordinates are not in the AeroSandbox
  database and are printed only in an appendix of the NREL report. No coordinates, no XFOIL
  side to compare against.
- **S834** — tripped drag only; no clean pair.
- **S822** — no Volume 4 files obtained. The Volume 1 files are a different test campaign
  and are not comparable.
