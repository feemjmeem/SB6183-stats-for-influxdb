# SB6183 Modem Stats emitted to Influxdb running as a Docker container

![Screenshot](https://i.imgur.com/wQnXPxU.png)

This tool is a parser of the Arris SB6183 cable modem to emit signal & power metrics to InfluxDB, modified from the original by @billimek.

Note: This fork has been modified to use InfluxDB 2. A telegraf configuration file is also included for outbound ping tests to correlate with modem issues. There is currently no error handling, so if your modem goes offline or is rebooted frequently, you will need to schedule this docker container to automatically restart.

## Grafana dashboard example
See this [example json](sb6183-modem-stats.json) for a grafana dashboard as shown in the screenshot above.
You will also need to set up the data sources in grafana as `cable_modem` and `ping` for this script and the telegraf config respectively.

## Configuration within config.ini

#### GENERAL
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|Delay          |Delay between runs                                                                                                  |
|Output         |Write console output while tool is running (deprecated, TODO: fix)                                                  |
#### INFLUXDB
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|URL            |InfluxDB URL (e.g. `http://192.168.0.50:8086`)                                                                      |
|Bucket         |Bucket to write collected stats to                                                                                  |
|Org            |InfluxDB organization                                                                                               |
|Token          |Token providing write access to the bucket                                                                          |
#### MODEM
|Key            |Description                                                                                                         |
|:--------------|:-------------------------------------------------------------------------------------------------------------------|
|URL            |URL of the cable modem info page.  Leave blank for http://192.168.100.1/RgConnect.asp                               |

## Usage

If running from console, before the first use run `pip3 install -r requirements.txt` or `pipenv install`

Enter your desired information in config.ini and run SB6183.py

Optionally, you can specify the --config argument to load the config file from a different location.  

***Requirements***

Python 3+ (tested on Python 3.9)

You will need the influxdb2 client library installed to use this - [Found Here](https://github.com/influxdata/influxdb-client-python)

## Docker Setup

1. Install [Docker](https://www.docker.com/)

2. Clone this repository.
```bash
git clone https://github.com/feemjmeem/SB6183-stats-for-influxdb.git
```

3. Modify `config.ini` file with your influxdb settings.

```bash
vim config.ini
```

4. Modify the 'URL =' line include the URL to your InfluxDB instance.
Example:

```bash
URL = http://192.168.0.50:8086
```

5. Build and run the container from the directory into which you cloned the repository.

```bash
docker build .
docker run sb6183
```