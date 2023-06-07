from flask import Flask, request
from prometheus_client import Counter, generate_latest
from influxdb_metrcs import InfluxMetrics


app = Flask(__name__)
c = Counter("Failure_reasons", "reasons", ["Stage", "reason"])

@app.route("/influxdb_metrics", methods=["GET"])
def metrics():
    i = InfluxMetrics()
    influx_metrics = i.failed_build_statics(db_name="ccda_radar_gel")
    if influx_metrics:
        for record in influx_metrics:
            c.labels(Stage=record["Stage"], reason=record["error"]).inc()
    answer = generate_latest()
    c.clear()
    return answer, 200
