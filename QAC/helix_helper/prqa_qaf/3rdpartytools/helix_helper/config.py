# =============================================================================
#  C O P Y R I G H T
# -----------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
# =============================================================================
# Filename: config.py
# Author(s): Ingo Jauch CC-AD/ESW4 (Maintainer)
#            Andre Silva CC-AD/ESW4 (Maintainer)
# ----------------------------------------------------------------------------
"""Shared HELIX project variables"""

from logger import LOGGER
from os import path, environ
from args import show_help_and_exit
from helix_commands import cli_version, cli_config_folder, git_rev_parse

# CONFIG/PARSING VARIABLES
_ACF_FILE = 'acf_file'
ANALYZE_FILE = 'analyze_file'
ANALYZE_LIST = 'analyze_list'
ANALYZE_PARAMS = 'analyze_params'
_BUILD_COMMAND = 'build_command'
_BUILD_LOG = 'build_log'
_COMPILER_LIST = 'compiler_list'
_CUSTOM_HELP_PATH = 'custom_help_path'
DATASTORE_PATH = 'datastore_path'
DATASTORE_TARGET = 'datastore_target'
HELPER_CREATE_BASELINE = 'helper_create_baseline'
HELPER_REMOVE_FILE_LIST = 'helper_remove_file_list'
HELPER_SET_BASELINE = 'helper_set_baseline'
HELPER_SUPPRESS_C_HEADER = 'helper_suppress_c_header'
HELPER_SUPPRESS_FILE_LIST_A = 'helper_suppress_file_list_a'
HELPER_SUPPRESS_FILE_LIST_S = 'helper_suppress_file_list_s'
HELPER_TARGET = 'helper_target'
JSON_FILTER = 'json_filter'
_LICENSE_SERVERS = 'license_servers'
_LOCAL_BASELINE_PATH = 'local_baseline_path'
QACLI = 'qacli'
QAGUI = 'qagui'
_NCF_FILE = 'ncf_file'
PROJECT_BUILDLOG_VIA_ARG = 'project_buildlog_via_arg'
PROJECT_ROOT = 'project_root'
PRQA_ANALYSIS_FILTERS = 'prqa_analysis_filters'
PRQA_ERROR_LEVEL = 'prqa_error_level'
PRQA_HELPER_SCRIPT_PATH = 'prqa_helper_script_path'
PRQA_MODULES = 'prqa_modules'
PRQA_PROJECT_PATH = 'prqa_project_path'
PRQA_PATH = 'prqa_path'
PRQA_SYNC_FILTERS = 'prqa_sync_filters'
PRQA_SYNC_TYPE = 'prqa_sync_type'
_RCF_FILE = 'rcf_file'
SKIP_EXIT_ON_ERROR = 'skip_exit_on_error'
USE_PYTHON_BUILD_SHELL = 'use_python_build_shell'
USE_SONARQUBE = 'use_sonarqube'
USE_VSCODE_INTEGRATION = 'use_vscode_integration'
_USER_MESSAGES = 'user_messages'
_VCF_FILE = 'vcf_file'
CLI_VERSION_STRING = 'cli_version_string'

BASE_CONFIG_LEVEL = {
    _ACF_FILE, ANALYZE_LIST, ANALYZE_PARAMS, _COMPILER_LIST, _CUSTOM_HELP_PATH,
    DATASTORE_TARGET, _LICENSE_SERVERS, _LOCAL_BASELINE_PATH, _NCF_FILE, QACLI,
    QAGUI, PROJECT_ROOT, PRQA_ERROR_LEVEL, PRQA_MODULES, PRQA_PATH,
    PRQA_SYNC_TYPE, _RCF_FILE, USE_PYTHON_BUILD_SHELL, _USER_MESSAGES,
    USE_SONARQUBE, USE_VSCODE_INTEGRATION, _VCF_FILE, CLI_VERSION_STRING
}

TARGET_CONFIG_LEVEL = {
    *BASE_CONFIG_LEVEL, ANALYZE_FILE, _BUILD_COMMAND, _BUILD_LOG,
    DATASTORE_TARGET, HELPER_REMOVE_FILE_LIST, HELPER_SET_BASELINE,
    HELPER_SUPPRESS_C_HEADER, HELPER_SUPPRESS_FILE_LIST_A,
    HELPER_SUPPRESS_FILE_LIST_S, HELPER_TARGET, JSON_FILTER, PRQA_PROJECT_PATH,
    PRQA_ANALYSIS_FILTERS, PRQA_SYNC_FILTERS, SKIP_EXIT_ON_ERROR
}


