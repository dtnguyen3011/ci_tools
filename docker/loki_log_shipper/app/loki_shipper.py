""" Server that exports Jenkins job console log to Loki via prom api
"""
import multiprocessing
import os
import re
import shutil
from collections import namedtuple
from typing import Tuple, List, Any
from zipfile import ZipFile
from pathlib import Path

import dateutil.parser
import requests
import snappy
from flask import Flask, request
from google.protobuf import timestamp_pb2

from logproto_pb2 import Entry, PushRequest, Stream

ENV_VARS: tuple = ('JENKINS_USER',
                   'JENKINS_PASSWORD',
                   'LOKI_URL',
                   'BATCH_SIZE',
                   'DRY_RUN')

Options = namedtuple(
    'Options', (
        'jenkins_user',
        'jenkins_password',
        'loki_url',
        'batch_size',
        'dry_run',
    )
)

def exctract_pr_number(job_name: str) -> Tuple[str, str]:
    pr_number = ""
    pr = re.findall("PR-\d+", job_name)
    if pr:
        pr_number = pr[0]
        job_name = job_name.replace(f"/{pr_number}", "")
    return job_name, pr_number

def generate_line(line: str, pr: str, build_id: str, commit_id: str) -> str:
    if pr:
        if commit_id:
            return f"{line} PR={pr[3:]} build={build_id} commit={commit_id}"
        else:
            return f"{line} PR={pr[3:]} build={build_id}"
    else:
        return line

def optimize_log_file_name(log: str) -> str:
    pattern = "(\(\d+\_\d+\))"
    new_log_file_name = re.sub(pattern, "", log)
    return new_log_file_name


def generate_stream(data: list, job_name: str, build_id: str, commit_id: str,
                    log_file: str) -> Stream:
    clear_job_name, pr = exctract_pr_number(job_name)
    log_file_name = optimize_log_file_name(log_file)
    return Stream(
        labels=compose_labels({'sourceJenkins': 'Jenkins',
                               'jobJenkins': clear_job_name, 'logJenkins': log_file_name}),
        entries=[Entry(timestamp=ts, line=generate_line(line, pr, build_id, commit_id)) for ts, line in data]
    )


def get_requests_session(username: str, password: str) -> requests.Session:
    session = requests.session()
    session.auth = (username, password)
    session.trust_env = False
    session.verify = False
    return session


def compose_labels(labels: dict) -> str:
    return '{' + ','.join((f'{k}="{v}"' for k, v in labels.items())) + '}'


class LogShipper:
    def __init__(self, loki_url: str):
        self.url = loki_url
        self.headers = {'Content-type': 'application/protobuf',
                        'Content-Encoding': 'snappy'}
        self.session = requests.session()
        self.session.trust_env = False

    def send_request(self, push_request: PushRequest):
        return requests.post(
            self.url, data=snappy.compress(push_request.SerializeToString()),
            headers=self.headers
        )

def download_artifacts(options: Options, job_url: str) -> None:
    artifacts_url = f'{job_url}/artifact/*zip*/archive.zip'
    session = get_requests_session(options.jenkins_user,
                                   options.jenkins_password)
    with session.get(artifacts_url, stream=True, verify = False) \
         as artifacts_request:
        artifacts_request.raise_for_status()
        with open('archive.zip', 'wb') as artifacts_file:
            for chunk in artifacts_request.iter_content(chunk_size=8192):
                artifacts_file.write(chunk)


def unpack_artifacts() -> None:
    with ZipFile('archive.zip', 'r') as artifacts_archive:
        artifacts_archive.extractall()
    if not os.path.exists('logs'):
        os.mkdir('logs')
    for log_file in os.listdir('archive/logs'):
        if log_file.endswith('.zip'):
            with ZipFile(f'archive/logs/{log_file}', 'r') as log_archive:
                log_archive.extractall()
        elif log_file.endswith('.log'):
            shutil.copyfile(f'archive/logs/{log_file}', f'logs/{log_file}')


