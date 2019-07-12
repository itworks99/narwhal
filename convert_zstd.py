import zlib
import zstd
import redis
import numpy as np

configuration = {
    "REMOTE_REDIS_HOST": "192.168.1.14",
    "REMOTE_REDIS_PORT": 6379,
    "REDIS_MAIN_DB": 0,
    "SEVERITY_PATTERN": "sev*"
}


def truncate_timestamp(item):
    return item[:16]


def redis_connect(redis, database):
    global configuration
    redis_connection = redis.Redis(
        host=configuration["REMOTE_REDIS_HOST"],
        port=configuration["REMOTE_REDIS_PORT"],
        db=database)
    return redis_connection


def prepare_keys(item):
    item = item.decode('UTF-8')
    item = item.replace("sev", '').strip()
    return item


def decode_bytes(item):
    return item.decode('UTF-8')


redis_main_db = redis_connect(redis, configuration["REDIS_MAIN_DB"])
connected_to_redis = True
print(" Connected to Redis.Starting conversion")

timeline = np.array([])
timestamps = np.array([])

severity_to_return = list(
    map(prepare_keys, (redis_main_db.keys(configuration["SEVERITY_PATTERN"]))))
severity_to_return.sort()

for severity_key in severity_to_return:
    timeline = np.concatenate((timeline, np.array(list(map(
        decode_bytes, (redis_main_db.lrange(('sev' + str(severity_key)), 0, -1)))))), axis=0)

timeline = np.sort(timeline, axis=None)
timestamps = np.unique(list(map(truncate_timestamp, timeline)))

for timestamp in timestamps:
    zipped_data = redis_main_db.lpop(timestamp)
    if zipped_data:
        data = zlib.decompress(bytearray(zipped_data))
        zstd_data = zstd.compress(data, 3)
        redis_main_db.rpush(timestamp, zstd_data)

redis_main_db.quit()
