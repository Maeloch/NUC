function chain=wholechain(father)

    chain(1).names = {father};
    chain(1).intes = [];
    chain(1).conct = [];
    current = 1;
    
    while current <= length(chain)
        
        [~,daugs,percents] = decayWay(chain(current).names{end});
        
        if isempty(daugs)
            
            chain(current).intes(end+1) = 0;
            chain(current).conct(end+1) = 0;
            
            current = current+1;

        else % At least one daughter exists
            
            chain(current).names(end+1) = daugs(1);
            
            % Permet l'initialisation de cette partie de la structure tout
            % en concervant le même indice entre intes[père->fils] et
            % lambda[père].
            
            if isempty( chain(current).intes )       
                chain(current).intes(    1) = percents(1);
                chain(current).conct(    1) = 1;
            else
                chain(current).intes(end+1) = percents(1);
                chain(current).conct(end+1) = 1;
            end
            
            % S'il en existe d'autre, on ajoute autant de colonne que
            % nécessaire
            
            for i=2:length(daugs)
                
                chain(end+1).names      = chain(current).names;
                chain(end  ).intes      = chain(current).intes;
                chain(end  ).conct      = zeros(size(chain(current).intes));
                
                chain(end  ).names(end) = daugs(i);
                chain(end  ).intes(end) = percents(i);
                chain(end  ).conct(end) = 0;

            end
           
        end

    end
    
    
    for i=1:length(chain)
        
        for j=1:length(chain(i).names)
    
            chain(i).lambdas(j) = lambda(chain(i).names{j});
            
        end
    end
    
      
end

