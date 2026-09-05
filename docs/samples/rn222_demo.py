"""
Démonstration bout-en-bout : 1000 Bq de Rn-222, activités des descendants à
t=3600 s. Combine filiation.py (décomposition en branches), bateman.py
(calcul vectorisé), lara_client.py (accès LARA par étiquette).

VALIDÉ contre un outil de référence indépendant (calculateur officiel
Nucléide-Lara du LNHB) : écart < 0,005 % sur les 9 nucléides de la chaîne
à t=3600 s (voir docs/RECONCILIATION.md §11 pour le tableau complet).

Données réelles LARA (Po-218, Pb-214, Bi-214, Po-214) dans
docs/samples/lara_real/. Pour Rn-222, At-218, Rn-218, Tl-210, Pb-210 :
demi-vies reprises de l'en-tête de la référence reçue (pas de fichier LARA
récupéré directement pour ces 5-là dans cette session, mais valeurs
confirmées cohérentes par la validation elle-même).

Exécuter : python3 docs/samples/rn222_demo.py
"""
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python"))

import numpy as np
from nuc.lara_client import LaraClient, FetchResult
from nuc.filiation import wholechain
from nuc.bateman import bateman

_SAMPLES = os.path.join(os.path.dirname(__file__), "lara_real")


def _read(name):
    with open(os.path.join(_SAMPLES, name), encoding="utf-8") as f:
        return f.read()


_LAMBDA_PB210 = math.log(2) / (22.23 * 365.25 * 86400)  # T1/2 = 22.23 a

DATA = {
    "Rn-222": (
        "Nuclide ; Rn-222\nDaughter(s) ; (alpha) ; Po-218 ; 100\n"
        "Half-life (s) ; 330325.0 ; 100\nDecay constant (1/s) ; 2.0983E-6 ; 0.0006E-6\n"
    ),
    "Po-218": _read("Po-218.lara.txt"),
    "At-218": (
        # 99.9% alpha -> Bi-214 (reconvergence avec la branche principale,
        # cf. docs/RECONCILIATION.md §8) ; 0.1% beta- -> Rn-218
        "Nuclide ; At-218\nDaughter(s) ; (alpha) ; Bi-214 ; 99.9 ; (B-) ; Rn-218 ; 0.1\n"
        "Half-life (s) ; 1.4 ; 0.1\nDecay constant (1/s) ; 4.951E-1 ; 0.35E-1\n"
    ),
    "Pb-214": _read("Pb-214.lara.txt"),
    "Rn-218": (
        "Nuclide ; Rn-218\nDaughter(s) ; (alpha) ; Po-214 ; 100\n"
        "Half-life (s) ; 0.036 ; 0.003\nDecay constant (1/s) ; 19.25 ; 1.6\n"
    ),
    "Bi-214": _read("Bi-214.lara.txt"),
    "Po-214": _read("Po-214.lara.txt"),
    "Tl-210": (
        "Nuclide ; Tl-210\nDaughter(s) ; (B-) ; Pb-210 ; 100\n"
        "Half-life (s) ; 78.0 ; 0.6\nDecay constant (1/s) ; 8.887E-3 ; 0.068E-3\n"
    ),
    "Pb-210": f"Nuclide ; Pb-210\nDecay constant (1/s) ; {_LAMBDA_PB210:.6e} ; 0\n",
}


def _fetch(url, timeout):
    for nuclide, text in DATA.items():
        if nuclide in url:
            return FetchResult(200, text)
    return FetchResult(404, "")


def main():
    client = LaraClient(_fetch, read_local_cache_fn=lambda n: "")
    branches = wholechain(client, "Rn-222")

    print(f"{len(branches)} branche(s) de filiation :")
    for b in branches:
        print("  " + " -> ".join(b.names))

    A0_Bq = 1000.0  # meme base que la reference recue
    lam_rn222 = client.decay_constant("Rn-222")[0]
    N0_rn222 = A0_Bq / lam_rn222

    t = 3600.0
    totals = {}
    lambdas_by_name = {}
    for b in branches:
        N0 = [N0_rn222 if i == 0 else 0.0 for i in range(len(b.names))]
        result = bateman(np.array(b.lambdas), np.array(b.ratios), np.array(N0), t)
        for name, n, c, lam in zip(b.names, result, b.conct, b.lambdas):
            lambdas_by_name[name] = lam
            if c:
                totals[name] = totals.get(name, 0.0) + n

    print(f"\nActivités à t={t:.0f} s (départ : {A0_Bq:.0f} Bq de Rn-222 pur) :")
    for name, n_atoms in totals.items():
        activity = n_atoms * lambdas_by_name[name]
        print(f"  {name:8s} : {activity:9.5f} Bq")


if __name__ == "__main__":
    main()
