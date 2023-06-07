#-----------------------------------------------------------------------------
#  Copyright (c) 2020 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: project_state.py
# Author(s): Andre Silva CC-AD/ESW4 (Maintainer)
# ----------------------------------------------------------------------------
"""Defines a Project class that extracts project related information from the HIS report"""

import csv
import json
import re
import sys
import xml.dom.minidom
from os import path, listdir
from datetime import datetime

from helix_commands import git_rev_parse, export_formatted_project_analysis
from logger import LOGGER
from html_exporter import LICENSE_WARNING

REGEX_FOR_ANALYSIS_LOG_STRING = (
    r'(?P<path>([A-Z]:(\\[^\\:]+)*)|(\/([^:]+)*)):'    # Matches OS agnostic filepath
    r'(?P<module>\w+):'    # Matches the component name
    r'(?P<return_code>\d+):'    # Return code
    r'(?P<files_to_parse>\d+):'    # Files to parse
    r'(?P<files_parsed>\d+)\s+?'    # Files already parsed
    r'(?P<timestamp>\([^\)]+\))?')    # Timestamp

# Project Metrics
# STCYA: Cyclomatic complexity Across project
# STFEC: File entity change versus parent snapshot
# STNEA: Number of Entry points Across project
# STNFA: Number of Functions Across project
# STNRA: Number of Recursions Across project
# STPPC: Project line percentage change versus parent snapshot
_PROJECT_METRICS = ['STCYA', 'STFEC', 'STNEA', 'STNFA', 'STNRA', 'STPPC']
# File Metrics
# STPLC: Total physical lines of code
# STFNC: Number of functions in file
_FILE_METRICS = ['STVAR', 'STPLC', 'STFNC']
# Class Metrics
# STCBO: Coupling to other classes
# STDIT: Deepest inheritance
# STLCM: Lack of cohesion within class
# STMTH: Number of methods declared in class
# STWMC: Weighted methods in class
_CLASS_METRICS = ['STMTH', 'STWMC', 'STCBO', 'STLCM', 'STDIT']
# Function Metrics
# STAV1: Average size of statement in function
# STAV2: Average size of statement in function
# STAV3: Average size of statement in function
# STST1: Number of statements in function
# STST2: Number of statements in function
# STST3: Number of statements in function
# STCAL: Number of functions called from function.
# STCYC: Cyclomatic complexity
# STM07: Essential Cyclomatic Complexity
# STLCT: Number of local variables declared
# STLIN: Number of code lines
# STLOP: Number of logical operators
# STM29: Number of functions calling this function
# STSUB: Number of function calls
# STUNR: Number of unreachable statements
# STUNV: Unused or non-reused variables
# STXLN: Number of executable lines
# STMIF: Deepest level of nesting
# STPAR: Number of parameters
# STRET: Number of return points in function
# STGTO: Number of GOTO's
# STPTH: Estimated static program paths
_FUNCTION_METRICS = [
    'STAV1', 'STAV2', 'STAV3', 'STCAL', 'STCYC', 'STM07', 'STLCT', 'STLIN',
    'STLOP', 'STM29', 'STSUB', 'STUNR', 'STUNV', 'STXLN', 'STMIF', 'STPAR',
    'STRET', 'STGTO', 'STST1', 'STST2', 'STST3', 'STPTH'
]
_METRICS_OF_INTEREST = {
    *_PROJECT_METRICS, *_FILE_METRICS, *_CLASS_METRICS, *_FUNCTION_METRICS
}

CSV_HEADER = [
    'line', 'column_number', 'component_and_message', 'description',
    'severity', 'suppression_bitmask', 'suppression_justification',
    'rule_group', 'rule_text'
]

CSV_HEADER_WITH_FILENAME = ['filename', *CSV_HEADER]

DEPRECATED_CSV_HEADER_WITH_FILENAME = [
    'Filename', 'Line number', 'Column number',
    'Producer component:Message number', 'Message text', 'Severity',
    'Suppression type bitmask', 'Suppression justification', 'Rule Group',
    'Rule text'
]


def _create_csv_writer(csv_file):
    return csv.writer(csv_file,
                      delimiter=',',
                      quotechar='"',
                      quoting=csv.QUOTE_NONNUMERIC)


def _get_file_analysis_from_row(row):
    # analysis_depth and filename are skipped as they are not parsed directly
    # row[0] is the analysis_depth
    if row and row[0] == '0':
        filename = row[1]
        finding = dict(zip(CSV_HEADER, row[2:]))

        LOGGER.debug('===\nfilename=%s\nheaders=%s\nrow=%s\nfinding=%s\n===',
                     filename, CSV_HEADER, row, finding)
        return (filename, finding)

    return None


