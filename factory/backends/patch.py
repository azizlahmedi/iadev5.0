# -*- coding: utf-8 -*-
import glob
import os
import re

from factory.backends.base import compiler_lt, delia_context, get_project_path


def get_content(path):
    with open(path, 'r', encoding='latin1') as fd:
        return fd.read()


def set_content(path, content):
    with open(path, 'w', encoding='latin1') as fd:
        fd.write(content)


def sub_latin1(path, patterns):
    content = get_content(path)
    for from_string, to_string in patterns:
        content = content.replace(from_string, to_string)
    set_content(path, content)


def sub_latin1_re(path, patterns):
    content = get_content(path)
    for from_string, to_string in patterns:
        content = re.sub(from_string, to_string, content)
    set_content(path, content)


class PatchBackend(object):
    def fix(self, schema_version, procedure_name, revision, checkout, compiler_version):
        self.fix_me0(schema_version, revision, checkout, compiler_version)
        self.fix_gt_translate(schema_version, revision, checkout)
        self.fix_bibconvertchainedate(schema_version, revision, checkout)
        self.fix_bibtraitelibellesmlg(schema_version, revision, checkout)
        self.fix_bibcalculsoldedevise(schema_version, revision, checkout)
        self.fix_bibcalculmouvementcommun2(schema_version, revision, checkout)
        self.fix_treprv(schema_version, revision, checkout)
        self.fix_floordiv(schema_version, revision, checkout)
        self.fix_invalid_pictures(schema_version, revision, checkout)
        self.fix_invamo(schema_version, revision, checkout)
        self.fix_type_debug(schema_version, revision, checkout)
        self.fix_bibverifcode(schema_version, revision, checkout)
        self.fix_forcou(schema_version, revision, checkout)
        self.fix_eqmouv(schema_version, revision, checkout, compiler_version)
        self.fix_majent(schema_version, revision, checkout)
        self.fix_ost2(schema_version, revision, checkout, compiler_version)
        self.fix_gencal(schema_version, revision, checkout)
        self.fix_calstc(schema_version, revision, checkout)
        self.fix_bibcalculjourscalendrier(schema_version, revision, checkout)

    def fix_me0(self, schema_version, revision, checkout, compiler_version):
        if schema_version == 2016 and compiler_lt(compiler_version, '1.0.4'):
            project_path = get_project_path(checkout, schema_version)
            mag_dir = os.path.join(project_path, 'adl', 'src', 'mag')
            if os.path.isdir(mag_dir):
                ctx = delia_context()
                ctx.initialize(project_path)
                for root, dirs, files in os.walk(mag_dir):
                    for bn in files:
                        if bn.endswith('.adl'):
                            procedure_name = bn.lower().split('.')[0].replace('_', '.')
                            procedure_hash = ctx.mv.get(2009, {}).get(procedure_name, {}).get('hash')
                            if procedure_hash:
                                path = os.path.join(root, bn)
                                content = get_content(path)
                                content = re.sub(re.escape('GP2009M:' + bn), 'GP2009M:%s.ME0' % procedure_hash.upper(), content, flags=re.IGNORECASE)
                                set_content(path, content)

    def fix_checkout(self, checkout, patterns, use_re):
        for source_dir in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', '*')):
            if os.path.isdir(source_dir) and os.path.basename(source_dir) not in ('gra', 'mlg'):
                for root, dirs, files in os.walk(source_dir):
                    for bn in files:
                        if use_re:
                            sub_latin1_re(os.path.join(root, bn), patterns)
                        else:
                            sub_latin1(os.path.join(root, bn), patterns)

    def fix_gt_translate(self, schema_version, revision, checkout):
        """
        https://iris.sungard-finance.fr/svn/viewvc/gp/trunk/gp2009/adl/src/bib/others/bibgttranslate.bib?r1=133009&r2=151364
        """
        if revision < 151364:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'bib', 'others', 'bibgttranslate.bib')):
                patterns = (
                    ('GET.TEXT (GT.msg.in', 'GET.TEXT.6 (GT.msg.in'),
                    ('GET.TEXT.2 (GT.msg.in', 'GET.TEXT.10 (GT.msg.in'),
                    ('GET.TEXT(GT.msg.a.traduire', 'GET.TEXT.6(GT.msg.a.traduire'),
                    ('GET.TEXT.2(GT.msg.a.traduire', 'GET.TEXT.10(GT.msg.a.traduire'),
                )
                sub_latin1(path, patterns)

    def fix_floordiv(self, schema_version, revision, checkout):
        if revision < 163684:
            patterns = [
                (r'\(\s*OSE\.TIME\s*/\s*3600\s*\)', 'FLOORDIV(OSE.TIME, 3600)'),
                (r'\(\s*TIME\s*/\s*3600\s*\)', 'FLOORDIV(TIME, 3600)'),
                (r'\(\s*Ta\.time\s*/\s*3600\s*\)', 'FLOORDIV(Ta.time, 3600)'),
                (r'\(\s*Ch\.TIME\s*/\s*3600\s*\)', 'FLOORDIV(Ch.TIME, 3600)'),
                (r'\(\s*Heure\.tmp\s*/\s*3600\s*\)', 'FLOORDIV(Heure.tmp, 3600)'),
                (r'\(\s*Time\s*/\s*3600\s*\)', 'FLOORDIV(Time, 3600)'),
                (r'\(\s*Ose\.time\s*/\s*3600\s*\)', 'FLOORDIV(Ose.time, 3600)'),
                (r'\(\s*HMSTR\.ose\.heure\.debut\s*/\s*3600\s*\)', 'FLOORDIV(HMSTR.ose.heure.debut, 3600)'),
                (r'\(\s*CTE\.Ecart\.time\s*/\s*3600\s*\)', 'FLOORDIV(CTE.Ecart.time, 3600)'),
                (r'\(\s*Tci\.time\s+OF\s+PROCEDURE\s*/\s*3600\s*\)', 'FLOORDIV(Tci.time OF PROCEDURE, 3600)'),
                (r'\(\s*TIME\s*/\s*60\s*\)', 'FLOORDIV(TIME, 60)'),
                (r'\(\s*OSE\.TIME\s*/\s*60\s*\)', 'FLOORDIV(OSE.TIME, 60)'),
                (r'\(\s*Ta\.time\s*/\s*60\s*\)', 'FLOORDIV(Ta.time, 60)'),
                (r'\(\s*Ch\.TIME\s*/\s*60\s*\)', 'FLOORDIV(Ch.TIME, 60)'),
                (r'\(\s*Heure\.tmp\s*/\s*60\s*\)', 'FLOORDIV(Heure.tmp, 60)'),
                (r'\(\s*Time\s*/\s*60\s*\)', 'FLOORDIV(Time, 60)'),
                (r'\(\s*Ose\.time\s*/\s*60\s*\)', 'FLOORDIV(Ose.time, 60)'),
                (r'\(\s*HMSTR\.ose\.heure\.debut\s*/\s*60\s*\)', 'FLOORDIV(HMSTR.ose.heure.debut, 60)'),
                (r'\(\s*CTE\.Ecart\.time\s*/\s*60\s*\)', 'FLOORDIV(CTE.Ecart.time, 60)'),
                (r'\(\s*Tci\.time\s+OF\s+PROCEDURE\s*/\s*60\s*\)', 'FLOORDIV(Tci.time OF PROCEDURE, 60)')
            ]
            self.fix_checkout(checkout, patterns, True)

        data = {
            (None, os.path.join('bib', 'bibconsult', 'bibconsultdatevaloecran.bib')): [
                ('MOVE(  (CPEG.numero-  (CPEG.numero MOD 17)) / 17 ) * 17 + 1 TO CPEG.lecture', 'MOVE FLOORDIV(CPEG.numero - (CPEG.numero MOD 17), 17) * 17 + 1 TO CPEG.lecture'),
            ],
            (None, os.path.join('mag', 'newport', 'caisbl', 'gestvl', 'newport_caisbl_gestvl.adl')): [
                ('MOVE (1 + ((Nb.vl - 1) / 10)) TO Nb.page.max', 'MOVE (1 + FLOORDIV((Nb.vl - 1), 10)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'front', 'valope', 'newport_front_valope.adl')): [
                ('MOVE Numero.ope / 14 + 1 TO Derniere.page', 'MOVE FLOORDIV(Numero.ope, 14) + 1 TO Derniere.page'),
                ('MOVE Numero.ope OF PROCEDURE / 14 TO Page.courante', 'MOVE FLOORDIV(Numero.ope OF PROCEDURE, 14) TO Page.courante'),
            ],
            (None, os.path.join('mag', 'newport', 'gesbdf', 'titbdf', 'newport_gesbdf_titbdf.adl')): [
                ('PRINT TO ETAT @tab to COL1 +(ose.largeur.etat-length(ce.chaine))/2,ce.chaine', 'PRINT TO ETAT @tab to COL1 + FLOORDIV(ose.largeur.etat - length(ce.chaine), 2), ce.chaine'),
            ],
            (None, os.path.join('mag', 'newport', 'gesita', 'glfund2', 'newport_gesita_glfund2.adl')): [
                ("+ (( Time-((Time/60)AS '2N')*60)AS '2N') AS '2C'", "+ (( Time-(FLOORDIV(Time,60)AS '2N')*60)AS '2N') AS '2C'"),
            ],
            (None, os.path.join('mag', 'newport', 'gesrep', 'intrep', 'newport_gesrep_intrep.adl')): [
                ("+((OSE.TIME-((OSE.TIME/60)AS '2N')*60)AS '2N')AS '2C'", "+((OSE.TIME-(FLOORDIV(OSE.TIME,60)AS '2N')*60)AS '2N')AS '2C'"),
            ],
            (None, os.path.join('agl', 'osebaliseetat.txt')): [
                ('PRINT TO OCM.Etat1 @TAB TO ( OCM.ColDebut1 + ( ABS( OCM.ColFin1 -  OCM.ColDebut1 )  - Length ( OCM.Mot1+OCM.Mot2 ) ) / 2 ) , OCM.Mot1, OCM.Mot2', 'PRINT TO OCM.Etat1 @TAB TO ( OCM.ColDebut1 + FLOORDIV( ABS( OCM.ColFin1 -  OCM.ColDebut1 )  - Length ( OCM.Mot1+OCM.Mot2 ), 2)) , OCM.Mot1, OCM.Mot2'),
                ('PRINT TO OCM.Etat @TAB TO ( OCM.ColDebut + ( ABS( OCM.ColFin -  OCM.ColDebut )  - Length ( OCM.Mot ) ) / 2 ) , OCM.Mot', 'PRINT TO OCM.Etat @TAB TO ( OCM.ColDebut + FLOORDIV( ABS( OCM.ColFin -  OCM.ColDebut )  - Length ( OCM.Mot ), 2)) , OCM.Mot'),
            ],
            (None, os.path.join('bib', 'bibcalcul', 'bibcalculcourtagefrance.bib')): [
                ('MOVE Nombre.de.jours / 365', 'MOVE FLOORDIV(Nombre.de.jours, 365)'),
            ],
            (None, os.path.join('bib', 'bibcalcul', 'bibcalculecheancierinst.bib')): [
                ('THEN\tMOVE 12 / Periodicite.echeance.verse OF PROCEDURE \tTO Periodicite.cp OF PROCEDURE', 'THEN\tMOVE FLOORDIV(12, Periodicite.echeance.verse OF PROCEDURE) \tTO Periodicite.cp OF PROCEDURE'),
                ('THEN\tMOVE 1 / Periodicite.echeance.verse OF PROCEDURE  \tTO Periodicite.cp OF PROCEDURE', 'THEN\tMOVE FLOORDIV(1, Periodicite.echeance.verse OF PROCEDURE)  \tTO Periodicite.cp OF PROCEDURE'),
                ('THEN\tMOVE 1 / Periodicite.echeance.recu OF PROCEDURE  \tTO Periodicite.cp OF PROCEDURE', 'THEN\tMOVE FLOORDIV(1, Periodicite.echeance.recu OF PROCEDURE)  \tTO Periodicite.cp OF PROCEDURE'),
                ('THEN\tMOVE 12 / Periodicite.echeance.recu OF PROCEDURE \tTO Periodicite.cp OF PROCEDURE', 'THEN\tMOVE FLOORDIV(12, Periodicite.echeance.recu OF PROCEDURE) \tTO Periodicite.cp OF PROCEDURE'),
            ],
            (None, os.path.join('bib', 'bibcalcul', 'bibcalculinteretsswap.bib')): [
                ('MOVE 1 / Periodicite.echeance.verse OF PROCEDURE TO Periodicite.cp.ech.verse OF PROCEDURE', 'MOVE FLOORDIV(1, Periodicite.echeance.verse OF PROCEDURE) TO Periodicite.cp.ech.verse OF PROCEDURE'),
                ('MOVE 12 / Periodicite.echeance.recu OF PROCEDURE TO Periodicite.cp.ech.recu OF PROCEDURE', 'MOVE FLOORDIV(12, Periodicite.echeance.recu OF PROCEDURE) TO Periodicite.cp.ech.recu OF PROCEDURE'),
                ('MOVE 1 / Periodicite.echeance.recu OF PROCEDURE TO Periodicite.cp.ech.recu OF PROCEDURE', 'MOVE FLOORDIV(1, Periodicite.echeance.recu OF PROCEDURE) TO Periodicite.cp.ech.recu OF PROCEDURE'),
                ('MOVE 12 / Periodicite.echeance.verse OF PROCEDURE TO Periodicite.cp.ech.verse OF PROCEDURE', 'MOVE FLOORDIV(12, Periodicite.echeance.verse OF PROCEDURE) TO Periodicite.cp.ech.verse OF PROCEDURE'),
            ],
            (None, os.path.join('bib', 'bibconsult', 'bibconsultdatearretecnpecran.bib')): [
                ('MOVE (  (CPEG.numero-  (CPEG.numero MOD 17)) / 17 ) * 17 + 1 TO CPEG.lecture', 'MOVE FLOORDIV(CPEG.numero - (CPEG.numero MOD 17), 17) * 17 + 1 TO CPEG.lecture'),
            ],
            (None, os.path.join('bib', 'bibconsult', 'bibconsultdatedelhdgecran.bib')): [
                ('MOVE (  (CPEG.numero-  (CPEG.numero MOD 17)) / 17 ) * 17 + 1 TO CPEG.lecture', 'MOVE FLOORDIV(CPEG.numero - (CPEG.numero MOD 17), 17) * 17 + 1 TO CPEG.lecture'),
            ],
            (None, os.path.join('bib', 'bibconsult', 'bibconsultdatefindemoiscnpsuipdd.bib')): [
                ('MOVE (  (CPEG.numero-  (CPEG.numero MOD 17)) / 17 ) * 17 + 1 TO CPEG.lecture', 'MOVE FLOORDIV(CPEG.numero - (CPEG.numero MOD 17), 17) * 17 + 1 TO CPEG.lecture'),
            ],
            (None, os.path.join('bib', 'bibconsult', 'bibconsultdatevaloecraninvref.bib')): [
                ('MOVE (  (CPEG.numero-  (CPEG.numero MOD 17)) / 17 ) * 17 + 1 TO CPEG.lecture', 'MOVE FLOORDIV(CPEG.numero - (CPEG.numero MOD 17), 17) * 17 + 1 TO CPEG.lecture'),
            ],
            (None, os.path.join('bib', 'bibconsult', 'bibconsultnumeroticketdelhdgecran.bib')): [
                ('MOVE (  (CPEG.numero-  (CPEG.numero MOD 17)) / 17 ) * 17 + 1 TO CPEG.lecture', 'MOVE FLOORDIV(CPEG.numero - (CPEG.numero MOD 17), 17) * 17 + 1 TO CPEG.lecture'),
            ],
            (None, os.path.join('bib', 'bibconsult', 'bibconsulttypedate.bib')): [
                ('MOVE (  (CPEG.numero-  (CPEG.numero MOD 17)) / 17 ) * 17 + 1 TO CPEG.lecture', 'MOVE FLOORDIV(CPEG.numero - (CPEG.numero MOD 17), 17) * 17 + 1 TO CPEG.lecture'),
            ],
            (None, os.path.join('bib', 'bibsaisie', 'bibsaisiediffvlcmcic.bib')): [
                ('MOVE (1 + ((Nb.vl - 1) / 12)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.vl - 1, 12)) TO Nb.page.max'),
            ],
            (None, os.path.join('bib', 'bibsaisie', 'bibsaisielistedelhdg.bib')): [
                ('MOVE (1 + ((Nb.vl - 1) / 12)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.vl - 1, 12)) TO Nb.page.max'),
            ],
            (None, os.path.join('bib', 'bibsaisie', 'bibsaisielisteobjetecranmajuni.bib')): [
                ('MOVE (1 + ((Nb.majuni - 1) / 8)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.majuni - 1, 8)) TO Nb.page.max'),
            ],
            (None, os.path.join('bib', 'bibsaisie', 'bibsaisielisteodlv4.bib')): [
                ('MOVE ((NB.comptes.tmp + 1)/2) AS Nb.total.pages TO Nb.total.pages', 'MOVE FLOORDIV(NB.comptes.tmp + 1, 2) AS Nb.total.pages TO Nb.total.pages'),
                ('MOVE ((Numero.ecriture.max + 1)/2) TO Nb.total.pages OF PROCEDURE', 'MOVE FLOORDIV(Numero.ecriture.max + 1, 2) TO Nb.total.pages OF PROCEDURE'),
            ],
            (None, os.path.join('bib', 'bibsaisie', 'bibsaisienewecrancutoff.bib')): [
                ('MOVE (1 + ((Nb.cutoff - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.cutoff - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('bib', 'others', 'bibcommunvalivldvlvl.bib')): [
                ('MOVE (1 + ((Nb.vl - 1) / 12)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.vl - 1, 12)) TO Nb.page.max'),
            ],
            (None, os.path.join('bib', 'others', 'bibcommunvldiasdvlias.bib')): [
                ('MOVE (1 + ((Nb.vl - 1) / 12)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.vl - 1, 12)) TO Nb.page.max'),
            ],
            (None, os.path.join('bib', 'others', 'bibcommunvldmuldvlmul.bib')): [
                ('MOVE (1 + ((Nb.vl - 1) / 12)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.vl - 1, 12)) TO Nb.page.max'),
            ],
            (None, os.path.join('bib', 'others', 'bibconstructionsoumissionbatch.bib')): [
                ('MOVE Num.ptf / Taille.lot TO Taille.lot', 'MOVE FLOORDIV(Num.ptf, Taille.lot) TO Taille.lot'),
            ],
            (None, os.path.join('bib', 'others', 'bibetatlissas.bib')): [
                ("PRINT TO ETAT @TAB TO COL1, '|',@TAB TO (OSE.LARGEUR.ETAT/2), '|',@TAB TO OSE.LARGEUR.ETAT, '|'", "PRINT TO ETAT @TAB TO COL1, '|',@TAB TO FLOORDIV(OSE.LARGEUR.ETAT, 2), '|',@TAB TO OSE.LARGEUR.ETAT, '|'"),
                (',@TAB TO (OSE.LARGEUR.ETAT/2)-7, "Numero"', ',@TAB TO FLOORDIV(OSE.LARGEUR.ETAT, 2)-7, "Numero"'),
                (',@TAB TO (OSE.LARGEUR.ETAT/4), Ligne.message', ',@TAB TO FLOORDIV(OSE.LARGEUR.ETAT, 4), Ligne.message'),
                (',@TAB TO (3*(OSE.LARGEUR.ETAT/4)), "Lignes de message"', ',@TAB TO (3*FLOORDIV(OSE.LARGEUR.ETAT, 4)), "Lignes de message"'),
                (',@TAB TO (OSE.LARGEUR.ETAT/4), "Lignes de message"', ',@TAB TO FLOORDIV(OSE.LARGEUR.ETAT, 4), "Lignes de message"'),
                (',@TAB TO (OSE.LARGEUR.ETAT/2)+3, "Nom des champs"', ',@TAB TO FLOORDIV(OSE.LARGEUR.ETAT, 2)+3, "Nom des champs"'),
            ],
            (None, os.path.join('bib', 'others', 'bibinfodescecheancierinstnewrev.bib')): [
                ("'S':\tMOVE 2 / CPC.periodicite TO CPC.periodicite.retour\t\t! Semestre", "'S':\tMOVE FLOORDIV(2, CPC.periodicite) TO CPC.periodicite.retour\t\t! Semestre"),
                ("'M':\tMOVE 12 / CPC.periodicite TO CPC.periodicite.retour\t\t! Mois", "'M':\tMOVE FLOORDIV(12, CPC.periodicite) TO CPC.periodicite.retour\t\t! Mois"),
                ("'T':\tMOVE 4 / CPC.periodicite TO CPC.periodicite.retour\t\t! Trimestre", "'T':\tMOVE FLOORDIV(4, CPC.periodicite) TO CPC.periodicite.retour\t\t! Trimestre"),
                ("'A':\tMOVE 1 / CPC.periodicite TO CPC.periodicite.retour\t\t! Annee", "'A':\tMOVE FLOORDIV(1, CPC.periodicite) TO CPC.periodicite.retour\t\t! Annee"),
            ],
            (None, os.path.join('mag', 'bib', 'interface', 'dumcri', 'commun', 'bib_interface_dumcri_commun.adl')): [
                ('MOVE NBTmp / 10 + 1  TO  NumPage.c', 'MOVE FLOORDIV(NBTmp, 10) + 1  TO  NumPage.c'),
            ],
            (None, os.path.join('mag', 'bib', 'param', 'dumcre', 'cdc', 'bib_param_dumcre_cdc.adl')): [
                ("LEFT.TRIM((MT15.max/1000 AS '18ZN') AS '23C') + ' !') AS Lib.anomalie TO Lib.anomalie", "LEFT.TRIM((FLOORDIV(MT15.max, 1000) AS '18ZN') AS '23C') + ' !') AS Lib.anomalie TO Lib.anomalie"),
            ],
            (None, os.path.join('mag', 'bib', 'parametre', 'interface', 'cacl', 'bib_parametre_interface_cacl.adl')): [
                ('MOVE ZL.corpsnombre/10 AS ZL.corpsnombre TO ZL.corpsnombre', 'MOVE FLOORDIV(ZL.corpsnombre, 10) AS ZL.corpsnombre TO ZL.corpsnombre'),
            ],
            (None, os.path.join('mag', 'bib', 'param', 'ost', 'valeur', 'bib_param_ost_valeur.adl')): [
                ('MOVE Compteur/100 AS Compteur.arrondi TO Compteur.arrondi', 'MOVE FLOORDIV(Compteur, 100) AS Compteur.arrondi TO Compteur.arrondi'),
            ],
            (None, os.path.join('mag', 'newport', 'caisbl', 'treprv', 'newport_caisbl_treprv.adl')): [
                ('MOVE LENGTH(LTDP.Champ.a.decomposer)/3 \tTO No.dern.date OF PROCEDURE', 'MOVE FLOORDIV(LENGTH(LTDP.Champ.a.decomposer), 3) \tTO No.dern.date OF PROCEDURE'),
            ],
            (None, os.path.join('mag', 'newport', 'cnp', 'ctlacav', 'newport_cnp_ctlacav.adl')): [
                ('PRINT @TAB TO ((OSE.LARGEUR.ETAT/2) AS \'3N\' - 18),"Tri par valeur puis par portefeuille",@cr,@cr', 'PRINT @TAB TO (FLOORDIV(OSE.LARGEUR.ETAT, 2) AS \'3N\' - 18),"Tri par valeur puis par portefeuille",@cr,@cr'),
                ('PRINT @TAB TO ((OSE.LARGEUR.ETAT/2) AS \'3N\' - 18),"Tri par portefeuille puis par valeur",@cr,@cr', 'PRINT @TAB TO (FLOORDIV(OSE.LARGEUR.ETAT, 2) AS \'3N\' - 18),"Tri par portefeuille puis par valeur",@cr,@cr'),
            ],
            (None, os.path.join('mag', 'newport', 'efa', 'ficpoo', 'newport_efa_ficpoo.adl')): [
                ('MOVE Numero.gen / 12 + 1 \tTO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12) + 1 \tTO Numero.courant'),
                ('MOVE Numero.eve / 12 + 1 \tTO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12) + 1 \tTO Numero.courant'),
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
            ],
            (None, os.path.join('mag', 'newport', 'etastk', 'consul', 'open', 'newport_etastk_consul_open.adl')): [
                ('MOVE Largest.ligne / 10 TO Numero TRUNCATED', 'MOVE FLOORDIV(Largest.ligne, 10) TO Numero TRUNCATED'),
            ],
            (None, os.path.join('mag', 'newport', 'eurovl', 'calprm', 'newport_eurovl_calprm.adl')): [
                ('MOVE 12/Periodicite.calcul TO Nb.month', 'MOVE FLOORDIV(12, Periodicite.calcul) TO Nb.month'),
                ('ADD 12/Periodicite.calcul TO Nb.month', 'ADD FLOORDIV(12, Periodicite.calcul) TO Nb.month'),
            ],
            (None, os.path.join('mag', 'newport', 'eurovl', 'cathdg', 'newport_eurovl_cathdg.adl')): [
                ('ADD 12/Periodicite.calcul TO Nb.month', 'ADD FLOORDIV(12, Periodicite.calcul) TO Nb.month'),
            ],
            (None, os.path.join('mag', 'newport', 'eurovl', 'majrmt', 'newport_eurovl_majrmt.adl')): [
                ('MOVE (Nombre.de.lignes) / 9 TO Num.max', 'MOVE FLOORDIV(Nombre.de.lignes, 9) TO Num.max'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'front2', 'chkses', 'newport_front2_chkses.adl')): [
                ('MOVE (Nombre.de.valeurs) / 9 TO Num.max', 'MOVE FLOORDIV(Nombre.de.valeurs, 9) TO Num.max'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'front2', 'opatra2', 'newport_front2_opatra2.adl')): [
                ("MOVE (CTE.Ecart.time/(24 * 3600)) AS '2N'", "MOVE FLOORDIV(CTE.Ecart.time, 24 * 3600) AS '2N'"),
            ],
            (None, os.path.join('mag', 'newport', 'gesaop', 'indtab', 'newport_gesaop_indtab.adl')): [
                ('MOVE Index. / 12  + 1 TO Numero.courant ECHO', 'MOVE FLOORDIV(Index., 12)  + 1 TO Numero.courant ECHO'),
                ('MOVE (Index. /12)  TO Numero.max ECHO', 'MOVE FLOORDIV(Index., 12)  TO Numero.max ECHO'),
                ('MOVE (Index. /12) + 1 TO Numero.max ECHO', 'MOVE FLOORDIV(Index., 12) + 1 TO Numero.max ECHO'),
            ],
            (None, os.path.join('mag', 'newport', 'gesaop', 'lissas', 'newport_gesaop_lissas.adl')): [
                ('@TAB TO (OSE.LARGEUR.ETAT/2)+3, Nom.champ', '@TAB TO FLOORDIV(OSE.LARGEUR.ETAT, 2)+3, Nom.champ'),
                (',@TAB TO (3 * (OSE.LARGEUR.ETAT/4)), Ligne.message', ',@TAB TO (3 * FLOORDIV(OSE.LARGEUR.ETAT, 4)), Ligne.message'),
            ],
            (None, os.path.join('mag', 'newport', 'gesaop', 'majcfao', 'newport_gesaop_majcfao.adl')): [
                ('MOVE Numero.AO.index / 8  + 1 TO Numero.courant ECHO', 'MOVE FLOORDIV(Numero.AO.index, 8)  + 1 TO Numero.courant ECHO'),
                ('MOVE (Numero.ao.index /8) + 1 TO Numero.max ECHO', 'MOVE FLOORDIV(Numero.ao.index, 8) + 1 TO Numero.max ECHO'),
                ('MOVE (Numero.ao.index /8) TO Numero.max ECHO', 'MOVE FLOORDIV(Numero.ao.index, 8) TO Numero.max ECHO'),
            ],
            (None, os.path.join('mag', 'newport', 'gesbdf', 'titbdf2', 'newport_gesbdf_titbdf2.adl')): [
                ('PRINT TO ETAT @tab to COL1 +(ose.largeur.etat-length(ce.chaine))/2,ce.chaine', 'PRINT TO ETAT @tab to COL1 +FLOORDIV(ose.largeur.etat-length(ce.chaine), 2),ce.chaine'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'extcrs', 'newport_gescou_extcrs.adl')): [
                ('"at now + ",secondes.attente/60 AS \'NNN\'," minute << \'!ATEOF!\'"', '"at now + ",FLOORDIV(secondes.attente, 60) AS \'NNN\'," minute << \'!ATEOF!\'"'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'foranx', 'newport_gescou_foranx.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'forcou', 'newport_gescou_forcou.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'forcpa', 'newport_gescou_forcpa.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'forctm', 'newport_gescou_forctm.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'fordvp', 'newport_gescou_fordvp.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 10)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 10)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'fordvs', 'newport_gescou_fordvs.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'fordvt', 'newport_gescou_fordvt.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 8)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 8)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'forext', 'newport_gescou_forext.adl')): [
                ('MOVE (1 + ((Nb.valeurs of procedure - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs of procedure - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'foroff', 'newport_gescou_foroff.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'forpos', 'newport_gescou_forpos.adl')): [
                ('MOVE (Nombre.de.lignes) / 9 TO Num.max', 'MOVE FLOORDIV(Nombre.de.lignes, 9) TO Num.max'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'forprm', 'newport_gescou_forprm.adl')): [
                ('LET Compteur.Page.Frm = ( ( Ligne.Courante / 13 + 1 ) AS Compteur.Page.Frm )', 'LET Compteur.Page.Frm = ( ( FLOORDIV(Ligne.Courante, 13) + 1 ) AS Compteur.Page.Frm )'),
                ('MOVE ( ( ( Ose.Index / 10 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm', 'MOVE ( ( FLOORDIV( Ose.Index, 10 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'lisspr', 'newport_gescou_lisspr.adl')): [
                (",@TAB TO COL.FR7 + (COL.FR8 - COL.FR7 - 5)/2, 'Taux'", ",@TAB TO COL.FR7 + FLOORDIV(COL.FR8 - COL.FR7 - 5, 2), 'Taux'"),
                (',@TAB TO COL.FR6 + (COL.FR7 - COL.FR6 - 8)/2, Date.spread', ',@TAB TO COL.FR6 + FLOORDIV(COL.FR7 - COL.FR6 - 8, 2), Date.spread'),
                (",@TAB TO COL.FR6 + (COL.FR7- COL.FR6 - 4)/2, 'Date'", ",@TAB TO COL.FR6 + FLOORDIV(COL.FR7- COL.FR6 - 4, 2), 'Date'"),
                (',@TAB TO COL.FR7 + (COL.FR8 - COL.FR7 - 10)/2, Spread', ',@TAB TO COL.FR7 + FLOORDIV(COL.FR8 - COL.FR7 - 10, 2), Spread'),
            ],
            (None, os.path.join('mag', 'newport', 'gescou', 'valinv', 'newport_gescou_valinv.adl')): [
                ('MOVE (1 + ((Nb.vl - 1) / 12)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.vl - 1, 12)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gescpt', 'etatram', 'newport_gescpt_etatram.adl')): [
                ('PRINT @TAB TO ((OSE.LARGEUR.ETAT - LENGTH(Lib.etat.1))/2),TRIM (Lib.etat.1),@CR', 'PRINT @TAB TO FLOORDIV(OSE.LARGEUR.ETAT - LENGTH(Lib.etat.1), 2),TRIM (Lib.etat.1),@CR'),
                ('PRINT @TAB TO ((OSE.LARGEUR.ETAT - LENGTH(Lib.etat.3))/2),TRIM (Lib.etat.3),@CR', 'PRINT @TAB TO FLOORDIV(OSE.LARGEUR.ETAT - LENGTH(Lib.etat.3), 2),TRIM (Lib.etat.3),@CR'),
                ('PRINT @TAB TO ((OSE.LARGEUR.ETAT - LENGTH(Lib.etat.2))/2),TRIM (Lib.etat.2),@CR', 'PRINT @TAB TO FLOORDIV(OSE.LARGEUR.ETAT - LENGTH(Lib.etat.2), 2),TRIM (Lib.etat.2),@CR'),
            ],
            (None, os.path.join('mag', 'newport', 'gesdcr', 'defsja', 'newport_gesdcr_defsja.adl')): [
                ('MOVE (Nombre.de.valeurs) / 9 TO Num.max', 'MOVE FLOORDIV(Nombre.de.valeurs, 9) TO Num.max'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'gesfis', 'bastis', 'newport_gesfis_bastis.adl')): [
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12)  + 1 TO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'gesfis', 'brpfis', 'newport_gesfis_brpfis.adl')): [
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12)  + 1 TO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'gesfis', 'forfis', 'newport_gesfis_forfis.adl')): [
                ('MOVE ((((Nb.valeurs OF PROCEDURE - 1) / Tableau.max) AS Nb.page.max) + 1) TO Nb.page.max', 'MOVE ((FLOORDIV(Nb.valeurs OF PROCEDURE - 1, Tableau.max) AS Nb.page.max) + 1) TO Nb.page.max'),
                ('MOVE (((Nb.valeurs OF PROCEDURE / Tableau.max) AS Nb.page.max) + 1) TO Nb.page.max', 'MOVE ((FLOORDIV(Nb.valeurs OF PROCEDURE, Tableau.max) AS Nb.page.max) + 1) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesfis', 'parfof', 'newport_gesfis_parfof.adl')): [
                ('MOVE (1 + ((Nb.ligne.max - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.ligne.max - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesfis', 'tisav', 'newport_gesfis_tisav.adl')): [
                ('LET Compteur.Page.Frm = ( ( Ligne.Courante / 9 + 1 ) AS Compteur.Page.Frm )', 'LET Compteur.Page.Frm = ( ( FLOORDIV(Ligne.Courante, 9) + 1 ) AS Compteur.Page.Frm )'),
                ('MOVE ( ( ( Ose.Index / 9 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm', 'MOVE ( ( FLOORDIV( Ose.Index , 9 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm'),
            ],
            (None, os.path.join('mag', 'newport', 'gesgbr', 'echufs', 'newport_gesgbr_echufs.adl')): [
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12)  + 1 TO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'gesind', 'defind', 'newport_gesind_defind.adl')): [
                ('MOVE (Nombre.de.valeurs) / 9 TO Num.max', 'MOVE FLOORDIV(Nombre.de.valeurs, 9) TO Num.max'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'gesita', 'lim810', 'newport_gesita_lim810.adl')): [
                (', @TAB TO COL2-(COL2-COL1)/2, Code.valeur', ', @TAB TO COL2-FLOORDIV(COL2-COL1, 2), Code.valeur'),
                (', @TAB TO COL2-(COL2-COL1)/2, Code.emetteur', ', @TAB TO COL2-FLOORDIV(COL2-COL1, 2), Code.emetteur'),
            ],
            (None, os.path.join('mag', 'newport', 'gesopc', 'calval', 'newport_gesopc_calval.adl')): [
                ('MOVE (1 + ((Nb.valeurs.max OF PROCEDURE - 1) / 12)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs.max OF PROCEDURE - 1, 12)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesopc', 'compor', 'newport_gesopc_compor.adl')): [
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12) + 1 TO Numero.courant'),
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesopc', 'echrbt', 'newport_gesopc_echrbt.adl')): [
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesopc', 'lnkpti', 'newport_gesopc_lnkpti.adl')): [
                ('MOVE (Nombre.de.valeurs) / 9 TO NUM.MAX', 'MOVE FLOORDIV(Nombre.de.valeurs, 9) TO NUM.MAX'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'gesopc', 'majfrp', 'newport_gesopc_majfrp.adl')): [
                ('MOVE ((Numero.maximum / 8) AS Numero.page.max.affichage) + 1 TO Numero.page.max.affichage', 'MOVE (FLOORDIV(Numero.maximum, 8) AS Numero.page.max.affichage) + 1 TO Numero.page.max.affichage'),
                ('MOVE ((Numero.maximum / 8) AS Numero.page.max.affichage) TO Numero.page.max.affichage', 'MOVE (FLOORDIV(Numero.maximum, 8) AS Numero.page.max.affichage) TO Numero.page.max.affichage'),
            ],
            (None, os.path.join('mag', 'newport', 'gesopc', 'parfri', 'newport_gesopc_parfri.adl')): [
                ('MOVE ( ( ( Ose.Index / 9 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm', 'MOVE ( ( FLOORDIV( Ose.Index, 9 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm'),
                ('MOVE ( ( Ose.Index / 9 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm', 'MOVE ( FLOORDIV( Ose.Index, 9 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm'),
                ('LET Compteur.Page.Frm = ( ( Ligne.Courante / 9 + 1 ) AS Compteur.Page.Frm )', 'LET Compteur.Page.Frm = ( ( FLOORDIV(Ligne.Courante, 9) + 1 ) AS Compteur.Page.Frm )'),
            ],
            (None, os.path.join('mag', 'newport', 'gesopc', 'valo', 'saifor', 'newport_gesopc_valo_saifor.adl')): [
                ('MOVE (1 + (Nb.devises.valo - 1) / 3) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.devises.valo - 1, 3)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'majvwf', 'newport_gespes_majvwf.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 8)) AS Nb.pages TO Nb.pages', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 8)) AS Nb.pages TO Nb.pages'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 8)) TO Nb.pages', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 8)) TO Nb.pages'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wflafc', 'newport_gespes_wflafc.adl')): [
                ('MOVE (((Nb.valeurs OF PROCEDURE / Tableau.max) AS Nb.page.max) + 1) TO Nb.page.max', 'MOVE ((FLOORDIV(Nb.valeurs OF PROCEDURE, Tableau.max) AS Nb.page.max) + 1) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wflafv', 'newport_gespes_wflafv.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) TO Nb.page.max'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) AS Nb.page.max TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) AS Nb.page.max TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wflcla', 'newport_gespes_wflcla.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 5)) TO Nb.page.max', 'MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 5)) TO Nb.page.max'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 5)) AS Nb.page.max TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 5)) AS Nb.page.max TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wflthd', 'newport_gespes_wflthd.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) TO Nb.page.max'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) AS Nb.page.max TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) AS Nb.page.max TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wflthr', 'newport_gespes_wflthr.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) TO Nb.page.max'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) AS Nb.page.max TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) AS Nb.page.max TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wflths', 'newport_gespes_wflths.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) TO Nb.page.max'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) AS Nb.page.max TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) AS Nb.page.max TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wflvar', 'newport_gespes_wflvar.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) TO Nb.page.max'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) AS Nb.page.max TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) AS Nb.page.max TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wtfcla', 'newport_gespes_wtfcla.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 5)) TO Nb.page.max', 'MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 5)) TO Nb.page.max'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 5)) AS Nb.page.max TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 5)) AS Nb.page.max TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gespes', 'wtfvar', 'newport_gespes_wtfvar.adl')): [
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) TO Nb.page.max'),
                ('MOVE (1 + ((Nb.valeurs OF PROCEDURE - 1) / 10)) AS Nb.page.max TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs OF PROCEDURE - 1, 10)) AS Nb.page.max TO Nb.page.max'),
            ],
            (184318, os.path.join('mag', 'newport', 'gespor', 'duppor', 'newport_gespor_duppor.adl')): [
                ('MOVE Numero.eve / 10  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 10)  + 1 TO Numero.courant'),
                ('MOVE Numero.eve / 10 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 10) TO Num.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesprt', 'etaper', 'newport_gesprt_etaper.adl')): [
                ('LET CALCUL.NO.TRIMESTRE = 4 * YEAR(Mois.echeance1) + (MONTH(Mois.echeance1) + 2) / 3', 'LET CALCUL.NO.TRIMESTRE = 4 * YEAR(Mois.echeance1) + FLOORDIV(MONTH(Mois.echeance1) + 2, 3)'),
            ],
            (None, os.path.join('mag', 'newport', 'gesrat', 'defcor', 'newport_gesrat_defcor.adl')): [
                ('MOVE (Nombre.de.valeurs) / 9 TO Num.max', 'MOVE FLOORDIV(Nombre.de.valeurs, 9) TO Num.max'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'gesrat', 'limsog', 'newport_gesrat_limsog.adl')): [
                (', @TAB TO COL2-(COL2-COL1)/2, Code.valeur', ', @TAB TO COL2-FLOORDIV(COL2-COL1, 2), Code.valeur'),
                (', @TAB TO COL2-(COL2-COL1)/2, Code.emetteur', ', @TAB TO COL2-FLOORDIV(COL2-COL1, 2), Code.emetteur'),
            ],
            (None, os.path.join('mag', 'newport', 'gesrat', 'ordreg', 'newport_gesrat_ordreg.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesrep', 'suirep', 'newport_gesrep_suirep.adl')): [
                ("MOVE Nb.exportes*100/Nb.portefeuille AS '2ZN' TO Pc.exportes", "MOVE FLOORDIV(Nb.exportes*100,Nb.portefeuille) AS '2ZN' TO Pc.exportes"),
                ("MOVE Nb.valides*100/Nb.portefeuille AS '2ZN' TO Pc.valides", "MOVE FLOORDIV(Nb.valides*100,Nb.portefeuille) AS '2ZN' TO Pc.valides"),
                ("MOVE Nb.calcules*100/Nb.portefeuille AS '2ZN' TO Pc.calcules", "MOVE FLOORDIV(Nb.calcules*100,Nb.portefeuille) AS '2ZN' TO Pc.calcules"),
                ("MOVE Nb.certifies*100/Nb.portefeuille AS '2ZN' TO Pc.certifies", "MOVE FLOORDIV(Nb.certifies*100,Nb.portefeuille) AS '2ZN' TO Pc.certifies"),
            ],
            (None, os.path.join('mag', 'newport', 'gessba', 'deffin', 'newport_gessba_deffin.adl')): [
                ('MOVE (Nombre.de.valeurs) / 9 TO Num.max', 'MOVE FLOORDIV(Nombre.de.valeurs, 9) TO Num.max'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'gessba', 'majsba', 'newport_gessba_majsba.adl')): [
                ('MOVE 12 / TDPM.Periodicite TO Periodicite.cp OF PROCEDURE', 'MOVE FLOORDIV(12, TDPM.Periodicite) TO Periodicite.cp OF PROCEDURE'),
                ('MOVE 1 / TDPM.Periodicite TO Periodicite.cp OF PROCEDURE', 'MOVE FLOORDIV(1, TDPM.Periodicite) TO Periodicite.cp OF PROCEDURE'),
            ],
            (None, os.path.join('mag', 'newport', 'gestab', 'liscal', 'newport_gestab_liscal.adl')): [
                ("LET Decalage.init = ((218 - Largeur.etat) / 2) AS '3N'", "LET Decalage.init = FLOORDIV(218 - Largeur.etat, 2) AS '3N'"),
            ],
            (None, os.path.join('mag', 'newport', 'gestau', 'fortin', 'newport_gestau_fortin.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'dvlost', 'newport_gestra_dvlost.adl')): [
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12)  + 1 TO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'echamd', 'newport_gestra_echamd.adl')): [
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 12 + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12) + 1 TO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'echufg', 'newport_gestra_echufg.adl')): [
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12)  + 1 TO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'forlac', 'newport_gestra_forlac.adl')): [
                ('LET Compteur.Page.Frm = ( ( Ligne.Courante / 12 + 1 ) AS Compteur.Page.Frm )', 'LET Compteur.Page.Frm = ( ( FLOORDIV(Ligne.Courante, 12) + 1 ) AS Compteur.Page.Frm )'),
                ('MOVE ( ( ( Ose.Index / 10 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm', 'MOVE ( ( FLOORDIV( Ose.Index, 10 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'forobj', 'newport_gestra_forobj.adl')): [
                ('LET Compteur.Page.Frm = ( ( Ligne.Courante / 12 + 1 ) AS Compteur.Page.Frm )', 'LET Compteur.Page.Frm = ( ( FLOORDIV(Ligne.Courante, 12) + 1 ) AS Compteur.Page.Frm )'),
                ('MOVE (1 + ((Ose.Index - 1) / 12)) TO Nb.page.max.frm', 'MOVE (1 + FLOORDIV(Ose.Index - 1, 12)) TO Nb.page.max.frm'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'fortvi', 'newport_gestra_fortvi.adl')): [
                ('MOVE ( ( ( Ose.Index / 10 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm', 'MOVE ( ( FLOORDIV( Ose.Index , 10 ) + 1 ) AS Nb.Page.Max.Frm ) TO Nb.Page.Max.Frm'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'genost', 'newport_gestra_genost.adl')): [
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
                ('MOVE Numero.eve / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 12  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12)  + 1 TO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'gracol', 'newport_gestra_gracol.adl')): [
                ('MOVE ABS(((Index.tableau.max-1)/12)+1) TO Nb.page.max', 'MOVE ABS(FLOORDIV(Index.tableau.max-1, 12)+1) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'grappe', 'newport_gestra_grappe.adl')): [
                ('MOVE ABS(((Index.tableau.max-1)/12)+1) TO Nb.page.max', 'MOVE ABS(FLOORDIV(Index.tableau.max-1, 12)+1) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'hobbil', 'newport_gestra_hobbil.adl')): [
                ('MOVE Numero.eve / 13 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 13) TO Num.max'),
                ('MOVE Numero.eve / 13  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 13)  + 1 TO Numero.courant'),
                ('MOVE Numero.gen / 13  + 1 TO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 13)  + 1 TO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'gestra', 'juscapi', 'newport_gestra_juscapi.adl')): [
                ('MOVE (MONTH(RT.Date) - 1)/3 TO Numero.bulletin TRUNCATED', 'MOVE FLOORDIV(MONTH(RT.Date) - 1, 3) TO Numero.bulletin TRUNCATED'),
                ('MOVE ((MONTH(Date.bulletin) - 1)/3) TO Numero.bulletin TRUNCATED', 'MOVE FLOORDIV(MONTH(Date.bulletin) - 1, 3) TO Numero.bulletin TRUNCATED'),
            ],
            (None, os.path.join('mag', 'newport', 'gestre', 'impfac', 'newport_gestre_impfac.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesval', 'cararc', 'newport_gesval_cararc.adl')): [
                ('MOVE (  (CPEG.numero-  (CPEG.numero MOD 17)) / 17 ) * 17 + 1 TO CPEG.lecture', 'MOVE FLOORDIV(CPEG.numero - (CPEG.numero MOD 17), 17) * 17 + 1 TO CPEG.lecture'),
            ],
            (None, os.path.join('mag', 'newport', 'gesval', 'carbdf', 'newport_gesval_carbdf.adl')): [
                ('PRINT TO ETAT @tab to COL1 +(ose.largeur.etat-length(ce.chaine))/2,ce.chaine', 'PRINT TO ETAT @tab to COL1 +FLOORDIV(ose.largeur.etat-length(ce.chaine), 2),ce.chaine'),
            ],
            (None, os.path.join('mag', 'newport', 'gesval', 'fortri', 'newport_gesval_fortri.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 11)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 11)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesval', 'placot', 'newport_gesval_placot.adl')): [
                ('MOVE I/10 TO No.page.max', 'MOVE FLOORDIV(I, 10) TO No.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesval', 'placot', 'unix', 'newport_gesval_placot_unix.adl')): [
                ('MOVE I/10 TO No.page.max', 'MOVE FLOORDIV(I, 10) TO No.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'gesval', 'vacsac', 'efa', 'newport_gesval_vacsac_efa.adl')): [
                ('PRINT TO ETAT.SORTIE.UNIX "at now + ",secondes.attente/60 AS \'NNN\'," minute << \'!ATEOF!\'",@cr', 'PRINT TO ETAT.SORTIE.UNIX "at now + ",FLOORDIV(secondes.attente, 60) AS \'NNN\'," minute << \'!ATEOF!\'",@cr'),
            ],
            (None, os.path.join('mag', 'newport', 'lance', 'procedure', 'newport_lance_procedure.adl')): [
                ('MOVE (Memoire.utilisee.entree / 1024) AS Memoire.utilisee.entree TO Memoire.utilisee.entree ! Mega Octet', 'MOVE FLOORDIV(Memoire.utilisee.entree, 1024) AS Memoire.utilisee.entree TO Memoire.utilisee.entree ! Mega Octet'),
            ],
            (None, os.path.join('mag', 'newport', 'lance', 'procedure', 'unix', 'newport_lance_procedure_unix.adl')): [
                ('MOVE (Memoire.utilisee.entree / 1024) AS Memoire.utilisee.entree TO Memoire.utilisee.entree \t! Mega Octet', 'MOVE FLOORDIV(Memoire.utilisee.entree, 1024) AS Memoire.utilisee.entree TO Memoire.utilisee.entree \t! Mega Octet'),
            ],
            (None, os.path.join('mag', 'newport', 'newrev', 'etechu', 'newport_newrev_etechu.adl')): [
                ('@tab to col1 +(ose.largeur.etat-length(ce.chaine))/2,ce.chaine', '@tab to col1 +FLOORDIV(ose.largeur.etat-length(ce.chaine), 2),ce.chaine'),
            ],
            (None, os.path.join('mag', 'newport', 'newrev', 'lechcomp', 'newport_newrev_lechcomp.adl')): [
                ('MOVE OSE.LARGEUR.ETAT / 2 TO Milieu.etat', 'MOVE FLOORDIV(OSE.LARGEUR.ETAT, 2) TO Milieu.etat'),
            ],
            (None, os.path.join('mag', 'newport', 'newrev', 'lisech', 'newport_newrev_lisech.adl')): [
                ('MOVE OSE.LARGEUR.ETAT / 2 TO Milieu.etat', 'MOVE FLOORDIV(OSE.LARGEUR.ETAT, 2) TO Milieu.etat'),
            ],
            (None, os.path.join('mag', 'newport', 'newrev', 'prerev', 'newport_newrev_prerev.adl')): [
                ('@tab to col1 +(ose.largeur.etat-length(ce.chaine))/2,ce.chaine', '@tab to col1 +FLOORDIV(ose.largeur.etat-length(ce.chaine), 2),ce.chaine'),
            ],
            (None, os.path.join('mag', 'newport', 'newrev', 'rearev', 'newport_newrev_rearev.adl')): [
                ('@tab to col1 +(ose.largeur.etat-length(ce.chaine))/2,ce.chaine', '@tab to col1 +FLOORDIV(ose.largeur.etat-length(ce.chaine), 2),ce.chaine'),
            ],
            (None, os.path.join('mag', 'newport', 'newrev', 'treprv', 'newport_newrev_treprv.adl')): [
                ('MOVE LENGTH(LTDP.Champ.a.decomposer)/3 \tTO No.dern.date OF PROCEDURE', 'MOVE FLOORDIV(LENGTH(LTDP.Champ.a.decomposer), 3) \tTO No.dern.date OF PROCEDURE'),
            ],
            (None, os.path.join('mag', 'newport', 'ost', 'eurost', 'newport_ost_eurost.adl')): [
                ('THEN\tMOVE Numero.tableau /10 \t\tTO No.dern.page', 'THEN\tMOVE FLOORDIV(Numero.tableau, 10) \t\tTO No.dern.page'),
                ('ELSE \tMOVE (Numero.tableau [Indice.affichage.max] /10) +1 \t\tTO No.page.1', 'ELSE \tMOVE FLOORDIV(Numero.tableau [Indice.affichage.max], 10) +1 \t\tTO No.page.1'),
                ('ELSE \tMOVE (Numero.tableau /10) +1 \t\tTO No.dern.page', 'ELSE \tMOVE FLOORDIV(Numero.tableau, 10) +1 \t\tTO No.dern.page'),
                ('THEN\tMOVE Numero.tableau [Indice.affichage.max] /10\t\tTO No.page.1', 'THEN\tMOVE FLOORDIV(Numero.tableau [Indice.affichage.max], 10)\t\tTO No.page.1'),
            ],
            (None, os.path.join('mag', 'newport', 'ost', 'isiost', 'newport_ost_isiost.adl')): [
                ('THEN\tMOVE Numero.tableau /10 \t\tTO No.dern.page', 'THEN\tMOVE FLOORDIV(Numero.tableau, 10) \t\tTO No.dern.page'),
                ('ELSE \tMOVE (Numero.tableau [Indice.affichage.max] /10) +1 \t\tTO No.page.1', 'ELSE \tMOVE FLOORDIV(Numero.tableau [Indice.affichage.max], 10) +1 \t\tTO No.page.1'),
                ('ELSE \tMOVE (Numero.tableau /10) +1 \t\tTO No.dern.page', 'ELSE \tMOVE FLOORDIV(Numero.tableau, 10) +1 \t\tTO No.dern.page'),
                ('THEN\tMOVE Numero.tableau [Indice.affichage.max] /10\t\tTO No.page.1', 'THEN\tMOVE FLOORDIV(Numero.tableau [Indice.affichage.max], 10)\t\tTO No.page.1'),
            ],
            (None, os.path.join('mag', 'newport', 'ost', 'ostcou', 'newport_ost_ostcou.adl')): [
                ('MOVE Compteur/100 AS Compteur.arrondi TO Compteur.arrondi', 'MOVE FLOORDIV(Compteur, 100) AS Compteur.arrondi TO Compteur.arrondi'),
            ],
            (None, os.path.join('mag', 'newport', 'ost', 'qteost', 'newport_ost_qteost.adl')): [
                ('THEN\tMOVE Numero.tableau /10 \t\tTO No.dern.page', 'THEN\tMOVE FLOORDIV(Numero.tableau, 10) \t\tTO No.dern.page'),
                ('ELSE \tMOVE (Numero.tableau [Indice.affichage.max] /10) +1 \t\tTO No.page.1', 'ELSE \tMOVE FLOORDIV(Numero.tableau [Indice.affichage.max], 10) +1 \t\tTO No.page.1'),
                ('ELSE \tMOVE (Numero.tableau /10) +1 \t\tTO No.dern.page', 'ELSE \tMOVE FLOORDIV(Numero.tableau, 10) +1 \t\tTO No.dern.page'),
                ('THEN\tMOVE Numero.tableau [Indice.affichage.max] /10\t\tTO No.page.1', 'THEN\tMOVE FLOORDIV(Numero.tableau [Indice.affichage.max], 10)\t\tTO No.page.1'),
            ],
            (None, os.path.join('mag', 'newport', 'pool', 'genpoo', 'newport_pool_genpoo.adl')): [
                ('MOVE Numero.eve / 12  + 1 \t\tTO Numero.courant', 'MOVE FLOORDIV(Numero.eve, 12)  + 1 \t\tTO Numero.courant'),
                ('MOVE Numero.eve / 12 TO Num.max', 'MOVE FLOORDIV(Numero.eve, 12) TO Num.max'),
                ('MOVE Numero.gen / 12  + 1 \t\tTO Numero.courant', 'MOVE FLOORDIV(Numero.gen, 12)  + 1 \t\tTO Numero.courant'),
            ],
            (None, os.path.join('mag', 'newport', 'redbck', 'valivl', 'newport_redbck_valivl.adl')): [
                ('MOVE (1 + ((Nb.vl - 1) / 12)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.vl - 1, 12)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'ubs', 'allpoo', 'newport_ubs_allpoo.adl')): [
                ('MOVE (1 + ((Nb.valeurs - 1) / 14)) TO Nb.page.max', 'MOVE (1 + FLOORDIV(Nb.valeurs - 1, 14)) TO Nb.page.max'),
            ],
            (None, os.path.join('mag', 'newport', 'ubs', 'insblk', 'newport_ubs_insblk.adl')): [
                ('MOVE (Nombre.de.valeurs) / 9 TO Num.max', 'MOVE FLOORDIV(Nombre.de.valeurs, 9) TO Num.max'),
                ('MOVE (Numero.ligne / 9) + 1 TO Page.affichee', 'MOVE FLOORDIV(Numero.ligne, 9) + 1 TO Page.affichee'),
            ],
            (None, os.path.join('mag', 'newport', 'util', 'audit', 'ost', 'newport_util_audit_ost.adl')): [
                ("MOVE ((HEURE.MINUTE / Frequence OF PROCEDURE) AS '5N') * Frequence OF PROCEDURE TO HEURE.MINUTE", "MOVE (FLOORDIV(HEURE.MINUTE, Frequence OF PROCEDURE) AS '5N') * Frequence OF PROCEDURE TO HEURE.MINUTE"),
            ],
            (None, os.path.join('mag', 'newport', 'util', 'lispec', 'newport_util_lispec.adl')): [
                ('@TAB TO (Col1 +(Ose.largeur.etat-LENGTH(Ce.chaine))/2),Ce.chaine,@CR', '@TAB TO (Col1 +FLOORDIV(Ose.largeur.etat-LENGTH(Ce.chaine), 2)),Ce.chaine,@CR'),
            ],
            (None, os.path.join('mag', 'util', 'cmcic', 'distrib', 'ao', 'util_cmcic_distrib_ao.adl')): [
                ('MOVE ARRONDI.MONTANT(Nb.ao.total / Nb.lot,0) AS Nb.ao.moy.par.lot TO Nb.ao.moy.par.lot', 'MOVE ARRONDI.MONTANT(FLOORDIV(Nb.ao.total, Nb.lot),0) AS Nb.ao.moy.par.lot TO Nb.ao.moy.par.lot'),
            ],
        }
        for (fix_revision, rel_path), patterns in data.items():
            if fix_revision is None or revision < fix_revision:
                for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', rel_path)):
                    if os.path.isfile(path):
                        sub_latin1(path, patterns)

    def fix_type_debug(self, schema_version, revision, checkout):
        """
        https://iris.sungard-finance.fr/svn/viewvc/gp/trunk/gp2009/adl/src/bib/bibtraite/bibtraitementmessage.bib?r1=147570&r2=163684
        """
        if revision < 163684:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'bib', 'bibtraite', 'bibtraitementmessage.bib')):
                patterns = (
                    ('AS "254C"', 'AS "250C"'),
                    ('TYPE @CR, TD.LIB', 'TYPE @CR, ">>> ", TD.LIB'),
                )
                sub_latin1(path, patterns)

    def fix_invalid_pictures(self, schema_version, revision, checkout):
        if revision < 159393:
            patterns = (
                ('AS " 2C"', 'AS "2C"'),
                ('AS " 5C"', 'AS "5C"')
            )
            self.fix_checkout(checkout, patterns, False)

    def fix_bibconvertchainedate(self, schema_version, revision, checkout):
        if revision < 155898:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'bib', 'bibconvert', 'bibconvertchainedate.bib')):
                content = get_content(path)
                contents = content.split('"DDMMY":', 1)
                if len(contents) == 2:
                    before, after = contents
                    pattern = 'IF (Cchd.date.saisie AS \'8C\') IS DATE "DD/MM/YY"'
                    if pattern in after:
                        content = before.rstrip() + '\n\t\tEND\n\tELSE\n\t\t' + pattern + after.split(pattern, 1)[1]
                        set_content(path, content)

    def fix_from(self, path, pattern, from_string, to_string):
        content = get_content(path)
        contents = content.split(pattern, 1)
        if len(contents) == 2:
            before, after = contents
            after = after.replace(from_string, to_string)
            set_content(path, before + pattern + after)

    def fix_bibtraitelibellesmlg(self, schema_version, revision, checkout):
        if revision < 151385:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'bib', 'bibtraite', 'bibtraitelibellesmlg.bib')):
                self.fix_from(
                    path,
                    'FUNCTION TRAITE.LIB.MESSAGE.SUP (',
                    'LET TRAITE.LIB.MESSAGE =', 'LET TRAITE.LIB.MESSAGE.SUP =',
                )

    def fix_bibcalculsoldedevise(self, schema_version, revision, checkout):
        if revision < 151605:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'bib', 'bibcalcul', 'bibcalculsoldedevise.bib')):
                self.fix_from(
                    path,
                    'FUNCTION CALCUL.SOLDE.DEVISE.DET',
                    'MOVE Asd.montant TO Calcul.solde.devise', 'MOVE Asd.montant TO Calcul.solde.devise.det',
                )

    def fix_treprv(self, schema_version, revision, checkout):
        if revision < 143240:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'mag', 'newport', 'newrev', 'treprv', 'newport_newrev_treprv.adl')):
                self.fix_from(
                    path,
                    'FUNCTION CONVERT.MONTANT.NUM (',
                    'MOVE DEFAULT TO Convert.montant.chaine', 'MOVE DEFAULT TO CONVERT.MONTANT.NUM',
                )
                self.fix_from(
                    path,
                    'FUNCTION CONVERT.MONTANT.NUM (',
                    ') TO Convert.montant.chaine', ') AS Montant TO CONVERT.MONTANT.NUM',
                )

    def fix_bibcalculmouvementcommun2(self, schema_version, revision, checkout):
        if revision < 137176:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'bib', 'bibcalcul', 'bibcalculmouvementcommun2.bib')):
                self.fix_from(
                    path,
                    'function calcul.quantite()',
                    'MOVE 1 TO Calcul.cours.devise.gestion', 'NOTHING ! MOVE 1 TO Calcul.cours.devise.gestion',
                )

    def fix_invamo(self, schema_version, revision, checkout):
        """
        https://iris.sungard-finance.fr/svn/viewvc/gp?view=rev&revision=154487
        """
        if revision < 154487:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'mag', 'newport', 'etastk', 'invamo', 'newport_etastk_invamo.adl')):
                pattern = 'FUNCTION Recherche.total.primitive'
                content = get_content(path)
                contents = content.split(pattern)
                if len(contents) == 3:
                    first, second, third = contents
                    second = second.replace("LET Recherche.primitive = 'Parametre non reconnu '",
                                            "LET Recherche.total.primitive = 'Parametre non reconnu '")
                    third = third.replace("LET Recherche.primitive = 'Parametre non reconnu '",
                                          "LET Recherche.total.primitive.bis = 'Parametre non reconnu '")
                    set_content(path, pattern.join([first, second, third]))

    def fix_bibverifcode(self, schema_version, revision, checkout):
        """
        https://support.neoxam.com/browse/DTMT-8717
        """
        if revision < 173717:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'bib', 'bibverif', 'bibverifcode.bib')):
                sub_latin1(path, (
                    ("MOVE ((POSITION(VALASCII,VI.Code)+9)/10) AS 'N' TO VI.Numero[VI.J]",
                     "MOVE FLOORDIV((POSITION(VALASCII,VI.Code)+9), 10) AS 'N' TO VI.Numero[VI.J]"),
                ))

    def fix_forcou(self, schema_version, revision, checkout):
        for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'mag', 'newport', 'gescou', 'forcou', 'newport_gescou_forcou.adl')):
            sub_latin1(path, (
                (",TRIM(LEFT.TRIM((Histo.debut.forcage OF PROCEDURE-Histo.fin.forcage OF PROCEDURE+1) AS '4C'))",
                 ",TRIM(LEFT.TRIM(((Histo.debut.forcage OF PROCEDURE-Histo.fin.forcage OF PROCEDURE+1) AS '10Z' ) AS '4C'))"),
            ))

    def fix_eqmouv(self, schema_version, revision, checkout, compiler_version):
        """
        https://support.neoxam.com/browse/DELIA-2402
        """
        if compiler_lt(compiler_version, '1.0.3'):
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'mag', 'newport', 'etastk', 'eqmouv', 'newport_etastk_eqmouv.adl')):
                sub_latin1(path, (
                    ("WHERE (  Code.transaction = Code.transaction OF TRANSACTION.",
                     "VIA ( Code.transaction = Code.transaction OF TRANSACTION. ) WHERE (  Code.transaction = Code.transaction OF TRANSACTION."),
                ))

    def fix_gencal(self, schema_version, revision, checkout):
        """
        https://support.neoxam.com/browse/DTMT-8836
        """
        if revision < 173459:
            for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'mag', 'newport', 'gestab', 'gencal', 'newport_gestab_gencal.adl')):
                sub_latin1(path, (
                    ("LET Numero.ligne = ((W.Base + (Jour.calendrier - Date.ouverture.exercice OF PROCEDURE) AS '4N') / 7)",
                     "LET Numero.ligne = FLOORDIV((W.Base + (Jour.calendrier - Date.ouverture.exercice OF PROCEDURE) AS '4N'), 7)"),
                ))

    def fix_calstc(self, schema_version, revision, checkout):
        """
        https://support.neoxam.com/browse/DTMT-8836
        """
        for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'mag', 'newport', 'clonage', 'calstc', 'newport_clonage_calstc.adl')):
            sub_latin1(path, (
                ("LET Numero.ligne = ((W.Base + (Jour.calendrier - Date.ouverture.exercice OF PROCEDURE) AS '4N') / 7)",
                 "LET Numero.ligne = FLOORDIV((W.Base + (Jour.calendrier - Date.ouverture.exercice OF PROCEDURE) AS '4N'), 7)"),
            ))

    def fix_ost2(self, schema_version, revision, checkout, compiler_version):
        """
        https://support.neoxam.com/browse/DELIA-2433
        """
        if compiler_lt(compiler_version, '0.3.44'):
            for option in ('basost', 'suiost', 'jbaost'):
                for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'mag', 'newport', 'ost2', option, 'newport_ost2_%s.adl' % option)):
                    sub_latin1(path, (
                        ("FOR EACH Impact.ost WHERE Date.effet > Date.",
                         "FOR EACH Impact.ost WHERE Date.effet > Date. SORTED ON Date.effet"),
                    ))

    def fix_majent(self, schema_version, revision, checkout):
        """
        https://support.neoxam.com/browse/DTMT-8783
        """
        for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'mag', 'newport', 'gesint', 'majent', 'newport_gesint_majent.adl')):
            patterns = (
                (
                    "MOVE Date.blocage.pee.ecr AS DATE 'DD/MM' TO Date.blocage.pee OF PROCEDURE",
                    "MOVE Date.blocage.pee.ecr AS DATE 'DD/MM' TO Date.blocage.pee OF PROCEDURE\nMOVE YEAR(TODAY) TO YEAR(Date.blocage.pee OF PROCEDURE)",
                ),
                (
                    "MOVE Date.blocage.part.ecr AS DATE 'DD/MM' TO Date.blocage.part",
                    "MOVE Date.blocage.part.ecr AS DATE 'DD/MM' TO Date.blocage.part\nMOVE YEAR(TODAY) TO YEAR(Date.blocage.part)",
                ),
                (
                    "MOVE Fin.exercice.social.ecr AS DATE 'DD/MM' TO Fin.exercice.social OF PROCEDURE",
                    "MOVE Fin.exercice.social.ecr AS DATE 'DD/MM' TO Fin.exercice.social OF PROCEDURE\nMOVE YEAR(TODAY) TO YEAR(Fin.exercice.social OF PROCEDURE)",
                ),
            )
            sub_latin1(path, patterns)

    def fix_bibcalculjourscalendrier(self, schema_version, revision, checkout):
        for path in glob.glob(os.path.join(checkout, 'gp*', 'adl', 'src', 'bib', 'bibcalcul', 'bibcalculjourscalendrier.bib')):
            patterns = (
                (
                    "MOVE (NJON.date.fin - NJON.date.debut)-((((NJON.date.fin - NJON.date.debut)/7) AS '4N')*7) TO NJON.nb.jours",
                    "MOVE (NJON.date.fin - NJON.date.debut)-((FLOORDIV(NJON.date.fin - NJON.date.debut, 7) AS '4N')*7) TO NJON.nb.jours",
                ),
                (
                    "MOVE (((NJON.date.fin - NJON.date.debut)/7) AS '4N') *5",
                    "MOVE (FLOORDIV(NJON.date.fin - NJON.date.debut, 7) AS '4N') *5",
                ),
            )
            sub_latin1(path, patterns)
