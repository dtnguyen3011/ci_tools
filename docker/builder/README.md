# Script for building images in CI

Script added to docker image `bcr-de01.inside.bosch.cloud/radar_gen5/python-builder:0.1`
### Parameters:
* `-u`  user for pip artifactory
* `-p`  password for pip artifactory
* `-n`  name of image
* `--push`  push image to docker registry

Default registry is `bcr-de01.inside.bosch.cloud/radar_gen5`

for tag script use file `version` 

### Example of usage:
```
pipeline {
    agent {
        label 'buildslaves_abts55144'
    }
    environment {
        CREDS    = credentials('BCR_TOKEN')
    }
    stages {

        stage("build image") {
            when { changeset "docker/loki_log_shipper/*" }
            steps {
                sh(script: """
                docker run --rm --privileged --name docker-builder -v /var/run/docker.sock:/var/run/docker.sock \
                -v ${WORKSPACE}/docker/loki_log_shipper:/app bcr-de01.inside.bosch.cloud/radar_gen5/python-builder:0.1 \
                python3 /builder/build.py -u $CREDS_USR -p $CREDS_PSW -n loki-shipper --push
                rm -f docker/loki_log_shipper/pip.conf
                """)
            }
        }
    }
}
```
