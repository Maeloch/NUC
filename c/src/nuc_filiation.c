#include "nuc_filiation.h"
#include <string.h>
#include <stdio.h>

typedef struct {
    nuc_lara_client *client;
    nuc_branch *branches;
    int count;
} visit_ctx;

static void visit(visit_ctx *ctx,
                   char prefix_names[NUC_MAX_CHAIN_LEN][NUC_LARA_NAME_LEN],
                   double prefix_lambdas[NUC_MAX_CHAIN_LEN],
                   double prefix_ratios[NUC_MAX_CHAIN_LEN],
                   int prefix_conct[NUC_MAX_CHAIN_LEN],
                   int prefix_len,
                   const char *nuclide, int own_conct) {
    if (prefix_len >= NUC_MAX_CHAIN_LEN || ctx->count >= NUC_MAX_BRANCHES) return;

    char names[NUC_MAX_CHAIN_LEN][NUC_LARA_NAME_LEN];
    double lambdas[NUC_MAX_CHAIN_LEN];
    double ratios[NUC_MAX_CHAIN_LEN];
    int conct[NUC_MAX_CHAIN_LEN];
    memcpy(names, prefix_names, sizeof(names));
    memcpy(lambdas, prefix_lambdas, sizeof(lambdas));
    memcpy(ratios, prefix_ratios, sizeof(ratios));
    memcpy(conct, prefix_conct, sizeof(conct));

    int len = prefix_len;
    snprintf(names[len], NUC_LARA_NAME_LEN, "%s", nuclide);
    si_value lam;
    nuc_lara_decay_constant(ctx->client, nuclide, &lam);
    lambdas[len] = lam.n;
    conct[len] = own_conct;
    len++;

    nuc_daughter daughters[NUC_LARA_MAX_DAUGHTERS];
    int nd = nuc_lara_daughters(ctx->client, nuclide, daughters);

    if (nd == 0) {
        nuc_branch *b = &ctx->branches[ctx->count];
        memcpy(b->names, names, sizeof(names));
        memcpy(b->lambdas, lambdas, sizeof(double) * len);
        memcpy(b->ratios, ratios, sizeof(double) * (len - 1));
        b->ratios[len - 1] = 0.0;  /* dernier maillon : inutilise par bateman() */
        memcpy(b->conct, conct, sizeof(int) * len);
        b->len = len;
        ctx->count++;
        return;
    }

    for (int idx = 0; idx < nd; idx++) {
        double next_ratios[NUC_MAX_CHAIN_LEN];
        memcpy(next_ratios, ratios, sizeof(next_ratios));
        next_ratios[len - 1] = daughters[idx].pct / 100.0;

        if (idx == 0) {
            visit(ctx, names, lambdas, next_ratios, conct, len, daughters[idx].daughter, 1);
        } else {
            /* 2e fille et suivantes : prefixe (jusqu'a `nuclide` inclus)
             * deja compte par la branche de la 1ere fille -> remis a zero
             * ICI seulement ; `daughters[idx].daughter` repart a conct=1. */
            int zeroed_conct[NUC_MAX_CHAIN_LEN] = {0};
            visit(ctx, names, lambdas, next_ratios, zeroed_conct, len, daughters[idx].daughter, 1);
        }
    }
}

int nuc_wholechain(nuc_lara_client *client, const char *father, nuc_branch branches[NUC_MAX_BRANCHES]) {
    visit_ctx ctx = {client, branches, 0};
    char names[NUC_MAX_CHAIN_LEN][NUC_LARA_NAME_LEN] = {{0}};
    double lambdas[NUC_MAX_CHAIN_LEN] = {0};
    double ratios[NUC_MAX_CHAIN_LEN] = {0};
    int conct[NUC_MAX_CHAIN_LEN] = {0};
    visit(&ctx, names, lambdas, ratios, conct, 0, father, 1);
    return ctx.count;
}
