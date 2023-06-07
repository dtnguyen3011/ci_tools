import os
import sys
import re
import argparse
from collections import Counter
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import subprocess

class Spacetime(object):
    def __init__(self):
        self.f_years = mdates.YearLocator()  # every year
        self.f_months = mdates.MonthLocator()  # every month
        self.f_years_fmt = mdates.DateFormatter('%Y')
        self.f_day = mdates.DayLocator()

        # Dates for Plots
        self.today = datetime.now()
        self.this_year = self.today.year
        self.last_monday = get_last_mondays()
        self.last_sunday = self.last_monday + timedelta(days=6)
        self.last_last_monday = get_last_mondays(1)
        self.last_last_sunday = self.last_last_monday + timedelta(days=6)

        self.this_year_start = "{}-1-1".format(self.this_year)
        self.this_year_end = "{}-12-31".format(self.this_year)

        self.this_year_start_d = datetime.strptime(self.this_year_start, '%Y-%m-%d')
        self.this_year_end_d = datetime.strptime(self.this_year_end, '%Y-%m-%d')


def get_last_mondays(week=0):
    """
    Get last mondays from current date.
    :param week: Last n Mondays. 0 last Mondays. 1  Monday before last monday. And so on
    :return: Date of last monday beginning at 0 OClock
    """
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday())
    last_monday = last_monday.replace(
        hour=0, minute=0, second=0, microsecond=0)
    if week:
        for _ in range(week):
            last_monday = last_monday - timedelta(days=7)
    return last_monday


def get_git_date_format(date_object):
    """
    Format date to "year-month-day" notation
    :param date_object:
    :return:
    """
    return date_object.strftime("%Y-%m-%d")


def subplot_pr(pos, plot_dates, y_values, title):
    ax = plt.subplot(pos)
    ax.bar(plot_dates, y_values, label=None)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle='--')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(plt.xticks()[1], rotation=30, ha='right')
    plt.ylabel('# merges')
    plt.title(title)

    return ax


def get_pr_from_log(git_dir, start_date, end_date):
    # Retrieve PRs from Log
    
    os.chdir(git_dir)
    stream = os.popen(
        'git log --pretty=format:"%cd|\"%s\"|%an" --before="{}" --after="{}" --merges --date=short-local'.format(end_date,
                                                                                                                 start_date)).readlines()
    merges_to_dev = []

    for line in stream:
        # Get Merges to Development
        regex_results = re.search('(\d+-\d+-\d+)\|(Merge pull request \#.*\ in .*to develop)', line)
        if regex_results:
            merges_to_dev.append(regex_results.group(1))
    if merges_to_dev:
        c_merges_dev = Counter(merges_to_dev)
        d_merges_dev = [datetime.strptime(date, '%Y-%m-%d')
                        for date in c_merges_dev.keys()]
        return d_merges_dev, list(c_merges_dev.values())
    else:
        return None, None


def parse_args():
    description = "Pull Request Statistics generation"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--directory', dest='directory', required=True,
                        help='The location of the git repository that shall be analyzed.')
    parser.add_argument('-o', '--output-location', dest='output_location', required=False,
                        default=os.path.dirname(os.path.abspath(
                            sys.argv[0])) + os.sep + "plot.png",
                        help='The location where the resulting plot shall be stored. Default is the directory of this script.')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    spacetime = Spacetime()
    originalDir = os.getcwd()
    
    # Get Plot Data
    dates_year, n_pr_year = get_pr_from_log(args.directory, spacetime.this_year_start, spacetime.this_year_end)
    dates_this_week, n_pr_this_week = get_pr_from_log(args.directory, spacetime.last_monday, spacetime.last_sunday)
    dates_last_week, n_pr_last_week = get_pr_from_log(args.directory, spacetime.last_last_monday, spacetime.last_last_sunday)

    # Fill dates with zeros if no dates exist
    if not dates_year:
        dates_year = [spacetime.this_year_start_d, spacetime.this_year_end_d]
        n_pr_year = [0, 0]

    if not dates_this_week:
        dates_this_week = [spacetime.last_monday, spacetime.last_sunday]  # this mondays
        n_pr_this_week = [0, 0]
    else:
        # Fill up
        weekdays = [dates.weekday() for dates in dates_this_week]
        for i in range(7):
            if i not in weekdays:
                dates_this_week.append(spacetime.last_monday + timedelta(days=i))
                n_pr_this_week.append(0)

    if not dates_last_week:
        dates_last_week = [spacetime.last_last_monday, spacetime.last_last_sunday]  # this mondays
        n_pr_last_week = [0, 0]
    else:
        # Fill up
        weekdays = [dates.weekday() for dates in dates_last_week]
        for i in range(7):
            if i not in weekdays:
                dates_last_week.append(spacetime.last_last_monday + timedelta(days=i))
                n_pr_last_week.append(0)

    # Plot it !
    fig = plt.figure()
    subplot_pr(211, dates_year, n_pr_year, "PR merges to dev")
    subplot_pr(223, dates_last_week, n_pr_last_week, "Last week")
    subplot_pr(224, dates_this_week, n_pr_this_week, "This week")

    # Format subplots
    plt.subplots_adjust(hspace=0.8, wspace=0.4, bottom=0.2)  # format subplots

    os.chdir(originalDir)
    fig.savefig(args.output_location)
