"""
nuc.bateman — équation de Bateman (chaîne de décroissance linéaire),
version vectorisée numpy.

Port de bateman.m, réorganisé pour l'usage Monte-Carlo que vous décrivez :
la version .m ne traite qu'UN jeu de lambdas/ratios/N0 à la fois — pour une
propagation d'incertitude Monte-Carlo (S tirages), il faut donc l'appeler S
fois depuis une boucle, chaque appel refaisant les boucles m/k/j en MATLAB
scalaire. C'est très probablement l'essentiel de la lenteur observée (le
compte d'opérations est modeste — une chaîne de 10 nucléides, c'est au pire
quelques centaines d'itérations m/k/j — mais un scalaire MATLAB/Python
interprété par tirage, répété S fois, s'additionne vite).

Ici, les boucles sur la TOPOLOGIE de la chaîne (m, i, k, j — petites, N
nucléides rarement > 15-20) restent en Python, mais chaque terme est
calculé en UNE opération numpy vectorisée sur TOUS les tirages Monte-Carlo
ET tous les instants demandés à la fois (formes (S,) et (T,), diffusées en
(S,T)). Le nombre d'itérations Python ne dépend donc plus de S : passer de
1 à 100 000 tirages ne coûte quasiment rien de plus en overhead d'appels.

Garde-fou ajouté (absent du .m reçu — la protection y était écrite en
commentaire puis désactivée, cf. docs/RECONCILIATION.md §6) : quand deux
lambdas d'un même groupe (m..i) sont quasi égaux, `lambda_j - lambda_k` au
dénominateur explose. Un tirage Monte-Carlo peut, par hasard, produire deux
valeurs très proches même si les lambdas nominaux ne le sont pas — on ne
peut donc pas se permettre d'ignorer le cas comme le ferait un code non
Monte-Carlo. Résolu par un décalage `epsilon` relatif minuscule (défaut
1e-10 relatif) appliqué aux paires quasi dégénérées, qui n'affecte pas le
résultat physique de façon mesurable mais évite le NaN/Inf.
"""
from __future__ import annotations
import numpy as np


def bateman_with_uncertainty(
    lambdas: np.ndarray,
    u_lambdas: np.ndarray,
    ratios: np.ndarray,
    u_ratios: np.ndarray,
    N0: np.ndarray,
    t,
    h_rel: float = 1e-6,
    **kwargs,
) -> tuple[np.ndarray, np.ndarray]:
    """
    (valeur, incertitude-type) par propagation **linéarisée correcte**
    (GUM : matrice jacobienne par différences finies centrées par rapport
    aux `lambdas`/`ratios` INDÉPENDANTS, combinaison quadratique en
    supposant ces entrées indépendantes entre elles).

    Pourquoi pas simplement des `Value`/`si_value` partout dans `bateman`
    (votre question) : la formule de Bateman réutilise le MÊME lambda_k
    plusieurs fois dans la même expression (le terme `exp(-lambda_k.t)`
    ET plusieurs dénominateurs `lambda_j - lambda_k` pour différents j) —
    une propagation `Value` "naïve" (nœud par nœud dans l'arbre de calcul)
    traite chaque occurrence comme une variable indépendante et se trompe
    dès qu'une valeur se répète. Exemple minimal et sans appel à
    `bateman` : avec la classe `Value` du dépôt `SI`,
    `Value(5.0, 0.3) - Value(5.0, 0.3)` donne `0 ± 0.424`, alors que la
    bonne réponse est `0 ± 0` (x−x vaut exactement 0, quelle que soit la
    valeur de x — aucune incertitude réelle ne subsiste). La fonction
    présente ici évite ce piège en dérivant par rapport à chaque lambda
    *une fois*, quel que soit le nombre de fois qu'il apparaît dans la
    formule.

    Validé par comparaison à un tirage Monte-Carlo (200 000 échantillons) :
    écart < 1 % (résidu de linéarisation, cohérent avec une formule non
    linéaire — voir `tests/test_bateman.py`). Toujours moins riche qu'un
    Monte-Carlo complet (suppose les entrées indépendantes, linéarise
    autour du point central) mais correct pour de petites incertitudes,
    et beaucoup moins coûteux qu'un grand ensemble Monte-Carlo si c'est
    tout ce dont vous avez besoin (ex. une estimation rapide, un
    contrôle de cohérence).

    lambdas/u_lambdas/ratios/u_ratios/N0 : tableaux (N,) — un seul jeu
    (pas de dimension d'échantillons : ceci EST l'alternative au
    Monte-Carlo, pas un outil à batcher par-dessus). `**kwargs` transmis
    à `bateman` (ex. `epsilon_rel`).
    """
    lambdas = np.asarray(lambdas, dtype=float)
    ratios = np.asarray(ratios, dtype=float)
    N0 = np.asarray(N0, dtype=float)
    n = len(lambdas)

    central = bateman(lambdas, ratios, N0, t, **kwargs)
    out_shape = central.shape

    variance = np.zeros(out_shape)
    for arr, u_arr, is_lambda in ((lambdas, u_lambdas, True), (ratios, u_ratios, False)):
        for k in range(n):
            if u_arr[k] == 0:
                continue
            h = max(h_rel * abs(arr[k]), h_rel)
            arr_plus = arr.copy(); arr_plus[k] += h
            arr_minus = arr.copy(); arr_minus[k] -= h
            if is_lambda:
                plus = bateman(arr_plus, ratios, N0, t, **kwargs)
                minus = bateman(arr_minus, ratios, N0, t, **kwargs)
            else:
                plus = bateman(lambdas, arr_plus, N0, t, **kwargs)
                minus = bateman(lambdas, arr_minus, N0, t, **kwargs)
            dOut_dArrK = (plus - minus) / (2 * h)
            variance += (dOut_dArrK * u_arr[k]) ** 2

    return central, np.sqrt(variance)


