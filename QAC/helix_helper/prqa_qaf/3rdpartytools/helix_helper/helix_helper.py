#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Usage: This is a script to help developers with the usage of the HELIX framework
# =============================================================================
#  C O P Y R I G H T
# -----------------------------------------------------------------------------
#  Copyright (c) 2018 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
# =============================================================================
# Filename: helix_helper.py
# Author(s): Ingo Jauch CC-AD/ESW4 (Maintainer)
#            Andre Silva CC-AD/ESW4 (Maintainer)
# ----------------------------------------------------------------------------

import csv
import json
import os
import re
import shutil
import sys
import stat
from zipfile import ZipFile, ZIP_DEFLATED

from time import sleep
from datetime import datetime
from args import parse_arguments
from config import Config
from config_parser import load_json_with_comments, parse_configuration_dicts
from file_transfer import copy_file_to_local_target_if_source_in_shared_folder
from logger import LOGGER, initialize
from helix_commands import *
from helix_version import HelixVersion
from project_state import ProjectState, REGEX_FOR_ANALYSIS_LOG_STRING, DEPRECATED_CSV_HEADER_WITH_FILENAME
from html_exporter import create_html_from_list_of_lists, LICENSE_WARNING
from suppress import *
from os import path
from glob import glob
from xml.dom import minidom
from sys import platform
from state_exporter import create_exports, create_csv_analysis, create_html_analysis, convert_qacli_view_to_summary, filter_csv_values_for_serverity_8_and_9

# python version check, to ensure that the correct python version is used
assert sys.version_info >= (3, 6)

_MODULE_NAME = 'HELIX_HELPER'


def _safe_remove_file(filepath):
    try:
        os.remove(filepath)
        LOGGER.info('File removed: %s', filepath)
        return True
    except OSError as error:
        LOGGER.warning('Could not remove file %s due to %s', filepath, error)
        return False


def _safe_delete_dirtree(directory):
    filepath_tree_depth = len(directory.split(path.sep))
    system_tree_depth_threshold = 3
    # Avoids problems as this can be a rather dangerous operation one should
    # check if this is not a system file or root of user home folder for instance
    if path.exists(
            directory) and filepath_tree_depth >= system_tree_depth_threshold:
        LOGGER.info('Deleting directory = %s', directory)
        shutil.rmtree(directory, ignore_errors=True, onerror=None)
        # Avoids async deletion problems
        max_retries = 32768
        retries = 0
        while path.exists(directory) and retries < max_retries:
            retries += 1


def _cleanup_project(config):
    # make sure we clean any old projects
    _safe_delete_dirtree(config.prqa_project_path)

    os.makedirs(config.prqa_project_path, exist_ok=True)
    os.makedirs(os.path.join(config.prqa_project_path, "s101"), exist_ok=True)
    os.makedirs(os.path.join(config.prqa_project_path, "custom_config"),
                exist_ok=True)
    os.makedirs(config.helper_logs_path, exist_ok=True)
    os.makedirs(os.path.join(config.helper_logs_path, "analysis"),
                exist_ok=True)
    os.makedirs(os.path.join(config.helper_logs_path, "qavupload"),
                exist_ok=True)
    os.makedirs(os.path.join(config.helper_logs_path, "export"), exist_ok=True)
    os.makedirs(config.via_path, exist_ok=True)
    _cleanup_exports(config)


def _cleanup_exports(config):
    export_path = os.path.join(config.prqa_project_path, "helper_logs",
                               "export")
    _safe_delete_dirtree(export_path)
    os.makedirs(export_path, exist_ok=True)
    _safe_delete_dirtree(config.prqa_report_path)
    os.makedirs(config.prqa_report_path, exist_ok=True)