def collect_artifacts_logs(options: Options, job_name: str, job_url: str,
                           build_id: str, commit_id: str, shipper: LogShipper) -> None:
    download_artifacts(options, job_url)
    unpack_artifacts()
    for log_file_name in os.listdir('logs'):
        print(log_file_name)
        with open(f'logs/{log_file_name}', errors='ignore') as log_file:
            read_data = log_file.readlines()
            process_data(options, job_name, read_data,
                         log_file_name, build_id, commit_id, shipper)


def collect_console_logs(options: Options, job_name: str, job_url: str,
                         build_id: str, commit_id: str, shipper: LogShipper) -> None:
    session = get_requests_session(options.jenkins_user,
                                   options.jenkins_password)
    result = session.get(f'{job_url}/consoleText')
    if result.status_code != 200:
        raise Exception(f'Error downloading console log data from'
                        f' {job_url}: {result.text}')
    process_data(options, job_name, result.text.splitlines(), '__console.log',
                 build_id, commit_id, shipper)


def process_data(options: Options, job_name: str, data, log_file: str,
                 build_id: str, commit_id: str, shipper: LogShipper) -> None:
    ts_regex = (r'\[?(?P<timestamp>(?P<year>\d{4})-(?P<month>\d{2})'
                r'-(?P<day>\d{2})T(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})'
                r'(?:\.(?P<ms>\d+))?(?P<tz>.*?)?)]?:?( |\])(?:\s+)?'
                r'(?P<message>.*)')

    processed_data = []
    for line in data:
        match = re.match(ts_regex, line)
        if match:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(
                dt=dateutil.parser.isoparse(match.group('timestamp'))
            )
            processed_data.append((timestamp, match.group('message')))

    batch_data = [processed_data[i:i + int(options.batch_size)] for i in
                  range(0, len(data), int(options.batch_size))]
    for batch in batch_data:
        stream = generate_stream(batch, job_name, build_id, commit_id, log_file)
        push_request = PushRequest(streams=[stream])
        if not options.dry_run == 'TRUE':
            shipper.send_request(push_request=push_request)
        else:
            print(push_request)


def worker(args) -> None:
    options, job_url, job_name, commit_id = args
    print(f'Started worker {multiprocessing.current_process().name} with '
          f'following args {options.jenkins_user, job_url, job_name, commit_id}')

    build_id = job_url[:-1].split('/')[-1]

    shipper = LogShipper(options.loki_url)

    workspace_name = f'{job_name}-{build_id}'.replace('/', '-')
    if os.path.exists(workspace_name):
        raise Exception(f'Workspace {workspace_name} already exists!')
    os.mkdir(workspace_name)
    os.chdir(workspace_name)

    collect_console_logs(options, job_name, job_url, build_id, commit_id, shipper)
    collect_artifacts_logs(options, job_name, job_url, build_id, commit_id, shipper)

    os.chdir(Path.home())
    shutil.rmtree(workspace_name, ignore_errors=True)
    print(f'Ended worker {multiprocessing.current_process().name}')


def load_options_from_env() -> Options:
    options: Options = Options(
        jenkins_user=os.getenv('JENKINS_USER', None),
        jenkins_password=os.getenv('JENKINS_PASSWORD', None),
        loki_url=os.getenv('LOKI_URL', None),
        batch_size=int(os.getenv('BATCH_SIZE', '1000')),
        dry_run=os.getenv('DRY_RUN', 'FALSE').upper()
    )
    if not all(options):
        missing_env_vars = [key.upper() for key, value in
                            options._asdict().items() if not value]
        raise Exception(f'Missing environment variables: '
                        f'{", ".join(missing_env_vars)}')
    return options


def create_app() -> Flask:
    options: Options = load_options_from_env()
    app: Flask = Flask(__name__)

    # pylint: disable=unused-variable
    @app.route('/', methods=['POST'])
    def home():
        job_url = request.args.get('jobUrl')
        job_name = request.args.get('jobName')
        commit_id = request.args.get('commitId')
        multiprocessing.Process(target=worker,
                                args=([options, job_url, job_name, commit_id],)).start()
        return '', 204

    # pylint: disable=unused-variable
    @app.route('/health', methods=['GET'])
    def health():
        return 'OK'

    return app


if __name__ == '__main__':
    create_app().run(debug=True, threaded=True)
