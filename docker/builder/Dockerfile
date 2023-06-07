FROM bcr-de01.inside.bosch.cloud/radar_gen5/python:3.9-alpine

ADD . /builder
RUN mkdir /app
WORKDIR /app
RUN pip install -r /builder/requirements.txt

