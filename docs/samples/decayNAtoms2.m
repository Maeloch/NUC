function [atoms,v_time,daughters] = decayNAtoms2(father,time_s,time_f,steps,natom0)

%% Création de la structure de filiation
% La taille de filiation donne le nombre de branches de décroissance
% possible, la taille d'une brache est une chaine de décroissance. Par
% exemple, il faut 8 étapes pour passer du Rn-222 au Pb-206, et il y a 15
% façon de le faire, 15 branches possibles. 

if isstring(father) || ischar(father)
    filiation = wholechain(father);
else
    filiation = father;
end

%% Initialisation

n_points = steps;
natom_0 = natom0;

lambdas = zeros(length(filiation),length(filiation(1).names));
ratios = zeros(length(filiation),length(filiation(1).names));
natoms = zeros(length(filiation),length(filiation(1).names));
results = zeros(length(filiation),length(filiation(1).names));

daughters= containers.Map();

cchain = chain(filiation(1).names{1});

atoms  = zeros(n_points+1,length(cchain));

v_time = time_s:(time_f-time_s)/n_points:time_f;

%% 
try
    
    % Création de la structure résultat
    for i=1:length(filiation)
        for j=1:length(filiation(i).names)

            lambdas(i,j)  = filiation(i).lambdas(j);
            ratios (i,j)  = filiation(i).intes(j);
            results(i,j)  = 0;

            % j'aurais aimé initialiser les différents Rn avec une valeur
            % non nulle, mais c'est une gageure à faire passer cette
            % information. Donc à la place, on va faire tourner plusieurs
            % fois le code et renvoyer la chaine de décroissance. une sorte
            % de dictionnaire.

%             if(length(natom_0)==length(filiation))
%                 natoms (i,j)  = natom_0(j); 
%             else
%                 natoms (i,j)  = 0;
%                 warning('DECAYNATOMS2:37  length(natom_0 != length(filiation)');
%             end
            
        end
        natoms(i,1)  = natom_0(1);
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
                        
                        if(~isKey(daughters,cchain{k}))
                            daughters(cchain{k}) = k;
                        end

                    end %if
                end %for k
            end %for j
        end %for i
         
%          for i=1:length(filiation)
%              results(i,1)  = results(i,1)/length(filiation);
%          end

    end

catch
    error('One or more nuclide cannot be identified.');
end

end
