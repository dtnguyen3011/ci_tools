#!/usr/bin/env python3
""" Script to update summary table in comment on Bitbucket PR page
"""

import argparse
import logging
import sys

from influxdb import InfluxDBClient

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
    inline_parser = subparsers.add_parser('inline', help=('Update Bitbucket summary report '
                                                          'with inline parameters'))
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

    file_parser = subparsers.add_parser('file', help=('Update Bitbucket summary report using'
                                                      ' summary JSON file'))
    file_parser.add_argument('--summary-json', required=True, action=ValidateStringArg,
                             help='JSON file name of summary')

    for subparser in subparsers.choices.values():
        subparser.add_argument('-u', '--user', required=True, action=ValidateStringArg,
                               help='System user username')
        subparser.add_argument('-p', '--password', required=True, action=ValidateStringArg,
                               help='System user password')
        subparser.add_argument('--commit-id', required=True, action=ValidateStringArg,
                               help='Commit ID')
        subparser.add_argument('--debug', action='store_true', default=False, dest='debug',
                               help='Enable debugging mode')
        subparser.add_argument('-ih', '--influx-host', default='abtv55170.de.bosch.com',
                               help='Influxdb host')
        subparser.add_argument('-ip', '--influx-port', default=8086, help='Influxdb port')

    return parser.parse_args()


def init_args_from_summary_file(file_name: str, file_args: argparse.Namespace) -> \
                                argparse.Namespace:
    summary_data: dict = read_json_file(file_name)
    file_args.__dict__['prid'] = summary_data['pr_id']
    file_args.__dict__['build_number'] = summary_data['build_number']
    file_args.__dict__['build_variant'] = summary_data['variant']
    file_args.__dict__['tool'] = summary_data['tool']
    file_args.__dict__['result'] = summary_data['result']
    return file_args


def __check_already_present(warnings_summary: dict, influx_client: InfluxDBClient) -> bool:
    result = influx_client.query('select tool, build_variant, branch, commit_id from pr_warnings')
    for report_summary in result.get_points(measurement='pr_warnings'):
        if (report_summary['tool'] == warnings_summary['tags']['tool'] and
            report_summary['build_variant'] == warnings_summary['fields']['build_variant'] and
            report_summary['branch'] == warnings_summary['fields']['branch'] and
            report_summary['commit_id'] == warnings_summary['fields']['commit_id']):
            return True
    return False


def push_summary_to_influx(report_args: dict, influx_client: InfluxDBClient) -> None:
    warnings_number = ''.join(filter(lambda char: char.isdigit(), report_args['result']))
    warnings_summary = [{
        'measurement': 'pr_warnings',
        'tags': {
            'tool': report_args['tool']
        },
        'fields': {
            'branch': f'PR-{report_args["prid"]}',
            'build_id': report_args['build_number'],
            'build_variant': report_args['build_variant'],
            'commit_id': report_args['commit_id'][:10],
            'warnings_number': int(warnings_number)
        }
    }]
    if __check_already_present(warnings_summary[0], influx_client):
        LOGGER.warning(('Summary for the same tool with this commit id and build variant '
                        'already present, skipping %s'), warnings_summary)
    else:
        LOGGER.info('Pushing summary: %s', warnings_summary)
        influx_client.write_points(warnings_summary)


if __name__ == '__main__':
    logging.basicConfig(format=('%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] '
                                '%(message)s'), level=logging.INFO)
    LOGGER = logging.getLogger(__name__)
    args = parse_args()

    if args.source == 'file':
        args = init_args_from_summary_file(args.summary_json, args)

    if args.debug:
        LOGGER.setLevel(logging.DEBUG)

    client = InfluxDBClient(host=args.influx_host, port=args.influx_port,
                            database='ccda_radar_gel')
    push_summary_to_influx(vars(args), client)
