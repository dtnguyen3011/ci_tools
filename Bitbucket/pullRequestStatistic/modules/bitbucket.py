#!/usr/bin/env python3
import json
import requests
import time
import logging
from datetime import timedelta
from modules.functions import *

# disable ssl warnings - we're inside the Bosch network, we trust self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class BitBucket:
    BITBUCKET_FETCH_LIMIT = 100  # max number of pages per request

    def __init__(self, url="https://sourcecode01.de.bosch.com/", project="PJDC",
                 repo="pj-dc_int", bb_login=None, bb_password=None):
        def get_bb_url(key):
            return urljoin(url, "rest", key, "1.0", "projects", project, "repos", repo)
        self.__url = get_bb_url("api")
        self.__branch_utils_url = get_bb_url("branch-utils")
        self.__jenkins_utils_url = get_bb_url("jenkins")
        self.__build_status_url = urljoin(url, "rest", "build-status", "1.0", "commits", "stats")
        self.session = requests.session()
        if bb_login and bb_password:
            self.session.auth = (bb_login, bb_password)

    def get_all_branches(self, details=False, order="MODIFICATION"):
        yield from self.__get_all_x("branches", {"details": details, "order": order})

    def get_all_tags(self):
        yield from self.__get_all_x("tags")

    def get_open_pull_requests(self):
        yield from self.__get_all_x("pull-requests")

    def get_all_pull_requests(self, **kwargs):
        if not kwargs:
            params = {"state": "all"}
        else:
            params = kwargs
        yield from self.__get_all_x("pull-requests", params)

    def get_activities_for_pr(self, pr_id):
        yield from self.__get_all_x(urljoin("pull-requests", pr_id, "activities"))

    def __get_all_x(self, key, params=None):
        """
        Getting all items from bitbucket e.g. all pull-requests.
        Parameters:
        :param key: type of elements to get e.g. "pull-requests"
        :param params: parameters to append to the URL as dict e.g."{"state": "all"}"
        """
        page_counter = 0
        if params is None:
            params = {"start": page_counter, "limit": self.BITBUCKET_FETCH_LIMIT}
        else:
            params.update({"start": page_counter, "limit": self.BITBUCKET_FETCH_LIMIT})
        logger.debug("Getting all {} with parameters: {}...".format(key, params))
        req = self.session.get(url_param_join(urljoin(self.__url, key), params))
        if req.status_code == 401:
            raise ConnectionError("Could not get {}. Unauthorized. Check your credentials or .netrc file".format(key))
        else:
            if req.status_code != 200:
                raise ConnectionError("Could not get {}. Status code: {} {}".format(key, req.status_code, req.text))
        while req.status_code == 200:
            br_data = req.json()
            page_counter += br_data["size"]
            logger.debug("Getting elements {} - {} for key {}...".format(page_counter,
                                                                         page_counter + br_data["size"], key))
            for br in br_data["values"]:
                yield br
            if br_data["isLastPage"]:
                break
            params["start"] = page_counter
            req = self.session.get(url_param_join(urljoin(self.__url, key), params))

    def get_an_x_from_repo(self, category, item):
        """
        Getting a specific item from the repository e.g. a specific commit.
        Parameters:
        :param category: type of the item e.g. "commits"
        :param item: the item itself e.g. "73969d640bcd536258e14005915cd65db3b4c440"
        """
        logger.info("Getting {} from category {}...".format(item, category))
        req = self.session.get(urljoin(self.__url, category, item))
        if req.status_code == 200:
            return req.json()
        else:
            if req.status_code == 401:
                raise ConnectionError("Could not get item \"{}\" from {}. Unauthorized. "
                                      "Check your credentials or .netrc file".format(item, category))
            else:
                raise ConnectionError("Could not get item \"{}\" from {}. Status code: {} {}"
                                      .format(item, category, req.status_code, req.text))

    def find_branch(self, branch_name):
        logger.info("Looking for branch {}...".format(branch_name))
        for br in self.get_all_branches():
            if br["displayId"] == branch_name:
                return br
        return None

    def __get_pr_update_date(self, pr_obj):
        """
        :param pr_obj: JSON of pull-request (as returned via API)
        Returns a timestamp of any last activity on pull request.
        """
        logger.debug("Getting pull request update date for PR#{}".format(pr_obj["id"]))
        return max([x["createdDate"] for x in self.get_activities_for_pr(pr_obj["id"])])

    def __get_last_commit_of_pr(self, pr_id):
        """
        Returns hash of the last commit in pull request
        """
        logger.debug("Getting last commit for PR#{}...".format(pr_id))
        return self.get_an_x_from_repo("pull-requests", pr_id)["fromRef"]["latestCommit"]

    def get_latest_commit_of_branch(self, branch):
        logger.debug("Getting latest commit of branch {}".format(branch))
        br = self.find_branch(branch)
        return br["latestCommit"]

    def get_pr_build_status(self, pr_id):
        """
        Returns:
            "success" if all builds for the pull request passed,
            "failed" if a build failed and no builds currently running,
            "inProgress" if any builds are running at the moment,
            "noBuilds" if there were no builds for pull request at all.
        """
        logger.debug("Getting pull request build status for PR#{}...".format(pr_id))
        req = self.session.get(urljoin(self.__build_status_url, self.__get_last_commit_of_pr(pr_id)),
                               headers={'X-Atlassian-Token': 'no-check'})
        resp = req.json()
        if resp["failed"] == 0 and resp["successful"] > 0 and resp["inProgress"] == 0:
            return "success"
        else:
            if resp["failed"] > 0 and resp["inProgress"] == 0:
                return "failed"
            else:
                if resp["inProgress"] > 0:
                    return "inProgress"
                else:
                    return "noBuilds"

    def find_open_prs_older_than(self, days):
        logger.info("Looking for pull requests older than {} days...".format(days))
        for pr in self.get_open_pull_requests():
            pr_age_days = timedelta(milliseconds=(time.time()*1000 - int(self.__get_pr_update_date(pr)))).days
            if pr_age_days > days:
                logger.debug("Pull request #{} is {} days old.".format(pr["id"], pr_age_days))
                yield pr

    def find_prs_updated_within_last_x_days(self, days):
        logger.info("Looking for pull requests updated within {} days...".format(days))
        for pr in self.get_all_pull_requests():
            pr_age_days = timedelta(milliseconds=(time.time()*1000 - int(self.__get_pr_update_date(pr)))).days
            if pr_age_days < days:
                logger.debug("Pull request #{} is {} days old.".format(pr["id"], pr_age_days))
                yield pr
            else:
                break

    def find_branches_older_than(self, days):
        logger.info("Looking for branches older than {} days...".format(days))
        for br in self.get_all_branches():
            cm = self.get_an_x_from_repo("commits", br["latestCommit"])
            cm_age_days = timedelta(milliseconds=(time.time() * 1000 - int(cm["authorTimestamp"]))).days
            logger.debug("Commit {} by {} is {} days old.".format(cm["displayId"], cm["author"]["name"], cm_age_days))
            if cm_age_days > days:
                logger.debug("Last commit #{} of branch {} is {} days old."
                             .format(cm["displayId"], br["displayId"], cm_age_days))
                yield br

    def find_tag(self, commit_id):
        logger.debug("Getting tag for commit ID: {}...".format(commit_id))
        for t in self.get_all_tags():
            if t["latestCommit"] == commit_id:
                return t
        return None

    def delete_branch(self, br_id):
        logger.info("Deleting branch #{}...".format(br_id))
        req = self.session.delete(urljoin(self.__branch_utils_url, "branches"),
                                  headers={"X-Atlassian-Token": "no-check", "Content-Type": "application/json"},
                                  data=json.dumps({"name": br_id, "dryRun": False}))
        if req.status_code == 204:
            logger.info("Branch {} was successfully deleted.".format(br_id))
            return True
        else:
            #raise ConnectionError("Branch {} could not be deleted. Response code: {}".format(br_id, req.status_code))
            logger.warning("Branch {} could not be deleted. Response code: {}".format(br_id, req.status_code))
            return False

    def create_branch(self, branch_name, from_ref="refs/heads/develop"):
        """
        creates a new branch
        :param branch_name: branch name to be created, e.g. delivery/PJDC-12345-sw-delivery-p1903.1.0
        :param from_ref: reference from which to create the new branch e.g. refs/heads/<branchname>, refs/tags/<tagname>
        """
        logger.info("Creating branch {} from branch {}...".format(branch_name, from_ref))
        branch_cmd = {'name': branch_name, 'startPoint': from_ref}
        req = self.session.post(urljoin(self.__branch_utils_url, "branches"),
                                data=json.dumps(branch_cmd),
                                headers={"X-Atlassian-Token": "no-check", "Content-Type": "application/json"})
        if req.status_code != 201:
            raise ConnectionError("Branch {} could not be created from {}. Response code: {} - {}"
                                  .format(branch_name, from_ref, req.status_code, req.text))

    def decline_a_pr(self, pr_id, pr_version):
        logger.info("Declining PR #{} with version {}...".format(pr_id, pr_version))
        req = self.session.post(urljoin(self.__url, "pull-requests", pr_id, "decline") +
                                "?version={}".format(pr_version), headers={'X-Atlassian-Token': 'no-check'})
        if req.status_code == 200:
            logger.info("Pull request #{} was successfully declined.".format(pr_id))
        else:
            raise ConnectionError("Pull request #{} could not be declined. Status code: {} {}"
                                  .format(pr_id, req.status_code, req.text))

    def trigger_build_for_pr(self, pr_id):
        logger.info("Triggering Jenkins builds for PR #{}...".format(pr_id))
        jenkins_trigger_appendix = "triggerJenkins?pr_id={}".format(pr_id)
        req = self.session.post(urljoin(self.__jenkins_utils_url, jenkins_trigger_appendix),
                                headers={'X-Atlassian-Token': 'no-check'})
        if req.status_code == 200:
            logger.info("Triggered builds for pull request #{} successfully".format(pr_id))
        else:
            raise ConnectionError("Could not trigger builds for PR #{}. Status code: {} {}"
                                  .format(pr_id, req.status_code, req.text))

    def get_file_content(self, path, branch_name):
        return "\n".join([x["text"] for x in self.browse(path, branch_name)])

    def browse(self, path, branch_name):
        # TODO: check if this function can be merged with __get_all_x(..)
        # not done yet because __get_all_x(..) yields br_data["value"] and doesn't support path or ?at patameter
        # In addition this function yields either data["children"]["values"] or data["lines"] for directory or
        # file browsing making it incompatible
        page_counter = 0 
        req = self.session.get(urljoin(self.__url, "browse", path) + "?at={}&start={}&limit={}"
                               .format(branch_name, page_counter, self.BITBUCKET_FETCH_LIMIT))
        if req.status_code != 200:
            raise ConnectionError("Status code: {} {}".format(req.status_code, req.text))
        while req.status_code == 200:
            br_data = req.json()
            if "lines" in br_data: # path is a text file
                for line in br_data["lines"]:
                    yield line
                page_counter += br_data["size"]
                if br_data["isLastPage"]:
                    break
            if "children" in br_data: # path is a directory
                for child in br_data["children"]["values"]:
                    yield child
                page_counter += br_data["children"]["size"]
                if br_data["children"]["isLastPage"]:
                    break
            req = self.session.get(urljoin(self.__url, "browse", path) + "?at={}&start={}&limit={}"
                                   .format(branch_name, page_counter, self.BITBUCKET_FETCH_LIMIT))

    def tag_commit(self, tag_name, commit, message=''):
        logger.info("Tagging commit ID {}".format(commit))
        tag_cmd = {'name': tag_name, 'startPoint': commit, 'message': message}
        req = self.session.post(urljoin(self.__url, "tags"),
                                data=json.dumps(tag_cmd),
                                headers={"X-Atlassian-Token": "no-check", "Content-Type": "application/json"})
        if req.status_code != 200:
            raise ConnectionError("Commit ID {} could not be tagged. Response code: {}"
                                  .format(commit, req.status_code))

if __name__ == "__main__":
    bb = BitBucket()
    #for i, old_pr in enumerate(bb.find_branches_older_than(60)):
    #    logger.debug("#{}: {}".format(str(i), old_pr["id"]))
    print(bb.get_file_content("CMakeLists.txt", "develop"))
    for entry in bb.browse("", "develop"):
        print(entry)