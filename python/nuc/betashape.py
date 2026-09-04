"""
nuc.betashape — lecture des fichiers BetaShape (X. Mougeot, LNHB), format
confirmé directement sur `beta-_H3_tot.bs` (H-3, réf. réelle) :
    - 15 lignes d'en-tête (titre, version, auteur, référence à citer,
      énergie moyenne annoncée, ligne de colonnes)
    - puis 3 colonnes : E (keV), dN/dE (par keV), incertitude-type
Confirme le saut de 15 lignes déjà supposé par Ebetam.m/Ebetap.m
(`bsfile`) — c'était juste, contrairement à la table d'émissions LARA qui,
elle, restait incertaine (voir docs/RECONCILIATION.md §3.3).

Convention de nom de fichier observée : "beta-_H3_tot.bs" ->
"{beta-|beta+}_{nucléide}_{tot|<n° de transition>}.bs".
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import numpy as np

_MEAN_ENERGY_RE = re.compile(r"Mean energy.*?:\s*([\d.]+)\s*\(?(\d*)\)?\s*keV")


@dataclass
class BetaSpectrum:
    energy_keV: np.ndarray       # E, keV
    density_per_keV: np.ndarray  # dN/dE, par keV
    unc_density: np.ndarray      # incertitude-type sur dN/dE
    mean_energy_keV: float       # annoncée dans le fichier (auto-cohérence : voir test)
    endpoint_keV: float          # derniere valeur de E (le point ou dN/dE retombe a 0)


def read_betashape_file(path: str) -> BetaSpectrum:
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    mean_e = float("nan")
    for line in lines[:15]:
        m = _MEAN_ENERGY_RE.search(line)
        if m:
            mean_e = float(m.group(1))
            break

    rows = [ln.split() for ln in lines[15:] if ln.strip()]
    data = np.array([[float(x) for x in r] for r in rows])
    E, dNdE, unc = data[:, 0], data[:, 1], data[:, 2]

    return BetaSpectrum(
        energy_keV=E, density_per_keV=dNdE, unc_density=unc,
        mean_energy_keV=mean_e, endpoint_keV=float(E[-1]),
    )


def betashape_filename(nuclide: str, sign: str, transition: str = "tot") -> str:
    """sign: "-" ou "+". Ex. betashape_filename("H-3","-") -> "beta-_H-3_tot.bs"
    -- NOTE : l'exemple reçu est "beta-_H3_tot.bs" (sans le tiret dans
    "H3") ; à confirmer si la convention de nommage retire systématiquement
    le tiret du nom de nucléide ou si c'est spécifique à cet exemple."""
    return f"beta{sign}_{nuclide}_{transition}.bs"
