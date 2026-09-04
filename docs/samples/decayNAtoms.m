function [atoms,v_time] = decayNAtoms(father,time,steps,natom0)
% 
% if iscell(father)
%     filiation = father;
% else
    filiation = wholechain(father);
% end


temps = time;
n_points = steps;
natom_0 = natom0;

lambdas = zeros(length(filiation),length(filiation(1).names));
ratios = zeros(length(filiation),length(filiation(1).names));
natoms = zeros(length(filiation),length(filiation(1).names));
results = zeros(length(filiation),length(filiation(1).names));

cchain = chain(father);
atoms  = zeros(n_points+1,length(cchain));

v_time = 0:temps/n_points:temps;


try
    
    % Création de la structure résultat
    for i=1:length(filiation)
        for j=1:length(filiation(i).names)

            lambdas(i,j)  = filiation(i).lambdas(j);
            ratios (i,j)  = filiation(i).intes(j);

            natoms (i,j)  = 0;
            results(i,j)  = 0;
        end
        natoms(i,1)  = natom_0;
    end

    for t=1:length(v_time)

        % Boucle sur bateman avec les chaines partielles
        for i=1:length(filiation)

            results(i,:) = bateman(lambdas(i,:),ratios(i,:),natoms(i,:),v_time(t));

        end
        % Concaténation des résultat

        for i=1:length(filiation)
            for j=1:length(filiation(i).names)

                for k=1:length(cchain)
                    if strcmp(cchain{k},filiation(i).names{j})
                        atoms(t,k) = atoms(t,k) + results(i,j)*filiation(i).conct(j);
                    end
                end

            end
        end
         
%          for i=1:length(filiation)
%              results(i,1)  = results(i,1)/length(filiation);
%          end

    end

catch
    error('One or more nuclide cannot be identified.');
end

end
