#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: config_parser.py
# Author(s): Ingo Jauch CC-AD/ESW3 (Maintainer)
#            Andre Silva CC-AD/ESW3 (Maintainer)
# ----------------------------------------------------------------------------
"""Configurations parsing utilities"""

import config
import re
from sys import platform

from args import parse_arguments, show_help_and_exit
from json import loads
from logger import LOGGER
from os import path
from sys import exit

_ARGS_PARSE_CONFIG = [
    ('analyse_list', config.ANALYZE_LIST),
    ('build_shell', config.USE_PYTHON_BUILD_SHELL),
    ('datastore_path', config.DATASTORE_PATH),
    ('datastore_target', config.DATASTORE_TARGET),
    ('file', config.ANALYZE_FILE),
    ('helper_create_baseline', config.HELPER_CREATE_BASELINE),
    ('helper_remove_file_list', config.HELPER_REMOVE_FILE_LIST),
    ('helper_set_baseline', config.HELPER_SET_BASELINE),
    ('helper_suppress_c_header', config.HELPER_SUPPRESS_C_HEADER),
    ('helper_suppress_file_list_a', config.HELPER_SUPPRESS_FILE_LIST_A),
    ('helper_suppress_file_list_s', config.HELPER_SUPPRESS_FILE_LIST_S),
    ('helper_target', config.HELPER_TARGET),
    ('project_buildlog_via_arg', config.PROJECT_BUILDLOG_VIA_ARG),
    ('project_root', config.PROJECT_ROOT),
    ('prqa_error_level', config.PRQA_ERROR_LEVEL),
    ('prqa_helper_script_path', config.PRQA_HELPER_SCRIPT_PATH),
    ('prqa_path', config.PRQA_PATH),
    ('prqa_project_path', config.PRQA_PROJECT_PATH),
    ('skip_exit_on_error', config.SKIP_EXIT_ON_ERROR),
    ('sonarqube', config.USE_SONARQUBE),
    ('vscode_integration', config.USE_VSCODE_INTEGRATION),
]


def load_json_with_comments(filepath):
    """Loads a JSON file from a given filepath and loads it. It can contain // based comments"""
    with open(filepath) as file_with_comments:
        config_file_without_comments = re.sub(r'^\s*//.*\n', '',
                                              file_with_comments.read(), 0,
                                              re.MULTILINE)
        return _with_keys_in_lowercase(loads(config_file_without_comments))


def parse_configuration_dicts(prqa_helper_filepath, args=None):
    prqa_helper_script_path = path.dirname(prqa_helper_filepath)
     
    parsed_args = {
        **parse_arguments(args),
        **{
            config.PRQA_HELPER_SCRIPT_PATH: prqa_helper_script_path
        }
    }

    return _parse_configuration_dicts(parsed_args)


def _create_parsed_config(parsed_config):
    return {
        pair[0]: pair[1]
        for pair in [
            _get_args_or_none(parsed_config.get(k), v)
            for (k, v) in _ARGS_PARSE_CONFIG
        ] if pair
    }


def _get_first_valid_config_of_two(first, second, config_name):
    return _get_first_str_or_second_if_none(first.get(config_name),
                                            second.get(config_name))


def _get_first_valid_config_of_three(first, second, third, config_name):
    result = _get_first_str_or_second_if_none(first.get(config_name),
                                              second.get(config_name))

    return result if result else third.get(config_name)


def _get_first_str_or_second_if_none(first: str, second: str):
    if first:
        return first

    return second


def _get_args_or_none(arg: str, config_name: str):
    if arg:
        arg_value = arg

        return (config_name, arg_value)

    return None


def _update_path_related_variables_in_parsed_config(parsed_config: dict,
                                                    config_from_file: dict,
                                                    target_config: dict,
                                                    datastore_target):

    datastore_target = _get_config_arg_or_target_and_exit_on_failure(
        parsed_config, config_from_file, config.DATASTORE_TARGET)
    project_root = path.normpath(
        _get_config_arg_or_target_or_general_and_exit_on_failure(
            parsed_config, target_config, config_from_file,
            config.PROJECT_ROOT))
    prqa_project_path = path.normpath(
        _get_config_arg_or_target_or_general_and_exit_on_failure(
            parsed_config, target_config, config_from_file,
            config.PRQA_PROJECT_PATH))
    if not path.isabs(prqa_project_path):
        prqa_project_path = path.join(project_root, prqa_project_path)

    # REVERSED Order - This is a hack to make the PRQA_PATH easily overwritten by the config file
    # to force using a specific version. The underlying problem is that the commandline always provides
    # a default so it would always override this.
    prqa_path = path.normpath(
        _get_config_arg_or_target_or_general_and_exit_on_failure(
            config_from_file, target_config, parsed_config, config.PRQA_PATH))

    if "win" in platform.lower():        
        QACLI_COMMAND = 'qacli.exe'
        QACGUI_COMMAND = 'qagui.exe'   
    else:   
        QACLI_COMMAND = 'qacli'
        QACGUI_COMMAND = 'qagui'  
    qacli = path.join(prqa_path, QACLI_COMMAND)
    qagui = path.join(prqa_path, QACGUI_COMMAND)


    parsed_config.update({
        config.QACLI: qacli,
        config.QAGUI: qagui,
        config.PRQA_PATH: prqa_path,
        config.PROJECT_ROOT: project_root,
        config.DATASTORE_TARGET: datastore_target
    })


def _return_self_or_exit_if_none(config_name, config_value):
    error_msg = 'Missing %s definition either in configs.'
    if not config_value:
        LOGGER.error(error_msg, config_name)
        show_help_and_exit()

    return config_value


def _get_config_arg_or_target_or_general_and_exit_on_failure(
        first_config, second_config, third_config, config_name):
    config_value = _get_first_valid_config_of_three(first_config,
                                                    second_config,
                                                    third_config, config_name)

    return _return_self_or_exit_if_none(config_name, config_value)


def _get_config_arg_or_target_and_exit_on_failure(first_config, second_config,
                                                  config_name):
    config_value = _get_first_valid_config_of_two(first_config, second_config,
                                                  config_name)

    return _return_self_or_exit_if_none(config_name, config_value)


def _parse_configuration_dicts(parsed_config: dict):
    LOGGER.debug("datastore_path = %s", parsed_config[config.DATASTORE_PATH])

    config_from_file = load_json_with_comments(
        parsed_config[config.DATASTORE_PATH])

    datastore_target = _get_config_arg_or_target_and_exit_on_failure(
        parsed_config, config_from_file, config.DATASTORE_TARGET).lower()
    LOGGER.debug("datastore_target = %s", datastore_target)

    target_config = _with_keys_in_lowercase(config_from_file[datastore_target])
    parsed_config = _create_parsed_config(parsed_config)

    config_from_file = {
        k: config_from_file[k]
        for k in config_from_file if k in config.BASE_CONFIG_LEVEL
    }
    target_config = {
        k: target_config[k]
        for k in target_config if k in config.TARGET_CONFIG_LEVEL
    }

    _update_path_related_variables_in_parsed_config(parsed_config,
                                                    config_from_file,
                                                    target_config,
                                                    datastore_target)

    LOGGER.info(
        "\n\nparsed config = %s\n\nconfig_from_file = %s\n\n target_config = %s\n\n",
        parsed_config, config_from_file, target_config)

    return (parsed_config, config_from_file, target_config)


def _with_keys_in_lowercase(to_convert: dict):
    return {key.lower(): to_convert[key] for key in to_convert}