def create_prqa_project(config, compiler_list, rcf, acf, vcf, ncf, messages):
    return_value = 0
    config_files_pair = [
        ('rcf', rcf),
        ('acf', acf),
        ('vcf', vcf),
        ('ncf', ncf),    # this ncf config style is deprecated with HELIX
        ('user-messages', messages)
    ]

    command_string = '{} admin --qaf-project-config -P {} {} {}'.format(
        config.qacli, config.prqa_project_path, compiler_list, ' '.join([
            '--{} {}'.format(param, config_file)
            for (param, config_file) in config_files_pair if config_file
        ]))
    [output, return_value] = run_command(command_string)

    set_relative_project_path(config)
    set_default_config(config)
    set_source_code_root(config)
    # disabled listing of config files since it takes up to 30sec
    # list_config_files(config)
    # HELIX conformal ncf config:
    # set_namerule_config(config)
    return return_value


def report(config, report_type, copy_to_reports: bool = True):
    def _get_ignore_dependencies_flag():
        helix_version = HelixVersion(config.cli_version_string)
        (major, minor) = helix_version.major_minor()
        return helix_version.is_helix() and major >= 2019 and minor >= 2

    output_path = config.prqa_report_path
    report_path = os.path.join(config.prqa_project_path, "report")
    export_report(config, report_type, _get_ignore_dependencies_flag())
    if copy_to_reports:
        try:
            _safe_delete_dirtree(report_path)
            shutil.copytree(output_path, report_path)
            LOGGER.info("Report folder copied to project root %s", report_path)
        except shutil.Error as e:
            LOGGER.error("Failed copying report folder: %s", e)
    return report_path


def export_qa_message(config):
    _, returncode = export_project_overview(config)
    if returncode == 2 or returncode == 0:
        LOGGER.info(
            "Export okay, Return code 2 equals Command Processing Failure, please check logs for findings"
        )
    else:
        LOGGER.error("view export Return code: " + str(returncode))
        sys.exit(returncode)


def _export_qacli_view(config):
    csv_values = ProjectState(config).get_analysis_csv_values()
    create_csv_analysis(config, config.project_git_commit, csv_values)
    only_8_and_9_csv_values = filter_csv_values_for_serverity_8_and_9(
        csv_values)
    create_html_analysis(config, config.project_git_commit,
                         only_8_and_9_csv_values)
    convert_qacli_view_to_summary(config, csv_values)


def _create_project_state(config, metrics: bool):
    def _has_summary_export():
        helix_version = HelixVersion(config.cli_version_string)
        (major, minor) = helix_version.major_minor()

        return helix_version.is_helix() and major > 2019 or minor >= 2

    _cleanup_exports(config)
    # Generates results_data.xml and json files
    if metrics:
        report(config, 'HMR', copy_to_reports=False)
    # Generates severity_summary.xml
    if _has_summary_export():
        export_project_summary(config)
    # Creates unified state.json
    state = ProjectState(config).create()
    with ZipFile(config.state_filepath, 'w',
                 compression=ZIP_DEFLATED) as state_file:
        state_file.writestr('state.json', json.dumps(state))
        LOGGER.info('Created successfully a state dump of the project at %s',
                    config.state_filepath)


def save_output(prqa_project_path, log_name, output):
    save_build_path = os.path.join(prqa_project_path, "helper_logs", "output")
    os.makedirs(save_build_path, exist_ok=True)
    output_log_file = os.path.join(save_build_path, log_name)
    LOGGER.info("Saving output log to: " + output_log_file)
    with open(output_log_file, "w") as output_file:
        output_file.write(output)


def save_build_log(prqa_project_path, build_log):
    save_build_path = os.path.join(prqa_project_path, "helper_logs", "build")
    os.makedirs(save_build_path, exist_ok=True)
    build_log_file = os.path.join(save_build_path, "build.log")
    LOGGER.info("Saving build log to: " + build_log_file)
    shutil.copy(build_log, build_log_file)


