#!/usr/local/bin/python
# -*- coding: cp1252 -*-
# ##############################*********************Synopsis*********************###############################
# Read QA Framwork Report prqa_SSR_ddmmyyy_hhmmss.csv provided as argument to the script
# ";" separates list containg amount of QA-framework warning per file separates by Warning Level with headline
# Format:
# Filename;Level 9 violations;Level 8 violations;Level 7 violations;Level 6 violations;Level 5 violations;Level 4 violations;Level 3 violations;Level 2 violations;Level 1 violations;Level 0 violations
# Multi-homed CMA;0;9078;0;369;0;0;0;0;4267;0
# D:/workspace/pj-if/build_cmake/Radar_C0/vinfo/build_version_info.c;0;0;0;0;0;0;0;0;6;0
# D:/workspace/pj-if/dia/examples/diacus/inc/diacus_runnable.hpp;0;0;0;1;4;0;0;2;0;0
#

import csv
import string
import collections
import pprint
import os
import re
import fnmatch
from time import localtime, strftime


# ##############################*********************SCRIPT*********************###############################
# Global information: could be read from a config file in future...


debug = 0
sbxRoot = ['C:/SBX/pj-if/']
sbxRootWin = ['C:\\SBX\\pj-if\\']
# sbxRoot = ['D:/SBX/pj-if/','D:/SBX/idc5/', 'C:/SBX/pj-vwmqb37w/']
# sbxRootWin = ['D:\\SBX\\pj-if\\','D:\\SBX\\idc5\\', 'C:\\SBX\\pj-vwmqb37w\\']

''' filename with path for logfile '''
logfile = None

logfilename = ''

separator = ';'

# global dictionaries to store results
#
# qaFindingDict dictionary to remoce and count duplicates split into attributes of message
#   line containes output line with a qa finding from qacli view with there defiend format string used to sort out and count duplicates
# qaFindingDict[line]['file'] filename with path relative to SBX root unix style containing the finding
# qaFindingDict[line]['line'] line number of finding
# qaFindingDict[line]['col'] column number of finding
# qaFindingDict[line]['msg'] finding of qaframework in format tool-Version:number e.g. qacpp-4.2.0:1599 -> message number
# qaFindingDict[line]['severity'] severity of the finding
# qaFindingDict[line]['msgText'] message text of the finding
# qaFindingDict[line]['commented'] 0 if finding is active, 1 if message is commented (inactive), in this case ther shall be a comment 'comText'
# qaFindingDict[line]['comText'] comment given if finding is deactivated
# qaFindingDict[line]['count'] counts amount of duplicate findings
# qaFindingDict[line]['origin'] input files the finding was detected, ' ' separated list
qaFindingDict = {}
# same structure as qaFindingDict, but to keep only list of commented out QA-Framework messages
commentedQaFindingDict = {}

# componentsDict dictionary used to set up lookup table for componentname and path relative to SBX root to the component
# to identify later on the components a file with warning belongs to by match of path to component
#   compname contains the name of the component
# componentsDict[componentsDict] path relative to SBX root unix style containing fiels of the component
componentsDict = {}

# QaMessages dictionary containing sumary of detected QA messages (findings)
#   key finding of qaframework in format tool-Version:number e.g. qacpp-4.2.0:1599 -> message number
# QaMessages[key]['count'] counts amount of findings
# QaMessages[key]['countCommented'] counts amount of commented findings
# QaMessages[key]['msgText'] message text of the finding
# QaMessages[key]['severity'] severity of the finding
QaMessages = {}

# fileSummary dictionary to store result of aggregation of findings according to the severity and sorting info
#   file filename with path relative to SBX root unix style containing the findings
# fileSummary[file]['delivery'] file is part of PJ-IF delivery 'x' -> yes '-' -> no, based on Flux output
# fileSummary[file]['comp'] name of the component the file belongs to or 'not allocatesd' in case match to get component failed, based on Flux output
# fileSummary[file]['L0'] count for findings of severity 0 (attentiion: key is integr value)
# fileSummary[file]['L1'] count for findings of severity 1 (attentiion: key is integr value)
# fileSummary[file]['L2'] count for findings of severity 2 (attentiion: key is integr value)
# fileSummary[file]['L3'] count for findings of severity 3 (attentiion: key is integr value)
# fileSummary[file]['L4'] count for findings of severity 4 (attentiion: key is integr value)
# fileSummary[file]['L5'] count for findings of severity 5 (attentiion: key is integr value)
# fileSummary[file]['L6'] count for findings of severity 6 (attentiion: key is integr value)
# fileSummary[file]['L7'] count for findings of severity 7 (attentiion: key is integr value)
# fileSummary[file]['L8'] count for findings of severity 8 (attentiion: key is integr value)
# fileSummary[file]['L9'] count for findings of severity 9 (attentiion: key is integr value)
# fileSummary[file]['GHSwarnings']  count for compiler Warnings with GHS compiler (attentiion: key is integr value)
# fileSummary[file]['filesystem']  sourcefile present in filesystem  ='x' -> yes
# fileSummary[file]['sourcetype']  type of sourcefile .c and .h -> "C", .cpp, .hpp and .inl -> "CPP"
# fileSummary[file][variantname] used to build variant variantname ='x' -> yes
# fileSummary[file]['origin'] input files the finding was detected, ' ' separated list
# fileSummary[file]['delivery_ipif'] file is part of PJ-IF delivery 'x' -> yes '-' -> no based on is inseide of path /ip_if/
# fileSummary[file]['comp_guess_arch'] name of the component the file belongs to or 'not allocatesd' in case match to get component failed
#                                      based on guessing /arch folder exists for a component
fileSummary = {}

# GHSwarnings dictionary to store result of aggregation GHS compiler Wrnings
#   file filename with path relative to SBX root unix style containing the findings
#   warning in format line <linenumber>: warning #<warning ID>, e.g. line 20: warning #1496-D
# GHSwarnings[file][warning] contains warningtext
GHSwarnings = {}

# GHSsummary dictionary to store result of aggregation GHS compiler Wrnings
#   file filename with path relative to SBX root unix style containing the findings
# GHSsummary[file]['GHSwarnings'] count for GHS warning per file
GHSsummary = {}

