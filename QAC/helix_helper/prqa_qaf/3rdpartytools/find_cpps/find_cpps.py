# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Usage: This is a script to help developers with the usage of the PRQA framework
#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2018 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: find_cpps.py
# Author(s):    Baumann Michael (CC-AD/EYC4)
#               Ingo Jauch CC-AD/ESW3 (Maintainer)
# ----------------------------------------------------------------------------
"""This script finds all cpp files which include given hpp/inl files, directly
or indirectly.

The main use case for this script is to support local QAC++ analysis using the
prqa_helper script[*], which is able to produce a lightweight PRQA
solution based only on the files which were modified in a pull request.

However, at the time of writing this find_cpps script, the prqa_helper script
had the following limitation: QAC++ can not analyze header files by themselves.
It always needs a cpp file. If a PR only modified a header file, but not a
corresponding cpp file, the prqa_helper script produces a PRQA solution which
does not contain the corresponding cpp files. Hence, the changes to the header
files might not be analyzed.

The find_cpps script offers a solution for this problem by taking a list of
file paths relative to a given repo root and producing a list of
corresponding cpp files. This list can then be supplied to the prqa_helper
script to produce a suitable PRQA solution.

In detail, this means:
- every cpp file in the input list is also written to the output list
- for every hpp/inl file in the input list, either
    * _all_ cpp files which (directly or indirectly) include that header file
      are written to the output list (option "all"), or
    * _one_ such cpp file is written to the output list (option "minimal").

A "minimal" output list leads to the smallest possible PRQA solution where all
modified files appear. However, it is currently not 100% certain whether this
would produce all QAC++ warnings that would have been produced when analyzing
the complete repository (in particular when the header files contain C++
template code).

A "complete" output list removes these uncertainties at the cost of a slightly
longer PRQA analysis time. However, in most cases, the analysis time will
still be significantly less than analyzing the whole repository.

By default, the find_cpps script:
- Assumes that it is called from somewhere within a git repository to
  be analyzed.
- Generates the input file list by producing the name-only git diff between
  the current git branch and its merge-base with origin/develop (like it
  would be done by the prqa_helper script). Note: local modifications which
  have not yet been committed to git are not considered in this list!
- Appends the output list of cpp files to the prqa_helper_file_list.txt in the
  current repository. This file can then be used with the prqa_helper script
  to produce the corresponding PRQA solution.

The find_cpps script can be customized (cf. --help) to:
- Consider an explicitly specified path to a repository.
- Take the file list from stdin instead of the git diff.
- Write the output list to stdout instead of the prqa_helper_file_list.txt.

[*] see https://sourcecode.socialcoding.bosch.com/projects/CDF/repos/prqa_helper/browse.

"""

import argparse
import itertools
import logging
from collections import defaultdict
import os
import re
import subprocess
import sys

HEADER_EXTENSIONS = ('.hpp', '.h', '.inl')
CPP_EXTENSIONS = ('.cpp', '.c', '.inl')
CPP_OUTPUT_EXTENSIONS = ('.cpp', '.c')
CODE_EXTENSIONS = CPP_EXTENSIONS + HEADER_EXTENSIONS
FILE_BLACKLIST_PATTERN = r'.*(_test_|_unittest_|_cantata_|_testHelper_|_buildReflections|dc_apl_test).*'
INCLUDE_SEARCH_PATTERN = r'#include\s+["<](.*)[>"]'

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())


def log_git_error_and_exit(error):
    """"Reports an error that happened while using the git command on the target directory"""
    LOG.error(
        '%s. Is the current directory (%s) under git version'
        ' control?', error, os.getcwd())
    sys.exit(1)


def get_top_level_repo_directory():
    """Returns the absolute path of the root of the git repository."""
    try:
        repo_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel']).strip().decode('utf-8')
        LOG.debug('Found repository root path: %s', repo_root)
        return repo_root
    except subprocess.CalledProcessError:
        log_git_error_and_exit('Could not find root of git repository')


