#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: logger.py
# Author(s): Andre Silva CC-AD/ESW3 (Maintainer)
#            Ingo Jauch CC-AD/ESW3 (Maintainer)
#            Pordzik Matthaeus ITKG/ENG34.1
# ----------------------------------------------------------------------------
"""Logger that on all levels to console"""

import logging
from sys import stdout

LOGGER = logging.getLogger()

def initialize(module_name):
    """Initializes the logger mechanism given the initialization arguments"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [{}] [%(levelname)s] %(message)s'.format(
            module_name),
        handlers=[logging.StreamHandler(stdout)])

def set_verbose():
    """Sets the verbose logging level"""
    LOGGER.setLevel(logging.DEBUG)