# GHSMessageCount dictionary containing sumary of detected GHS compiler warnings
#   key warning of GHS Compiler in format warning #xxx-D e.g. warning #170-D -> warning number
# GHSMessageCount[key]['count'] counts amount of findings
# GHSMessageCount[key]['countCommented'] counts amount of commented findings
# GHSMessageCount[key]['msgText'] message text of the finding
GHSMessageCount = {}

# deliveryCompDict dictonary containing files belonging to the delivery and subdict containig the component
#   file filename with path relative to SBX root unix style containing the findings
# deliveryCompDict[file]['comp'] = name of the component
deliveryCompDict = {}

# Team allocation
teamAllocationDict = {'uC_fwLr/core/rbAdc/': 'uC_Lr',
                      'uC_fwLr/core/blockStructure/': 'uC_Lr',
                      'uC_fwLr/core/rbHwCrc/': 'uC_Lr',
                      'uC_fwLr/core/ifx/': 'uC_Lr',
                      'uC_fwLr/core/rbMemProt/': 'uC_Lr',
                      'uC_fwLr/core/memstack/': 'uC_Lr',
                      'uC_fwLr/core/rbPda/': 'uC_Lr',
                      'uC_fwLr/core/rbOsSetup/': 'uC_Lr',
                      'uC_fwLr/core/rbTaskAliveCheck/': 'uC_Lr',
                      'PJIF/rbSchedrbSched/': 'uC_Lr',
                      'uC_fwLr/core/rbSysLog/': 'uC_Lr',
                      'uC_fwLr/core/rbTime/': 'uC_Lr',
                      'uC_fwLr/core/rbTrapHandler/': 'uC_Lr',
                      'uC_fwLr/core/rbLinker/': 'uC_Lr',
                      'uC_fwLr/core/rbMonReact/': 'uC_Lr',
                      'uC_fwLr/ifr/rbLinkerPL/': 'uC_Lr',
                      'uC_fwLr/ifr/engineering_clock/': 'uC_Lr',
                      'uC_fwLr/ifr/rbCS520/': 'uC_Lr',
                      'uC_fwLr/ifr/rtaos/': 'uC_Lr',
                      'uC_fwLr/ifr/rbAlarmHandler/': 'uC_Lr',
                      'uC_fwLr/ifr/rbSpi/': 'uC_Lr',
                      'radar_if/startup/': 'uC_Lr',
                      'uC_fwLr/ifr/rbSysLogPL/': 'uC_Lr',
                      'uC_fwLr/ifr/uwehandler/': 'uC_Lr',
                      'net/rbNetCom/': 'Com',
                      'net/rbNetScheduler/': 'Com',
                      'net/rbNetLdt/': 'Com',
                      'net/rbNetE2E/': 'Com',
                      'net/rbNetSigMon/': 'Com',
                      'net/rbNetXcp/': 'Com',
                      'if_fw/ifs/': 'Com',
                      'if_fw/core/globaltime/': 'Com',
                      'rbPdm/': 'SAM',
                      'rbSysEvM/': 'SAM',
                      'mom/daddy/': 'MOM',
                      'mom/vfc/': 'MOM',
                      'mom/scom/': 'MOM',
                      'uC_fwBg/core/flashTest/': 'uC_RBEI',
                      'uC_fwBg/core/bist/': 'uC_RBEI',
                      'uC_fwBg/core/rbsbst/': 'uC_RBEI',
                      'uC_fwBg/core/rbSftMon/': 'uC_RBEI',
                      'uC_fwBg/core/rbInterruptHandler/': 'uC_RBEI',
                      'dia/': 'RBEI_SAM',
                      'uC_fwBg/core/rbSwTestInterface/': 'uC_RBEI',
                      'uC_fwLr/core/rbHSMPrepare/': 'uC_RBEI',
                      'BootManager/if_boot/BootManager/': 'uC_RBEI',
                      'uC_fwBg/core/rbHwCfgCheck/': 'uC_RBEI',
                      'uC_fwBg/core/rbMpuSRIBusConfig/': 'uC_RBEI',
                      'rbSched/rbSchedTarget/': 'uC_Lr',
                      'uC_fwBg/core/rbSysMode/': 'uC_RBEI',
                      'uC_fwBg/core/rbPFlashIntegrity/': 'uC_RBEI',
                      'uC_fwLr/core/': 'uC_Lr',
                      'uC_fwBg/ifr/rbHwCfgCheck/': 'uC_RBEI',
                      'uC_fwBg/ifr/bist/': 'uC_RBEI',
                      'uC_fwBg/ifr/rbsbst/': 'uC_RBEI',
                      'uC_fwBg/core/mon/': 'uC_RBEI',
                      'uC_fwBg/ifr/mon/': 'uC_RBEI',
                      'rbSched/': 'uC_Lr',
                      'dasy_uC_fw/': 'DASy',
                      'if_fw/core/uartCommunication/': 'DASy',
                      'if_fw/core/cubas/stubs/': 'SAM',
                      'net/inc/': 'Com',
                      'rba/CUBAS/': 'CAP',
                      'tools/vx1100/': 'MT',
                      'uC_fwLr/ifr/': 'uC_Lr',
                      'radar_if/component/startup/': 'uC_Lr',
                      'radar_if/component/rbIfController/': 'uC_Lr',
                      'radar_if/component/rbSched/': 'uC_Lr',
                      'radar_if/component/rtaos/': 'uC_Lr',
                      'radar_if/component/syslog_prj/': 'uC_Lr',
                      'btc_tools/': 'Tools',
                      'rba/Templates/': 'Security',
                      'rba/Tools/': 'DASy',
                      'tools/mt/': 'MT',
                      'tools/qac/': 'Tools',
                      '1r1v_fw/': '1R1V',
                      '1r1v_fw/': '1R1V',
                      'ip_dc/': 'DA-Core',
                      'rc_apl_radar/': 'DSP',
                      'rc_fw/': 'DSP',
                      'ip_vmc/': 'VMC',
                      'jenkins/': 'INT',
                      'radar_int/': 'IPIF',
                      'uP_uC_Cmn/': 'DASy'}

