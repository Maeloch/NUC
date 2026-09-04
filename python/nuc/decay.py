"""
nuc.decay — loi de décroissance radioactive. Port de NUC.xlam / nuc.bas.

Repris du travail déjà réalisé et testé (chat précédent) : les 4 dérivées
partielles de `decay()` ont été vérifiées indépendamment par différences
finies (écart < 1e-9 relatif) sur un cas Co-60 (T½ NNDC). Non re-dérivé ici.
"""
from __future__ import annotations
import math


def decroissance(A0: float, date_origine_j: float, date_actuelle_j: float, periode_j: float) -> float:
    """Activité décrue, sans incertitude. Dates en jours (ex. Excel serial)."""
    return A0 * math.exp(-math.log(2) * (date_actuelle_j - date_origine_j) / periode_j)


def decay(A0: float, u_A0: float,
          date_origine_j: float, u_date_origine: float,
          date_actuelle_j: float, u_date_actuelle: float,
          periode_j: float, u_periode: float) -> tuple[float, float]:
    """Équivalent DECAY() : activité à date_actuelle et son incertitude-type
    (propagation GUM, 4 termes indépendants : A0, date_actuelle,
    date_origine, période). A(t) = A0.exp(-ln2.(t-t0)/T)."""
    dt = date_actuelle_j - date_origine_j
    k = math.exp(-math.log(2) * dt / periode_j)
    valeur = A0 * k

    d_dA0 = k
    d_dt = -A0 * math.log(2) / periode_j * k
    d_dt0 = A0 * math.log(2) / periode_j * k
    d_dT = A0 * math.log(2) * dt / periode_j ** 2 * k

    variance = (d_dA0 * u_A0) ** 2 + (d_dt * u_date_actuelle) ** 2 \
        + (d_dt0 * u_date_origine) ** 2 + (d_dT * u_periode) ** 2
    return valeur, math.sqrt(variance)


def period_from_lambda(lam: float, u_lam: float, unite_s: float = 1.0) -> tuple[float, float]:
    """(T½, u(T½)) dans l'unité choisie (unite_s = durée d'1 unité, en
    secondes). T½ = ln(2)/λ ; u(T½) = ln(2).u(λ)/λ² (un seul terme)."""
    u = 1.0 / unite_s
    t = math.log(2) / lam * u
    u_t = math.log(2) * u_lam / lam ** 2 * u
    return t, u_t


def lambda_from_period(t_half: float, u_t_half: float, unite_s: float = 1.0) -> tuple[float, float]:
    """Inverse de period_from_lambda : (λ, u(λ)) en s⁻¹ à partir de T½."""
    t_half_s = t_half * unite_s
    u_t_half_s = u_t_half * unite_s
    lam = math.log(2) / t_half_s
    u_lam = math.log(2) * u_t_half_s / t_half_s ** 2
    return lam, u_lam
