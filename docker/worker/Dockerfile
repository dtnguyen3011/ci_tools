FROM bcr-de01.inside.bosch.cloud/radar_gen5/python:3.9-alpine

ADD ./requirements.txt requirements.txt
RUN mkdir /workdir
WORKDIR /workdir
RUN pip install -r ../requirements.txt