def get_file_diff_from_head_to_merge_base(args):
    """ The function get_file_diff_from_head_to_merge_base gets the name of the files which were changed or added
        Output:
         normed_diff_as_list... Struct of a List with changed files name"""
    try:
        merge_base_hash = subprocess.check_output(
            ['git', 'merge-base', 'HEAD',
             args.merge_base]).strip().decode('utf-8')
        diff = subprocess.check_output(
            ['git', 'diff', 'HEAD', merge_base_hash,
             '--name-only']).strip().decode('utf-8')
        normed_diff_as_list = [
            os.path.normpath(path.strip()) for path in diff.split()
        ]
        LOG.debug(
            'File diff from HEAD to merge-base with origin/develop:\n%s',
            '\n'.join('    {}'.format(path) for path in normed_diff_as_list))
        return read_filepaths_from_lines(normed_diff_as_list)
    except subprocess.CalledProcessError:
        log_git_error_and_exit('Could not create git diff')


def convert_to_repo_relative_path(repo_filepath, filepath):
    """Convert a given path (as specified in an #include) to a path relative to the top level of a repository.
    :param filepath:            Path to convert.
    :param repo_filepath:       The repository base filepath
    :return:                    Path relative to top level of repository.
    """
    relpath = os.path.normpath(filepath)
    try:
        common_relative_path = os.path.commonpath([repo_filepath, relpath])
    except ValueError:
        common_relative_path = ''

    try:
        relpath = os.path.relpath(filepath, common_relative_path)
    except ValueError as error:
        # this can happen if for example replath is used on files on different harddrives
        LOG.error('Normalizing file %s with root %s failed due to %s',
                        filepath, common_relative_path, error)

    return relpath


def parse_included_files_in_file_content(file_content_as_list_of_lines):
    """Return all paths occurring in #include statements in the given file content.

    :param file_content_as_list_of_lines:   Content of a file, given as a list of lines.
    :return:    A sequence of paths included in the given file content.
    """
    for line in file_content_as_list_of_lines:
        match = re.search(INCLUDE_SEARCH_PATTERN, line)
        if match:
            yield match.group(1).strip()


def is_3rd_party_include(include_path, third_party_includes):
    """Check whether an include path points to a 3rd party component (vfc, Daddy, VMC).

    :param include_path:    Include path string to check.
    :return:                True if the path points to a 3rd party component, False else.
    """
    third_party_prefixes = []
    if third_party_includes:
        third_party_prefixes = read_file_list(third_party_includes)

    return any(prefix in include_path for prefix in third_party_prefixes)


def is_test_file(file_path):
    """Check whether a given path denotes a unit test file.

    :param file_path:   Path to be checked.
    :return:            True if the file is a unit test file (according to naming conventions), False else.
    """
    return re.match(FILE_BLACKLIST_PATTERN, file_path)


def is_code_file(file_path):
    """Check whether a given path denotes a C++ code file (not a unit test file).

    :param file_path:   Path to be checked.
    :return:            True if the file is a cpp, hpp, h or inl file and not a unit test file, False else.
    """
    has_code_extension = os.path.splitext(file_path)[1] in CODE_EXTENSIONS
    return has_code_extension and not is_test_file(file_path)


def is_header_code_file(file_path):
    """Check whether a given path denotes a C/C++ header file (not a unit test file).

    :param file_path:   Path to be checked.
    :return:            True if the file is a hpp/h/inl file and not a unit test file, False else.
    """
    has_header_extension = os.path.splitext(file_path)[1] in HEADER_EXTENSIONS
    return has_header_extension and not is_test_file(file_path)


def is_cpp_code_file(file_path):
    """Check whether a given path denotes a cpp file.

    :param file_path:   Path to be checked.
    :return:            True if the file is a cpp file and not a unit test file, False else.
    """
    has_cpp_extension = os.path.splitext(file_path)[1] in CPP_EXTENSIONS
    return has_cpp_extension and not is_test_file(file_path)


def get_fileid_from_path(header_filepath):
    return os.path.basename(header_filepath)


