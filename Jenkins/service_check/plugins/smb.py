""" Plugin to check if specified SMB share can be accessed
"""
import os
import sys
import jsonschema

sys.path.append('..')
from service_check import read_json_file
from .plugin import Plugin
from .plugin import UnsupportedPlatformException


class Smb(Plugin):
    @staticmethod
    def execute(config: dict):
        jsonschema.validate(config, read_json_file('schemas/smb.json'))
        path: str = config['path']
        if sys.platform != 'win32':
            raise UnsupportedPlatformException("SMB share can be checked only on windows platform")
        os.listdir(path)
