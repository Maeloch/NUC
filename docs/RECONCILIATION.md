# Réconciliation des sources — bibliothèque NUC

Même principe que `docs/RECONCILIATION.md` du dépôt `SI` : rien n'est
deviné silencieusement, tout est tracé ici. NUC dépend de `SI` (unités,
`Value`/`si_value`, arrondi).

## 1. Sources

| Source | Nature | Statut |
|---|---|---|
| 16 fichiers `.m` (ce chat) | Couche « données + spectres » : accès LARA (`bddfile`, `decayWay`, `totalEnergyQ`, `Ealpha/Ebetam/Ebetap/Eec/Egamma`, `lambda`, `massActivity`), chaîne de décroissance (`chain`, `daughters`), mise en forme de spectre (`Palpha/Pelectron/Pgamma/Sbeta`) | Reçus tels quels ; approche de lecture **fragile** (position fixe), voir §2 |
| `Lara.cpp`/`Lara.hpp` (ce chat) | Classe C++ singleton, 2012, mêmes fonctions (`lambda`, `massActivity`, `decay`, `spectre`, `A`/`Z`/`S`/`name`) + **table des 118 éléments** | La plus ancienne version connue du même besoin ; table d'éléments directement réutilisable, reste fragile (position fixe) — voir §2 |
| `NUC_LARA_corrige.bas` (chat précédent, retrouvé en mémoire) | Module VBA déjà corrigé : URL Laraweb à jour, timeout HTTP, **lecture par étiquette** (pas par position), repli cache local | Référence pour la robustesse — approche reprise ici pour Python/Matlab/C |
| `nuc.decay` (chat précédent, retrouvé en mémoire) | `decay_constant`, `period`, `decroissance`, `decay` (loi de décroissance + propagation GUM à 4 termes) | Déjà testé (dérivées vérifiées par différences finies sur T½ Co-60/NNDC) — repris tel quel |
| Échantillon réel `Zr-95.lara.txt` (chat précédent, capturé par requête directe le 09/2026) | En-tête complet d'un vrai fichier LARA | Fait foi pour les champs d'en-tête (voir §3) ; ne couvre PAS la table d'émissions (raies α/β/γ) |

**Fonctions référencées mais non fournies** (16 fichiers = « presque toutes »,
selon vos mots) : `Pbeta.m` (forme du spectre β continu), `bsfile.m` (accès
aux fichiers BetaShape), et le format exact des fichiers BetaShape
lui-même. Reconstruits au mieux ci-dessous, clairement signalés comme tels
— voir §5.

## 2. Fragilité systématique de la lecture (3 générations, même défaut)

`Lara.cpp` (2012), les `.m` reçus, et le VBA *avant* sa correction dans le
chat précédent partagent tous la même approche : sauter un nombre fixe de
lignes puis un nombre fixe de « mots », plutôt que de chercher un champ par
son étiquette. Déjà documenté comme fragile pour VBA (`docs/ANOMALIES.md`
de `epicea-libs`, point 5) : le nombre de lignes d'en-tête dépend du
nucléide (présence ou non de `Daughter(s)`, `Q+`, `Q-`, `Possible
parent(s)`), donc un décalage fixe ne peut pas être fiable sur toute la
base (~300 nucléides). Vérifié à l'époque : pour Zr-95, `Decay constant`
est en ligne 8, pas 9 comme le VBA d'origine le supposait.

**Décision** : Python/Matlab/C/VBA de ce dépôt lisent tous par **étiquette**
(chercher la ligne qui commence par `"Decay constant"`, `"Daughter(s)"`,
etc.), comme la version VBA déjà corrigée — pas par position. C'est un
changement de comportement par rapport aux 16 `.m` reçus et à `Lara.cpp`,
signalé ici plutôt qu'appliqué en silence.

## 3. Format LARA reconstitué

### 3.1 Champs d'en-tête — confirmés sur données réelles (Zr-95)

```
Nuclide ; Zr-95
Element ; Zirconium
Z ; 40
Daughter(s) ; (B-) ; Nb-95 ; 100
Q- ; 1124.8
Half-life (d) ; 64.032 ; 0.006
Half-life (s) ; 5.5324E6 ; 0.0005E6
Decay constant (1/s) ; 125.289E-9 ; 0.012E-9
Specific activity (Bq/g) ; 794.22E12 ; 0.07E12
Reference ; INEEL - 1998
Emissions (7 lines) sorted by increasing energy
[... 7 lignes de raies, non capturées à l'époque ...]
```

Un nucléide stable n'a pas de ligne `Decay constant` (utilisé comme test de
stabilité, voir `isStable`/`is_stable`).

