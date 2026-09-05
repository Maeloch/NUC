function test_filiation()
    addpath(fileparts(mfilename('fullpath')));
    addpath(fullfile(fileparts(mfilename('fullpath')), '..'));

    global n_total n_failed
    n_total = 0; n_failed = 0;

    test_linear();
    test_branching();
    test_reconvergence_mass_conservation();

    printf("\n%d/%d tests passed\n", n_total - n_failed, n_total);
    if n_failed > 0
        error("%d test(s) failed", n_failed);
    end
end

function check(cond, msg)
    global n_total n_failed
    n_total = n_total + 1;
    if ~cond
        n_failed = n_failed + 1;
        printf("FAIL %s\n", msg);
    end
end

function txt = make_lara(nuclide, daughters_str, lam)
% daughters_str: deja formate "way ; d1 ; pct1 ; way2 ; d2 ; pct2" ou ''
    txt = sprintf('Nuclide ; %s\n', nuclide);
    if ~isempty(daughters_str)
        txt = [txt sprintf('Daughter(s) ; %s\n', daughters_str)];
        txt = [txt sprintf('Decay constant (1/s) ; %g ; %g\n', lam, lam*0.01)];
    end
end

function client = client_for(map)
    keys_ = keys(map);
    function txt = fetch(nuclide)
        txt = '';
        for i = 1:length(keys_)
            if ~isempty(strfind(nuclide, keys_{i}))
                txt = map(keys_{i});
                return
            end
        end
    end
    client = lara_client_new(@fetch);
end

function test_linear()
    m = containers.Map();
    m('A') = make_lara('A', 'beta- ; B ; 100', 1e-3);
    m('B') = make_lara('B', 'beta- ; C ; 100', 2e-3);
    m('C') = make_lara('C', '', 0);
    client = client_for(m);

    branches = filiation(client, 'A');
    check(length(branches) == 1, 'chaine lineaire : 1 branche');
    check(isequal(branches(1).names, {'A','B','C'}), 'chaine lineaire : noms');
    check(isequal(branches(1).conct, [1 1 1]), 'chaine lineaire : conct tout a 1');
end

function test_branching()
    m = containers.Map();
    m('A') = make_lara('A', 'beta- ; B ; 60 ; alpha ; C ; 40', 1e-3);
    m('B') = make_lara('B', '', 0);
    m('C') = make_lara('C', '', 0);
    client = client_for(m);

    branches = filiation(client, 'A');
    check(length(branches) == 2, 'embranchement : 2 branches');
    for i = 1:2
        if strcmp(branches(i).names{end}, 'B')
            check(isequal(branches(i).conct, [1 1]), 'embranchement : (A,B) conct=[1,1]');
        else
            check(isequal(branches(i).conct, [0 1]), 'embranchement : (A,C) conct=[0,1]');
        end
    end
end

function test_reconvergence_mass_conservation()
    m = containers.Map();
    m('A') = make_lara('A', 'beta- ; B ; 70 ; beta- ; C ; 30', 1e-3);
    m('B') = make_lara('B', 'beta- ; D ; 100', 5e-4);
    m('C') = make_lara('C', 'beta- ; D ; 100', 8e-4);
    m('D') = make_lara('D', '', 0);
    client = client_for(m);

    branches = filiation(client, 'A');
    check(length(branches) == 2, 'reconvergence : 2 branches (A-B-D, A-C-D)');

    t = 1e6;
    total = 0.0;
    for i = 1:length(branches)
        b = branches(i);
        N0 = zeros(1, length(b.names)); N0(1) = 1000.0;
        result = bateman(b.lambdas, b.ratios, N0, t);
        result = squeeze(result)';
        total = total + sum(result .* b.conct);
    end
    check(abs(total - 1000.0) < 1.0, sprintf('reconvergence : masse conservee (%.4f)', total));
end
