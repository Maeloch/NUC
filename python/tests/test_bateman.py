"""Tests de nuc.bateman : fidélité au port scalaire de référence (bateman.m),
vectorisation temps/tirages, garde-fou lambdas quasi dégénérés."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from nuc.bateman import bateman


def _bateman_reference(lambdas, ratios, natoms_0, time):
    """Port scalaire fidèle de bateman.m — pour validation uniquement."""
    n = len(lambdas)
    natoms_t = list(natoms_0)
    if time <= 0:
        return natoms_t
    for i in range(n):
        M = 0.0
        for m in range(i):
            Q = 1.0
            for q in range(m, i):
                Q *= ratios[q] * lambdas[q]
            K = 0.0
            for k in range(m, i + 1):
                J = 1.0
                for j in range(m, i + 1):
                    if j != k:
                        J *= (lambdas[j] - lambdas[k])
                K += math.exp(-lambdas[k] * time) / J
            M += natoms_0[m] * Q * K
        natoms_t[i] = natoms_0[i] * math.exp(-lambdas[i] * time) + M
    return natoms_t


LAMBDAS = [0.8, 0.5, 0.3, 0.2, 0.1]
RATIOS = [0.7, 1.0, 0.9, 0.5, 1.0]
N0 = [1000.0, 50.0, 0.0, 0.0, 0.0]


def test_matches_reference_multiple_times():
    for t in (0.01, 0.5, 2.0, 10.0):
        ref = _bateman_reference(LAMBDAS, RATIOS, N0, t)
        vec = bateman(np.array(LAMBDAS), np.array(RATIOS), np.array(N0), t)
        assert max(abs(r - v) / max(abs(r), 1e-30) for r, v in zip(ref, vec)) < 1e-9


def test_time_vectorization_matches_per_time_calls():
    ts = np.array([0.01, 0.5, 2.0, 10.0])
    vec_t = bateman(np.array(LAMBDAS), np.array(RATIOS), np.array(N0), ts)
    assert vec_t.shape == (4, 5)
    for i, tt in enumerate(ts):
        ref = _bateman_reference(LAMBDAS, RATIOS, N0, float(tt))
        assert max(abs(r - v) / max(abs(r), 1e-30) for r, v in zip(ref, vec_t[i])) < 1e-9


def test_sample_batch_vectorization_matches_per_sample_calls():
    S = 5
    lambdas_mc = np.tile(LAMBDAS, (S, 1))
    ratios_mc = np.tile(RATIOS, (S, 1))
    N0_mc = np.tile(N0, (S, 1))
    vec = bateman(lambdas_mc, ratios_mc, N0_mc, 2.0)
    assert vec.shape == (S, 5)
    ref = _bateman_reference(LAMBDAS, RATIOS, N0, 2.0)
    for s in range(S):
        assert max(abs(r - v) / max(abs(r), 1e-30) for r, v in zip(ref, vec[s])) < 1e-9


def test_degenerate_lambdas_stay_finite():
    # lambdas[0] et lambdas[2] quasi identiques : bateman_reference() plante
    # (division par ~0) ; la version vectorisee doit rester finie grace au
    # garde-fou epsilon.
    lambdas = np.array([0.5, 0.2, 0.5000000001, 0.9])
    ratios = np.array([0.6, 1.0, 0.3, 1.0])
    n0 = np.array([1000.0, 0.0, 0.0, 0.0])
    result = bateman(lambdas, ratios, n0, 2.0)
    assert np.all(np.isfinite(result))


def test_exactly_degenerate_lambdas_also_stay_finite():
    lambdas = np.array([0.5, 0.2, 0.5, 0.9])  # egalite exacte, pas juste proche
    ratios = np.array([0.6, 1.0, 0.3, 1.0])
    n0 = np.array([1000.0, 0.0, 0.0, 0.0])
    result = bateman(lambdas, ratios, n0, 2.0)
    assert np.all(np.isfinite(result))


def test_mass_conservation_no_branching_loss():
    # Chaine simple sans perte (tous les ratios a 1) : la somme des atomes
    # (peres + fils a tout instant) doit rester egale a N0 initial, tant
    # que le dernier nucleide de la chaine est stable... mais ici le
    # dernier decroit aussi -> on verifie plutot la conservation partielle
    # sur une chaine tronquee a 2 maillons stables au bout.
    lambdas = np.array([0.3, 0.1, 1e-12])  # le dernier quasi stable
    ratios = np.array([1.0, 1.0, 1.0])
    n0 = np.array([1000.0, 0.0, 0.0])
    result = bateman(lambdas, ratios, n0, 50.0)  # temps long -> tout descend en bout de chaine
    assert abs(result.sum() - 1000.0) < 1.0  # conservation a 0.1% pres


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    ok, fail = 0, 0
    for t in tests:
        try:
            t(); ok += 1; print(f"PASS {t.__name__}")
        except Exception as e:
            fail += 1; print(f"FAIL {t.__name__}: {e!r}")
    print(f"\n{ok} réussis, {fail} échoués")
