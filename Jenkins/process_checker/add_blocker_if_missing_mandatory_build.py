#!/usr/bin/env python3
""" Script to add a failure build in bitbucket commit metadata to block PR if missing mandatory build for given commit
"""
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import json
import argparse


def parse_args() -> argparse.Namespace:
    """Adds and parses command line arguments

    Returns:
      argparse.Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True, type=str, help='System user username')
    parser.add_argument('-p', '--password', required=True, type=str, help='System user password')
    parser.add_argument('-c', '--commit-id', required=True, type=str, help='Commit id')
    parser.add_argument('-i', '--pr-id', required=True, type=str, help='Pull Request ID')
    parser.add_argument('--renew', action='store_true', default=False, help='Renew build status by succesful build')
    parser.add_argument('--debug', action='store_true', default=False, help='Enable debugging mode')

    return parser.parse_args()


def main(args: argparse.Namespace) -> None:
    logging.info("add_blocker_if_missing_mandatory_build()")

    bb_url = "https://sourcecode01.de.bosch.com"
    session = requests.Session()
    session.auth = args.user, args.password
    retries = Retry(total=3,
                    backoff_factor=5,
                    allowed_methods=["GET", "POST"],
                    status_forcelist=[400, 401])
    session.mount(bb_url, HTTPAdapter(max_retries=retries))
    bb_rest_api_url = f"{bb_url}/rest/build-status/1.0/commits/{args.commit_id}"
    if args.renew:
        json_data = {
            "state": "SUCCESSFUL",
            "key": "Check_Full_Build_Triggered",
            "name": "Trigger_Full_Build is successful in the latest commit!",
            "url": "https://inside-docupedia.bosch.com/confluence/x/_i8yiQ",
            "description": "Trigger_Full_Build job have been executed for this commit. All the related jobs would be triggered."
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        with session.post(bb_rest_api_url, data=json.dumps(json_data), headers=headers) as response:
            response.raise_for_status()
    else:
        isSuccess = False
        with session.get(bb_rest_api_url) as response:
            response.raise_for_status()
            for build in response.json()["values"]:
                if "Trigger_Full_Build" in build["name"] and build["state"] == "SUCCESSFUL":
                    isSuccess = True
                    break

        if not isSuccess:
            json_data = {
                "state": "FAILED",
                "key": "Check_Full_Build_Triggered",
                "name": "Trigger_Full_Build must be successful in the latest commit before this PR can be merged!",
                "url": f"https://rb-artifactory.bosch.com/artifactory/cc-da-radar-vwag-e3-release-local/VAG/Cx_Pipeline/Process_Checker/Is_your_PR_ready_to_merge.html?pr={args.pr_id}",
                "description": "Trigger_Full_Build build is required for the head commit of this PR. Please trigger it for complete the verification process of your PR"
            }

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            with session.post(bb_rest_api_url, data=json.dumps(json_data), headers=headers) as response:
                response.raise_for_status()

    logging.info("~add_blocker_if_missing_mandatory_build()")


if __name__ == '__main__':
    args = parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    main(args)
