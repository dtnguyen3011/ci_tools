#!/usr/bin/env python3
""" Script to create and compare compiler warnings
"""
import os
import sys
import json
import re
import argparse
import logging
import pprint
from collections import Counter
from datetime import datetime, timedelta
import typing
from jinja2 import Environment, FileSystemLoader

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
  parser.add_argument('--artifactory-job-path', required=True, action=ValidateArg, help='Artifactory path to job files')
  parser.add_argument('-cf', '--changed-files', required=True, action=ValidateArg,
                      help='Name of the file containing list of changed files')
  parser.add_argument('-tf', '--threshold-file', required=False, action=ValidateArg,
                      help='JSON file containing tresholds for tools')
  parser.add_argument('--build-variant', required=True, action=ValidateArg, help='Build variant')
  parser.add_argument('--ignore-type', required=False, action=ValidateArg, default=[], nargs='+',
                      help='Remove specified warning type from comparison')
  parser.add_argument('-sc', '--source-commit', required=False, action=ValidateArg, default='Not found',
                      help='Source commit for compiler warning check')
  parser.add_argument('-tc', '--target-commit', required=False, action=ValidateArg, default='Not found',
                      help='Target commit for compiler warning check')
  parser.add_argument('--debug', action='store_true', default=False, dest='debug', help='Enable debugging mode')

  return parser.parse_args()


def read_thresholds_file(tool: str, thresholds_file: str) -> typing.Counter:
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
  thresholds = Counter()
  with open(thresholds_file, 'r') as tf:
    data = json.loads(tf.read())
    tool_thresholds = data[tool]
    for threshold in tool_thresholds:
      thresholds.update({threshold['component_name']: threshold['threshold']})
  return thresholds


def get_dates(shift: int = 0) -> typing.Tuple[str, ...]:
  """Get tuple of date strings formatted as %Y-%m-%d

  Arguments:
    shift: Positive or negative integer which represents how many days
           will be included in tuple except current date. If shift is 0
           or hot provided, then there be only current date.

  Returns:
    Tuple[str, ...]
  """
  return tuple(datetime.strftime(datetime.now() - timedelta(x), '%Y-%m-%d') for x in range(0, abs(shift) + 1))


# TODO: Substitute with inline variant
def contains_dates(string: str, dates: typing.Tuple[str, ...]) -> bool:
  """Determines if string contains any string from tuple

  """
  for date in dates:
    if date in string:
      return True
  return False


class CLWarning:
  """Compiler/Linker warning object
  """

  def __init__(self, object_data: dict):
    self.file_path = object_data['file_path']
    self.row = object_data['row']
    self.column = object_data['column']
    self.message = object_data['message']
    self.components = object_data['components']
    self.teams = object_data['teams']
    self.severity = object_data['severity']
    self.type_name = object_data['type_name']
    self.quantity = None
    self.domain = object_data['domain']
    self.pr_related = True

  def __eq__(self, other):
    select_keys = ['file_path', 'message', 'components', 'severity', 'type_name']
    if isinstance(other, self.__class__):
      return ({k: v for k, v in self.__dict__.items() if k in select_keys} ==
              {k: v for k, v in other.__dict__.items() if k in select_keys})
    else:
      return False

  def __repr__(self):
    return f'CLWarning({self.__dict__})'

  def __hash__(self):
    severity = self.severity or ''
    type_name = self.type_name or ''

    return hash(self.file_path + str(self.message) + repr(self.components) +
                severity + type_name)


