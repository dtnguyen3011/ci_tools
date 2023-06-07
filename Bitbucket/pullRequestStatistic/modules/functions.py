import calendar
from datetime import datetime
import re
from urllib.parse import unquote, urlparse, parse_qsl, urlencode, ParseResult


def urljoin(*args):
    return "/".join([str(x).rstrip('/') for x in args])


def url_param_join(url, params):
    url = unquote(url)
    parsed_url = urlparse(url)
    get_args = parsed_url.query
    parsed_get_args = dict(parse_qsl(get_args))
    parsed_get_args.update(params)
    encoded_get_args = urlencode(parsed_get_args, doseq=True)
    return ParseResult(
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, encoded_get_args, parsed_url.fragment
    ).geturl()


def get_day_start_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000


def timestamp_in_ms_to_ns(timestamp_in_milliseconds):
    return int(timestamp_in_milliseconds * 1000 * 1000)


def get_period_by_halfquartal(halfquartal):
    return "{} - {}".format(calendar.month_abbr[halfquartal*2 - 1], calendar.month_abbr[halfquartal*2])


def yes_no(question):
    while "the answer is invalid":
        reply = str(input(question+' (Y/N): ')).lower().strip()
        if reply[0] == 'Y' or reply[0] == 'y' or reply[0] == 'yes':
            return True
        if reply[0] == 'N' or reply[0] == 'n' or reply[0] == 'no':
            return False


def compile_regex_from_list(regex_list):
    return re.compile("(?:" + "|".join(regex_list) + ")")