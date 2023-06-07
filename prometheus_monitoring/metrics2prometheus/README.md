## api for getting metrics from influxdb and provide it for prometheus

#### Building image
python3 ./build.py

#### for deploy create file .env with next variables:
* INFLUXDB_URL
* INFLUXDB_PORT
* INFLUXDB_USERNAME
* INFLUXDB_PASSWORD
* TIME_RANGE - same as scrape interval in prometheus

#### .env file format
```text
INFLUXDB_URL="abtv55170.de.bosch.com"
INFLUXDB_PORT="8086"
```

#### Metrics:
`Failure_reasons{"Stage","reason"}` - counter with failures by timerange

#### Dashboard
https://abtv55170.de.bosch.com:3000/d/Gyln4hXnk/build-failures-stats

#### Alerts_query
```
(sum_over_time(Failure_reasons_total[3h])) > 5
```
