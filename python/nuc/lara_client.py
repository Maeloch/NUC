"""
nuc.lara_client — Client Laraweb (LNHB) robuste : requête web avec repli sur
cache local, analyse PAR ÉTIQUETTE (jamais par position fixe — voir
docs/RECONCILIATION.md §2 : les 16 .m reçus et Lara.cpp (2012) lisent tous
par position fixe, fragile car le nombre de lignes d'en-tête dépend du
nucléide).

Le transport HTTP et le cache local sont injectés (`fetch_fn`,
`read_local_cache_fn`, `write_local_cache_fn`) : aucune dépendance réseau
ni chemin codé en dur, contrairement à `bddfile.m` (chemin OneDrive
personnel) — voir docs/RECONCILIATION.md §4. Le chemin de cache par défaut
se règle via la variable d'environnement NUC_LARA_CACHE_DIR.

Champs d'en-tête (§3.1 de RECONCILIATION.md) validés sur un vrai fichier
capturé (Zr-95, 09/2026) : Nuclide, Element, Z, Daughter(s), Q+/Q-, Half-life
(d)/(s), Decay constant (1/s), Specific activity (Bq/g), Reference.
La table d'émissions (raies α/β/γ) n'a PAS d'échantillon réel disponible à
ce stade (§3.3) : `emission_lines()` suit l'hypothèse la plus détaillée
disponible (commentaire d'Egamma.m) mais reste NON VÉRIFIÉE.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional
import os

LARA_URL_TEMPLATE = "http://www.lnhb.fr/Laraweb/Results/{nuclide}.lara.txt"
# Confirmé directement (pas de suffixe "_@04" nécessaire, contrairement à
# l'hypothèse précédente — voir docs/RECONCILIATION.md §6) : fonctionne et
# correspond à la recopie locale de l'utilisateur.
DEFAULT_CACHE_DIR = os.environ.get("NUC_LARA_CACHE_DIR", os.path.expanduser("~/.cache/nuc/lara"))


@dataclass
class FetchResult:
    status: int
    text: str


FetchFn = Callable[[str, float], FetchResult]


def looks_like_lara_file(txt: str) -> bool:
    """Un vrai fichier .lara.txt commence par 'Nuclide ;'."""
    return txt.strip().startswith("Nuclide ")


def parse_field(text: str, label: str) -> Optional[list[str]]:
    """Cherche `label` comme un des champs séparés par ';' d'une ligne
    (pas nécessairement le premier — ex. "Q- ; 260 ; Qalpha ; 6114.68" :
    Po-218 a Q- ET Qalpha sur la MÊME ligne, cf. échantillon réel). Renvoie
    la sous-liste [label, valeur, ...] à partir de ce champ, nettoyée.
    None si absent (résultat normal, ex. nucléide stable)."""
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(";")]
        for i, p in enumerate(parts):
            if p == label or p.startswith(label + " "):
                return parts[i:]
    return None


def _default_read_cache(nuclide: str) -> str:
    path = os.path.join(DEFAULT_CACHE_DIR, f"{nuclide}.lara.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _default_write_cache(nuclide: str, text: str) -> None:
    try:
        os.makedirs(DEFAULT_CACHE_DIR, exist_ok=True)
        with open(os.path.join(DEFAULT_CACHE_DIR, f"{nuclide}.lara.txt"), "w", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        pass  # cache local best-effort : un echec d'ecriture ne doit pas interrompre le calcul


class LaraClient:
    """Cache mémoire (par nucléide) + repli sur cache local injectable."""

    def __init__(self, fetch_fn: FetchFn,
                 read_local_cache_fn: Callable[[str], str] = _default_read_cache,
                 write_local_cache_fn: Callable[[str, str], None] = _default_write_cache,
                 timeout_s: float = 5.0):
        self._fetch = fetch_fn
        self._read_cache = read_local_cache_fn
        self._write_cache = write_local_cache_fn
        self._timeout = timeout_s
        self._memory_cache: dict[str, str] = {}

    def fetch(self, nuclide: str, force_web: bool = False) -> str:
        if not force_web and nuclide in self._memory_cache:
            return self._memory_cache[nuclide]

        url = LARA_URL_TEMPLATE.format(nuclide=nuclide)
        text = ""
        try:
            r = self._fetch(url, self._timeout)
            if r.status == 200 and looks_like_lara_file(r.text):
                text = r.text
                self._write_cache(nuclide, text)
        except Exception:
            text = ""

        if not text:
            text = self._read_cache(nuclide)

        self._memory_cache[nuclide] = text
        return text

    def field(self, nuclide: str, label: str) -> Optional[list[str]]:
        text = self.fetch(nuclide)
        return parse_field(text, label) if text else None

    def is_stable(self, nuclide: str) -> bool:
        return self.field(nuclide, "Decay constant") is None

    def decay_constant(self, nuclide: str) -> tuple[float, float]:
        if self.is_stable(nuclide):
            return 0.0, 0.0
        f = self.field(nuclide, "Decay constant")
        return float(f[1]), float(f[2])

    def specific_activity(self, nuclide: str) -> tuple[float, float]:
        """Bq/g. Le champ s'appelle "Specific activity" dans les vraies
        données LARA — massActivity.m (reçu) cherche par erreur "Mass
        activity" en commentaire (fonctionne quand même car il ne teste
        que le 1er caractère 'S', voir docs/RECONCILIATION.md §3.1)."""
        if self.is_stable(nuclide):
            return 0.0, 0.0
        f = self.field(nuclide, "Specific activity")
        return float(f[1]), float(f[2])

    def daughters(self, nuclide: str) -> list[tuple[str, str, float]]:
        """[(voie, nucléide_fils, intensité_%), ...]. 3 champs par voie,
        SANS incertitude sur l'intensité (suit decayWay.m, le plus récent
        des deux formats trouvés — voir docs/RECONCILIATION.md §3.2 pour
        l'écart avec Lara.cpp/2012, qui attendait un 4e champ)."""
        f = self.field(nuclide, "Daughter(s)")
        if f is None:
            return []
        rest = f[1:]  # apres l'etiquette "Daughter(s)"
        out = []
        for i in range(0, len(rest) - 2, 3):
            way, daughter, pct = rest[i], rest[i + 1], rest[i + 2]
            try:
                out.append((way, daughter, float(pct)))
            except ValueError:
                break
        return out

    def q_value(self, nuclide: str, kind: str) -> Optional[float]:
        """kind: "Q+", "Q-", "Qalpha", ... (voir totalEnergyQ.m)."""
        f = self.field(nuclide, kind)
        return float(f[1]) if f else None


def default_client(fetch_fn: FetchFn) -> LaraClient:
    """Construit un client avec le cache disque par défaut
    (NUC_LARA_CACHE_DIR ou ~/.cache/nuc/lara)."""
    return LaraClient(fetch_fn)
