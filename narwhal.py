from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import endpoints, reactor, task
from pri import PRI

import datetime
import os
import re
import socket
import time

import dateutil.parser
import msgpack
import numpy as np
# import orjson
import json
import redis
import tablib
import zstd
from klein import Klein

VERSION = "0.2"
DASH_LINE = "-----------------------------------------------------------------"

configuration = {
    "SERVER_NAME": "Narwhal",
    "REMOTE_REDIS_HOST": "192.168.1.14",
    "REMOTE_REDIS_PORT": 6379,
    "REDIS_MAIN_DB": 0,
    "SYSLOG_CACHE_PROCESS_INTERVAL": 2,
    "SYSLOG_CACHE_DB_NES": 1,
    "COMPRESSION_TYPE": 3,
    "DASHBOARD_WEB_INTERFACE": "0.0.0.0",
    "DASHBOARD_WEB_PORT": 3000,
    "PRIVATE_KEY": "localhost.pem",
    "SEVERITY_TO_RETURN": "0 1 2 3",
    "DASHBOARD_SHOW_HOURS": 4,
    "DASHBOARD_DATA_REFRESH_SECONDS": 3,
    "ENDPOINT_SYSLOG_TRANSMISSION_INTERVAL_SECONDS": 1,
    "SEVERITY_PATTERN": "sev*"
}

LOG_MESSAGE_START = "Narwhal server started"
LOG_MESSAGE_STOP = "Narwhal server stopped"

# RFC 5424
SEVERITY_CODE = [
    "emerg",
    "alert",
    "crit",
    "err",
    "warning",
    "notice",
    "info",
    "debug"
]

redis_main_db = ""
narwhal_log_facility = []
chart_severity = 0


def display_console_banner():

    base_url = "https://" + \
        configuration["DASHBOARD_WEB_INTERFACE"] + ":" + \
        str(configuration["DASHBOARD_WEB_PORT"])

    print(DASH_LINE)
    print("    _  __                __        __ ")
    print("   / |/ /__ ______    __/ /  ___ _/ / ")
    print("  /    / _ `/ __/ |/|/ / _ \/ _ `/ /  ")
    print(" /_/|_/\_,_/_/  |__,__/_//_/\_,_/_/    server v." + VERSION)
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


def narwhal_log(message):
    global narwhal_log_facility
    global configuration
    ip = socket.gethostbyname(socket.gethostname())
    narwhal_log_facility.append(
        [
            datetime.datetime.now().replace(microsecond=0).isoformat(),
            ip,
            5,
            16,
            ip,
            configuration['SERVER_NAME'],
            datetime.datetime.utcnow().isoformat(),
            message
        ])


def syslog_cache_processor(redis_syslog_cache, redis_main_db):

    global narwhal_log_facility

    date_field = ""
    redis_cache_data = np.array([])
    dt = []
    ip = []
    endpoint = []
    raw_message = []
    redis_data = []
    data = np.empty([8])
    data_to_redis = []

    cache_stored_keys = list(map(
        decode_bytes, (redis_syslog_cache.hkeys("raw_message_block"))))

    redis_syslog_cache_pipeline = redis_syslog_cache.pipeline()
    for key in cache_stored_keys:
        redis_syslog_cache_pipeline.hget("raw_message_block", key)

    for compressed_data in redis_syslog_cache_pipeline.execute():
        decompressed_data = zstd.decompress(compressed_data)
        redis_cache_data = msgpack.unpackb(decompressed_data, raw=False)
        for entry in redis_cache_data:
            ip += entry['ip']
            endpoint += entry['ep']
            raw_message += entry['ms']

    for key in cache_stored_keys:
        redis_syslog_cache_pipeline.hdel("raw_message_block", key)

    redis_syslog_cache_pipeline.execute()

    for index in range(len(raw_message)):
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
            system, message = right_part_of_the_raw_message.split(
                ": ", 1)
        except ValueError:
            system = str(right_part_of_the_raw_message)
            message = ""

        new_date_field = timestamp[:16]
        if date_field == "":
            date_field = new_date_field

        if new_date_field != date_field:
            data = np.reshape(data, (-1, 8))
            redis_main_db_pipeline = redis_main_db.pipeline()

            for severity_key in range(8):
                for index in range(len(data)):
                    if (data[index][2] == str(severity_key)):
                        data_to_redis.append(data[index].tolist())

                if data_to_redis:
                    data_compressed = zstd.compress(
                        msgpack.packb(data_to_redis),
                        configuration['COMPRESSION_TYPE'])
                    compressed_records_count = len(data_to_redis)

                    redis_main_db_pipeline.hset(
                        severity_key, date_field, data_compressed)
                    redis_main_db_pipeline.hincrby(
                        severity_key, 'total', compressed_records_count)
                    keys_to_score = {date_field:  compressed_records_count}
                    redis_main_db_pipeline.zadd(
                        (str(severity_key) + "T"), keys_to_score)
                    data_to_redis = []

            redis_main_db_pipeline.execute()
            date_field = new_date_field
            data = np.empty([8])

        data_row = np.array([timestamp[:16],
                             endpoint[index],
                             severity,
                             facility,
                             ip[index],
                             system,
                             timestamp,
                             message])
        data = np.concatenate((data, data_row), axis=0)

    if narwhal_log_facility:
        for log_row in narwhal_log_facility:
            data = np.concatenate((data, log_row), axis=0)
        narwhal_log_facility.clear()

    calculate_statistic(redis_main_db)
    return


