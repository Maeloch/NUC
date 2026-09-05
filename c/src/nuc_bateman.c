#include "nuc_bateman.h"
#include <math.h>
#include <stdlib.h>

void nuc_bateman(const double *lambdas, const double *ratios, const double *N0,
                  int n, const double *t, int n_t, double epsilon_rel,
                  double *out) {
    if (epsilon_rel <= 0.0) epsilon_rel = 1e-10;

    for (int idx = 0; idx < n_t * n; idx++) out[idx] = 0.0;

    double *K = (double *)malloc(sizeof(double) * (size_t)n_t);

    for (int i = 0; i < n; i++) {
        for (int it = 0; it < n_t; it++) {
            out[it * n + i] += N0[i] * exp(-lambdas[i] * t[it]);
        }

        for (int m = 0; m < i; m++) {
            double Q = 1.0;
            for (int q = m; q < i; q++) Q *= ratios[q] * lambdas[q];

            for (int it = 0; it < n_t; it++) K[it] = 0.0;

            for (int k = m; k <= i; k++) {
                double denom = 1.0;
                for (int j = m; j <= i; j++) {
                    if (j == k) continue;
                    double diff = lambdas[j] - lambdas[k];
                    double lk = fabs(lambdas[k]);
                    double floor_ = epsilon_rel * (lk > 1e-300 ? lk : 1e-300);
                    if (fabs(diff) < floor_) {
                        diff = (diff >= 0 ? 1.0 : -1.0) * floor_;
                    }
                    denom *= diff;
                }
                for (int it = 0; it < n_t; it++) {
                    K[it] += exp(-lambdas[k] * t[it]) / denom;
                }
            }

            for (int it = 0; it < n_t; it++) {
                out[it * n + i] += N0[m] * Q * K[it];
            }
        }
    }

    free(K);
}
