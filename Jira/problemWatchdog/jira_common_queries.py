#!/usr/bin/python3

## ---------------------------------------------------------------------------------------


def and_jql(jql_list: list) -> list:
    return ' AND '.join(jql_list)

def or_jql(jql_list: list) -> list:
    return ' OR '.join(jql_list)

def jql_cmp(s1: str, s2: str) -> bool:
    return s1.replace(' ', '') == s2.replace(' ', '')

## ---------------------------------------------------------------------------------------

class CommonJql:
    """
    Query to get all program features of given PI, for Watchdog
    PI string needs to be given via .format()
    """
    jql_business_benefits = (
        ' project = {} AND type = "Program Feature" AND fixVersion = {}'
        ' AND resolution in (Unresolved, Resolved, Incomplete)'
        ' AND (status = "In Progress" OR status = Closed)'
    )

    """
    Query open problems for Problem Watchdog 
    """
    jql_all_open_problems = (
        ' project = {} AND issuetype in (Problem)'
        ' AND status != Closed'
    )

    """
    Query closed problems for Problem Watchdog 
    """
    jql_all_resolved_problems = (
        ' project = {} AND issuetype in (Problem)'
        ' AND status = Closed AND resolution in (Resolved)'
    )

    """
    Query all problems for Problem Watchdog, irregardless of status
    """
    jql_all_problems = (
        ' project = {} AND issuetype in (Problem)'
    )

    """
    Query all defects for the System Release Notes
    """
    jql_all_defects = (
        jql_all_problems +
        ' AND "Problem Type" = Defect AND Severity in (Strong, Medium)'
    )

    """
    Generally a good way to order by severity and priority
    """
    jql_order = (
        ' ORDER BY Severity, priority DESC'
    )