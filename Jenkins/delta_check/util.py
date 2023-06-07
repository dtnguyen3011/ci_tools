import re
import json
import typing
# import jsonschema
from datetime import datetime, timedelta


def contains_dates(string: str, dates: typing.Tuple[str, ...]) -> bool:
    """Determines if string contains any string from tuple

    """
    for date in dates:
        if date in string:
            return True
    return False


def get_dates(shift: int = 0) -> typing.Tuple[str, ...]:
    """Get tuple of date strings formatted as %Y-%m-%d

    Arguments:
      shift: Positive or negative integer which represents how many days
             will be included in tuple except current date. If shift is 0
             or hot provided, then there be only current date.

    Returns:
      Tuple[str, ...]
    """
    return tuple(datetime.strftime(datetime.now() - timedelta(x), '%Y-%m-%d') for x in range(0, abs(shift) + 1))


def extract_sort_key(dirname: str) -> str:
    """ Finds and returns ISO8601 formatted datetime or date string.
        If no date found than returns unmodified string.
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2}(?:T\d{2}-\d{2}-\d{2})?)', dirname)
    if match is not None:
        return match.group()
    return dirname


# def validate_json(schema_file: str, data: dict) -> None:
#     """Validate JSON data against provided schema file
#     """
#     with open(schema_file, 'r') as schf:
#         schema = json.load(schf)
#     jsonschema.validate(instance=data, schema=schema)


def read_json_file(file_name: str, schema_file: typing.Optional[str] = None) -> dict:
    """Read JSON file and validate if schema_file parameter is provided
    """
    with open(file_name, 'r') as rfile:
        data = json.load(rfile)
    # if schema_file:
    #     validate_json(schema_file, data)
    return data


def write_json_file(file_name: str, data: dict) -> None:
    """ Write data to JSON formatted file
    """
    with open(file_name, 'w') as outfile:
        outfile.write(json.dumps(data))
