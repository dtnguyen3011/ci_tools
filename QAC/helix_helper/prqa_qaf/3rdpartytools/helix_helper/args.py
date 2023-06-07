#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: args.py
# Author(s): Ingo Jauch CC-AD/ESW3 (Maintainer)
#            Andre Silva CC-AD/ESW3 (Maintainer)
# ----------------------------------------------------------------------------

import argparse
import sys


def _create_arguments_parser():
    parser = argparse.ArgumentParser(description='Helper for QA Framework')

    parser.add_argument(
        '-hcb',
        '--helper_create_baseline',
        help='If specified, a baseline will be created after an analysis run',
        choices=["no", "yes"],
        default="no")

    parser.add_argument(
        '-hsb',
        '--helper_set_baseline',
        help=
        'If specified, it will set an baseline when creating a new project from the baseline path'
    )

    parser.add_argument(
        '-ppp',
        '--prqa_project_path',
        help=
        'If this value overrides the project path specified in the json datastore'
    )

    parser.add_argument(
        '-hsc',
        '--helper_suppress_c_header',
        help=
        'If set to a yes value all C headers .h will be ignored in the anaylsis',
        choices=["no", "yes"],
        default="no")

    parser.add_argument(
        '-hsfa',
        '--helper_suppress_file_list_a',
        help=
        'Give the absolute path or relative path (relative to project repo folder) of a text file, which contains list of files to be excluded from the analysis',
        default="")

    parser.add_argument(
        '-hrfl',
        '--helper_remove_file_list',
        help=
        'Removes the given file list from the project (e.g. as workaround for fatal errors)',
        default="")

    parser.add_argument(
        '-hsfs',
        '--helper_suppress_file_list_s',
        help=
        'Give the absolute path or relative path (relative to project repo folder) of a text file, which contains list of files to be excluded from the sync',
        default="")

    parser.add_argument(
        '-pjb',
        '--project_buildlog_via_arg',
        help=
        'If specified, it uses the following json build log as input to create a prqa project. It will override the build log settings from the config file'
    )

    parser.add_argument('-dp',
                        '--datastore_path',
                        help='Absolute path to the prqa_helper config file',
                        required=True)

    parser.add_argument(
        '-pp',
        '--prqa_path',
        help='Absolute path to the directory where PRQA is installed',
        default='C:/TCC/Tools/prqa_framework/2.4.0_WIN64/common/bin')

    parser.add_argument('-dt',
                        '--datastore_target',
                        help='Project in map which holds the configuration')

    parser.add_argument('-pr',
                        '--project_root',
                        help='Project in map which holds the configuration')

    parser.add_argument('-pel',
                        '--prqa_error_level',
                        help='Set debugging level in prqa',
                        choices=['NONE', 'ERROR', 'INFO', 'DEBUG', 'TRACE'],
                        default='ERROR')

    parser.add_argument('-ht',
                        '--helper_target',
                        help='what to do',
                        choices=[
                            'create', 'analyze', 'report', 'gui', 'qavupload',
                            'qaview', 's101gen', 'state', 'state_no_metrics',
                            'export_state'
                        ],
                        default='create')

    parser.add_argument(
        '-sq',
        '--sonarqube',
        help=
        'Generate output message and MDR report for SonarQube Plugin from HIVE/DO-IT',
        choices=['yes', 'no'],
        default='no')

    parser.add_argument('-f',
                        '--file',
                        help='analyze single file',
                        default="no")

    parser.add_argument('-al',
                        '--analyse_list',
                        help='analyze all files contained in a list',
                        default="no")

    parser.add_argument('-vsc',
                        '--vscode_integration',
                        help='integrate output into ms vs code',
                        default="no")

    parser.add_argument(
        '-pbs',
        '--build_shell',
        help='false/true :use python build shell for running the build command',
        default=False)

    parser.add_argument(
        '-see',
        '--skip_exit_on_error',
        const=True,
        help=
        'false/true :if set then will ignore errors and continue execution',
        type=bool,
        nargs='?')

    return parser


def show_help_and_exit():
    """Parses arguments from commandline"""
    parser = _create_arguments_parser()
    parser.print_help()
    sys.exit(1)


def parse_arguments(args=None):
    """Parses arguments from commandline"""

    parser = _create_arguments_parser()
    if args:
        parsed_args = parser.parse_args(args)
    else:
        parsed_args = parser.parse_args()

    return vars(parsed_args)
