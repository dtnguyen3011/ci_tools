#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
#  C O P Y R I G H T
# ------------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
# ------------------------------------------------------------------------------
# Author: Pham Ngoc Thai (RBVH/EDA15)
# Date create: 26th Oct 2020
# Last modify: 19nd Nov 2020
# ==============================================================================

import re
import os
import sys
import in_place
import argparse


def parse_args():
    description = "Update SW header information for released a2l-db"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--header-file', required=True,
                        help='SW config header file')
    parser.add_argument('-f', '--a2l-file', required=True,
                        help='path a2l file')
    return parser.parse_args()


def sw_header_parser(swVersionCfg):
    try:
        sw_version = {}
        if swVersionCfg != None:
            # Open SW version configuration file
            with open(os.path.realpath(swVersionCfg), 'r') as swInfoFile:
                swInfo = re.findall(
                    r'\n(?!//)#define +\w+ +\S.*', swInfoFile.read())
                for statement in swInfo:
                    sw_version.update(
                        {statement.split()[1]: statement.split()[2]})
        print("[INFO] SW header : {}".format(sw_version))
        return sw_version
    except IOError:
        sys.exit("[ERROR] Problem for reading or writing SW version file.")


def update_a2l(a2lfile, replace):
    '''
    This function is to update info in a2l file
    with declared pattern as below
    '''
    sw_ver_line_pattern = re.compile(r'^\s*VERSION\s+\"\S+\"')
    sw_ver_pattern = re.compile(r'\"\S+\"')

    with in_place.InPlace(a2lfile) as file:
        for line in file:
            if bool(sw_ver_line_pattern.match(line)):
                line = sw_ver_pattern.sub(replace, line)
            else:
                line = line
            file.write(line)
    print("[INFO] Finish")

def main():
    '''
    This script is to update BUILD_SW_VERSION for release a2l support for MT_update job
    '''
    args = parse_args()
    sw_version = sw_header_parser(args.header_file)
    # Process SW info based on the convention provided by project: <MRR|LRR|ACA>E3<AUDI|VW><Release>>RC_<RC_Number> ==> [a-zA-Z]*\d+_RC\S+
    tmp = re.findall(r'[a-zA-Z0-9]{1}\d{3}_[\da-zA-Z\_\-]+', sw_version['BUILD_SW_VERSION'])
    a2l_sw_version = '\"' + tmp[0] + '\"'
    print("[INFO] SW VERSION", a2l_sw_version)
    update_a2l(args.a2l_file, a2l_sw_version)

if __name__ == "__main__":
    main()
