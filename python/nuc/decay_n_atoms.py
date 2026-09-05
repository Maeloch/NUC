"""
nuc.decay_n_atoms — port de decayNAtoms.m/decayNAtoms2.m : population de
TOUS les descendants d'un nucléide, sur une grille de temps, à partir d'un
nombre d'atomes initial. Assemble `wholechain` (filiation.py, corrigée
§8) et `bateman` (vectorisé, §6) — les deux déjà validées indépendamment
à <0,005 % contre l'outil de référence LNHB sur la chaîne Rn-222 (§11).
"""
from __future__ import annotations
import numpy as np
from .lara_client import LaraClient
from .filiation import wholechain


def decay_n_atoms(client: LaraClient, father: str, natom0: float, times) -> dict[str, np.ndarray]:
    """Nombre d'atomes de `father` et de tous ses descendants, à chaque
    instant de `times` (scalaire ou tableau), en partant de `natom0`
    atomes de `father` à t=0 (les descendants démarrent à 0 — comme
    decayNAtoms.m). Renvoie {nom_nucleide: tableau (T,) ou scalaire}.

    Équivaut à decayNAtoms.m (chaîne depuis un seul point de départ) —
    pour l'usage de decayNAtoms2.m (reprendre une filiation déjà calculée
    à un instant intermédiaire, avec des N0 différents par branche),
    appeler `wholechain` séparément et passer le résultat à `bateman`
    directement (voir docs/RECONCILIATION.md §6 pour pourquoi
    `decayNAtoms2` n'a pas été portée telle quelle : son but principal,
    initialiser chaque isotope de la chaîne à un N0 différent, se fait
    plus simplement en construisant le tableau N0 par branche à la main).
    """
    branches = wholechain(client, father)
    times_arr = np.atleast_1d(np.asarray(times, dtype=float))

    totals: dict[str, np.ndarray] = {}
    for b in branches:
        from .bateman import bateman  # import tardif : evite un cycle
        N0 = np.array([natom0 if i == 0 else 0.0 for i in range(len(b.names))])
        result = bateman(np.array(b.lambdas), np.array(b.ratios), N0, times_arr)  # (T, N)
        for j, (name, c) in enumerate(zip(b.names, b.conct)):
            if not c:
                continue
            contribution = result[:, j]
            totals[name] = totals.get(name, np.zeros_like(contribution)) + contribution

    if np.ndim(times) == 0:
        return {k: v[0] for k, v in totals.items()}
    return totals


def decay_n_atoms_activities(client: LaraClient, father: str, natom0: float, times) -> dict[str, np.ndarray]:
    """Comme `decay_n_atoms`, mais renvoie les activités (Bq = N.λ) plutôt
    que les nombres d'atomes bruts — c'est ce que la démonstration Rn-222
    (docs/samples/rn222_demo.py) compare à l'outil de référence LNHB."""
    from .lara_client import LaraClient as _LC  # (pour le type hint seulement)
    atoms = decay_n_atoms(client, father, natom0, times)
    lambdas = {name: client.decay_constant(name)[0] for name in atoms}
    return {name: n * lambdas[name] for name, n in atoms.items()}
