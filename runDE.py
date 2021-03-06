from __future__ import print_function

########################################################################
# File: runDE.py
#  executable: runDE.py
# Purpose: 
#
#          
# Author: Cameron M. Soulette
# History:      cms 12/05/2018 Created
#
########################################################################


########################################################################
# Hot Imports & Global Variable
########################################################################


import os, sys
import pandas as pd
import numpy as np
from rpy2 import robjects
from rpy2.robjects import r,pandas2ri, Formula
from rpy2.robjects.lib import grid
pandas2ri.activate()
R = robjects.r

########################################################################
# CommandLine
########################################################################

class CommandLine(object) :
    '''
    Handle the command line, usage and help requests.
    CommandLine uses argparse, now standard in 2.7 and beyond. 
    it implements a standard command line argument parser with various argument options,
    and a standard usage and help,
    attributes:
    myCommandLine.args is a dictionary which includes each of the available command line arguments as
    myCommandLine.args['option'] 
    
    methods:
    
    '''
    
    def __init__(self, inOpts=None) :
        '''
        CommandLine constructor.
        Implements a parser to interpret the command line argv string using argparse.
        '''
        import argparse
        self.parser = argparse.ArgumentParser(description = ' runDE.py - a rpy2 convenience tool to run DESeq2.',
                                             epilog = 'Please feel free to forward any questions/concerns to /dev/null', 
                                             add_help = True, #default is True 
                                             prefix_chars = '-', 
                                             usage = '%(prog)s --workingdir dir_name --outdir out_dir --group1 conditionA --group2 conditionB --batch batch --matrix counts_matrix.txt')
        # Add args
        
        self.parser.add_argument("--filter"    , action = 'store', required=False, default = 10, type=int,
                                    help='Output file name prefix.')
        self.parser.add_argument("--group1"    , action = 'store', required=True, 
                                    help='Sample group 1.')
        self.parser.add_argument("--group2"    , action = 'store', required=True, 
                                    help='Sample group 2.')
        self.parser.add_argument("--batch"     , action = 'store', required=False, default=None,
                                    help='Secondary sample attribute (used in design matrix).')
        self.parser.add_argument("--matrix"     , action = 'store', required=True,
                                    help='Input count files.')

        if inOpts is None :
            self.args = vars(self.parser.parse_args())
        else :
            self.args = vars(self.parser.parse_args(inOpts))

# main



def main():
    '''
    maine
    '''

    # Command Line Stuff...
    myCommandLine = CommandLine()

    outdir     = "diffExpOut"
    group1     = myCommandLine.args['group1']
    group2     = myCommandLine.args['group2']
    batch      = myCommandLine.args['batch']  
    matrix     = myCommandLine.args['matrix']
    prefix     = "flair_diffexp"
    




    # make the quant DF
    quantDF  = pd.read_table(matrix, header=0, sep='\t')
    quantDF  = quantDF.set_index('ids')
    df = pandas2ri.py2ri(quantDF)

    # now make the formula
    with open(matrix) as l:
        header = next(l).rstrip().split()[1:]
    
    formula     = [ [x,x.split("_")[1],x.split("_")[-1]] for x in header]
    formulaDF   = pd.DataFrame(formula)
    formulaDF.columns = ['sampleName','condition','batch']
    formulaDF   = formulaDF.set_index('sampleName')
    sampleTable = pandas2ri.py2ri(formulaDF)

    design = Formula("~ batch + condition")
    print(sampleTable)

    # import DESeq2
    from rpy2.robjects.packages import importr
    import rpy2.robjects.lib.ggplot2 as ggplot2
    methods   = importr('methods')
    deseq     = importr('DESeq2')
    grdevices = importr('grDevices')
    qqman     = importr('qqman')



    dds = deseq.DESeqDataSetFromMatrix(countData = df,
                                        colData = sampleTable,
                                        design = design)

    dds  = deseq.DESeq(dds)
    cont = robjects.r["grep"]("condition",robjects.r['resultsNames'](dds),value="TRUE")
    
    # get results; orient the results for groupA vs B
    res = deseq.results(dds, name=cont)
    # results with shrinkage
    resLFC = deseq.lfcShrink(dds, coef=cont, type="apeglm")
    resdf  = robjects.r['as.data.frame'](res)
    
    R.assign('res', res)
    R('write.table(res, file="testres.tsv", quote=FALSE, col.names=NA)')
    reslfc  = robjects.r['as.data.frame'](resLFC)

    # plot MA and PC stats for the user
    plotMA    = robjects.r['plotMA']
    plotDisp  = robjects.r['plotDispEsts']
    plotPCA   = robjects.r['plotPCA']
    plotQQ    = robjects.r['qq']
    
    vsd       = robjects.r['vst'](dds, blind=robjects.r['F'])
    # get pca data
    pcaData    = plotPCA(vsd, intgroup=robjects.StrVector(("condition", "batch")), returnData=robjects.r['T'])
    percentVar = robjects.r['attr'](pcaData, "percentVar")

    # arrange 
    grdevices.pdf(file="./%s/%s_%s_vs_%s_%s_cutoff_plots.pdf" % (outdir,prefix,group1,group2,str(batch)))


    x = "PC1: %s" % int(percentVar[0]*100) + "%% variance"
    y = "PC2: %s" % int(percentVar[1]*100) + "%% variance"
    
    pp = ggplot2.ggplot(pcaData) + \
            ggplot2.aes_string(x="PC1", y="PC2", color="condition", shape="batch") + \
            ggplot2.geom_point(size=3) + \
            robjects.r['xlab'](x) + \
            robjects.r['ylab'](y) + \
            ggplot2.theme_classic() + \
            ggplot2.coord_fixed()
    pp.plot()

    plotMA(res, ylim=robjects.IntVector((-3,3)), main="MA-plot results")
    #plotMA(res, main="MA-plot results")
    plotMA(resLFC, ylim=robjects.IntVector((-3,3)), main="MA-plot LFCSrrhinkage")
    #plotMA(resLFC, main="MA-plot LFCSrrhinkage")
    plotQQ(resdf.rx2('pvalue'), main="pvalue QQ")
    plotQQ(reslfc.rx2('pvalue'), main="LFCSrhinkage pvalue QQ")
    hh = ggplot2.ggplot(resdf) + \
            ggplot2.aes_string(x="pvalue") + \
            ggplot2.geom_histogram() + \
            ggplot2.theme_classic() 
    hh.plot()
    plotDisp(dds, main="Dispersion Estimates")
    grdevices.dev_off()


    lfcOut =  "./%s/%s_%s_deseq2_results_LFC.tsv" % (outdir,prefix,str(batch))
    resOut =  "./%s/%s_%s_deseq2_results.tsv" % (outdir,prefix,str(batch))

    robjects.r['write.table'](reslfc, file=lfcOut, quote=False, sep="\t")
    robjects.r['write.table'](resdf, file=resOut, quote=False, sep="\t")
    sys.exit(1)
    reslsf = pandas2ri.ri2py(reslfc)
    res    = pandas2ri.ri2py(resdf)


    reslsf.to_csv("./%s/%s_%s_deseq2_results_LFC.tsv" % (outdir,prefix,str(batch)), 
                    sep='\t')
    res.to_csv("./%s/%s_%s_deseq2_results.tsv" % (outdir,prefix,str(batch)), 
                    sep='\t')

if __name__ == "__main__":
    main()