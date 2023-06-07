#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2018 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: helix_commands.py
# Author(s): Ingo Jauch CC-AD/ESW4 (Maintainer)
#            Andre Silva CC-AD/ESW4 (Maintainer)
# ----------------------------------------------------------------------------
import os
import codecs
import sys

from subprocess import PIPE, Popen, CalledProcessError
from shlex import split
from time import time
from os import path

from logger import LOGGER
"""
Format export in the following custom format
    %u   Context message depth
    %F - File name (absolute, including path)
    %l - Line number
    %c - Column number
    %G - Rule group
    %p - Producer component (e.g. qacpp-3.1)
    %N - Message number (zero padded to four digits)
    %r - Rule text
    %t - Message text
    %Y - Severity
    %S - Suppression type bitmask
    %j - Suppression justification
"""
_FORMAT_SEQUENCE = [
    '%u', '%F', '%l', '%c', '%p:%N', '\\"%t\\"', '%Y', '%S', '\\"%j\\"',
    '\\"%G\\"', '\\"%r\\"'
]


def _ensure_utf8_in_output(a_output):
    if a_output.encoding.upper() != 'UTF-8':
        return codecs.getwriter('utf-8')(a_output.buffer, 'strict')
    return a_output


def ensure_utf8_stdout_call_once():
    """Forces output in utf-8 encoding. Must only be called once during initialization"""
    sys.stdout = _ensure_utf8_in_output(sys.stdout)
    sys.stderr = _ensure_utf8_in_output(sys.stderr)


def _decode_and_print_stdout_line(line, use_logger: bool, silent: bool):
    line_utf8 = line.decode('utf-8', errors='ignore').rstrip()
    if not silent:
        if use_logger:
            LOGGER.info('%s', line_utf8)
        else:
            print('{}\n'.format(line_utf8))

    return line_utf8


def _run_command(command_list: str, build_shell: bool, use_logger: bool,
                 silent: bool):
    output = ''
    # In an Unix system the commandline string needs to be split for proper parameter forwarding
    # and also it will break if parameters are bound directly to the command string
    command_string_or_list = command_list if sys.platform == 'win32' else split(
        command_list)
    command_process = Popen(command_string_or_list,
                            stdout=PIPE,
                            shell=build_shell)
    output = '\n'.join([
        _decode_and_print_stdout_line(line, use_logger, silent)
        for line in iter(command_process.stdout.readline, b'')
    ])
    command_process.stdout.close()
    command_process.wait()

    return (output, command_process.returncode)


# FIXME - Make it private, this should not be called directly (use decorator)
# And then remove default parameters values
def run_command(command_string: str,
                fast_fail: bool = True,
                build_shell: bool = False,
                use_logger: bool = True,
                silent: bool = False):
    """Runs commandline in a shell and gets it's output result"""
    return_code = 0
    output = ""
    start = time()
    LOGGER.info("# running command: %s, build_shell=%s", command_string,
                build_shell)

    try:
        (output, return_code) = _run_command(command_string, build_shell,
                                             use_logger, silent)
    except CalledProcessError as command_error:
        LOGGER.info("### %s", str(command_error))
        LOGGER.info(command_error.output)
        LOGGER.info("###")
        if fast_fail:
            sys.exit(command_error.returncode)
        return_code = command_error.returncode

    end = time()
    LOGGER.info("# running command finished: %s", end - start)
    return [output, return_code]


def command(fail_fast: bool = True,
            build_shell: bool = False,
            use_logger: bool = True,
            silent: bool = False):
    """Decorator for the 'run_command' function
    """
    def command_decorator(function):
        def function_wrapper(*args, **kwargs):
            command_list = function(*args, **kwargs)
            command_string = " ".join(command_list)
            return run_command(command_string,
                               fast_fail=fail_fast,
                               build_shell=build_shell,
                               use_logger=use_logger,
                               silent=silent)

        return function_wrapper

    return command_decorator


@command()
def set_license_server(config, sever_url: str):
    LOGGER.info("License server will be set to %s", sever_url)
    return [config.qacli, "admin", "--set-license-server", sever_url]


@command()
def list_license_server(config):
    return [config.qacli, "admin", "--list-license-servers"]


@command()
def check_license_server(config):
    return [config.qacli, "admin", "--check-license"]


@command()
def set_debug_level(config):
    return [config.qacli, "admin", "--debug-level", config.prqa_error_level]