# ##############################*********************writelog*********************###############################
# subroutine to write log info to STDOUT and into a logfile 
# input:
#   logfilename: name of file to be created
#   toBeLoged: content to be written to logfile, e.g. dictionaly or list 


def writelogPprint(nameToBeLoged, toBeLoged):
    localLogfilename = 'evalViewLog_' + nameToBeLoged + '.log'

    writelog(timestamp() + ' create Logfile for: ' + localLogfilename + '\n')

    # Open a file
    localLogfile = open(localLogfilename, "w")

    localLogfile.write(logfilename + '\n')
    localLogfile.write(logfilename + ' = ')

    pprint.pprint(toBeLoged, localLogfile)

    localLogfile.close()

    writelog(timestamp() + ' create Logfile for: ' + localLogfilename + ' after writelogPprint\n')


###############################*********************timestamp*********************###############################
# subroutine to timestamp in format hh:mm:ss
# input: none

def timestamp():
    timestr = strftime("%H:%M:%S", localtime())

    return timestr


###############################*********************writelog*********************###############################
# subroutine to write log info to STDOUT and into logfile 
# input: none

def writelog(toBeLogged):
    global logfile
    global logfilename
    print(toBeLogged)
    writetofile = toBeLogged + '\n'
    logfile.write(writetofile)


###############################*********************create_dict*********************###############################
# subroutine Creates the folder structure in the release directory
# input:
#   string inputfile # Path and filename of file to read (qacli_view oputput)
#   string local_dict # dictionary the result has to be added to 

def create_dict(inputfile: object, local_dict: object, sbxRoot: object) -> object:
    count = 0
    # local_dict = {} # create dict

    with open(inputfile) as file:
        for line in file:
            count = count + 1
            line = line.rstrip()  # remove trailing whitespace and \n
            line = line.replace('\\', '/')  # convert path to UNIX style
            for rootDir in sbxRoot:
                line = line.replace(rootDir, '')  # remove leading Sandboxroot from path
            line = line.replace('pjif_fw', 'ip_if')  # convert path of Dasy DAY PJIF delivery to PJIF path of delivery
            # identifier to split finding list
            # Attention dependency to quacli view -f defiend foramt string fpr output !!!!
            headingslist = ['file', 'line', 'col', 'msg', 'severity', 'msgText', 'commented', 'comText']
            # remove and count duplicates
            if line in local_dict:
                # line is a duplicate finding just count it as duplicate
                local_dict[line]['count'] = local_dict[line]['count'] + 1
                # get variant Name out of filename e.g.Radar_C0_MXL_flist.txt
                matchvariant = re.search(inputfile, local_dict[line]['origin'])
                if not matchvariant:
                    local_dict[line]['origin'] = local_dict[line]['origin'] + ' ' + inputfile
            else:
                # get attributes for finding
                attrlist = line.split(separator)
                # identify comment lines and section headings and skip processing of line
                if len(attrlist) == len(headingslist):
                    # detected the first time
                    local_dict[line] = {}  # create sub dict
                    local_dict[line]['count'] = 1
                    colcount = 0
                    for col in attrlist:
                        value = attrlist[colcount]
                        local_dict[line][headingslist[colcount]] = value
                        colcount = colcount + 1
                    # keep Info where detected
                    local_dict[line]['origin'] = inputfile

    # print ("\nsub: def create_dict(inputfile, local_dict) ")
    # pprint.pprint(local_dict)
    ##    for key, sub_dict in sorted(local_dict.items()):
    ##        print ('key: '+ key)
    ##        print ('file: ' + local_dict[key]['file'])
    ##        print ('msg: ' + local_dict[key]['msg'])
    return local_dict


###############################*********************getCompilerWarnings*********************###############################
# subroutine creste a dictonary contianing aggregated Compiler Warnings
# input:
#   inputfile # Path and filename of file to read (Compiler Warning summary oputput from btc_tools CMAKE)
#   dictionary local_dict # dictionary containin the result in fomat:
#                              local_dict[filename][count] 

def getCompilerWarnings(inputfile, local_dict, sbxRoot):
    count = 0
    print('Compiler Warning inputfile: ' + inputfile)
    with open(inputfile) as file:
        for line in file:
            count = count + 1
            line = line.rstrip()  # remove trailing whitespace and \n
            line = line.replace('\\', '/')  # convert path to UNIX style
            line = line.replace('//', '/')  # remove double // from path if there
            line = line.replace('WARNING - ',
                                '')  # ??? todo find more general solution remove double "WARNING - " from path if there (added for 1903 in btc_tools
            for rootDir in sbxRoot:
                line = line.replace(rootDir, '')  # remove leading Sandboxroot from path
            while re.search(r'/\.\./', line):
                line = re.sub(r'[a-zA-Z0-9_-]+/\.\./', '',
                              line)  # cancel /<something>/../ from path for generated headers
            line = line.replace('pjif_fw', 'ip_if')  # convert path of Dasy DAY PJIF delivery to PJIF path of delivery
            # search for Filename enclosed by "" at beinnin gof the line
            ## matchfilename = re.search(r'^"([a-zA-Z0-9_/.-]*)"',line)
            matchfilename = re.search(r'^"(.+)"', line)
            if matchfilename:
                filename = matchfilename.group(1)

                local_dict[filename] = {}  # create sub dict
                local_dict[filename]['warnings'] = {}  # create sub dict
            # search for line 9: warning #1-D: last line of file ends without a newline
            # and allocate it to the last matched filename
            matchmessage = re.search(r'(line .*: warning #.*): (.*)', line)
            if matchmessage:
                local_dict[filename]['warnings'][matchmessage.group(1)] = matchmessage.group(2)

                if 'origin' in local_dict[filename]:
                    matchvariant = re.search(inputfile, local_dict[filename]['origin'])
                    if not matchvariant:
                        local_dict[filename]['origin'] = local_dict[filename]['origin'] + ' ' + inputfile
                else:
                    local_dict[filename]['origin'] = inputfile

    return local_dict


