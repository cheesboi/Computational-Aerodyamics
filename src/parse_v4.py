import numpy as np

def read_v4(path):
    lines = open(path).read().splitlines()
    meta = {}
    for ln in lines[:4]:
        if ":" in ln:
            k, v = ln.split(":", 1); meta[k.strip()] = v.strip()
    blocks, i = [], 0
    while i < len(lines):
        if lines[i].strip().startswith("Average Reynolds"):
            Re = float(lines[i+1]); n = int(lines[i+3])
            rows = []
            for j in range(i+5, i+5+n):
                p = [float(x) for x in lines[j].split()]
                rows.append(dict(alpha=p[0], cl=p[1], cd=p[2], span=np.array(p[3:])))
            blocks.append(dict(Re=Re, rows=rows, **meta))
            i += 5+n
        else: i += 1
    return blocks

if __name__ == "__main__":
    for f in ("e387_c_drg","e387_tf_drg","fx63137_c_drg","fx63137_tf_drg"):
        bs = read_v4(f"uiuc/{f}.txt")
        print(f"{f:<18} {len(bs)} Re blocks: {[int(b['Re']) for b in bs]}   "
              f"{len(bs[0]['rows'][0]['span'])} spanwise cols")
