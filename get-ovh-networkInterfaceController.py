#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
import ovh
from time import sleep
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from dataclasses import dataclass
from dotenv import dotenv_values
import logging

def main():
    mrtg_types=['traffic:download','traffic:upload', 'errors:upload', 'errors:download', 'packets:upload','packets:download']
    config=dotenv_values(".env")

    client = ovh.Client(
        endpoint='ovh-eu',               # Endpoint of API OVH Europe (List of available endpoints)
        application_key=config['APP_KEY'],    # Application Key
        application_secret=config['APP_SECRET'], # Application Secret
        consumer_key=config['CONSUMER_KEY'],       # Consumer Key
    )
    @dataclass
    class SERVER:
        name: str
        interfaces: list
    @dataclass
    class MEASUREMENT:
        server: str
        linktype: str
        mac: str
        timestamp: int
        value: float

    result = client.get('/dedicated/server')
    all_servers=[]
    for server in result:
        url= '/dedicated/server/'+server+'/networkInterfaceController'
        try: 
            list_of_macs=client.get(url)
        except:
            logging.warning('API Error:'+ url)
        all_mac_details=[]
        for mac in list_of_macs:
            url= '/dedicated/server/'+server+'/networkInterfaceController/'+mac
            try:
                mac_details=client.get(url)
            except:
                logging.warning('API Error:'+ url)
            all_mac_details.append(mac_details)
            
        all_servers.append( SERVER( server , all_mac_details))

    for i in mrtg_types:
        result_list=[]
        for server in all_servers:
            for interface in server.interfaces :
                mac = interface['mac']
                url= "/dedicated/server/"+server.name+"/networkInterfaceController/"+mac+"/mrtg"
                try:
                     result2 = client.get(url, period="hourly", type=i,)
                except:
                    logging.warning('API Error'+i+url)
                    logging.warning(str(interface))
                    continue
                for j in result2:
                    try:
                        value= float(j['value']['value'])
                    except:
                        continue
                    result_list.append( MEASUREMENT( server=server.name, mac=mac,
                        timestamp= int(j['timestamp']),
                        value= float(j['value']['value']),
                        linktype=interface['linkType'] ))
        with InfluxDBClient.from_config_file("config.toml") as client:
            with client.write_api() as writer:
                logging.info('writing length:', len(result_list))
                writer.write(
                    bucket='network-poll',
                    record=result_list,
                    record_measurement_name=i,
                    record_tag_keys=['server','mac','linktype'],
                    record_field_keys=['value'],
                    record_time_key='timestamp',
                    write_precision='s'
                )


if __name__ == '__main__':
    main()
