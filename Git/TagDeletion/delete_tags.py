#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
#  C O P Y R I G H T
# ------------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
# ------------------------------------------------------------------------------
# Author: Luu Anh Hung (RBVH/EET11)
# Date create: 14th Dec 2020
# Last modify: 22th Dec 2020
# ==============================================================================
import argparse
import http.client
from base64 import b64encode
import json


def parse_args():
    description = "Filtered and delete tags"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--project', '-pj', dest='project', required=True,
                        help='Project in BitBucket')
    parser.add_argument('--repo', '-rp', dest='repo', required=True,
                        help='Repository in BitBucket')
    parser.add_argument('--usernamebb', '-ubb', dest='usernamebb', required=True,
                        help='Username for access BitBucket')
    parser.add_argument('--passwordbb', '-pbb', dest='passwordbb', required=True,
                        help='Password for access BitBucket')
    parser.add_argument('--pretext', '-p', dest='pretext', required=True,
                        help='Pre-text to filter tags')
    parser.add_argument('--dryrun', '-dry', dest='dryrun', action="store_true", required=False, default=False,
                        help='Dry run for delete action (True/False)')
    return parser.parse_args()


def request_api(method, api, basic_auth):
    conn = http.client.HTTPSConnection("sourcecode01.de.bosch.com")
    headers = {'Authorization': 'Basic %s' % basic_auth}
    payload = ''
    conn.request(method, api, payload, headers)

    return conn


def get_filtered_tags(pre_text, project_name, repository_name, basic_auth):
    print('Getting filtered tags from server')

    filtered_tags = []

    start = 0
    limit = 1000
    while True:
        api = "/rest/api/latest/projects/{}/repos/{}/tags?start={}&limit={}"\
            .format(project_name, repository_name, start, limit)
        conn = request_api("GET", api, basic_auth)
        response = conn.getresponse()

        try:
            # Stop if cannot get tags from server
            if response.status != 200:
                print("Cannot get tags from server")
                break

            # Parse response data into json object
            data = json.loads(response.read().decode("utf-8"))

            # Filter for tags base on prefix of display name
            if data["size"] > 0:
                for tag in data["values"]:
                    if tag["displayId"].lower().startswith(pre_text.lower()):
                        filtered_tags.append(tag)
            else:
                break

            # Stop finding if reach the end of list
            if data["isLastPage"]:
                break

            # Increase for next page
            start = start + limit
        finally:
            conn.close()

    return filtered_tags


def delete_tags(filtered_tags, project_name, repository_name, basic_auth, dry_run):
    if len(filtered_tags) == 0:
        print("No filtered tag found.")
        return

    for tag in filtered_tags:
        print("Delete tag: {} - Commit: {}".format(tag["id"], tag["latestCommit"]))

        if dry_run:
            print("===>DRY-RUN: Not delete")
            continue

        api = "/rest/git/1.0/projects/{}/repos/{}/tags/{}"\
            .format(project_name, repository_name, tag["displayId"])
        conn = request_api("DELETE", api, basic_auth)
        response = conn.getresponse()

        try:
            # status code 204 means delete completed
            if response.status != 204:
                data = json.loads(response.read().decode("utf-8"))
                if data["errors"]:
                    for error in data["errors"]:
                        print("===>ERROR: " + error["message"])
        finally:
            conn.close()


def main():
    print('##########################################')
    print('##    Method filter and delete tags     ##')
    print('################  START  #################')
    print('##########################################')

    # prepare arguments
    args = parse_args()
    project_name = args.project
    repository_name = args.repo
    bb_user = args.usernamebb
    bb_pwd = args.passwordbb
    pre_text = args.pretext
    dry_run = args.dryrun

    # Authentication information
    basic_auth = b64encode("{}:{}".format(bb_user, bb_pwd).encode()).decode("ascii")

    # Get id list of filtered tags
    filtered_tags = get_filtered_tags(pre_text, project_name, repository_name, basic_auth)

    # Delete filtered tags
    delete_tags(filtered_tags, project_name, repository_name, basic_auth, dry_run)

    print('##########################################')
    print('#################  END  ##################')
    print('##########################################')


if __name__ == "__main__":
    main()
