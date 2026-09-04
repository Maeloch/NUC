"""
nuc.chain — chaîne de décroissance (nucléide de départ + tous ses
descendants, récursivement). Port direct de chain.m/daughters.m : logique
de parcours de graphe pure, indépendante des incertitudes de format
d'`docs/RECONCILIATION.md` §3 (elle ne dépend que de `LaraClient.daughters`,
déjà testée).
"""
from __future__ import annotations
from .lara_client import LaraClient


def daughters(client: LaraClient, elt_name: str) -> list[str]:
    """Tous les descendants de `elt_name` (récursif, sans doublon), dans
    l'ordre de découverte. Port de daughters.m."""
    elements = [d for _way, d, _pct in client.daughters(elt_name)]
    seen = set(elements)
    i = 0
    while i < len(elements):
        for _way, d, _pct in client.daughters(elements[i]):
            if d not in seen:
                seen.add(d)
                elements.append(d)
        i += 1
    return elements


def chain(client: LaraClient, elt_name: str) -> list[str]:
    """[elt_name] + tous ses descendants. Port de chain.m."""
    return [elt_name] + daughters(client, elt_name)