def sync_project(config):
    LOGGER.info("### SYNC PROJECT ###")
    return_value = 0
    os.chdir(config.project_root)
    sync_type = config.prqa_sync_type
    if sync_type in ("JSON", "BUILD_LOG"):
        LOGGER.info("# using build log: " + config.build_log)
    if sync_type == "JSON":
        json_filter_string = config.json_filter
        build_log = config.build_log
        if json_filter_string:
            build_log = _use_json_sync_filter(json_filter_string, build_log)
        save_build_log(config.prqa_project_path, build_log)
        if config.helper_suppress_file_list_s:
            LOGGER.info("### SUPPRESS FILE IN STATIC LIST FOR SYNC###")
            file_list_path_s = config.helper_suppress_file_list_s
            LOGGER.info("Use sync suppression list: " + file_list_path_s)
            build_log = suppress_file_in_static_list_s(config, build_log,
                                                       file_list_path_s)
        [output, return_value] = sync_project_json(config, build_log)
        return return_value
    elif sync_type == "BUILD_LOG":
        build_log = config.build_log
        if config.helper_suppress_file_list_s:
            LOGGER.info("### SUPPRESS FILE IN STATIC LIST FOR SYNC###")
            file_list_path_s = config.helper_suppress_file_list_s
            LOGGER.info("Use sync suppression list: " + file_list_path_s)
            build_log = suppress_file_in_static_list_s_build_log(
                config.project_root, build_log, file_list_path_s)
        [output, return_value] = sync_project_build_log(config, build_log)
        return return_value
    elif sync_type == "MONITOR":
        [output, return_value] = sync_project_monitor(config)
        # sys.exit(1) # commented out since it is not testable otherwise
        return return_value
    else:
        LOGGER.error("Unknown helper sync type")
        sys.exit(1)
        return -1


def _use_json_sync_filter(json_filter_string, build_log):
    LOGGER.info("# using JSON filters: " + json_filter_string)
    r1 = re.compile(json_filter_string)

    modified_buildlog = build_log + ".tmp"

    modified_json = []
    with open(build_log, "rt") as fin:
        data = json.load(fin)
        LOGGER.info("Original JSON length: %s", len(data))
        for item in data:
            if r1.search(item['file']):
                modified_json.append(item)
    LOGGER.info("Filtered JSON length: %s", len(modified_json))
    with open(modified_buildlog, "wt") as fout:
        json.dump(modified_json,
                  fout,
                  sort_keys=True,
                  indent=4,
                  ensure_ascii=False)
    return modified_buildlog


def check_for_custom_help(config, file_to_check):
    if config.custom_help_path:
        LOGGER.info("Using custom help")
        help_keyword = "__bosch_help__"
        modified_file = path.join(config.prqa_project_path, 'custom_config',
                                  'custom_rcf.xml')
        os.makedirs(path.dirname(modified_file), exist_ok=True)
        with open(file_to_check, "rt") as fin:
            with open(modified_file, "wt") as fout:
                for line in fin:
                    fout.write(
                        line.replace(help_keyword, config.custom_help_path))
        return modified_file

    return file_to_check


