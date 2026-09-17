"""A thin, paranoid wrapper around XFOIL.

Three design decisions here are not obvious, and each one exists because getting
it wrong produced a wrong published number at some point in this study:

1.  Graphics off.  `PLOP / G F` must be the first thing sent.  Without it XFOIL
    tries to open a plot window and aborts on any machine without a display.

2.  One angle of attack per subprocess.  XFOIL run as a continuous sweep carries
    boundary-layer state from point to point, so a single bad solve silently
    corrupts every point after it.  One process per point costs speed and buys
    independence.

3.  Convergence screening (`strict=True`).  XFOIL prints a lift and a drag
    whether or not it converged.  A solve that exhausts its iteration limit with
    a large residual still reports numbers, and nothing in those numbers marks
    them as invalid.  See tests/test_screening.py for a real case that returned
    a drag four times the measured value this way.

There is a fourth check that does not live in this file because it needs more
than one solve: forced-transition drag must be independent of Ncrit, since XTR
bypasses the amplification model entirely.  A point that violates that invariant
has converged to the wrong branch -- converged, low residual, and wrong.  No
residual test can catch it.  `tripped_drag_is_ncrit_invariant` below applies it.
"""

import os
import re
import subprocess

_RMS = re.compile(r"^\s*(\d+)\s+rms:\s*([-\d.E+]+)", re.M)
_RES = re.compile(r"a =\s*([-\d.]+)\s+CL =\s*([-\d.]+).*?CD =\s*([\d.]+)", re.S)
_SID = re.compile(r"Side\s+(\d)\s+(free|forced)\s+transition at x/c =\s*([\d.]+)")

RMS_TOL = 1e-4


def xfoil(dat, alpha, Re, ncrit=9, xtr=None, iters=300, timeout=30, strict=True):
    """Run one XFOIL point.

    Parameters
    ----------
    dat : str
        Path to an airfoil coordinate file (Selig format).
    alpha : float
        Angle of attack, degrees.
    Re : float
        Reynolds number based on chord.
    ncrit : float
        Amplification factor for the e^N transition model. XFOIL's default is 9,
        which corresponds to an "average" wind tunnel. It is a free parameter,
        not a measurement -- see the study's section 5.4.
    xtr : tuple(float, float) or None
        (upper, lower) x/c at which to FORCE transition. None lets XFOIL decide
        via e^N. Note that XFOIL takes the earlier of natural and forced, so
        xtr=(0.02, 1.0) trips the upper surface and leaves the lower one free.
    iters : int
        Iteration limit passed to XFOIL.
    timeout : float
        Wall-clock seconds before the subprocess is killed.
    strict : bool
        Reject solutions XFOIL did not converge. Turn this off only to
        demonstrate what it protects against.

    Returns
    -------
    dict with keys CL, CD, xtr_top, xtr_bot -- or None if the point was
    rejected, timed out, or produced no parseable result.
    """
    # XFOIL's filename buffer is 48 characters. A longer path makes LOAD fail
    # with "*** LOAD NOT COMPLETED ***" and no other complaint, so the point
    # just vanishes. Run in the file's own directory and load by basename,
    # which keeps the string short however deep the directory is. This also
    # keeps XFOIL's stray .bl scratch files out of the working directory.
    workdir = os.path.dirname(os.path.abspath(dat)) or "."
    fname = os.path.basename(dat)
    if len(fname) > 48:
        raise ValueError(f"coordinate filename too long for XFOIL (48 char max): {fname}")

    vpar = f"N {ncrit}\n" + (f"XTR {xtr[0]} {xtr[1]}\n" if xtr else "")
    cmds = (
        f"PLOP\nG F\n\n"
        f"LOAD {fname}\nAF\nOPER\nVPAR\n{vpar}\n"
        f"VISC {Re}\nITER {iters}\nALFA {alpha}\n\nQUIT\n"
    )
    try:
        out = subprocess.run(
            ["xfoil"], input=cmds, capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        ).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    if "LOAD NOT COMPLETED" in out:
        raise RuntimeError(f"XFOIL could not read {dat}")

    res, its, sid = _RES.findall(out), _RMS.findall(out), _SID.findall(out)
    if not res or not its or not sid:
        return None

    if strict:
        n, rms = int(its[-1][0]), float(its[-1][1])
        if n >= iters or abs(rms) > RMS_TOL:
            return None  # never converged: the answer depends on `iters`
        if "Convergence failed" in out.split(f"rms: {its[-1][1]}")[-1]:
            return None

    top = [s for s in sid if s[0] == "1"][-1]
    bot = [s for s in sid if s[0] == "2"][-1]
    return dict(
        CL=float(res[-1][1]),
        CD=float(res[-1][2]),
        xtr_top=float(top[2]),
        xtr_bot=float(bot[2]),
    )


def tripped_drag_is_ncrit_invariant(dat, alpha, Re, ncrits=(7, 9, 11, 13),
                                    xtr=(0.02, 0.05), tol=0.10):
    """The physics screen: forced-transition drag must not depend on Ncrit.

    Returns (ok, spread, values). `spread` is the fractional range of the drag
    values across `ncrits`. A point that fails this has converged to a different
    solution branch at some Ncrit, which a residual test cannot detect.

    tol=0.10 separates ordinary numerical scatter (0-3% in practice) from a
    branch switch (62% in the one case found in this study). A tighter 0.5%
    tolerance was tried first and rejected sound points.
    """
    vals = []
    for n in ncrits:
        r = xfoil(dat, alpha, Re, ncrit=n, xtr=xtr)
        if r is None:
            return False, float("nan"), vals
        vals.append(r["CD"])
    mean = sum(vals) / len(vals)
    spread = (max(vals) - min(vals)) / mean
    return spread <= tol, spread, vals


def make_dat(name, path, n_points_per_side=120):
    """Write a repanelled coordinate file from the AeroSandbox database.

    Panel count is not cosmetic. The stock 97-panel FX 63-137 gives a Re=100,000
    drag error of +16.9% against the wind tunnel; the same airfoil at 239 panels
    gives -9.5%. Same airfoil, same conditions, opposite conclusion.
    """
    import aerosandbox as asb

    af = asb.Airfoil(name).repanel(n_points_per_side=n_points_per_side)
    with open(path, "w") as f:
        f.write(name.upper() + "\n")
        for x, y in af.coordinates:
            f.write(f"{x:.6f} {y:.6f}\n")
    return path
