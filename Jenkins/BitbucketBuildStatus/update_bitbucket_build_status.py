#!/usr/bin/env python3
""" Script to update build status table in comment on Bitbucket PR page
"""

import sys
import re
import logging
import argparse
import time
import typing
from os.path import exists
from util import read_json_file
from bitbucket import BitbucketAPI, Comment


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
    parser.add_argument('--prid', required=True, action=ValidateIntArg, help='Pull request ID')
    parser.add_argument('--commit-hash', required=True, action=ValidateStringArg, help='Commit has is used to report build status')

    parser.add_argument('--build-variant', required=True, action=ValidateStringArg, help='Build variant')
    parser.add_argument('--target', required=True, action=ValidateStringArg, help='Reporting target build name')
    parser.add_argument('--overall-status', required=True, action=ValidateStringArg, help='Overall status of target build')
    parser.add_argument('--error-message', required=False, action=ValidateStringArg, help='Error message of target build')
    parser.add_argument('--error-message-file', required=False, action=ValidateStringArg, help='File contains error message of target build')
    parser.add_argument('--log-file', required=False, action=ValidateStringArg, help='Link to log file of target build')
    parser.add_argument('--addition-info', required=False, action=ValidateStringArg,
                               help='Additional info to display',
                               default=None)
    parser.add_argument('--addition-info-json-file', required=False, action=ValidateStringArg,
                               help='Additional info json file to display',
                               default=None)

    parser.add_argument('-u', '--user', required=True, action=ValidateStringArg, help='System user username')
    parser.add_argument('-p', '--password', required=True, action=ValidateStringArg, help='System user password')
    parser.add_argument('-bu', '--bitbucket-url', required=False, action=ValidateStringArg, help='Bitbucket URL',
                            default='https://sourcecode01.de.bosch.com')
    parser.add_argument('-br', '--bitbucket-repo', required=True, action=ValidateStringArg,
                            help='Bitbucket repo name')
    parser.add_argument('-bp', '--bitbucket-project', required=True, action=ValidateStringArg,
                            help='Bitbucket project name')
    parser.add_argument('--debug', action='store_true', default=True, dest='debug',
                            help='Enable debugging mode')

    return parser.parse_args()

