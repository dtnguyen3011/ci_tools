#!/usr/bin/env python3
""" Script to update Bitbucket Code Insights with results of compiler warnings analysis
"""

from __future__ import annotations

import argparse
import logging
import sys
from os.path import exists, splitdrive

from requests import Response

from bitbucket import BitbucketAPI
from util import read_json_file


class ValidateIntArg(argparse.Action):
    """Class to validate if string argument is an integer
    """

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            values = int(values)
        except ValueError:
            LOGGER.error('Argument --%s must be integer', self.dest)
            sys.exit(1)
        setattr(namespace, self.dest, int(values))


class ValidateStringArg(argparse.Action):
    """Class to validate if string argument is an non-empty string
    """

    def __call__(self, parser, namespace, values, option_string=None):
        if values == '':
            LOGGER.error('Argument --%s cannot be empty string', self.dest)
            sys.exit(1)
        setattr(namespace, self.dest, values)


def parse_args() -> argparse.Namespace:
    """Adds and parses command line arguments

    Returns:
      Command line arguments
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='source', title='Source')
    subparsers.required = True
    inline_parser = subparsers.add_parser(
        'inline', help='Update Bitbucket Code Insights with inline parameters'
    )
    inline_parser.add_argument('--prid', required=True, action=ValidateIntArg,
                               help='Pull request ID')

    inline_parser.add_argument('--build-number', required=True, action=ValidateIntArg,
                               help='Build number')

    inline_parser.add_argument('--build-variant', required=True, action=ValidateStringArg,
                               help='Build variant')
    inline_parser.add_argument('--tool', required=True, action=ValidateStringArg,
                               help='Reporting tool name')
    inline_parser.add_argument('--result', required=True, action=ValidateStringArg,
                               help='Result of tool execution')
    inline_parser.add_argument('--details', required=False, action=ValidateStringArg,
                               help='Detail field of summary table. '
                                    'Usually link to full report',
                               default=[], nargs='+')
    inline_parser.add_argument('-c', '--components', required=False, action=ValidateStringArg,
                               help='List of components',
                               default=[], nargs='+')
    file_parser = subparsers.add_parser(
        'file', help='Update Bitbucket summary report using summary JSON file'
    )
    file_parser.add_argument('--summary-json', required=True, action=ValidateStringArg,
                             help='JSON file name of summary')
    file_parser.add_argument('--report-json', required=False, action=ValidateStringArg,
                             help='JSON file name of report, necessary for annotations')


    for subparser in subparsers.choices.values():
        subparser.add_argument('-u', '--user', required=True, action=ValidateStringArg,
                               help='System user username')
        subparser.add_argument('-p', '--password', required=True, action=ValidateStringArg,
                               help='System user password')
        subparser.add_argument('-bu', '--bitbucket-url', required=False, action=ValidateStringArg,
                               help='Bitbucket URL', default='https://sourcecode01.de.bosch.com')
        subparser.add_argument('-br', '--bitbucket-repo', required=True, action=ValidateStringArg,
                               help='Bitbucket repo name')
        subparser.add_argument('-bp', '--bitbucket-project', required=True,
                               action=ValidateStringArg, help='Bitbucket project name')
        subparser.add_argument('-ci', '--commit-id', required=True, action=ValidateStringArg,
                               help='Bitbucket commit id')
        subparser.add_argument('--debug', action='store_true', default=False, dest='debug',
                               help='Enable debugging mode')

    return parser.parse_args()


def init_args_from_summary_file(file_name: str, input_args: argparse.Namespace) -> \
        argparse.Namespace:
    """Adds and parses arguments provided in a summary json file

    Returns:
      Summary file arguments
    """
    summary_data: dict = read_json_file(file_name)
    input_args.__dict__['prid'] = summary_data['pr_id']
    input_args.__dict__['build_number'] = summary_data['build_number']
    input_args.__dict__['build_variant'] = summary_data['variant']
    input_args.__dict__['tool'] = summary_data['tool']
    input_args.__dict__['result'] = summary_data['result']
    input_args.__dict__['details'] = summary_data['details']
    input_args.__dict__['components'] = summary_data['components']
    return input_args


class UpdateBitbucketCodeInsights:
    """
    A Class for adding code insights to provided bitbucket commit with details from provided
    reports
    ...

    Attributes
    ----------
    bitbucket_api: BitbucketAPI
        API object of bitbucket
    commitid: str
        ID of the commit, for which Code Insights will be added
    details: str
        String with detains about Code Insights report
    components: list
        Component were warnings were found, if any
    report_url : str
        URL of the Code Insights report, generate automaticaly in add_report() method

    Methods
    -------
    add_report(report_params: dict):
        Adds or updates Code Insight report with specified parameters.
    add_annotation(report_findings: dict):
        Adds or updates annotation of warning for the Code Insight report.
    """

    def __init__(self, bitbucket_api: BitbucketAPI, commitid: str,
                 details: str, components: list) -> None:
        self.bitbucket_api = bitbucket_api
        self.commitid = commitid
        self.details = details or '-'
        self.components = ' '.join(map(lambda component: f'`{component}`', components)) or '-'
        self.report_url = None

    def add_report(self, report_params: dict) -> None:
        """
        Adds or updates Code Insight report with specified parameters.

        Parameters:
            report_params (dict): Dictionary with parameters about report, such as build_variant,
                                  result, build_number and so on.
        """
        report_key: str = f'{self.commitid[:4]}_{report_params["build_variant"]}'
        self.report_url: str = (
            f'https://sourcecode01.de.bosch.com/rest/insights/1.0/projects/'
            f'{report_params["bitbucket_project"]}/repos/{report_params["bitbucket_repo"]}'
            f'/commits/{self.commitid}/reports/{report_key}'
        )
        result: str = 'PASS' if report_params["result"] == '0 :white_check_mark:' else 'FAIL'
        link: str = self.details.replace('[Report](', '').replace(')', '') if '[Report]' in \
                    self.details else None

        report: dict = {
            'title': f'{report_params["build_variant"]} #{report_params["build_number"]}',
            'details': (f'{report_params["tool"]} check for {report_params["build_variant"]} build'
                        f' #{report_params["build_number"]}'),
            'result': result,
        }

        if self.components:
            report['data'] = [{
                'title': 'Components',
                'type': 'TEXT',
                'value': self.components
            }]
        if link:
            report['link'] = link
        LOGGER.info('Publishing report %s to %s', report, self.report_url)
        result: Response = self.bitbucket_api.put(self.report_url, report)
        LOGGER.debug('Response %i %s %s', result.status_code, result.reason, result.text)

    def add_annotation(self, report_findings: dict, tool_name: str, build_variant: str) -> None:
        """
        Adds or updates annotation of warning for the Code Insight report.

        Parameters:
            report_findings (dict): Dictionary with details about warning, such as severity,
                                    message, message and line of the code.
            tool_name (str): Name of the tool which provided warnings report
            build_variant (str): Name of the build variant

        """
        annotations: list = []
        annotations_url: str = f'{self.report_url}/annotations'
        for report_item in report_findings:
            severity = report_item['severity'] if report_item['severity'] in \
                       ['LOW', 'MEDIUM', 'HIGH'] else 'HIGH'
            path_in_repo: str = splitdrive(report_item['file_path'])[1].replace('\\', '/') \
                                                                       .lstrip('/')

            annotation = {
                'line': report_item['row'],
                'message': f'{tool_name} {build_variant}: {report_item["message"]}',
                'path': path_in_repo,
                'severity': severity
            }

            annotations.append(annotation)

        if annotations:
            LOGGER.info('Cleaning previous annotations, if there are any')
            result = self.bitbucket_api.delete(annotations_url)
            LOGGER.debug('Response %i %s %s', result.status_code, result.reason, result.text)
            LOGGER.info('Adding annotations %s to report %s', annotations, self.report_url)
            result = self.bitbucket_api.post(annotations_url, {'annotations': annotations})
            LOGGER.debug('Response %i %s %s', result.status_code, result.reason, result.text)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s',
        level=logging.INFO
    )
    LOGGER = logging.getLogger(__name__)
    args = parse_args()

    if args.source == 'file':
        args = init_args_from_summary_file(args.summary_json, args)

    if args.debug:
        LOGGER.setLevel(logging.DEBUG)

    bitbucket_api_instance = BitbucketAPI(args.bitbucket_url, args.user, args.password,
                                          args.bitbucket_project, args.bitbucket_repo,
                                          verify_ssl=False)
    report_updater = UpdateBitbucketCodeInsights(bitbucket_api_instance, args.commit_id,
                                                 args.details, args.components)
    report_updater.add_report(vars(args))
    if args.report_json:
        if exists(args.report_json):
            report_data: dict = read_json_file(args.report_json).get('data', [])
            report_updater.add_annotation(report_data, args.tool, args.build_variant)
        else:
            LOGGER.warning('Provided report file %s is not found, annotations will not be added',
                           args.report_json)
