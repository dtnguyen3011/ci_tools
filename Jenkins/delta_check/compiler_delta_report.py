#!/usr/bin/env python3
""" Script to convert output of compiler delta check to report configuration
"""

import sys
import argparse
import logging
import json
import util
import csv
from bitbucket import BitbucketAPI


class ValidateArg(argparse.Action):
    """Class to validate if string argument is an empty string
    """

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        if values == '':
            LOGGER.error('Argument %s cannot be empty string', self.dest)
            sys.exit(1)
        setattr(namespace, self.dest, values)


def parse_args() -> argparse.Namespace:
    """Adds and parses command line arguments

    Returns:
      argparse.Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True, action=ValidateArg, help='System user username')
    parser.add_argument('-p', '--password', required=True, action=ValidateArg, help='System user password')
    parser.add_argument('--data-file', required=True, action=ValidateArg, help='Warnings delta JSON file')
    parser.add_argument('--summary-file', required=True, action=ValidateArg, help='Summary JSON file')
    parser.add_argument('--output-file', required=True, action=ValidateArg, help='Output JSON file name')
    parser.add_argument('--artifactory-url', required=False, action=ValidateArg, help='Artifactory URL',
                        default='https://rb-artifactory.bosch.com/artifactory')
    parser.add_argument('--artifactory-repo', required=True, action=ValidateArg, help='Artifactory repo')
    parser.add_argument('--artifactory-job-path', required=True, action=ValidateArg,
                        help='Artifactory path to job artifacts')
    parser.add_argument('--artifactory-report-path', required=True, action=ValidateArg,
                        help='Artifactory path to report app')
    parser.add_argument('--bitbucket-url', required=False, action=ValidateArg, help='Bitbucket URL',
                        default='https://sourcecode01.de.bosch.com')
    parser.add_argument('--bitbucket-repo', required=True, action=ValidateArg, help='Bitbucket repo name')
    parser.add_argument('--bitbucket-project', required=True, action=ValidateArg, help='Bitbucket project name')
    parser.add_argument('-sc', '--source-commit', required=False, action=ValidateArg, default='Not found',
                        help='Source commit for compiler warning check')
    parser.add_argument('-tc', '--target-commit', required=False, action=ValidateArg, default='Not found',
                        help='Target commit for compiler warning check')
    parser.add_argument('--debug', action='store_true', default=False, dest='debug', help='Enable debugging mode')
    parser.add_argument('--to-csv', required=False, action=ValidateArg, help='Output CSV file name')

    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    bitbucket_api: BitbucketAPI = BitbucketAPI(args.bitbucket_url, args.user, args.password,
                                 args.bitbucket_project, args.bitbucket_repo, verify_ssl=False)
    try:
        summary_data = util.read_json_file(args.summary_file)
        warnings_data = util.read_json_file(args.data_file)

        pr_title: str = bitbucket_api.get_pr(summary_data['pr_id']).title

        header = {
            "title": f"PR-{summary_data['pr_id']} #{summary_data['build_number']}",
            "header": f"PR-{summary_data['pr_id']} ({pr_title})",
            "subtitle": f"Compiler/linker warnings check for {summary_data['variant']} build №{summary_data['build_number']}",
            "additionalText": f"Merge of source commit {args.source_commit} and target commit {args.target_commit}<br/>",
        }

        columns = [
        {
          "id": 1,
          "title": "Qty",
          "field": "quantity",
          "cellType": "text",
          "sorting": True,
          "filtering": False,
          "width": "6%",
          "grouping": False
        },
        {
          "id": 2,
          "title": "Domain",
          "field": "domain",
          "cellType": "chips",
          "width": "10%"
        },
        {
          "id": 3,
          "title": "Filename",
          "field": "file_path",
          "cellType": "text"
        },
        {
          "id": 4,
          "title": "Row",
          "field": "row",
          "cellType": "text",
          "filtering": False,
          "width": "6%"
        },
        {
          "id": 5,
          "title": "Col",
          "field": "column",
          "cellType": "text",
          "filtering": False,
          "width": "6%"
        },
        {
          "id": 6,
          "title": "Type",
          "field": "type_name",
          "cellType": "text",
          "filtering": False
        },
        {
          "id": 7,
          "title": "Message",
          "field": "message",
          "cellType": "text",
          "grouping": False
        },
        {
          "id": 8,
          "title": "Team",
          "field": "teams",
          "cellType": "chips"
        }
      ]

        report_data = {
            "header": header,
            "columns": columns,
            "data": warnings_data
        }

        with open(args.output_file, 'w') as outfile:
            outfile.write(json.dumps(report_data))

        # Update summary with correct link to the report app
        summary_data['details'] = f'[Report]({args.artifactory_url}/{args.artifactory_repo}/{args.artifactory_report_path}' \
                                  f'?dataUrl={args.artifactory_url}/{args.artifactory_repo}/{args.artifactory_job_path}/' \
                                  f'{args.output_file})'

        if args.to_csv:
          csv_lines = []
          csv_line = []
          # Add csv header
          for item in columns:
            csv_line.append(item["title"])
          csv_lines.append(csv_line)
          # Add csv data
          for item in warnings_data:
            csv_line = []
            for column in columns:
              csv_line.append(item[column["field"]])
            csv_lines.append(csv_line)
          # Write csv file
          try:
            with open(args.to_csv, 'w', newline='') as file:
              writer = csv.writer(file)
              writer.writerows(csv_lines)
          except IOError as error:
            raise Exception('Could not write warnings file: %s', error.filename)

        with open(args.summary_file, 'w') as outfile:
            outfile.write(json.dumps(summary_data))

    except Exception as exc:
        LOGGER.error('Could not read input file (%s), report will not be generated.', exc)
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s', level=logging.INFO)
    LOGGER = logging.getLogger(__name__)
    args = parse_args()
    main(args)
