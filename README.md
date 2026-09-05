# NUC — données et calculs nucléaires de base

Accès aux données de décroissance radioactive (base LARA du LNHB) et
calculs de chaîne de décroissance (équation de Bateman) — en **Python,
Matlab/Octave, C, et VBA**. Dépend du dépôt [`SI`](../SI) (unités,
`Value`/`si_value`).

Besoin d'origine : les données de base (période, constante de
décroissance, filiation, activité) pour un maximum de radionucléides.
Les calculs plus spécialisés (spectres béta précis, pouvoir d'arrêt/
portée) restent volontairement hors périmètre — des logiciels dédiés
existent déjà pour ça (BetaShape/LNHB, ASTAR/PSTAR/NIST).

Voir [`docs/RECONCILIATION.md`](docs/RECONCILIATION.md) pour l'historique
complet : sources, écarts trouvés entre elles, décisions, et — section
« Annexe » et notes « pas encore fait » disséminées dans chaque partie —
tout ce qui reste ouvert.

## Contenu

| Dossier | Langage | Statut |
|---|---|---|
| [`python/nuc/`](python/nuc) | Python | Complet pour le périmètre ci-dessus, testé |
| [`matlab/`](matlab) | Matlab/Octave | `filiation`/`lara_*`/`bateman`/`periodic_table` portés et testés ; pas de `decay_n_atoms`/`azn`/`emissions` dédiés |
| [`c/`](c) | C99 | `nuc_lara`/`nuc_filiation`/`nuc_bateman`/`nuc_periodic_table` portés et testés ; pas d'`azn`/`emissions`/`decay_n_atoms` dédiés |
| [`vba/source/`](vba/source) | VBA | `LARA.bas` (accès Laraweb corrigé) et `PeriodicTable.bas` ; **pas de `filiation`/`bateman` VBA** (voir Annexe) |
| [`docs/`](docs) | — | `RECONCILIATION.md` (détail complet) + `samples/` (données réelles LARA/BetaShape, démonstrations) |

## Principe

```
periodic_table / azn  →  identifie un nucléide ("Co-60" → A,Z,N,état)
lara_client            →  accès Laraweb par étiquette (pas par position), cache
filiation (wholechain) →  décompose l'arbre de décroissance en branches linéaires
bateman                →  résout chaque branche (vectorisé temps + Monte-Carlo)
decay_n_atoms          →  assemble les deux : population de toute la chaîne, sur une grille de temps
```

```python
import sys; sys.path.insert(0, "python")
from nuc.lara_client import LaraClient
from nuc.decay_n_atoms import decay_n_atoms_activities

client = LaraClient(mon_fetch_http)  # mon_fetch_http : fonction (url, timeout) -> texte
act = decay_n_atoms_activities(client, "Rn-222", N0, [0, 900, 1800, 3600])
```

## Validé contre une référence indépendante

La chaîne Rn-222 (1000 Bq, t=3600 s) donne les mêmes résultats dans les
**trois** langages (Python/Matlab/C), eux-mêmes comparés au calculateur
officiel Nucléide-Lara du LNHB : écart maximal 0,004 % sur 9 nucléides.
Détail complet dans `docs/RECONCILIATION.md` §11 (validation) et §12-13
(parité entre langages).

## Bugs trouvés et corrigés (détail : `docs/RECONCILIATION.md`)

- **`wholechain`** (reconstruite en `filiation.py`/`.m`/`nuc_filiation.c`) :
  la branche d'une 2ᵉ fille d'embranchement ne comptait jamais sa propre
  population ; corrigé, avec une subtilité supplémentaire trouvée en
  testant sur un cas de reconvergence réel (voir §8).
- **`bateman`** : lent en usage Monte-Carlo (un jeu de paramètres par
  appel) — vectorisé sur les tirages et le temps (×15 mesuré) ; garde
  ajoutée contre les lambdas quasi dégénérés (désactivée en commentaire
  dans le fichier reçu).
- **URL LARA** : confirmée (`/Laraweb/Results/`, pas de suffixe requis).
- **Table d'émissions** : ordre de colonnes confirmé sur données réelles
  (celui d'`Egamma.m` était juste, celui du prototype C++ de 2012 obsolète).
- Deux bugs C (`si_units.c`-like : déclarations implicites int-au-lieu-de-
  pointeur) trouvés en compilant, pas en lisant.

## Tests

```bash
# Python
cd python && for f in tests/test_*.py; do python3 "$f"; done

# C (nécessite le dépôt SI cloné à côté, cf. c/Makefile)
cd c && make test

# Matlab / Octave
cd matlab/tests && octave-cli --eval "test_filiation"
```

## Annexe — ce qui n'a volontairement pas été fait

- **Pouvoir d'arrêt / portée (Bethe-Bloch)** : hors périmètre (besoin
  d'origine = données de base, pas de calcul spécialisé — NIST ASTAR/PSTAR
  y répondent déjà). Contexte de recherche conservé dans la conversation
  si repris un jour : Bethe seul dévie fortement aux basses énergies
  (jusqu'à plusieurs centaines de % selon une étude comparative sur
  l'Al₂O₃), ASTAR/SRIM sont la référence fiable.
- **Spectre β précis** (`Pbeta`) : approximation de Fermi, sciemment
  imparfaite pour les transitions complexes (l'auteur lit les vraies
  données BetaShape/LNHB en pratique — `Pbeta` n'est qu'un repli).
- **Émissions combinées au temps** (simuler une mesure : intensités de
  raies × population de chaîne au cours du temps) : objectif clair, pas
  encore assemblé.
- **`NON_PREFIXABLE`** (dépôt `SI`) : ajoutée en Python seulement, pas
  encore reportée vers Matlab/C/VBA.
- **VBA** : pas de `filiation`/`bateman`/`decay_n_atoms` (seul `LARA.bas`,
  déjà corrigé avant cette session, et `PeriodicTable.bas` sont présents).
- **`decayNAtoms2.m`** (reprendre une filiation à un instant intermédiaire
  avec des N0 différents par branche) : pas d'équivalent dédié — se fait
  directement en construisant le tableau N0 par branche avant d'appeler
  `bateman`.
