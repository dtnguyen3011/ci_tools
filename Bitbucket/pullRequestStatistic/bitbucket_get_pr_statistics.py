import argparse
from datetime import datetime
from math import ceil
from modules.bitbucket import *
from modules.bitbucketproject import *
from modules.influx import *
from modules.functions import *
from time import time

logging.basicConfig(
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ACTIVITIES_TO_CHECK = ["OPENED", "MERGED", "DECLINED", "REOPENED"]
DAY_IN_NS = 86400000000000
MEASUREMENT_ACTIVITIES = "pull_requests_activities"
MEASUREMENT_OPEN = "pull_requests_open"


def add_data_about_prs_updated_within_x_days_to_influxdb(bitbucket, project, repo, days):
    """
    :param days: amount of days to be checked. 0 or None for all.
    :return: None
    """
    if not days:
        updated_prs = bitbucket.get_all_pull_requests()
    else:
        updated_prs = list(bitbucket.find_prs_updated_within_last_x_days(days))
    for pr in updated_prs:
        logger.info("#{}: {}".format(pr["id"], pr["title"]))
        get_and_push_pr_data(bitbucket, project, repo, pr)


def push_pr_data(project, repo, pr_id, action, timestamp):
    x = datetime.fromtimestamp(timestamp / 1e3)
    PI_number = ceil(int(x.strftime("%m"))/2)
    tags = {
        "project": project,
        "repository": repo,
        "half_quarter": "{}-{}: {}".format(x.strftime("%Y"), PI_number, get_period_by_halfquartal(PI_number)),
        "week": "{}-{}".format(x.strftime("%Y"), x.strftime("%W")),
        "month": "{}-{}".format(x.strftime("%Y"), x.strftime("%m")),
        "action": action
    }
    fields = {
        "pr_id": pr_id
    }
    logger.info("{}/{}: PR #{} was {} on Half-quarter #{}. Week #{}, Month #{}".format(project,
                                                                                       repo,
                                                                                       pr_id,
                                                                                       tags["action"],
                                                                                       tags["half_quarter"],
                                                                                       tags["week"],
                                                                                       tags["month"]))
    influx.push_data(influx_compile_push_request_body(MEASUREMENT_ACTIVITIES, tags, fields,
                                                      timestamp_in_ms_to_ns(timestamp) + int(pr_id)))


def get_and_push_pr_data(bitbucket, project, repo, pr_obj):
    for activity in bitbucket.get_activities_for_pr(pr_obj["id"]):
        if activity["action"] in ACTIVITIES_TO_CHECK:
            push_pr_data(project, repo, pr_obj["id"], activity["action"], int(
                activity["createdDate"]))


def distinct_by_action(project, repo, action, time='now()'):
    query = (
        "SELECT DISTINCT(pr_id) FROM {}"
        " WHERE project = '{}'"
        " AND repository = '{}'"
        " AND action = '{}'"
        " AND time <= {}".format(MEASUREMENT_ACTIVITIES, project, repo, action, time))
    logger.info(f"Distinct by action query: {query}")
    return {x['distinct'] for x in influx.influx_connection.query(query).get_points()}


def count_activities_by_action(project, repo, action, time='now()'):
    query = (
        "SELECT COUNT(pr_id) FROM {}"
        " WHERE project = '{}'"
        " AND repository = '{}'"
        " AND action = '{}'"
        " AND time <= {}"
        " GROUP BY action".format(MEASUREMENT_ACTIVITIES, project, repo, action, time))
    result = list(influx.influx_connection.query(query))
    logger.info(f"Count activities by action query: {query}")
    if len(result) == 0:
        return 0
    else:
        return int(result[0][0]["count"])


def check_for_deleted(bitbucket, project, repo):
    logger.info("Checking for deleted PRs")
    all_prs = distinct_by_action(project, repo, 'OPENED')
    merged = distinct_by_action(project, repo, 'MERGED')
    deleted = distinct_by_action(project, repo, 'DELETED')
    opened_prs = set()

    logger.info(f"all_prs {all_prs}")
    logger.info(f"merged {merged}")
    logger.info(f"deleted {deleted}")

    for pr in all_prs.difference(merged).difference(deleted):
        logger.info(f"pr {pr}")
        query = (
            "SELECT LAST(pr_id), action FROM {}"
            " WHERE project = '{}'"
            " AND repository = '{}'"
            " AND pr_id = {}".format(MEASUREMENT_ACTIVITIES, project, repo, pr))
        status = list(influx.influx_connection.query(query))
        logger.info(f"status {status}")
        if status[0][0]['action'] == 'OPENED' or status[0][0]['action'] == 'REOPENED':
            opened_prs.add(pr)

    actually_opened = [x['id'] for x in bitbucket.get_open_pull_requests()]
    logger.info(f"actually_opened {actually_opened}")

    for pr in opened_prs.difference(actually_opened):
        logger.info(f"pr1 {pr}")
        try:
            bitbucket.get_an_x_from_repo("pull-requests", pr)
        except ConnectionError:
            push_pr_data(project, repo, pr, "DELETED", time() * 1000)
        else:
            get_and_push_pr_data(bitbucket, project, repo, {"id": pr})


def count_open_prs_by_day(project, repo, measurements, days_from_now=0):
    tags = {
        "project": project,
        "repository": repo
    }
    end_day_ms = influx.get_newest_entry_day([measurements], tags) * 1000
    logger.info(f"end_day_ms {end_day_ms}")
    # If there are no entries at all, then we do not write anything into the measurement.
    if end_day_ms is None:
        return
    end_day = timestamp_in_ms_to_ns(end_day_ms)
    if days_from_now == 0:
        start_day = timestamp_in_ms_to_ns(
            influx.get_oldest_entry_day([measurements], tags))
    else:
        time_shift = days_from_now * DAY_IN_NS
        start_day = end_day - time_shift
    logger.info("Counting open pull requests by days...")
    logger.info("Start day is {}; end day is {}...".format(start_day, end_day))
    current_day = start_day
    while current_day <= end_day:
        open_prs = count_activities_by_action(project, repo, 'OPENED', current_day)\
            + count_activities_by_action(project, repo, 'REOPENED', current_day)\
            - count_activities_by_action(project, repo, 'MERGED', current_day) \
            - count_activities_by_action(project, repo, 'DECLINED', current_day)\
            - count_activities_by_action(project, repo, 'DELETED', current_day)
            
        fields = {
            "open_prs": open_prs
        }
        logger.info("There were {} open pull requests on {}".format(
            open_prs, current_day))
        influx.push_data(influx_compile_push_request_body(MEASUREMENT_OPEN, tags, fields,
                                                          current_day))
        current_day += DAY_IN_NS


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--bbuser", "-bu", help="Username to log in to bitbucket as."
                        " If not specified, .netrc data is used",
                        required=False)
    parser.add_argument("--bbpassw", "-bp", help="Password to log in to bitbucket with."
                        " If not specified, .netrc data is used.",
                        required=False)
    parser.add_argument("--days", "-d", help="Look for info about PRs updated within the specified number of days.",
                        required=True, type=int)
    parser.add_argument("--inuser", "-inu", help="Username to log in to InfluxDB as.",
                        required=False)
    parser.add_argument("--inpassw", "-inpw", help="Password to log in to InfluxDB with.",
                        required=False)
    parser.add_argument("--insrv", "-ins", help="InfluxDB server address.",
                        required=True)
    parser.add_argument("--inport", "-inp", help="InfluxDB server port.",
                        required=True)
    parser.add_argument("--indb", "-idb", help="InfluxDB database to use.",
                        required=True)
    parser.add_argument("--project", "-p", help="Bitbucket project id.",
                        required=True)
    parser.add_argument("--repo", "-r", help="Repositories to look into."
                        " If none is specified, all repositories of the project will be examined",
                        nargs='*')
    parser.add_argument("--all-data", "-ad", action="store_true", default=False, dest='get_all_data',
                        help='Getting all data from bitbucket (-d is ignored).')
    args = parser.parse_args()
    if args.repo:
        repos = args.repo
    else:
        bitbucketproject = BitBucketProject(
            bb_login=args.bbuser, bb_password=args.bbpassw, project=args.project)
        repos = bitbucketproject.get_all_repos()

    influx = Influx(args.insrv, args.inport,
                    args.inuser, args.inpassw, args.indb)
    for repo in repos:
        logger.info(
            "Sending PR statistics for {}/{}...".format(args.project, repo))
        bitbucket = BitBucket(
            bb_login=args.bbuser, bb_password=args.bbpassw, project=args.project, repo=repo)

        if args.get_all_data:
            add_data_about_prs_updated_within_x_days_to_influxdb(
                bitbucket, args.project, repo, days=0)
            check_for_deleted(bitbucket, args.project, repo)
            count_open_prs_by_day(args.project, repo, MEASUREMENT_ACTIVITIES)
        else:
            add_data_about_prs_updated_within_x_days_to_influxdb(
                bitbucket, args.project, repo, days=args.days)
            check_for_deleted(bitbucket, args.project, repo)
            count_open_prs_by_day(args.project, repo,
                                  MEASUREMENT_ACTIVITIES, args.days)
