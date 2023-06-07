"""
    Description: script to get info from generated warning file __Warnings.txt
    and put comment to pull request if warnings appear on changed files.
    Version: 3.7
    Ex: python compiler_warning_to_bitbucket.py 
"""

import argparse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from Bitbucket import BitbucketApi


def parse_args():
    description = "Get compiler warning data from generated warning file and comment to pull request"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-u', '--bb_user',
                        help='Username for access BitBucket')
    parser.add_argument('-p', '--bb_pwd',
                        help='Password for access BitBucket')
    parser.add_argument('-pj', '--project',
                        help='Project in BitBucket')
    parser.add_argument('-rp', '--repo',
                        help='Repository in BitBucket')
    parser.add_argument('-d', '--drive-map',
                        help='Some sw build have different mapping drive for build folder. Used in ccache build vag pj')
    parser.add_argument('-v', '--variant', required=True,
                        help='Variant used to build')
    parser.add_argument('-wf', '--warning-file', required=True,
                        help='Input warning txt file')
    parser.add_argument('-cf', '--changed-files', required=True,
                        help='file contain list of changedfiles')
    return parser.parse_args()


def get_changed_files(file, drive_map=None):
    changed_files = []
    with open(file, "r") as f:
        file_list = f.readlines()
    for i in range(len(file_list)):
        file_list[i] = file_list[i].rstrip()
    file_list = list(filter(None, file_list))
    if drive_map:
        file_list = [i.replace(os.getcwd(), drive_map) for i in file_list]
    for i in file_list:
        changed_files.append({'name': i.replace("\\", "/"), 'warning': 0})
    return changed_files

def get_warning_on_changed_files(warning_file, changed_files):
    with open(warning_file, "r") as f:
        lines = f.read().splitlines()
    lines = list(filter(None, lines))
    for line in lines:
        for file in changed_files:
            if file['name'] in line:
                file['warning'] += 1

    # Remove element doesn't have warning
    changed_files = [file for file in changed_files if file['warning'] > 0]
    print(changed_files)
    return changed_files

def create_comment(changed_files, variant):
    if changed_files:
        comment = f"Variant: {variant} :no_entry:\\n"
        for i in changed_files:
            comment+= f"{i['name']}. Warnings: {i['warning']}\\n"
        print(comment)
    else:
        comment = ""
        print("No warnings found on changed files")
    return comment

if __name__ == "__main__":
    args = parse_args()
    files = get_changed_files(args.changed_files, args.drive_map)
    data = get_warning_on_changed_files(args.warning_file, files)
    comment = create_comment(data, args.variant)
    pull_request = os.getenv('LUCX_PULL_REQUEST', 'null')
    if args.bb_user and args.bb_pwd and args.project and args.repo and comment:
        repo = BitbucketApi.BitbucketApi(args.project, args.repo, args.bb_user, args.bb_pwd)
        http_data = f"{{\\\"text\\\": \\\"{comment}\\\"}}"
        repo.post_comment_to_pullrequest(pull_request, http_data)
    else:
        print("Not putting comment to pull request")
