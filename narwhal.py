import datetime
import json
import os
import re
import zlib

import dateutil.parser
import msgpack
import numpy as np
import redis
import tablib
from klein import Klein
from twisted.internet import endpoints, reactor, task
from twisted.web.server import Site
from twisted.web.static import File

from pri import PRI

VERSION = "0.2"
DASH_LINE = "-----------------------------------------------------------------"

configuration = {
    "SERVER_NAME": "Narwhal",
    "REMOTE_REDIS_HOST": "192.168.1.14",
    "REMOTE_REDIS_PORT": 6379,
    "REDIS_MAIN_DB": 0,
    "SYSLOG_CACHE_PROCESS_INTERVAL": 2,
    "SYSLOG_CACHE_DB_NES": 1,
    "COMPRESSION_TYPE": 5,
    "DASHBOARD_WEB_INTERFACE": "0.0.0.0",
    "DASHBOARD_WEB_PORT": 3000,
    "PRIVATE_KEY": "localhost.pem",
    "SEVERITY_TO_RETURN": "0 1 2 3",
    "DASHBOARD_SHOW_HOURS": 4,
    "DASHBOARD_DATA_REFRESH_SECONDS": 3,
    "ENDPOINT_SYSLOG_TRANSMISSION_INTERVAL_SECONDS": 1,
    "SEVERITY_PATTERN": "sev*"
}

# RFC 5424
SEVERITY_CODE = {
    0: "emerg",
    1: "alert",
    2: "crit",
    3: "err",
    4: "warning",
    5: "notice",
    6: "info",
    7: "debug",
}

data_record_template = {
    "n": [],
    "dt": [],
    "endpoint": [],
    "severity": [],
    "facility": [],
    "ip": [],
    "system": [],
    "timestamp": [],
    "event": [],
}

redis_main_db = ""
date_key = ""


def display_console_banner():

    base_url = "https://" + \
        configuration["DASHBOARD_WEB_INTERFACE"] + ":" + \
        str(configuration["DASHBOARD_WEB_PORT"])

    print(DASH_LINE)
    print("    _  __                __        __ ")
    print("   / |/ /__ ______    __/ /  ___ _/ / ")
    print("  /    / _ `/ __/ |/|/ / _ \/ _ `/ /  ")
    print(" /_/|_/\_,_/_/  |__,__/_//_/\_,_/_/    syslog server v." + VERSION)
    print(DASH_LINE)
    print(" URL's: "+base_url)
    print("        " + base_url + "/json")
    print("        " + base_url + "/json_alerts")
    print("        " + base_url + "/csv")
    print("        " + base_url + "/csv_alerts")
    return


def load_env_variable(env_variable):
    global configuration
    env_variable_value = os.getenv(env_variable)
    if env_variable_value:
        print(env_variable_value)
        configuration[env_variable] = env_variable_value
    return


def load_configuration():
    global configuration

    try:
        load_env_variable("SERVER_NAME")
        load_env_variable("REMOTE_REDIS_HOST")
        load_env_variable("REMOTE_REDIS_PORT")
        load_env_variable("REDIS_MAIN_DB")
        load_env_variable("SYSLOG_CACHE_PROCESS_INTERVAL")
        load_env_variable("SYSLOG_CACHE_DB_NES")
        load_env_variable("COMPRESSION_TYPE")
        load_env_variable("DASHBOARD_WEB_INTERFACE")
        load_env_variable("DASHBOARD_WEB_PORT")
        load_env_variable("PRIVATE_KEY")
        load_env_variable("SEVERITY_TO_RETURN")
        load_env_variable("DASHBOARD_SHOW_HOURS")
        load_env_variable("DASHBOARD_ZOOM_HOURS")
        load_env_variable("DASHBOARD_DATA_REFRESH_SECONDS")
        load_env_variable("ENDPOINT_SYSLOG_TRANSMISSION_INTERVAL_SECONDS")
        load_env_variable("SEVERITY_PATTERN")
    except Exception:
        print(DASH_LINE)
        print("ERROR: Enviroment variable is not available.")
        print(DASH_LINE)
        raise


def redis_connect(redis, database):
    global configuration
    redis_connection = redis.Redis(
        host=configuration["REMOTE_REDIS_HOST"],
        port=configuration["REMOTE_REDIS_PORT"],
        db=database)
    return redis_connection


def decode_syslog_pri(pos):
    line = int(pos)
    if line < 192:
        facility = PRI[line][0]
        severity = PRI[line][1]
    else:
        facility = 999
        severity = 99
    return facility, severity


