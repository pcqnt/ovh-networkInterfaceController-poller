#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
import ovh
from time import sleep
from influxdb_client import InfluxDBClient
from influxdb_client.domain.write_precision import WritePrecision
from dataclasses import dataclass
from os import environ
import logging

def main():
    mrtg_types=['traffic:upload', 'traffic:download', 
        'errors:upload', 'errors:download', 
        'packets:upload','packets:download']
    #logging.basicConfig(level=logging.DEBUG)

    client_ovh = ovh.Client(
        endpoint='ovh-eu',               # Endpoint of API OVH Europe (List of available endpoints)
        application_key=environ['OVH_APP_KEY'],    # Application Key
        application_secret=environ['OVH_APP_SECRET'], # Application Secret
        consumer_key=environ['OVH_CONSUMER_KEY'],       # Consumer Key
    )
    @dataclass
    class INTERFACE:
        servername: str
        detail: dict
    @dataclass
    class MEASUREMENT:
        server: str
        linktype: str
        mac: str
        timestamp: int
        value: float
        measurement_type: str

    result = client_ovh.get('/dedicated/server')
    all_interfaces=[]
    for server in result:
        url= '/dedicated/server/'+server+'/networkInterfaceController'
        try: 
            list_of_macs=client_ovh.get(url)
        except:
            logging.warning('API Error:'+url)
        else:
            for mac in list_of_macs:
                url= '/dedicated/server/'+server+'/networkInterfaceController/'+mac
                try:
                    mac_details=client_ovh.get(url)
                except:
                    logging.warning('API Error :'+url)
                else:
                    all_interfaces.append(INTERFACE(servername=server,detail=mac_details))
    result_list=[]
    for i in mrtg_types:
        for interface in all_interfaces:
            mac = interface.detail['mac']
            url= '/dedicated/server/'+interface.servername+'/networkInterfaceController/'+mac+'/mrtg'
            try:
                result2 = client_ovh.get(url, period='hourly', type=i,)
            except:
                logging.warning('API Error (this can be caused by a disconnected interface on the server): '+url+' '+str(interface))
            else:
                for j in result2:
                    try:
                        value= float(j['value']['value'])
                    except:
                        logging.warning('Error converting value to float:"'+str(value)+'"')
                    else:
                        result_list.append( MEASUREMENT( server=interface.servername, 
                            mac=mac,
                            timestamp= int(j['timestamp']),
                            value= float(j['value']['value']),
                            linktype=interface.detail['linkType'],
                            measurement_type=i ))
    with InfluxDBClient.from_config_file("config.toml") as client_influx:
        with client_influx.write_api() as writer:
            logging.info('writing length:'+str(len(result_list)))
            writer.write(
                bucket='network-poll',
                record=result_list,
                record_measurement_key='server',
                record_tag_keys=['mac','linktype','measurement_type'],
                record_field_keys=['value'],
                record_time_key='timestamp',
                write_precision=WritePrecision.S)

if __name__ == '__main__':
    main()
