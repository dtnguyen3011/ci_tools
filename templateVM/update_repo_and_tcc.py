'''
Script to update repo and, TCC version in repo and run TCC update.
Version: Python 3.6
Directory structure as below change if desired.
This script will call UpdateRepos.bat for pulling latest code on repo and installtcc.bat
or install_itc2.bat for updating TCC tools
Batch file update TCC has to be in the same lavel as this script and will take one argument is TCC version.
Currently batch file will find TCC in IF and Selena TCC version.
'''

import os
import subprocess
import argparse
import re
import logging
import yaml
import glob
import sys


script_loc = os.path.dirname(os.path.realpath(__file__))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-cf', '--config-file', help='Config file for repo info',
                        default='{}/repo_loc.yaml'.format(script_loc))
    return parser.parse_args()

def execute_cmd(cmd) -> int:
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = pipe.communicate()
    logging.debug(output.decode())
    return pipe.returncode

def get_config(config_file) -> list:
    """
    Read config yaml file and return config object
    :return: dict: config content
    """
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Finished reading config: {config_file}")
        return config
    except IOError as e:
        logging.error(f"Problem reading config file: {e}")
        sys.exit(1)

def is_linux() -> bool:
    logging.info(f"Machine is {os.name}")
    return os.name == "posix"


def main(args) -> None:
    config = get_config(args.config_file)
    is_failed = False
    machine_name = os.getenv("COMPUTERNAME", "Could not found computer name")
    machine_config = next(filter(lambda x: x['osType'] == 'windows', config))
    update_repo_cmd = script_loc + "\\UpdateRepo.bat "
    if is_linux():
        machine_config = next(filter(lambda x: x['osType'] == 'linux', config))
        update_repo_cmd = script_loc + "/UpdateRepo.sh "
    repos_to_update = glob.glob(machine_config['repoWildcard'])
    for repo_loc in repos_to_update:
        if not os.path.exists(repo_loc):
            logging.error(f"Could not found repo path: {repo_loc} on {machine_name}")
            continue
        logging.info(update_repo_cmd + repo_loc)
        return_code = execute_cmd(update_repo_cmd + repo_loc)
        is_failed = True if return_code != 0 else False
    if is_failed:
        logging.error(f"Update repo {repo_loc} failed on {machine_name}")
        sys.exit(1)

    if 'tcc_files' in machine_config:
        tcc_ver = []
        for tcc_file in machine_config['tcc_files']:
            if os.path.isfile(tcc_file):
                logging.debug(f"Reading file {tcc_file}")
                with open(tcc_file, 'r') as f:
                    tcc_ver.append(f.readline().rstrip())
            else:
                logging.info(f"Could not found {tcc_file} in {machine_name}")
        # Run update tcc
        tcc_ver.append("RadarGen5CI:DevLatest")
        logging.info(tcc_ver)

        tcc_packages_pattern = re.compile(r'^TCC_.+_(Windows|Linux)_.+')
        itc2_packages_pattern = re.compile(r'.+\:.+')

        for i in tcc_ver:
            if tcc_packages_pattern.match(i):
                logging.info(f"Execute TCC to install {i}")
                tcc_xml = "ITO\TCC\Base\{}\Windows\{}.xml".format(
                    i.split("_")[1], i)
                update_tcc_cmd = script_loc + "\\install_tcc.bat " + tcc_xml
            elif itc2_packages_pattern.match(i):
                logging.info(f"Execute ITC2 to install {i}")
                update_tcc_cmd = script_loc + "\\install_itc2.bat " + i
            else:
                logging.warning("Invalid package format!!!")
            logging.info(update_tcc_cmd)
            return_code = execute_cmd(update_tcc_cmd)
            is_failed = True if return_code != 0 else False
        if is_failed:
            logging.error(f"Update tcc failed on {machine_name}")
            sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s',
                                                                            level=logging.DEBUG)
    args = parse_args()
    main(args)
