FROM bcr-de01.inside.bosch.cloud/radar_gen5/python:3.9-alpine

ADD  app /app
WORKDIR /app
ADD pip.conf /etc/pip.conf
RUN pip install -r requirements.txt
RUN addgroup -g 2000 python-app && adduser -u 2000 -G python-app -s /bin/sh -D python-app
RUN rm -f /etc/pip.conf
USER 2000

CMD gunicorn --bind 0.0.0.0:5000 wsgi:app