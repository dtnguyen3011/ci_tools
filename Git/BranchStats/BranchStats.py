'''
    File name: BranchStats.py
    Author: Marcel Lucas, Uwe Lang, Christoph Granzow
    Date created: 11/12/2018
    Date last modified: 05/02/2019
    Python Version: 3.7.4
'''

import argparse
import subprocess
import json
from subprocess import Popen, PIPE
from datetime import datetime, timedelta
import os


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
    parser.add_argument('-t', '--ticket', dest='addTicketInfo', required=False,
                        default='', help='option for add detailed ticket information')
    parser.add_argument('-f', '--filename', dest='filename',
                        help='option for the file name or path (rel/abs)')

    return parser.parse_args()

def curl_query_json(user, pwd, query_url):
    cmd = f'curl -u {user}:{pwd} "{query_url}"'
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = pipe.communicate()
    jsondata = json.loads(out.decode("utf-8"))
    return jsondata

if __name__ == '__main__':
    args = parse_args()
    project_name = args.project
    repository_name = args.repo
    bb_user = args.usernamebb
    bb_pwd = args.passwordbb
    addTicketInfo = args.addTicketInfo

    if not args.filename:
        file_name = f'BranchStats_{args.repo}.csv'
    else:
        file_name = args.filename

    # urls
    bb_api_url = f"https://sourcecode01.de.bosch.com/rest/api/1.0/projects/{project_name}/repos/{repository_name}"
    bb_url = f"https://sourcecode01.de.bosch.com/projects/{project_name}/repos/{repository_name}"
    jira_api_url = "https://rb-tracker.bosch.com/tracker08/rest/api/latest/issue"
    jira_url = "https://rb-tracker.bosch.com/tracker08/browse"


    # package and meta properties
    branch_pkg= 'com.atlassian.bitbucket.server.bitbucket-branch'
    jira_pkg = 'com.atlassian.bitbucket.server.bitbucket-jira'
    ref_pkg = 'com.atlassian.bitbucket.server.bitbucket-ref-metadata'
    meta_ahead = 'ahead-behind-metadata-provider'
    meta_commit = 'latest-commit-metadata'
    jira_list = 'branch-list-jira-issues'
    meta_pr = 'outgoing-pull-request-metadata'

    # Initialize data
    nextPageStart = 0
    isLastPage = False
    branchInfos = []

    while (isLastPage == False):
        # query branch data
        bb_query = f'{bb_api_url}/branches?details=true&start={nextPageStart}'
        jsondata = curl_query_json(bb_user, bb_pwd, bb_query)
        isLastPage = jsondata['isLastPage']

        # read data for each branch
        for i in range(jsondata['size']):
            # reset branch data dict
            branchData = {'name': '', 'ahead': '', 'behind': '', 'lastModifiedDate': '', 'lastModifiedBy': '',
                          'ticketID': '', 'ticketStatus': '', 'prID': '', 'prState': '', 'targetBranch': '',
                          'ticketAssignee' : '', 'ticketURL' : '', 'BranchURL' : '', 'prURL' : ''}
            branchData["name"] = jsondata['values'][i]['displayId']
            branchData["BranchURL"] = f"{bb_url}/browse?at={jsondata['values'][i]['id']}"

            # check if ahead behind metadata are available (otherwise this is the reference branch)
            if f"{branch_pkg}:{meta_ahead}" in jsondata['values'][i]['metadata']:
                branchData["ahead"] = jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_ahead}"]['ahead']
                branchData["behind"] = jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_ahead}"]['behind']
            else:
                branchData["ahead"] = 'Reference'
                branchData["behind"] = 'Reference'

            # check if authors display name is available => try to get the best information
            if 'displayName' in jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_commit}"]['author']:
                branchData["lastModifiedBy"] = jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_commit}"]['author']['displayName']
            elif 'name' in jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_commit}"]['author']:
                branchData["lastModifiedBy"] = jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_commit}"]['author']['name']
            elif 'emailAddress' in jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_commit}"]['author']:
                branchData["lastModifiedBy"] = jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_commit}"]['author']['emailAddress']

            # get timestamp and format to UTC
            time = int(jsondata['values'][i]['metadata'][f"{branch_pkg}:{meta_commit}"]['authorTimestamp'])
            branchData["lastModifiedDate"]  = str(datetime.fromtimestamp(time / 1000))

            # check if the branch was created via JIRA and get ticket info
            if len(jsondata['values'][i]['metadata'][f"{jira_pkg}:{jira_list}"]) > 0:
                branchData["ticketID"] = jsondata['values'][i]['metadata'][f"{jira_pkg}:{jira_list}"][0]['key']

                # check if detailed ticket info should be added
                if addTicketInfo:
                    jira_query = f'{jira_api_url}/{branchData["ticketID"]}?fields=assignee,status'
                    jsondataTicket =  curl_query_json(bb_user, bb_pwd, jira_query)

                    # check for error messages => permissions for board might be missing
                    if 'errorMessages' not in jsondataTicket:
                        branchData["ticketStatus"] = jsondataTicket ['fields']['status']['name']
                        branchData["ticketURL"] = f"{jira_url}/{branchData['ticketID']}"
                        if ('assignee' in jsondataTicket['fields']) and jsondataTicket['fields']['assignee']:
                            branchData["ticketAssignee"] = jsondataTicket['fields']['assignee']['displayName']

            # get Pullrequest information
            if f'{ref_pkg}:{meta_pr}' in jsondata['values'][i]['metadata']:
                if 'pullRequest' in jsondata['values'][i]['metadata'][f'{ref_pkg}:{meta_pr}']:
                    branchData["prID"] = jsondata['values'][i]['metadata'][f'{ref_pkg}:{meta_pr}']['pullRequest']['id']
                    branchData["prState"] = jsondata['values'][i]['metadata'][f'{ref_pkg}:{meta_pr}']['pullRequest']['state']
                    branchData["targetBranch"] = jsondata['values'][i]['metadata'][f'{ref_pkg}:{meta_pr}']['pullRequest']['toRef']['displayId']
                    branchData["prURL"] = f"{bb_url}/pull-requests/{branchData['prID']}/overview"

            branchInfos.append(branchData)

        if (isLastPage == False):
            nextPageStart = jsondata['nextPageStart']


    # create file in
    print(f"Start writing file {file_name}")
    with open(file_name, "w", encoding="iso-8859-1") as f:

        # create and write header
        csv_header = ['Branch', 'Ahead', 'Behind', 'Last Modified on', 'Last Modified by', 'PR ID', 'PR Status',
                      'Target Branch', 'Ticket ID']

        if addTicketInfo:
            csv_header.extend(['Ticket Status', 'Ticket Assignee'])

        csv_header.extend(['Branch URL', 'PR URL'])

        if addTicketInfo:
            csv_header.extend(['Ticket URL\n'])

        print(";".join(csv_header))
        f.write(';'.join(csv_header))

        # write line by line
        for branch in branchInfos:

            if addTicketInfo:
                f.write(u"{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};{10};{11};{12};{13}\n".format(  branch['name'],
                                                                                                  branch['ahead'],
                                                                                                  branch['behind'],
                                                                                                  branch['lastModifiedDate'],
                                                                                                  branch['lastModifiedBy'],
                                                                                                  branch['prID'],
                                                                                                  branch['prState'],
                                                                                                  branch['targetBranch'],
                                                                                                  branch['ticketID'],
                                                                                                  branch['ticketStatus'],
                                                                                                  branch['ticketAssignee'],
                                                                                                  branch['BranchURL'],
                                                                                                  branch['prURL'],
                                                                                                  branch['ticketURL']
                                                                                                  )
                    )
            else:
                f.write(u"{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};{10}\n".format(   branch['name'],
                                                                                    branch['ahead'],
                                                                                    branch['behind'],
                                                                                    branch['lastModifiedDate'],
                                                                                    branch['lastModifiedBy'],
                                                                                    branch['prID'],
                                                                                    branch['prState'],
                                                                                    branch['targetBranch'],
                                                                                    branch['ticketID'],
                                                                                    branch['BranchURL'],
                                                                                    branch['prURL']
                                                                                    )
                        )

        print("Report generated under: " + os.getcwd() + '/' + file_name)
