# Narwhal

A simple syslog server created for cloud and remote deployments where amount of traffic and storage are precious. Still in development.

## Features

- Adjustable data compression based on [zstd real-time compression algorithm](https://facebook.github.io/zstd/)
- Adjustable data transmission periods
- Export of the selected alert categories as JSON endpoints / CSV files
- Simple web dashboard

## Screenshot

TBA

## Installation and configuration

                                +------------------------+          +-------------+
                                | Narwhal endpoint       | +------> |             |
      Syslog data  +----------> | UDP:514                |          |             |
                                |                        | <------+ |             |
                                |------------------------|          |    Redis    |
                                                                    |             |
                                +------------------------+          |             |
                                |                        | +------> |             |
                                | Narwhal server         |          |             |
                                | dashboard at HTTPS:3000| <------+ |             |
                                +------------------------+          +-------------+

### Installation

Start with

    docker run -d -it -p 3000:8080/tcp -e REMOTE_REDIS_HOST='xxx.xxx.xxx.xxx' itworks99/narwhal:latest

where REMOTE_REDIS_HOST value is an ip address of the Redis server.

### Configuration

You can configure desired settings through environment variables for server Docker container:

    "SERVER_NAME": "Narwhal"
    
    "REMOTE_REDIS_HOST" - the IP address of the remote redis host. 
    
    "REMOTE_REDIS_PORT" - remote redis server network port set by default to 6379

    "REDIS_MAIN_DB" - main redis database, by default 0
    
    "SYSLOG_CACHE_PROCESS_INTERVAL" - the amount of seconds between attempts to read and process compressed data cache in redis. It is set to 2 seconds by default.
    
    "SYSLOG_CACHE_DB_NES" - data cache redis database, by default 1
    
    "COMPRESSION_TYPE" - zstd compression type set by default to 3
    
    "DASHBOARD_WEB_INTERFACE": "0.0.0.0"
    
    "DASHBOARD_WEB_PORT": 3000
    
    "PRIVATE_KEY" - private key file to sign https sessions. The default filename is "localhost.pem"
    
    "SEVERITY_TO_RETURN" - messages with severity codes that condsidered critical, the default setting is "0 1 2 3"
    
    "DASHBOARD_SHOW_HOURS" - last X hours to display on web dashboard. The default value is 4 hours.
    
    "DASHBOARD_DATA_REFRESH_SECONDS" - web dashboard data refresh interval.  The default value is 3 seconds.
    
    "ENDPOINT_SYSLOG_TRANSMISSION_INTERVAL_SECONDS" - data transmission interval between endpoint and redis server, 1 second by default.

### Web dashboard

TBA

### JSON endpoints

TBA

### Download data as CSV files

TBA
