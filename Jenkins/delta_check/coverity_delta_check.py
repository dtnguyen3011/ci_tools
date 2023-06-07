#!/usr/bin/env python3
""" Script to create and compare compiler warnings
"""
import os
import csv
import sys
import json
import re
import argparse
import logging
import pprint
from io import StringIO
from pathlib import PurePath
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional, Union, List, Dict, Tuple, TextIO, Counter as CounterType

from artifactory import ArtifactoryStorageAPI
from bitbucket import BitbucketAPI
from update_bitbucket_summary import UpdateBitbucketSummary

logging.basicConfig(format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s', level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class ValidateArg(argparse.Action):
    """Class to validate if string argument is an empty string
    """

    def __call__(self, parser, namespace, values, option_string=None):
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
    parser.add_argument('--bitbucket-url', required=False, action=ValidateArg, help='Bitbucket URL',
                        default='https://sourcecode01.de.bosch.com')
    parser.add_argument('--bitbucket-repo', required=True, action=ValidateArg, help='Bitbucket repo name')
    parser.add_argument('--bitbucket-project', required=True, action=ValidateArg, help='Bitbucket project name')
    parser.add_argument('--artifactory-url', required=False, action=ValidateArg, help='Artifactory URL',
                        default='https://rb-artifactory.bosch.com/artifactory')
    parser.add_argument('--artifactory-repo', required=True, action=ValidateArg, help='Artifactory repo')
    parser.add_argument('--artifactory-baseline-path', required=True, action=ValidateArg,
                        help='Artifactory path to baselines')
    parser.add_argument('--artifactory-job-path', required=True, action=ValidateArg,
                        help='Artifactory path to job files')
    parser.add_argument('-cf', '--changed-files', required=True, action=ValidateArg,
                        help='Name of the file containing list of changed files')
    parser.add_argument('--coverity-csv-file', required=True, action=ValidateArg,
                        help='Name of the coverity report csv file')
    parser.add_argument('-tf', '--threshold-file', required=False, action=ValidateArg,
                        help='JSON file containing tresholds for tools')
    parser.add_argument('--build-variant', required=True, action=ValidateArg, help='Build variant')
    parser.add_argument('--ignore-type', required=False, action=ValidateArg, default=[], nargs='+',
                        help='Remove specified warning type from comparison')
    parser.add_argument('--debug', action='store_true', default=False, dest='debug', help='Enable debugging mode')

    return parser.parse_args()


def read_thresholds_file(tool: str, thresholds_file: str) -> CounterType:
    """Read content of thresholds file for specified tool

       Thresholds file is a JSON file with following format
       { "tool_name": [
         {
          "threshold": -1,
          "component_name": "AUTOSAR"
         }, ...
         ], ...
       }
       JSON Schema:
      {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "minProperties": 1,
        "properties": {
          "tool_name": {
            "type": "array",
            "uniqueItems": true,
            "minItems": 1,
            "items": {
              "type": "object",
              "properties": {
                "threshold": {
                  "type": "integer"
                },
                "component_name": {
                  "type": "string"
                }
              },
              "required": [
                "threshold",
                "component_name"
              ]
            }
          }
        }
      }

      Arguments:
        tool:
        thresholds_file: Name of the thresholds file

      Raises:
        IOError
    """
    thresholds: Counter = Counter()
    with open(thresholds_file, 'r') as tfile:
        data = json.loads(tfile.read())
        tool_thresholds = data[tool]
        for threshold in tool_thresholds:
            thresholds.update({threshold['component_name']: threshold['threshold']})
    return thresholds


def get_dates(shift: int = 0) -> Tuple[str, ...]:
    """Get tuple of date strings formatted as %Y-%m-%d

    Arguments:
      shift: Positive or negative integer which represents how many days
             will be included in tuple except current date. If shift is 0
             or hot provided, then there be only current date.

    Returns:
      Tuple[str, ...]
    """
    return tuple(datetime.strftime(datetime.now() - timedelta(x), '%Y-%m-%d') for x in range(0, abs(shift) + 1))


def contains_dates(string: str, dates: Tuple[str, ...]) -> bool:
    """Determines if string contains any string from tuple

    """
    for date in dates:
        if date in string:
            return True
    return False


def strip_drive(line: str) -> str:
    """Remove windows drive letter from path string
    """
    position: int = line.find(':\\')
    if position != -1:
        return line.rstrip()[position + 2:]
    return line


def get_changed_files(file_name: str) -> List[PurePath]:
    """Get files changed in PR from lucx provided CHANGED_FILES_FILE
    """

    try:
        with open(file_name, 'r') as changed_files_file:
            files_list = [PurePath(strip_drive(line).strip()) for line in changed_files_file.readlines() if
                          line.rstrip() != '']
            return files_list

    except IOError as error:
        LOGGER.error('Could not read changed files file: %s', error)
        raise


def read_csv(stream: Union[TextIO, str]) -> List[Dict[str, str]]:
    if isinstance(stream, str):
        stream = StringIO(stream)
    csv_reader = csv.DictReader(stream)
    return [dict(fields) for fields in csv_reader]


def read_csv_file(file_name: str) -> Optional[List[Dict[str, str]]]:
    """ Reads and returns the contents of the report CSV file if the file exists.
        If a file does not exist means that the files in the changed file list that were
        passed to sca_tools are not compilable. If there are errors in the sca_tools
        it will not generate a file also but will return a non-zero exit code and fail
        before this script.
    """

    try:
        with open(file_name, 'r') as infile:
            return read_csv(infile)
    except IOError as error:
        LOGGER.error('Could not read coverity report file: %s', error)
        return None


class CoverityWarning:
    # pylint: disable=too-many-instance-attributes

    stripped_main_event_file_pathname: str
    merge_key: str
    occurrence_count_for_mk: int
    occurrence_number_in_mk: int
    checker_name: str
    subcategory: str
    type: str
    subtype: str
    code_language: str
    extra: str
    domain: str
    language: str
    main_event_line_number: int
    function_display_name: str
    function_mangled_name: str
    category: str
    category_description: str
    cwe_category: str
    impact: str
    impact_description: str
    subcategory_local_effect: str
    subcategory_short_description: str
    subcategory_long_description: str
    main_event_file_pathname: str
    team: str
    components: str

    def __init__(self, object_data: dict):
        self.stripped_main_event_file_pathname = object_data['strippedMainEventFilePathname']
        self.merge_key = object_data['mergeKey']
        self.occurrence_count_for_mk = int(object_data['occurrenceCountForMK'])
        self.occurrence_number_in_mk = int(object_data['occurrenceNumberInMK'])
        self.checker_name = object_data['checkerName']
        self.subcategory = object_data['subcategory']
        self.type = object_data['type']
        self.subtype = object_data['subtype']
        self.code_language = object_data['code-language']
        self.extra = object_data['extra']
        self.domain = object_data['domain']
        self.language = object_data['language']
        self.main_event_line_number = int(object_data['mainEventLineNumber'])
        self.function_display_name = object_data['functionDisplayName']
        self.function_mangled_name = object_data['functionMangledName']
        self.category = object_data['category']
        self.category_description = object_data['categoryDescription']
        self.cwe_category = object_data['cweCategory']
        self.impact = object_data['impact']
        self.impact_description = object_data['impactDescription']
        self.subcategory_local_effect = object_data['subcategoryLocalEffect']
        self.subcategory_short_description = object_data['subcategoryShortDescription']
        self.subcategory_long_description = object_data['subcategoryLongDescription']
        self.main_event_file_pathname = object_data['mainEventFilePathname']
        self.team = object_data['Team']
        self.components = object_data['Components']

    def __hash__(self):
        return int(self.merge_key, 16)

    def __eq__(self, other):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return self.merge_key == other.merge_key

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__dict__})'