@command(fail_fast=False)
def analyze_file(config, filepath, output_log_file):
    return [
        config.qacli, "analyze", "-P", config.prqa_project_path,
        "--output-progress", output_log_file, config.analyze_params, filepath
    ]


@command()
def set_default_config(config):
    return [
        config.qacli, "admin", "--qaf-project", config.prqa_project_path,
        "--set-default-config", "--config Initial"
    ]


@command()
def set_source_code_root(config):
    return [
        config.qacli, "admin", "--qaf-project", config.prqa_project_path,
        "--set-source-code-root", config.project_root
    ]


@command()
def list_config_files(config):
    return [
        config.qacli, "admin", "--qaf-project", config.prqa_project_path,
        "--list-config-files"
    ]


@command()
def export_report(config, report_type: str, ignore_dependencies: bool = False):
    """Exports a helix report using the report cmd line"""
    cmd_base = [config.qacli, "report"]
    args = []
    # This is used as a workaround for RCMA which can yield 
    # the report cmd unusable if files are out-of-date/sync
    if ignore_dependencies:
        args.append('--ignore')
    args.extend([
        "-P", "\"{}\"".format(config.prqa_project_path), "--type", report_type
    ])

    return [*cmd_base, *args]


@command()
def set_up_project(config, compiler_list, appendix: list):
    LOGGER.info("Creating PRQA project in:  %s", config.prqa_project_path)
    command_list = [
        config.qacli, "admin", "--qaf-project-config", "-P",
        config.prqa_project_path, compiler_list
    ]
    return command_list + appendix


@command(fail_fast=False, build_shell=True)
def export_project_overview(config):
    export_path = os.path.join(config.prqa_project_path, "qa_messages.txt")
    return [
        config.qacli, "view", "--qaf-project \"" + config.prqa_project_path +
        '" --medium STDOUT -r 2>&1 > "' + export_path + '"'
    ]


@command(fail_fast=False, build_shell=True)
def export_project_summary(config):
    """Exports a XML summary of the project current findings"""
    return [
        config.qacli,
        'view',
        '--qaf-project',
        '\"{}\"'.format(config.prqa_project_path),
        '-t SUMMARY -m XML -o',
        '\"{}\"'.format(config.prqa_report_path),
    ]


@command(fail_fast=False, build_shell=True, use_logger=False, silent=True)
def export_formatted_project_analysis(config):
    """Exports a formatted project analysis in a csv compliant format"""
    return [
        config.qacli, 'view', '--qaf-project',
        '\"{}\"'.format(config.prqa_project_path),
        '--suppressed-messages --rules --medium STDOUT --format',
        ','.join(_FORMAT_SEQUENCE)
    ]


@command(fail_fast=False)
def qac_suppress(config, module, filepath):
    return [
        config.qacli, "pprops --qaf-project",
        "\"" + config.prqa_project_path + "\"", "-c", module, "-O", filepath,
        "--set-options"
    ]


@command(fail_fast=False)
def sync_project_json(config, build_log):
    return [
        config.qacli, "sync", "--qaf-project",
        "\"" + config.prqa_project_path + "\"", "--type", "JSON", build_log
    ]


@command(fail_fast=False)
def sync_project_build_log(config, build_log: str):
    return [
        config.qacli, "sync", "--qaf-project",
        "\"" + config.prqa_project_path + "\"", "--type", "BUILD_LOG",
        build_log
    ]

# setting the relative path for the project for portable projects
@command(fail_fast=False)
def set_relative_project_path(config):
    prqa_path_to_root_relative_path = path.relpath(config.project_root, config.prqa_project_path)
    relative_project_path = path.join("""${PROJECT_ROOT}""", prqa_path_to_root_relative_path)
    return [
        config.qacli, 
        "admin", 
        "--qaf-project",
        "\"{}\"".format(config.prqa_project_path),
        "--set-project-root",
        "SOURCE_ROOT",
        "--path",
        relative_project_path
    ]
    
@command(fail_fast=False)
def remove_files_from_project(config):
    return [
        config.qacli, 
        "admin", 
        "--qaf-project",
        "\"{}\"".format(config.prqa_project_path),
        "-D", 
        config.helper_remove_file_list
    ]

@command(fail_fast=False)
def sync_project_monitor(config):
    return [
        config.qacli, "admin", "--qaf-project",
        "\"" + config.prqa_project_path + "\"", "-b", config.build_command
    ]


@command(fail_fast=False, build_shell=True)
def s101_gen(config):
    return [
        config.qacli, "upload", "--qaf-project", config.prqa_project_path,
        "--s101-upload", "--upload-location",
        os.path.join(config.prqa_project_path, "s101"), "2>&1"
    ]


