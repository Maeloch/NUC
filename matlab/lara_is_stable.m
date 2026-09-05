function s = lara_is_stable(client, nuclide)
% LARA_IS_STABLE Vrai si le champ "Decay constant" est absent.
    txt = lara_fetch(client, nuclide);
    s = isempty(lara_field(txt, 'Decay constant'));
end
