function txt = lara_fetch(client, nuclide)
% LARA_FETCH Texte LARA de `nuclide`, mémoïsé pour la durée de vie de
% `client` (containers.Map est un handle -- la mise à jour du cache est
% visible même si `client` a été passé par valeur, voir lara_client_new.m).
    if isKey(client.cache, nuclide)
        txt = client.cache(nuclide);
        return
    end
    txt = client.fetch_fn(nuclide);
    client.cache(nuclide) = txt;
end
