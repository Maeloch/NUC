function d = lara_daughters(client, nuclide)
% LARA_DAUGHTERS Cell array de struct(way, daughter, pct) -- 3 champs par
% voie (voie ; fille ; %), sans incertitude sur l'intensite, conforme au
% format LARA actuel (voir docs/RECONCILIATION.md paragraphe 3.2 : diverge
% de Lara.cpp/2012, qui attendait un 4e champ).
    d = {};
    f = lara_field(lara_fetch(client, nuclide), 'Daughter(s)');
    if isempty(f)
        return
    end
    rest = f(2:end);  % apres l'etiquette "Daughter(s)"
    i = 1;
    while i + 2 <= length(rest)
        d{end+1} = struct('way', rest{i}, 'daughter', rest{i+1}, ...
                           'pct', str2double(rest{i+2}));
        i = i + 3;
    end
end
