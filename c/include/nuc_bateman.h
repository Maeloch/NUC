/*
 * nuc_bateman.h — equation de Bateman (chaine de decroissance lineaire),
 * C99. Port de bateman.m / nuc/bateman.py : meme garde-fou pour les
 * lambdas quasi degeneres (absent du bateman.m recu -- desactive en
 * commentaire, voir docs/RECONCILIATION.md §6).
 *
 * Contrairement aux versions Python/Matlab (vectorisees sur les tirages
 * Monte-Carlo ET le temps, pour compenser la lenteur des boucles
 * interpretees), cette version C ne vectorise que sur le temps : en C,
 * une boucle sur les tirages Monte-Carlo est deja rapide (code compile),
 * la vectorisation "tirages" qui etait le point cle en Python/Matlab n'a
 * pas la meme urgence ici -- appeler nuc_bateman() dans une boucle C pour
 * chaque tirage reste largement suffisant.
 */
#ifndef NUC_BATEMAN_H
#define NUC_BATEMAN_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * lambdas, ratios, N0 : tableaux de taille `n` (chaine lineaire de `n`
 * nucleides, dans l'ordre ; ratios[n-1] inutilise).
 * t : tableau de `n_t` instants.
 * out : tableau de sortie, taille `n_t * n` (rempli en ordre
 * [temps][nucleide], i.e. out[it*n + i] = N_i(t[it])).
 * epsilon_rel : decalage relatif pour les lambdas quasi degeneres d'un
 * meme groupe (0 -> valeur par defaut 1e-10).
 */
void nuc_bateman(const double *lambdas, const double *ratios, const double *N0,
                  int n, const double *t, int n_t, double epsilon_rel,
                  double *out);

#ifdef __cplusplus
}
#endif
#endif /* NUC_BATEMAN_H */