@command()
def list_components(config):
    return [
        config.qacli, "pprops", "--qaf-project",
        "\"" + config.prqa_project_path + "\"", "--list-components"
    ]


@command(fail_fast=False, build_shell=True, use_logger=False)
def vscode_output(config):
    flist = ""
    if config.use_flist:
        flist = " " + str(config.analyze_file)

    return [
        config.qacli, "view", "--qaf-project", config.prqa_project_path,
        "--format \"%F:%l:%c: %p-%N-%r %t\"", "-m", "STDOUT" + flist, "2>&1"
    ]


@command()
def setup_baseline(config, baseline_path: str):
    return [
        config.qacli, "baseline", "-P", "\"" + config.prqa_project_path + "\"",
        "--baseline-type", "LOCAL", "--set-baseline", "--local-source",
        "\"" + baseline_path + "\""
    ]


@command()
def create_baseline(config):
    LOGGER.info("Baseline (files.sup) will be created in: " + os.path.join(
        config.prqa_project_path, "prqa", "configs", "Initial", "output"))
    return [
        config.qacli, "baseline", "-P", "\"" + config.prqa_project_path + "\"",
        "--baseline-type", "LOCAL", "--generate-baseline"
    ]


@command(fail_fast=False)
def apply_sync_filter(config, sync_filter: str):
    LOGGER.info("Applying sync filter for: " + sync_filter)
    return [
        config.qacli, "pprops", "--qaf-project",
        "\"" + config.prqa_project_path + "\"", "--sync-setting",
        "FILE_FILTER", "--set", sync_filter
    ]


def apply_sync_filters(config):
    for sync_filter in config.prqa_sync_filters:
        apply_sync_filter(config, sync_filter)


@command(fail_fast=False)
def apply_analysis_filter(config, module: str, analysis_filters_file: str):
    LOGGER.info(
        "Trying to apply PRQA_ANALYSIS_FILTERS for module: {}".format(module))
    return [
        config.qacli, "pprops", "--qaf-project",
        "\"" + config.prqa_project_path + "\"", "-c", module, "-O ",
        analysis_filters_file, "--set-options"
    ]


@command(fail_fast=False, build_shell=True)
def build_project_with_shell(config):
    LOGGER.info("### BUILDING PROJECT WITH SHELL ###")
    LOGGER.info("# changing dir path to " + config.project_root)
    os.chdir(config.project_root)
    return [config.build_command]


@command(fail_fast=False, build_shell=False)
def build_project_without_shell(config):
    LOGGER.info("### BUILDING PROJECT WITHOUT SHELL ###")
    LOGGER.info("# changing dir path to " + config.project_root)
    os.chdir(config.project_root)
    return [config.build_command]


def launch_gui(config):
    command = " ".join(
        [config.qagui, "--qaf-project", config.prqa_project_path])
    LOGGER.info(command)
    Popen(command)


@command(fail_fast=False, build_shell=True)
def upload_qaf_project(config, qavProjectName: str, qavProjectSnapshot: str,
                       qavUploadSource: str, qavServerUrl: str,
                       qavUsername: str, qavPassword: str):
    return [
        config.qacli, "upload", "--qaf-project", config.prqa_project_path,
        "--qav-upload", "--upload-project", qavProjectName, "--snapshot-name",
        qavProjectSnapshot, "--upload-source", qavUploadSource, "--url",
        qavServerUrl, "--username", qavUsername, "--password", qavPassword
    ]


@command(fail_fast=False)
def git_rev_parse(config):
    os.chdir(config.project_root)
    return ["git", "rev-parse", "--verify", "HEAD"]


@command(fail_fast=False)
def cli_version(config):
    os.chdir(config.project_root)
    return [config.qacli, "--version"]


@command(fail_fast=False)
def cli_config_folder(config):
    return [config.qacli, "admin --get-user-data-location"]


@command()
def set_namerule_config(config):
    return [
        config.qacli, "pprops", "--qaf-project", config.prqa_project_path,
        "-c", "namecheck-2.0.0", "-T", "C++", "-o", "nrf", "--set",
        config.ncf_file
    ]


@command(fail_fast=False)
def delete_file_to_optimize_project(config, optimization_workaround_path):
    return [
        config.qacli, "admin --qaf-project", config.prqa_project_path,
        "--optimize --remove-files", optimization_workaround_path
    ]
