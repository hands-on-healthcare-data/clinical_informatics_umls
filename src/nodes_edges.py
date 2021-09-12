"""
SUMMARY
-------

This .py assumes you are querying the SQLite database found at the relative path ->../sqlite/umls.db. 
This database is created via the following shell script located wthin that same directory. -->../create_sqlite_db. 

The sqlite3 database created contains two tables NOT created via UMLS® MetamorphoSys 
(available to only UMLS license holders). 
    to do: write SQL DDL to create equivalent view or table for MySQL & PostgresSQL dataabse setups

The two additional tables are as follows: [HIERARCHY, MRCONREL]. 
    -> This optiomization reduces dependency of several expensive joins on 3 of the 4 largest tables within UMLS 
    -> [MRHIER, MRREL, MRCONSO]. Please note this will require more local disk space. 
    to do: Include more expensive queries using MRHIER, MRREL & MRCONSO rather than HIERARCHY & MRCONREL.

../sqlite/create_sqlite_db.sh will create a SQLite database within same directory as the script itself.
Additional the database requires ~20GiB available disk space.


"""

import sys
import os
if not sys.warnoptions:               # Do not output warnings unless involves system
    import warnings
    warnings.simplefilter("ignore")
import numpy as np
import pandas as pd
import sqlite3

# import getpass                       # Use to hide creds when using below connections
# import mysql.connector               # MySQL connection
# import psycopg2                      # postgresSQL connection
# from sqlalchemy import create_engine # Need for a postgresSQL connection

# Database Connection Creds & Params:
# **************************************
# user = getpass.getuser()             # Requires getpass (getpass2 from PyPi)
# password = getpass.getpass()         # Requires getpass (getpass2 from PyPi)
# host = ""
# dbname = ""
# **************************************

# Establish database connection using postgresSQL
# engine = create_engine(
#     url=f"postgresql+psycopg2://{user}:{password}@{host}/postgres")

# Establish database connection using MySQL -> to do: Add code for connection object (conn) for MySQL database connection


# Establish database connection using local sqlite3 (using sqlite3 in this script)
db_name = "umls.db"
relative_path_to_sqlite = "../sqlite/"
conn = sqlite3.connect(os.path.join(relative_path_to_sqlite, db_name))


# **************************************************************
# GRAPH LABELS & NODES
# **************************************************************
# Label: SemanticType
# import: semanticsNode.csv
semantic_node = """
                  
                  SELECT DISTINCT TUI            
                                , STY
                                , STN  
                                , 'SemanticType'  AS ":LABEL"
                  FROM MRSTY;
                  
                  """
semanticTypeNode = pd.read_sql_query(
    semantic_node, conn).drop_duplicates().replace(np.nan, '')
semanticTypeNode.columns = ["SemanticTypeId:ID", "sty", "stn", ":LABEL"]
semanticTypeNode.to_csv(path_or_buf="../import/semanticTypeNode.csv",
                        header=True,
                        index=False)
print("SemanticTypeNode.csv successfully written out...")
# **************************************************************
# Label: Concept
# import: conceptNode.csv
concept_node = """
                  
                  SELECT DISTINCT CUI       AS "ConceptId:ID"
                                , STR       AS name
                                , 'Concept' AS ":LABEL"
                  FROM MRCONSO
                  WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
                                'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR', 
                                'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                      AND SUPPRESS = 'N'
                      AND ISPREF = 'Y'
                      AND TS = 'P'
                      AND STT = 'PF';
                      
                      """
conceptNode = pd.read_sql_query(
    concept_node, conn).drop_duplicates().replace(np.nan, '')
conceptNode.to_csv(path_or_buf="../import/conceptNode.csv",
                   header=True,
                   index=False)
print("conceptNode.csv successfully written out...")
# **************************************************************
# Label: Atom
# import: atomNode.csv
atom_node = """

            SELECT DISTINCT AUI                    AS "AtomId:ID"
                          , STR                    AS name
                          , SAB                    AS ontology
                          , TTY                    AS tty
                          , ISPREF                 AS isPref
                          , STT                    AS stt
                          , TS                     AS ts
                          , 'Atom'                 AS ":LABEL"
            FROM MRCONSO 
            WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
                          'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR', 
                          'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                AND SUPPRESS = 'N';
                
                """
atomNode = pd.read_sql_query(atom_node, conn).drop_duplicates([
    'AtomId:ID']).replace(np.nan, "")
