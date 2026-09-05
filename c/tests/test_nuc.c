#include "../include/nuc.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

static int failed = 0;
static int total = 0;

#define CHECK(cond, msg) do { \
    total++; \
    if (!(cond)) { failed++; printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, msg); } \
} while (0)

#define CLOSE(a, b, tol) (fabs((a) - (b)) <= (tol) * (fabs(b) > 1 ? fabs(b) : 1))

/* ------------------------------------------------------------------
 * Donnees synthetiques pour les tests de filiation (embranchement +
 * reconvergence), memes cas que test_filiation.py / test_filiation.m.
 * ------------------------------------------------------------------ */
static const char *test_fetch(const char *nuclide, double timeout_s) {
    (void)timeout_s;
    if (strcmp(nuclide, "A") == 0)
        return "Nuclide ; A\nDaughter(s) ; beta- ; B ; 70 ; beta- ; C ; 30\nDecay constant (1/s) ; 1e-3 ; 1e-5\n";
    if (strcmp(nuclide, "B") == 0)
        return "Nuclide ; B\nDaughter(s) ; beta- ; D ; 100\nDecay constant (1/s) ; 5e-4 ; 5e-6\n";
    if (strcmp(nuclide, "C") == 0)
        return "Nuclide ; C\nDaughter(s) ; beta- ; D ; 100\nDecay constant (1/s) ; 8e-4 ; 8e-6\n";
    if (strcmp(nuclide, "D") == 0)
        return "Nuclide ; D\n";
    return "";
}

static void test_filiation_reconvergence_mass_conservation(void) {
    nuc_lara_client client;
    nuc_lara_client_init(&client, test_fetch, 5.0);

    nuc_branch branches[NUC_MAX_BRANCHES];
    int nb = nuc_wholechain(&client, "A", branches);
    CHECK(nb == 2, "2 branches (A-B-D, A-C-D)");

    double t = 1e6;
    double total_mass = 0.0;
    for (int b = 0; b < nb; b++) {
        double N0[NUC_MAX_CHAIN_LEN] = {0};
        N0[0] = 1000.0;
        double out[NUC_MAX_CHAIN_LEN];
        nuc_bateman(branches[b].lambdas, branches[b].ratios, N0, branches[b].len, &t, 1, 0.0, out);
        for (int i = 0; i < branches[b].len; i++) {
            if (branches[b].conct[i]) total_mass += out[i];
        }
    }
    CHECK(CLOSE(total_mass, 1000.0, 1e-3), "masse conservee (reconvergence)");

    nuc_lara_client_free(&client);
}

static void test_bateman_matches_matlab_python_reference(void) {
    /* Chaine lineaire simple, meme valeurs que test_bateman.py/m, plusieurs instants */
    double lambdas[5] = {0.8, 0.5, 0.3, 0.2, 0.1};
    double ratios[5]  = {0.7, 1.0, 0.9, 0.5, 1.0};
    double N0[5]      = {1000.0, 50.0, 0.0, 0.0, 0.0};
    double ts[4] = {0.01, 0.5, 2.0, 10.0};
    double out[4 * 5];

    nuc_bateman(lambdas, ratios, N0, 5, ts, 4, 0.0, out);

    /* Valeurs de reference recalculees fraichement depuis le port scalaire
     * fidele de bateman.m (nuc/tests/test_bateman.py::_bateman_reference),
     * PAS retapees de memoire -- une premiere version de ce test utilisait
     * par erreur des valeurs d'un tout autre jeu (lambdas) explore plus tot
     * dans la session, qui ne correspondait pas a ces lambdas/N0 precis. */
    double ref_t2[5] = {201.8965179946554, 328.2287619885743, 219.39188021855597,
                         48.813322591464726, 2.928227911210692};
    for (int i = 0; i < 5; i++) {
        char msg[64]; snprintf(msg, sizeof(msg), "bateman t=2.0 nuclide %d", i);
        CHECK(CLOSE(out[2 * 5 + i], ref_t2[i], 1e-5), msg);
    }
}

/* ------------------------------------------------------------------
 * Chaine reelle Rn-222 : memes donnees que rn222_demo.py/.m, comparees a
 * la meme reference LNHB (docs/RECONCILIATION.md §11), deja validee a
 * <0.005% en Python et Matlab -- ce test verifie la parite du port C.
 * ------------------------------------------------------------------ */
