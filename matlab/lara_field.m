function parts = lara_field(txt, label)
% LARA_FIELD Cherche `label` comme un des champs separes par ';' d'une
% ligne de `txt` (pas necessairement le premier -- ex. "Q- ; 260 ; Qalpha ;
% 6114.68" : Po-218 a Q- ET Qalpha sur la MEME ligne, cf. echantillon reel).
% Renvoie un cell array des champs a partir de ce point, nettoyes ; {} (cell
% vide) si absent (resultat normal, ex. nucleide stable).
    parts = {};
    lines = strsplit(txt, {'\n', '\r\n'});
    for i = 1:length(lines)
        raw = strtrim(strsplit(lines{i}, ';'));
        for j = 1:length(raw)
            p = raw{j};
            if strcmp(p, label) || startsWith(p, [label ' '])
                parts = raw(j:end);
                return
            end
        end
    end
end
