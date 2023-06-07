#!/usr/bin/env python3
""" Script to get current software fix version from Commonrepo repository
"""
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import argparse


def parse_args() -> argparse.Namespace:
    """Adds and parses command line arguments

    Returns:
      argparse.Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True, type=str, help='System user username')
    parser.add_argument('-p', '--password', required=True, type=str, help='System user password')
    parser.add_argument('--debug', action='store_true', default=False, dest='debug', help='Enable debugging mode')

    return parser.parse_args()


"""
  * Function to get current software fix version from in repository with the given tag pattern
  *
  * @param project Project key
  * @param repo Repo name
  * @param pattern tag pattern for software fix version
  * @param credentialsId Credential to access Bitbucket
  * @return current software fixversion
"""


def main(args: argparse.Namespace) -> None:
    logging.debug("get_current_allow_swf_pattern()")

    bb_url = "https://sourcecode01.de.bosch.com"    
    project_key = "VWAG_E3"
    repository_slug = "commonrepo"
    pattern = "SWF_"
    current_swf = 0
    adapted_pattern = ""
    current_swf_tag = ""
    session = requests.Session()
    session.auth = args.user, args.password
    retries = Retry(total=3,
                    backoff_factor=5,
                    allowed_methods=["GET"],
                    status_forcelist=[400, 401, 404])
    session.mount(bb_url, HTTPAdapter(max_retries=retries))
    bb_rest_api_url = f"{bb_url}/rest/api/latest/projects/{project_key}/repos/{repository_slug}/tags?filterText={pattern}&orderBy=MODIFICATION"

    with session.get(bb_rest_api_url) as response:
        response.raise_for_status()
        logging.debug(f"Rest api response: {response.json()}")
        current_swf_tag = response.json()["values"][0]["displayId"]
        logging.debug(f"Current SWF tag: {current_swf_tag}")
        current_swf = int(current_swf_tag.split("_")[1])
        integral = int(current_swf / 10)
        remainder = int(current_swf % 10)
        adapted_pattern = f"([0-9a-zA-Z]|)({integral}[{remainder + 1}-9]|{integral +1}0)_SW"
        print(adapted_pattern)

    logging.debug("~get_current_allow_swf_pattern()")


if __name__ == '__main__':
    args = parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    main(args)
