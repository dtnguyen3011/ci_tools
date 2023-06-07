#!/usr/bin/env python3
""" Script to update summary table in comment on Bitbucket PR page
"""

import sys
import re
import logging
import argparse
import time
import typing
from util import read_json_file
from bitbucket import BitbucketAPI, Comment

logging.basicConfig(format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s', level=logging.INFO)
LOGGER = logging.getLogger(__name__)
# Actual limitation is 32768, use 32700 to ensure additional letter don't change the length
BITBUCKET_MAX_LENGTH = 32700


class ValidateIntArg(argparse.Action):
    """Class to validate if string argument is an integer
    """

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            values = int(values)
        except:
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
    inline_parser = subparsers.add_parser('inline', help='Update Bitbucket summary report with inline parameters')
    inline_parser.add_argument('--prid', required=True, action=ValidateIntArg, help='Pull request ID')
    inline_parser.add_argument('--build-number', required=True, action=ValidateIntArg, help='Build number')

    inline_parser.add_argument('--build-variant', required=True, action=ValidateStringArg, help='Build variant')
    inline_parser.add_argument('--tool', required=True, action=ValidateStringArg, help='Reporting tool name')
    inline_parser.add_argument('--result', required=True, action=ValidateStringArg, help='Result of tool execution')
    inline_parser.add_argument('--details', required=False, action=ValidateStringArg,
                               help='Detail field of summary table. Usually link to '
                                    'full report', default=None)
    inline_parser.add_argument('-c', '--components', required=False, action=ValidateStringArg,
                               help='List of components',
                               default=[], nargs='+')
    inline_parser.add_argument('--comment', required=False, action=ValidateStringArg,
                               help='Additional commets to display',
                               default=None)
    file_parser = subparsers.add_parser('file', help='Update Bitbucket summary report using summary JSON file')
    file_parser.add_argument('--summary-json', required=True, action=ValidateStringArg, help='JSON file name of summary')

    for subparser in subparsers.choices.values():
        subparser.add_argument('-u', '--user', required=True, action=ValidateStringArg, help='System user username')
        subparser.add_argument('-p', '--password', required=True, action=ValidateStringArg, help='System user password')
        subparser.add_argument('-bu', '--bitbucket-url', required=False, action=ValidateStringArg, help='Bitbucket URL',
                               default='https://sourcecode01.de.bosch.com')
        subparser.add_argument('-br', '--bitbucket-repo', required=True, action=ValidateStringArg,
                               help='Bitbucket repo name')
        subparser.add_argument('-bp', '--bitbucket-project', required=True, action=ValidateStringArg,
                               help='Bitbucket project name')
        subparser.add_argument('--debug', action='store_true', default=False, dest='debug',
                               help='Enable debugging mode')
        subparser.add_argument('-ch', '--commit-hash', required=True, action=ValidateStringArg,
                               help='Commit hash is used to report')
        subparser.add_argument('--build-url', required=True, action=ValidateStringArg, help='Build url')

    return parser.parse_args()


def init_args_from_summary_file(file_name: str, args: argparse.Namespace) -> argparse.Namespace:
    summary_data: dict = read_json_file(file_name)
    args.__dict__['prid'] = summary_data['pr_id']
    args.__dict__['build_number'] = summary_data['build_number']
    args.__dict__['build_variant'] = summary_data['variant']
    args.__dict__['tool'] = summary_data['tool']
    args.__dict__['result'] = summary_data['result']
    args.__dict__['details'] = summary_data['details']
    args.__dict__['components'] = summary_data['components']
    args.__dict__['comment'] = summary_data['comment']
    return args

class UpdateBitbucketSummary:
    def __init__(self, bitbucket_api: BitbucketAPI, prid: int, build_variant: str, result: str, tool: str,
                 details: str, components: list, comment: str, build_number: int, build_url: str,
                 commit_hash: str, user: str) -> None:
        self.bitbucket_api = bitbucket_api
        self.pr = bitbucket_api.get_pr(prid)
        self.build_variant = build_variant
        self.result = result
        self.tool = tool
        self.details = details or '-'
        self.components = ' '.join(map(lambda component: f'`{component}`', components)) or '-'
        self.detail = comment or '-'
        self.build_number = build_number
        self.build_url = build_url
        self.commit_hash = commit_hash
        self.user = user

    def update(self):
        comment = self._find_latest_comment()
        if comment:
            if comment.text.startswith(f'### Build report {self.commit_hash} ') and comment.author["name"].lower() == self.user.lower():
                new_line = self.__create_table_rows(self.tool, self.result, self.details, self.components, self.detail, self.build_number, self.build_url)
                if (len(comment.text) + len(new_line) < BITBUCKET_MAX_LENGTH):
                    LOGGER.debug('Build commit hash on comment is matching, updating old comment.')
                    self._update_existing_comment(comment)
                else:
                    LOGGER.debug('Build commit hash on comment is matching but reach limitation of comment length, creating additional comment.')
                    self._create_new_comment()
            else:
                LOGGER.debug('Build commit hash on comment is not matching, deleting old comment.')
                self._delete_outdated_comment()
                LOGGER.debug('Creating comment with new build commit hash')
                self._create_new_comment()
        else:
            LOGGER.debug('No comment with report table found. Creating new one.')
            self._create_new_comment()

    def _delete_outdated_comment(self):
        comments = self.pr.get_comments()
        for comment in comments:
            if '### Build report' in comment and not comment.text.startswith(f'### Build report {self.commit_hash} '):
                self.pr.delete_comment(comment)

    def _find_latest_comment(self) -> typing.Optional[Comment]:
        comments = self.pr.get_comments()
        for comment in comments:
            if '### Build report' in comment:
                return comment
        return None

    def __create_table_rows(self, tool: str, result: str, details: str, components: str,
                            comment: str, build_number: int, build_url: str, build_variant: str = ''):
        table_rows: str = ''
        lists = [[build_variant],
                 [tool],
                 result.split('\n'),
                 details.split('\n'),
                 [components],
                 (f'[\#{build_number}]({build_url})').split('\n'),
                 comment.split('\n')]
        max_elements: int = max(len(lst) for lst in lists)
        for lst in lists:
            lst.extend([''] * (max_elements - len(lst)))

        for row in zip(*lists):
            table_rows += '|' + '|'.join([str(item) for item in row]) + '|\n'
        return table_rows

    def _create_new_comment(self) -> Comment:
        text = f'### Build report {self.commit_hash} ` `\n\n' \
               '|**Variant**|**Tool**|**Result**|**Details**|**Components**|**Build**|**Comment**|\n' \
               '|-|-|-|-|-|-|-|\n' \
               f'{self.__create_table_rows(self.tool, self.result, self.details, self.components, self.detail, self.build_number, self.build_url, self.build_variant)}\n\n' \
               f'###### Reply to this comment to make it permanent.'
        return self.pr.create_comment(text)

    def _update_existing_comment(self, comment: Comment, retries: int = 3) -> bool:
        if retries <= 0:
            raise Exception('Could not update existing comment.')
        new_line = self.__create_table_rows(self.tool, self.result, self.details, self.components, self.detail, self.build_number, self.build_url)
        new_message, replaced = re.subn(r'^(\|' + self.build_variant + r'\|.*?\n(?:^\|\|.*\n)*)',
                                        fr'\g<1>{new_line}', comment.text, flags=re.MULTILINE)
        if not replaced:
            new_line = self.__create_table_rows(self.tool, self.result, self.details, self.components, self.detail,
                                                self.build_number, self.build_url, self.build_variant)
            new_message = re.sub(r'^((?:\|.*?\n)+)', fr'\g<1>{new_line}', comment.text,
                                 flags=re.MULTILINE)

        new_comment = self.pr.update_comment(comment, new_message)
        if not new_comment:
            time.sleep(1)
            LOGGER.debug(f'Could not update the comment, retrying, {retries} retries left.')
            comment = self.pr.get_comment(comment.id)
            self._update_existing_comment(comment, retries - 1)


if __name__ == '__main__':
    args = parse_args()

    if args.source == 'file':
        args = init_args_from_summary_file(args.summary_json, args)

    if args.debug:
        LOGGER.setLevel(logging.DEBUG)

    bitbucket_api = BitbucketAPI(args.bitbucket_url, args.user, args.password, args.bitbucket_project,
                                 args.bitbucket_repo, verify_ssl=False)
    report_updater = UpdateBitbucketSummary(bitbucket_api, args.prid, args.build_variant, args.result, args.tool,
                                            args.details, args.components, args.comment, args.build_number, args.build_url, args.commit_hash, args.user)
    report_updater.update()
