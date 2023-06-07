#=============================================================================
#  C O P Y R I G H T
#-----------------------------------------------------------------------------
#  Copyright (c) 2020 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
#=============================================================================
# Filename: 	file_transfer.py
# Author(s): 	Andre Silva (CC-AD/ESW4)
# ----------------------------------------------------------------------------

from datetime import datetime
from hashlib import sha256
from os import path
from shutil import copyfile

from logger import LOGGER


def _sha256_digest(filepath):
    block_size = 65536
    file_hash = sha256()

    with open(filepath, 'rb') as file_to_hash:
        file_block = file_to_hash.read(block_size)
        while len(file_block) > 0:
            file_hash.update(file_block)
            file_block = file_to_hash.read(block_size)

        return file_hash.hexdigest()


def _copy_files_if_hashes_are_different(source_folder, target_folder,
                                        filename):
    def check_if_filepath_exists_and_log_if_it_does_not(filepath):
        if not path.exists(filepath):
            LOGGER.warning('Could not find the file in path: %s', filepath)
            return False

        return True

    source_filepath = path.join(source_folder, filename)
    target_filepath = path.join(target_folder, filename)

    if not check_if_filepath_exists_and_log_if_it_does_not(source_filepath):
        return ''

    source_sha256 = _sha256_digest(source_filepath)
    target_sha256 = ''
    if path.exists(target_filepath):
        target_sha256 = _sha256_digest(target_filepath)

    if target_sha256 != source_sha256:
        delta_time = datetime.now()
        copyfile(source_filepath, target_filepath)
        delta_time = datetime.now() - delta_time
        LOGGER.info('Copied %s to %s in %s', source_filepath, target_filepath,
                    delta_time)

    return target_folder

_NETWORK_WARNING_STR = '''Configured LOCAL_BASELINE_PATH is a network share. 
Because of Helix performance reasons this file will be copied from %s to %s.

To avoid this mechanism either make sure LOCAL_BASELINE_PATH is not a network share. (Normally in the xxx_helper.json)'''

def copy_file_to_local_target_if_source_in_shared_folder(
        source_folder, target_folder, filename):
    """If the source folder is a network folder then copy the baseline locally if necessary"""
    def is_network_folder(filepath):
        return filepath.startswith('//') or filepath.startswith('\\\\')

    if is_network_folder(source_folder):
        LOGGER.info(
            _NETWORK_WARNING_STR,
            source_folder, target_folder)
        return _copy_files_if_hashes_are_different(source_folder,
                                                   target_folder, filename)

    return source_folder
