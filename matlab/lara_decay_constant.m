function [val, unc] = lara_decay_constant(client, nuclide)
% LARA_DECAY_CONSTANT [valeur, incertitude] en s^-1. (0,0) si stable.
    if lara_is_stable(client, nuclide)
        val = 0.0; unc = 0.0;
        return
    end
    f = lara_field(lara_fetch(client, nuclide), 'Decay constant');
    val = str2double(f{2});
    unc = str2double(f{3});
end