###############################*********************countCompilerWarnings*********************###############################
# subroutine creste a dictonary contianing aggregated Compiler Warnings
# input:
#   dictionary input_dict # dictionary containin the input in fomat:
#                              input_dict[file][warning] = warningtext
#   dictionary local_dict # dictionary containin the result in fomat:
#                              local_dict[file]['GHSwarnings'] = count

def countCompilerWarnings(input_dict, local_dict):
    GHSMessageCount = {}  # -> create subdictionary

    for sourcefile in input_dict:

        local_dict[sourcefile] = {}  # create sub dict
        intermediateDict = input_dict[sourcefile]['warnings']

        for warning in intermediateDict:
            # count per file
            # only if content is not 'origin' ???Todo with changed dict structure obsolete
            if warning != 'origin':  # todo ??? replace condition here by using "line 79: warning #1441-D" -> change sequence -> place after match statement below.
                if 'GHSwarnings' in local_dict[sourcefile]:
                    local_dict[sourcefile]['GHSwarnings'] = local_dict[sourcefile]['GHSwarnings'] + 1
                else:
                    local_dict[sourcefile]['GHSwarnings'] = 1

            # take over origin
            local_dict[sourcefile]['GHSorigin'] = input_dict[sourcefile]['origin']

            # count per Warning number
            ##  get "warning #xxx-D" out of e.g."line 43: warning #170-D" to sort out 'origin'
            match = re.search(r'.+(warning .+)', warning)
            if match:
                GHSwarning = match.group(1)
                if GHSwarning in GHSMessageCount:
                    # found again
                    GHSMessageCount[GHSwarning]['count'] = GHSMessageCount[GHSwarning]['count'] + 1
                else:
                    # first appearance
                    GHSMessageCount[GHSwarning] = {}  # create sub dict
                    GHSMessageCount[GHSwarning]['count'] = 1
                    GHSMessageCount[GHSwarning]['msgText'] = input_dict[sourcefile]['warnings'][warning]

    writelogPprint('GHSMessageCount', GHSMessageCount)

    return local_dict


###############################*********************get_source_files*********************###############################
# subroutine get all source Files inside repo
# input:
#   dictionary input_dict # dictionary containg the input in fomat:
#                              input_dict[file]['filesystem'] = 'x'
def get_source_files(root, input_dict, sbxRoot):
    for root, dirnames, filenames in os.walk(root):
        match = 0
        for filename in fnmatch.filter(filenames, '*.c'):
            fulln = os.path.join(root, filename)
            stripFilename(fulln, input_dict, 'C', sbxRoot)
        for filename in fnmatch.filter(filenames, '*.h'):
            fulln = os.path.join(root, filename)
            stripFilename(fulln, input_dict, 'C', sbxRoot)
        for filename in fnmatch.filter(filenames, '*.cpp'):
            fulln = os.path.join(root, filename)
            stripFilename(fulln, input_dict, 'CPP', sbxRoot)
        for filename in fnmatch.filter(filenames, '*.hpp'):
            fulln = os.path.join(root, filename)
            stripFilename(fulln, input_dict, 'CPP', sbxRoot)
        for filename in fnmatch.filter(filenames, '*.inl'):
            fulln = os.path.join(root, filename)
            stripFilename(fulln, input_dict, 'CPP', sbxRoot)

    return input_dict


###############################*********************stripFilename*********************###############################
# subroutine get all source Files inside repo
# input:
#   fulln Filename with path
#   dictionary input_dict # dictionary containg the input in fomat:
#                              input_dict[file]['filesystem'] = 'x'
#                              input_dict[file]['sourcetype'] = sourcetype
#   sourcetype: Identifier for sourcetype, e.g. 'C; or 'CPP'

def stripFilename(fulln, input_dict, sourcetype, sbxRoot):
    files = []

    # exclude .git/... -> git directory and everything below
    gitdir = re.search(r"\.git.+$", fulln)
    if gitdir:
        # print ('ignored:' + fulln)
        match = 0
    else:
        fulln = fulln.rstrip()  # remove trailing whitespace and \n
        fulln = fulln.replace('\\', '/')  # convert path to UNIX style
        fulln = fulln.replace('/arch', '')  # remove treiling /arch
        for rootDir in sbxRoot:
            fulln = fulln.replace(rootDir, '')  # remove leading Sandboxroot
        fulln = fulln.replace('pjif_fw', 'ip_if')  # convert path of Dasy DAY PJIF delivery to PJIF path of delivery
        files.append(fulln)
        input_dict[fulln] = {}
        input_dict[fulln]['filesystem'] = 'x'
        input_dict[fulln]['sourcetype'] = sourcetype

    # destinguish C and CPP

    if debug:
        writelogPprint('Sourcefiles', files)

    return input_dict


###############################*********************getUsedInVariant*********************###############################
# subroutine creste a dictonary contianing files used in Variant from list in flist.txt
# input:
#   inputfile # Path and filename of file to read (flist as oputput from btc_tools CMAKE)
#   list usedInVariant # list containing the result in fomat:
#                              usedInVariant[..) = filename 

def getUsedInVariant(inputfile, usedInVariant, sbxRoot):
    count = 0
    print('flist inputfile: ' + inputfile)
    with open(inputfile) as file:
        for line in file:
            count = count + 1
            line = line.rstrip()  # remove trailing whitespace and \n
            line = line.replace('\\', '/')  # convert path to UNIX style
            line = line.replace('//', '/')  # remove double // from path if there
            for rootDir in sbxRoot:
                line = line.replace(rootDir, '')  # remove leading Sandboxroot from path
            while re.search(r'/\.\./', line):
                line = re.sub(r'[a-zA-Z0-9_-]+/\.\./', '',
                              line)  # cancel /<something>/../ from path for generated headers
            line = line.replace('pjif_fw', 'ip_if')  # convert path of Dasy DAY PJIF delivery to PJIF path of delivery

            usedInVariant.append(line)  # append to list

    print(count)
    return usedInVariant


###############################*********************getDeliveryAndComponetFromFlux*********************###############################
# subroutine creste a dictonary contianing files used in Variant from list in flist.txt
# input:
#   inputfile # Path and filename of file to read (Output from Flux script)
#   dict DeliveryComponentDict # dict containing the result in fomat:
#                DeliveryComponentDict[filename]['delivery'] = 'x'
#                DeliveryComponentDict[filename]['comp'] = compname
# retrn:
#   DeliveryComponentDict

