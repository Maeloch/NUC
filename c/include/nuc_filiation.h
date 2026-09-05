/*
 * nuc_filiation.h — decompose l'arbre de decroissance d'un nucleide en
 * branches lineaires, pretes pour nuc_bateman(). Port C99 de
 * nuc/filiation.py / matlab/filiation.m -- meme correctif de reconvergence
 * (voir docs/RECONCILIATION.md §8 : le prefixe explicitement partage au
 * moment d'un embranchement est remis a zero, mais tout nœud nouvellement
 * visite en aval -- nucleide jamais vu OU point de reconvergence -- repart
 * a conct=1 ; une simple marque "deja vu" globale confondrait les deux et
 * sous-compterait un nucleide atteint par plusieurs chemins distincts,
 * comme verifie sur le cas reel At-218->Bi-214 de la demonstration Rn-222,
 * §11, validee a <0.005% contre l'outil LNHB).
 */
#ifndef NUC_FILIATION_H
#define NUC_FILIATION_H

#include "nuc_lara.h"

#ifdef __cplusplus
extern "C" {
#endif

#define NUC_MAX_CHAIN_LEN   16   /* nucleides par branche (chaines reelles : rarement > 10) */
#define NUC_MAX_BRANCHES    64   /* branches par arbre (embranchements combines) */

typedef struct {
    char   names[NUC_MAX_CHAIN_LEN][NUC_LARA_NAME_LEN];
    double lambdas[NUC_MAX_CHAIN_LEN];
    double ratios[NUC_MAX_CHAIN_LEN];   /* ratios[len-1] inutilise, convention bateman() */
    int    conct[NUC_MAX_CHAIN_LEN];
    int    len;
} nuc_branch;

/* Remplit `branches` (jusqu'à NUC_MAX_BRANCHES) avec la décomposition de
 * l'arbre de décroissance de `father`. Renvoie le nombre de branches
 * trouvées (0 si `father` inconnu/erreur, `NUC_MAX_BRANCHES` atteint =
 * arbre tronqué, à agrandir la constante si besoin). */
int nuc_wholechain(nuc_lara_client *client, const char *father,
                    nuc_branch branches[NUC_MAX_BRANCHES]);

#ifdef __cplusplus
}
#endif
#endif /* NUC_FILIATION_H */