class CoverityWarnings(Counter):
    # pylint: disable=abstract-method
    def __init__(self, warnings: Union[List[dict], dict] = None):
        super().__init__()
        if warnings:
            for warning in warnings:
                coverity_warning = CoverityWarning(warning)
                self.update({coverity_warning: coverity_warning.occurrence_count_for_mk})

    def __sub__(self, other):
        if other.__class__ is not self.__class__:
            return NotImplemented

        result = CoverityWarnings()
        diff = super().__sub__(other)
        for elem, count in diff.items():
            result.update({elem: count})
        return result

    def filter_with_changed_files(self, changed_files: list) -> 'CoverityWarnings':
        """Filter warnings Counter by removing counter items that do not contain paths from changed files list
        """
        LOGGER.info(changed_files)
        result = CoverityWarnings()
        for warning, count in self.items():
            path = PurePath(warning.stripped_main_event_file_pathname)
            LOGGER.debug('Checking %s', path)
            if any(map(lambda changed_file, path=path: changed_file.match(str(path)), changed_files)):
                result.update({warning: count})
        return result


class CoverityWarningsDeltaCheck:
    """ Class to delta check coverity warnings
    """

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.tool = 'coverity'
        self.prid = int(os.getenv('LUCX_PULL_REQUEST', ''))
        self.build_number = int(os.getenv('BUILD_NUMBER', ''))
        LOGGER.debug(os.environ)
        self.bitbucket_api = BitbucketAPI(self.args.bitbucket_url, self.args.user, self.args.password,
                                          self.args.bitbucket_project, self.args.bitbucket_repo, verify_ssl=False)
        self.pr_title = self.bitbucket_api.get_pr(self.prid).title
        self.report_file = f'{self.args.build_variant}.report.html'
        self.report_url = f'{self.args.artifactory_url}/{self.args.artifactory_repo}/{self.args.artifactory_job_path}' \
                          f'/warnings/{self.report_file}'

        if self.args.debug:
            LOGGER.setLevel(logging.DEBUG)
        LOGGER.debug('Script called with following args:\n%s\n', pprint.pformat(vars(self.args)))

        if not self.prid:
            LOGGER.error('Script run as part of the PR, but LUCX_PULL_REQUEST environment variable is not set')
            sys.exit(1)
        if not self.build_number:
            LOGGER.error('Could not get environment variable BUILD_NUMBER')
            sys.exit(1)

    def __call__(self):
        """Main method
        """

        try:
            baseline, baseline_folder = self._get_baseline(self.args.coverity_csv_file)  # baseline warnings
            warnings = read_csv_file(self.args.coverity_csv_file)  # current warnings
            changed_files = get_changed_files(self.args.changed_files)  # changed files

            # Generate compiler warnings delta
            baseline_coverity_warnings = CoverityWarnings(read_csv(baseline))
            current_coverity_warnings = CoverityWarnings(warnings)

            delta = current_coverity_warnings.filter_with_changed_files(changed_files=changed_files) \
                    - baseline_coverity_warnings

            if delta:
                new_warning_count = sum(delta.values())
                new_warning_components = []

                self._bitbucket_update_message(f'{new_warning_count} :no_entry:',
                                               links=[f'[report]({self.report_url})'],
                                               components=new_warning_components,
                                               detail=f'Delta from [{baseline_folder[1:]}]({self.args.artifactory_url}' \
                                                      f'/{self.args.artifactory_repo}/{self.args.artifactory_baseline_path}' \
                                                      f'{baseline_folder})')
                sys.exit(1)

        except Exception as exc:
            LOGGER.exception(exc)
            self._bitbucket_update_message(':no_entry:', detail=f':boom: Error: {exc}')
            sys.exit(1)

        LOGGER.debug('Updating bitbucket message with "no new findings"')
        self._bitbucket_update_message('0 :white_check_mark:',
                                       detail=f'Delta from [{baseline_folder[1:]}]({self.args.artifactory_url}' \
                                              f'/{self.args.artifactory_repo}/{self.args.artifactory_baseline_path}' \
                                              f'{baseline_folder})')
        sys.exit(0)

    @staticmethod
    def __extract_sort_key(dirname: str) -> str:
        """ Finds and returns ISO8601 formatted datetime or date string.
            If no date found than returns unmodified string.
        """
        match = re.search(r'(\d{4}-\d{2}-\d{2}(?:T\d{2}-\d{2}-\d{2})?)', dirname)
        if match is not None:
            return match.group()
        return dirname

    def _get_baseline(self, baseline_file_name: str) -> Tuple[str, str]:
        """Get baseline JSON from Artifactory
        """
        artifactory = ArtifactoryStorageAPI(self.args.artifactory_url, self.args.artifactory_repo,
                                            self.args.user, self.args.password)
        build_folders = artifactory.get_info(self.args.artifactory_baseline_path)['children']

        dates = get_dates(-60)
        build_folders = filter(lambda item: item['folder'] and contains_dates(item['uri'], dates), build_folders)
        build_folders = list(map(lambda item: item['uri'], build_folders))
        LOGGER.debug('List of build folders:\n%s\n', pprint.pformat(build_folders))

        baseline: str = ''
        baseline_folder = ''
        baseline_file_name = os.path.basename(baseline_file_name)

        for build_folder in sorted(build_folders, key=self.__extract_sort_key, reverse=True):
            try:
                baseline_file_path = \
                    f'{self.args.artifactory_baseline_path}{build_folder}/{self.args.build_variant}/{baseline_file_name}'
                baseline_data = artifactory.get_artifact(baseline_file_path)
                baseline = baseline_data
                baseline_folder = build_folder
                break
            except Exception as exc:
                LOGGER.warning('Could not get baseline %s: %s', baseline_file_path, exc)

        if not baseline:
            LOGGER.error('No recent baseline found')
            raise Exception('No recent baseline found')

        LOGGER.info('Found baseline in %s', baseline_folder)
        return baseline, baseline_folder

    def _bitbucket_update_message(self, result: str, links: Optional[List] = None, components: Optional[List] = None,
                                  detail: str = '') -> None:
        """Recreate Bitbucket message with new information
        """
        details = '' if links is None else '\n'.join(links) 

        report_updater = UpdateBitbucketSummary(self.bitbucket_api, self.prid, self.args.build_variant, result,
                                                self.tool, details, components or [], detail, self.build_number)
        report_updater.update()


if __name__ == '__main__':
    cmdargs = parse_args()
    CoverityWarningsDeltaCheck(cmdargs)()