def getDeliveryAndComponetFromFlux(inputfile, localDict, sbxRoot):
    print('getDeliveryAndComponetFromFlux: flist inputfile: ' + inputfile)
    with open(inputfile) as file:
        for line in file:
            line = line.rstrip()  # remove trailing whitespace and \n
            line = line.replace('\\', '/')  # convert path to UNIX style
            line = line.replace('//', '/')  # remove double // from path if there
            for rootDir in sbxRoot:
                line = line.replace(rootDir, '')  # remove leading Sandboxroot from path
            while re.search(r'/\.\./', line):
                line = re.sub(r'[a-zA-Z0-9_-]+/\.\./', '',
                              line)  # cancel /<something>/../ from path for generated headers
            line = line.replace('pjif_fw', 'ip_if')  # convert path of Dasy DAY PJIF delivery to PJIF path of delivery

            matchobj = re.search(r'(.+);(.+)', line)
            if matchobj:
                filename = matchobj.group(1)
                compname = matchobj.group(2)
                # print (filename + ' -> ' + compname)
                localDict[filename] = {}
                localDict[filename]['delivery'] = 'x'
                localDict[filename]['comp'] = compname

    writelogPprint('getDeliveryAndComponetFromFlux', localDict)

    return localDict


###############################
###############################*********************MAIN*********************###############################
###############################

