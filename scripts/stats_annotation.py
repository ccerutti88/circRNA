#!/usr/bin/env python3
#usage: python3 scripts/stats_annotation.py -i results_pig_testis_31/annotation_circRNAs_f_0_95.out -o stats_annotation.tsv

# Imports:
import os
import argparse
import pandas as pd
import numpy as np
import re
import sys

# Utility functions
def eprint(*args, **kwargs):
    print(*args,  file=sys.stderr, **kwargs)

def get_sample(file):
    sample_name = os.path.split(os.path.dirname(file))[1]
    return sample_name

def read_file(file):
    """ Read the circ_rnas_annotation.out file and return a pandas dataframe"""
    df = pd.read_table(file, sep='\t')
    df.replace(np.nan, "", inplace=True)
    return df

def intersection(lst1, lst2): 
    return list(set(lst1) & set(lst2)) 

def get_stats(file, df):
    """ Read the circ_rnas_annotation dataframe and return all statistics to tabular 
        format about circRNAs"""
    nb_tot_exonic = len(df)
    sample = get_sample(file)
    header = list(df.columns.values.tolist())
    
    # Arrays:
    exonic_circ_names = []
    infraexonic_tot_names = []
    monoexonic_circ_names = []
    true_exonic = []
    
    # Counters circRNAs type:
    nb_tot_exonic = 0
    nb_monoexonic = 0
    nb_start_end_exonic = 0
    nb_antisens_exonic = 0
    nb_true_intronic = 0
    nb_infraexonic_tot = 0
    nb_infraexonic_sens = 0
    nb_infraexonic_antisens = 0
    nb_single_annotated_junction = 0

    for index, row in df.iterrows():
        if row.nb_ccr >= 5:
            nb_circ_tot = len(df)
            exon_id_start = row.exons_id_start.split(",")
            exon_start = str(exon_id_start[0])
            exon_start_tmp = exon_start.split("_")
            exon_start = exon_start_tmp[0]
            exon_id_end = row.exons_id_end.split(",")
            exon_end = str(exon_id_end[0])
            exon_end_tmp = exon_end.split("_")
            exon_end = exon_end_tmp[0]
            
            # Exonic circRNAs (True exonics circRNAs):
            if ((len(row.exons_id_start) > 0 or len(row.exons_id_end) > 0)
                and len(row.intron_name) == 0):
                nb_tot_exonic += 1
                exonic_circ_names.append(row.circ_rna_name)
                if row.circ_rna_name in exonic_circ_names:
                    if row.strand == "+": 
                        if ("5" and "+") in row.exons_id_start:
                            if len(row.exons_id_end)==0:
                                nb_single_annotated_junction += 1
                            if ("3" and "+") in row.exons_id_end:
                                nb_start_end_exonic += 1
                                true_exonic.append(row)
                                if ((len(exon_id_start)==1 and len(exon_id_end)==1) and (exon_start == exon_end)):
                                    nb_monoexonic += 1
                                    monoexonic_circ_names.append(row.circ_rna_name)
                        if ("3" and "+") in row.exons_id_end:
                            if len(row.exons_id_start)==0:
                                nb_single_annotated_junction += 1
                        if ("3" and "-") in row.exons_id_start:
                            if ("5" and "-") in row.exons_id_end:
                                nb_antisens_exonic += 1
                    elif row.strand == "-":                         
                        if ("5" and "-") in row.exons_id_end:
                            if len(row.exons_id_start)==0:
                                nb_single_annotated_junction += 1
                            if ("3" and "-") in row.exons_id_start:
                                nb_start_end_exonic += 1
                                true_exonic.append(row)
                                if ((len(exon_id_start)==1 and len(exon_id_end)==1) and (exon_start == exon_end)):
                                    nb_monoexonic += 1
                                    monoexonic_circ_names.append(row.circ_rna_name)
                        if ("3" and "-") in row.exons_id_start:
                            if len(row.exons_id_end)==0:
                                nb_single_annotated_junction += 1
                        if ("5" and "+") in row.exons_id_start:
                            if ("3" and "+") in row.exons_id_end:
                                nb_antisens_exonic += 1

            # Infraexonic circRNAs: 
            if ((len(row.gene_id_ife) > 0) and (row.circ_rna_name not in monoexonic_circ_names)):
                nb_infraexonic_tot += 1
                infraexonic_tot_names.append(row.circ_rna_name)
                if row.circ_rna_name in infraexonic_tot_names:
                    if row.strand == "+":
                        if "+" in row.gene_id_ife:
                            nb_infraexonic_sens += 1
                        elif "-" in row.gene_id_ife:
                            nb_infraexonic_antisens += 1
                    elif row.strand == "-":
                        if "-" in row.gene_id_ife:
                            nb_infraexonic_sens += 1
                        elif "+" in row.gene_id_ife:
                            nb_infraexonic_antisens += 1

            # True intronic circRNAs: 
            if len(row.intron_name) > 0:  
                if row.strand == "+":
                    if (row.end_i - row.end) in range(-5,32):
                        if (row.start - row.start_i) in range(-5,5) or (row.start==row.start_i):
                            nb_true_intronic += 1
                    elif (row.start == row.start_i and (row.end_i - row.end) > 32): 
                        nb_true_intronic += 1
                elif row.strand == "-":        
                    if (row.start - row.start_i) in range(-5,32):             
                        if ((row.end - row.end_i) in range(-5,5) or (row.end == row.end_i)): 
                            nb_true_intronic += 1
                    elif (row.end == row.end_i and (row.start - row.start_i) > 32): 
                        nb_true_intronic += 1
                          
    # Write the true exonic table:
    write_true_exonic_table(true_exonic, header, "true_exonic_circ.tsv")

    nb_circ_annotated = nb_start_end_exonic + nb_true_intronic
    nb_circ_non_annotated = nb_circ_tot - (nb_circ_annotated + nb_antisens_exonic + nb_infraexonic_antisens)

    return "\t".join(map(str,[sample, nb_circ_tot, nb_tot_exonic, nb_start_end_exonic, nb_single_annotated_junction, nb_antisens_exonic,
                              nb_monoexonic, nb_infraexonic_tot, nb_infraexonic_sens, nb_infraexonic_antisens,
                              nb_true_intronic, nb_circ_annotated, nb_circ_non_annotated]))+"\n"

def write_stat_table(stats, output_file):
    with open(output_file, "w") as fout:
        fout.write(stats)

def write_true_exonic_table(self, header, path, index=None, sep="\t", na_rep='', float_format=None,
           index_label=None, mode='w', encoding=None, date_format=None, decimal='.'):
    """
    Write a circRNAs list to a tabular-separated file (tsv).
    """
    from pandas.core.frame import DataFrame
    df = DataFrame(self)
    # result is only a string if no path provided, otherwise None
    result = df.to_csv(path, index=index, sep=sep, na_rep=na_rep, float_format=float_format, 
                       header=header, index_label=index_label, mode=mode, encoding=encoding, 
                       date_format=date_format, decimal=decimal)
    if path is None:
        return result

def main():

    # Read the circRNAs annotation file:
    df_circ_annot = read_file(args.input_file)

    # Compute statistics:
    stats = get_stats(args.input_file, df_circ_annot)
    print(stats)

    # Write the stats table:
    write_stat_table(stats, args.output_file)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Sample file')
    parser.add_argument('-i', '--input_file',
                        required=True, help='Sample file')
    parser.add_argument('-o', '--output_file',
                        required=True, help='Sample file')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_arguments()
    main()