def check_and_replace_component_path_in_xml(config, xml_in_filepath: str):
    def get_prqa_component_path(component_name):
        def is_component_name_in_prqa_path(component_path, target_component):
            component_name = path.basename(component_path).rsplit(
                '-')[0].lower()
            return target_component.lower() == component_name

        # TODO - Workaround to avoid changing all the script behavior to expect the
        # prqa_path to be the root of the PRQA package and not the bin folder
        prqa_components_path = config.prqa_path
        common_bin_rel_path = path.join('common', 'bin')
        if common_bin_rel_path in config.prqa_path:
            prqa_components_path = path.normpath(
                path.join(config.prqa_path, '..', '..', 'components'))

        for component_filepath in glob('{}\\**'.format(prqa_components_path)):
            if is_component_name_in_prqa_path(component_filepath,
                                              component_name):
                return component_filepath

        return None

    help_keyword = '__component_path__'
    LOGGER.info('config.prqa_project_path= {} xml_in_filepath= {}'.format(
        config.prqa_project_path, xml_in_filepath))

    xml_out_filepath = path.join(config.prqa_project_path, 'custom_config',
                                 'custom_messages.xml')

    with open(xml_in_filepath, 'r', encoding='utf-8',
              errors='replace') as xml_in_file:
        xml_in_content = xml_in_file.read()
        if not help_keyword in xml_in_content:
            LOGGER.info(
                'Not creating a new messages file due to absence of %s',
                help_keyword)
            return xml_in_filepath

        LOGGER.info('Using custom cpp help')
        dom_tree = minidom.parseString(xml_in_content)
        messages = dom_tree.getElementsByTagName('messages')
        for message in messages:
            component_name = message.getAttribute('component')
            component_filepath = get_prqa_component_path(component_name)
            if component_filepath != None:
                for component_message in message.getElementsByTagName(
                        'message'):
                    help_attribute = component_message.getAttribute('help')

                    if help_keyword in help_attribute:
                        component_message.setAttribute(
                            'help',
                            help_attribute.replace(help_keyword,
                                                   component_filepath))
            else:
                LOGGER.error("component not found: " + component_name)
        with open(xml_out_filepath, "w+") as output_file:
            xml_content = dom_tree.toprettyxml(newl='')
            output_file.write(xml_content)

        return xml_out_filepath


def check_for_qa_msg(config, file_to_check):
    qa_help_keyword = "__qa_help__"

    LOGGER.info("file_to_check= %s", file_to_check)
    LOGGER.info("config.prqa_project_path= %s", config.prqa_project_path)

    modified_file = path.join(config.prqa_project_path, 'custom_config',
                              'custom_messages.xml')
    with open(file_to_check, "rt") as fin:
        fin_content = fin.read()

        if qa_help_keyword in fin_content:
            LOGGER.info("Using built-in prqa help")
            with open(modified_file, "wt") as fout:
                for line in fin.readlines():
                    fout.write(
                        line.replace(qa_help_keyword, config.qa_help_path))

            return modified_file

    return file_to_check


def check_if_project_exists(prqa_project_path):
    if not os.path.exists(prqa_project_path):
        LOGGER.error("prqa project not found, cant continue: " +
                     prqa_project_path)
        sys.exit(1)


def get_log_timestamp():
    file_timestamp = datetime.today().strftime('%Y%m%d_%H%M%S.%f')[:-3]
    return file_timestamp


def analyze_project(config):
    def analyze_file_and_check(a_file):
        output_log_file = os.path.join(
            config.analysis_path,
            "analyze_output_{}.log".format(get_log_timestamp()))
        [_, return_value] = analyze_file(config, a_file, output_log_file)
        check_analysis_output_for_nonzeros(config, output_log_file,
                                           return_value)
        return return_value

    clean_analysis_logs(config.prqa_log_path)
    return_value = 0
    if config.analyze_list != "no":
        file_list_path = os.path.abspath(config.analyze_list)
        if os.path.exists(file_list_path):
            _return_value = analyze_file_and_check('-F  {}'.format(file_list_path))
            return_value = _return_value if _return_value != 0 else 0
        else:
            LOGGER.error("The file {} doesn't exist!".format(file_list_path))
            sys.exit(1)

    elif config.use_flist:
        return_value = analyze_file_and_check(config.analyze_file)
    else:
        # empty files analyzes the whole project
        return_value = analyze_file_and_check("")

    save_analysis_logs(config)

    return return_value


