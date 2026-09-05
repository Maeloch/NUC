Attribute VB_Name = "LARA"
'===============================================================================
' LARA.bas -- acces Laraweb (LNHB) par etiquette, avec cache memoire et
' repli sur cache local. Corrige par rapport au module d'origine :
'   - Remplace l'ancien couple GET_LARA/LARA_TXT(nuclide, numero_de_ligne)
'     (fragile : le nombre de lignes d'en-tete depend du nucleide) par un
'     reperage par ETIQUETTE (LARA_FIELD) -- robuste quel que soit le
'     nombre de lignes d'en-tete pour ce nucleide precis.
'   - Remplace "Microsoft.XMLHTTP" par "WinHttp.WinHttpRequest.5.1", qui
'     expose un vrai timeout explicite (SetTimeouts) -- sans lui, un
'     probleme reseau pouvait figer Excel indefiniment.
'   - isStable() : un nucleide est stable si le champ "Decay constant" est
'     absent de ses donnees LARA. Remplace l'ancienne implementation qui
'     comparait la ligne 3 (Z) a "Z " (fragile et peu lisible).
'
' URL confirmee directement par l'auteur (pas de suffixe "_@04" necessaire,
' voir docs/RECONCILIATION.md paragraphe 6 du depot NUC) : ajuster
' LARA_BASE_URL et LOCAL_CACHE_DIR ci-dessous si votre environnement differe.
'
' Non teste en conditions reelles (reseau/proxy du laboratoire) -- a
' valider avant mise en production. Le format de fichier a ete verifie par
' requete directe (09/2026) mais LNHB peut le faire evoluer sans preavis ;
' la bascule automatique vers le cache local en cas d'echec reste le filet
' de securite si le format change de nouveau.
'===============================================================================

Private Const LARA_BASE_URL As String = "http://www.lnhb.fr/Laraweb/Results/"
Private Const LOCAL_CACHE_DIR As String = "O:\SCA\X-ECHANGES\Macros\Lara\"  ' a adapter a votre environnement

Private laraCache As Object   ' Scripting.Dictionary : nuclide (String) -> texte complet (String)

' ------------------------------------------------------------------------
' GetFromWebpage -- requete HTTP GET simple, avec timeout et verification
' du statut. Renvoie le corps de la reponse si le statut est 200, une
' chaine vide sinon (reseau indisponible, timeout, page d'erreur, ...).
'
' timeout_ms : delai maximum en millisecondes pour la resolution DNS, la
' connexion, l'envoi et la reception, chacun. 5000 ms (5 s) par defaut.
' ------------------------------------------------------------------------
Private Function GetFromWebpage(url As String, Optional timeout_ms As Long = 5000) As String
On Error GoTo Err_GetFromWebpage

    Dim objWeb As Object
    Set objWeb = CreateObject("WinHttp.WinHttpRequest.5.1")

    ' (resolution, connexion, envoi, reception) -- les 4 timeouts de WinHttp
    objWeb.SetTimeouts timeout_ms, timeout_ms, timeout_ms, timeout_ms

    objWeb.Open "GET", url, False
    objWeb.Send

    If objWeb.Status = 200 Then
        GetFromWebpage = objWeb.responseText
    Else
        GetFromWebpage = ""   ' statut HTTP <> 200 -> echec propre
    End If

    Set objWeb = Nothing
    Exit Function

Err_GetFromWebpage:
    ' Timeout, DNS/proxy indisponible, ou tout autre incident reseau :
    ' echec propre plutot que de laisser Excel planter ou se figer.
    GetFromWebpage = ""
    Set objWeb = Nothing
End Function

' ------------------------------------------------------------------------
' looks_like_lara_file -- validation grossiere mais efficace : un vrai
' fichier .lara.txt commence par "Nuclide ;". Filet de securite
' supplementaire, independant du code de statut HTTP.
' ------------------------------------------------------------------------
Private Function looks_like_lara_file(txt As String) As Boolean
    looks_like_lara_file = (Left(Trim(txt), 8) = "Nuclide ")
End Function

Private Function local_cache_path(nuclide As String) As String
    local_cache_path = LOCAL_CACHE_DIR & nuclide & ".txt"
End Function

Private Function GetText(sFile As String) As String
On Error GoTo Err_GetText
   Dim nSourceFile As Integer, sText As String
   nSourceFile = FreeFile
   Open sFile For Input As #nSourceFile
   sText = Input$(LOF(nSourceFile), nSourceFile)
   Close #nSourceFile
   GetText = sText
   Exit Function
Err_GetText:
   GetText = ""
End Function

Private Sub WriteText(sFile As String, content As String)
On Error Resume Next
    Dim nFile As Integer
    nFile = FreeFile
    Open sFile For Output As #nFile
    Print #nFile, content
    Close #nFile
End Sub

