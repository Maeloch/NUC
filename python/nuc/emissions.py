"""
nuc.emissions — table des raies d'émission LARA (α, γ, X), format confirmé
sur données réelles (Pb-214, Ra-223, Po-218, Bi-214, Po-214 -- voir
docs/samples/lara_real/ et docs/RECONCILIATION.md §9) :

    Energy (keV) ; Ener. unc. (keV) ; Intensity (%) ; Int. unc. (%) ; Type ; Origin ; Lvl. start ; Lvl. end

Confirme l'ordre de colonnes déjà indiqué par le commentaire d'Egamma.m
(type en 5e position) — PAS celui de Lara.cpp::spectre() (2012, type en
1re position), qui reflétait un format plus ancien ou un découpage
différent (espaces plutôt que ';').

Types observés : "g" (gamma), "X..." (rayons X : XL, XKa1, XKa2, XK'b1,
XK'b2 — sous-couche en suffixe), "a" (alpha), "a*" (alpha dit "longue
portée" — depuis un état excité peuplé par la désintégration précédente ;
rencontré dans Bi-214.lara.txt sous forme de raies alpha du Po-214,
descendant à vie très courte, inclus dans le même fichier par convention
spectroscopique). Les champs numériques peuvent être vides (incertitude
non publiée) — remplacés par NaN, pas 0, pour rester distinguables d'une
incertitude réellement nulle.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from .lara_client import LaraClient


@dataclass
class EmissionLine:
    energy_keV: float
    unc_energy_keV: float
    intensity_pct: float
    unc_intensity_pct: float
    type_: str
    origin: str
    lvl_start: str
    lvl_end: str


def _f(s: str) -> float:
    s = s.strip()
    return float(s) if s else math.nan


def emission_lines(client: LaraClient, nuclide: str, type_prefixes: tuple[str, ...]) -> list[EmissionLine]:
    """Raies dont le `Type` commence par l'un de `type_prefixes` (ex.
    `("g","X")` pour gamma+X comme Egamma.m, `("a",)` pour alpha)."""
    text = client.fetch(nuclide)
    if not text:
        return []

    lines = text.splitlines()
    try:
        header_idx = next(i for i, l in enumerate(lines) if l.strip().startswith("Energy (keV)"))
    except StopIteration:
        return []  # "No emissions..." ou format inattendu

    out = []
    for line in lines[header_idx + 1:]:
        if line.strip().startswith("="):
            break
        parts = [p.strip() for p in line.split(";")]
        if len(parts) < 6:
            continue
        type_ = parts[4]
        if not any(type_.startswith(p) for p in type_prefixes):
            continue
        out.append(EmissionLine(
            energy_keV=_f(parts[0]), unc_energy_keV=_f(parts[1]),
            intensity_pct=_f(parts[2]), unc_intensity_pct=_f(parts[3]),
            type_=type_, origin=parts[5],
            lvl_start=parts[6] if len(parts) > 6 else "",
            lvl_end=parts[7] if len(parts) > 7 else "",
        ))
    return out


def Egamma(client: LaraClient, nuclide: str) -> list[EmissionLine]:
    """Gamma + rayons X (types "g" et "X..."). Port d'Egamma.m."""
    return emission_lines(client, nuclide, ("g", "X"))


def Ealpha(client: LaraClient, nuclide: str) -> list[EmissionLine]:
    """Alpha, y compris "longue portée" (types "a" et "a*"). Port d'Ealpha.m."""
    return emission_lines(client, nuclide, ("a",))
