import numpy as np, re

def read_lft(path):
    """Parse a UIUC .LFT file -> list of dicts, one per Reynolds number."""
    lines = open(path).read().splitlines()
    meta = {}
    for ln in lines[:4]:
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip()
    blocks, i = [], 0
    while i < len(lines):
        if lines[i].strip().startswith("Average Reynolds"):
            Re = float(lines[i+1])
            n  = int(lines[i+3])
            rows = []
            for j in range(i+5, i+5+n):
                p = lines[j].split()
                rows.append((float(p[0]), float(p[1]), float(p[2])))
            a = np.array([r[0] for r in rows])
            cl = np.array([r[1] for r in rows])
            # split the sweep where alpha stops increasing
            turn = int(np.argmax(a))
            blocks.append(dict(Re=Re, n=n, alpha=a, cl=cl, turn=turn,
                               up=(a[:turn+1], cl[:turn+1]),
                               down=(a[turn+1:], cl[turn+1:]), **meta))
            i += 5 + n
        else:
            i += 1
    return blocks

if __name__ == "__main__":
    for f in ("uiuc/S1223.LFT", "uiuc/S1223GF4.LFT", "uiuc/S1223RTL.LFT"):
        print("="*70)
        for b in read_lft(f):
            au, cu = b["up"]
            print(f'{f.split("/")[-1]:<14} Re={b["Re"]:>8.0f}  "{b["Comment"]}"  builder={b["Builder"]}')
            print(f'   points {b["n"]:>3}  (up {len(au)}, down {len(b["down"][0])})')
            k = int(np.argmax(cu))
            print(f'   UPSTROKE   CLmax = {cu[k]:.3f} at alpha {au[k]:.2f}')
            ad, cd = b["down"]
            if len(cd):
                kk = int(np.argmax(cd))
                print(f'   DOWNSTROKE CLmax = {cd[kk]:.3f} at alpha {ad[kk]:.2f}')
