import os, sys
import numpy as np
## input is a drimseq output table with AS events from suppa2
# format is like so:

# feature_id gene_id wt1_wt_b1  ... lr df pvalue adj_pvalue
# 10_exclusion ENSGR0000002586;SE:chrY:2590715-2591355:2591405-2594301:+_0 0.93 ... 1 2 3 0.01
# example file here -> /private/groups/brookslab/csoulette/projects/nanopore/20190110_analysis/as_analysis/drim_se.out.tsv

incOut = open("mutant_sig_inclusion_exoncoords.bed",'w')
excOut = open("mutant_sig_exclusion_exoncoords.bed",'w')

with open(sys.argv[1]) as lines:
    header = next(lines)
    for l in lines:
        c = l.rstrip().split()
        inex, gid = c[1], c[2].replace(";",":").replace("_",":").split(":")
        p = float(c[-1]) if c[-1] !='NA' else 1.0
 
        

        if p< 0.05:
        
            leftVals, rightVals = np.asarray(c[3:3+3],dtype=float), np.asarray(c[3+3:3+3+3],dtype=float)    
            wtM = np.median(leftVals)
            mtM = np.median(rightVals)


            print(leftVals,rightVals)
            if "inclusion" in inex and float(c[3])>float(c[6]):
                if gid[2] == "+":
                    
                    print(gid[2],int(gid[3].split("-")[-1])-5,int(gid[4].split("-")[0],gid[1])+5,".",gid[-2], "%.2f" % (wtM-mtM), file=incOut, sep="\t")
                else:
                    
                    print(gid[2],int(gid[3].split("-")[-1])-6,int(gid[4].split("-")[0])+5,gid[1],".",gid[-2], "%.2f" % (wtM-mtM), file=incOut, sep="\t")
            elif "exclusion" in inex and float(c[3])>float(c[6]):
                if gid[2] == "+":
                    
                    print(gid[2],int(gid[3].split("-")[-1])-5,int(gid[4].split("-")[0],gid[1])+5,".",gid[-2], "%.2f" % (mtM-wtM), file=excOut, sep="\t")
                else:
                    
                    print(gid[2],int(gid[3].split("-")[-1])-6,int(gid[4].split("-")[0])+5,gid[1],".",gid[-2], "%.2f" % (mtM-wtM), file=excOut, sep="\t")



incOut.close()
excOut.close()
