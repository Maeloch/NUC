function out = bateman(lambdas, ratios, N0, t, epsilon_rel)
% BATEMAN Equation de Bateman (chaine de decroissance lineaire), vectorisee.
%
% Meme principe que nuc/bateman.py (voir ce fichier pour la discussion
% complete) : les boucles sur la TOPOLOGIE de la chaine (indices m,i,k,j --
% petites, N nucleides rarement > 15-20) restent en Matlab, mais chaque
% terme est calcule en une seule operation vectorisee sur TOUS les tirages
% Monte-Carlo (dimension S) et tous les instants demandes (dimension T) a
% la fois. Le nombre d'iterations de boucle ne depend donc plus de S.
%
% lambdas, ratios, N0 : matrices S x N (S tirages -- Monte-Carlo, ou S=1
%   pour un calcul classique -- N nucleides de la chaine, dans l'ordre).
%   Vecteurs 1 x N acceptes (S=1).
% t : scalaire ou vecteur 1 x T.
% epsilon_rel : decalage relatif applique aux paires de lambdas quasi
%   degenerees d'un meme groupe (defaut 1e-10) -- absent de la version
%   scalaire d'origine (bateman.m recu), qui plante par division par (quasi)
%   zero dans ce cas ; voir docs/RECONCILIATION.md paragraphe 6. Un tirage
%   Monte-Carlo peut produire deux lambdas tres proches par hasard meme si
%   les valeurs nominales ne le sont pas : la garde ne peut pas etre omise
%   ici comme dans un usage non Monte-Carlo.
%
% Sortie : S x T x N (N_i(t) pour chaque tirage, instant, nucleide).

    if nargin < 5, epsilon_rel = 1e-10; end

    if isvector(lambdas), lambdas = reshape(lambdas,1,[]); end
    if isvector(ratios),  ratios  = reshape(ratios, 1,[]); end
    if isvector(N0),      N0      = reshape(N0,     1,[]); end
    t = reshape(t,1,[]);  % 1 x T

    [S, N] = size(lambdas);
    T = numel(t);

    out = zeros(S, T, N);

    for i = 1:N
        % terme propre : N_i(0).exp(-lambda_i.t)
        out(:,:,i) = out(:,:,i) + N0(:,i) .* exp(-lambdas(:,i) * t);

        for m = 1:(i-1)
            % Q(m,i) = produit_{q=m}^{i-1} ratio_q . lambda_q  -- (S x 1)
            Q = prod(ratios(:,m:i-1) .* lambdas(:,m:i-1), 2);

            % K(m,i,t) = somme_{k=m}^{i} exp(-lambda_k t) / prod_{j!=k}(lambda_j-lambda_k)
            K = zeros(S, T);
            for k = m:i
                diff = lambdas(:,m:i) - lambdas(:,k);   % S x (i-m+1), colonne (k-m+1) -> 0
                col_k = k - m + 1;
                keep = true(1, size(diff,2));
                keep(col_k) = false;
                diff_others = diff(:, keep);            % S x (i-m)

                % Garde-fou lambdas quasi degeneres (voir en-tete de fonction)
                lk = abs(lambdas(:,k));                 % S x 1
                too_close = abs(diff_others) < epsilon_rel * max(lk, 1e-300);
                sgn = sign(diff_others); sgn(sgn==0) = 1;
                replacement = sgn .* (epsilon_rel .* max(lk, 1e-300));  % broadcast S x 1 -> S x (i-m)
                diff_safe = diff_others;
                diff_safe(too_close) = replacement(too_close);

                denom = prod(diff_safe, 2);             % S x 1
                K = K + exp(-lambdas(:,k) * t) ./ denom;
            end

            out(:,:,i) = out(:,:,i) + N0(:,m) .* Q .* K;
        end
    end
end
