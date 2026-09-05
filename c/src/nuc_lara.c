#define _POSIX_C_SOURCE 200809L  /* strdup, strtok_r (POSIX, pas C99 pur) */
#include "nuc_lara.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>

void nuc_lara_client_init(nuc_lara_client *client, nuc_fetch_fn fetch_fn, double timeout_s) {
    memset(client, 0, sizeof(*client));
    client->fetch_fn = fetch_fn;
    client->timeout_s = timeout_s;
}

void nuc_lara_client_free(nuc_lara_client *client) {
    for (int i = 0; i < client->cache_len; i++) {
        free(client->cache_keys[i]);
        free(client->cache_texts[i]);
    }
    client->cache_len = 0;
}

const char *nuc_lara_fetch(nuc_lara_client *client, const char *nuclide) {
    for (int i = 0; i < client->cache_len; i++) {
        if (strcmp(client->cache_keys[i], nuclide) == 0) return client->cache_texts[i];
    }

    const char *text = client->fetch_fn ? client->fetch_fn(nuclide, client->timeout_s) : NULL;
    if (!text) text = "";

    if (client->cache_len < NUC_LARA_CACHE_MAX) {
        client->cache_keys[client->cache_len] = strdup(nuclide);
        client->cache_texts[client->cache_len] = strdup(text);
        client->cache_len++;
        return client->cache_texts[client->cache_len - 1];
    }
    /* cache plein : pas bloquant, on renvoie le texte sans le memoiser */
    return text;
}

static char *trim(char *s) {
    while (isspace((unsigned char)*s)) s++;
    if (*s == '\0') return s;
    char *end = s + strlen(s) - 1;
    while (end > s && isspace((unsigned char)*end)) *end-- = '\0';
    return s;
}

/* Decoupe `line` sur ';' en copiant des champs nettoyes dans out[][field_len],
 * jusqu'a max_fields. Renvoie le nombre de champs. `line` est modifiee
 * (strtok-like) : appeler sur une COPIE si l'original doit etre preserve. */
static int split_fields(char *line, char out[][64], int max_fields, int field_len) {
    int n = 0;
    char *save = NULL;
    char *tok = strtok_r(line, ";", &save);
    while (tok && n < max_fields) {
        char *t = trim(tok);
        snprintf(out[n], (size_t)field_len, "%s", t);
        n++;
        tok = strtok_r(NULL, ";", &save);
    }
    return n;
}

int nuc_lara_field(const char *text, const char *label, char out[][64], int max_fields, int field_len) {
    char buf[4096];
    size_t label_len = strlen(label);

    char *text_copy = strdup(text);
    char *save_line = NULL;
    char *line = strtok_r(text_copy, "\n", &save_line);

    while (line) {
        /* travaille sur une copie de la ligne pour la decouper sans abimer `line` */
        snprintf(buf, sizeof(buf), "%s", line);
        char fields[32][64];
        int nf = split_fields(buf, fields, 32, 64);
        for (int i = 0; i < nf; i++) {
            int is_match = (strcmp(fields[i], label) == 0) ||
                           (strncmp(fields[i], label, label_len) == 0 && fields[i][label_len] == ' ');
            if (is_match) {
                int out_n = 0;
                for (int j = i; j < nf && out_n < max_fields; j++, out_n++) {
                    snprintf(out[out_n], (size_t)field_len, "%s", fields[j]);
                }
                free(text_copy);
                return out_n;
            }
        }
        line = strtok_r(NULL, "\n", &save_line);
    }
    free(text_copy);
    return 0;
}

int nuc_lara_is_stable(nuc_lara_client *client, const char *nuclide) {
    char out[8][64];
    const char *text = nuc_lara_fetch(client, nuclide);
    return nuc_lara_field(text, "Decay constant", out, 8, 64) == 0;
}

void nuc_lara_decay_constant(nuc_lara_client *client, const char *nuclide, si_value *result) {
    if (nuc_lara_is_stable(client, nuclide)) {
        *result = si_v(0.0, 0.0);
        return;
    }
    char out[8][64];
    const char *text = nuc_lara_fetch(client, nuclide);
    int n = nuc_lara_field(text, "Decay constant", out, 8, 64);
    if (n < 3) { *result = si_v(0.0, 0.0); return; }
    *result = si_v(atof(out[1]), atof(out[2]));
}

int nuc_lara_daughters(nuc_lara_client *client, const char *nuclide, nuc_daughter out[NUC_LARA_MAX_DAUGHTERS]) {
    char fields[32][64];
    const char *text = nuc_lara_fetch(client, nuclide);
    int n = nuc_lara_field(text, "Daughter(s)", fields, 32, 64);
    if (n < 4) return 0;  /* fields[0]="Daughter(s)" + au moins 1 voie (3 champs) */

    int count = 0;
    for (int i = 1; i + 2 < n && count < NUC_LARA_MAX_DAUGHTERS; i += 3, count++) {
        snprintf(out[count].way, NUC_LARA_WAY_LEN, "%s", fields[i]);
        snprintf(out[count].daughter, NUC_LARA_NAME_LEN, "%s", fields[i + 1]);
        out[count].pct = atof(fields[i + 2]);
    }
    return count;
}