atomNode.to_csv(path_or_buf="../import/atomNode.csv",
                header=True,
                index=False)
print("atomNode.csv successfully written out...")
# **************************************************************
# Label: Code
# import: codeNode.csv
code_node = """
               
               SELECT DISTINCT (SAB || '#' || CODE)    AS "CodeId:ID"
                             , SAB                    
                             , STR
                             , CODE
                             , TTY
                             , ('Code' || ';' || SAB)  AS ":LABEL"
               FROM MRCONSO
               WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
                             'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR', 
                             'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                  AND SUPPRESS = 'N';
                  
                  """
codeNode = pd.read_sql_query(code_node, conn).drop_duplicates(
    ['CodeId:ID', 'STR']).replace(np.nan, "")
codeNode.columns = ["CodeId:ID", "ontology", "name", "code", "tty", ":LABEL"]
codeNode.to_csv(path_or_buf="../import/codeNode.csv",
                header=True,
                index=False)
print("codeNode.csv successfully written out...")
# **************************************************************
# Labels: ['ICDO3Code', 'ENSEMBLGENE_ID', 'ENTREZGENE_ID', 'NDC']
# import: attributeNode.csv
atui_node = """

               SELECT DISTINCT ATUI                                AS "AtuiId:ID"
                             , ATV                                 AS attributeCode
                             , STR                                 AS name
                             , CASE 
                                 WHEN ('Attribute' || ';' || ATN) = 'Attribute;ICD-O-3_CODE' 
                                     THEN 'Attribute;ICDO3Code' 
                                   ELSE ('Attribute' || ';' || ATN) 
                                   END                              AS ":LABEL"
               FROM MRSAT sat
                       JOIN MRCONSTY c ON sat.CUI = c.CUI
               WHERE ATN IN ('ICD-O-3_CODE', 'NDC')
                   AND sat.SUPPRESS = 'N'
                   AND sat.SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
                                   'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR',
                                   'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US');
                                   
                                   """
attributeNode = pd.read_sql_query(atui_node, conn).drop_duplicates().replace(
    np.nan, '').sort_values('AtuiId:ID')
attributeNode.to_csv(path_or_buf='../import/attributeNode.csv',
                     header=True,
                     index=False)
print("attributeNode.csv successfully written out...")
# **************************************************************
# Labels:
# import: attributeNode.csv
defintion_node = """

                  With CUIlist as (
                        SELECT DISTINCT CUI 
                        FROM MRCONSO 
                        WHERE ISPREF = 'Y' 
                            AND MRCONSO.STT = 'PF' 
                            AND MRCONSO.TS = 'P' 
                            AND MRCONSO.LAT = 'ENG') 
                  SELECT DISTINCT MRDEF.ATUI
                                , MRDEF.SAB
                                , MRDEF.DEF
                                , 'Defintion' AS ":LABEL"
                  FROM MRDEF inner join CUIlist on MRDEF.CUI = CUIlist.CUI 
                  WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC', 
                                'ICD9CM', 'ICD10CM', 'ICD10PCS',
                                'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                    AND SUPPRESS = 'N'
                    AND MRDEF.SAB != 'MSH'
                    AND MRDEF.SAB != 'MDR';
                    
                    """
defNode = pd.read_sql_query(defintion_node, conn)
defNode.columns = ['DefinitionId:ID', 'ontology', 'definition', ':LABEL']
defNode.to_csv(path_or_buf='../import/defNode.csv',
               header=True,
               index=False)
print("defNode.csv successfulLY written out...")
# **************************************************************
# GRAPH EDGES
# **************************************************************
# has_sty.csv & sty_of.csv
has_sty_rel = """

                 SELECT DISTINCT s.CUI          AS ":START_ID"
                               , s.TUI          AS ":END_ID"
                               , 'HAS_STY'      AS ":TYPE"
                 FROM MRSTY s
                         JOIN MRCONSO c ON s.CUI = c.CUI
                 WHERE c.SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
                                 'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR', 
                                 'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                     AND c.SUPPRESS = 'N'
                     AND c.ISPREF = 'Y'
                     AND c.TS = 'P'
                     AND c.STT = 'PF';
                     
                     """
has_sty = pd.read_sql_query(
    has_sty_rel, conn).drop_duplicates().replace(np.nan, '')
is_sty_of = has_sty[[':END_ID', ':START_ID', ':TYPE']]
is_sty_of[':TYPE'] = 'IS_STY_OF'
is_sty_of.columns = [':START_ID', ':END_ID', ':TYPE']
has_sty.to_csv(path_or_buf='../import/has_sty.csv',
               header=True,
               index=False)
