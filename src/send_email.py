#!/usr/bin/env python3.7

import smtplib
import sys
from email.mime.text import MIMEText

# Declare SMTP server. Refer below artical for more detail. 
# https://inside-docupedia.bosch.com/confluence/display/CCT/ContinuousIntegrationDevelopmentIssues
host = "rb-smtp-int.bosch.com"
port = 25

def send_email(sender, receiver, subject, message, html_email=False, cc=None, bcc=None):
    """A generic function to send emails.

    Args:
        sender (str): same as email "from"
        receiver (list): list of strings with email addresses, same as email "to"
        subject (str): subject of email
        message (str): message string, may contain html tags
        html_email (bool): per default send as plain text email, send html email if true
        cc (list): list of email addresses
        bcc (list): list of email addresses

    Returns:
        Nothing
    """
    msg = MIMEText(message, ('html' if html_email else 'plain'))
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(receiver)
    if(cc is not None): msg['CC'] = ", ".join(cc)
    if(bcc is not None): msg['BCC'] = ", ".join(bcc)
    smtp = smtplib.SMTP(host, port)
    smtp.send_message(msg)
    smtp.quit()
