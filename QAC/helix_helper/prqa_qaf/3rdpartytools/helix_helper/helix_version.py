#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2020 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: 	helix_version.py
# Author(s): 	Silva André (CC-AD/ESW4)
# ----------------------------------------------------------------------------
"""Parses information about the helix version and provides helper methods"""

from logger import LOGGER
import re

_REGEX_FOR_FULL_VERSION_LINE = (
    r'(?P<name>PRQA\sFramework|Helix\sQAC)(\sversion)?'    # PRQA / Helix string
    r'\s(?P<version>(\.?\d)+(-[a-zA-Z]+)?)')    # version number

_REGEX_FOR_MAJOR_MINOR = (
    r'(?P<major>\d+)'    # Major version
    r'\.(?P<minor>\d+)'    # Minor version
)


class HelixVersion:
    """Helix version related utils"""
    def __init__(self, cli_version_string):
        self._cli_version_string = cli_version_string
        (self._software_name,
         self._software_version) = self._get_software_name_and_version()

    def _get_software_name_and_version(self):
        for match in re.finditer(_REGEX_FOR_FULL_VERSION_LINE,
                                 self._cli_version_string, re.MULTILINE):
            software_name = match.group('name')
            software_version = match.group('version')
            if software_name and software_version:
                return (software_name, software_version)

        LOGGER.warning('Unknown software version = %s', self._cli_version_string)
        return ('Unknown Software', 'Unknown version')

    def major_minor(self):
        """Gets the major and minor versions for the supported version"""
        for match in re.finditer(_REGEX_FOR_MAJOR_MINOR,
                                 self._software_version, re.MULTILINE):
            major = match.group('major')
            minor = match.group('minor')
            if major and minor:
                return (int(major), int(minor))

        # Unknown major and minors
        LOGGER.warning('Unknown major and minor. version = %s', self._software_version)
        return (0, 0)

    def is_helix(self):
        """Returns wether the running software is helix"""
        return 'Helix' in self._software_name

    def is_prqa(self):
        """Returns wether the running software is prqa"""
        return 'PRQA' in self._software_name