print("has_sty.csv successfully written out...")
is_sty_of.to_csv(path_or_buf='../import/is_sty_of.csv',
                 header=True,
                 index=False)
print("is_sty_of.csv successfully written out...")
# **************************************************************
# has_umls_atom.csv
has_umls_aui = """

                  SELECT DISTINCT SAB || '#' || CODE     AS ":START_ID"
                                , AUI                    AS ":END_ID"
                                , 'HAS_UMLS_AUI'         AS ":TYPE"
                  FROM MRCONSO
                  WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
                                'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR', 
                                'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                      AND SUPPRESS = 'N';
                      
                      """
has_umls_aui_rel = pd.read_sql_query(
    has_umls_aui, conn).drop_duplicates().replace(np.nan, '')
has_umls_aui_rel.to_csv(path_or_buf="../import/has_umls_atom.csv",
                        header=True,
                        index=False)
print("has_umls_atom.csv successfully written out...")
# **************************************************************
# has_cui.csv
has_cui = """

             SELECT DISTINCT AUI           AS ":START_ID"
                           , CUI           AS ":END_ID"
                           , 'HAS_CUI'     AS ":TYPE"
             FROM MRCONSO
             WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
                           'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR',
                           'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                 AND SUPPRESS = 'N';
                 
                 """
has_cui_rel = pd.read_sql_query(
    has_cui, conn).drop_duplicates().replace(np.nan, '')
has_cui_rel.to_csv(path_or_buf="../import/has_cui.csv",
                   header=True,
                   index=False)
print("has_cui.csv successfully written out...")
# **************************************************************
# code_has_child.csv
has_child = """

              SELECT DISTINCT (SAB || '#' || CODE)   AS ":START_ID"
                            , (SAB2 || '#' || CODE2) AS ":END_ID"
                            , 'HAS_CHILD'            AS ":TYPE"
              FROM HIERARCHY
              WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
                            'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR', 
                            'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                  AND CODE != CODE2;
                  
                  """
has_child_code = pd.read_sql_query(
    has_child, conn).drop_duplicates().replace(np.nan, '')
has_child_code.to_csv(path_or_buf='../import/has_child_code.csv',
                      header=True,
                      index=False)
print("has_child_code.csv successfully written out...")
# **************************************************************
# code_has_attribute.csv
has_attr = """

              SELECT DISTINCT ATUI                           AS ":END_ID"
                           , (SAB || '#' || CODE)            AS ":START_ID"
                           , CASE 
                               WHEN ATN = 'ICD-O-3_CODE' 
                                   THEN 'ICDO3Code' 
                                ELSE ATN END                  AS ":TYPE"
              FROM MRSAT
              WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC', 'ICD9CM', 
                            'ICD10CM', 'ICD10PCS', 'MDR', 'MED-RT', 
                            'NCI', 'RXNORM', 'SNOMEDCT_US')
                  AND ATN IN ('ICD-O-3_CODE', 'NDC')
                  AND SUPPRESS = 'N';
                  
                  """
code_has_attribute = pd.read_sql_query(
    has_attr, conn).drop_duplicates().replace(np.nan, '')
code_has_attribute.to_csv(path_or_buf='../import/code_has_attribute.csv',
                          header=True,
                          index=False)
print("code_has_attribute.csv successfully written out...")
# **************************************************************
# semanticType_isa_rel.csv
sty_isa_rel = """
                 WITH srdef_query AS (SELECT DISTINCT UI
                                      FROM SRDEF
                                      WHERE RT = 'STY')
                 SELECT DISTINCT UI3       AS ":END_ID"
                               , UI1       AS ":START_ID"
                               , 'STY_ISA' AS ":TYPE"
                 FROM SRSTRE1
                         INNER JOIN srdef_query ON UI1 = srdef_query.UI
                 WHERE UI2 = 'T186';"""
sty_isa = pd.read_sql_query(
    sty_isa_rel, conn).drop_duplicates().replace(np.nan, "")
sty_isa.to_csv(path_or_buf="../import/sty_isa.csv",
               header=True,
               index=False)
print("sty_isa.csv successfully written out...")
# **************************************************************
# cui_cui_re = """

