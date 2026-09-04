"""
Démonstration bout-en-bout : 100 Bq de Rn-222, activités des descendants à
t=3600 s. Combine filiation.py (décomposition en branches), bateman.py
(calcul vectorisé), lara_client.py (accès LARA par étiquette).

Données réelles LARA (Po-218, Pb-214, Bi-214, Po-214) sauvegardées dans
docs/samples/lara_real/. Pour Rn-222, Tl-210, Pb-210 : PAS de fichier LARA
récupéré dans cette session — demi-vies de littérature (bien établies,
mais non vérifiées directement sur LARA comme le reste). At-218 (branche
β⁻ de Po-218, 0.022 %) traité comme stable faute de données — sous-estime
légèrement cette branche déjà marginale ; Rn-218 (descendant d'At-218) non
inclus du tout. Voir docs/RECONCILIATION.md §9 pour le détail complet.

Exécuter : python3 docs/samples/rn222_demo.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python"))

import numpy as np
from nuc.lara_client import LaraClient, FetchResult
from nuc.filiation import wholechain
from nuc.bateman import bateman

_SAMPLES = os.path.join(os.path.dirname(__file__), "lara_real")


def _read(name):
    with open(os.path.join(_SAMPLES, name), encoding="utf-8") as f:
        return f.read()


DATA = {
    "Rn-222": (
        "Nuclide ; Rn-222\n"
        "Daughter(s) ; (alpha) ; Po-218 ; 100\n"
        "Half-life (s) ; 330350.4 ; 100\n"
        "Decay constant (1/s) ; 2.0982E-6 ; 0.0006E-6\n"
    ),  # litterature (T1/2 = 3.8235 j) -- pas recupere sur LARA cette session
    "Po-218": _read("Po-218.lara.txt"),
    "Pb-214": _read("Pb-214.lara.txt"),
    "Bi-214": _read("Bi-214.lara.txt"),
    "Po-214": _read("Po-214.lara.txt"),
    "Tl-210": (
        "Nuclide ; Tl-210\n"
        "Daughter(s) ; (B-) ; Pb-210 ; 100\n"
        "Half-life (s) ; 78.0 ; 0.6\n"
        "Decay constant (1/s) ; 8.887E-3 ; 0.068E-3\n"
    ),  # litterature (T1/2 = 1.30 min)
    "Pb-210": (
        "Nuclide ; Pb-210\n"
        "Half-life (s) ; 700614720 ; 3153600\n"
    ),  # litterature (T1/2 = 22.20 a) -- pas de "Decay constant" : traite
        # comme un puits final sur l'echelle de temps de cette demo (1h)
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

    A0_Bq = 100.0
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
        print(f"  {name:8s} : {activity:9.4f} Bq")


if __name__ == "__main__":
    main()
