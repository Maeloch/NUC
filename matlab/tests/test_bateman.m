function test_bateman()
    addpath(fileparts(mfilename('fullpath')));
    addpath(fullfile(fileparts(mfilename('fullpath')), '..'));

    lambdas = [0.8, 0.5, 0.3, 0.2, 0.1];
    ratios  = [0.7, 1.0, 0.9, 0.5, 1.0];
    N0      = [1000.0, 50.0, 0.0, 0.0, 0.0];

    ok = true;
    for t = [0.01, 0.5, 2.0, 10.0]
        ref = bateman_original(lambdas, ratios, N0, t);
        vec = bateman(lambdas, ratios, N0, t);
        vec = squeeze(vec)';  % S=1,T=1 -> vecteur 1xN comme ref
        err = max(abs(ref - vec) ./ max(abs(ref), 1e-30));
        fprintf('t=%6.2f  ecart max relatif = %.3e\n', t, err);
        ok = ok && (err < 1e-9);
    end

    % Vectorisation multi-tirages (S=3, memes valeurs repetees -> memes resultats)
    lambdas_mc = repmat(lambdas, 3, 1);
    ratios_mc  = repmat(ratios, 3, 1);
    N0_mc      = repmat(N0, 3, 1);
    vec_mc = bateman(lambdas_mc, ratios_mc, N0_mc, 2.0);  % 3 x 1 x 5
    ref2 = bateman_original(lambdas, ratios, N0, 2.0);
    for s = 1:3
        err = max(abs(ref2 - squeeze(vec_mc(s,1,:))') ./ max(abs(ref2),1e-30));
        ok = ok && (err < 1e-9);
    end
    fprintf('Vectorisation multi-tirages (S=3) : ecart max = %.3e\n', err);

    % Cas quasi degenere : ne doit pas planter (contrairement a bateman_original)
    lambdas_deg = [0.5, 0.2, 0.5000000001, 0.9];
    ratios_deg  = [0.6, 1.0, 0.3, 1.0];
    N0_deg      = [1000.0, 0.0, 0.0, 0.0];
    vec_deg = bateman(lambdas_deg, ratios_deg, N0_deg, 2.0);
    fprintf('Cas quasi degenere : fini = %d, valeurs = %s\n', ...
        all(isfinite(vec_deg(:))), mat2str(squeeze(vec_deg)',6));
    ok = ok && all(isfinite(vec_deg(:)));

    if ok
        fprintf('\nTOUS LES TESTS PASSENT\n');
    else
        error('des tests ont echoue');
    end
end
