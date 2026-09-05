/*
 * nuc_lara.h — client LARA (LNHB) en C99 : parsing par étiquette (pas par
 * position fixe), cache mémoire par nucléide. Port de nuc/lara_client.py /
 * matlab/lara_client_new.m — voir docs/RECONCILIATION.md §2 pour la
 * discussion de la fragilité des lectures par position (Lara.cpp/2012 et
 * les .m reçus) que ce fichier corrige.
 *
 * Dépend de la bibliothèque C du dépôt SI (si_value) pour représenter les
 * grandeurs avec incertitude (constante de décroissance, etc.) — voir
 * ../../README.md pour le chemin d'inclusion (dépôts frères SI/ et NUC/).
 *
 * Le transport (réseau, cache disque) est injecté via un pointeur de
 * fonction : ce fichier ne fait que le cache mémoire pour la durée de vie
 * du client, comme lara_client.py.
 */
#ifndef NUC_LARA_H
#define NUC_LARA_H

#include "si_value.h"

#ifdef __cplusplus
extern "C" {
#endif

#define NUC_LARA_CACHE_MAX   64    /* nucleides distincts en cache par client */
#define NUC_LARA_MAX_DAUGHTERS 8   /* largement suffisant (schemas reels : 1-3) */
#define NUC_LARA_NAME_LEN     16
#define NUC_LARA_WAY_LEN      16

/* Retourne le texte LARA de `nuclide` (alloué par l'appelant ou statique -
 * peu importe, seul le contenu est copié par nuc_lara_fetch), ou NULL/
 * chaîne vide en cas d'échec. `timeout_s` informatif, géré par l'appelant. */
typedef const char *(*nuc_fetch_fn)(const char *nuclide, double timeout_s);

typedef struct {
    nuc_fetch_fn fetch_fn;
    double timeout_s;
    char  *cache_keys[NUC_LARA_CACHE_MAX];
    char  *cache_texts[NUC_LARA_CACHE_MAX];  /* alloues (strdup), liberes par nuc_lara_client_free */
    int    cache_len;
} nuc_lara_client;

typedef struct {
    char way[NUC_LARA_WAY_LEN];
    char daughter[NUC_LARA_NAME_LEN];
    double pct;
} nuc_daughter;

void nuc_lara_client_init(nuc_lara_client *client, nuc_fetch_fn fetch_fn, double timeout_s);
void nuc_lara_client_free(nuc_lara_client *client);

/* Texte LARA de `nuclide`, mémoïsé (recherché au plus une fois par
 * nucléide pour la durée de vie de `client`). */
const char *nuc_lara_fetch(nuc_lara_client *client, const char *nuclide);

/* Cherche `label` comme un des champs separes par ';' d'une ligne de
 * `text` (pas necessairement en tete de ligne -- Q-/Qalpha peuvent
 * partager la meme ligne, cf. docs/RECONCILIATION.md §9). Copie jusqu'a
 * `max_fields` champs (nettoyes) dans `out[][field_len]`. Renvoie le
 * nombre de champs copies (>=1, `out[0]` = label lui-meme), ou 0 si absent. */
int nuc_lara_field(const char *text, const char *label,
                    char out[][64], int max_fields, int field_len);

int nuc_lara_is_stable(nuc_lara_client *client, const char *nuclide);

/* (valeur, incertitude) en s^-1. (0,0) si stable. */
void nuc_lara_decay_constant(nuc_lara_client *client, const char *nuclide, si_value *out);

/* Remplit `out` (jusqu'à NUC_LARA_MAX_DAUGHTERS) avec les voies de
 * désintégration (3 champs par voie : voie ; fille ; % -- sans
 * incertitude, format LARA actuel, voir docs/RECONCILIATION.md §3.2).
 * Renvoie le nombre de voies trouvées. */
int nuc_lara_daughters(nuc_lara_client *client, const char *nuclide, nuc_daughter out[NUC_LARA_MAX_DAUGHTERS]);

#ifdef __cplusplus
}
#endif
#endif /* NUC_LARA_H */
