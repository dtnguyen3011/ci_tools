docker run -it -v ${PWD}:${PWD} --network=host bcr-de01.inside.bosch.cloud/radar_gen5/cx_automation:${1:-1.0.0} /bin/bash
