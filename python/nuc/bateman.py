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