**Écart de nommage trouvé** : `massActivity.m` cherche une ligne
`"Mass activity (Bq/g)"`, mais le champ réel s'appelle `"Specific activity
(Bq/g)"`. Sans conséquence dans `massActivity.m` lui-même (il ne teste que
le premier caractère `'S'`, qui matche par coïncidence "Specific"), mais
**le nom en commentaire est faux** — corrigé dans ce portage (`"Specific
activity"` partout, recherche par étiquette complète, plus par 1er
caractère).

### 3.2 Ligne `Daughter(s)` — écart trouvé entre `Lara.cpp` (2012) et le Matlab reçu

- `Lara.cpp::decay()` découpe la ligne par groupes de **4 champs** :
  voie ; nucléide fils ; intensité ; **incertitude de l'intensité**.
- `decayWay.m` (reçu) découpe par groupes de **3 champs** : voie ; fils ;
  intensité — **sans incertitude** (`totalEnergyQ.m` le confirme
  explicitement : *« no uncertainty in the LNHB files for daughters
  proportion »*).

Écart réel entre deux générations de code (2012 vs aujourd'hui), pas une
erreur de transcription d'un seul côté — le format a probablement changé,
ou cette incertitude a été retirée de LaraWeb depuis 2012. **Décision** :
suivre le Matlab reçu (le plus récent, et sa justification est explicite),
3 champs sans incertitude — à confirmer si un échantillon récent avec
plusieurs voies de décroissance est fourni.

### 3.3 Table des émissions (α/β/γ) — non résolu, échantillon nécessaire

`Egamma.m` documente en commentaire l'ordre
`Energy ; Ener. unc. ; Intensity ; Int. unc. ; Type ; Origin ; Lvl. start ;
Lvl. end` (type en position 5). `Lara.cpp::spectre()` suppose au contraire
le type en **première** position (`tmp_gst[0] == type`), puis énergie/
incertitude/intensité/incertitude aux index 2/4/6/8 d'une ligne découpée
par espaces. Les deux ne peuvent pas être justes simultanément avec la
même règle de découpe, et je n'ai pas d'échantillon réel de cette section
précise (la capture Zr-95 du chat précédent s'arrête juste avant, à
`"Emissions (7 lines)..."`). Tant que je n'ai pas une vraie section
d'émissions, `Ealpha`/`Ebetam`/`Ebetap`/`Eec`/`Egamma` sont portées en
suivant le commentaire du Matlab reçu (le plus détaillé des deux, et le
plus récent), **non vérifiées** — signalé clairement dans chaque fonction
et dans `docs/GAPS.md`.

## 4. `bddfile` — chemin de cache et URL

- VBA corrigé (chat précédent) : cache sur lecteur réseau labo
  (`O:\SCA\X-ECHANGES\Macros\Lara\<nuclide>.txt`), URL
  `http://www.lnhb.fr/nuclides/<nuclide>.lara.txt` (vérifiée par requête
  directe).
- `bddfile.m` (reçu) : cache sur **chemin OneDrive personnel**
  (`C:\Users\dougniaux-gre\OneDrive - irsn.fr\...`), URL
  `http://www.lnhb.fr/Laraweb/Results/<nuclide>.lara.txt` — **l'ancienne
  URL, déjà identifiée comme périmée**.
- `Lara.cpp` (2012) : chemin arbitraire fourni à l'exécution
  (`Lara::init(path)`), pas d'accès web du tout (fichiers locaux
  uniquement).

