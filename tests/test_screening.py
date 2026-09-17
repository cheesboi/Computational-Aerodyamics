"""Tests for the XFOIL screening logic.

These are physics tests, not smoke tests. Each one encodes a specific way this
study produced a wrong number before the screening existed, so a regression here
is a regression in a published result rather than in a convenience function.

They need XFOIL on PATH and aerosandbox installed. They do NOT need the UIUC
wind tunnel data, so anyone who clones the repository can run them:

    pip install -r requirements.txt
    apt-get install -y xfoil
    pytest -v
"""

import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from xfoil_driver import make_dat, tripped_drag_is_ncrit_invariant, xfoil  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("xfoil") is None, reason="XFOIL not installed"
)


@pytest.fixture(scope="session")
def airfoils(tmp_path_factory):
    d = tmp_path_factory.mktemp("airfoils")
    return {
        name: make_dat(name, str(d / f"{name}.dat"))
        for name in ("e387", "fx63137", "sd2030")
    }


# --------------------------------------------------------------------------
# the driver returns physically sensible numbers at all
# --------------------------------------------------------------------------

def test_converged_point_is_sane(airfoils):
    r = xfoil(airfoils["e387"], 4.0, 200_000)
    assert r is not None
    assert 0.5 < r["CL"] < 1.2, r["CL"]
    assert 0.008 < r["CD"] < 0.020, r["CD"]
    assert 0.0 < r["xtr_top"] <= 1.0


def test_forced_transition_lands_where_asked(airfoils):
    """XTR should put transition exactly at the requested station."""
    r = xfoil(airfoils["e387"], 4.0, 200_000, xtr=(0.02, 0.05))
    assert r is not None
    assert r["xtr_top"] == pytest.approx(0.02, abs=1e-3)
    assert r["xtr_bot"] == pytest.approx(0.05, abs=1e-3)


def test_xtr_upper_only_leaves_lower_free(airfoils):
    """xtr=(0.02, 1.0) must trip the upper surface and NOT force the lower one.

    XFOIL takes the earlier of natural and forced transition, and 1.0 is the
    default, so this is 'upper only'. Getting this backwards would have made the
    surface decomposition in the study meaningless.
    """
    free = xfoil(airfoils["fx63137"], 4.0, 200_000)
    upper_only = xfoil(airfoils["fx63137"], 4.0, 200_000, xtr=(0.02, 1.00))
    assert free is not None and upper_only is not None
    assert upper_only["xtr_top"] == pytest.approx(0.02, abs=1e-3)
    # lower surface should be unchanged from the free-transition solution
    assert upper_only["xtr_bot"] == pytest.approx(free["xtr_bot"], abs=0.05)


# --------------------------------------------------------------------------
# screen one: the residual test
# --------------------------------------------------------------------------

def test_rejects_known_nonconverged_point(airfoils):
    """FX 63-137, Re = 100,000, alpha = 8 deg does not converge.

    It exhausts 300 iterations with rms ~0.23 and reports Cd ~0.119 against a
    measured 0.032 -- nearly four times the experiment. Including it flipped the
    sign of a headline result in an earlier revision of this study.
    """
    assert xfoil(airfoils["fx63137"], 8.0, 100_000, strict=True) is None


def test_the_rejected_point_is_actually_garbage(airfoils):
    """Show what the screen is protecting against, rather than asserting a rule.

    With strict=False the same point returns a drag far outside anything
    physical for this airfoil at this Reynolds number.
    """
    loose = xfoil(airfoils["fx63137"], 8.0, 100_000, strict=False)
    assert loose is not None, "expected XFOIL to report SOMETHING here"
    neighbour = xfoil(airfoils["fx63137"], 4.0, 100_000, strict=True)
    assert neighbour is not None
    assert loose["CD"] > 3 * neighbour["CD"], (loose["CD"], neighbour["CD"])


def test_iteration_limit_changes_the_unscreened_answer(airfoils):
    """The signature of a non-result: its value depends on how long you ran.

    A converged solution is insensitive to the iteration cap. This one is not,
    which is the whole argument for the screen.
    """
    a = xfoil(airfoils["fx63137"], 8.0, 100_000, iters=200, strict=False)
    b = xfoil(airfoils["fx63137"], 8.0, 100_000, iters=400, strict=False)
    assert a is not None and b is not None
    assert abs(a["CD"] - b["CD"]) / b["CD"] > 0.02


# --------------------------------------------------------------------------
# screen two: the physics invariant
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name,Re", [("e387", 100_000), ("sd2030", 100_000)])
def test_tripped_drag_does_not_depend_on_ncrit(airfoils, name, Re):
    """XTR bypasses the e^N model, so forced-transition drag is Ncrit-invariant.

    This is the control that licenses the whole Ncrit sensitivity study: if the
    tripped side moved, the sweep would be measuring the setup, not the model.
    In practice these agree to five significant figures.
    """
    ok, spread, vals = tripped_drag_is_ncrit_invariant(airfoils[name], 4.0, Re)
    assert ok, f"tripped drag moved {100*spread:.1f}% across Ncrit: {vals}"
    assert spread < 0.01, f"expected near-exact invariance, got {100*spread:.2f}%"


def test_free_transition_drag_DOES_depend_on_ncrit(airfoils):
    """The other half of the control: the clean side must move, or the sweep
    would have nothing to measure. E387 clean drag rises ~77% from Ncrit 7 to 13.
    """
    lo = xfoil(airfoils["e387"], 4.0, 100_000, ncrit=7)
    hi = xfoil(airfoils["e387"], 4.0, 100_000, ncrit=13)
    assert lo is not None and hi is not None
    assert hi["CD"] > 1.2 * lo["CD"], (lo["CD"], hi["CD"])


# --------------------------------------------------------------------------
# panel convergence
# --------------------------------------------------------------------------

def test_panel_converged_at_120_per_side(tmp_path):
    """239 panels is converged; the study's results all use it.

    A coarse airfoil does not announce itself -- it returns a converged,
    plausible, wrong number. This asserts the chosen resolution is on the flat
    part of the curve.
    """
    coarse = make_dat("sd2030", str(tmp_path / "c.dat"), n_points_per_side=90)
    fine = make_dat("sd2030", str(tmp_path / "f.dat"), n_points_per_side=160)
    rc = xfoil(coarse, 4.0, 100_000)
    rf = xfoil(fine, 4.0, 100_000)
    assert rc is not None and rf is not None
    assert abs(rc["CD"] - rf["CD"]) / rf["CD"] < 0.02


# --------------------------------------------------------------------------
# regression: XFOIL's 48-character filename limit
# --------------------------------------------------------------------------

def test_long_path_still_loads(tmp_path):
    """XFOIL's filename buffer is 48 characters.

    A longer path makes LOAD fail with '*** LOAD NOT COMPLETED ***' and nothing
    else -- the point simply disappears, which looks identical to a convergence
    rejection. The driver works around it by running in the file's directory and
    loading by basename. This caught a real failure on a deep pytest tmp_path,
    and would hit anyone who clones into a nested folder.
    """
    deep = tmp_path / ("nested/" * 6)
    deep.mkdir(parents=True)
    dat = make_dat("e387", str(deep / "a.dat"))
    assert len(str(dat)) > 48, "this test needs a path longer than XFOIL's buffer"
    r = xfoil(dat, 4.0, 200_000)
    assert r is not None and 0.5 < r["CL"] < 1.2
