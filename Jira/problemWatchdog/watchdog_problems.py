#!/usr/bin/python3
# ==============================================================================
#  C O P Y R I G H T
# ------------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
# ==============================================================================
#
# Description:
# 	This script provides helpers to find problem tickets, which
#   are not filled correctly, or need attantion by involved people.
#   For each finding, emails will be sent.
#
#   Among others, the script implements the following checks.
#
# CHECKS: find problem where the origin is not set->      ask to set it!
# CHECKS: find problem which have no description           ->      ask to add description for the ticket!
# CHECKS: find problem which have no priority        ->      ask to set it!
# CHECKS: find analyzed problems without link                  ->      ask to create, estimate, and link a story!
# CHECKS: find analyzed problems without component                  ->      ask to assign ticket to a component!
# CHECKS: find problems that had no activity since 4 months      ->      ask to update or close!
# CHECKS: find problems that have no problem type          ->      ask to set it!
# CHECKS: find problems without assignee                       ->      ask to assign the ticket to the right person!
# CHECKS: find problems where the affected version is wrong    ->      ask to correct it!
# CHECKS: find closed problem without fix versions      ->      need to fix it!
# CHECKS: find problems which have no severity          ->      ask to specify the severity !

import logging
import sys
import os
import argparse
from JiraWrapper import JiraWrapper
from problemTicket import ProblemTicket
from jira_common_queries import *
from jira_watchdog_utils import *
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from src.send_email import send_email


# ---------------------------------------------------------------------------------------

SUBJECT = "[{project}] Missing required information in your submitted ticket {id}"

TEMPLATE = """
<p>Hello!!!</p>

<p><b>Please take a look at the problem ticket {id}:</b><br>
   <i>{title}</i><br><br>
{url}</p>

<p><b>The reason why you get this email:</b><br>
{reason}</p>

<p>
Check out the detailed <a href={problem_management_link}>{project} Problem Management plan</a>.
</p>

<p>Thank you for your cooperation!</p>

<p>Your Problem ticket watchdog<br>... brought to you by {signature}</p>
"""

TEMPLATE_MD = """
Hi {recipient},

Please check this problem ticket with the detail as below
{reason}

Check out the detailed [{project} Problem Management plan|{problem_management_link}]

Thank you for your cooperation!
Your Problem ticket watchdog...
... brought to you by {signature}
"""

# ---------------------------------------------------------------------------------------

def operate_problems(jql, subject, reason):
    logging.info("-"*100)
    logging.info("Query: {}".format(jql))
    li = jira.search_issues(jql)

    logging.info("Issues: {}".format(len(li)))
    logging.info("Subject: {}".format(subject))

    for i in li:
        logging.info(fields_str(i, get_versions(i)))
        matchedTickets.append(ProblemTicket(i, subject, reason))


def notify(tickets, email=False, add_comment=False):
    for ticket in tickets:
        if email:
            recipient_email , recipient_id = get_mail_from_ticket(ticket.ticket)
            values = {'id': ticket.ticket.key, 'url': JiraWrapper.TICKET_URL +
                        ticket.ticket.key, 'reason': ticket.reason, 'title': ticket.ticket.fields.summary, 'problem_management_link': doculink, 'project': ticket.ticket.fields.project.key, 'signature': signature}
            msg = TEMPLATE.format(**values)
            subject = SUBJECT.format(
                project=ticket.ticket.fields.project.key, id=ticket.ticket.key)
            logging.info(f'Send reminder email to {recipient_email}')
            send_email("XC-DA RADAR Continuous X <xcdaradarcontinuousx@bosch.com>",
                        recipient_email, subject, msg, html_email=True)

        if add_comment:
            recipient_email , recipient_id = get_mail_from_ticket(ticket.ticket)
            comment = TEMPLATE_MD.format(recipient=' '.join([f"[~{id}]" for id in recipient_id]),
                                        reason=ticket.reason.replace(r"<br>",r' \\'),
                                        project=ticket.ticket.fields.project.key,
                                        problem_management_link=doculink,
                                        signature=signature)
            logging.info(f'Add reminder comment in ticket {ticket.ticket.key}')
            jira.add_comment(ticket.ticket.key, comment)

# This function to merge duplicate ticket which have the same ticket's key but different type and reason.
def mergeDuplicateElements(tickets):
    sortedlist = sorted(tickets, key=lambda ticket: ticket.ticket.key)
    i = 0
    while i < len(sortedlist)-1:
        if sortedlist[i].ticket.key == sortedlist[i+1].ticket.key:
            sortedlist[i] = sortedlist[i] + sortedlist[i+1]
            sortedlist.remove(sortedlist[i+1])
        else:
            i += 1
    return sortedlist
