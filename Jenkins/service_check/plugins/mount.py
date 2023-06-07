import os
import sys
import subprocess
import jsonschema

sys.path.append('..')
from service_check import read_json_file
from .plugin import Plugin
from .plugin import UnsupportedPlatformException

class Mount(Plugin):
    @staticmethod
    def execute(config: dict):
        jsonschema.validate(config, read_json_file('schemas/mount.json'))

        if sys.platform != 'linux':
            raise UnsupportedPlatformException("Mount point can be checked only on linux platform")

        mount_point: str = config['mount_point']
        network_path: str = config['network_path']
        cmd = "df | grep '" + mount_point + "' | awk '{print $1}'"
        file_system = subprocess.check_output(cmd, shell=True).rstrip().decode("utf-8")

        if not file_system:
            raise Exception(f'MOUNT check FAILED for unmounted path {mount_point}')

        if network_path != file_system:
            raise Exception(f'MOUNT check FAILED for wrong network path on mount point {mount_point} to {file_system}, instead of {network_path}')

        os.listdir(mount_point)
