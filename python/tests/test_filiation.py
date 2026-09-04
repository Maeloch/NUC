"""Tests de nuc.filiation : décomposition en branches, conct correct sur un
embranchement (les 2 filles doivent apparaître, chacune comptée une fois),
et vérification qu'un nucléide partagé par plusieurs branches n'est
récupéré (réseau/cache) qu'une seule fois -- le point de lenteur que vous
avez signalé pour wholechain.m."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nuc.lara_client import LaraClient, FetchResult
from nuc.filiation import wholechain
from nuc.bateman import bateman
import numpy as np


def _client_for(data: dict[str, str], call_counter: dict[str, int] | None = None) -> LaraClient:
    def fetch(url, timeout):
        for nuclide, text in data.items():
            if nuclide in url:
                if call_counter is not None:
                    call_counter[nuclide] = call_counter.get(nuclide, 0) + 1
                return FetchResult(200, text)
        return FetchResult(404, "")
    return LaraClient(fetch, read_local_cache_fn=lambda n: "")


def _lara(nuclide: str, daughters: list[tuple[str, str, float]], lam: float) -> str:
    d = "Daughter(s) ; " + " ; ".join(f"{w} ; {n} ; {p}" for w, n, p in daughters) if daughters else ""
    lines = [f"Nuclide ; {nuclide}"]
    if d:
        lines.append(d)
        lines.append(f"Decay constant (1/s) ; {lam} ; {lam*0.01}")
    return "\n".join(lines) + "\n"


# --- Chaine lineaire simple : A -> B -> C(stable) ---
LINEAR = {
    "A": _lara("A", [("beta-", "B", 100.0)], 1e-3),
    "B": _lara("B", [("beta-", "C", 100.0)], 2e-3),
    "C": _lara("C", [], 0.0),
}

# --- Embranchement : A -> B (60%) et A -> C (40%), B et C stables ---
BRANCHING = {
    "A": _lara("A", [("beta-", "B", 60.0), ("alpha", "C", 40.0)], 1e-3),
    "B": _lara("B", [], 0.0),
    "C": _lara("C", [], 0.0),
}

# --- Embranchement PUIS re-convergence : A -> B(70%)/C(30%), B -> D, C -> D ---
# (ancetre commun D atteint par 2 branches differentes : doit n'etre compte qu'une fois)
RECONVERGE = {
    "A": _lara("A", [("beta-", "B", 70.0), ("beta-", "C", 30.0)], 1e-3),
    "B": _lara("B", [("beta-", "D", 100.0)], 5e-4),
    "C": _lara("C", [("beta-", "D", 100.0)], 8e-4),
    "D": _lara("D", [], 0.0),
}


def test_linear_chain_single_branch():
    client = _client_for(LINEAR)
    branches = wholechain(client, "A")
    assert len(branches) == 1
    assert branches[0].names == ["A", "B", "C"]
    assert branches[0].conct == [1, 1, 1]  # aucun partage, tout compte


def test_branching_both_daughters_counted():
    client = _client_for(BRANCHING)
    branches = wholechain(client, "A")
    assert len(branches) == 2

    # branche 1 : A(conct=1) -> B(conct=1)
    # branche 2 : A(conct=0, deja compte) -> C(conct=1, nouvelle)
    names_conct = {tuple(b.names): b.conct for b in branches}
    assert names_conct[("A", "B")] == [1, 1]
    assert names_conct[("A", "C")] == [0, 1]  # <- le point corrige : C doit valoir 1, pas 0

    # Chaque nucleide unique (A, B, C) doit apparaitre avec conct=1 EXACTEMENT une fois au total
    from collections import Counter
    all_names = [n for b in branches for n in b.names]
    all_conct = [c for b in branches for c in b.conct]
    ones = Counter(n for n, c in zip(all_names, all_conct) if c == 1)
    assert ones == Counter({"A": 1, "B": 1, "C": 1})


def test_reconvergent_descendant_counted_once_per_distinct_path():
    """D est atteint par 2 chemins distincts (via B et via C), avec des
    rapports de branchement differents : ce sont deux contributions
    DIFFERENTES a additionner (pas des doublons a dedupliquer comme le
    prefixe A partage). D doit donc apparaitre avec conct=1 dans les DEUX
    branches -- seul A (le prefixe reellement partage) doit etre dedoublonne.
    Voir docstring de nuc.filiation.wholechain pour la distinction."""
    client = _client_for(RECONVERGE)
    branches = wholechain(client, "A")

    from collections import Counter
    all_names = [n for b in branches for n in b.names]
    all_conct = [c for b in branches for c in b.conct]
    ones = Counter(n for n, c in zip(all_names, all_conct) if c == 1)
    assert ones == Counter({"A": 1, "B": 1, "C": 1, "D": 2}), ones


def test_shared_nuclide_fetched_only_once():
    """Le point de lenteur signale : A apparait dans les 2 branches de
    BRANCHING (prefixe commun) -- doit etre recupere UNE seule fois."""
    calls: dict[str, int] = {}
    client = _client_for(BRANCHING, call_counter=calls)
    wholechain(client, "A")
    # A, B, C sont chacun un nucleide UNIQUE -> chacun doit avoir ete
    # recupere exactement 1 fois, meme si A est traverse par les 2 branches.
    assert calls == {"A": 1, "B": 1, "C": 1}, calls


def test_reconvergent_shared_nuclides_fetched_once_each():
    calls: dict[str, int] = {}
    client = _client_for(RECONVERGE, call_counter=calls)
    wholechain(client, "A")
    # D est traverse par les 2 branches (via B et via C) : doit quand meme
    # n'etre recupere qu'une fois (comme A, B, C).
    assert calls == {"A": 1, "B": 1, "C": 1, "D": 1}, calls


def test_end_to_end_with_bateman_mass_conservation():
    """Pipeline complet filiation -> bateman : la somme des populations
    ponderees par conct doit converger vers N0 initial a temps long (aucune
    perte, aucun double comptage), sur le cas avec reconvergence."""
    client = _client_for(RECONVERGE)
    branches = wholechain(client, "A")

    t = 1e6  # temps tres long devant toutes les demi-vies -> tout descend en D (stable)
    total = 0.0
    for b in branches:
        N0 = [1000.0 if i == 0 else 0.0 for i in range(len(b.names))]
        result = bateman(np.array(b.lambdas), np.array(b.ratios), np.array(N0), t)
        total += sum(r * c for r, c in zip(result, b.conct))

    assert abs(total - 1000.0) < 1.0, f"masse non conservee : {total}"


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    ok, fail = 0, 0
    for t in tests:
        try:
            t(); ok += 1; print(f"PASS {t.__name__}")
        except Exception as e:
            fail += 1; print(f"FAIL {t.__name__}: {e!r}")
    print(f"\n{ok} réussis, {fail} échoués")
