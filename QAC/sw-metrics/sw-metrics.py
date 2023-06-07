"""
    sw-metrics:
    script to collect file and line based sw-metics data like
    - CAC/CPP warnings by severity level
    - Compiler Warnings
    - ...
    along with aggrgation over different variants (and repos)
    - based on content of repo (filesystem), variant, .. were the findings are detected

    orgaized in 2 stages
    - do evaluation for a dedicated tool -> derive detailed report per tool
    - do summary over all tools just stating amount of findings per category
"""

import argparse
import os
import sys
import configparser
import re

# sys.path.append(os.path.join(os.path.dirname(__file__), "../..")) to be added for lucx
from lib import lucxlog, lucxargs

import QASystem_Radar_Default_full_QAF24
import evalViewLog


def get_args():
    desc = "sw-metrics:\nscript to collect file and line based sw-metics data like"
    parser = argparse.ArgumentParser(description=desc)
    parser = lucxargs.add_log_level(parser)
    parser.add_argument('-cf', '--changed-files', help='List of C or CPP files changed')
    parser.add_argument('-v', '--variant-list', help='List of build variants', required=True)
    parser.add_argument('--config', default='CONFIG')
    return parser.parse_args()


def upper(in_var):
    """ Just a dummy function to show the unittest framework. """
    return in_var.upper()



def write_ini_file(configFile):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {'ServerAliveInterval': '45',
                         'Compression': 'yes',
                         'CompressionLevel': '9'}
    config['bitbucket.org'] = {}
    config['bitbucket.org']['User'] = 'hg'
    config['topsecret.server.com'] = {}

    topsecret = config['topsecret.server.com']
    topsecret['Port'] = '50022'  # mutates the parser
    topsecret['ForwardX11'] = 'no'  # same here
    config['DEFAULT']['ForwardX11'] = 'yes'
    with open(configFile, 'w') as configfile:
        config.write(configfile)

def read_ini_file(configFile, sbxRoot, generatedFilesDir, qaclicfg, teamallocationtable):
    config = configparser.ConfigParser()
    # set configparser to keep results case sensitive
    config.optionxform = str

    LOGGER.info(configFile)
    config.read(configFile)

    sbxRootStr = re.sub(r"\s+", "", config['DEFAULT']['sbxRoot'], flags=re.UNICODE)  # remove whitespace
    sbxRoot += sbxRootStr.split(',')
    LOGGER.info(sbxRoot)

    generatedFilesDirStr = re.sub(r"\s+", "", config['DEFAULT']['generatedFilesDir'], flags=re.UNICODE) # remove whitespace
    generatedFilesDir += generatedFilesDirStr.split(',')
    LOGGER.info(generatedFilesDir)

    qaclicfg['qaclipath'] = config['QA-Framework']['qacli']

    qaConfListStr = config['QA-Framework']['qaConfList']
    qaConfListStr = re.sub(r"\s+", "", qaConfListStr, flags=re.UNICODE)  # remove whitespace
    qaclicfg['qaConfList'] = []
    qaclicfg['qaConfList'] += qaConfListStr.split(',')

    qaclicfg['doQacliAnalyze'] = config['QA-Framework']['doQacliAnalyze']

    qaclicfg['doQacliView'] = config['QA-Framework']['doQacliView']

    LOGGER.info(qaclicfg)


    for key in config['Team-Allocation']:
        teamallocationtable[key] = config['Team-Allocation'][key]

    LOGGER.info(teamallocationtable)
    LOGGER.info(config.sections())
    return config

def main():
    sbxRoot = []

    # variant list for aggregation of several variants provided as list from configfile
    # e.g. ['Radar_C0_MXL', 'DASY_INT_DEFAULT_ENH']
    variantList =[]

    generatedFilesDir = []

    # dict to store QAC Config
    # qaclicfg[qaclipath] qacli.exe with path
    # qaclicfg['qaConfList'][] list of qacconfigurarions
    # qaclicfg['doQacliAnalyze'] [True|False] do qaframework analysis
    # qaclicfg['doQacliView'] [True|False] do qaframework view export
    qaclicfg ={}

    # list of QA-Framework configurations for aggregation of several QA-Framework configurations provided as ',' separated list
    # e.g. ['C_ALL_FILES', 'C_CROSS_MODULE', 'C_DA_AD_FILES', 'CPP_ALL_FILES]
    qaConfList =[]

    # dict to store team allocation as lookup table
    # teamallocationtable['pathsnippet from Sandbox'] = 'teamname'
    # e.g. teamallocationtable['mom/daddy/']= 'MOM'
    teamallocationtable = {}

    args = get_args()
    LOGGER.setLevel(args.log_level)

    configFile = args.config
    print(configFile)
    #write_ini_file(configFile)

    variantList = args.variant_list.split(',')

    # get parameters from config file
    config = read_ini_file(configFile, sbxRoot, generatedFilesDir, qaclicfg, teamallocationtable)

    LOGGER.info('Main:')
    LOGGER.info(sbxRoot)
    LOGGER.info(generatedFilesDir)
    LOGGER.info(variantList)
    LOGGER.info(qaclicfg)
    LOGGER.info(teamallocationtable)
    LOGGER.info(args.changed_files)

    QASystem_Radar_Default_full_QAF24.main(sbxRoot, variantList, generatedFilesDir, qaclicfg, args.changed_files)
    evalViewLog.main(sbxRoot, variantList, generatedFilesDir, teamallocationtable)


if __name__ == "__main__":
    LOGGER = lucxlog.get_logger(__file__)
    main()