def check_analysis_output_for_nonzeros(config, output_log_file, return_value):
    def _log_errors_and_exit_if_necessary(failed_files):
        if len(failed_files) > 0:
            LOGGER.error("Found %s with non-0 exit codes.", len(failed_files))
            with open(output_log_file.replace("analyze_output_",
                                              "analyze_failures_"),
                      "w+",
                      encoding='utf-8') as output_file:
                output_file.writelines(failed_files)
        if return_value != 0:
            LOGGER.error(
                "Analysis failed with return code %s. Failed files = %s",
                return_value, failed_files)
            if not config.skip_exit_on_error:
                # Saves log files before exiting
                save_analysis_logs(config)
                sys.exit(return_value)

    LOGGER.info('Checking out analysis output for potential failures')
    failed_files = []

    if not path.exists(output_log_file):
        LOGGER.warning("Analysis log not found: %s", output_log_file)
        return

    with open(output_log_file, "r") as analysis_log:
        analysis_log_content = analysis_log.read()
        for match in re.finditer(REGEX_FOR_ANALYSIS_LOG_STRING,
                                 analysis_log_content, re.MULTILINE):
            prqa_returncode = match.group('return_code')
            if prqa_returncode != "0":
                match_string = 'path={}, module={}, return_code={}'.format(
                    match.group('path'), match.group('module'),
                    match.group('return_code'))
                if match.group('timestamp'):
                    match_string = '{}, timestamp={}'.format(
                        match_string, match.group('timestamp'))
                LOGGER.error(match_string)
                failed_files.append(match_string)
        _log_errors_and_exit_if_necessary(failed_files)


def save_analysis_logs(config):
    log_artifact_dir = config.analysis_path
    logs_dir = config.prqa_log_path
    LOGGER.info("Saving logs from %s to %s", logs_dir, log_artifact_dir)

    if os.path.exists(config.prqa_log_path):
        os.makedirs(log_artifact_dir, exist_ok=True)
        filelist = os.listdir(logs_dir)
        for filepath in filelist:
            LOGGER.info("Saving file %s", filepath)
            shutil.copy(os.path.join(logs_dir, filepath), log_artifact_dir)
    else:
        LOGGER.info("Nothing to save in %s", logs_dir)


def clean_analysis_logs(logs_dir):
    LOGGER.info("# Cleaning logs: " + logs_dir)
    if path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            _safe_remove_file(path.join(logs_dir, filename))
    else:
        LOGGER.info("# Nothing to clean in %s", logs_dir)


def check_buildlog(config):
    sync_type = config.prqa_sync_type
    if sync_type in ["JSON", "BUILD_LOG"]:
        LOGGER.info("### CHECKING BUILD LOG ###")
        # build log from args has priority, and we dont build
        if config.project_buildlog_via_arg:
            build_log = os.path.normpath(
                os.path.join(config.project_root,
                             os.path.normpath(
                                 config.project_buildlog_via_arg)))
        else:
            build_log = os.path.normpath(
                os.path.join(config.project_root,
                             os.path.normpath(config.build_log)))
            if config.build_command:
                if config.use_python_build_shell:
                    build_project_with_shell(config)
                else:
                    build_project_without_shell(config)
            else:
                LOGGER.info(
                    "INFO: No build command provided in config, skipping build."
                )
        exists = os.path.isfile(build_log)
        if exists:
            return build_log
        else:
            LOGGER.error("No buildlog found, cant continue")
            sys.exit(1)


def apply_analysis_filters(config):
    # without modules we cant continue
    modules = config.prqa_modules
    if modules:
        LOGGER.info("PRQA_MODULES found")
        # check if we have any filters, otherwise we dont have anything to do
        if config.prqa_analysis_filters:
            LOGGER.info("PRQA_ANALYSIS_FILTERS found")
            # transform the analysis_filters into a file for performance reasons
            filter_files = config.prqa_analysis_filters
            LOGGER.info('Using analysis_filters = %s', filter_files)
            with open(os.path.join(config.via_path, "analysis_filter.via"),
                      "w+") as f:
                for line in filter_files:
                    f.write("-q " + line + "\n")
            # apply fitlers to each module
            for module in modules:
                LOGGER.info("appyling PRQA_ANALYSIS_FILTERS to module " +
                            module)
                apply_analysis_filter(
                    config, module,
                    os.path.join(config.via_path, "analysis_filter.via"))