' ------------------------------------------------------------------------
' LARA_FETCH -- coeur du module. Renvoie le texte complet des donnees LARA
' d'un nucleide (toutes lignes), en tentant le web puis en repliant sur le
' cache local. Cache memoire (laraCache) pour la duree du classeur ouvert :
' les appels repetes (un par champ demande) pour le MEME nucleide ne
' declenchent qu'UNE requete reseau.
'
' Parametre force_web : Vrai pour forcer une nouvelle tentative reseau meme
' si ce nucleide est deja en cache memoire. Faux par defaut.
' ------------------------------------------------------------------------
Function LARA_FETCH(nuclide As String, Optional force_web As Boolean = False) As String

    If laraCache Is Nothing Then
        Set laraCache = CreateObject("Scripting.Dictionary")
    End If

    If Not force_web And laraCache.Exists(nuclide) Then
        LARA_FETCH = laraCache(nuclide)
        Exit Function
    End If

    Dim url As String, web_txt As String, result As String
    url = LARA_BASE_URL & nuclide & ".lara.txt"
    web_txt = GetFromWebpage(url)

    If looks_like_lara_file(web_txt) Then
        result = web_txt
        ' Rafraichit le cache local avec la reponse fraiche.
        WriteText local_cache_path(nuclide), web_txt
    Else
        ' Web indisponible/invalide -> repli sur le cache local existant.
        result = GetText(local_cache_path(nuclide))
    End If

    laraCache(nuclide) = result
    LARA_FETCH = result

End Function

' ------------------------------------------------------------------------
' LARA_FIELD -- trouve la ligne commencant par `label` dans les donnees
' d'un nucleide, et la renvoie decoupee sur ";" (chaque element "Trim"e).
'
' Exemples de label : "Nuclide", "Z", "Decay constant", "Specific activity",
' "Half-life (s)", "Daughter(s)".
'
' Renvoie un tableau vide (LBound > UBound) si le label n'est pas trouve
' (nucleide stable sans certains champs, ou label absent/mal orthographie).
' ------------------------------------------------------------------------
Function LARA_FIELD(nuclide As String, label As String) As Variant

    Dim txt As String, lignes() As String, i As Long
    txt = LARA_FETCH(nuclide)

    If txt = "" Then
        LARA_FIELD = Array()   ' ni web ni cache disponibles
        Exit Function
    End If

    lignes = Split(txt, vbLf)

    For i = LBound(lignes) To UBound(lignes)
        If Left(Trim(lignes(i)), Len(label)) = label Then
            Dim brut() As String, parts() As String, j As Long
            brut = Split(lignes(i), ";")
            ReDim parts(LBound(brut) To UBound(brut))
            For j = LBound(brut) To UBound(brut)
                parts(j) = Trim(brut(j))
            Next j
            LARA_FIELD = parts
            Exit Function
        End If
    Next i

    LARA_FIELD = Array()   ' label non trouve pour ce nucleide

End Function

' ------------------------------------------------------------------------
' isStable -- un nucleide est considere stable si le champ "Decay constant"
' est absent de ses donnees LARA.
' ------------------------------------------------------------------------
Function isStable(nuclide As String) As Boolean
    Dim d As Variant
    d = LARA_FIELD(nuclide, "Decay constant")
    isStable = (LBound(d) > UBound(d))   ' tableau vide -> champ absent -> stable
End Function

' ------------------------------------------------------------------------
' DecayConstant_v2 -- (valeur, incertitude) en s^-1. (0,0) si stable.
' Remplace l'ancienne version fondee sur GET_LARA(nuclide, 9, 5).
' ------------------------------------------------------------------------
Function DecayConstant_v2(nuclide As String) As Double()
    Dim P(1) As Double
    If isStable(nuclide) Then
        P(0) = 0: P(1) = 0
    Else
        Dim d As Variant
        d = LARA_FIELD(nuclide, "Decay constant")
        If LBound(d) <= UBound(d) Then
            P(0) = CDbl(d(1))
            P(1) = CDbl(d(2))
        End If
    End If
    DecayConstant_v2 = P
End Function

' ------------------------------------------------------------------------
' Daughters -- voies de desintegration : tableau 2D (n_voies x 3), colonnes
' (voie, nucleide fils, %). Sans incertitude sur l'intensite (format LARA
' actuel -- voir docs/RECONCILIATION.md paragraphe 3.2). NON PORTE depuis
' le chat precedent : ajoutee ici pour completer le module au meme niveau
' que les versions Python/Matlab/C (nuc/lara_client.py, lara_daughters.m,
' nuc_lara_daughters).
' ------------------------------------------------------------------------
Function Daughters(nuclide As String) As Variant
    Dim f As Variant
    f = LARA_FIELD(nuclide, "Daughter(s)")

    If LBound(f) > UBound(f) Then
        Daughters = Array()
        Exit Function
    End If

    Dim n_voies As Long
    n_voies = (UBound(f) - LBound(f)) \ 3   ' 3 champs par voie apres l'etiquette

    Dim result() As Variant
    ReDim result(1 To n_voies, 1 To 3)

    Dim i As Long, base As Long
    For i = 1 To n_voies
        base = LBound(f) + 1 + (i - 1) * 3   ' +1 pour sauter l'etiquette "Daughter(s)"
        result(i, 1) = f(base)       ' voie
        result(i, 2) = f(base + 1)   ' nucleide fils
        result(i, 3) = CDbl(f(base + 2))  ' %
    Next i

    Daughters = result
End Function