#                 SELECT DISTINCT CUI2
#                               , CUI
#                               , CASE
#                                     WHEN RELA = ''
#                                 THEN REL
#                                 ELSE RELA END AS ":TYPE"
#                 FROM MRCONREL
#                 WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
#                              'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR',
#                              'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
#                     AND SAB2 IN ('ATC', 'DRUGBANK', 'GO', 'HGNC',
#                                 'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR',
#                                 'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
#                     AND ISPREF = 'Y'
#                     AND ISPREF2 = 'Y'
#                     AND TS = 'P'
#                     AND TS2 = 'P'
#                     AND STT = 'PF'
#                     AND STT2 = 'PF'
#                     AND REL NOT IN ('SIB', 'SY');

#                     """

# #cui_cui_rel.csv
cui_cui_re = """
                
                SELECT DISTINCT r.CUI2                AS ":START_ID"
                              , r.CUI1                AS ":END_ID"
                              , CASE
                                    WHEN r.RELA = ''
                                        THEN r.REL
                                    ELSE r.RELA END AS ":TYPE"
                FROM MRREL r
                         INNER JOIN MRCONSO c ON r.CUI2 = c.CUI
                         INNER JOIN MRCONSO c2 ON r.CUI1 = c2.CUI
                WHERE c.SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC', 
                                'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR',
                                'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                    AND c2.SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC', 'ICD9CM', 
                                   'ICD10CM', 'ICD10PCS', 'MDR', 'MED-RT', 
                                   'NCI', 'RXNORM', 'SNOMEDCT_US')
                    AND c.SUPPRESS = 'N'
                    AND c.TS = 'P'
                    AND c.STT = 'PF'
                    AND c.ISPREF = 'Y'
                    AND c2.SUPPRESS = 'N'
                    AND c2.TS = 'P'
                    AND c2.STT = 'PF'
                    AND c2.ISPREF = 'Y';
                    
                    """
cui_cui_rel = pd.read_sql_query(cui_cui_re, conn)
cui_cui_rel_df = cui_cui_rel[cui_cui_rel[':START_ID']
                             != cui_cui_rel[':END_ID']]
cui_cui_rel_df2 = cui_cui_rel_df[(cui_cui_rel_df[':TYPE'] != 'SY') & (
    cui_cui_rel_df[':TYPE'] != 'SIB')]
cui_cui_rel_df2[":TYPE"] = cui_cui_rel_df2[":TYPE"].str.upper()
cui_cui_rel_final = cui_cui_rel_df2[(cui_cui_rel_df2[':START_ID']) != (
    cui_cui_rel_df2[':END_ID'])].drop_duplicates().replace(np.nan, '')
cui_cui_rel_final.to_csv(path_or_buf="../import/cui_cui_rel.csv",
                         header=True,
                         index=False)
print("cui_cui_rel.csv successfully written out...")
# **************************************************************
# cui_def_rel.csv
cui_defintion_rel = """
                   
                   SELECT DISTINCT ATUI
                                 , CUI
                                 , 'CUI_HAS_ATTRIBUTE' AS ":TYPE"
                   FROM MRDEF 
                   WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC', 
                                'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR',
                                'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                       AND SUPPRESS = 'N';
                   
                   """
cui_def_rel = pd.read_sql_query(
    cui_defintion_rel, conn).drop_duplicates().replace(np.nan, '')
cui_def_rel.columns = [':END_ID', ':START_ID', ':TYPE']
cui_def_rel.to_csv(path_or_buf='../import/cui_def_rel.csv',
                   header=True,
                   index=False)
print("cui_def_rel.csv successfully written out...")
# **************************************************************
# def_aui_rel.csv
defintion_aui_rel = """
                   
                   SELECT DISTINCT ATUI
                                 , AUI
                                 , 'ATTRIBUTE_HAS_AUI' AS ":TYPE"
                   FROM MRDEF 
                   WHERE SAB IN ('ATC', 'DRUGBANK', 'GO', 'HGNC', 
                                'ICD9CM', 'ICD10CM', 'ICD10PCS', 'MDR',
                                'MED-RT', 'NCI', 'RXNORM', 'SNOMEDCT_US')
                       AND SUPPRESS = 'N';
                   
                   """
def_aui_rel = pd.read_sql_query(
    defintion_aui_rel, conn).drop_duplicates().replace(np.nan, '')
def_aui_rel.columns = [':START_ID', ':END_ID', ':TYPE']
def_aui_rel.to_csv(path_or_buf='../import/def_aui_rel.csv',
                   header=True,
                   index=False)
# **************************************************************
