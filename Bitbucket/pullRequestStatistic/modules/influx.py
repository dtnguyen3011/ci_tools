from influxdb import InfluxDBClient
from modules.bitbucket import *
import dateutil.parser

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def influx_compile_push_request_body(measurement_name, tags_dict, fields_dict, timestamp):
    return [{
        "measurement": measurement_name,
        "tags": tags_dict,
        "fields": fields_dict,
        "time": timestamp
    }]


class Influx:
    def __init__(self, influx_server, influx_port, influx_user, influx_password, influx_database):
        self.database = influx_database
        self.influx_connection = InfluxDBClient(influx_server, influx_port, influx_user, influx_password,
                                                influx_database)

    def push_data(self, prepared_request):
        self.influx_connection.write_points(prepared_request)
        logger.info("Written to InfluxDB successfully.")
        logger.debug("Written data: {}".format(prepared_request))

    def get_oldest_entry_day(self, measurements, tags=None):
        the_oldest = None
        for measurement in measurements:
            query = "SELECT * FROM {} {} ORDER BY time ASC;".format(measurement, Influx._where_and(tags))
            result = list(self.influx_connection.query(query))
            if result:
                oldest_by_activity = get_day_start_timestamp(dateutil.parser.parse(result[0][0]["time"]).timestamp())
                if the_oldest is None:
                    the_oldest = oldest_by_activity
                if the_oldest > oldest_by_activity:
                    the_oldest = oldest_by_activity
        return the_oldest

    def get_newest_entry_day(self, measurements, tags=None):
        the_newest = None
        for measurement in measurements:
            query = 'SELECT * FROM {} {} ORDER BY time DESC;'.format(measurement, Influx._where_and(tags))
            result = list(self.influx_connection.query(query))
            if result:
                newest_by_activity = (dateutil.parser.parse(result[0][0]["time"]).timestamp())
                if the_newest is None:
                    the_newest = newest_by_activity
                if the_newest < newest_by_activity:
                    the_newest = newest_by_activity
        return the_newest

    @staticmethod
    def _where_and(tags):
        if not tags:
            return ''
        where_clause = ' AND '.join("{} = '{}'".format(k, v) for k, v in tags.items())
        return 'WHERE ' + where_clause