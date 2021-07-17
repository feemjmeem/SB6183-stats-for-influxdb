import configparser
import os
import sys
import argparse
from influxdb_client import InfluxDBClient, WriteApi, WriteOptions
import time
from datetime import datetime
from bs4 import BeautifulSoup
import requests

class configManager():

    def __init__(self, config):
        print('Loading Configuration File {}'.format(config))
        self.modem_url = []
        config_file = os.path.join(os.getcwd(), config)
        if os.path.isfile(config_file):
            self.config = configparser.ConfigParser()
            self.config.read(config_file)
        else:
            print('ERROR: Unable To Load Config File: {}'.format(config_file))
            sys.exit(1)

        self._load_config_values()
        print('Configuration Successfully Loaded')

    def _load_config_values(self):

        # General
        self.delay = self.config['GENERAL'].getint('Delay', fallback=2)
        self.output = self.config['GENERAL'].getboolean('Output', fallback=True)

        # InfluxDB
        self.influx_url = self.config['INFLUXDB'].get('URL', fallback='http://localhost:8086')
        self.influx_bucket = self.config['INFLUXDB'].get('Bucket', fallback='cable_modem_stats')
        self.influx_org = self.config['INFLUXDB'].get('Org')
        self.influx_token = self.config['INFLUXDB'].get('Token')
        self.influx_verify_ssl = self.config['INFLUXDB'].getboolean('Verify_SSL', fallback='True')

        # Cable Modem
        self.modem_url = self.config['MODEM'].get('URL', fallback='http://192.168.100.1/RgConnect.asp')

class InfluxdbModem():

    def __init__(self, config=None):

        self.config = configManager(config=config)
        self.output = self.config.output
        self.influx_client = InfluxDBClient(
            url=self.config.influx_url,
            token=self.config.influx_token,
            org=self.config.influx_org,
            verify_ssl=self.config.influx_verify_ssl
        )
        self.influx_write = self.influx_client.write_api()
        self.modem_url = self.config.modem_url

    def parse_modem(self):

        print('Getting modem stats')
        try:
            resp = requests.get(self.modem_url)
            status_html = resp.content
            resp.close()
            soup = BeautifulSoup(status_html, 'html.parser')
        except Exception as e:
            print('ERROR: Failed to get modem stats.  Aborting')
            print(e)
            sys.exit(1)

        series = []
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        # downstream table
        for table_row in soup.find_all("table")[2].find_all("tr")[2:]:
            if table_row.th:
                continue
            channel = table_row.find_all('td')[0].text.strip()
            channel_id = table_row.find_all('td')[3].text.strip()
            frequency = table_row.find_all('td')[4].text.replace(" Hz", "").strip()
            power = table_row.find_all('td')[5].text.replace(" dBmV", "").strip()
            snr = table_row.find_all('td')[6].text.replace(" dB", "").strip()
            corrected = table_row.find_all('td')[7].text.strip()
            uncorrectables = table_row.find_all('td')[8].text.strip()

            downstream_result_dict = {
                'measurement': 'downstream_statistics',
                'time': current_time,
                'fields': {
                    'channel_id': int(channel_id),
                    'frequency': int(frequency),
                    'power': float(power),
                    'snr': float(snr),
                    'corrected': int(corrected),
                    'uncorrectables': int(uncorrectables)
                },
                'tags': {
                    'channel': int(channel)
                }
            }
 
            series.append(downstream_result_dict)


            # if self.output:
            #     print("channel:{},channel_id:{},frequency:{},power:{},snr:{},corrected:{},uncorrectables:{}".format(channel, channel_id, frequency, power, snr, corrected, uncorrectables))

        # upstream table
        for table_row in soup.find_all("table")[3].find_all("tr")[2:]:
            if table_row.th:
                continue
            channel = table_row.find_all('td')[0].text.strip()
            channel_id = table_row.find_all('td')[3].text.strip()
            frequency = table_row.find_all('td')[5].text.replace(" Hz", "").strip()
            power = table_row.find_all('td')[6].text.replace(" dBmV", "").strip()

            upstream_result_dict = {
                'measurement': 'upstream_statistics',
                'time': current_time,
                'fields': {
                    'channel_id': int(channel_id),
                    'frequency': int(frequency),
                    'power': float(power),
                    'snr': float(snr)
                },
                'tags': {
                    'channel': int(channel)
                }
            }

            series.append(upstream_result_dict)

            # if self.output:
            #     print("channel:{},channel_id:{},frequency:{},snr:{}".format(channel, channel_id, frequency, snr))

        self.write_influx_data(series)

    def run(self):
        while True:
            self.parse_modem()
            print("sleeping  {}s".format(self.config.delay))
            sys.stdout.flush()
            time.sleep(self.config.delay)

    def write_influx_data(self, json_data):
        """
        Writes the provided JSON to the database
        :param json_data:
        :return:
        """
        # if self.output:
        #     print(json_data)
        
        self.influx_write.write(self.config.influx_bucket, self.config.influx_org, json_data)
        
def main():

    parser = argparse.ArgumentParser(description="A tool to send modem stats statistics to InfluxDB")
    parser.add_argument('--config', default='config.ini', dest='config', help='Specify a custom location for the config file')
    args = parser.parse_args()
    collector = InfluxdbModem(config=args.config)
    collector.run()

if __name__ == '__main__':
    main()