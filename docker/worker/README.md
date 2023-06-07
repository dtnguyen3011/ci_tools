# docker-based worker for python scripts

## Build
manual:
``` shell
docker build -t bcr-de01.inside.bosch.cloud/radar_gen5/python-worker:3.9 .
docker push bcr-de01.inside.bosch.cloud/radar_gen5/python-worker:3.9
```

## Usage

```
steps {
    sh(script: """
    git checkout -f master
    docker run --rm --name docker-worker -v ${WORKSPACE}:/workdir bcr-de01.inside.bosch.cloud/radar_gen5/python-worker:3.9 \
    python3 app/main.py
    """)
}
```