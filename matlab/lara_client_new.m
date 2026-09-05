function client = lara_client_new(fetch_fn, varargin)
% LARA_CLIENT_NEW Cree un "client" LARA : cache memoire par nucleide +
% fonction de recuperation injectable (meme principe que lara_client.py,
% voir docs/RECONCILIATION.md paragraphe 2 -- lecture par etiquette, pas
% par position fixe, et memoisation pour ne recuperer chaque nucleide
% qu'une seule fois quel que soit le nombre de branches qui le traversent).
%
% fetch_fn : function handle @(nuclide) -> texte (chaine vide si echec).
%            L'appelant gere lui-meme le reseau/cache disque a l'interieur
%            de cette fonction ; lara_client_new ne fait QUE le cache
%            memoire pour la duree de vie de `client`.
%
% Usage :
%   client = lara_client_new(@(n) my_fetch_function(n));
%   txt = lara_fetch(client, 'Rn-222');
%   [val, unc] = lara_decay_constant(client, 'Rn-222');

    client.fetch_fn = fetch_fn;
    client.cache = containers.Map('KeyType', 'char', 'ValueType', 'any');
end