class UpdateBitbucketBuildStatus:

    status_mapping = {
        "Success" : ":white_check_mark:Success",
        "Fail" : ":no_entry:Fail",
        "In progress" : ":arrows_counterclockwise:In_progress",
        "Abort" : ":heavy_multiplication_x:Abort",
        "n/a" : ":white_circle:N/A",
    }

    def __init__(self, bitbucket_api: BitbucketAPI, prid: int, build_variant: str, target: str,
                 overall_status: str, error_message: str, error_message_file: str, log_file: str, addition_info: str,
                 addition_info_json_file: str, commit_hash: str, user: str) -> None:
        self.bitbucket_api = bitbucket_api
        self.pr = bitbucket_api.get_pr(prid)
        self.build_variant = build_variant
        self.target = target
        self.overall_status = overall_status
        if error_message_file:
            self.error_message = open(error_message_file, "r").read() or '-'
        else:
            self.error_message = error_message or '-'
        if len(self.error_message) > 210:
            self.error_message = f'{self.error_message[0:200]}[...]'
        self.log_file = log_file or '-'
        if addition_info_json_file and exists(addition_info_json_file):
            self.addition_info = open(addition_info_json_file, "r").read() or '-'
            addition_info_data: dict = read_json_file(addition_info_json_file)
            self.addition_info = f'Failed stage: {addition_info_data["name"]}'
            if addition_info_data["meta"]:
                if "description" in addition_info_data["meta"]:
                    self.addition_info += f'\nDescription: {addition_info_data["meta"]["description"]}'
                if "documentation" in addition_info_data["meta"]:
                    self.addition_info += f'\nDocumentation: {addition_info_data["meta"]["documentation"]}'
                if "maintainer" in addition_info_data["meta"]:
                    self.addition_info += f'\nMaintainer: {addition_info_data["meta"]["maintainer"]}'
        else:
            self.addition_info = addition_info or '-'
        self.commit_hash = commit_hash
        self.user = user

    def update(self):
        comment = self._find_latest_comment()
        if comment:
            if comment.text.startswith(f'### Build status report {self.commit_hash} ') and comment.author["name"].lower() == self.user.lower():
                LOGGER.debug('Build commit hash on comment is matching, updating old comment.')
                self._update_existing_comment(comment)
            else:
                LOGGER.debug('Build commit hash on comment is not matching, deleting old comment.')
                self.pr.delete_comment(comment)
                LOGGER.debug('Creating comment with new build commit hash')
                self._create_new_comment()
        else:
            LOGGER.debug('No comment with report table found. Creating new one.')
            self._create_new_comment()

    def _find_latest_comment(self) -> typing.Optional[Comment]:
        comments = self.pr.get_comments()
        for comment in comments:
            if '### Build status report' in comment:
                return comment
        return None

    def __create_table_rows(self, overall_status: str, error_message: str, log_file: str,
                            addition_info: str, build_variant: str = '', target: str = ''):
        # Generate symbol for input status
        if overall_status not in self.status_mapping:
            LOGGER.error('Overall status "%s" is not available', overall_status)
            sys.exit(1)
        overall_status = self.status_mapping[overall_status]
        
        # Generate link to log file
        if "http" in log_file:
            log_file = "[Log](" + log_file + ")"

        table_rows: str = ''
        lists = [[build_variant],
                 [target],
                 overall_status.split('\n'),
                 error_message.replace("|", "\\|").split('\n'),
                 log_file.split('\n'),
                 addition_info.replace("|", "\\|").split('\n')]
        max_elements: int = max(len(lst) for lst in lists)
        for lst in lists:
            lst.extend([''] * (max_elements - len(lst)))

        for row in zip(*lists):
            table_rows += '|' + '|'.join([str(item) for item in row]) + '|\n'
        return table_rows

    def _create_new_comment(self) -> Comment:
        text = f'### Build status report {self.commit_hash} ` `\n' \
               f'### Quality Gate failed and no clue? [read here](https://inside-docupedia.bosch.com/confluence/x/FFmtfg)\n\n' \
               '|**Variant**|**Target**|**Overall Status**|**Error message**|**Link to log file**|**Additional info**|\n' \
               '|-|-|-|-|-|-|\n' \
               f'{self.__create_table_rows(self.overall_status, self.error_message, self.log_file, self.addition_info, self.build_variant, self.target)}\n\n' \
               f'###### Reply to this comment to make it permanent.'
        return self.pr.create_comment(text)

    def _update_existing_comment(self, comment: Comment, retries: int = 3) -> bool:
        if retries <= 0:
            raise Exception('Could not update existing comment.')
        new_line = self.__create_table_rows(self.overall_status, self.error_message, self.log_file, self.addition_info, self.build_variant, self.target)

        # Check for abort status constraint: Last status should be "In Progress"
        if self.status_mapping["Abort"] in new_line:
            new_message, replaced = re.subn(r'^(\|' + self.build_variant + r'\|' + self.target + r'\|' + self.status_mapping["In progress"] + r'\|.*?\n)',
                                        new_line.replace("\\", "\\\\"), comment.text, flags=re.MULTILINE)
            if not replaced:
                LOGGER.debug(f'Skip update abort status due to last status is not in progress')
                return
        # Other status should be updated without any constraint
        else:
            new_message, replaced = re.subn(r'^(\|' + self.build_variant + r'\|' + self.target + r'\|.*?\n(\|\|\|\|\|\|.*?\n)*)',
                                        new_line.replace("\\", "\\\\"), comment.text, flags=re.MULTILINE)
            if not replaced:
                LOGGER.debug(f'Could not replace for : {new_line}')
                new_line = self.__create_table_rows(self.overall_status, self.error_message, self.log_file, self.addition_info,
                                                    self.build_variant, self.target)
                new_message = re.sub(r'^((?:\|.*?\n)+)', fr'\g<1>{new_line}', comment.text,
                                    flags=re.MULTILINE)
        new_comment = self.pr.update_comment(comment, new_message)
        if not new_comment:
            time.sleep(60)
            LOGGER.debug(f'Could not update the comment, retrying, {retries} retries left.')
            comment = self.pr.get_comment(comment.id)
            self._update_existing_comment(comment, retries - 1)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s', level=logging.INFO)
    LOGGER = logging.getLogger(__name__)
    args = parse_args()

    if args.debug:
        LOGGER.setLevel(logging.DEBUG)

    bitbucket_api = BitbucketAPI(args.bitbucket_url, args.user, args.password, args.bitbucket_project,
                                 args.bitbucket_repo, verify_ssl=False)
    report_updater = UpdateBitbucketBuildStatus(bitbucket_api, args.prid, args.build_variant, args.target, args.overall_status,
                                                args.error_message, args.error_message_file, args.log_file, args.addition_info,
                                                args.addition_info_json_file, args.commit_hash, args.user)
    report_updater.update()