""" Plugin to check if remote HTTP endpoint responds with specified code
"""
import sys
import requests
import urllib3
import jsonschema

sys.path.append('..')
from service_check import read_json_file
from .plugin import Plugin


class Http(Plugin):
    @staticmethod
    def execute(config: dict):
        jsonschema.validate(config, read_json_file('schemas/http.json'))
        session = requests.Session()
        retries = urllib3.Retry(total=3,
                                backoff_factor=1,
                                status_forcelist=[500, 502, 503, 504])
        username = config.get('username', None)
        password = config.get('password', None)
        headers = config.get('headers', {})
        if username and password:
            session.auth = (username, password)
        session.verify = False
        if not session.verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.mount(config['url'], requests.adapters.HTTPAdapter(max_retries=retries))
        result = session.request(
            method=config['method'],
            url=config['url'],
            headers=headers,
            timeout=3
        )
        if result.status_code != config['expectedReturnCode']:
            raise Exception(f'HTTP check for url {config["url"]} returned code '
                            f'{result.status_code}, but expected {config["expectedReturnCode"]}')