def available_severity_keys(redis_connection):

    severity_keys = []
    redis_pipeline = redis_connection.pipeline()
    for index in range(7):
        redis_pipeline.exists(str(index))
    sev_key = 0
    for item in redis_pipeline.execute():
        if item:
            severity_keys.append(str(sev_key))
        sev_key += 1
    return severity_keys


def calculate_statistic(redis_connection):
    messages_by_severity = [0, 0, 0, 0, 0, 0, 0, 0]
    severity_keys = available_severity_keys(redis_connection)
    for severity_key in severity_keys:
        messages_by_severity[int(severity_key)] = int((redis_connection.hget(
            severity_key, 'total')).decode('UTF-8'))
    print(" Messages by severity (1-8):" + str(messages_by_severity) +
          " Total messages: " + str(sum(messages_by_severity)),
          end="\r", flush=True)
    return


def decode_bytes(item):
    return item.decode('UTF-8')


def truncate_timestamp(item):
    return item.decode('UTF-8')[:16]


def truncate_timestamp_for_chart(item):
    return (item[:15] + "0")


def prepare_chart_data(item):
    global chart_severity
    return({"x": item[0].decode('UTF-8'), "y": chart_severity, "z": item[1].decode('UTF-8')})


def prepare_timeline(item):
    return(item[0].decode('UTF-8'))


def respond_to_dashboard_data_request(redis_connection):

    global chart_severity

    dashboard = {}
    dashboard['ChartData0'] = []
    dashboard['ChartData1'] = []
    dashboard['ChartData2'] = []
    dashboard['ChartData3'] = []
    dashboard['ChartData4'] = []
    dashboard['ChartData5'] = []
    dashboard['ChartData6'] = []
    dashboard['ChartData7'] = []
    timeline = []
    events = []
    messages_by_severity = [0, 0, 0, 0, 0, 0, 0, 0]

    severity_keys = available_severity_keys(redis_connection)
    for severity_key in severity_keys:
        chart_severity = severity_key
        events = redis_connection.zrange(
            (str(severity_key)+"T"), 0, -1, withscores=True)
        events = np.atleast_2d(events)
        dashboard[('ChartData' + str(severity_key))
                  ] = list(map(prepare_chart_data, events))
        timeline += list(map(prepare_timeline, events))

        messages_by_severity[int(severity_key)] = int((redis_connection.hget(
            severity_key, "total")).decode('UTF-8'))

    # timeline = np.reshape(timeline, (-1, 2))
    timeline.sort()

    first_timestamp = timeline[0]
    last_timestamp = timeline[-1]

    dashboard["total_events"] = sum(messages_by_severity)
    dashboard["messages_per_second"] = 0
    dashboard["seconds_between_messages"] = 0

    # sev_key = []
    # for severity in range(len(SEVERITY_CODE)):
    # sev_key += SEVERITY_CODE[severity]

    delta = (dateutil.parser.parse(
        last_timestamp) -
        dateutil.parser.parse(first_timestamp))

    dashboard["messages_per_second"] = round(
        (dashboard["total_events"] / delta.total_seconds()), 2
    )
    dashboard["seconds_between_messages"] = round(
        (delta.total_seconds() / dashboard["total_events"]), 2
    )

    dashboard["logAlertCount"] = messages_by_severity[0] + \
        messages_by_severity[1] + \
        messages_by_severity[2] + messages_by_severity[3]
    dashboard["logWarningsCount"] = messages_by_severity[4]
    dashboard["logMessageCount"] = messages_by_severity[5] + \
        messages_by_severity[6] + messages_by_severity[7]

    redis_config = redis_connection.info("memory")

    dashboard["redis_used_memory_human"] = redis_config["used_memory_human"]
    dashboard["redis_used_memory"] = redis_config["used_memory"]
    dashboard["redis_total_system_memory_human"] = redis_config[
        "total_system_memory_human"
    ]
    dashboard["redis_total_system_memory"] = redis_config[
        "total_system_memory"
    ]
    return json.dumps(dashboard)


