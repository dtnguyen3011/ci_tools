#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2020 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: 	state_exporter.py
# Author(s): 	Silva André (CC-AD/ESW4)
# ----------------------------------------------------------------------------
"""Exports state information to csv and html"""

import csv
import json
import sys
from os import path
from zipfile import ZipFile

from logger import LOGGER
from project_state import DEPRECATED_CSV_HEADER_WITH_FILENAME, CSV_HEADER
from html_exporter import create_html_from_list_of_lists, LICENSE_WARNING
from check_qaview import count_number_of_issues, print_number_of_found_issues, print_number_of_open_issues


def _create_html_file_from_list_of_lists(
        config,
        git_commit,
        title_basename,
        html_filepath,
        list_of_lists,
        report_description: str = LICENSE_WARNING):
    title = '{} for {}'.format(title_basename,
                               path.basename(config.project_root))
    with open(html_filepath, 'w+', newline='', encoding='utf-8') as html_file:
        cct_files = ','.join(
            [path.basename(cct) for cct in config.compiler_list])
        rcf_file = path.basename(config.rcf_file)
        html_file.write(
            create_html_from_list_of_lists(title, config.project_root,
                                           git_commit,
                                           config.cli_version_string, rcf_file,
                                           cct_files, list_of_lists,
                                           report_description))
        LOGGER.info('State html summary written to %s', html_filepath)


def _create_csv_writer(csv_file):
    return csv.writer(csv_file,
                      delimiter=',',
                      quotechar='"',
                      quoting=csv.QUOTE_NONNUMERIC)


def convert_qacli_view_to_summary(config, csv_values):
    """Converts a qacli view report to a summary of open and total severities"""
    open_issue_level_dict = count_number_of_issues(csv_values)
    print_number_of_found_issues(open_issue_level_dict)
    print_number_of_open_issues(open_issue_level_dict)
    check_qaview_csv_filepath = path.join(config.prqa_project_path,
                                          'qacli-view-summary.csv')
    with open(check_qaview_csv_filepath, 'w+', newline='',
              encoding='utf-8') as check_qaview_csv_file:
        csv_file_writer = _create_csv_writer(check_qaview_csv_file)
        csv_file_writer.writerows(
            [[key, value] for key, value in open_issue_level_dict.items()])
        LOGGER.info('Writing qacli-view-summary csv file to %s',
                    check_qaview_csv_filepath)

    check_qaview_csv_values = []
    for key, value in open_issue_level_dict.items():
        check_qaview_csv_values.extend([[key, value]])

    check_qaview_html_filepath = path.join(config.prqa_project_path,
                                           'qacli-view-summary.html')
    with open(check_qaview_html_filepath, 'w+', newline='',
              encoding='utf-8') as check_qaview_html_file:
        cct_files = ','.join(
            [path.basename(cct) for cct in config.compiler_list])
        rcf_file = path.basename(config.rcf_file)
        check_qaview_html_file.write(
            create_html_from_list_of_lists("qacli-view-summary",
                                           config.project_root,
                                           config.project_git_commit,
                                           config.cli_version_string,
                                           rcf_file,
                                           cct_files,
                                           check_qaview_csv_values,
                                           report_description=""))
        LOGGER.info('Writing qacli-view-summary html file to %s',
                    check_qaview_html_filepath)


def _convert_state_to_severity_summary(config, git_commit, state_analysis,
                                       summary_details: bool):
    def _get_row_csv_values(files_with_summary, total_sums):
        filepath, file_state = files_with_summary
        row = [
            filepath,
            file_state.get('analysis_error_count'),
            file_state.get('analysis_exit_status'),
            file_state.get('severities_total')
        ]
        # Fills in the analysis_log parts of the file if present
        if file_state.get('analysis_log'):
            analysis_log = file_state.get('analysis_log')
            row.append(','.join([
                '{}:{}'.format(analysis['module'], analysis['analysis_code'])
                for analysis in analysis_log
            ]))
            module_errors = len([
                analysis for analysis in analysis_log
                if analysis['analysis_code'] != '0'
            ])
            row.append(module_errors)
            # Module errors sum
            total_sums[5] += module_errors
        else:
            row.extend(['-', 0])
        row.extend(
            [file_state['severities'][(str(id))] for id in range(0, 10)])
        indices_to_sum = [1, 3]
        indices_to_sum.extend(list(range(6, 16)))
        for i in indices_to_sum:
            total_sums[i] = total_sums[i] + int(row[i])

        return row

    headers = [
        'filename', 'analysis_error_count', 'analysis_exit_status',
        'severities_total', 'module_outputs', 'module_error_count'
    ]
    headers.extend(['severity{}'.format(id) for id in range(0, 10)])
    files_with_summary = [(filepath, file_state['summary'])
                          for filepath, file_state in state_analysis.items()
                          if file_state.get('summary')]

    state_summary_filepath = path.join(config.prqa_project_path,
                                       'report_summary.csv')
    with open(state_summary_filepath, 'w+', newline='',
              encoding='utf-8') as csv_file:
        csv_file_writer = _create_csv_writer(csv_file)
        csv_values = [headers]
        total_sums = ['Total', 0, '-', 0, '-', 0]
        total_sums.extend([0 for i in range(0, 10)])
        csv_values.extend([
            row for row in map(lambda x: _get_row_csv_values(x, total_sums),
                               files_with_summary) if row
        ])
        # Printing details will require a Helix License and therefore
        # should be avoided in some specific use cases
        report_description = ""
        if summary_details:
            csv_values.insert(1, total_sums)
            report_description = LICENSE_WARNING
        else:
            csv_values = [headers, total_sums]
        csv_file_writer.writerows(csv_values)
        LOGGER.info('Report csv summary written to %s', state_summary_filepath)

        _create_html_file_from_list_of_lists(
            config, git_commit, 'Static Code Analysis Summary Report',
            path.join(config.prqa_project_path, 'report_summary.html'),
            csv_values, report_description)


