#!/usr/bin/env python3
""" Script to download latest baselines
"""

import sys
import argparse
import logging
import typing
import subprocess
from util import get_dates, contains_dates, extract_sort_key, write_json_file
from artifactory import ArtifactoryStorageAPI


class NoRecentBaselineException(Exception):
    pass


def positive_int(value: str) -> typing.Optional[int]:
    if int(value) > 0:
        return int(value)
    return None


def nonempty_str(value: str) -> typing.Optional[str]:
    if len(value) > 0:
        return value
    return None


def parse_args() -> argparse.Namespace:
    """Adds and parses command line arguments

    Returns:
      argparse.Namespace
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True, type=nonempty_str, help='System user username')
    parser.add_argument('-p', '--password', required=True, type=nonempty_str, help='System user password')
    parser.add_argument('--type', required=True, type=nonempty_str, help='Kind of tools do you want to use, ex: qac, compiler',)
    parser.add_argument('--baseline-file', required=False, type=nonempty_str, help='File name of the baseline to download',)
    parser.add_argument('--artifactory-url', required=False, type=nonempty_str, help='Artifactory URL',
                        default='https://rb-artifactory.bosch.com/artifactory')
    parser.add_argument('--artifactory-repo', required=True, type=nonempty_str, help='Artifactory repo')
    parser.add_argument('--artifactory-baseline-path', required=True, type=nonempty_str, help='Arfifactory baseline path')
    parser.add_argument('--artifactory-baseline-subfolder', required=False, type=nonempty_str, default='baselines',
                        help='Subfolder of baseline path')
    parser.add_argument('--summary-json', required=False, type=nonempty_str,
                        help='JSON file name of summary')
    parser.add_argument('--build-variant', required=True, type=nonempty_str, help='Build variant')
    parser.add_argument('--build-number', required=False, type=positive_int, default=None, help='Build number')
    parser.add_argument('--prid', required=False, type=positive_int, default=None, help='Pull request ID')
    parser.add_argument('--days', required=False, type=int, default=1, help='Time scope in days')
    parser.add_argument('--save-as', required=False, default='', help='Save baseline as')
    parser.add_argument('--tool', required=False, default='compiler', help='Tool to report in summary file')
    parser.add_argument('--download-commit-file', action='store_true', default=False, help='Download commit file')
    parser.add_argument('--debug', action='store_true', default=False, dest='debug', help='Enable debugging mode')

    return parser.parse_args()


def get_build_folders():
    """Get build folders baseline from Artifactory
    """
    artifactory = ArtifactoryStorageAPI(args.artifactory_url, args.artifactory_repo,
                                        args.user, args.password)
    build_folders = artifactory.get_info(args.artifactory_baseline_path)['children']

    dates = get_dates(args.days)
    build_folders = filter(lambda item: item['folder'] and contains_dates(item['uri'], dates), build_folders)
    build_folders = list(map(lambda item: item['uri'], build_folders))
    return build_folders, artifactory
    
def get_compiler_baseline() -> typing.Tuple[str, str, str]:
    """Get baseline JSON from Artifactory
    """
    build_folders, artifactory = get_build_folders()
    LOGGER.debug('List of build folders:\n%s\n', '\n'.join(build_folders))

    baseline = None
    commit = None
    baseline_file = args.baseline_file or f'warnings-{args.build_variant}.json'
    baseline_commit_file = f'{baseline_file.replace(".json", "")}.commit'
    baseline_folder = None

    for build_folder in sorted(build_folders, key=extract_sort_key, reverse=True):
        try:
            print(f'{args.artifactory_baseline_path}/{build_folder}/{args.artifactory_baseline_subfolder}/{baseline_file}')
            baseline = artifactory.get_artifact(
                f'{args.artifactory_baseline_path}/{build_folder}/{args.artifactory_baseline_subfolder}/{baseline_file}')
            baseline_folder = build_folder
            if args.download_commit_file:
                print(f'{args.artifactory_baseline_path}/{build_folder}/{args.artifactory_baseline_subfolder}/{baseline_commit_file}')
                commit = artifactory.get_artifact(
                    f'{args.artifactory_baseline_path}/{build_folder}/{args.artifactory_baseline_subfolder}/{baseline_commit_file}')
            break
        except Exception as exc:
            LOGGER.warning('Could not get baseline from %s: %s', build_folder, exc)

    if not baseline:
        LOGGER.error('No recent baseline found')
        raise NoRecentBaselineException('No recent baseline found')

    LOGGER.info('Found baseline in %s', baseline_folder)
    return baseline, commit, baseline_folder


def get_qac_baseline() -> typing.Tuple[str, str, str]:
    """Get baseline files.sup from Artifactory
    """
    build_folders, artifactory = get_build_folders()
    LOGGER.debug('List of build folders:\n%s\n', '\n'.join(build_folders))

    baseline = None
    baseline_file = args.baseline_file or f'files.sup'
    baseline_url = None

    for build_folder in sorted(build_folders, key=extract_sort_key, reverse=True):
        try:
            baseline_url = f'{args.artifactory_baseline_path}/{build_folder}/{args.artifactory_baseline_subfolder}/{args.build_variant}/{baseline_file}'
            print(f'{baseline_url}')
            baseline = artifactory.check_exitsFile(baseline_url)
            break
        except Exception as exc:
            LOGGER.warning('Could not get baseline from %s: %s', build_folder, exc)

    if not baseline:
        LOGGER.error('No recent baseline found')
        raise NoRecentBaselineException('No recent baseline found')

    LOGGER.info('Found baseline in %s', baseline_url)
    return baseline_url


def main(args: argparse.Namespace) -> None:
    if args.type == "compiler":
        try:
            baseline, commit, _ = get_compiler_baseline()
        except Exception as exc:
            LOGGER.error(exc)
            write_json_file(args.summary_json, {
                'pr_id': args.prid,
                'build_number': args.build_number,
                'variant': args.build_variant,
                'tool': args.tool,
                'result': ':no_entry:',
                'details': '',
                'components': list(),
                'comment': f':boom: Error: {exc}',
            })
            sys.exit(1)

        file_name: str = args.save_as or f'baseline-{args.build_variant}.json'
        with open(file_name, 'w') as outfile:
            outfile.write(baseline)

        if args.download_commit_file:
            baseline_commit_file = f'{args.save_as.replace(".json", "")}.commit'
            file_name: str = baseline_commit_file or f'baseline-{args.build_variant}.commit'
            with open(file_name, 'w') as outfile:
                outfile.write(commit)
    elif args.type == "qac":
        try:
            baseline_url = get_qac_baseline()
            download_baseline_command = f"curl --url {args.artifactory_url}/{args.artifactory_repo}/{baseline_url} --user {args.user}:{args.password} --insecure --output {args.save_as} --create-dirs"
            subprocess.check_call(download_baseline_command)
            print("QAC Baseline downloaded successfully")
        except Exception as exc:
            LOGGER.error(exc)
            sys.exit(1)
        except subprocess.CalledProcessError as exc:
            LOGGER.error(exc)
            sys.exit(1)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s', level=logging.INFO)
    LOGGER = logging.getLogger(__name__)
    args = parse_args()

    LOGGER.setLevel(args.debug)
    main(args)