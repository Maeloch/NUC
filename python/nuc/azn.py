"""
nuc.azn — analyse d'un nom de nucléide ("Co-60", "Ta-180m", "H-3", ...) en
(A, Z, N, état). Fonction absente des 16 fichiers .m reçus (référencée dans
massActivity.m, Sbeta.m) mais présente sous le nom `Lara::A`/`Lara::Z`/
`Lara::S` dans Lara.cpp (2012) — reconstituée à partir de cette source,
voir docs/RECONCILIATION.md §5.

Convention (identique à Lara.cpp) :
    - Z : numéro atomique, déduit du symbole (avant le premier "-")
    - A : nombre de masse, après le dernier "-" (un éventuel suffixe "m"
      métastable final est retiré avant la conversion en entier)
    - état : "F" (fondamental) ou "M" (métastable, nom se terminant par
      un caractère non numérique, typiquement "m" — ex. "Ta-180m")
    - N = A - Z (nombre de neutrons)
"""
from __future__ import annotations
from dataclasses import dataclass
from .periodic_table import z_of_symbol, symbol_of_z


@dataclass(frozen=True)
class Nuclide:
    A: int
    Z: int
    N: int
    state: str  # "F" ou "M"


def AZN(elt_name: str) -> Nuclide:
    """Analyse "Co-60" -> Nuclide(A=60, Z=27, N=33, state='F').
    "Ta-180m" -> Nuclide(A=180, Z=73, N=107, state='M')."""
    state = "M" if not elt_name[-1].isdigit() else "F"
    core = elt_name[:-1] if state == "M" else elt_name

    symbol, _, mass_str = core.rpartition("-")
    z = z_of_symbol(symbol)
    a = int(mass_str)
    return Nuclide(A=a, Z=z, N=a - z, state=state)


def nuclide_name(a: int, z: int, state: str = "F", sep: str = "-") -> str:
    """Reconstruit un nom : (60, 27, 'F') -> "Co-60" ; (180, 73, 'M') -> "Ta-180m"."""
    symbol = symbol_of_z(z)
    suffix = "m" if state != "F" else ""
    return f"{symbol}{sep}{a}{suffix}"
