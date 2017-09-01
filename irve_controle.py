import sys
import csv
import json
import re
import array

regexp_insee = re.compile('^\d[0-9AB]\d\d\d$')
regexp_id = re.compile('^FR.*')
regexp_date_AAAAMMJJ = re.compile('^20\d\d[/\-][01]\d[/\-][0-3]\d$')
regexp_date_AAAAMMJJ_court = re.compile('^20\d\d[01]\d[0-3]\d$')
regexp_date_JJMMAAAA = re.compile('^[0-3][/\-][01]\d[/\-]\d20\d\d$')
regexp_float = re.compile('^[\+\-]?\d*\.\d*$')

erreurs = []

def report_err(ligne, colonne, gravite, libelle):
    erreurs.append(dict(ligne=ligne, colonne=colonne, gravite=gravite, libelle=libelle))

def irve_check(input, encoding='utf-8', delimiter=';'):
    try:
        with open(input, 'r', encoding=encoding) as irve_csv:
            irve_reader = csv.reader(irve_csv, delimiter=delimiter)
            header = None
            ligne = 0
            err = 0
            for irve in irve_reader:
                ligne = ligne+1
                if header is None:
                    header = irve
                    if len(header)<17:
                        report_err(0, 0, 3, 'ERR entête: nombre de colonnes inférieur à 17')
                        return(3) # structure du fichier incorrecte, inutile de poursuivre
                elif len(irve) < 17: # contrôle du nombre minimal de colonnes
                    report_err(ligne, 0, 2, 'ERR ligne %s : nombre de colonnes inférieur à 17' % ligne)
                else:
                    if len(irve) > 17:
                        report_err(ligne, 0, 0, "INFO ligne %s : colonnes supplémentaires %s au lieu de 17" % (ligne, len(irve)))
                    if irve[0] == '':
                        report_err(ligne, 1, 1, 'ERR ligne %s : n_amenageur est vide' % ligne)
                    if irve[3] != '' and regexp_id.match(irve[3]) is None:
                        report_err(ligne, 4, 1, "ERR ligne %s : id_station invalide '%s'" % (ligne,irve[3]))
                    if irve[4] == '':
                        report_err(ligne, 4, 1, 'ERR ligne %s : n_station est vide' % ligne)
                    if irve[5] == '':
                        report_err(ligne, 6, 1, 'ERR ligne %s : ad_station est vide' % ligne)
                    if irve[6] == '':
                        report_err(ligne, 7, 0, 'INFO ligne %s : code_insee est vide' % ligne)
                    elif  regexp_insee.match(irve[6]) is None:
                        report_err(ligne, 7, 0, "INFO ligne %s : code_insee invalide '%s'" % (ligne,irve[6]))
                    if ',' in irve[7]:
                        report_err(ligne, 8, 0, "INFO ligne %s : Xlongitude mal formatté '%s' (séparateur décimal devrait être un point au lieu de la virgule)" % (ligne,irve[7]))
                    if regexp_float.match(irve[7].replace(',','.')) is None:
                        report_err(ligne, 8, 1, "ERR ligne %s : Xlongitude invalide '%s'" % (ligne,irve[7]))
                    irve[7] = irve[7].replace(',','.')
                    if float(irve[7]) < -180 or float(irve[7]) > 180 :
                        report_err(ligne, 8, 1, "ERR ligne %s : Xlongitude hors limites -180/+180 '%s'" % (ligne,irve[7]))
                    if ',' in irve[8]:
                        report_err(ligne, 8, 0, "INFO ligne %s : Ylatitude mal formatté '%s' (séparateur décimal devrait être un point au lieu de la virgule)'" % (ligne,irve[8]))
                    if regexp_float.match(irve[8].replace(',','.')) is None:
                        report_err(ligne, 9, 1, "ERR ligne %s : Ylatitude invalide '%s'" % (ligne,irve[8]))
                    irve[8] = irve[8].replace(',','.')
                    if float(irve[8]) < -90 or float(irve[8]) > 90 :
                        report_err(ligne, 9, 1, "ERR ligne %s : Ylatitude hors limites -90/+90° '%s'" % (ligne,irve[8]))
                    if float(irve[7]) > 40 and float(irve[7]) < 55 and float(irve[8]) > -10 and float(irve[8]) < 10:
                        report_err(ligne, 8, 0, "INFO ligne %s : inversion Ylatitude '%s' / Xlongitude '%s'" % (ligne,irve[8],irve[7]))
                    if int(irve[9]) < 1 or int(irve[9]) > 20:
                        report_err(ligne, 10, 1, "ERR ligne %s : nbre_pdc invalide '%s'" % (ligne,irve[9]))
                    if irve[10] != '' and regexp_id.match(irve[10]) is None:
                        report_err(ligne, 11, 1, "ERR ligne %s : id_pdc invalide '%s'" % (ligne,irve[10]))
                    if irve[11] not in ['7','18','22','45','50']:
                        report_err(ligne, 12, 1, "INFO ligne %s : puiss_max invalide '%s'" % (ligne,irve[11]))
                    if irve[13].lower() not in ['gratuit','payant']:
                        report_err(ligne, 14, 1, "ERR ligne %s : acces_recharge invalide (gratuit/payant uniquement) '%s'" % (ligne,irve[13]))
                    if regexp_date_AAAAMMJJ_court.match(irve[16]) is not None:
                        report_err(ligne, 17, 0, "INFO ligne %s : date_maj AAAAMMJJ au lieu de AAAA/MM/JJ '%s'" % (ligne,irve[16]))
                    elif regexp_date_JJMMAAAA.match(irve[16]) is not None:
                        report_err(ligne, 17, 0, "INFO ligne %s : date_maj JJ/MM/AAAA au lieu de AAAA/MM/JJ '%s'" % (ligne,irve[16]))
                    elif regexp_date_AAAAMMJJ.match(irve[16]) is None:
                        report_err(ligne, 17, 1, "ERR ligne %s : date_maj invalide, AAAA/MM/JJ attendu '%s'" % (ligne,irve[16]))
            gravite_max = 0
            for e in erreurs:
                if e["gravite"]>gravite_max:
                    gravite_max=e["gravite"]

        if gravite_max < 3:
            print(json.dumps(dict(gravite_max=gravite_max, erreurs=erreurs)))

        return(gravite_max)

    except:
        return(4)

# test combinaisons UTF/ISO et delimiteur ; ou tab
if irve_check(sys.argv[1],encoding='utf-8', delimiter=';') >=3:
    erreurs = []
    if irve_check(sys.argv[1],encoding='utf-8', delimiter='\t') >= 3:
        erreurs = []
        if irve_check(sys.argv[1],encoding='iso8859-1', delimiter=';') >= 3:
            erreurs = []
            if irve_check(sys.argv[1],encoding='iso8859-1', delimiter='\t') >=3:
                print(json.dumps(dict(gravite_max=4, erreurs=[])))