def _get_metrics(entity_name, entity_type, entity_line, json_entity):
    metrics = json_entity.get('metrics')
    if not metrics:
        return None

    entity_metrics = {
        name: value
        for name, value in metrics.items() if name in _METRICS_OF_INTEREST
    }

    return {
        'name': entity_name,
        'type': entity_type,
        'line': entity_line,
        'metrics': entity_metrics
    }


def _create_file_metrics(filepath, json_data):
    file_metrics = {'type': 'file'}
    metrics = _get_metrics(filepath, 'file', '', json_data)
    if metrics:
        file_metrics['metrics'] = metrics
    submetrics = []
    for entity in json_data.get('entities', []):
        submetric = _get_metrics(entity.get('name'), entity.get('type'),
                                 entity.get('line'), entity)
        if submetric:
            submetrics.append(submetric)
    if submetrics:
        file_metrics['submetrics'] = submetrics

    return file_metrics


def _log_error_if_file_not_in_analysis(analysis, normalized_filepath):
    if not analysis.get(normalized_filepath):
        LOGGER.debug(
            'Information missing for file = %s while adding violations',
            normalized_filepath)


class ProjectState:
    def __init__(self, config):
        self._config = config

    def _generate_consolidated_json(self, file_root):
        project_data = {}

        if not file_root:
            return project_data

        for file_entity in file_root.getElementsByTagName('File'):
            filepath = path.normpath(file_entity.getAttribute('path'))
            json_attribute = file_entity.getElementsByTagName('Json')
            if not json_attribute:
                LOGGER.error("Error parsing file = %s. Ignoring it.", filepath)
                continue
            json_file = path.normpath(
                json_attribute.item(0).firstChild.nodeValue)
            json_data = None
            with open(json_file, 'r') as blibs_file:
                json_data = json.loads(blibs_file.read())

            if not json_data:
                LOGGER.error("Error parsing json_file = %s. Ignoring it.",
                             json_file)
                continue

            normalized_path = self._normalize_path(filepath)
            if not normalized_path:
                LOGGER.error('Invalid path = %s', filepath)
                continue

            project_data[normalized_path] = _create_file_metrics(
                filepath, json_data)

        return project_data

    def _normalize_path(self, filepath):
        # Workaround for problematic paths
        if len(filepath) < 3 or filepath == "C:\\Program":
            return None

        last_three_chars = filepath[-3:]
        if last_three_chars == 'cma':
            return 'cma'
        relpath = filepath
        try:
            relpath = path.relpath(filepath, self._config.project_root)
        except ValueError as error:
            LOGGER.error('Normalizing file %s with root %s failed due to %s',
                         filepath, self._config.project_root, error)

        return relpath

    def _parse_analyse_logs(self):
        def _get_analyse_information_from_regex(analysis, re_match):
            normalized_filepath = self._normalize_path(
                path.normpath(re_match.group('path')))
            if not normalized_filepath:
                return

            analysis.setdefault(normalized_filepath, []).append({
                'analysis_code':
                re_match.group('return_code'),
                'module':
                re_match.group('module'),
                'timestamp':
                re_match.group('timestamp')
            })

        file_list = [
            path.join(self._config.analysis_path, log_file)
            for log_file in listdir(self._config.analysis_path)
            if log_file.endswith('.log')
        ]
        file_list.sort()

        if not file_list:
            return {}

        log_filepath = file_list[-1]
        LOGGER.info('Opening log %s to extract analysis output information',
                    log_filepath)
        with open(log_filepath, 'r') as analysis_log:
            analysis_outputs = {}
            for match in re.finditer(REGEX_FOR_ANALYSIS_LOG_STRING,
                                     analysis_log.read(), re.MULTILINE):
                _get_analyse_information_from_regex(analysis_outputs, match)

            return analysis_outputs

    def _add_summary_per_file_to_dict(self, analysis):
        def _parse_file_summary(file_entity):
            severities = {
                severity_entity.getAttribute('id'):
                severity_entity.firstChild.nodeValue
                for severity_entity in file_entity.getElementsByTagName(
                    'Severity')
            }
            severities_total = file_entity.getElementsByTagName(
                'SeverityTotal').item(0).firstChild.nodeValue
            analysis_error_count = file_entity.getElementsByTagName(
                'AnalysisErrorCount').item(0).firstChild.nodeValue
            analysis_exit_status = file_entity.getElementsByTagName(
                'AnalysisExitStatus').item(0).firstChild.nodeValue
            filepath = file_entity.getElementsByTagName('Name').item(
                0).firstChild.nodeValue

            return (filepath, {
                'severities': severities,
                'severities_total': severities_total,
                'analysis_error_count': analysis_error_count,
                'analysis_exit_status': analysis_exit_status
            })

        xml_filepath = path.normpath(
            path.join(self._config.prqa_report_path, 'severity_summary.xml'))
        if not path.exists(xml_filepath):
            LOGGER.info('File %s does not exists')
            return

        LOGGER.info("Parsing Summary XML file = %s", xml_filepath)
        summary_dom = xml.dom.minidom.parse(xml_filepath)
        # Gets the file root for processing
        file_summaries = [
            _parse_file_summary(file_entity)
            for file_entity in summary_dom.getElementsByTagName('File')
        ]
        for filepath, file_summary in file_summaries:
            # Sets the file name as it might not have been included by the processing
            # of results_data.xml. In real-life situations it is often not reliable
            normalized_filepath = self._normalize_path(filepath)
            _log_error_if_file_not_in_analysis(analysis, normalized_filepath)
            analysis.setdefault(normalized_filepath, {})
            analysis[normalized_filepath]['summary'] = file_summary

        # Adds analysis log section if present
        for filepath, analysis_output in self._parse_analyse_logs().items():
            if analysis.get(filepath):
                analysis[filepath]['summary'].setdefault(
                    'analysis_log', analysis_output)

    def _add_violations_per_file_to_dict(self, analysis):
        csv_from_output = self._get_csv_analysis()

        # Fills data rows
        violations_per_file_to_dict = {}
        for filepath, finding in [
                csv_parse_result for csv_parse_result in map(
                    _get_file_analysis_from_row, csv_from_output)
                if csv_parse_result
        ]:
            normalized_filepath = self._normalize_path(filepath)
            _log_error_if_file_not_in_analysis(analysis, normalized_filepath)
            analysis.setdefault(normalized_filepath, {})
            analysis[normalized_filepath].setdefault('findings',
                                                     []).append(finding)

        return violations_per_file_to_dict

    def _get_csv_analysis(self):
        analysis_output, returncode = export_formatted_project_analysis(
            self._config)
        # code 2 means: command processing failure
        success_codes = [0, 2]
        if returncode in success_codes:
            LOGGER.info("Export returned code %s", returncode)
        else:
            LOGGER.error("View export returned code: %s", str(returncode))
            sys.exit(returncode)

        # Reads input from the analysis output
        return csv.reader(analysis_output.split('\n'),
                          delimiter=',',
                          quotechar='"')

    def get_analysis_csv_values(self):
        def _get_row_csv_values(row):
            # analysis_depth and filename are skipped as they are not parsed directly
            # row[0] is the analysis_depth
            if row and row[0] == '0':
                filename = row[1]
                result_row = [self._normalize_path(filename)]
                result_row.extend(row[2:])

                return result_row

            return None

        csv_from_output = self._get_csv_analysis()

        csv_values = [DEPRECATED_CSV_HEADER_WITH_FILENAME]
        csv_values.extend([
            row for row in map(_get_row_csv_values, csv_from_output) if row
            ])

        return csv_values

    def _parse_file_root(self):
        xml_filepath = path.normpath(
            path.join(self._config.prqa_report_path, 'results_data.xml'))

        if not path.exists(xml_filepath):
            LOGGER.warn('File %s not be found. Report HMR failed?',
                        xml_filepath)
            return None

        LOGGER.info("Parsing XML file = %s", xml_filepath)
        xml_dom = xml.dom.minidom.parse(xml_filepath)
        # Gets the file root for processing
        file_root = [
            dataroot for dataroot in xml_dom.getElementsByTagName('dataroot')
            if dataroot.getAttribute('type') == 'per-file'
        ][0]

        return file_root

    def create(self):
        LOGGER.info('git hash = %s', self._config.project_git_commit)
        file_root = self._parse_file_root()
        state = {
            'git_commit':
            self._config.project_git_commit,
            'project_root':
            self._config.project_root,
            'prqa_project_relative_path':
            self._normalize_path(self._config.prqa_project_path),
            'cli_version':
            self._config.cli_version_string,
            'timestamp':
            datetime.now().strftime('%Y_%m_%d_%H_%M_%S'),
            'cct':
            ','.join(
                [path.basename(cct) for cct in self._config.compiler_list]),
            'ncf':
            path.basename(self._config.ncf_file),
            'rcf':
            path.basename(self._config.rcf_file),
            'vcf':
            path.basename(self._config.vcf_file),
            'user_messages':
            path.basename(self._config.user_messages),
            'analysis':
            self._generate_consolidated_json(file_root)
        }
        # Appends additional information from results_data.xml and jsons
        self._add_violations_per_file_to_dict(state['analysis'])
        # Appends additional information from severity_summary.xml
        self._add_summary_per_file_to_dict(state['analysis'])

        return state
