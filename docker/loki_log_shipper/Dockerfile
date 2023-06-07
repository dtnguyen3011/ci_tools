FROM bcr-de01.inside.bosch.cloud/radar_gen5/loki-shipper-base:v0.1

COPY /app /loki_shipper
WORKDIR /loki_shipper
RUN pip install -r requirements.txt
RUN addgroup --gid 109396 loki_shipper \
    && adduser --disabled-password --home /loki_shipper --uid 109396 --ingroup loki_shipper loki_shipper
RUN rm -f /etc/pip.conf
RUN apk del gcc g++
USER 109396

CMD python3 -m gunicorn -w 4 -b 0.0.0.0:5000 'loki_shipper:create_app()'