def create_mapping_of_file_to_all_direct_includers(repo_filepath,
                                                   search_directories,
                                                   third_party_includes):
    """Create a mapping which takes a file and returns a set of all direct includers of that given file.

    A direct includer of a given file is a C++ code file which contains an #include statement referring to the given
    file.

    :repo_filepath: Path to the root of the DC repository to analyze.
    :search_directories All directories to be in the search for the files.
    :return:            A function which takes a PJ-DC repo-relative file path and returns a set of PJ-DC repo-relative
                        file paths which denote direct includers of the specified file.
    """
    def get_all_code_file_paths():
        # Gets all paths from the "find_cpp_code_dirs.txt"
        code_file_paths = []
        for code_dir in search_directories:
            for parent_directory, _, file_names in os.walk(
                    os.path.join(repo_filepath, code_dir)):
                # Filters the filenames if it is a code
                code_file_names = filter(is_code_file, file_names)
                code_file_paths.extend(
                    os.path.join(parent_directory, f) for f in code_file_names)
        return code_file_paths

    dict_mapping_file_to_all_direct_includers = defaultdict(set)

    for code_file_path in get_all_code_file_paths():
        code_file_path_relative_to_repo = convert_to_repo_relative_path(
            repo_filepath, code_file_path)
        with open_with_utf8(code_file_path) as code_file:
            # Read the content of the *.c/*.cpp/*.h/*.hpp files
            code_file_content = code_file.readlines()
            include_paths = parse_included_files_in_file_content(
                code_file_content)
            # Filters the includes files and checks if their are third party path
            relevant_include_paths_relative_to_repo = [
                convert_to_repo_relative_path(repo_filepath, include_path)
                for include_path in include_paths
                if not is_3rd_party_include(include_path, third_party_includes)
            ]  #looks if the path isnt in the find_cpp_3rd_party_prefixes.txt data
        # Saves the abs. path of the h/hpp and c/cpp which are included in th c/cpp files
        for relevant_include_path in relevant_include_paths_relative_to_repo:
            dict_mapping_file_to_all_direct_includers[get_fileid_from_path(
                relevant_include_path)].add(code_file_path_relative_to_repo)
    # Sort and save the included path in a  with the argument file_path and the expression dict_mapping_file_to_all_direct_includers
    return lambda file_path: dict_mapping_file_to_all_direct_includers[
        get_fileid_from_path(file_path)]


def find_cpps_which_include_header_file(header_file_path,
                                        map_file_to_all_direct_includers):
    """Get a sequence of cpp files which include a given header file directly or indirectly.

    :param header_file_path:                    A repo-relative path to a C++ header file (hpp/h/inl).
    :param map_file_to_all_direct_includers:    A function which takes a file path and returns a sequence of all code
                                                files in the repository which include the specified file directly via an
                                                #include statement.
    :return: A generator object which produces a new cpp file including the given header file (directly or indirectly)
             with each iteration.
    """
    if not is_header_code_file(header_file_path):
        raise ValueError(
            '`header_file_path` is not a supported header file format.')

    # 'files_which_include_given_header_file' will be filled iteratively, starting with all direct includers
    files_which_include_given_header_file = map_file_to_all_direct_includers(
        header_file_path)

    found_cpps = set()
    while True:
        # Filters the founded included filenames if they are c/cpp codes
        cpp_files_which_include_given_header_file = filter(
            is_cpp_code_file, files_which_include_given_header_file)
        # Saves the c/cpp filenames
        for cpp_file in cpp_files_which_include_given_header_file:
            if cpp_file not in found_cpps:
                found_cpps.add(cpp_file)
                yield cpp_file

        files_which_include_given_file_indirectly = set(
            itertools.chain.from_iterable(
                map_file_to_all_direct_includers(f)
                for f in files_which_include_given_header_file))
        # Number of items and return None if no change or nothing was found
        old_number_of_includers = len(files_which_include_given_header_file)
        files_which_include_given_header_file.update(
            files_which_include_given_file_indirectly)
        new_number_of_includers = len(files_which_include_given_header_file)
        if new_number_of_includers == old_number_of_includers:
            return None


def remove_empty_lines_from_file(file_path):
    """Remove all empty lines from a given file.

    :param file_path: Path the the file.
    """
    with open_with_utf8(file_path) as file_in:
        lines = file_in.readlines()

    lines_without_empty_lines = [
        line for line in lines if not line.strip() == ''
    ]

    with open_with_utf8(file_path, mode='w+') as file_out:
        file_out.writelines(lines_without_empty_lines)


