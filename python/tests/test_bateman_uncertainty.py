"""Tests de nuc.bateman.bateman_with_uncertainty : validation contre un
tirage Monte-Carlo de référence, et démonstration du problème de la
propagation Value naïve (variable réutilisée) qui justifie cette approche
plutôt qu'un simple si_value/Value partout dans bateman()."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from nuc.bateman import bateman, bateman_with_uncertainty


def test_matches_monte_carlo_reference():
    lambdas = np.array([0.8, 0.5, 0.3])
    u_lambdas = np.array([0.05, 0.03, 0.02])
    ratios = np.array([1.0, 1.0, 1.0])
    u_ratios = np.zeros(3)
    N0 = np.array([1000.0, 0.0, 0.0])
    t = 2.0

    _, u_analytic = bateman_with_uncertainty(lambdas, u_lambdas, ratios, u_ratios, N0, t)

    rng = np.random.default_rng(0)
    S = 200_000
    lambdas_mc = lambdas + u_lambdas * rng.standard_normal((S, 3))
    out_mc = bateman(lambdas_mc, np.tile(ratios, (S, 1)), np.tile(N0, (S, 1)), t)
    u_mc = out_mc.std(axis=0)

    rel_err = np.abs(u_analytic - u_mc) / u_mc
    assert np.all(rel_err < 0.02), rel_err  # <2% : residu de linearisation attendu, pas un bug


def test_zero_uncertainty_inputs_give_zero_output_uncertainty():
    lambdas = np.array([0.8, 0.5, 0.3])
    ratios = np.array([1.0, 1.0, 1.0])
    N0 = np.array([1000.0, 0.0, 0.0])
    _, u = bateman_with_uncertainty(lambdas, np.zeros(3), ratios, np.zeros(3), N0, 2.0)
    assert np.allclose(u, 0.0)


def test_naive_value_propagation_would_be_wrong_illustration():
    """N'appelle pas bateman() -- illustre juste, avec la classe Value du
    depot SI, pourquoi une propagation naive (nœud par nœud) se trompe des
    qu'une variable incertaine est reutilisee plusieurs fois dans la meme
    expression : exactement la structure de bateman() (un meme lambda_k
    dans exp() ET dans plusieurs denominateurs (lambda_j - lambda_k))."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "SI", "python"))
    from si import Value  # depot SI, frere de celui-ci

    x = Value(5.0, 0.3)
    y = x - x  # vaut exactement 0, quelle que soit la valeur de x -> incertitude vraie = 0
    assert y.n == 0.0
    assert y.u > 0.4  # la propagation Value naive se trompe : incertitude non nulle a tort


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    ok, fail = 0, 0
    for t in tests:
        try:
            t(); ok += 1; print(f"PASS {t.__name__}")
        except Exception as e:
            fail += 1; print(f"FAIL {t.__name__}: {e!r}")
    print(f"\n{ok} réussis, {fail} échoués")
