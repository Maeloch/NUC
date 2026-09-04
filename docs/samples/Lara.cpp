//
//  Lara.cpp
//  Decay
//
//  Created by Grégoire Dougniaux on 18/10/12.
//  Copyright 2012 __MyCompanyName__. All rights reserved.
//

#include "Lara.hpp"
#include "Parseur.hpp"

#include "logFile.hpp"

string          Lara::bddpath = "";
vector<string>  Lara::table;
map<string,int> Lara::index;
vector<string>  Lara::short_element;
vector<string>  Lara::long_element;


//definition du singleton
Lara Lara::Singleton;

//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////

void Lara::addElement(string little_name, string entire_name)
{
    short_element.push_back(little_name);
     long_element.push_back(entire_name);
}
bool Lara::builtElementTable()
{
    try
    {
        short_element.clear();
        long_element.clear();
        
        addElement("H" , "Hydrogène");
        addElement("He", "Hélium");     //2
        
        addElement("Li", "Lithium");
        addElement("Be", "Béryllium");
        addElement("B" , "Bore");
        addElement("C" , "Carbone");
        addElement("N" , "Azote");
        addElement("O" , "Oxygène");
        addElement("F" , "Fluor");
        addElement("Ne", "Néon");       //10
        
        addElement("Na", "Sodium");
        addElement("Mg", "Magnésium");
        addElement("Al", "Aluminium");
        addElement("Si", "Silicium");
        addElement("P" , "Phosphore");
        addElement("S" , "Soufre");
        addElement("Cl", "Chlore");
        addElement("Ar", "Argon");      //18
        
        addElement("K" , "Potassium");
        addElement("Ca", "Calcium");
        addElement("Sc", "Scandium");
        addElement("Ti", "Titane");
        addElement("V" , "Vanadium");
        addElement("Cr", "Chrome");
        addElement("Mn", "Manganèse");
        addElement("Fe", "Fer");
        addElement("Co", "Cobalt");
        addElement("Ni", "Nickel");
        addElement("Cu", "Cuivre");
        addElement("Zn", "Zinc");
        addElement("Ga", "Gallium");
        addElement("Ge", "Germanium");
        addElement("As", "Arsenic");
        addElement("Se", "Sélénium");
        addElement("Br", "Brome");
        addElement("Kr", "Krypton");    //36
        
        addElement("Rb", "Rubidium");
        addElement("Sr", "Strontium");
        addElement("Y" , "Yttrium");
        addElement("Zr", "Zirconium");
        addElement("Nb", "Niobium");
        addElement("Mo", "Molybdène");
        addElement("Tc", "Technétium");
        addElement("Ru", "Ruthérium");
        addElement("Rh", "Rhodium");
        addElement("Pd", "Palladium");
        addElement("Ag", "Argent");
        addElement("Cd", "Cadmium");
        addElement("In", "Indium");
        addElement("Sn", "Etain");
        addElement("Sb", "Antimoine");
        addElement("Te", "Tellure");
        addElement("I" , "Iode");
        addElement("Xe", "Xénon");      //54
        
        addElement("Cs", "Césium");
        addElement("Ba", "Baryum");
        
        //lanthanides
        addElement("La", "Lanthane");
        addElement("Ce", "Cérium");
        addElement("Pr", "Praséodyme");
        addElement("Nd", "Néodyme");
        addElement("Pm", "Prométhium");
        addElement("Sm", "Samarium");
        addElement("Eu", "Europium");
        addElement("Gd", "Gadolinium");
        addElement("Tb", "Terbium");
        addElement("Dy", "Dysprosium");
        addElement("Ho", "Holmium");
        addElement("Er", "Erbium");
        addElement("Tm", "Thullium");
        addElement("Yb", "Ytterbium");
        addElement("Lu", "Lutécium");   //71
        //
        
        addElement("Hf", "Hafnium");
        addElement("Ta", "Tantale");
        addElement("W" , "Tungstène");
        addElement("Re", "Rhénium");
        addElement("Os", "Osmium");
        addElement("Ir", "Iridium");
        addElement("Pt", "Platine");
        addElement("Au", "Or");
        addElement("Hg", "Mercure");
        addElement("Tl", "Thallium");
        addElement("Pb", "Plomb");
        addElement("Bi", "Bismuth");
        addElement("Po", "Polonium");
        addElement("At", "Astate");
        addElement("Rn", "Radon");      //86
        
        addElement("Fr", "Francium");
        addElement("Ra", "Radium");
        
        //actinides
        addElement("Ac", "Actinium");
        addElement("Th", "Thorium");
        addElement("Pa", "Protactinium");
        addElement("U" , "Uranium");
        addElement("Np", "Neptunium");
        addElement("Pu", "Plutonium");
        addElement("Am", "Américium");
        addElement("Cm", "Curium");
        addElement("Bk", "Berkélium");
        addElement("Cf", "Californium");
        addElement("Es", "Einsteinium");
        addElement("Fm", "Fermium");
        addElement("Md", "Mendélévium");
        addElement("No", "Nobélium");
        addElement("Lr", "Lawrencium"); //103
        //
        
        addElement("Rf", "Rutherfordium");
        addElement("Db", "Dubnium");
        addElement("Sg", "Seaborgium");
        addElement("Bh", "Bohrium");
        addElement("Hs", "Hassium");
        addElement("Mt", "Meitnérium");
        addElement("Ds", "Darmstadtium");
        addElement("Rg", "Roentgenium");
        addElement("Cn", "Copernicium"); //112 ...
        addElement("Uut","Ununtrium");
        addElement("Fl", "Flévorium");
        addElement("Uup","Ununpentium");
        addElement("Lv", "Livermorium");
        addElement("Uus","Ununseptium");
        addElement("Uuo","Ununoctium"); //118
        
        return true;
    }
    catch( int err )
    {
        throw err;
    }
    return false;
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////

string Lara::name(int A, int Z, char S = 'F', char sep = '-')
{
    std::ostringstream ostr;
    ostr << short_name(Z) << sep << A;
    
    if( S != 'F' ) ostr << 'm';
    
    return string( ostr.str() );
}


string Lara::bddfile(string elt_name)
{
    if( bddpath == "" )
    {
        flog("error: Lara nuclear database has to be initilised: type 'Lara::init(\"/your/bdd/path/\");'");
        return "";
    }
    string fileid;

    if( elt_name[elt_name.length() -1] == 't' )    fileid = bddpath + elt_name                  ;
    else                                           fileid = bddpath + elt_name + string(".txt");
    
    return fileid;
}


value Lara::massActivity(int A, int Z, char S)
{
    return massActivity(name(A, Z, S));
}
value Lara::massActivity(string elt_name)
{
    value res;

    ifstream ifile( bddfile(elt_name).c_str() );

    if(!ifile.is_open())
    {
        double A_ = A(elt_name);
        return value(Avogadro,0)/value(A_,A_*0.005)*lambda(elt_name)*becquerel/gram;
    }

    string tmp_str; string tmp;
    double tmp_dbl;
    for(unsigned int i=1; i<=5; i++) getline(ifile,tmp);
    for(unsigned int i=1; i<=4; i++) ifile >> tmp_str;
    
    ifile >> tmp_dbl; res.n = tmp_dbl;
    ifile >> tmp_str;
    ifile >> tmp_dbl; res.u = tmp_dbl;
    
    ifile.close();

    return res*becquerel/gram;

}


value Lara::lambda(int A, int Z, char S='F')
{
    return lambda( name(A,Z,S,'-') );
}
value Lara::lambda(string elt_name)
{
    value res;
    
    ifstream ifile( bddfile(elt_name).c_str() );
    
    if(!ifile.is_open())
    {
        //flog("Unable to read BDD to get decay constant for " + elt_name + ". It is assumed stable and lambda is set to 0");
        return value(0,0)/second;
    }

    string tmp_str; string tmp;
    double tmp_dbl;
    for(unsigned int i=1; i<=4; i++) getline(ifile,tmp);
    for(unsigned int i=1; i<=4; i++) ifile >> tmp_str;
    
    ifile >> tmp_dbl; res.n = tmp_dbl;
    ifile >> tmp_str;
    ifile >> tmp_dbl; res.u = tmp_dbl;
    
    ifile.close();
    
    return res/second;
}


bool Lara::decay(int A, int Z, char S, vector<string>& daugthers, vector<string>& ways, vector<value>& intensities)
{
    return decay(name(A, Z, S), daugthers, ways, intensities);
}
bool Lara::decay(string elt_name, vector<string>& daugthers, vector<string>& ways, vector<value>& intensities)
{
    value res;
    
    ifstream ifile( bddfile(elt_name).c_str() );
    
    if(!ifile.is_open())
    {
        //flog("Unable to read BDD to get decay ways for " + elt_name + ". It is assumed stable.");
        return false;
    }
    
    string  tmp_str;
    value   tmp_val;
    for(unsigned int i=1; i<=3; i++) getline(ifile,tmp_str);
    for(unsigned int i=1; i<=2; i++) ifile >> tmp_str;
    
    
    // Decay way(s) ; alpha ; Fr-221 ; 100 ; 0.186 ...
    getline(ifile,tmp_str);
    istringstream iss(tmp_str);

    vector<string> tmp_gst;
    while ( std::getline( iss, tmp_str, ' ' ) )
    {
        tmp_gst.push_back(tmp_str);
    }
    for( unsigned int i=2; i<tmp_gst.size(); i+=8 )
    {
        ways.       push_back(                  tmp_gst[i+0]          );
        daugthers.  push_back(                  tmp_gst[i+2]          );
        intensities.push_back( value(   str2dbl(tmp_gst[i+4]),
                                        str2dbl(tmp_gst[i+6]))*perCent);
    }
    
    ifile.close();
    
    return true;
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////

unsigned int Lara::A(string elt_name)
{
    string s = elt_name;
    
    if( !isnumeric(&elt_name[elt_name.length()-1]) )
    {
        s = elt_name.substr( 0, elt_name.size()-1 );
    }
    
    size_t ext_pos = s.find_last_of( '-' );
    string t = s.substr( ext_pos+1 );
    
    return str2dbl( t );
}

unsigned int Lara::Z(string elt_name)
{
    string name = elt_name.substr( 0, elt_name.find_first_of( '-' ) );
    
    for(unsigned int i=0; i<short_element.size();i++)
        if(short_element[i]==name)
            return i+1;
    
    return 0;
}

char Lara::S(string elt_name)
{
    if( !isnumeric(&elt_name[elt_name.length()-1]) ) return 'M'; return 'F';
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////

bool Lara::spectre(string elt_name, string type, vector<vector< value > > &res )
{
    for( unsigned int i=0; i<res.size(); i++) res[i].clear(); res.clear();
    
    
    ifstream ifile( bddfile(elt_name).c_str() );
        
    if(!ifile.is_open())
    {
        //flog("Unable to read BDD to get decay ways for " + elt_name + ". It is assumed stable.");
        return false;
    }
    
    vector<value>   energies;
    vector<value>   intensities;
    vector<string>  tmp_gst;
    string          tmp_str;
    value           tmp_val;
    istringstream   iss;
    
    for(unsigned int i=1; i<=7; i++) getline(ifile, tmp_str);
    
    while( !ifile.eof() )
    {
        getline(ifile,tmp_str);
        iss.clear(); iss.str(tmp_str);
        tmp_gst.clear();
        
        if( tmp_str.size()>10)
        {
            while ( std::getline( iss, tmp_str, ' ' ) ) tmp_gst.push_back(tmp_str);

            if( tmp_gst[0] == type )
            {
                energies.   push_back( value(str2dbl( tmp_gst[2] ), max(str2dbl(tmp_gst[4]),0.050))*keV);
                intensities.push_back( value(str2dbl( tmp_gst[6] ), max(str2dbl(tmp_gst[8]),1e-06))*perCent);
            }
        }
    }
    
    res.clear();
    res.push_back(energies);
    res.push_back(intensities);
    
    ifile.close();

    return res.size()>0;
}

//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////