def create_new_project(config):
    LOGGER.info("### CREATING NEW PRQA PROJECT ###")
    return_value = 0
    _cleanup_project(config)
    # pre processing config
    absolute_rcf = check_for_custom_help(config, config.rcf_file)
    LOGGER.info('cwd = %s, user_messages = %s', os.getcwd(),
                config.user_messages)
    absolute_messages = check_for_qa_msg(config, config.user_messages)
    absolute_messages = check_and_replace_component_path_in_xml(
        config, absolute_messages)
    absolute_vcf = config.vcf_file
    absolute_ncf = config.ncf_file
    absolute_acf = config.acf_file
    compiler_list = ' '.join([
        '--cct {}'.format(compiler) for compiler in config.compiler_list
    ]).rstrip()

    LOGGER.info(
        'cwd = %s, acf = %s, ncf = %s, rcf = %s, vcf = %s, user_messages = %s',
        os.getcwd(), absolute_acf, absolute_ncf, absolute_rcf, absolute_vcf,
        absolute_messages)
    return_value = create_prqa_project(config, compiler_list, absolute_rcf,
                                       absolute_acf, absolute_vcf,
                                       absolute_ncf, absolute_messages)

    LOGGER.info("### APPLYING PRQA SYNC FILE FILTERS ###")
    apply_sync_filters(config)

    LOGGER.info("### APPLYING PRQA ANALYSIS FILE FILTERS ###")
    apply_analysis_filters(config)

    LOGGER.info("### SETTING LICENSE SERVERS ###")
    list(map(lambda x: set_license_server(config, x), config.license_servers))

    if config.verbose:
        LOGGER.info("### LISTING SERVERS ###")
        list_license_server(config)

        LOGGER.info("### CHECKING LICENSE ###")
        check_license_server(config)

    LOGGER.info("### SETTING DEBUG LEVEL ###")
    set_debug_level(config)

    if config.verbose:
        LOGGER.info("### LIST COMPONENTS ###")
        list_components(config)

    if config.helper_suppress_c_header:
        LOGGER.info("### SUPPRESS C HEADER ###")
        suppress_c_header(config)

    if config.helper_suppress_file_list_a:
        LOGGER.info("### SUPPRESS FILE IN STATIC LIST FOR ANALYSIS###")
        file_list_path_a = config.helper_suppress_file_list_a
        LOGGER.info(file_list_path_a)
        suppress_file_in_static_list_a(config, file_list_path_a)
    return return_value


def optimize_helix_project(config):
    """
    Starting with Helix2019.1 an "optimize" flag was introduced to remove duplicates in the project.xml.
    This increases the performance in projects with a lot of files in it.
    Currently the only way to "trigger" this optimization is to add/remove a file. 
    Hence we remove a not existing file from the project.
    """
    if HelixVersion(config.cli_version_string).is_helix():
        LOGGER.info("### OPTIMIZE HELIX PROJECT ###")
        optimization_workaround_path = os.path.join(config.prqa_project_path,
                                                    "custom_config",
                                                    "helix_optimization.txt")
        with open(optimization_workaround_path,
                  "w") as optimization_workaround_file:
            # \n is placed to indicate EOL (End of Line)
            optimization_workaround_file.write(
                "helix_optimization_workaround_file.cpp\n")
            _ = delete_file_to_optimize_project(config,
                                                optimization_workaround_path)
            LOGGER.info(
                "### OPTIMIZE done, non-zero exit status 2 is okay here ###")


