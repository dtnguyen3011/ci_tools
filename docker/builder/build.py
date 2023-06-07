import docker
import os
import argparse

def configure_pip():
    """
    configure pip to use bosch pip artifactory
    """
    user = parameters.user
    password = parameters.password
    with open('pip.conf.example', 'r') as fp:
        file = fp.readlines()
    newfile = ''
    for line in file:
        newfile += line.replace('pip-user', user).replace('pip-password', password)
    with open('pip.conf', 'w') as fp:
        fp.write(newfile)

def update_version(release: str):
    """
    update version in version file
    """
    with open('version', 'r') as fp:
        cur_version = fp.read().split('.')
    if release == 'major':
        new_version = f'{str(int(cur_version[0]) + 1)}.{cur_version[1]}'
    elif release == 'minor':
        new_version = f'{cur_version[0]}.{str(int(cur_version[1]) + 1)}'
    else:
        print('version doesn`t defined, updated minor')
        new_version = f'{cur_version[0]}.{str(int(cur_version[1]) + 1)}'
    with open('version', 'w') as fp:
        fp.write(new_version)

def build_and_push_image(registry: str, push: bool):
    """
    auth in registry, build and push image
    """
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    repository = 'bcr-de01.inside.bosch.cloud/radar_gen5'
    client.login(username=parameters.user, password=parameters.password, registry='https://bcr-de01.inside.bosch.cloud')
    with open('version', 'r') as fp:
        version = fp.read()
    tag = f'{repository}/{registry}:v{version}'
    client.images.build(path=os.curdir, tag=tag)
    if push:
        client.images.push(repository=f'{repository}/{registry}', tag=f'v{version}')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True, help='user for pip artifactory')
    parser.add_argument('-p', '--password', required=True, help='password for pip artifactory')
    parser.add_argument('-r', '--release', required=False, default='minor', help='minor or major release')
    parser.add_argument('-n', '--name', required=True, help='name of image')
    parser.add_argument('--push', required=False, action='store_true', help='push image to registry')
    args = parser.parse_args()
    return args


parameters = parse_args()
configure_pip()
# update_version(parameters.release) Not use without updating version in git
build_and_push_image(parameters.name, parameters.push)
