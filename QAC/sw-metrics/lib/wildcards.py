""" Wildcard is a library for helping you match regex stuff. """
import re

def matches_wildcard_pattern(string, wildcard_expression):
    """
    Method for checking if string matches a unix-like wildcard
    expression.
    """
    string = string.replace('\\', '/')

    regex_pattern = wildcard_expression.replace('.', '\\.')
    regex_pattern = regex_pattern.replace("/", '\\/')
    regex_pattern = regex_pattern.replace('*', '[^\\/]*')
    regex_pattern = regex_pattern.replace('[^\\/]*[^\\/]*', '.*')
    regex = re.compile(regex_pattern)
    match = re.match(regex, string)

    return match and match.group(0) == string
