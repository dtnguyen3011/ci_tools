#!/usr/bin/python3

## ---------------------------------------------------------------------------------------

def fields_str(ticket, more_text=""):
    return('{}: assignee={} reporter={} | {}'.format(ticket.key, ticket.fields.assignee, ticket.fields.reporter, more_text))

## ---------------------------------------------------------------------------------------

def get_mail_from_ticket(ticket):
    emails = []
    uids = []
    f = ticket.fields
    if(f.assignee is not None): 
        emails.append(f.assignee.emailAddress)
        uids.append(f.assignee.key)
    if(f.reporter is not None): 
        emails.append(f.reporter.emailAddress)
        uids.append(f.reporter.key)
    return emails, uids

## ---------------------------------------------------------------------------------------

def get_versions(ticket):
    f = ticket.fields
    ret = {}
    ret['aff'] = [x.name for x in f.versions]
    ret['fix'] = [x.name for x in f.fixVersions]
    return(ret)
## ---------------------------------------------------------------------------------------