def find_cpps_for_header_files(header_files, repo_root, cpp_result_amount,
                               search_directories, third_party_includes):
    """ The function find_cpps_for_header_files calls the functions which are responsible to find the files and to create the generator
            Input:
                header_files...             Struct of Paths which has been changed from the user
                repo_root...                String path of the repo
                cpp_result_amount...        String of the Setting which have been to use
            Output:
                founded_cpps_header_files... Struct of a list which contains the filenames/path which header influenced c/cpps """
    # Detect all included files and writes the abs. path in that var.
    map_file_to_all_direct_includers = create_mapping_of_file_to_all_direct_includers(
        repo_root, search_directories, third_party_includes)

    cpp_paths_generators = [
        find_cpps_which_include_header_file(header_file,
                                            map_file_to_all_direct_includers)
        for header_file in header_files
    ]

    if cpp_result_amount == 'all':
        return set(itertools.chain.from_iterable(cpp_paths_generators))
    elif cpp_result_amount == 'minimal':
        return set(
            next(cpp_paths_generator, '')
            for cpp_paths_generator in cpp_paths_generators)
    else:
        raise ValueError(
            'The value "{}" is not supported for parameter `cpp_result_amount`.'
            .format(cpp_result_amount))


def setup_argument_parser():
    """Set up argparse command line argument parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--cpp-result-amount',
        choices=['all', 'minimal'],
        default='all',
        help=
        'Specify how many cpps to produce. For "all", a list of ALL cpps which include the given '
        'hpp/inl files (directly or indirectly) is produced. This is recommended when hpp/inl '
        'files contain C++ template code. For "minimal", a MINIMAL set of cpps which include the '
        'given hpp/inl files (directly or indirectly) is produced.')
    parser.add_argument(
        '--repo-root',
        help='Explicitly specify the PJ-DC repository to use. If not specified, '
        'it is assumed that the script is called from the repo to be used')
    parser.add_argument(
        '--to-stdout',
        action='store_true',
        help='Write results to stdout. Otherwise, the results are '
        'appended to the prqa_helper_file_list.txt in the '
        'repository root.')
    parser.add_argument('--from-stdin',
                        action='store_true',
                        help='Read file list from stdin. Otherwise, the file '
                        'list is taken from the git diff of the current '
                        'branch in the repository and its merge-base '
                        'with origin/develop.')
    parser.add_argument(
        '--from-list',
        help='Read file list from specified input file. Otherwise, the file '
        'list is taken from the git diff of the current '
        'branch in the repository and its merge-base '
        'with origin/develop.')
    parser.add_argument(
        '--merge_base',
        default="origin/develop",
        help='Which is the diff made against, default is origin/develop')
    parser.add_argument(
        '--code-dirs-file',
        help=
        'Absolute path to a file thats contains a list with folders (relative to the repo root) that should be scanned for includes'
    )
    parser.add_argument(
        '--prefixes',
        default=False,
        help=
        'Absolute path to a file thats contains a list with 3rdparty prefixes that will be excluded from the scan for includes'
    )
    parser.add_argument('--output_path',
                        default="prqa_helper_file_list.txt",
                        help='where to write the output as a file')
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('-v', '--verbose', action='store_true')
    verbosity_group.add_argument('-q', '--quiet', action='store_true')

    return parser


def set_logging_level(logging_arguments):
    """Set logging level depending on parsed command line arguments."""
    logging_level_dict = {
        'verbose': logging.DEBUG,
        'quiet': logging.ERROR,
        None: logging.INFO
    }

    active_flags = [arg for arg, active in logging_arguments if active]
    logging_level = next(iter(active_flags), None)
    LOG.setLevel(logging_level_dict.get(logging_level))


def check_command_line_arguments(args):
    """Verify correctness and consistency of parsed command line arguments."""
    assert args.cpp_result_amount in ('all', 'minimal')


def determine_repo_root_to_use(args):
    """Return the path to the repo root to be used, depending on the parsed command line arguments."""
    if args.repo_root:
        return os.path.abspath(os.path.normpath(args.repo_root))
    else:
        return get_top_level_repo_directory()


def read_filepaths_from_lines(line_or_lines):
    """Read filepaths one or several lines. These filepaths must be whitespace separated"""
    lines = None

    if isinstance(line_or_lines, list):
        lines = line_or_lines
    else:
        lines = [line_or_lines]

    # Converts a list of lists into a list leaving the empty strings out
    flatten = lambda list_of_lists: [
        item for a_list in list_of_lists for item in a_list if item
    ]

    return flatten(
        [filepaths_line.rstrip("\'\"\n").split() for filepaths_line in lines])


def open_with_utf8(filepath, mode="r"):
    """Opens a file with utf8 encoding and the given mode"""
    return open(filepath, mode=mode, encoding="utf-8", errors="replace")


def read_file_list(file_list_path):
    """Reads a filepath list from a given filepath"""
    file_list_path = os.path.abspath(file_list_path)
    if os.path.exists(file_list_path):
        filepaths = [line for line in open_with_utf8(file_list_path)]
        return read_filepaths_from_lines(filepaths)
    else:
        LOG.error('Could not read list: %s', file_list_path)
        sys.exit(1)


def norm_filepaths(filepaths, repo_root):
    """Normalized a list of filepaths by applying convert_to_repo_relative_path to each line"""
    normalized_lines = []
    for line in filepaths:
        norm_path = convert_to_repo_relative_path(repo_root, line)
        normalized_lines.append(norm_path)
    return normalized_lines

def get_input_files(args, repo_root):
    """Return the list of input files, depending on the parsed command line arguments."""
    if args.from_stdin:
        filepath_lines = sys.stdin.readlines()
        return read_filepaths_from_lines(norm_filepaths(filepath_lines, repo_root))
    elif args.from_list:
        return norm_filepaths(read_file_list(args.from_list), repo_root)
    else:
        os.chdir(repo_root)
        return get_file_diff_from_head_to_merge_base(args)


def create_output_producer(args, repo_root):
    """Create a function to produce the computed output list, depending on the parsed command line arguments.

    If args.to_stdout is True, the created function will print the output to stdout.
    Otherwise, it will append the output to the prqa_helper_file_list.txt in the defined PJ-DC repository.

    :param args:        Parsed command line arguments.
    :param repo_root:   Root of the PJ-DC repository to work in.
    :return:            A function which takes a list of cpp file paths, and writes them to the defined output.
    """
    if args.to_stdout:

        def output_producer(cpp_paths):
            for cpp_path in cpp_paths:
                print(cpp_path)

        return output_producer
    else:

        def output_producer(cpp_paths):
            list_file_path = os.path.join(repo_root, args.output_path)
            list_file = open_with_utf8(list_file_path, mode='w+')
            list_file.write(
                '\n'
            )  # in case the previous file content does not end with a newline
            list_file.write('\n'.join(cpp_paths).replace('\\', '/'))
            list_file.close()
            LOG.info('cpp paths have been written to %s', list_file_path)

            remove_empty_lines_from_file(list_file_path)
            LOG.debug('Removed empty lines from output file.')

        return output_producer


def initialize_search_directories(args, repo_filepath):
    """Initializes search directories according to the provided script parameters"""
    search_directories = None

    if args.code_dirs_file:
        search_directories = read_file_list(args.code_dirs_file)
    else:
        search_directories = [
            dirs for dirs in next(os.walk(repo_filepath))[1]
            if not ".git" in dirs
        ]

    return search_directories


def run():
    """Runs find_cpp by parsing the executable arguments"""
    # Transforming input arguments
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Precheck and gets data
    check_command_line_arguments(args)
    set_logging_level({(k, vars(args)[k]) for k in ('quiet', 'verbose')})
    repo_filepath = determine_repo_root_to_use(args)
    # By default search the repo dir for folder to search, otherwise use "whitelist"
    search_directories = initialize_search_directories(args, repo_filepath)
    input_files = get_input_files(args, repo_filepath)
    produce_output = create_output_producer(args, repo_filepath)

    LOG.debug('input files = %s', input_files)

    # Filtering and finding relevant filenames
    cpp_input_files = filter(is_cpp_code_file, input_files)
    header_input_files = list(filter(is_header_code_file, input_files))
    cpp_paths_input = set(cpp_input_files)

    third_party_includes = args.prefixes

    founded_cpps_header_files = find_cpps_for_header_files(
        header_input_files, repo_filepath, args.cpp_result_amount,
        search_directories, third_party_includes)

    LOG.debug('cpp paths input = %s', cpp_paths_input)
    LOG.debug('search directories = %s', search_directories)
    LOG.debug('third party includes = %s', third_party_includes)
    LOG.debug('founded cpp header files = %s', founded_cpps_header_files)

    cpp_paths = cpp_paths_input | founded_cpps_header_files
    cpp_paths = [
        cpp_path for cpp_path in cpp_paths
        if cpp_path.endswith(CPP_OUTPUT_EXTENSIONS)
    ]
    LOG.debug('output paths = %s', cpp_paths)

    produce_output(cpp_paths)


if __name__ == '__main__':
    run()