def main(sbxRoot, variantList, generatedFilesDir, teamallocationtable):
    global logfile
    global qaFindingDict
    global deliveryCompDict
    global fileSummary
    global GHSwarnings
    global GHSsummary

    teamAllocationDict = teamallocationtable

    #sbxRootWin = sbxRoot.copy()
    sbxRootWin = []

    for rootDir in sbxRoot:
        rootDirWin = rootDir.replace('/', '\\')
        sbxRootWin.append(rootDirWin)
        print(rootDir + ' new: ' + rootDirWin)

    mypath = os.getcwd()

    logfilename = mypath + "\\evalView.log"
    print('logfilename: ' + logfilename)
    # Open a file
    logfile = open(logfilename, "w")

    outstring = timestamp() + ' Start\n\n'
    writelog(outstring)


    for rootDir in sbxRoot:
        get_source_files(rootDir, fileSummary, sbxRoot)

    writelogPprint('fileSummary', fileSummary)

    viewfilelist = []

    # Evaluate all *_view.log results from qacli view output
    listOfViews = os.listdir('.')
    pattern = "*_view.log"
    for inputfile in listOfViews:
        if fnmatch.fnmatch(inputfile, pattern):
            viewfilelist.append(inputfile)

    writelogPprint('viewfilelist', viewfilelist)

    for inputfile in viewfilelist:
        qaFindingDict = create_dict(inputfile, qaFindingDict, sbxRoot)

    writelogPprint('qaFindingDict', qaFindingDict)

    ##----------------------------------------------------------------------------------------
    # Part2 get components
    ##----------------------------------------------------------------------------------------


    for rootDir in sbxRootWin:
        if os.path.exists(rootDir):
            chDirResult = os.chdir(rootDir)
            print('current dir: ', rootDir)
        else:
            print('chdir Result: ', rootDir, ' does not exist')

        mycommand = 'dir arch /A:D /S /B'

        compfilellist = os.popen(mycommand).readlines()
        os.chdir(mypath)
        writelogPprint('componentlistFilesystem1', compfilellist)

        for line in compfilellist:
            line = line.rstrip()  # remove trailing whitespace and \n
            line = line.replace('\\', '/')  # convert path to UNIX style
            line = line.replace('/arch', '')  # remove trailing /arch
            for rootDirLinux in sbxRoot:
                line = line.replace(rootDirLinux, '')  # remove leading Sandboxroot
            line = line.replace('pjif_fw', 'ip_if')  # convert path of Dasy DAY PJIF delivery to PJIF path of delivery
            match = re.search(r"\w*$", line)
            if match:
                compname = match.group()
                # print (compname ,': ', line)
                componentsDict[compname] = line
            else:
                print('fail', ': ', line)

    # print("componentlist Filsystem 2")

    writelogPprint('componentsDict', componentsDict)

    ##----------------------------------------------------------------------------------------
    # Part3+4+5+6
    # - add components to findings
    # - Aggregate warnings per level in files
    # - count overall appearance of mesages
    # - add delivery to findings (path contains "ip_if")
    ##----------------------------------------------------------------------------------------

    for qaFinding in qaFindingDict:
        s = qaFindingDict[qaFinding]['file']

        ##----------------------------------------------------------------------------------------
        # Part 4 aggregate warninglevel per file
        ##----------------------------------------------------------------------------------------
        severity = int(qaFindingDict[qaFinding]['severity'])

        # severity Level item
        severity = 'L' + str(severity)

        # count if not commented out
        if qaFindingDict[qaFinding]['commented'] is '0':
            if s not in fileSummary:
                fileSummary[s] = {}  # create sub dict

            if 'L0' in fileSummary[s]:
                fileSummary[s][severity] = fileSummary[s][severity] + 1
            else:
                # first appearance = intialize all severity levels to count 0
                fileSummary[s]['L0'] = 0
                fileSummary[s]['L1'] = 0
                fileSummary[s]['L2'] = 0
                fileSummary[s]['L3'] = 0
                fileSummary[s]['L4'] = 0
                fileSummary[s]['L5'] = 0
                fileSummary[s]['L6'] = 0
                fileSummary[s]['L7'] = 0
                fileSummary[s]['L8'] = 0
                fileSummary[s]['L9'] = 0

                # add the current finding
                fileSummary[s][severity] = fileSummary[s][severity] + 1
        else:
            intermediate = qaFindingDict[qaFinding]
            # print ('intermediate: ' + qaFinding)
            commentedQaFindingDict[qaFinding] = {}
            commentedQaFindingDict[qaFinding].update(intermediate)

        ##----------------------------------------------------------------------------------------
        # Part 5 count message appearance
        ##----------------------------------------------------------------------------------------
        key = qaFindingDict[qaFinding]['msg']

        # count if not commented out
        if qaFindingDict[qaFinding]['commented'] is '0':
            if key in QaMessages:
                QaMessages[key]['count'] = QaMessages[key]['count'] + 1
            else:
                QaMessages[key] = {}  # create sub dict
                QaMessages[key]['count'] = 1
                QaMessages[key]['countCommented'] = 0

                QaMessages[key]['msgText'] = qaFindingDict[qaFinding]['msgText']
                QaMessages[key]['severity'] = qaFindingDict[qaFinding]['severity']
        else:
            if key in QaMessages:
                QaMessages[key]['countCommented'] = QaMessages[key]['countCommented'] + 1
            else:
                QaMessages[key] = {}  # create sub dict
                QaMessages[key]['countCommented'] = 1
                QaMessages[key]['count'] = 0

                QaMessages[key]['msgText'] = qaFindingDict[qaFinding]['msgText']
                QaMessages[key]['severity'] = qaFindingDict[qaFinding]['severity']

    writelog('QA-Findings\n')

    writelogPprint('qaFindingDict', qaFindingDict)
    writelogPprint('commentedQaFindingDict', commentedQaFindingDict)
    writelogPprint('QaMessages', QaMessages)

    ##----------------------------------------------------------------------------------------
    # Part 6 generate output as csv for messages count
    ##----------------------------------------------------------------------------------------

    outfilename = mypath + "\\messageSummary.csv"
    print('outfilename: ' + outfilename)
    # Open a file
    outfile = open(outfilename, "w")

    writetofile = 'message' + ';' + 'severity' + ';' + 'msgText' + ';' + 'count' + ';' + 'countCommented' + '\n'
    outfile.write(writetofile)

    for message in QaMessages:
        s = qaFindingDict[qaFinding]['file']
        writetofile = message + ';' + QaMessages[message]['severity'] + ';' + QaMessages[message]['msgText'] + ';' + str(
            QaMessages[message]['count']) + ';' + str(QaMessages[message]['countCommented']) + '\n'
        outfile.write(writetofile)

    outfile.close()

    outstring = timestamp() + ' write messageSummary.csv\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 6 get GHS compiler warnings
    ##----------------------------------------------------------------------------------------

    # Evaluate all *_warninglog.log results from Compiler Warning summary output
    listOfWarningLogFiles = os.listdir('.')
    pattern = "*_warninglog.log"
    for inputfile in listOfWarningLogFiles:
        if fnmatch.fnmatch(inputfile, pattern):
            getCompilerWarnings(inputfile, GHSwarnings, sbxRoot)

    writelogPprint('GHSwarnings', GHSwarnings)

    countCompilerWarnings(GHSwarnings, GHSsummary)

    writelogPprint('GHSsummary', GHSsummary)

    # add results from Compiler to summary
    # fileSummary.update(GHSsummary) removes origal entry -> no QA-system findings in file with ghs Warnings
    for sourcefile in GHSsummary:

        if sourcefile not in fileSummary:
            print('GHSCompiler Warnings add file not in filesummary yet: ' + sourcefile)
            fileSummary[sourcefile] = {}  # create subdict

        fileSummary[sourcefile]['GHSwarnings'] = GHSsummary[sourcefile]['GHSwarnings']
        fileSummary[sourcefile]['GHSorigin'] = GHSsummary[sourcefile]['GHSorigin']

    outstring = timestamp() + ' get and count Compilerwarnings\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 7a get component and delivery info
    ##----------------------------------------------------------------------------------------
    for file in fileSummary:

        ##----------------------------------------------------------------------------------------
        # Part 7aa get component
        ##----------------------------------------------------------------------------------------
        match = 0
        for component in componentsDict:
            pattern = componentsDict[component]
            ##        print('component:' + component)
            ##        print('pattern:' + pattern)

            if re.search(pattern, file):
                componentAllocated = component
                match = 1

        if match == 0:
            componentAllocated = "comp not allocated"

        fileSummary[file]['comp_guess_arch'] = componentAllocated

        ##----------------------------------------------------------------------------------------
        # Part 7ab get component and delivery_ipif info
        ##----------------------------------------------------------------------------------------
        pattern = 'ip_if'

        if re.search(pattern, file):
            fileSummary[file]['delivery_ipif'] = 'x'
        else:
            fileSummary[file]['delivery_ipif'] = '-'

    outstring = timestamp() + ' allocate components to filelist\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 7b get component and delivery info from FLUX
    ##----------------------------------------------------------------------------------------
    fluxDeliveryInfoAvailable = 0
    fluxInputfile = 'FluxinfoRadar.txt.txt'
    if os.path.isfile(fluxInputfile):
        fluxDeliveryInfoAvailable = 1
        deliveryCompDict = getDeliveryAndComponetFromFlux(fluxInputfile, deliveryCompDict, sbxRoot)

    fluxInputfile = 'FluxinfoDASY.txt.txt'
    if os.path.isfile(fluxInputfile):
        fluxDeliveryInfoAvailable = 1
        deliveryCompDict = getDeliveryAndComponetFromFlux(fluxInputfile, deliveryCompDict, sbxRoot)

    for file in fileSummary:
        if fluxDeliveryInfoAvailable == 0:
            # set everything to delivery, but leave component nit allocated
            fileSummary[file]['delivery'] = 'x'
            fileSummary[file]['comp'] = 'comp not allocated'
        else:
            if file in deliveryCompDict:
                fileSummary[file]['delivery'] = 'x'
                fileSummary[file]['comp'] = deliveryCompDict[file]['comp']
            else:
                fileSummary[file]['delivery'] = '-'
                fileSummary[file]['comp'] = 'comp not allocated'

    writelogPprint('deliveryCompDict', deliveryCompDict)

    ##----------------------------------------------------------------------------------------
    # Part 8 Team allocation
    ##----------------------------------------------------------------------------------------

    writelogPprint('teamAllocationDict', teamAllocationDict)

    for file in fileSummary:
        match = 0
        for filepath in teamAllocationDict:

            if re.search(filepath, file):
                fileSummary[file]['team'] = teamAllocationDict[filepath]
                match = 1

        if match == 0:
            fileSummary[file]['team'] = "team not allocated"

    for file in GHSwarnings:
        match = 0
        for filepath in teamAllocationDict:

            if re.search(filepath, file):
                GHSwarnings[file]['team'] = teamAllocationDict[filepath]
                match = 1

        if match == 0:
            GHSwarnings[file]['team'] = "team not allocated"

    for line in qaFindingDict:
        match = 0
        for filepath in teamAllocationDict:

            if re.search(filepath, qaFindingDict[line]['file']):
                qaFindingDict[line]['team'] = teamAllocationDict[filepath]
                match = 1

        if match == 0:
            qaFindingDict[line]['team'] = "team not allocated"

    outstring = timestamp() + ' allocate team to filelist\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 8 get usage of files in Variants from flist
    ##----------------------------------------------------------------------------------------

    usedInVariant = []
    usedInOneOfTheVariants = []

    # Evaluate all *_warninglog.log results from Compiler Warning summary output
    listOfFlistFiles = os.listdir('.')
    pattern = "*_flist.txt"
    for inputfile in listOfWarningLogFiles:
        if fnmatch.fnmatch(inputfile, pattern):
            # get variant Name out of filename e.g.Radar_C0_MXL_flist.txt
            matchvariant = re.search(r'(.+)_flist.txt', inputfile)
            if matchvariant:
                variantname = matchvariant.group(1)
            else:
                print("variant not found in  " + inputfile)

            getUsedInVariant(inputfile, usedInVariant, sbxRoot)

            title = 'used in Variant ' + variantname
            writelogPprint(title, usedInVariant)

            # add results from flist per variant to summary
            for sourcefile in usedInVariant:

                if sourcefile in fileSummary:
                    fileSummary[sourcefile][variantname] = "x"
                else:
                    print('file from Flist not in filesummary yet: ' + sourcefile)
                    fileSummary[sourcefile] = {}  # create subdict
                    fileSummary[sourcefile][variantname] = "x"

                # agregate used info
                if sourcefile not in usedInOneOfTheVariants:
                    usedInOneOfTheVariants.append(sourcefile)

            usedInVariant.clear()

    # add results from flist aggregated used in one of the variants to summary
    for sourcefile in usedInOneOfTheVariants:

        if sourcefile in fileSummary:
            fileSummary[sourcefile]['usedInOneOfTheVariants'] = "x"
        else:
            print('file from Flist not in filesummary yet: ' + sourcefile)
            fileSummary[sourcefile] = {}  # create subdict
            fileSummary[sourcefile]['usedInOneOfTheVariants'] = "x"

    outstring = timestamp() + ' get used in Variant\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 8 log filesummary
    ##----------------------------------------------------------------------------------------

    writelogPprint('fileSummary_initial', fileSummary)

    ##----------------------------------------------------------------------------------------
    # Part 9 generate output as csv for messages in files
    ##----------------------------------------------------------------------------------------

    outfilename = mypath + "\\warningSummary.csv"
    print('outfilename: ' + outfilename)
    # Open a file
    outfile = open(outfilename, "w")

    FileSummaryItemList = ['delivery',
                           'comp',
                           'team',
                           'L9',
                           'L8',
                           'L7',
                           'L6',
                           'L5',
                           'L4',
                           'L3',
                           'L2',
                           'L1',
                           'L0',
                           'GHSwarnings',
                           'filesystem',
                           'sourcetype',
                           'usedInOneOfTheVariants',
                           'GHSorigin',
                           'delivery_ipif',
                           'comp_guess_arch']

    for i in variantList:
        FileSummaryItemList.append(i)

    # Headline:
    writetofile = 'file;'
    for item in FileSummaryItemList:
        writetofile = writetofile + item + ';'

    writetofile = writetofile + '\n'
    outfile.write(writetofile)

    # one line per file in filesummary
    for file in (sorted(fileSummary.keys())):
        writetofile = file + ';'

        for item in FileSummaryItemList:
            if item in fileSummary[file]:
                writetofile = writetofile + str(fileSummary[file][item]) + ';'
            else:
                writetofile = writetofile + '0;'

        writetofile = writetofile + '\n'
        outfile.write(writetofile)

    outfile.close()

    outstring = timestamp() + ' write filelist\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 9a generate output as csv for GHS Warnings
    ##----------------------------------------------------------------------------------------

    outfilename = mypath + "\\GHSWarninglist.csv"
    print('outfilename: ' + outfilename)
    # Open a file
    outfile = open(outfilename, "w")

    writetofile = 'sourcefile' + ';' + 'warning' + ';' + 'warningText' + '\n'
    outfile.write(writetofile)
    print(writetofile)

    for sourcefile in (sorted(GHSwarnings.keys())):
        # for sourcefile in GHSwarnings:
        intermediateDict = GHSwarnings[sourcefile]['warnings']
        # if part of the delivery
        if sourcefile in deliveryCompDict:  # todo add condition to limit outpot too delivery depending on parameter
            for warning in intermediateDict:
                # if warning != 'origin': #todo ??? replace condition here by spliting "line 79: warning #1441-D" into "79" as lineno. and "#1441-D" as warningno.
                warningtext = intermediateDict[warning].replace(';', 'semicolon')
                writetofile = sourcefile + ';' + warning + ';' + warningtext + ';' + GHSwarnings[sourcefile][
                    'origin'] + ';' + GHSwarnings[sourcefile]['team'] + ';''\n'
                outfile.write(writetofile)
                # print(writetofile)

    outfile.close()

    outstring = timestamp() + ' write GHSWarninglist.csv\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 9b generate output as csv for GHS Warnings
    ##----------------------------------------------------------------------------------------

    outfilename = mypath + "\\GHSWarninglistAll.csv"
    print('outfilename: ' + outfilename)
    # Open a file
    outfile = open(outfilename, "w")

    writetofile = 'sourcefile' + ';' + 'warning' + ';' + 'warningText' + '\n'
    outfile.write(writetofile)
    print(writetofile)

    for sourcefile in (sorted(GHSwarnings.keys())):
        # for sourcefile in GHSwarnings:
        intermediateDict = GHSwarnings[sourcefile]['warnings']
        # if part of the delivery
        for warning in intermediateDict:
            # if warning != 'origin': #todo ??? replace condition here by spliting "line 79: warning #1441-D" into "79" as lineno. and "#1441-D" as warningno.
            warningtext = intermediateDict[warning].replace(';', 'semicolon')
            writetofile = sourcefile + ';' + warning + ';' + warningtext + ';' + GHSwarnings[sourcefile][
                'origin'] + ';' + GHSwarnings[sourcefile]['team'] + ';''\n'
            outfile.write(writetofile)
            # print(writetofile)

    outfile.close()

    outstring = timestamp() + ' write GHSWarninglist.csv\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 10 generate output as list output for QAframework findings
    ##----------------------------------------------------------------------------------------
    outfilename = mypath + "\\QAFrameworkWarningList.csv"
    print('outfilename: ' + outfilename)
    # Open a file
    outfile = open(outfilename, "w")

    QaFrameworkSummaryItemList = ['file',
                                  'line',
                                  'severity',
                                  'origin',
                                  'team',
                                  'commented',
                                  'comText']

    writetofile = ''

    # Headline:
    for item in QaFrameworkSummaryItemList:
        writetofile = writetofile + item + ';'

    writetofile = writetofile + '\n'
    outfile.write(writetofile)

    # one line per file in filesummary
    for file in (sorted(qaFindingDict.keys())):
        writetofile = ''
        # if part of the delivery and severity >=5 for C or >=8 for CPP files
        sourcefile = qaFindingDict[file]['file']
        if sourcefile in deliveryCompDict and sourcefile in fileSummary:
            if (int(qaFindingDict[file]['severity']) >= 5 and fileSummary[sourcefile]['sourcetype'] == 'C') \
                    or \
                    (int(qaFindingDict[file]['severity']) >= 8 and fileSummary[sourcefile][
                        'sourcetype'] == 'CPP'):  # todo add condition to limit outpot too delivery depending on parameter
                for item in QaFrameworkSummaryItemList:
                    if item in qaFindingDict[file]:
                        writetofile = writetofile + str(qaFindingDict[file][item]) + ';'
                    else:
                        writetofile = writetofile + '0;'

                writetofile = writetofile + '\n'
                outfile.write(writetofile)

    outfile.close()

    outstring = timestamp() + ' write QAFrameworkWarningList\n'
    writelog(outstring)

    # logfile.close()

    ##----------------------------------------------------------------------------------------
    # Part 11 generate output as list output for QAframework findings
    ##----------------------------------------------------------------------------------------
    outfilename = mypath + "\\QAFrameworkWarningListFull.csv"
    print('outfilename: ' + outfilename)
    # Open a file
    outfile = open(outfilename, "w")

    QaFrameworkSummaryItemList = ['file',
                                  'line',
                                  'msg',
                                  'msgText',
                                  'severity',
                                  'origin',
                                  'team',
                                  'commented',
                                  'comText']

    writetofile = ''

    # Headline:
    for item in QaFrameworkSummaryItemList:
        writetofile = writetofile + item + ';'

    writetofile = writetofile + '\n'
    outfile.write(writetofile)

    # one line per file in filesummary
    for file in (sorted(qaFindingDict.keys())):
        writetofile = ''
        # if part of the delivery and severity >=5 for C or >=8 for CPP files
        sourcefile = qaFindingDict[file]['file']
        if sourcefile in deliveryCompDict and sourcefile in fileSummary:
            if (int(qaFindingDict[file]['severity']) >= 5 and fileSummary[sourcefile]['sourcetype'] == 'C') \
                    or \
                    (int(qaFindingDict[file]['severity']) >= 8 and fileSummary[sourcefile][
                        'sourcetype'] == 'CPP'):  # todo add condition to limit outpot too delivery depending on parameter
                for item in QaFrameworkSummaryItemList:
                    if item in qaFindingDict[file]:
                        writetofile = writetofile + str(qaFindingDict[file][item]) + ';'
                    else:
                        writetofile = writetofile + '0;'

                writetofile = writetofile + '\n'
                outfile.write(writetofile)

    outfile.close()

    outstring = timestamp() + ' write QAFrameworkWarningList\n'
    writelog(outstring)

    ##----------------------------------------------------------------------------------------
    # Part 12 generate output as list output for QAframework findings
    ##----------------------------------------------------------------------------------------
    outfilename = mypath + "\\QAFrameworkWarningListFullAll.csv"
    print('outfilename: ' + outfilename)
    # Open a file
    outfile = open(outfilename, "w")

    QaFrameworkSummaryItemList = ['file',
                                  'line',
                                  'msg',
                                  'msgText',
                                  'severity',
                                  'origin',
                                  'team',
                                  'commented',
                                  'comText']

    writetofile = ''

    # Headline:
    for item in QaFrameworkSummaryItemList:
        writetofile = writetofile + item + ';'

    writetofile = writetofile + '\n'
    outfile.write(writetofile)

    # one line per file in filesummary
    for file in (sorted(qaFindingDict.keys())):
        writetofile = ''
        # if part of the delivery and severity >=5 for C or >=8 for CPP files
        sourcefile = qaFindingDict[file]['file']
        if sourcefile in fileSummary and 'sourcetype' in fileSummary[sourcefile]:
            if (int(qaFindingDict[file]['severity']) >= 5 and fileSummary[sourcefile]['sourcetype'] == 'C') \
                    or \
                    (int(qaFindingDict[file]['severity']) >= 8 and fileSummary[sourcefile][
                        'sourcetype'] == 'CPP'):  # todo add condition to limit outpot too delivery depending on parameter
                for item in QaFrameworkSummaryItemList:
                    if item in qaFindingDict[file]:
                        writetofile = writetofile + str(qaFindingDict[file][item]) + ';'
                    else:
                        writetofile = writetofile + '0;'

                writetofile = writetofile + '\n'
                outfile.write(writetofile)
        else:
            print ("QAF not listed no sourcefile or sourcetype " + sourcefile)

    outfile.close()

    outstring = timestamp() + ' write QAFrameworkWarningListFullAll\n'
    writelog(outstring)
    logfile.close()

    print('=====complete=====')

if __name__ == "__main__":

    main()