def _is_filepath_only_basename(filepath):
    return not path.dirname(path.normpath(filepath))


class Config:
    """Class that abstracts the three hierarchical levels of configuration. \
    Read-only access to the variables themselves. This is immutable by design"""
    _REQUIRED_VARIABLES = [
        _ACF_FILE, QACLI, QAGUI, PROJECT_ROOT, PRQA_PROJECT_PATH, PRQA_PATH,
        PRQA_SYNC_TYPE, _RCF_FILE, _VCF_FILE
    ]

    def __init__(self, general_config: dict, target_config: dict,
                 commandline_config: dict):
        self._general_config = general_config
        self._target_config = target_config
        self._commandline_config = commandline_config
        self._load_environment_variables()
        self._check_for_required_variables()
        self._determine_helix_configuration_path()

    def _load_environment_variables(self):
        LOGGER.info('Loading Environment Variables')
        self._verbose = bool(environ.get('VERBOSE'))
        LOGGER.info('VERBOSE is: %s', self._verbose)

    def _check_for_helix_installation(self):
        if not path.exists(self.qacli):
            LOGGER.error('Helix executable could not be found in path %s. %s',
                         self.qacli,
                         'Please install it with TCC, iSM or manually.')
            show_help_and_exit()

    def _determine_helix_configuration_path(self):
        """Determines the helix configuration path based on the Helix version and the OS.
        e.g
            If PRQA and Linux           -> /home/my_username/.config/PRQA. 
            If Helix 2019.1 and Windows -> C:\\Users\\my_username_\\AppData\\Local\\Perforce\\2019.1_WIN64"""
        self._check_for_helix_installation()
        self._cli_version_string = cli_version(self)[0]
        helix_base_path = path.dirname(
            path.dirname(path.normpath(self.prqa_path)))
        helix_config_basename = path.basename(helix_base_path)

        os_config_folder = path.normpath(
            cli_config_folder(self)[0].split('=')[1].strip())
        self._helix_config_path = path.join(os_config_folder,
                                            helix_config_basename)

    def _check_for_required_variables(self):
        missing_variables = {
            var
            for var in self._REQUIRED_VARIABLES
            if self._get_commandline_target_or_general_config(var) is None
        }
        if missing_variables:
            LOGGER.error('The following variables are missing = %s',
                         missing_variables)
            show_help_and_exit()

    def _get_absolute_path_or_relative_to_project_root(self, config_path):
        config_path = path.normpath(config_path)
        return config_path if path.isabs(config_path) else path.join(self.project_root, config_path)

    def _get_final_path_if_config_exists(self, path_config_name):
        config_path = self._get_commandline_target_or_general_config(
            path_config_name)
        return self._get_absolute_path_or_relative_to_project_root(
            config_path) if config_path else None

    def _get_config_folder_relative_path(self, default_relative_path,
                                         filepath):
        return path.join(self._helix_config_path, default_relative_path,
                         filepath)

    def _get_config_path(self, path_config_name, default_relative_path):
        """Gets a configuration normalized path given a configuration name and a relative default path as an input. 
        If only the basename is provided e.g. messages.xml , then the configuration will be figured depending on the
        OS, Helix version and the default_relative_path parameter e.g. user_library/user_messages . Otherwise, it is
        going to be calculated according to the prqa_project_path"""
        filepath = self._get_commandline_target_or_general_config(
            path_config_name)
        if filepath and _is_filepath_only_basename(filepath):
            return self._get_config_folder_relative_path(
                default_relative_path, filepath)
        return self._get_final_path_if_config_exists(path_config_name)

    def _get_commandline_target_or_general_config(self,
                                                  config_name,
                                                  default=None):
        if self._commandline_config.get(config_name):
            return self._commandline_config[config_name]
        if self._target_config.get(config_name):
            return self._target_config[config_name]

        value_or_none = self._general_config.get(config_name)
        return value_or_none if value_or_none else default

    def get_path_relative_to_project_root(self, filepath):
        """Gets relative path to the project_root"""
        resolved_filepath = self._get_absolute_path_or_relative_to_project_root(
            path.normpath(filepath))
        LOGGER.info(
            'Getting relative path to the project root for filepath = %s resolved_filepath = %s',
            filepath, resolved_filepath)

        return resolved_filepath

    @property
    def acf_file(self):
        """Gets the property acf_file"""
        return self._get_config_path(_ACF_FILE, path.join('config', 'acf'))

    @property
    def analysis_path(self):
        """Gets the property analysis_path"""
        return path.join(self.prqa_project_path, "helper_logs", "analysis")

    @property
    def analyze_file(self):
        """Gets the property analyze_file"""
        return self._get_commandline_target_or_general_config(ANALYZE_FILE)

    @property
    def analyze_list(self):
        """Gets the property analyze_list"""
        return self._get_commandline_target_or_general_config(ANALYZE_LIST)

    @property
    def analyze_params(self):
        """Gets the property analyze_params"""
        return self._get_commandline_target_or_general_config(ANALYZE_PARAMS)

    @property
    def build_command(self):
        """Gets the property build_command"""
        return self._get_commandline_target_or_general_config(_BUILD_COMMAND)

    @property
    def build_log(self):
        """Gets the property build_log"""
        return self._get_final_path_if_config_exists(_BUILD_LOG)

    @property
    def cli_version_string(self):
        """Gets the property cli_version_string"""
        return self._cli_version_string

    @property
    def compiler_list(self):
        """Gets the property compiler_list"""
        compiler_list = self._get_commandline_target_or_general_config(
            _COMPILER_LIST, default=[])

        return [
            self._get_config_folder_relative_path(path.join('config', 'cct'),
                                                  compiler)
            if _is_filepath_only_basename(compiler) else
            self._get_absolute_path_or_relative_to_project_root(compiler)
            for compiler in compiler_list
        ]

    @property
    def custom_help_path(self):
        """Gets the property custom_help_path"""
        return self._get_final_path_if_config_exists(_CUSTOM_HELP_PATH)

    @property
    def datastore_path(self):
        """Gets the property datastore_path"""
        return self._get_commandline_target_or_general_config(DATASTORE_PATH)

    @property
    def datastore_target(self):
        """Gets the property datastore_target"""
        return self._get_commandline_target_or_general_config(DATASTORE_TARGET)

    @property
    def helper_create_baseline(self):
        """Gets the property helper_create_baseline"""
        return self._get_commandline_target_or_general_config(
            HELPER_CREATE_BASELINE) == 'yes'

    @property
    def helper_logs_path(self):
        """Gets the property helper_logs_path"""
        return path.join(self.prqa_project_path, "helper_logs")

    @property
    def helper_remove_file_list(self):
        """Gets the property helper_remove_file_list"""
        return self._get_commandline_target_or_general_config(
            HELPER_REMOVE_FILE_LIST)

    @property
    def helper_set_baseline(self):
        """Gets the property helper_set_baseline"""
        return self._get_final_path_if_config_exists(HELPER_SET_BASELINE)

    @property
    def helper_suppress_c_header(self):
        """Gets the property helper_suppress_c_header"""
        return self._get_commandline_target_or_general_config(
            HELPER_SUPPRESS_C_HEADER) == 'yes'

    @property
    def helper_suppress_file_list_a(self):
        """Gets the property helper_suppress_file_list_a"""
        filepath_or_none = self._get_final_path_if_config_exists(
            HELPER_SUPPRESS_FILE_LIST_A)

        return filepath_or_none if filepath_or_none else ""

    @property
    def helper_suppress_file_list_s(self):
        """Gets the property helper_suppress_file_list_s"""
        filepath_or_none = self._get_final_path_if_config_exists(
            HELPER_SUPPRESS_FILE_LIST_S)

        return filepath_or_none if filepath_or_none else ""

    @property
    def helper_target(self):
        """Gets the property helper_target"""
        return self._get_commandline_target_or_general_config(HELPER_TARGET)

    @property
    def json_filter(self):
        """Gets the property json_filter"""
        return self._get_commandline_target_or_general_config(JSON_FILTER)

    @property
    def license_servers(self):
        """Gets the property license_servers"""
        default_servers = [
            "5065@rb-lic-rlm-prqa2.de.bosch.com",    # >= QAC 9.7
            "5065@rb-lic-rlm-prqa-gl.de.bosch.com",    # <= QAC 9.6
            "5065@rb-lic-rlm-prqa-cc.de.bosch.com"    # QAC++
        ]
        return self._get_commandline_target_or_general_config(
            _LICENSE_SERVERS, default=default_servers)

    @property
    def local_baseline_path(self):
        """Gets the property local_baseline_path"""
        return self._get_final_path_if_config_exists(_LOCAL_BASELINE_PATH)

    @property
    def qacli(self):
        """Gets the property qacli"""
        return self._get_commandline_target_or_general_config(QACLI)

    @property
    def qagui(self):
        """Gets the property qagui"""
        return self._get_commandline_target_or_general_config(QAGUI)

    @property
    def qa_help_path(self):
        """Gets the property qa_help_path (directory)"""
        return path.dirname(self.prqa_path)

    @property
    def ncf_file(self):
        """Gets the property ncf_file"""
        return self._get_config_path(_NCF_FILE, path.join('config', 'ncf'))

    @property
    def project_git_commit(self):
        def _get_git_hash():
            git_cmd_out, result = git_rev_parse(self)

            return git_cmd_out if result == 0 else "unknown"

        return _get_git_hash()

    @property
    def verbose(self):
        return self._verbose

    @property
    def project_root(self):
        """Gets the property project_root"""
        return self._get_commandline_target_or_general_config(PROJECT_ROOT)

    @property
    def project_buildlog_via_arg(self):
        """Gets the property project_buildlog_via_arg"""
        return self._get_final_path_if_config_exists(PROJECT_BUILDLOG_VIA_ARG)

    @property
    def prqa_analysis_filters(self):
        """Gets the property prqa_analysis_filters"""
        prqa_analysis_filters = self._get_commandline_target_or_general_config(
            PRQA_ANALYSIS_FILTERS, default=[])

        return [
            self._get_absolute_path_or_relative_to_project_root(
                analysis_filter) for analysis_filter in prqa_analysis_filters
        ]

    @property
    def prqa_error_level(self):
        """Gets the property prqa_error_level"""
        return self._get_commandline_target_or_general_config(PRQA_ERROR_LEVEL)

    @property
    def prqa_helper_script_path(self):
        """Gets the property prqa_helper_script_path"""
        return self._get_commandline_target_or_general_config(
            PRQA_HELPER_SCRIPT_PATH)

    @property
    def prqa_modules(self):
        """Gets the property prqa_modules"""
        return self._get_commandline_target_or_general_config(PRQA_MODULES)

    @property
    def prqa_project_path(self):
        """Gets the property prqa_project_path"""
        return self._get_final_path_if_config_exists(PRQA_PROJECT_PATH)

    @property
    def prqa_path(self):
        """Gets the property prqa_path"""
        return self._get_commandline_target_or_general_config(PRQA_PATH)

    @property
    def prqa_log_path(self):
        """Gets the property prqa_log_path"""
        return path.join(self._helix_config_path, 'app', 'logs')

    @property
    def prqa_report_path(self):
        """Gets the property prqa_report_path"""
        return path.join(self.prqa_project_path, "prqa", "configs", "Initial",
                         "reports")

    @property
    def prqa_sync_filters(self):
        """Gets the property prqa_path"""
        return self._get_commandline_target_or_general_config(
            PRQA_SYNC_FILTERS, default=[])

    @property
    def prqa_sync_type(self):
        """Gets the property prqa_sync_type"""
        return self._get_commandline_target_or_general_config(PRQA_SYNC_TYPE)

    @property
    def rcf_file(self):
        """Gets the property rcf_file"""
        return self._get_config_path(_RCF_FILE, path.join('config', 'rcf'))

    @property
    def skip_exit_on_error(self):
        """Gets the property skip_exit_on_error"""
        return self._get_commandline_target_or_general_config(
            SKIP_EXIT_ON_ERROR)

    @property
    def state_filepath(self):
        """Gets the property state_filepath"""
        return path.join(self.prqa_project_path, 'state.json.zip')

    @property
    def use_flist(self):
        """Gets the property use_flist"""
        return self.analyze_file != 'no'

    @property
    def use_python_build_shell(self):
        """Gets the property use_python_build_shell"""
        return self._get_commandline_target_or_general_config(
            USE_PYTHON_BUILD_SHELL)

    @property
    def use_sonarqube(self):
        """Gets the property use_sonarqube"""
        return self._get_commandline_target_or_general_config(
            USE_SONARQUBE) == 'yes'

    @property
    def use_vscode_integration(self):
        """Gets the property use_vscode_integration"""
        return self._get_commandline_target_or_general_config(
            USE_VSCODE_INTEGRATION)

    @property
    def user_messages(self):
        """Gets the property user_messages"""
        return self._get_config_path(
            _USER_MESSAGES, path.join('user_library', 'user_messages'))

    @property
    def vcf_file(self):
        """Gets the property vcf_file"""
        return self._get_config_path(_VCF_FILE, path.join('config', 'vcf'))

    @property
    def via_path(self):
        """Gets the property via_path"""
        return path.join(self.helper_logs_path, 'suppressions')