def _convert_state_to_file_metrics(config, git_commit, state_analysis):
    def _get_row_csv_values(file_with_submetrics):
        filepath, submetrics = file_with_submetrics

        def _convert_submetric_to_rows(entity_type, entity_name, entity_line,
                                       metrics):
            if not metrics or not entity_type:
                return None

            rows = []
            rows.extend([[
                filepath, entity_name, entity_line, entity_type, metric_name,
                metric_value
            ] for metric_name, metric_value in metrics.items()])

            return rows

        rows = []
        subrows = map(
            lambda x: _convert_submetric_to_rows(x.get('type'), x.get(
                'name'), x.get('line'), x.get('metrics')), submetrics)
        for subrow in subrows:
            if subrow:
                rows.extend(subrow)

        return rows

    headers = [
        'path', 'entity_name', 'entity_line', 'entity_type', 'metric_name',
        'metric_value'
    ]
    files_with_submetrics = [
        (filepath, file_state['submetrics'])
        for filepath, file_state in state_analysis.items()
        if file_state.get('submetrics')
    ]

    state_metrics_filepath = path.join(config.prqa_project_path,
                                       'report_metrics.csv')
    with open(state_metrics_filepath, 'w+', newline='',
              encoding='utf-8') as csv_file:
        csv_values = [headers]
        for row in map(_get_row_csv_values, files_with_submetrics):
            if row:
                csv_values.extend(row)
        csv_file_writer = _create_csv_writer(csv_file)
        csv_file_writer.writerows(csv_values)
        LOGGER.info('Report csv metrics written to %s', state_metrics_filepath)

        _create_html_file_from_list_of_lists(
            config, git_commit, 'Code Metrics Report',
            path.join(config.prqa_project_path, 'report_metrics.html'),
            csv_values)

def filter_csv_values_for_serverity_8_and_9(csv_values):
    def _get_row_open_severity_8and9_csv_values(row):
        suppression_type_bitmask_value = row[6]
        severity_value = row[5]
        if suppression_type_bitmask_value == '0' and (severity_value == '8' or severity_value == '9'):
            return row
        return None

    only_8_and_9_csv_values = [DEPRECATED_CSV_HEADER_WITH_FILENAME]
    only_8_and_9_csv_values.extend([
        row for row in map(_get_row_open_severity_8and9_csv_values, csv_values[1:]) if row
    ])

    return only_8_and_9_csv_values

def _convert_state_to_file_analysis(config, git_commit, state_analysis):
    def _get_row_csv_values(file_with_findings):
        filepath, findings = file_with_findings

        def _convert_finding_to_rows(finding):
            if not finding:
                return None

            row = [filepath]
            row.extend([finding.get(col_name) for col_name in CSV_HEADER])
            return row

        return [
            finding for finding in map(_convert_finding_to_rows, findings)
            if finding
        ]

    files_with_findings = [(filepath, file_state['findings'])
                           for filepath, file_state in state_analysis.items()
                           if file_state.get('findings')]

    csv_values = [DEPRECATED_CSV_HEADER_WITH_FILENAME]
    for row in map(_get_row_csv_values, files_with_findings):
        csv_values.extend(row)

    create_csv_analysis(config, git_commit, csv_values)
    convert_qacli_view_to_summary(config, csv_values)

    only_8_and_9_csv_values = filter_csv_values_for_serverity_8_and_9(csv_values)
    create_html_analysis(config, git_commit, only_8_and_9_csv_values)
    

def create_csv_analysis(config, git_commit, csv_values):
    """Creates CSV for qacli-view"""
    state_analysis_filepath = path.join(config.prqa_project_path,
                                        'qacli-view.csv')
    with open(state_analysis_filepath, 'w+', newline='',
              encoding='utf-8') as csv_file:
        # This is a workaround to mimic qacli-view.csv deprecated behavior
        # it should be deprecated in the future and therefore removed from CSV
        csv_file.write('\n'.join([git_commit, LICENSE_WARNING, '']))
        csv_file_writer = _create_csv_writer(csv_file)
        csv_file_writer.writerows(csv_values)
        LOGGER.info('Report csv analysis written to %s',
                    state_analysis_filepath)

def create_html_analysis(config, git_commit, csv_values):
    """Creates HTML for qacli-view"""
    _create_html_file_from_list_of_lists(
        config, git_commit, '- Open Severity 8 and 9 issues from qacli-view',
        path.join(config.prqa_project_path, 'open-8-and-9-qacli-view.html'),
        csv_values)

def create_exports(config, metrics: bool, summary_details: bool = True):
    """Export State information to CSV and HTML"""
    LOGGER.info('Reading state file with path %s', config.state_filepath)
    with ZipFile(config.state_filepath, mode='r') as state_zip_file:
        with state_zip_file.open('state.json') as state_file:
            state = json.loads(state_file.read())
            state_analysis = state.get('analysis')

            if not state_analysis:
                LOGGER.error('No analysis in state file found. Exiting')
                sys.exit(1)

            git_commit = state.get('git_commit')
            _convert_state_to_severity_summary(config, git_commit,
                                               state_analysis, summary_details)
            # TODO(slv2abt): Summarize metrics into a nicer base format.
            if metrics:
                _convert_state_to_file_metrics(config, git_commit,
                                               state_analysis)
            _convert_state_to_file_analysis(config, git_commit, state_analysis)
