function natoms_t = bateman(lambdas,ratios,natoms_0,time)

%#codegen

    % petit
    %EPSILON = 1e-100;
    
    useValue = false;%~isnumeric(lambdas) || ~isnumeric(ratios) || ~isnumeric(natoms_0) || ~isnumeric(time);
   
    
    if useValue
        natoms_t = value(natoms_0);
    else
        natoms_t = natoms_0;
    end
        
    if time <= 0
        return;
    end
    
    
%     
%     % valeurs partielles
%     M = value();
%     Q = value();
%     K = value();
%     J = value();

    % Pour chaque radionucléide de la liste (non mergée)
    for i=1:length(lambdas)

        % Equation de Bateman pour le m-ième atome de la liste (grand-père ; père ; fils ; ...)
        if useValue
            M = value(0,0); % somme
        else
            M = 0; % somme
        end
        
        for m=1:i-1 % pas le current

            % Produit des b_{père,fils} * \lambda_père
            if useValue
                Q = value(1,0);
            else
                Q = 1;
            end
            
            for q=m:i-1 % pas le dernier fils, atoms.last()
                Q = Q * ratios(q) * lambdas(q);
            end

            % Somme des exp^{-\lambda_k * t} / \prod{ \lambda_j - \lambda_k }
            if useValue
                K = value(0,0);
            else
                K = 0;
            end
            
            for k=m:i % jusqu'au current
            
                % \prod{ \lambda_j - \lambda_k }
                if useValue
                    J = value(1,0);
                else
                    J = 1;
                end
                for j=m:i % jusqu'au current
                
                    if j~=k
                    
                        %if lambdas(j) ~= lambdas(k)
                            J = J * (lambdas(j)-lambdas(k));
                        %else
                        %    J = J * EPSILON;
                        %end
                    end
                end

                K = K + exp(-lambdas(k)*time) / J;
                
            end
            % Contribution de chaque élément de la chaîne au current
            M = M +  natoms_0(m) * Q * K;
           
        end
        natoms_t(i) = natoms_0(i) * exp(-lambdas(i)*time) + M;
                        
    end

end