def syslog_cache_processor(redis_syslog_cache, redis_main_db):

    global data_record_template
    global date_key
    data = np.array([])
    dt = []
    ip = []
    endpoint = []
    raw_message = []

    data_block = data_record_template

    cache_entries_count = redis_syslog_cache.llen("raw_message_block")

    redis_syslog_cache_pipeline = redis_syslog_cache.pipeline()
    for count in range(cache_entries_count):
        redis_syslog_cache_pipeline.lpop("raw_message_block")

    for compressed_data in redis_syslog_cache_pipeline.execute():
        decompressed_data = zlib.decompress(bytearray(compressed_data))
        data = msgpack.unpackb(decompressed_data, raw=False)
        for entry in data:
            dt += entry['dt']
            ip += entry['ip']
            endpoint += entry['endpoint']
            raw_message += entry['raw_message']

    for index in range(len(dt)):
        if raw_message[index].startswith("<"):
            facility, severity = decode_syslog_pri(
                raw_message[index].split(">", 1)[0].strip("<"))

        timestamp = re.search(
            r"[A-Z][a-z]{2}\s{1,2}\d{1,2}(?:\s\d{4})?\s\d{2}[:]\d{2}[:]\d{2}(?:\.\d{1,6})?(?:\s[A-Z]{3})?",
            raw_message[index].split(">", 1)[1],
        ).group()

        right_part_of_the_raw_message = raw_message[index].split(
            ">", 1)[1].replace(timestamp, '')
        try:
            system, message = right_part_of_the_raw_message.split(": ", 1)
        except ValueError:
            system = right_part_of_the_raw_message
            message = ""

        new_date_key = dt[index][:16]

        if date_key == "":
            date_key = new_date_key

        if new_date_key != date_key:

            for date_index in range(len(data_block["dt"])):
                severity_key = "sev" + str(data_block["severity"][date_index])
                redis_main_db.rpush(severity_key, data_block["dt"][date_index])

            data_packed = msgpack.packb(
                [data_block], use_bin_type=True)
            data_compressed = zlib.compress(
                data_packed, configuration["COMPRESSION_TYPE"])
            redis_main_db.rpush(date_key, data_compressed)

            date_key = new_date_key
            data_block["n"].clear()
            data_block["dt"].clear()
            data_block["endpoint"].clear()
            data_block["severity"].clear()
            data_block["facility"].clear()
            data_block["ip"].clear()
            data_block["system"].clear()
            data_block["timestamp"].clear()
            data_block["event"].clear()

        data_block["dt"].append(dt[index])
        data_block["endpoint"].append(endpoint[index])
        data_block["severity"].append(severity)
        data_block["facility"].append(facility)
        data_block["ip"].append(ip[index])
        data_block["system"].append(system)
        data_block["timestamp"].append(timestamp)
        data_block["event"].append(message)
    calculate_statistic(redis_main_db)
    return


def available_severity_keys(redis_connection):
    severity_keys = redis_connection.keys(configuration["SEVERITY_PATTERN"])
    severity_keys.sort()
    return severity_keys


def calculate_statistic(redis_connection):
    messages_by_severity = [0, 0, 0, 0, 0, 0, 0, 0]
    severity_keys = available_severity_keys(redis_connection)
    for severity_key in severity_keys:
        severity_key = severity_key.decode('UTF-8')
        array_position = int(severity_key.replace('sev', '').strip())
        messages_by_severity[array_position] = redis_connection.llen(
            severity_key)
    print(" Messages by severity (1-8):" + str(messages_by_severity) +
          " Total messages: " + str(sum(messages_by_severity)),
          end="\r", flush=True)
    return


def decode_bytes(item):
    return item.decode('UTF-8')


def truncate_timestamp(item):
    return item[:16]


def truncate_timestamp_for_chart(item):
    return (item[:15] + "0")