**Décision** : ce dépôt paramètre le chemin du cache local (variable
d'environnement / argument, jamais un chemin personnel codé en dur) et
utilise l'URL vérifiée `/nuclides/`. Cohérent avec le principe déjà
appliqué à `SI` de ne pas figer de chemin propre à une machine dans du
code destiné à être réutilisé.

## 5. Fonctions manquantes, reconstruites — à confirmer

- **`AZN`** (élément → A, Z, N) : **résolue** grâce à `Lara.cpp`, qui
  contient `Lara::A()`/`Lara::Z()`/`Lara::S()` et surtout la table complète
  des 118 éléments (`builtElementTable`). Reprise telle quelle (voir
  `periodic_table.*`).
- **`Pbeta`** (forme du spectre β continu) : absente des fichiers reçus.
  Reconstruite à partir de votre propre description (*« une simplification
  à base de Fermi et autre »*, chat précédent) : spectre de Fermi
  non-relativiste avec facteur de Fermi approché (Wilkinson/Behrens-Jänecke
  simplifié) et correction empirique de forme, PAS confrontée à une
  référence (BetaShape ou table tritium) — **statut expérimental**, à
  vérifier en priorité si vous avez un exemple BetaShape à comparer.
- **`bsfile`** / format BetaShape : aucun échantillon. `Ebetam.m`/`Ebetap.m`
  sautent 15 lignes puis lisent 3 colonnes numériques jusqu'à la fin du
  fichier (`fscanf(fileid(i),'%f %f %f',[3 Inf])`) — c'est tout ce que je
  peux inférer de la structure sans exemple. Porté tel quel (saut de 15
  lignes, 3 colonnes), non testé.

## 6. Compléments (fichiers réels reçus : H-3.lara.txt, beta-_H3_tot.bs, bateman.m)

**URL LARA, précision** : `http://www.lnhb.fr/Laraweb/Results/H-3_@04.lara.txt`
(suffixe `_@04`, sans doute un numéro de révision) est présentée comme la
source de référence complète ; `http://www.lnhb.fr/nuclides/<nuclide>.lara.txt`
(sans suffixe) reste la seule que j'ai personnellement vérifiée par requête
directe (chat précédent, Zr-95/Nb-95/Ag-110/Er-169). N'ayant pas d'accès
réseau vers `lnhb.fr` depuis cet environnement (domaine hors liste
autorisée), je ne peux vérifier ni confirmer le format exact du suffixe
`_@04` (fixe ? dépendant du nucléide ou de la date ?) — `lara_client.py`
garde l'URL simple déjà vérifiée, en gardant `LARA_URL_TEMPLATE` isolée et
documentée pour être ajustée d'un endroit unique si le suffixe s'avère
nécessaire.

**Format BetaShape — confirmé sur données réelles** (`beta-_H3_tot.bs`) :
15 lignes d'en-tête puis 3 colonnes (E keV, dN/dE par keV, incertitude).
Validé par recalcul direct : énergie moyenne recalculée à partir des 312
points = 5.69562 keV, contre 5.69565(32) keV annoncée dans le fichier
lui-même — cohérent. Confirme que le saut de « 15 lignes » d'`Ebetam.m`/
`Ebetap.m`/`bsfile.m` était déjà juste (contrairement à la table
d'émissions LARA, §3.3, toujours sans échantillon).

Convention de nom de fichier observée : `beta-_H3_tot.bs` — remarque : le
tiret du nom de nucléide semble absent (`H3`, pas `H-3`) ; à confirmer si
c'est systématique.

**`Ebetam`/`Ebetap` — clarification de leur rôle réel**, en relisant le
code à la lumière du fichier BetaShape reçu : `data(:,1,end)` ne récupère
que le **dernier point** du fichier (l'énergie de fin de spectre, ex.
18.591 keV pour H-3 — qui coïncide exactement avec `Q- ; 18.591` du
`.lara.txt`). Ces fonctions renvoient donc un point de fin de spectre
(« endpoint »), pas la courbe complète — c'est ce point qui sert
d'argument `endpoint` à `Pbeta`, laquelle recalcule la forme elle-même
(Fermi). `unc_E`/`unc_I` restent déclarées mais jamais renseignées dans
`Ebetam.m`/`Ebetap.m` reçus (incertitude non propagée à ce stade) — repris
tel quel, signalé ici plutôt que « corrigé » silencieusement.

**Bateman — lenteur diagnostiquée et traitée.** La version reçue
(`bateman.m`) est un port fidèle et correct de l'équation de Bateman
classique (chaîne linéaire, formule à triple somme/produit m/k/j) — la
lenteur ne vient pas d'une erreur de formule, mais du fait qu'un seul jeu
(lambdas, ratios, N0) est traité par appel : une propagation Monte-Carlo à
S tirages nécessite donc S appels, chacun ré-exécutant les boucles m/k/j
en scalaire interprété. `python/nuc/bateman.py` et `matlab/bateman.m`
(nouveaux) gardent les boucles sur la **topologie** de la chaîne (petite,
N rarement > 15-20) en Python/Matlab, mais vectorisent chaque terme sur
**tous les tirages et tous les instants à la fois** (formes `(S,N)` /
`(T,)` → sortie `(S,T,N)`) : le nombre d'itérations de boucle ne dépend
plus de S. Mesuré : ×15 sur un cas réaliste (chaîne à 8 nucléides, 20 000
tirages, Python vectorisé vs. boucle Python pure fidèle au .m — la
comparaison face à MATLAB scalaire réel n'a pas pu être mesurée, MATLAB
n'étant pas disponible dans cet environnement, mais l'écart attendu est au
moins comparable). Validé par comparaison exacte (écart relatif nul) avec
un port scalaire fidèle du `.m` reçu, sur plusieurs instants et plusieurs
tirages, dans les deux langages.

**Garde-fou ajouté, absent du `.m` reçu** : deux lambdas quasi égaux dans
un même groupe font exploser `lambda_j - lambda_k` au dénominateur (la
protection existait en commentaire dans `bateman.m` puis avait été
désactivée). Un tirage Monte-Carlo peut produire ce cas par hasard même
si les lambdas nominaux sont bien distincts — la garde ne peut donc pas
être omise ici. Décalage epsilon relatif (1e-10 par défaut) appliqué aux
seules paires concernées ; testé sur un cas quasi dégénéré et un cas
exactement dégénéré (les deux plantent avec la formule brute, les deux
restent finis avec la garde), dans les deux langages, avec un résultat
identique entre Python et Matlab à 6 chiffres significatifs.

**Non repris pour l'instant** : `decayNAtoms`/`decayNAtoms2` elles-mêmes
(portage direct possible maintenant que `wholechain` est reconstituée, voir
§8) ; version C de `bateman` (valeur ajoutée moindre une fois la version
vectorisée numpy/Matlab en place, sauf besoin de très gros volumes).

## 8. `wholechain` — reconstruction (deux défauts trouvés, un plus profond que prévu)

Reçue et analysée. Deux défauts confirmés :

**Lenteur des accès fichier** : `decayWay()` est appelé pour chaque
nucléide de chaque branche, puis chaque nucléide est de nouveau lu dans la
boucle finale (`lambda(...)`) — sans aucun cache, un nucléide partagé par
plusieurs branches (très fréquent : ancêtres communs) est relu autant de
fois qu'il apparaît. Résolu simplement : `nuc.filiation.wholechain` prend
un unique `LaraClient` à réutiliser pour tout l'arbre, qui mémorise déjà
chaque nucléide par lui-même (voir §2) — chaque nucléide n'est effectivement
récupéré qu'une seule fois, quel que soit le nombre de branches qui le
traversent. Vérifié explicitement dans `test_filiation.py` (compte les
appels réseau, pas juste les occurrences dans les branches).

**Comptage `conct` : bug confirmé, plus subtil qu'il n'y paraissait.**
Premier symptôme trouvé en relisant le code : la branche créée pour la 2ᵉ
(3ᵉ, ...) fille d'un embranchement remet tout son `conct` à zéro, y
compris sa toute dernière position — qui est pourtant la fille elle-même,
un nucléide qui n'apparaît dans aucune autre branche. Avec
`decayNAtoms.m`, sa population n'est alors jamais comptabilisée nulle
part.

Une première correction (ne zéroter que le préfixe partagé, pas la
nouvelle fille) semblait suffire mais a échoué au test de bout en bout
(conservation de la masse) sur un cas de **reconvergence** (A se sépare en
B et C, qui redonnent tous les deux D) : la masse totale calculée valait
700 sur 1000 attendus. Cause : un simple ensemble « déjà vu » confond deux
situations différentes — un **préfixe partagé** entre branches sœurs (A
dans les 2 branches : vraie redondance, la même valeur calculée deux fois,
un seul comptage suffit) et un **point de reconvergence en aval** (D
atteint via B *et* via C : deux contributions *différentes*, calculées
avec des rapports de branchement différents, qui doivent s'additionner,
pas se dédupliquer). Corrigé en ne zérotant *que* le préfixe explicitement
partagé au moment précis d'un embranchement, sans état global : tout nœud
nouvellement visité en aval — qu'il s'agisse d'un nucléide jamais vu ou
d'un point de reconvergence — repart avec `conct=1`. Testé sur les deux
cas (embranchement simple, embranchement + reconvergence), avec
vérification de conservation de la masse via `bateman()` de bout en bout.

Ce second défaut n'aurait pas été visible sur un simple examen du code ou
même sur le premier test (embranchement sans reconvergence, qui passait
déjà avec la correction naïve) — seul le test de conservation de la masse
sur un cas de reconvergence l'a révélé. Les chaînes de décroissance
naturelles reconvergent couramment (séries de l'uranium, du thorium) :
un cas à surveiller si `decayNAtoms`/`decayNAtoms2` sont testées sur un
vrai nucléide de ces familles.

Pas encore fait : portage Matlab de `filiation.py` (même logique,
faisable directement) ; portage de `decayNAtoms`/`decayNAtoms2`
elles-mêmes sur cette base.

## 7. Périmètre volontairement laissé de côté

`nuc.stopping_power` (Bethe-Bloch) et le module `Spectrum.bas`/`Autre.bas`
complet ne font pas partie des 16 fichiers transmis pour cette passe — non
traités ici. Une ébauche Python existe dans le travail du chat précédent
(non vérifiée indépendamment à l'époque) ; à reprendre séparément si vous
le souhaitez.
