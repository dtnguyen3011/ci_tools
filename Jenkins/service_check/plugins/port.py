""" Plugin to check if specified TCP port is open on target host
"""
import sys
import socket
import jsonschema

sys.path.append('..')
from service_check import read_json_file
from .plugin import Plugin


class Port(Plugin):
    @staticmethod
    def execute(config: dict) -> None:
        jsonschema.validate(config, read_json_file('schemas/port.json'))
        host = config['host']
        port = config['port']
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        location = (host, port)
        result = sock.connect_ex(location)
        if result != 0:
            raise Exception(f"TCP Port {port} is closed on {host}")