# TODO: Find out if it's possible to make Counter count to be linked to field of the CLWarning
class CLWarnings(Counter):
  """Object containing list of warnings
  """

  def __init__(self, warnings: dict = None):
    super().__init__()
    if warnings:
      for warning in warnings:
        super().update({CLWarning(warning): warning['quantity']})

  def __sub__(self, other):
    result = CLWarnings()
    diff = super().__sub__(other)
    for elem, count in diff.items():
      result.update({elem: count})
    return result

  def filter_by_domain(self, domain: str) -> 'CLWarnings':
    """ Filter that belong to specified domain

    Args:
      domain: domain for filter

    Returns:
      CLWarnings
    """
    result = CLWarnings()
    for elem, count in self.items():
      if elem.domain == domain:
        result.update({elem: count})
    return result

  def filter_by_types(self, types: list) -> 'CLWarnings':
    """ Filter out specific warning types

    Args:
      types: list of types to filter out

    Returns:
      CLWarnings
    """
    result = CLWarnings()
    types_upper = [t.upper() for t in types]
    for elem, count in self.items():
      if (elem.type_name is None) or (elem.type_name.upper() not in types_upper):
        result.update({elem: count})
    return result

  def filter_by_component(self, component: str) -> 'CLWarnings':
    """Filter out warnings with specified component

    Returns:
      CLWarnings
    """
    result = CLWarnings()
    for elem, count in self.items():
      if component.upper() not in map(lambda team: team.upper(), elem.teams):
        result.update({elem: count})
    return result

  def get_warnings_per_component(self) -> typing.Counter:
    """ Get warning count per component
        If warning belongs to multiple components, adds warnings quantity to each component

    Returns:
        Counter
    """
    result = Counter()
    for elem, count in self.items():
      for team in elem.teams:
        result.update({team: count})
    return result

  def filter_with_changed_files(self, changed_files: list) -> 'CLWarnings':
    """Filter warnings Counter by removing counter items that do not contain paths from changed files list

    Args:
      changed_files: list of changed files in form of 'dir/subdir/subdir2/filename

    Returns:
      CLWarnings
    """

    def strip_drive(line: str) -> str:
      """Remove windows drive letter from path string
      """
      return line.rstrip()[line.find(':\\') + 2:]

    LOGGER.info(changed_files)
    result = CLWarnings()
    for warning, count in self.items():
      file = warning.file_path
      path = strip_drive(os.path.abspath(file))
      LOGGER.debug('Checking %s', path)
      if any(map(lambda changed_file: changed_file.endswith(path), changed_files)):
        result.update({warning: count})
    return result


