import docker
import os

def configure_pip():
    user = os.getenv("PIP_USER")
    password = os.getenv("PIP_PASSWORD")
    with open("pip.conf.example", "r") as fp:
        file = fp.readlines()
    newfile  = ""
    for line in file:
        newfile += line.replace("pip-user", user).replace("pip-password", password)
    with open("pip.conf", "w") as fp:
        fp.write(newfile)

def update_version(release):
    with open("version", "r") as fp:
        cur_version = fp.read().split('.')
    if release == "major":
        new_version = f"{str(int(cur_version[0]) + 1)}.{cur_version[1]}"
    elif release == "minor":
        new_version = f"{cur_version[0]}.{str(int(cur_version[1]) + 1)}"
    else:
        print("version doesn't defined, updated minor")
        new_version = f"{cur_version[0]}.{str(int(cur_version[1]) + 1)}"
    with open("version", "w") as fp:
        fp.write(new_version)

def build_and_push_image(registry, push=None):
    client = docker.from_env()
    repository = "bcr-de01.inside.bosch.cloud/radar_gen5"
    with open("version", "r") as fp:
        version = fp.read()
    tag = f"{repository}/{registry}:v{version}"
    client.images.build(path=os.curdir, tag=tag)
    if push:
        client.images.push(tag=tag)



configure_pip()
update_version("minor")
build_and_push_image("metrics2prometheus")