static const char *rn222_fetch(const char *nuclide, double timeout_s) {
    (void)timeout_s;
    if (strstr(nuclide, "Rn-222"))
        return "Nuclide ; Rn-222\nDaughter(s) ; alpha ; Po-218 ; 100\nDecay constant (1/s) ; 2.0983E-6 ; 0.0006E-6\n";
    if (strstr(nuclide, "Po-218"))
        return "Nuclide ; Po-218\nDaughter(s) ; B- ; At-218 ; 0.022 ; alpha ; Pb-214 ; 99.978\nDecay constant (1/s) ; 3.762E-3 ; 0.027E-3\n";
    if (strstr(nuclide, "At-218"))
        return "Nuclide ; At-218\nDaughter(s) ; alpha ; Bi-214 ; 99.9 ; B- ; Rn-218 ; 0.1\nDecay constant (1/s) ; 4.951E-1 ; 0.35E-1\n";
    if (strstr(nuclide, "Pb-214"))
        return "Nuclide ; Pb-214\nDaughter(s) ; B- ; Bi-214 ; 100\nDecay constant (1/s) ; 429.2E-6 ; 0.7E-6\n";
    if (strstr(nuclide, "Rn-218"))
        return "Nuclide ; Rn-218\nDaughter(s) ; alpha ; Po-214 ; 100\nDecay constant (1/s) ; 19.25 ; 1.6\n";
    if (strstr(nuclide, "Bi-214"))
        return "Nuclide ; Bi-214\nDaughter(s) ; B- ; Po-214 ; 99.979 ; alpha ; Tl-210 ; 0.021\nDecay constant (1/s) ; 583.5E-6 ; 2.9E-6\n";
    if (strstr(nuclide, "Po-214"))
        return "Nuclide ; Po-214\nDaughter(s) ; alpha ; Pb-210 ; 100\nDecay constant (1/s) ; 4.271E3 ; 0.032E3\n";
    if (strstr(nuclide, "Tl-210"))
        return "Nuclide ; Tl-210\nDaughter(s) ; B- ; Pb-210 ; 100\nDecay constant (1/s) ; 8.887E-3 ; 0.068E-3\n";
    if (strstr(nuclide, "Pb-210"))
        return "Nuclide ; Pb-210\nDecay constant (1/s) ; 9.8865E-10 ; 0\n";  /* T1/2=22.23a */
    return "";
}

static double find_lambda(nuc_branch *branches, int nb, const char *name) {
    for (int b = 0; b < nb; b++)
        for (int i = 0; i < branches[b].len; i++)
            if (strcmp(branches[b].names[i], name) == 0) return branches[b].lambdas[i];
    return 0.0;
}

static void test_rn222_chain_matches_lnhb_reference(void) {
    nuc_lara_client client;
    nuc_lara_client_init(&client, rn222_fetch, 5.0);

    nuc_branch branches[NUC_MAX_BRANCHES];
    int nb = nuc_wholechain(&client, "Rn-222", branches);
    CHECK(nb == 5, "5 branches (comme Python/Matlab)");

    si_value lam_rn222;
    nuc_lara_decay_constant(&client, "Rn-222", &lam_rn222);
    double A0 = 1000.0;
    double N0_rn222 = A0 / lam_rn222.n;
    double t = 3600.0;

    /* accumulateurs par nom (recherche lineaire, chaine courte) */
    char names[16][NUC_LARA_NAME_LEN];
    double totals[16] = {0};
    int n_names = 0;

    for (int b = 0; b < nb; b++) {
        double N0[NUC_MAX_CHAIN_LEN] = {0};
        N0[0] = N0_rn222;
        double out[NUC_MAX_CHAIN_LEN];
        nuc_bateman(branches[b].lambdas, branches[b].ratios, N0, branches[b].len, &t, 1, 0.0, out);

        for (int i = 0; i < branches[b].len; i++) {
            if (!branches[b].conct[i]) continue;
            int found = -1;
            for (int k = 0; k < n_names; k++) {
                if (strcmp(names[k], branches[b].names[i]) == 0) { found = k; break; }
            }
            if (found < 0) {
                found = n_names++;
                snprintf(names[found], NUC_LARA_NAME_LEN, "%s", branches[b].names[i]);
            }
            totals[found] += out[i];
        }
    }

    /* Reference LNHB (docs/RECONCILIATION.md §11) */
    struct { const char *name; double ref_bq; } refs[] = {
        {"Rn-222", 992.47}, {"Po-218", 993.03}, {"At-218", 0.21847},
        {"Pb-214", 755.81}, {"Rn-218", 0.00021847}, {"Bi-214", 491.03},
        {"Po-214", 490.93}, {"Tl-210", 0.099384}, {"Pb-210", 0.00071132},
    };
    for (size_t r = 0; r < sizeof(refs) / sizeof(refs[0]); r++) {
        double lam = find_lambda(branches, nb, refs[r].name);
        double n_atoms = 0.0;
        for (int k = 0; k < n_names; k++) {
            if (strcmp(names[k], refs[r].name) == 0) { n_atoms = totals[k]; break; }
        }
        double activity = n_atoms * lam;
        char msg[128];
        snprintf(msg, sizeof(msg), "%s : %.5f Bq (ref %.5f)", refs[r].name, activity, refs[r].ref_bq);
        CHECK(CLOSE(activity, refs[r].ref_bq, 5e-4), msg);  /* meme tolerance que Python/Matlab (<0.05%) */
        printf("  %-8s %10.5f Bq   (ref LNHB : %.5f)\n", refs[r].name, activity, refs[r].ref_bq);
    }

    nuc_lara_client_free(&client);
}

int main(void) {
    test_filiation_reconvergence_mass_conservation();
    test_bateman_matches_matlab_python_reference();
    printf("\n--- Chaine Rn-222 vs reference LNHB ---\n");
    test_rn222_chain_matches_lnhb_reference();

    printf("\n%d/%d tests passed\n", total - failed, total);
    return failed ? 1 : 0;
}
