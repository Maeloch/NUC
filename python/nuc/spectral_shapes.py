"""
nuc.spectral_shapes — formes de raies et de spectre continu, pour la
synthèse d'un spectre de désintégration (port de Palpha.m/Pelectron.m/
Pgamma.m ; Pbeta reconstruite, voir plus bas).
"""
from __future__ import annotations
import math
import numpy as np


def Palpha(energy, mu: float, sigma: float):
    """Raie alpha : gaussienne normalisée (aire = 1). Port direct de Palpha.m."""
    energy = np.asarray(energy, dtype=float)
    return 1.0 / (math.sqrt(2 * math.pi) * sigma) * np.exp(-((energy - mu) ** 2) / (2 * sigma ** 2))


def Pelectron(energies, mu: float):
    """Raie de capture électronique (X/Auger) : port direct de Pelectron.m.
    `sigma` est dérivée de l'étendue de la grille `energies` elle-même
    (2*(max-min)/n, puis mise à l'échelle par 2000 — constante empirique
    du fichier d'origine, non redérivée ici), et le résultat est normalisé
    en somme (distribution discrète), pas en intégrale continue comme
    Palpha."""
    energies = np.asarray(energies, dtype=float)
    sigma = 2.0 * (energies[-1] - energies[0]) / energies.size
    y = np.exp(-((energies - mu) ** 2) / (2000.0 * sigma ** 2))
    return y / y.sum()


def Pgamma(energies, mu: float, sigma: float, tail=()):
    """Raie gamma : gaussienne, avec 0, 1 ou 2 paramètres de traîne basse
    énergie (modèle exponentiel raccordé, courant en spectrométrie gamma
    pour représenter la diffusion Compton incomplète). Port direct de
    Pgamma.m ; `tail` : tuple vide, à 1 ou 2 éléments (le second pondère
    la traîne par sqrt(energy), comme dans le fichier d'origine)."""
    energies = np.asarray(energies, dtype=float)
    n = len(tail)

    if n == 0:
        return np.exp(-((energies - mu) ** 2) / (2 * sigma ** 2))

    if n == 1:
        t = tail[0]
    else:
        t = tail[0] + tail[1] * np.sqrt(energies)

    core = energies >= (mu - t)
    gauss = np.exp(-((energies - mu) ** 2) / (2 * sigma ** 2))
    exp_tail = np.exp(t * (2 * energies - 2 * mu + t) / (2 * sigma ** 2))
    return np.where(core, gauss, exp_tail)


def Pbeta(energy, Z: int, endpoint: float, elt_name: str = ""):
    """
    Forme du spectre béta continu — spectre de Fermi non-relativiste avec
    facteur de Coulomb approché.

    ⚠️ RECONSTRUITE : absente des 16 fichiers .m reçus (référencée par
    Sbeta.m mais jamais fournie). Vous l'aviez décrite (chat précédent)
    comme « une simplification à base de Fermi et autre » — ceci est ma
    meilleure reconstitution de cette description, PAS une vérification
    contre BetaShape ou une table de référence (tritium ou autre) comme le
    reste de ce dépôt. `elt_name` n'est pas utilisé par le calcul lui-même
    (gardé pour compatibilité de signature avec Sbeta.m, qui l'appelle
    ainsi) — statut expérimental, à corriger dès qu'un exemple BetaShape
    est disponible (voir docs/RECONCILIATION.md §5).

    `endpoint` : énergie maximale du spectre (MeV si Z<0 par convention
    Sbeta.m -> beta+, sinon beta- ; le signe encode le type d'émission,
    repris tel quel du fichier d'origine).

    Forme (non-relativiste, sans les corrections radiatives/d'écrantage
    électronique) :
        N(E) ∝ p.(E0-E).F(Z,E)   avec p = sqrt(E.(E+2 mₑc²))
    F(Z,E) : facteur de Fermi, approximation non-relativiste de Bethe :
        F(Z,E) ≈ 2πη / (1 - exp(-2πη)),  η = ∓αZ/β  (- pour β⁻, + pour β⁺)
    """
    MEC2 = 0.510998950  # MeV
    ALPHA = 7.2973525693e-3  # constante de structure fine (CODATA — cf. depot SI)

    energy = np.asarray(energy, dtype=float)
    E0 = abs(endpoint)
    beta_plus = endpoint < 0  # convention Sbeta.m : energies(nrj) positif -> beta-, negatif -> beta+

    with np.errstate(invalid="ignore"):
        T = np.clip(E0 - energy, 0, None)  # energie cinetique residuelle, >=0
        Etot = energy + MEC2
        p = np.sqrt(np.clip(energy * (energy + 2 * MEC2), 0, None))
        beta_v = np.divide(p, Etot, out=np.zeros_like(Etot), where=Etot > 0)

        eta = np.where(beta_v > 0, (-1 if not beta_plus else 1) * ALPHA * Z / np.maximum(beta_v, 1e-12), 0.0)
        two_pi_eta = 2 * math.pi * eta
        # 2*pi*eta / (1 - exp(-2*pi*eta)), limite -> 1 quand eta -> 0
        fermi = np.where(np.abs(two_pi_eta) > 1e-8,
                          two_pi_eta / (1.0 - np.exp(-two_pi_eta)),
                          1.0 + two_pi_eta / 2.0)

        y = p * T * fermi
        y = np.where((energy >= 0) & (energy <= E0), y, 0.0)

    total = y.sum()
    return y / total if total > 0 else y