def respond_to_dashboard_data_request(redis_connection):

    global configuration

    dashboard = {}
    timeline = []

    severity_keys = available_severity_keys(redis_connection)
    for severity_key in severity_keys:
        severity_key = severity_key.decode('UTF-8')
        timeline += redis_connection.lrange(severity_key, 0, -1)

    dashboard["total_events"] = len(timeline)

    if timeline:
        timeline.sort()

        dashboard["firstDataTimestamp"] = timeline[0].decode('UTF-8')
        dashboard["lastDataTimestamp"] = timeline[-1].decode('UTF-8')

        dashboard["timeline"] = []
        dashboard["timeline_events"] = []

        start_date = dateutil.parser.parse(
            dashboard["firstDataTimestamp"])
        end_date = dateutil.parser.parse(dashboard["lastDataTimestamp"])

        for severity in range(len(SEVERITY_CODE)):
            sev_key = "sev" + str(severity)
            dashboard["chartDatasev" + str(severity)] = {
                "name": SEVERITY_CODE[severity],
                "data": []
            }

            dashboard[sev_key] = redis_connection.llen(sev_key)

            sev_key_dt = list(
                map(decode_bytes, (redis_connection.lrange(sev_key, 0, -1))))

            axisX, axisY = np.unique(
                list(map(truncate_timestamp_for_chart, sev_key_dt)), return_counts=True)

            dashboard["chartData" +
                      sev_key]["data"] = dict(zip(axisX, axisY.astype(str)))

        delta = (dateutil.parser.parse(
            dashboard["lastDataTimestamp"]) -
            dateutil.parser.parse(dashboard["firstDataTimestamp"]))

        if dashboard["total_events"] > 0:
            dashboard["messages_per_second"] = round(
                (dashboard["total_events"] / delta.total_seconds()), 2
            )
            dashboard["seconds_between_messages"] = round(
                (delta.total_seconds() / dashboard["total_events"]), 2
            )
        else:
            dashboard["messages_per_second"] = 0
            dashboard["seconds_between_messages"] = 0

    redis_config = redis_connection.info("memory")

    dashboard["redis_used_memory_human"] = redis_config["used_memory_human"]
    dashboard["redis_used_memory"] = redis_config["used_memory"]
    dashboard["redis_total_system_memory_human"] = redis_config[
        "total_system_memory_human"
    ]
    dashboard["redis_total_system_memory"] = redis_config[
        "total_system_memory"
    ]
    dashboard["configuration"] = configuration

    return json.dumps(dashboard)


def prepare_keys(item):
    item = item.decode('UTF-8')
    item = item.replace("sev", '').strip()
    return item


def respond_to_events_data_request(redis_connection, events_to_return, mode):

    global configuration
    dt = np.array([])
    endpoint = np.array([])
    severity = np.array([])
    facility = np.array([])
    ip = np.array([])
    system = np.array([])
    time = np.array([])
    event = np.array([])

    timeline = np.array([])
    timestamps = np.array([])

    if events_to_return == "alerts":
        severity_to_return = configuration['SEVERITY_TO_RETURN'].split()
    if events_to_return == "all":
        severity_keys = available_severity_keys(redis_connection)
        severity_to_return = list(map(prepare_keys, severity_keys))

    severity_to_return.sort()

    for severity_key in severity_to_return:
        severity_key_str = 'sev' + str(severity_key)
        timeline = np.concatenate((timeline, np.array(list(
            map(decode_bytes, (redis_connection.lrange(severity_key_str, 0, -1)))))), axis=0)

    timeline.sort()

    timestamps = list(map(truncate_timestamp, timeline))
    timestamps = np.unique(timestamps)

    redis_pipeline = redis_connection.pipeline()
    for timestamp in timestamps:
        redis_pipeline.lrange(timestamp, 0, -1)

    for zipped_data in redis_pipeline.execute():
        if len(zipped_data) > 0:
            data = (msgpack.unpackb(
                zlib.decompress(zipped_data[0]), raw=False))[0]
            dt = np.concatenate((dt, np.array(data['dt'])), axis=0)
            endpoint = np.concatenate(
                (endpoint, np.array(data["endpoint"])), axis=0)
            severity = np.concatenate(
                (severity, np.array(data["severity"])), axis=0)
            facility = np.concatenate(
                (facility, np.array(data["facility"])), axis=0)
            ip = np.concatenate((ip, np.array(data["ip"])), axis=0)
            system = np.concatenate((system, np.array(data["system"])), axis=0)
            time = np.concatenate(
                (time, np.array(list(data["timestamp"]))), axis=0)
            event = np.concatenate((event, np.array(data["event"])), axis=0)
    if events_to_return == "alerts":
        for index in range((len(severity)-1), -1, -1):
            if str(int(severity[index])) not in severity_to_return:
                dt = np.delete(dt, index)
                endpoint = np.delete(endpoint, [index])
                severity = np.delete(severity, [index])
                facility = np.delete(facility, [index])
                ip = np.delete(ip, [index])
                system = np.delete(system, [index])
                time = np.delete(time, [index])
                event = np.delete(event, [index])

    if mode == "json":
        num = []
        for n in range(len(dt)):
            num.append(str(n))

        data_to_return = {
            "n": list(num),
            "dt": list(dt),
            "endpoint": list(endpoint),
            "severity": list(severity),
            "facility": list(facility.astype(int).astype(str)),
            "ip": list(ip),
            "system": list(system),
            "timestamp": list(time),
            "event": list(event)
        }
        return (json.dumps(data_to_return))

    if mode == "csv":
        csv_dataset = tablib.Dataset()

        csv_dataset.append_col(list(dt), header='dt')
        csv_dataset.append_col(list(endpoint), header='endpoint')
        csv_dataset.append_col(list(severity), header='severity')
        csv_dataset.append_col(list(facility), header='facility')
        csv_dataset.append_col(list(ip), header='ip')
        csv_dataset.append_col(list(system), header='system')
        csv_dataset.append_col(list(time), header='timestamp')
        csv_dataset.append_col(list(event), header='event')

        return csv_dataset.export('csv')


