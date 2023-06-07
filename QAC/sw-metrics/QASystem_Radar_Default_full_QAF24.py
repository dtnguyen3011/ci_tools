#!/usr/local/bin/python3
# -*- coding: cp1252 -*-
###############################*********************Synopsis*********************###############################
# Run QA Anlysis, view and Report generation one after the other
# currently available configurations are:
##C_ALL_FILES
##C_CROSS_MODULE
##C_DA_AD_FILES
##CPP_ALL_FILES

import csv
import string
import collections
import pprint
import os
import sys
from time import gmtime, strftime

# sys.path.append(os.path.join(os.path.dirname(__file__), "../..")) to be added for lucx
from lib import lucxlog, lucxargs

###############################*********************SCRIPT*********************###############################
# Global information: in case of external usage provided by ConfigFileparser result
# alt qacli = 'C:\\TCC\\Tools\\prqa_framework\\2.2.2_WIN64\\common\\bin\\qacli.exe'
qacli = 'C:\\TCC\\Tools\\prqa_framework\\2.4.0_WIN64\\common\\bin\\qacli.exe'
qaProjectBase = 'C:\\SBX\\pj-if\\generatedFiles\\##VARIANT##\\prqa\\'
qaConfList = ['C_DA_AD_FILES','CPP_ALL_FILES']


###############################*********************qacli_analyze*********************###############################
# subroutine to call external qacli.exe for Analysis of a QA Project
# input:
#   string qaproject # Path to the qaproject to be analyzed
#   string variant # name variant to be analyzed
#   string qaconfig # name of the qaproject configuration to be analyzed

def qacli_analyze(qaproject, prjvariant, qaconfig, qacli, fileOption):
    mycommand = qacli + ' analyze -P ' + qaproject + '\\'+ fileOption + ' -cf ' + ' --force-complete > ' + prjvariant + '_' + qaconfig + '_analyze.log'
    writelog (mycommand)
    sys.stdout.flush()
    ret = os.system(mycommand)
    sys.stdout.flush()
    logstring = 'Result: ' +  str(ret) + '\n'
    writelog (logstring)

###############################*********************qacli_view*********************###############################
# subroutine to call external qacli.exe for view analysis results of a QA Project
# input:
#   string qaproject # Path to the qaproject to be analyzed
#   string prjvariant # name variant to be analyzed
#   string qaconfig # name of the qaproject configuration to be analyzed

def qacli_view(qaproject, prjvariant, qaconfig, qacli, fileOption):
    mycommand = qacli + ' view -P ' + qaproject + '\\' + fileOption + ' -f \"%F;%l;%c;%p:%N;%Y;%t;%S;%j\" -s -M -m STDOUT > ' + prjvariant + '_' + qaconfig + '_view.log'
    # special handling of CPP_ALL_FILES Configuration, due to Hang-up of qucli.exe for this with -M option 
    if qaconfig == 'CPP_ALL_FILES':
        # remove -M from command
        mycommand = mycommand.replace(' -M ',' ')
    writelog (mycommand)
    sys.stdout.flush()
    ret = os.system(mycommand)
    sys.stdout.flush()
    logstring = 'Result: ' +  str(ret) + '\n'
    writelog (logstring)

###############################*********************timestamp*********************###############################
# subroutine to timestamp in format hh:mm:ss
# input: none

def timestamp():
    print (strftime("%H:%M:%S", gmtime()))


###############################*********************writelog*********************###############################
# subroutine to write log info to STDOUT and into logfile 
# input: none

def writelog(toBeLogged):
    global logfile
    print (toBeLogged)
    writetofile = toBeLogged + '\n'
    logfile.write (writetofile)


###############################*********************MAIN*********************###############################

def main(sbxRoot = ['C:/SBX/pj-if/'],
         variantList = ['Radar_C2_ASIL_B', 'Radar_C2_QM'],
         generatedFilesDir = ['generatedFiles'],
         qaclicfg ={'qaclipath': 'C:\\TCC\\Tools\\prqa_framework\\2.4.0_WIN64\\common\\bin\\qacli.exe',
                 'qaConfList': ['C_ALL_FILES', 'C_CROSS_MODULE', 'C_DA_AD_FILES', 'CPP_ALL_FILES'],
                 'doQacliAnalyze': 'False',
                 'doQacliView': 'True'
                 },
        changedFiles=""
         ):
    global logfile

    LOGGER = lucxlog.get_logger()

    LOGGER.info('here we are in QAC analzis')

    qacli = qaclicfg['qaclipath']
    LOGGER.info(qacli)
    ### to be made rady to use rea lists istead o flist with 1 element
    qaProjectBase = sbxRoot[0].replace('/', '\\') + \
                    generatedFilesDir[0].replace('/', '\\') + \
                    '\\##VARIANT##\\prqa\\'

    qaConfList = qaclicfg['qaConfList']

    doQacliAnalyze = qaclicfg['doQacliAnalyze']
    print(doQacliAnalyze)
    doQacliView = qaclicfg['doQacliView']
    print(doQacliView)


    mypath = os.getcwd()
    #os.chdir('d:/workspace/pj-if')

    logfilename = mypath + "\\QASystems_Radar_default.log"
    print (logfilename)
    # Open a file
    logfile = open(logfilename, "w")

    writelog( "Logfile QA-Systems results \n\n")

    writelog ("Project Variants \n ")
    for variant in variantList:
            writelog (variant)

    writelog ("QAProject Configurations \n ")
    for line in qaConfList:
            writelog (line)

    writelog ("Analysis\n ")

    if changedFiles:
        fileOption = ' --files ' + changedFiles
    else:
        fileOption = ''

    for variant in variantList:
        myQaprojectBase = qaProjectBase.replace('##VARIANT##',variant)
        writelog (myQaprojectBase)

        for qaConf in qaConfList:
            writelog (qaConf)


            if (doQacliAnalyze == 'True'):
                timestamp()
                qaproject = myQaprojectBase + qaConf
                qacli_analyze(qaproject, variant, qaConf, qacli, fileOption)

            if (doQacliView == 'True'):
                timestamp()
                qaproject = myQaprojectBase + qaConf
                qacli_view(qaproject, variant, qaConf, qacli, fileOption)

    timestamp()

    # clean up
    os.chdir(mypath)

    writelog('=====complete=====')

    # Close opend logfile
    logfile.close()


if __name__ == "__main__":
    LOGGER = lucxlog.get_logger(__file__)
    main()
