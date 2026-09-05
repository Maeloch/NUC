function rn222_demo()
% RN222_DEMO Meme demonstration que rn222_demo.py, en Matlab : verifie la
% parite entre les deux portages (filiation.m/bateman.m vs filiation.py/
% bateman.py), tous deux valides independamment contre l'outil LNHB
% (docs/RECONCILIATION.md paragraphe 11).
    addpath(fullfile(fileparts(mfilename('fullpath')), '..', '..', 'matlab'));

    m = containers.Map();
    m('Rn-222') = sprintf(['Nuclide ; Rn-222\nDaughter(s) ; alpha ; Po-218 ; 100\n' ...
        'Decay constant (1/s) ; 2.0983E-6 ; 0.0006E-6\n']);
    m('Po-218') = fileread(fullfile(fileparts(mfilename('fullpath')), 'lara_real', 'Po-218.lara.txt'));
    m('At-218') = sprintf(['Nuclide ; At-218\nDaughter(s) ; alpha ; Bi-214 ; 99.9 ; B- ; Rn-218 ; 0.1\n' ...
        'Decay constant (1/s) ; 4.951E-1 ; 0.35E-1\n']);
    m('Pb-214') = fileread(fullfile(fileparts(mfilename('fullpath')), 'lara_real', 'Pb-214.lara.txt'));
    m('Rn-218') = sprintf(['Nuclide ; Rn-218\nDaughter(s) ; alpha ; Po-214 ; 100\n' ...
        'Decay constant (1/s) ; 19.25 ; 1.6\n']);
    m('Bi-214') = fileread(fullfile(fileparts(mfilename('fullpath')), 'lara_real', 'Bi-214.lara.txt'));
    m('Po-214') = fileread(fullfile(fileparts(mfilename('fullpath')), 'lara_real', 'Po-214.lara.txt'));
    m('Tl-210') = sprintf(['Nuclide ; Tl-210\nDaughter(s) ; B- ; Pb-210 ; 100\n' ...
        'Decay constant (1/s) ; 8.887E-3 ; 0.068E-3\n']);
    lam_pb210 = log(2) / (22.23*365.25*86400);
    m('Pb-210') = sprintf('Nuclide ; Pb-210\nDecay constant (1/s) ; %.6e ; 0\n', lam_pb210);

    keys_ = keys(m);
    function txt = fetch(nuclide)
        txt = '';
        for i = 1:length(keys_)
            if ~isempty(strfind(nuclide, keys_{i}))
                txt = m(keys_{i});
                return
            end
        end
    end
    client = lara_client_new(@fetch);

    branches = filiation(client, 'Rn-222');
    fprintf('%d branche(s) de filiation :\n', length(branches));
    for i = 1:length(branches)
        fprintf('  %s\n', strjoin(branches(i).names, ' -> '));
    end

    A0 = 1000.0;
    lam_rn222 = lara_decay_constant(client, 'Rn-222');
    N0_rn222 = A0 / lam_rn222;
    t = 3600.0;

    totals = containers.Map();
    lambdas_by_name = containers.Map();
    for i = 1:length(branches)
        b = branches(i);
        N0 = zeros(1, length(b.names)); N0(1) = N0_rn222;
        result = squeeze(bateman(b.lambdas, b.ratios, N0, t))';
        for j = 1:length(b.names)
            lambdas_by_name(b.names{j}) = b.lambdas(j);
            if b.conct(j)
                if isKey(totals, b.names{j})
                    totals(b.names{j}) = totals(b.names{j}) + result(j);
                else
                    totals(b.names{j}) = result(j);
                end
            end
        end
    end

    fprintf('\nActivités à t=%.0f s (départ : %.0f Bq de Rn-222 pur) :\n', t, A0);
    names_ = keys(totals);
    for i = 1:length(names_)
        n = names_{i};
        activity = totals(n) * lambdas_by_name(n);
        fprintf('  %-8s : %9.5f Bq\n', n, activity);
    end
end