def bateman(
    lambdas: np.ndarray,
    ratios: np.ndarray,
    N0: np.ndarray,
    t,
    epsilon_rel: float = 1e-10,
) -> np.ndarray:
    """
    Résout la chaîne linéaire grand-père -> père -> ... -> arrière-petit-fils.

    lambdas, ratios, N0 : tableaux de forme (S, N) — S tirages (Monte-Carlo
        ou S=1 pour un calcul classique), N nucléides de la chaîne, dans
        l'ordre (ratios[:, i] = fraction des désintégrations de i qui
        produit i+1 ; ratios[:, N-1] n'est jamais utilisé, comme dans
        bateman.m). Les tableaux 1D (N,) sont acceptés (repris comme S=1).
    t : scalaire ou tableau (T,) — instant(s) d'évaluation.
    epsilon_rel : décalage relatif appliqué aux paires (lambda_j, lambda_k)
        quasi dégénérées d'un même groupe, pour éviter la division par ~0.

    Retourne un tableau (S, T, N) : N_i(t) pour chaque tirage, instant,
    nucléide de la chaîne. Si `t` est un scalaire, la dimension T est
    retirée (S, N) ; si en plus S==1 à l'entrée (tableaux 1D), (N,) ou (T,N).
    """
    lambdas = np.atleast_2d(np.asarray(lambdas, dtype=float))
    ratios = np.atleast_2d(np.asarray(ratios, dtype=float))
    N0 = np.atleast_2d(np.asarray(N0, dtype=float))
    t_arr = np.atleast_1d(np.asarray(t, dtype=float))  # (T,)

    S, N = lambdas.shape
    T = t_arr.shape[0]

    out = np.zeros((S, T, N))

    for i in range(N):
        # terme "propre" : N_i(0).exp(-lambda_i.t)
        out[:, :, i] += N0[:, i:i + 1] * np.exp(-lambdas[:, i:i + 1] * t_arr[None, :])

        for m in range(i):
            # Q(m,i) = produit_{q=m}^{i-1} ratio_q . lambda_q  -- (S,)
            Q = np.prod(ratios[:, m:i] * lambdas[:, m:i], axis=1)

            # K(m,i,t) = somme_{k=m}^{i} exp(-lambda_k t) / prod_{j!=k}(lambda_j-lambda_k)  -- (S,T)
            K = np.zeros((S, T))
            for k in range(m, i + 1):
                diff = lambdas[:, m:i + 1] - lambdas[:, k:k + 1]  # (S, i-m+1), colonne k -> 0
                # Neutralise la colonne k elle-meme (j==k exclu du produit)
                col_k = k - m
                mask = np.ones(diff.shape[1], dtype=bool)
                mask[col_k] = False
                diff_others = diff[:, mask]  # (S, i-m)

                # Garde-fou lambdas quasi degeneres (cf. docstring) : ecarte
                # les paires trop proches de zero d'un epsilon relatif,
                # signe préservé (ou +epsilon si la difference est nulle).
                too_close = np.abs(diff_others) < epsilon_rel * np.maximum(
                    np.abs(lambdas[:, k:k + 1]), 1e-300)
                sign = np.where(diff_others >= 0, 1.0, -1.0)
                diff_others = np.where(
                    too_close,
                    sign * epsilon_rel * np.maximum(np.abs(lambdas[:, k:k + 1]), 1e-300),
                    diff_others,
                )

                denom = np.prod(diff_others, axis=1)  # (S,)
                K += (np.exp(-lambdas[:, k:k + 1] * t_arr[None, :]) / denom[:, None])

            out[:, :, i] += N0[:, m:m + 1] * Q[:, None] * K

    # Simplifie la forme de sortie si S==1 et/ou t scalaire (confort d'usage)
    scalar_t = np.ndim(t) == 0
    if scalar_t:
        out = out[:, 0, :]  # (S, N)
    if out.shape[0] == 1:
        out = out[0]  # (N,) ou (T,N)
    return out