def upload_to_qa_verify(config):
    def get_env_or_exit_if_none(name: str):
        value = os.environ.get(name)
        if not value:
            LOGGER.error("Environment variable {} is missing".format(name))
            sys.exit(1)
        return value

    LOGGER.info("### UPLOAD TO QAVERIFY ###")
    qav_project_name = get_env_or_exit_if_none('QAV_PROJECT_NAME')
    qav_project_snapshot = get_env_or_exit_if_none('QAV_PROJECT_SNAPSHOT')
    qav_server_url = get_env_or_exit_if_none('QAV_SERVER_URL')
    qav_username = get_env_or_exit_if_none('QAV_USERNAME')
    qav_password = get_env_or_exit_if_none('QAV_PASSWORD')
    qav_upload_source = get_env_or_exit_if_none('QAV_UPLOAD_SOURCE')

    [output, return_value
     ] = upload_qaf_project(config, qav_project_name, qav_project_snapshot,
                            qav_upload_source, qav_server_url, qav_username,
                            qav_password)
    save_output(config.prqa_project_path,
                "qavupload_output_{}.log".format(get_log_timestamp()), output)

    if return_value != 0:
        LOGGER.error("Dashboard \"qavupload\" failed with return code %s",
                     return_value)


def set_and_update_baseline(config, baseline_path):
    if baseline_path:
        norm_baseline_path = path.normpath(baseline_path)
        local_baseline_path = path.join(config.prqa_project_path, "prqa",
                                        "configs", "Initial", "output")
        final_baseline_path = copy_file_to_local_target_if_source_in_shared_folder(
            norm_baseline_path, local_baseline_path, 'files.sup')
        setup_baseline(config, final_baseline_path)


def set_baseline(config):
    baseline_path = config.helper_set_baseline
    if config.local_baseline_path:
        baseline_path = config.local_baseline_path
    set_and_update_baseline(config, baseline_path)


def run():
    ensure_utf8_stdout_call_once()
    initialize(_MODULE_NAME)
    prqa_helper_filepath = os.path.realpath(__file__)
    (parsed_config, general_config,
     target_config) = parse_configuration_dicts(prqa_helper_filepath)

    config = Config(general_config, target_config, parsed_config)

    if config.helper_target != "create":
        check_if_project_exists(config.prqa_project_path)

    if config.helper_target == "create":
        # this step verifies if we have a working build to fail fast,
        # otherwise we could call it before sync
        build_log = check_buildlog(config)
        create_new_project(config)
        set_baseline(config)
        sync_project(config)
        optimize_helix_project(config)
        # Feature to remove files (compilation units) from a qac project (after sync, monitor etc)
        # that should not be analyzed, maybe because they cause a fatal error that has no other workaround
        if config.helper_remove_file_list:
            os.chdir(config.project_root)
            if os.path.exists(config.helper_remove_file_list):
                LOGGER.info("Removing Files from project")
                [_output, _return_value] = remove_files_from_project(config)
            else:
                LOGGER.warning(
                    "Option helper_remove_file_list set but file does not exist"
                )
    elif config.helper_target == "analyze":
        analyze_project(config)
        if config.helper_create_baseline:
            create_baseline(config)
        if config.use_vscode_integration != "no":
            vscode_output(config)
    elif config.helper_target == "report":
        report(config, 'RCR')
    elif config.helper_target == "qavupload":
        upload_to_qa_verify(config)
    elif config.helper_target == "gui":
        launch_gui(config)
    elif config.helper_target == "s101gen":
        s101_gen(config)
    elif config.helper_target == "state":
        _create_project_state(config, metrics=True)
        create_exports(config, metrics=True, summary_details=True)
    elif config.helper_target == "state_no_metrics":
        _create_project_state(config, metrics=False)
        create_exports(config, metrics=False, summary_details=True)
    elif config.helper_target == "qaview":
        _export_qacli_view(config)
        if config.use_sonarqube:
            export_qa_message(config)
            report(config, 'MDR')
    elif config.helper_target == "export_state":
        create_exports(config, metrics=True, summary_details=True)
    else:
        LOGGER.error("Unknown option for helper")
        sys.exit(1)
    LOGGER.info("- done -")


if __name__ == "__main__":
    run()
