#!/usr/bin/python
# ----------------------------------------------------------------------------
#Usage: This is a script to help developers with the usage of the PRQA framework
#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2018 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: check_qaview.py
# Author(s): Ingo Jauch CC-AD/ESW4 (Maintainer)
# ----------------------------------------------------------------------------
"""
The purpose of this script is parse the export of PRQA (via qaview command from helper) for
which serverity levels are contained in the export and then fail or pass the build on jenkins.

For example, if there are serveral servitylevel 8 warnings, 300 ID 4444, 9000 ID 1234 and 3000 ID 1239
in the export you could implement a jenkins gate to fail the build if there are 301 warnings via:
 python.exe check_qaview.py --qaview_csv qacli-view.csv -f8 301 -i 1234,1239
"""
import argparse
import csv
import os
import re
import subprocess
import sys
from contextlib import suppress

args = None

# Row indexes for particular information
index_IDs = 3
index_suppression_flag = 6
index_severity_level_info = 9

# Levels from 0 to 9
levels = range(10)


def usage_message():
    message = "python prqa_helper.py -qacsv / --qaview_csv [path to qaview export]\n"
    for level in reversed(levels):
        message += (f"                      -f{level} / --fail{level} "
                    "[script will fail if warnings exceed this integer]\n")
    message += "                      -i / --ignore [IDs that can be ignored]\n"
    return message


def argumentparser():
    parser = argparse.ArgumentParser(
        description='Helper for QA Framework',
        usage=usage_message(),
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-qacsv',
                        '--qaview_csv',
                        help='path to qaview export file',
                        required=True)
    parser.add_argument(
        '-i',
        '--ignore',
        help='error IDs that can be ignored (as a CSV list)',
    )
    for level in reversed(levels):
        parser.add_argument(
            f"-f{level}",
            f"--fail{level}",
            help='script will fail if warnings exceed this integer',
        )

    return parser.parse_args()


def print_number_of_found_issues(issues_dict):
    print("TOTAL FOUND ISSUES:")
    for level in reversed(levels):
        print(f"total_number_of_severitylevel{level}: " +
              str(issues_dict.get(f"total_number_of_severitylevel{level}")))
    print(f"project_total_warnings: " +
              str(issues_dict.get(f"project_total_warnings")))
    print("")


def print_number_of_open_issues(issues_dict):
    print("OPEN/UNSUPPRESSED ISSUES:")
    for level in reversed(levels):
        print(f"open_number_of_severitylevel{level}: " +
              str(issues_dict.get(f"open_number_of_severitylevel{level}")))
    print(f"project_open_warnings: " +
              str(issues_dict.get(f"project_open_warnings")))
    print("")


def list_of_open_issue_level(issues_dict):
    open_issues = []
    for level in reversed(levels):
        if not getattr(args, f"fail{level}"):
            continue
        if issues_dict.get(f"open_number_of_severitylevel{level}")> int(
                getattr(args, f"fail{level}")):
            open_issues.append(str(level))
    return open_issues


def match_severity_level(item: str):
    """Returns a match or None"""
    return re.search(r"severitylevel(?P<level>\d)", item)


def get_severity_level(item):
    """Get the severity level of the warning
    Args:
        item (str): row item with severity level info
    Returns:
        int: severity level. If no level is found, return None
    """
    match = match_severity_level(item)
    if match:
        return int(match.group("level"))
    return None


def count_number_of_issues(csv_list, IDs_to_ignore_tuple = ()):

    # Containers for number of warnings
    total_number_of_severitylevel = [0] * 10
    total_number_of_severitylevel_bitmask_comment = [0] * 10
    total_number_of_severitylevel_bitmask_pragma = [0] * 10
    total_number_of_severitylevel_bitmask_baseline = [0] * 10
    open_number_of_severitylevel = [0] * 10
    project_total_warnings = 0
    project_open_warnings = 0

    issues_dict = {}
    for row in csv_list:
        # Suppress rows that don't correspond to warnings
        with suppress(IndexError):
            level = get_severity_level(row[index_severity_level_info])
            if not level:
                continue
            total_number_of_severitylevel[level] += 1
            project_total_warnings += 1
            if not any(s in row[index_IDs] for s in IDs_to_ignore_tuple):
                # check bitmask types and count accordingly, at this point, we ignore dashboard types
                if row[index_suppression_flag] == "0":
                    open_number_of_severitylevel[level] += 1
                    project_open_warnings += 1
                if row[index_suppression_flag] == "1":
                    total_number_of_severitylevel_bitmask_comment[level] += 1
                if row[index_suppression_flag] == "4":
                    total_number_of_severitylevel_bitmask_baseline[level] += 1
                if row[index_suppression_flag] == "5":
                    total_number_of_severitylevel_bitmask_pragma[level] += 1
    
    for level in levels:
        issues_dict.update({f"total_number_of_severitylevel{level}": total_number_of_severitylevel[level]})
        if (level >= 8):
            issues_dict.update({f"total_number_of_severitylevel{level}_suppression_bitmask_comment": total_number_of_severitylevel_bitmask_comment[level]})
            issues_dict.update({f"total_number_of_severitylevel{level}_suppression_bitmask_baseline": total_number_of_severitylevel_bitmask_baseline[level]})
            issues_dict.update({f"total_number_of_severitylevel{level}_suppression_bitmask_pragma": total_number_of_severitylevel_bitmask_pragma[level]})
        issues_dict.update({f"open_number_of_severitylevel{level}": open_number_of_severitylevel[level]})
    issues_dict.update({f"project_total_warnings": project_total_warnings})
    issues_dict.update({f"project_open_warnings": project_open_warnings})
    return issues_dict

def file_has_problems():
    if not os.path.isfile(args.qaview_csv):
        return True
    return False


if __name__ == "__main__":
    args = argumentparser()

    if file_has_problems():
        print("ERROR")
        print("File \"" + str(args.qaview_csv) + "\" is not readable")
        sys.exit(1)

    arg_IDs_to_ignore_tuple = args.ignore.split(',') if args.ignore else ()
    print(f"IDs that were ignored: {arg_IDs_to_ignore_tuple} \n")

    with open(args.qaview_csv) as csv_file:
        file_content = csv_file.read()

    csv_from_output = csv.reader(file_content.split('\n'),
                          delimiter=',',
                          quotechar='"')    
    
    issues_dict = count_number_of_issues(csv_from_output, arg_IDs_to_ignore_tuple)

    print_number_of_found_issues(issues_dict)
    print_number_of_open_issues(issues_dict)

    open_issue_level = list_of_open_issue_level(issues_dict)
    if open_issue_level:
        print("\nOpen/Unsuppressed Issues of level(s) {} found!".format(
            ", ".join(open_issue_level)))
        sys.exit(1)