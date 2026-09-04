/*
 * nuc_periodic_table.h -- table des 118 elements, extraite de Lara.cpp
 * (G. Dougniaux, 2012). Voir docs/RECONCILIATION.md paragraphe 5.
 */
#ifndef NUC_PERIODIC_TABLE_H
#define NUC_PERIODIC_TABLE_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int Z;
    const char *symbol;
    const char *name_fr;  /* UTF-8 */
} nuc_element;

#define NUC_N_ELEMENTS 118
extern const nuc_element NUC_ELEMENTS[NUC_N_ELEMENTS];

/* Numero atomique a partir du symbole (ex. "Zr" -> 40). 0 si inconnu. */
int nuc_z_of_symbol(const char *symbol);

/* Symbole a partir de Z (ex. 40 -> "Zr"). NULL si hors [1,118]. */
const char *nuc_symbol_of_z(int z);

#ifdef __cplusplus
}
#endif
#endif /* NUC_PERIODIC_TABLE_H */
