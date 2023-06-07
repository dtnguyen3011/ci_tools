#!/usr/bin/env python3
import json
import requests
import logging
from modules.functions import *

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class BitBucketProject:
    BITBUCKET_FETCH_LIMIT = 100  # max number of pages per request

    def __init__(self, project, url="https://sourcecode01.de.bosch.com/",
                 bb_login=None, bb_password=None):
        self.__request_url = urljoin(url, "rest", "api", "1.0", "projects", project, "repos")
        self.session = requests.session()
        if bb_login and bb_password:
            self.session.auth = (bb_login, bb_password)

    def get_all_repos(self):
        page_start = 0
        params = {"start": page_start, "limit": self.BITBUCKET_FETCH_LIMIT}
        logger.debug("Getting all repositories with parameters: {}...".format(params))
        resp = self.session.get(url_param_join(self.__request_url, params))
        if resp.status_code == 401:
            raise ConnectionError("Could not get list of repositories. Unauthorized. Check your credentials or .netrc file")
        else:
            if resp.status_code != 200:
                raise ConnectionError("Could not get list of repositories. Status code: {} {}".format(resp.status_code, resp.text))
        while resp.status_code == 200:
            page = resp.json()
            page_start += page["size"]
            logger.debug("Getting repositories {} - {}...".format(page_start,
                                                                  page_start + page["size"]))
            for item in page["values"]:
                yield item["slug"]
            if page["isLastPage"]:
                break
            params["start"] = page_start
            resp = self.session.get(url_param_join(self.__request_url, params))