def respond_to_events_data_request(redis_connection, events_to_return, mode):

    global configuration
    dt = []
    endpoint = []
    severity = []
    facility = []
    ip = []
    system = []
    time = []
    event = []

    timeline = np.array([])
    timestamps = np.array([])

    if events_to_return == "alerts":
        severity_to_return = configuration['SEVERITY_TO_RETURN'].split()
    if events_to_return == "all":
        severity_to_return = list(available_severity_keys(redis_connection))

    redis_pipeline = redis_connection.pipeline()

    for severity_key in severity_to_return:
        if events_to_return == "alerts":
            severity_key = (str(severity_key))
        redis_pipeline.hgetall(severity_key)

    for redis_data in redis_pipeline.execute():
        if redis_data:
            redis_data_keys = redis_data.keys()
            for key in redis_data_keys:
                if key.decode() != "total":
                    data_block = np.reshape(
                        (msgpack.unpackb(zstd.decompress(redis_data[key]))),
                        (-1, 8))
                    for data in data_block:
                        dt.append(data[0].decode())
                        endpoint.append(data[1].decode())
                        severity.append(data[2].decode())
                        facility.append(data[3].decode())
                        ip.append(data[4].decode())
                        system.append(data[5].decode())
                        time.append(data[6].decode())
                        event.append(data[7].decode())

    if mode == "json":
        num = [str(n) for n in range(np.count_nonzero(dt))]
        return (json.dumps({
            "n": list(num),
            "dt": dt,
            "endpoint": endpoint,
            "severity": severity,
            "facility": facility,
            "ip": ip,
            "system": system,
            "timestamp": time,
            "event": event
        }))

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


@nserv.route("/")
def root(request):
    index_file = ""
    index_file_handler = open("build/index.html", "r")
    for readIndexLine in index_file_handler:
        index_file += readIndexLine
    index_file_handler.close()
    return index_file


@nserv.route("/manifest.json")
def static(request):
    manifest_file = ""
    manifest_file_handler = open("build/manifest.json", "r")
    for readIndexLine in manifest_file_handler:
        manifest_file += readIndexLine
    manifest_file_handler.close()
    return manifest_file


@nserv.route("/static/", branch=True)
def static(request):
    return File("build/static/")


@nserv.route("/static/img/", branch=True)
def img(request):
    return File("build/static/img/")


@nserv.route("/dashboard", branch=True)
def return_dashboard_data(request):
    request = enable_cors(request)

    dashboard = respond_to_dashboard_data_request(redis_main_db)
    data = respond_to_events_data_request(redis_main_db, "alerts", "json")
    jsonMerged = {**json.loads(dashboard), **json.loads(data)}
    return json.dumps(jsonMerged)


@nserv.route("/server_data")
def server_data_req(request):
    request = enable_cors(request)
    # return respond_to_dashboard_data_request(redis_main_db)
    return respond_to_events_data_request(redis_main_db, "all", "json")

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
            print("Connected to Redis.")

        except redis.ConnectionError:

            connected_to_redis = False

            print(DASH_LINE)
            print("Error - check configuration or status of the Redis server.")
            print(DASH_LINE)

        if connected_to_redis:

            narwhal_log(LOG_MESSAGE_START)

            print("Processing cache...")
            start_time = time.time()
            syslog_cache_processor(redis_syslog_cache, redis_main_db)
            print("Processed cache on server start in %s seconds.             " %
                  round(time.time() - start_time))

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

            # reactor.suggestThreadPoolSize(30)
            reactor.run()

    except (IOError, SystemExit):

        raise
    except KeyboardInterrupt:
        narwhal_log(LOG_MESSAGE_STOP)
        print("Shutting down server...")
        syslog_cache_processor(redis_syslog_cache, redis_main_db)
        reactor.callFromThread(reactor.stop)
        # reactor.stop
        print("done.")
