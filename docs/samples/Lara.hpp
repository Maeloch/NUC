//
//  Lara.h
//  Decay
//
//  Created by Grégoire Dougniaux on 18/10/12.
//  Copyright 2012 __MyCompanyName__. All rights reserved.
//
#ifndef Lara_H
#define Lara_H

//#include "Base.h"
#include "Adjuvants.hpp"
#include "Value.hpp"
//#include "string.hpp"
#include <string>
#include <vector>
#include <map>
#include "logFile.hpp"
using namespace std;

class Lara
{
public:
    
    static inline bool init(string path){bddpath = path; G4UnitDefinition::BuildUnitsTable(); return builtElementTable();}
    
    static  string dataPath(){return bddpath;}

    static  string name(int A, int Z, char S, char sep);

    static  value  lambda(int A, int Z, char S);
    static  value  lambda(string elt_name);
    
    static  value  halflife(int A, int Z, char S){return value(log(2),0)/lambda(A,Z,S);}
    static  value  halflife(string elt_name){return value(log(2),0)/lambda(elt_name);}
    
    static  value  massActivity(int A, int Z, char S);
    static  value  massActivity(string elt_name);
    
    static  bool   decay(int A, int Z, char S, vector<string>& daugthers, vector<string>& ways, vector<value>& intensities);
    static  bool   decay(string elt_name, vector<string>& daugthers, vector<string>& ways, vector<value>& intensities);

    static  string  short_name(unsigned int Z){if(Z-1<short_element.size()) return short_element[Z-1]; return "no_name";}
    static  string  long_name (unsigned int Z){if(Z-1< long_element.size()) return  long_element[Z-1]; return "no_name";}
    
/**/
    
    static  unsigned int A(string elt_name);
    static  unsigned int Z(string elt_name);
    static  char         S(string elt_name);

/**/
    
    static bool spectre(string elt_name, string type, vector<vector< value > > &res );
    
private:
    
    static  vector<string>  table;
    static  map<string,int> index;


// SINGLETON
    Lara(){}
    Lara(const Lara& DT){init(bddpath);}
    Lara operator=(const Lara&) {return *this;}

    ~Lara(){}

    static  string bddfile(string elt_name);

    static bool builtElementTable();
    static void addElement(string little_name, string entire_name);
    static vector<string> short_element;
    static vector<string> long_element;

    static string bddpath;
    static Lara Singleton;
};

#endif
