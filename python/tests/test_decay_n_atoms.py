"""Tests de decay_n_atoms.py : cohérence avec les valeurs déjà validées
(rn222_demo.py, elle-même comparée à <0.005% contre l'outil LNHB) et
vectorisation multi-instants."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nuc.lara_client import LaraClient, FetchResult
from nuc.decay_n_atoms import decay_n_atoms_activities

_SAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "samples", "lara_real")


def _read(name):
    with open(os.path.join(_SAMPLES, name), encoding="utf-8") as f:
        return f.read()


_LAMBDA_PB210 = math.log(2) / (22.23 * 365.25 * 86400)

DATA = {
    "Rn-222": "Nuclide ; Rn-222\nDaughter(s) ; alpha ; Po-218 ; 100\nDecay constant (1/s) ; 2.0983E-6 ; 0.0006E-6\n",
    "Po-218": _read("Po-218.lara.txt"),
    "At-218": "Nuclide ; At-218\nDaughter(s) ; alpha ; Bi-214 ; 99.9 ; B- ; Rn-218 ; 0.1\nDecay constant (1/s) ; 4.951E-1 ; 0.35E-1\n",
    "Pb-214": _read("Pb-214.lara.txt"),
    "Rn-218": "Nuclide ; Rn-218\nDaughter(s) ; alpha ; Po-214 ; 100\nDecay constant (1/s) ; 19.25 ; 1.6\n",
    "Bi-214": _read("Bi-214.lara.txt"),
    "Po-214": _read("Po-214.lara.txt"),
    "Tl-210": "Nuclide ; Tl-210\nDaughter(s) ; B- ; Pb-210 ; 100\nDecay constant (1/s) ; 8.887E-3 ; 0.068E-3\n",
    "Pb-210": f"Nuclide ; Pb-210\nDecay constant (1/s) ; {_LAMBDA_PB210:.6e} ; 0\n",
}

_REF_BQ = {  # rn222_demo.py / reference LNHB (docs/RECONCILIATION.md §11)
    "Rn-222": 992.47458, "Po-218": 993.02714, "Pb-214": 755.80473,
    "Bi-214": 491.05022, "Po-214": 490.94728,
}


def _client():
    def fetch(url, timeout):
        for k, v in DATA.items():
            if k in url:
                return FetchResult(200, v)
        return FetchResult(404, "")
    return LaraClient(fetch, read_local_cache_fn=lambda n: "")


def test_matches_rn222_demo_single_time():
    client = _client()
    lam_rn = client.decay_constant("Rn-222")[0]
    N0 = 1000.0 / lam_rn
    act = decay_n_atoms_activities(client, "Rn-222", N0, 3600.0)
    for name, ref in _REF_BQ.items():
        assert abs(act[name] - ref) < 1e-3, (name, act[name], ref)


def test_multi_time_matches_single_time_calls():
    client = _client()
    lam_rn = client.decay_constant("Rn-222")[0]
    N0 = 1000.0 / lam_rn
    times = [900.0, 1800.0, 3600.0]
    multi = decay_n_atoms_activities(client, "Rn-222", N0, times)
    for i, t in enumerate(times):
        single = decay_n_atoms_activities(client, "Rn-222", N0, t)
        for name in ("Pb-214", "Bi-214"):
            assert abs(multi[name][i] - single[name]) < 1e-6


def test_activity_builds_up_monotonically_for_daughter():
    client = _client()
    lam_rn = client.decay_constant("Rn-222")[0]
    N0 = 1000.0 / lam_rn
    times = [0, 900, 1800, 2700, 3600]
    act = decay_n_atoms_activities(client, "Rn-222", N0, times)
    pb214 = list(act["Pb-214"])
    assert pb214 == sorted(pb214)  # strictement croissant tant que loin de l'equilibre
    assert pb214[0] < 1e-9  # ~0 a t=0 (residu flottant negligeable, cf. exp(-lambda*0) dans bateman)


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    ok, fail = 0, 0
    for t in tests:
        try:
            t(); ok += 1; print(f"PASS {t.__name__}")
        except Exception as e:
            fail += 1; print(f"FAIL {t.__name__}: {e!r}")
    print(f"\n{ok} réussis, {fail} échoués")
