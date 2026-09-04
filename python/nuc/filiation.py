"""
nuc.filiation — décompose l'arbre de décroissance (branchements compris)
d'un nucléide en chemins linéaires (« branches de filiation »), prêts à
être passés un par un à `nuc.bateman.bateman`. Reconstruction de
`wholechain.m`, sur les deux points que vous avez signalés :

1. **Lenteur des accès fichier** : `wholechain.m` appelle `decayWay()` pour
   chaque nucléide de chaque branche, PUIS ré-ouvre le fichier de chaque
   nucléide une seconde fois dans sa boucle finale (`lambda(...)`) — sans
   cache, un nucléide partagé par plusieurs branches (très courant : les
   ancêtres communs) est relu autant de fois qu'il apparaît. Ici, tout
   passe par une unique instance de `LaraClient` réutilisée pour tout
   l'arbre : chaque nucléide n'est effectivement récupéré (réseau ou
   cache disque) qu'une seule fois, quel que soit le nombre de branches
   qui le traversent (voir `test_filiation.py`, qui vérifie précisément
   ce point : nombre d'appels réseau == nombre de nucléides UNIQUES, pas
   nombre d'occurrences dans les branches).

2. **Logique de `conct`** : en relisant `wholechain.m`, la branche créée
   pour la 2ᵉ (3ᵉ, ...) fille d'un embranchement a TOUT son `conct` mis à
   zéro, y compris sa toute dernière position — qui est pourtant cette
   fille elle-même, un nucléide qui n'apparaît dans AUCUNE autre branche.
   Avec `decayNAtoms.m` (`atoms(t,k) += results(i,j)*conct(i,j)`), la
   population de cette fille n'est alors jamais comptabilisée nulle part.
   Ici, la règle est : la première branche (dans l'ordre où elles sont
   énumérées) qui atteint un nucléide donné le « réclame » (`conct=1`) ;
   toute branche qui le retraverse ensuite (ascendance partagée) le
   compte à zéro. Testé sur un embranchement à 2 filles : les DEUX
   filles apparaissent dans le total, chacune comptée une seule fois.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .lara_client import LaraClient


@dataclass
class FiliationBranch:
    names: list[str] = field(default_factory=list)
    lambdas: list[float] = field(default_factory=list)   # s^-1, un par nucleide de `names`
    ratios: list[float] = field(default_factory=list)    # fraction (0-1) names[i] -> names[i+1] ; ratios[-1] inutilise (convention bateman.m)
    conct: list[int] = field(default_factory=list)        # 0/1 : compter names[i] depuis CETTE branche ?


def wholechain(client: LaraClient, father: str) -> list[FiliationBranch]:
    """Decompose l'arbre de decroissance de `father` en branches lineaires.
    Une seule instance de `client` doit etre reutilisee pour tout l'arbre
    (voir docstring du module) -- ne pas en recreer une par appel.

    Note de conception (trouvee en testant sur un cas de reconvergence,
    A -> B/C -> D commun aux deux) : un simple ensemble global "deja vu"
    confond deux situations differentes -- un PREFIXE partage entre deux
    branches sœurs (vraie redondance : A calcule deux fois donnerait
    exactement la meme valeur, un seul comptage suffit) et un point de
    RECONVERGENCE en aval (D atteint via B ET via C : ce sont deux
    contributions DIFFERENTES, calculees avec des rapports de branchement
    differents, qui doivent s'ADDITIONNER, pas se dedupliquer). Utiliser un
    ensemble global aurait, comme un ensemble global l'aurait fait, compte
    D une seule fois au lieu de deux -- masse non conservee dans les tests.
    Corrige : seul le prefixe explicitement partage au moment precis d'un
    embranchement est remis a zero (voir `else` ci-dessous) ; tout nœud
    nouvellement visite en aval repart avec conct=1 par defaut, qu'il
    s'agisse d'un nœud jamais vu ou d'un point de reconvergence."""
    branches: list[FiliationBranch] = []

    def visit(prefix_names, prefix_lambdas, prefix_ratios, prefix_conct, nuclide, own_conct):
        names = prefix_names + [nuclide]
        lambdas = prefix_lambdas + [client.decay_constant(nuclide)[0]]
        conct = prefix_conct + [own_conct]

        daughters = client.daughters(nuclide)  # [(voie, fille, pct), ...]

        if not daughters:
            branches.append(FiliationBranch(
                names=names, lambdas=lambdas,
                ratios=prefix_ratios + [0.0],  # dernier maillon : ratio non utilise par bateman()
                conct=conct,
            ))
            return

        for idx, (_way, daughter, pct) in enumerate(daughters):
            if idx == 0:
                # Premiere fille : prolonge la branche courante, le prefixe
                # (y compris `nuclide`) garde le conct qu'on vient de calculer.
                visit(names, lambdas, prefix_ratios + [pct / 100.0], conct, daughter, own_conct=1)
            else:
                # 2e fille et suivantes : ce meme prefixe (jusqu'a `nuclide`
                # inclus) est deja entierement compte par la branche de la
                # 1ere fille -> remis a zero ICI (uniquement ce prefixe
                # explicite, pas un etat global) pour eviter le double
                # comptage. `daughter`, elle, est nouvelle dans CETTE
                # branche et repart a conct=1 -- que ce soit un nœud
                # jamais visite ou un point de reconvergence en aval.
                visit(names, lambdas, prefix_ratios + [pct / 100.0], [0] * len(conct), daughter, own_conct=1)

    visit([], [], [], [], father, own_conct=1)
    return branches

    visit([], [], [], [], father)
    return branches