class CompilerWarningsDeltaCheck:
  """ Class to delta check compiler warnings
  """

  def __init__(self, args: argparse.Namespace):
    self.args = args
    self.tool = 'compiler'
    self.prid = int(os.getenv('LUCX_PULL_REQUEST', None))
    self.build_number = int(os.getenv('BUILD_NUMBER', None))
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
      baseline, baseline_folder = self._get_baseline()  # baseline warnings
      warnings = self._get_warnings()  # current warnings
      changed_files = self._get_changed_files()  # changed files

      baseline_warnings = CLWarnings(baseline)
      current_warnings = CLWarnings(warnings)

      # Check for compiler warning thresholds if threshold file argument exists
      if self.args.threshold_file:
        LOGGER.info('Checking thresholds...')
        warnings_per_component = current_warnings.get_warnings_per_component()
        thresholds = read_thresholds_file(self.tool, self.args.threshold_file)
        LOGGER.debug('Warnings per component: %s', warnings_per_component)
        LOGGER.debug('Configured thresholds: %s', thresholds)
        for threshold in thresholds:
          if thresholds[threshold] == -1:
            # Filter out the warnings with specified threshold if threshold is -1
            LOGGER.info('Ignoring all warnings for component %s', threshold)
            current_warnings = current_warnings.filter_by_component(threshold)

      current_linker_warnings = current_warnings.filter_by_domain('linker')
      current_compiler_warnings = current_warnings.filter_by_domain('compiler')

      # Generate compiler warnings delta
      delta = current_compiler_warnings \
                .filter_with_changed_files(changed_files) \
                .filter_by_types(self.args.ignore_type) - baseline_warnings

      if delta:
        new_warning_count = sum(delta.values())
        new_warning_components = set()
        for warning in delta.keys():
          new_warning_components.update(warning.teams)
        if 'undefined' in new_warning_components:
          new_warning_components.remove('undefined')
        if not new_warning_components:
          new_warning_components = []

        report_warnings = []
        for warning, count in delta.items():
          warning.quantity = count
          report_warnings.append(warning.__dict__)
        for warning, count in current_linker_warnings.items():
          warning.quantity = count
          report_warnings.append(warning.__dict__)

        self._create_html_report(report_warnings)
        self._bitbucket_update_message(f'{new_warning_count} :no_entry:', links=[f'[report]({self.report_url})'],
                                       components=new_warning_components,
                                       detail=f'Delta from [{baseline_folder[1:]}]({self.args.artifactory_url}' \
                                              f'/{self.args.artifactory_repo}/{self.args.artifactory_baseline_path}' \
                                              f'{baseline_folder})')
        sys.exit(1)

    except Exception as e:
      LOGGER.exception(e)
      self._bitbucket_update_message(':no_entry:', detail=f':boom: Error: {e}')
      sys.exit(1)

    LOGGER.debug('Updating bitbucket message with "no new findings"')
    self._bitbucket_update_message('0 :white_check_mark:',
                                   detail=f'Delta from [{baseline_folder[1:]}]({self.args.artifactory_url}' \
                                          f'/{self.args.artifactory_repo}/{self.args.artifactory_baseline_path}' \
                                          f'{baseline_folder})')
    sys.exit(0)

  def _get_changed_files(self) -> list:
    """Get files changed in PR from lucx provided CHANGED_FILES_FILE
    """

    def strip_drive(line: str) -> str:
      """ Strip windows drive letter from string
      """
      return line.rstrip()[line.find(':\\') + 2:]

    try:
      with open(self.args.changed_files, 'r') as changed_files_file:
        files_list = [strip_drive(line) for line in changed_files_file.readlines() if line.rstrip() != '']
        return files_list

    except IOError as error:
      LOGGER.error('Could not read file: %s', error)
      raise Exception('Could not read changed files file')

  @staticmethod
  def __extract_sort_key(dirname: str) -> str:
    """ Finds and returns ISO8601 formatted datetime or date string.
        If no date found than returns unmodified string.
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2}(?:T\d{2}-\d{2}-\d{2})?)', dirname)
    if match is not None:
      return match.group()
    return dirname

  def _get_baseline(self) -> typing.Tuple[dict, str]:
    """Get baseline JSON from Artifactory
    """
    artifactory = ArtifactoryStorageAPI(self.args.artifactory_url, self.args.artifactory_repo,
                                        self.args.user, self.args.password)
    build_folders = artifactory.get_info(self.args.artifactory_baseline_path)['children']

    dates = get_dates(-1)
    build_folders = filter(lambda item: item['folder'] and contains_dates(item['uri'], dates), build_folders)
    build_folders = list(map(lambda item: item['uri'], build_folders))
    LOGGER.debug('List of build folders:\n%s\n', pprint.pformat(build_folders))

    baseline = None
    baseline_file = f'warnings-{self.args.build_variant}.json'
    baseline_folder = None

    for build_folder in sorted(build_folders, key=self.__extract_sort_key, reverse=True):
      try:
        baseline = artifactory.get_artifact(
            f'{self.args.artifactory_baseline_path}/{build_folder}/baselines/{baseline_file}')
        baseline = json.loads(baseline)
        baseline_folder = build_folder
        break
      except Exception as e:
        LOGGER.warning('Could not get baseline from %s: %s', build_folder, e)

    if not baseline:
      LOGGER.error('No recent baseline found')
      raise Exception('No recent baseline found')

    LOGGER.info('Found baseline in %s', baseline_folder)
    return baseline, baseline_folder

  def _get_warnings(self) -> dict:
    """Read compiler warnings from JSON formatted file
    """
    try:
      with open(f'warnings-{self.args.build_variant}.json', 'r') as warnings:
        return json.loads(warnings.read())

    except IOError as error:
      LOGGER.error('Could not read file: %s', error)
      raise Exception('Could not read file with compiler warnings')

  def _bitbucket_update_message(self, result: str, links: list = None, components: list = None,
                                detail: str = None) -> None:
    """Recreate Bitbucket message with new information
    """
    details = '' if links is None else '\n'.join(links)

    report_updater = UpdateBitbucketSummary(self.bitbucket_api, self.prid, self.args.build_variant, result, self.tool,
                                            details, components or [], detail, self.build_number)
    report_updater.update()

  def _create_html_report(self, data: list) -> None:
    """Create HTML report with Jinja2
    """
    loader = Environment(loader=FileSystemLoader('./cust/common/tools/ci_tools/Jenkins/delta_check/templates'))
    template = loader.get_template('compiler_delta_report.html')
    page_body = template.render(json_data=json.dumps(data), prid=self.prid, variant=self.args.build_variant,
                                build_number=self.build_number, pr_title=self.pr_title,
                                source_commit=self.args.source_commit, target_commit=self.args.target_commit)
    report_file = open(self.report_file, 'w')
    report_file.write(page_body)


if __name__ == '__main__':
  cmdargs = parse_args()
  CompilerWarningsDeltaCheck(cmdargs)()
