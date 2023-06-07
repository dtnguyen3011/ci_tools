#!/bin/bash
docker build --network=host \
       --build-arg http_proxy=${http_proxy} \
       --build-arg https_proxy=${https_proxy} \
       -t bcr-de01.inside.bosch.cloud/radar_gen5/cx_automation:${1:-1.0.0} .
