from influxdb import InfluxDBClient
import os
import re
import datetime

class InfluxMetrics:

    def __init__(self):
        db_url = os.getenv("INFLUXDB_URL")
        db_port = os.getenv("INFLUXDB_PORT") or "8086"
        db_user = os.getenv("INFLUXDB_USERNAME")
        db_pass = os.getenv("INFLUXDB_PASSWORD")
        self.client = InfluxDBClient(host=db_url, port=db_port, username=db_user, password=db_pass)

    def failed_build_statics(self, db_name: str) -> list:
        """
        get data from DB and find information about error in stages
        :param db_name: name of database with errors
        :return: list of dicts with stages and errors
        """
        data = []
        timerange = os.getenv("TIME_RANGE")     # should be same as prometheus scrape interval
        self.client.switch_database(db_name)
        result = self.client.query(
            f'SELECT * FROM "pull_request_builds_statistics" WHERE time > now() -1d'
        )
        points = result.get_points(measurement="pull_request_builds_statistics")
        if points:
            for point in points:
                if point["result"] == "FAILURE":
                    if self.calculate_timeperiod(point) < self.convert_to_seconds(timerange):
                        data += self.find_stage_and_error(point)
        return data

    def calculate_timeperiod(self, record):
        time_now = datetime.datetime.utcnow()
        try:
            time_record = datetime.datetime.strptime(record["time"], '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            time_record = datetime.datetime.strptime(record["time"], '%Y-%m-%dT%H:%M:%SZ')
        return (time_now - time_record).total_seconds() - record["build_duration"] / 1000


    @staticmethod
    def convert_to_seconds(s):
        seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        return int(s[:-1]) * seconds_per_unit[s[-1]]

    @staticmethod
    def parse(reason: str, pattern: str) -> dict:
        """
        parse string for found stage name and error message
        :param reason: string with failed massage
        :param pattern: pattern for Stage name
        :return: dict with stage name and error message
        """
        stages = {}
        pattern_error = r'(?<=with message \")(.*)'
        for data in reason.split(";"):

            stage = re.findall(pattern, data)
            error = re.findall(pattern_error, data)

            if stage and error:
                if stages.get(stage[0]) is None:
                    stages.update({stage[0]: error[0][:-1]})
        return stages

    def find_stage_and_error(self, record: dict) -> list:
        """
        detect stage name(or other useful information) and error message
        :param record: record from database with information about build
        :return: list of dicts of stages and error
        """
        reason = record["failure_reason"]
        stages = {}
        if "Merging of branch" in reason:
            exit_code = re.findall(r'(?<=Aborting the merge failed with message \")(.*)', reason)[0][:-1]
            stages.update({"Merging of branch": exit_code})
        elif "The JSON input text should neither be null nor empty" in reason:
            stages.update({"Converting jsonString": "The JSON input text should neither be null nor empty"})
        elif "Stage" in reason:
            for data in reason.split(";"):

                stage = re.findall(r'(?<=Stage in \").*?(?=\")', data) or re.findall(r'(?<=Stage \").*?(?=\")', data)
                error = re.findall(r'(?<=with message \")(.*)', data)

                if stage and error:
                    if stages.get(stage[0]) is None:
                        stages.update({stage[0]: error[0][:-1]})
        elif "n/a" in reason:
            stages.update({"Undefined": "Undefined"})
        elif "Archiving failed" in reason:
            stages.update(self.parse(reason, r'(?<=Archiving in \").*?(?=\")'))
        elif "Node in" in reason and "Stage" not in reason:
            stages.update(self.parse(reason, r'(?<=Node in \").*?(?=\")'))
        elif "http-put via curl" in reason:
            error = re.findall(r'(?<=with message \")(.*)', reason)[0]
            stages.update({"http-put via curl": error})
        else:
            stages.update({"Undefined": reason.split(";")[0]})

        stage_data = []
        for k, v in stages.items():
            stage_data.append({"Stage": k, "error": v})
        return stage_data

