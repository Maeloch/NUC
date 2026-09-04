Attribute VB_Name = "PeriodicTable"
'==============================================================================
' PeriodicTable.bas -- table des 118 elements, extraite de Lara.cpp
' (G. Dougniaux, 2012). Voir docs/RECONCILIATION.md paragraphe 5.
'==============================================================================

Function ElementSymbols() As Variant
    ElementSymbols = Array("H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Uut", "Fl", "Uup", "Lv", "Uus", "Uuo")
End Function

Function ElementNamesFr() As Variant
    ElementNamesFr = Array("Hydrogène", "Hélium", "Lithium", "Béryllium", "Bore", "Carbone", "Azote", "Oxygène", "Fluor", "Néon", "Sodium", "Magnésium", "Aluminium", "Silicium", "Phosphore", "Soufre", "Chlore", "Argon", "Potassium", "Calcium", "Scandium", "Titane", "Vanadium", "Chrome", "Manganèse", "Fer", "Cobalt", "Nickel", "Cuivre", "Zinc", "Gallium", "Germanium", "Arsenic", "Sélénium", "Brome", "Krypton", "Rubidium", "Strontium", "Yttrium", "Zirconium", "Niobium", "Molybdène", "Technétium", "Ruthérium", "Rhodium", "Palladium", "Argent", "Cadmium", "Indium", "Etain", "Antimoine", "Tellure", "Iode", "Xénon", "Césium", "Baryum", "Lanthane", "Cérium", "Praséodyme", "Néodyme", "Prométhium", "Samarium", "Europium", "Gadolinium", "Terbium", "Dysprosium", "Holmium", "Erbium", "Thullium", "Ytterbium", "Lutécium", "Hafnium", "Tantale", "Tungstène", "Rhénium", "Osmium", "Iridium", "Platine", "Or", "Mercure", "Thallium", "Plomb", "Bismuth", "Polonium", "Astate", "Radon", "Francium", "Radium", "Actinium", "Thorium", "Protactinium", "Uranium", "Neptunium", "Plutonium", "Américium", "Curium", "Berkélium", "Californium", "Einsteinium", "Fermium", "Mendélévium", "Nobélium", "Lawrencium", "Rutherfordium", "Dubnium", "Seaborgium", "Bohrium", "Hassium", "Meitnérium", "Darmstadtium", "Roentgenium", "Copernicium", "Ununtrium", "Flévorium", "Ununpentium", "Livermorium", "Ununseptium", "Ununoctium")
End Function

' Numero atomique a partir du symbole (ex. "Zr" -> 40). 0 si inconnu.
Function ZOfSymbol(symbol As String) As Integer
    Dim syms As Variant, i As Integer
    syms = ElementSymbols()
    For i = LBound(syms) To UBound(syms)
        If syms(i) = symbol Then
            ZOfSymbol = i + 1
            Exit Function
        End If
    Next i
    ZOfSymbol = 0
End Function
