function branches = filiation(client, father)
% FILIATION Decompose l'arbre de decroissance de `father` en branches
% lineaires, pretes pour bateman(). Port Matlab de nuc/filiation.py --
% meme logique, meme correctif de reconvergence (voir docs/RECONCILIATION.md
% paragraphe 8) : le prefixe explicitement partage au moment d'un
% embranchement est remis a zero (evite un double comptage), mais tout
% nœud nouvellement visite en aval repart a conct=1, qu'il s'agisse d'un
% nucleide jamais vu ou d'un point de reconvergence -- une simple marque
% "deja vu" globale confondrait les deux et sous-compterait un nucleide
% atteint par plusieurs chemins distincts (voir le cas reel At-218->Bi-214
% dans la demonstration Rn-222, valide a <0.005% contre l'outil LNHB).
%
% branches : struct array avec les champs names (cell array), lambdas
% (vecteur), ratios (vecteur, dernier element inutilise par bateman()),
% conct (vecteur 0/1).

    branches = struct('names', {}, 'lambdas', {}, 'ratios', {}, 'conct', {});
    branches = visit_(client, {}, [], [], [], father, 1, branches);
end

function branches = visit_(client, prefix_names, prefix_lambdas, prefix_ratios, prefix_conct, nuclide, own_conct, branches)
    names = [prefix_names, {nuclide}];
    lam = lara_decay_constant(client, nuclide);
    lambdas = [prefix_lambdas, lam];
    conct = [prefix_conct, own_conct];

    daughters = lara_daughters(client, nuclide);

    if isempty(daughters)
        b.names = names;
        b.lambdas = lambdas;
        b.ratios = [prefix_ratios, 0.0];  % dernier maillon : inutilise par bateman()
        b.conct = conct;
        branches(end+1) = b;
        return
    end

    for idx = 1:length(daughters)
        d = daughters{idx};
        ratios_next = [prefix_ratios, d.pct / 100.0];
        if idx == 1
            branches = visit_(client, names, lambdas, ratios_next, conct, d.daughter, 1, branches);
        else
            % 2e fille et suivantes : ce prefixe (jusqu'a `nuclide` inclus)
            % est deja compte par la branche de la 1ere fille -> remis a
            % zero ICI seulement ; `d.daughter` repart a conct=1.
            branches = visit_(client, names, lambdas, ratios_next, zeros(size(conct)), d.daughter, 1, branches);
        end
    end
end
