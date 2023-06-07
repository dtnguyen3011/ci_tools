'''
    File name: BranchStats.py
    Author: Christoph Granzow
    Date created: 11/12/2018
    Date last modified: 05/02/2019
    Python Version: 3.7.4
'''

import argparse
import subprocess
import json
from subprocess import Popen, PIPE


def parse_args():
    description = "Branch Statistics generation. Branch Develop as reference"
    parser = argparse.ArgumentParser(description=description) 
    parser.add_argument('-pj', '--project', dest='project', required=True,
                        help='Project in BitBucket')
    parser.add_argument('-rp', '--repo', dest='repo', required=True,
                        help='Repository in BitBucket')
    parser.add_argument('-ubb', '--usernamebb', dest='usernamebb', required=True,
                        help='Username for access BitBucket')
    parser.add_argument('-pbb', '--passwordbb', dest='passwordbb', required=True,
                        help='Password for access BitBucket')
    parser.add_argument('-f', '--filename', dest='filename', required=True,
                        default='FilesToDelete.txt', help='file with files to delete (rel/abs)')

    return parser.parse_args()

def curl_delete(user, pwd, query_url, branch):
    cmd = f'curl -X DELETE -u "{user}:{pwd}" -k "{query_url}" -H "Content-Type: application/json" -d "{{\\"name\\": \\"{branch}\\", \\"dryRun\\": false}}"'
    print(cmd)
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = pipe.communicate()
    return out

if __name__ == '__main__':
    args = parse_args()
    project_name = args.project
    repository_name = args.repo
    bb_user = args.usernamebb
    bb_pwd = args.passwordbb
    file_name = args.filename

    # urls
    bb_branch_util_url = f"https://sourcecode01.de.bosch.com/rest/branch-utils/1.0/projects/{project_name}/repos/{repository_name}"
    bb_url = f"https://sourcecode01.de.bosch.com/projects/{project_name}/repos/{repository_name}"

    # Initialize data
    branchNames = []

    with open(file_name, "r", encoding="iso-8859-1") as branchesToDelete:
        for row in branchesToDelete:
            branchNames.append(row.split()[0])

    print('\n'.join(branchNames))


    for branch in branchNames:
        # query branch data
        bb_query = f'{bb_branch_util_url}/branches'
        ref_branch = f"refs/heads/{branch}"
        print(bb_query)
        response = curl_delete(bb_user, bb_pwd, bb_query, ref_branch)
        print(response)
