#!/usr/bin/env python3
""" Script to check infrastructure service availability
"""

import sys
import argparse
import logging
import json
from enum import Enum
from pprint import pformat
from typing import List
from itertools import chain
from jsonpath_ng import parse
from simple_plugin_loader import Loader
from plugins.plugin import Plugin

logging.basicConfig(format='%(asctime)s [%(module)s] [%(levelname)-5.5s] %(message)s', level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class ValidateArg(argparse.Action):
    """Class to validate if string argument is an empty string
    """

    def __call__(self, parser, namespace, values, option_string=None):
        if values == '':
            LOGGER.error('Argument %s cannot be empty string', self.dest)
            sys.exit(1)
        setattr(namespace, self.dest, values)


class CheckLevel(Enum):
    all = 'all'
    stage = 'stage'

    def __str__(self):
        return str(self.value)


def load_plugins() -> dict:
    """ Loads plugin modules
        Returns: dict of loaded plugin modules
    """
    loader = Loader()
    plugins = loader.load_plugins('plugins', Plugin)
    return plugins


def parse_args() -> argparse.Namespace:
    """Adds and parses command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--meta-file', required=True, action=ValidateArg,
                        help='JSON file containing metadata of LUCX config')
    parser.add_argument('--check-level', required=False, default='all', type=CheckLevel, choices=list(CheckLevel),
                        help='Check level of script')
    parser.add_argument('--debug', action='store_true', default=False, dest='debug', help='Enable debugging mode')
    parser.add_argument('--services', nargs='+', action=ValidateArg, default='all',
                        help='Service names that should be checked')
    credentials = parser.add_argument_group('credentials')
    credentials.add_argument('--user', required='--password' in sys.argv, action=ValidateArg,
                             help='User name for service(s)')
    credentials.add_argument('--password', required='--user' in sys.argv, action=ValidateArg,
                             help='Password for service(s)')
    return parser.parse_args()


def read_json_file(config_file: str) -> dict:
    """ Read and parse JSON config file
    """
    config: dict = dict()
    try:
        with open(config_file, 'r') as infile:
            config_text = infile.read()
        config = json.loads(config_text)
    except IOError as ioe:
        LOGGER.error('Error reading input file: %s', ioe)
    except json.decoder.JSONDecodeError as jde:
        LOGGER.error('Error decoding JSON: %s', jde)
    return config


def extract_service_configs(config: dict, query: str) -> List:
    jsonpath_expr = parse(query)
    return [match.value for match in jsonpath_expr.find(config)]


def filter_service_configs(configs: list, services: List[str]) -> list:
    if 'all' in services:
        return configs
    return [config for config in configs if config['name'] in services]


def main(args: argparse.Namespace, plugins: dict) -> None:
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)
    LOGGER.debug('Script called with following args:\n%s\n', pformat(vars(args)))

    config = read_json_file(args.meta_file)
    plugin_configs = extract_service_configs(config, '$..meta.dependsOnServices')
    plugin_configs = list(chain(*plugin_configs))
    plugin_configs = filter_service_configs(plugin_configs, args.services)
    LOGGER.info('%i Service(s) selected for check', len(plugin_configs))

    error_count = []
    for plugin_config in plugin_configs:
        if args.user and args.password:
            plugin_config['username'] = args.user
            plugin_config['password'] = args.password
        check_type = plugin_config['checkType']
        LOGGER.debug(pformat(plugin_config))
        if check_type not in plugins.keys():
            LOGGER.error('Plugin for check type %s is not found on %s!', check_type, plugin_config['name'])
            error_count.append(plugin_config['name'])
        try:
            plugins[check_type].execute(plugin_config)
            LOGGER.info('Check status for "%s" (%s) is OK', plugin_config['name'], check_type)
        except Exception as exc: #pylint: disable=broad-except
            LOGGER.error('Check status for "%s" (%s) is FAILED', plugin_config['name'], check_type)
            LOGGER.error(exc)
            error_count.append(plugin_config['name'])
    if error_count:
        message = "Some services (" + ", ".join(error_count) + ") cannot be accessed right now. Please wait a moment to try again or Contact Cx Team for support !!!"
        sys.exit(message)


if __name__ == '__main__':
    main(parse_args(), load_plugins())
