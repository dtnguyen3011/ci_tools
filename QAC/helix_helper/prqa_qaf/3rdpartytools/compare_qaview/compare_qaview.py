#!/usr/bin/env python
"""Script for comparing of qaview csv's"""

import csv
import argparse
import sys


def parse_arguments():
    """Parsing of command line arguments

    Returns:
        dict: arguments
    """
    parser = argparse.ArgumentParser(
        description=
        'Compare a subset of qaview findings to a full set of qaview findings',
        formatter_class=argparse.RawTextHelpFormatter)

    required = parser.add_argument_group('required arguments')
    required.add_argument('--input_file')
    required.add_argument('--compare_file')

    return vars(parser.parse_args())


def parse_qaview_csv(file_path: str):
    """Parses a qaview csv an returns a dict with qaview findings  and severity levels

    Args:
        file_path (str): Path to qaview csv file

    Returns:
        dict: Maps qaview findings to severity level
    """
    findings = dict()

    with open(file_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        for row in csv_reader:
            if row and len(row) == 10:
                # key:   file name + line number
                # value: severity level
                key = "{}_line{}_column{}".format(row[0], row[1], row[2])
                findings[key] = ",".join(row)

    return findings


def compare_qaview_paths(input_data: dict, compare_data: dict):
    """Checks if all qaview findings in compare_data are contained in input_data as well

    Args:
        input_data (dict): Full set of findings
        compare_data (dict): Sub set of findinds

    Returns:
        dict: Missing data
    """
    findings = dict()

    for [key, value] in compare_data.items():
        if key in input_data:
            continue
        findings[key] = value

    return findings


def print_missing_paths(missing_data: dict):
    """Prints all qaview findings that are missing in the full set

    Args:
        missing_data (dict): Missing data
    """
    for value in missing_data.values():
        print(value)


if __name__ == "__main__":
    args = parse_arguments()

    if not all(args.values()):
        print("""
        Not all arguments given.
        Arguments:
        --input_file   <file> : Full set of findings
        --compare_file <file> : Sub set of findinds
        """)
        sys.exit(1)

    INPUT_FILE = args["input_file"]
    COMPARE_FILE = args["compare_file"]

    INPUT_DATA = parse_qaview_csv(INPUT_FILE)
    COMPARE_DATA = parse_qaview_csv(COMPARE_FILE)

    MISSING_DATA = compare_qaview_paths(INPUT_DATA, COMPARE_DATA)
    print_missing_paths(MISSING_DATA)