# ---------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Define param
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", "-pj", required=True,
                        help="Project name. E.g: PJRV, PJDC, PJVWMQB")
    parser.add_argument("--user", "-u", required=False,
                        help="User name, .netrc file will be used if not specify")
    parser.add_argument("--password", "-p", required=False,
                        help="Password, .netrc file will be used if not specify")
    parser.add_argument("--docupedia", "-doc", required=False,
                        help="Docupedia link of project problem management")
    parser.add_argument("--signature", "-sign", required=False,
                        help="Let receiver know who remind them")
    parser.add_argument("--addcomment", "-c",
                        help="Notify to ticket author via email",
                        default=False, action="store_true")
    parser.add_argument("--sendemail", "-e",
                        help="Add comment in jira problem ticket",
                        default=False, action="store_true")
    args = parser.parse_args()

    # Define logger
    logging.basicConfig(filename='{}_Problem_watchdog.txt'.format(args.project),
                        format='%(asctime)s [%(levelname)s]      %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

    jira = JiraWrapper(basic_auth=(args.user, args.password)) if (args.user and args.password) else JiraWrapper()

    doculink = args.docupedia
    signature = args.signature

    # logging information
    logging.info(f"Project: {args.project}")
    logging.info(f"Notify via email: {args.sendemail}")
    logging.info(f"Add comment in problem ticket: {args.addcomment}")

    matchedTickets = []
    # ------------------------START CHECK----------------------------------------------------
    if args.project in ["VWMRRMEBVOLUMEN", "VAGAPL", "AURFPREM", "FRVVWMQB"]:
        # CHECKS: find problem where the origin is not set->      ask to set it!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "Origin  is EMPTY", "affectedVersion not in (ASPICE,Tools)"]),
            "Problem's origin is missing",
            "The origin value needs to be specified!<br>Please choose 'Project Internal', 'Project External', or 'Customer'."
        )

        # CHECKS: find problem which have no description           ->      ask to add description for the ticket!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "description  is EMPTY", "affectedVersion not in (ASPICE,Tools)"]),
            "Problem's description is missing",
            "The description needs to be added!<br>Please choose add an description for ticket"
        )

        # CHECKS: find problem which have no priority        ->      ask to set it!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "priority = None", "affectedVersion not in (ASPICE,Tools)"]),
            " Problem's priority is missing",
            "The problem's priority needs to be set!<br>Please choose 'high','Low' or 'Medium'. 'None' is not OK"
        )

        # CHECKS: find analyzed problems without link                  ->      ask to create, estimate, and link a story!
        operate_problems(
            and_jql([CommonJql.jql_all_problems.format(args.project),
                    "status = Analyzed", "issueFunction NOT IN hasLinks()", "affectedVersion not in (ASPICE,Tools)"]),
            "Analyzed Problem without link",
            "This problem ticket is analyzed, but there is no link to a following task, which would resolve this problem.<br>It is a good practice to create, estimate, and link a story or bugfix with this problem."
        )

        # CHECKS: find analyzed problems without component                  ->      ask to assign ticket to a component!
        operate_problems(
            and_jql([CommonJql.jql_all_problems.format(args.project),
                    "status = Analyzed", "component is EMPTY", "affectedVersion not in (ASPICE,Tools)"]),
            "Analyzed Problem without component",
            "This problem ticket is analyzed, but there is no component mentioned. <br> Please assign the problem ticket to a specific component."
        )

        # CHECKS: find problems that had no activity since 4 months      ->      ask to update or close!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "updated < startOfMonth(-4)", "affectedVersion not in (ASPICE,Tools)"]),
            "Outdated Ticket",
            "Last update to this ticket was more than four months ago!<br>Please update or close!"
        )

        # CHECKS: find problems that have no problem type          ->      ask to set the problem type
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "'Problem Type' is EMPTY", "affectedVersion not in (ASPICE,Tools)"]),
            "Missing problem Type",
            "The field 'Problem Type' is not specified.<br>Please set to 'Defect', 'Performance Issue', or 'Other'."
        )

        # CHECKS: find problems without assignee                       ->      ask to assign the ticket to the right person!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "assignee is EMPTY", "affectedVersion not in (ASPICE,Tools)"]),
            "Problem is not assigned",
            "This problem ticket is not closed and does not have an assignee.<br>Please make sure to assign it to someone from the project."
        )

        # CHECKS: find problems where the affected version is missing or wrong    ->      ask to correct it!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "affectedVersion is EMPTY"]),
            "Problem's affects Version is missing",
            "The value of 'Affects Version/s' needs to be set to the release version ID in which the problem was found !<br>Please make sure to use the right syntax."
        )

        # CHECKS: find closed problem without fix versions      ->      need to fix it!
        operate_problems(
            # NOTE: only taking defects from beginning of this year (i.e. 2019)
            and_jql([CommonJql.jql_all_resolved_problems.format(args.project),
                    "fixVersion is EMPTY", "resolutiondate > startOfYear()", "affectedVersion not in (ASPICE,Tools)"]),
            "Closed problem without fix versions",
            "This is a resolved problem, therefore the values of 'Fix Version/s' needs to be set correctly!<br>Please make sure to use the right syntax.",
        )

        # CHECKS: find problems which don't have a severity            ->      ask to specify the severity
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(args.project),
                    " Severity is EMPTY", "affectedVersion not in (ASPICE,Tools)"]),
            "Missing problem's severity",
            "The 'Severity' of problem ticket needs to be specified!<br>Please choose 'Minor', 'Medium', or 'Strong'."
        )
    else:
        # CHECKS: find problem where the origin is not set->      ask to set it!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "Origin  is EMPTY"]),
            "Problem's origin is missing",
            "The origin value needs to be specified!<br>Please choose 'Project Internal', 'Project External', or 'Customer'."
        )

        # CHECKS: find problem which have no description           ->      ask to add description for the ticket!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "description  is EMPTY"]),
            "Problem's description is missing",
            "The description needs to be added!<br>Please choose add an description for ticket"
        )

        # CHECKS: find problem which have no priority        ->      ask to set it!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "priority = None"]),
            " Problem's priority is missing",
            "The problem's priority needs to be set!<br>Please choose 'high','Low' or 'Medium'. 'None' is not OK"
        )

        # CHECKS: find analyzed problems without link                  ->      ask to create, estimate, and link a story!
        operate_problems(
            and_jql([CommonJql.jql_all_problems.format(args.project),
                    "status = Analyzed", "issueFunction NOT IN hasLinks()"]),
            "Analyzed Problem without link",
            "This problem ticket is analyzed, but there is no link to a following task, which would resolve this problem.<br>It is a good practice to create, estimate, and link a story or bugfix with this problem."
        )

        # CHECKS: find analyzed problems without component                  ->      ask to assign ticket to a component!
        operate_problems(
            and_jql([CommonJql.jql_all_problems.format(args.project),
                    "status = Analyzed", "component is EMPTY"]),
            "Analyzed Problem without component",
            "This problem ticket is analyzed, but there is no component mentioned. <br> Please assign the problem ticket to a specific component."
        )

        # CHECKS: find problems that had no activity since 4 months      ->      ask to update or close!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "updated < startOfMonth(-4)"]),
            "Outdated Ticket",
            "Last update to this ticket was more than four months ago!<br>Please update or close!"
        )

        # CHECKS: find problems that have no problem type          ->      ask to set the problem type
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "'Problem Type' is EMPTY"]),
            "Missing problem Type",
            "The field 'Problem Type' is not specified.<br>Please set to 'Defect', 'Performance Issue', or 'Other'."
        )

        # CHECKS: find problems without assignee                       ->      ask to assign the ticket to the right person!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "assignee is EMPTY"]),
            "Problem is not assigned",
            "This problem ticket is not closed and does not have an assignee.<br>Please make sure to assign it to someone from the project."
        )

        # CHECKS: find problems where the affected version is missing or wrong    ->      ask to correct it!
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(
                args.project), "affectedVersion is EMPTY"]),
            "Problem's affects Version is missing",
            "The value of 'Affects Version/s' needs to be set to the release version ID in which the problem was found !<br>Please make sure to use the right syntax."
        )

        # CHECKS: find closed problem without fix versions      ->      need to fix it!
        operate_problems(
            # NOTE: only taking defects from beginning of this year (i.e. 2019)
            and_jql([CommonJql.jql_all_resolved_problems.format(args.project),
                    "fixVersion is EMPTY", "resolutiondate > startOfYear()"]),
            "Closed problem without fix versions",
            "This is a resolved problem, therefore the values of 'Fix Version/s' needs to be set correctly!<br>Please make sure to use the right syntax.",
        )

        # CHECKS: find problems which don't have a severity            ->      ask to specify the severity
        operate_problems(
            and_jql([CommonJql.jql_all_open_problems.format(args.project),
                    " Severity is EMPTY"]),
            "Missing problem's severity",
            "The 'Severity' of problem ticket needs to be specified!<br>Please choose 'Minor', 'Medium', or 'Strong'."
        )
    # ------------------------------------END CHECK------------------------------------------
    matchedTicketList = mergeDuplicateElements(matchedTickets)
    # Send email to notify.
    notify(matchedTicketList, args.sendemail, args.addcomment)
# ------------------------------------------------------------------------------------------