nserv = Klein()


class NotFound(Exception):
    pass


def enable_cors(request):
    request.responseHeaders.addRawHeader("Access-Control-Allow-Origin", "*")
    request.responseHeaders.addRawHeader("Access-Control-Allow-Methods",
                                         "PUT, GET, POST, DELETE, OPTIONS")
    request.responseHeaders.addRawHeader(
        "Access-Control-Allow-Headers",
        "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token",
    )
    return request


@nserv.route("/", methods=["GET"])
def root(request):
    index_file = ""
    index_file_handler = open("build/index.html", "r")
    for readIndexLine in index_file_handler:
        index_file += readIndexLine
    index_file_handler.close()
    return index_file


@nserv.route("/static/img/", branch=True)
def img(request):
    return File("build/static/img/")


@nserv.route("/static/", branch=True)
def static(request):
    return File("build/static/")


@nserv.route("/server_data")
def server_data_req(request):
    request = enable_cors(request)
    return respond_to_dashboard_data_request(redis_main_db)


@nserv.route("/server_events")
def server_events_req(request):
    request = enable_cors(request)
    return respond_to_events_data_request(redis_main_db, "alerts", "json")


@nserv.route("/csv_alerts", branch=True)
def export_csv_alerts(request):
    request.responseHeaders.addRawHeader(
        b"content-type", b"application/csv")
    request.responseHeaders.addRawHeader(b"content-disposition", b"attachment")
    content = respond_to_events_data_request(redis_main_db, "alerts", "csv")
    return content


@nserv.route("/csv_all", branch=True)
def export_csv_all(request):
    request.responseHeaders.addRawHeader(
        b"content-type", b"application/csv")
    request.responseHeaders.addRawHeader(b"content-disposition", b"attachment")
    content = respond_to_events_data_request(redis_main_db, "all", "csv")
    return content


@nserv.route("/json_alerts", branch=True)
def export_json_alerts(request):
    request.responseHeaders.addRawHeader(b"content-type", b"application/json")
    content = respond_to_events_data_request(redis_main_db, "alerts", "json")
    return content


@nserv.route("/json_all", branch=True)
def export_json_all(request):
    request.responseHeaders.addRawHeader(b"content-type", b"application/json")
    content = respond_to_events_data_request(redis_main_db, "all", "json")
    return content


@nserv.handle_errors(NotFound)
@nserv.handle_errors(FileNotFoundError)
def error(self, request):
    # request.setResponseCode(404)
    error_file = ""
    error_file_handler = open("build/error.html", "r")
    for readErrorLine in error_file_handler:
        error_file += readErrorLine
    error_file_handler.close()
    return error_file


def main_server_loop_failed(failure):
    print("ERROR - main server loop failed:")
    print(DASH_LINE)
    print(failure.getBriefTraceback())
    reactor.stop()


resource = nserv.resource

if __name__ == "__main__":
    try:
        load_configuration()

        try:

            display_console_banner()

            redis_syslog_cache = redis_connect(
                redis, configuration['SYSLOG_CACHE_DB_NES'])
            redis_main_db = redis_connect(redis,
                                          configuration["REDIS_MAIN_DB"])
            connected_to_redis = True
            print(DASH_LINE)
            print(" Connected to Redis.")

        except redis.ConnectionError:

            connected_to_redis = False

            print(DASH_LINE)
            print("Error - check configuration or status of the Redis server.")
            print(DASH_LINE)

        if connected_to_redis:

            # endpoint_description = (
            #     "tcp:port=" + str(configuration["DASHBOARD_WEB_PORT"]) +
            #     ":interface=" + configuration["DASHBOARD_WEB_INTERFACE"])

            endpoint_description = (
                "ssl:" + str(configuration["DASHBOARD_WEB_PORT"]) +
                ":interface=" + configuration["DASHBOARD_WEB_INTERFACE"] +
                ":privateKey="+configuration["PRIVATE_KEY"])

            endpoint = endpoints.serverFromString(reactor,
                                                  endpoint_description)
            endpoint.listen(Site(nserv.resource()))

            syslog_cache_processor_task = task.LoopingCall(
                syslog_cache_processor, redis_syslog_cache, redis_main_db)

            main_server_processor_loop = syslog_cache_processor_task.start(
                configuration["SYSLOG_CACHE_PROCESS_INTERVAL"])

            main_server_processor_loop.addErrback(main_server_loop_failed)

            reactor.run()

    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print("Shutting down server...")
        redis_main_db.quit()
        redis_syslog_cache.quit()
        reactor.callFromThread(reactor.stop)
        # reactor.stop
        print("done.")
