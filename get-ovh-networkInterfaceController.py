#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
import ovh
from influxdb_client import InfluxDBClient
from influxdb_client.domain.write_precision import WritePrecision
from dataclasses import dataclass
from os import environ
import logging

@dataclass
class INTERFACE:
    servername: str
    linkType: str
    mac: str
    virtualNetworkInterface: str
@dataclass
class MEASUREMENT:
    server: str
    linkType: str
    mac: str
    timestamp: int
    value: float
    measurement_type: str

def get_all_interfaces(client_ovh):
    all_my_servers = client_ovh.get('/dedicated/server')
    all_interfaces=[]
    for server in all_my_servers:
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
                    all_interfaces.append(INTERFACE(servername=server,
                        linkType=mac_details['linkType'],
                        mac=mac_details['mac'],
                        virtualNetworkInterface=mac_details['virtualNetworkInterface']))
    return all_interfaces

def get_all_metrics(client_ovh, interfaces_to_poll, mrtg_type):
    result_list=[]
    for interface in interfaces_to_poll:
        url= '/dedicated/server/'+interface.servername+'/networkInterfaceController/'+interface.mac+'/mrtg'
        try:
            result = client_ovh.get(url, period='hourly', type=mrtg_type,)
        except:
            logging.warning('API Error (this can be caused by a disconnected interface on the server): '+url+' '+str(interface))
        else:
            for point in result:
                try:
                    value= float(point['value']['value'])
                except:
                    logging.debug('Error converting value to float:'+str(point))
                else:
                    result_list.append( MEASUREMENT( server=interface.servername, 
                        mac=interface.mac,
                        timestamp= int(point['timestamp']),
                        value= float(point['value']['value']),
                        linkType=interface.linkType,
                        measurement_type=mrtg_type ))
    return result_list
    

def main():
    #logging.basicConfig(level=logging.DEBUG)
    client_ovh = ovh.Client(
        endpoint='ovh-eu',               # Endpoint of API OVH Europe (List of available endpoints)
        application_key=environ['OVH_APP_KEY'],    # Application Key
        application_secret=environ['OVH_APP_SECRET'], # Application Secret
        consumer_key=environ['OVH_CONSUMER_KEY'],       # Consumer Key
    )
    all_mrtg_types=['traffic:upload', 'traffic:download', 
        'errors:upload', 'errors:download', 
        'packets:upload','packets:download']

    all_interfaces=get_all_interfaces(client_ovh)
    result_list=[]

    for mrtg_type in all_mrtg_types:
        result_list.append(get_all_metrics(client_ovh, all_interfaces, mrtg_type))
   
    with InfluxDBClient.from_config_file("config.toml") as client_influx:
        with client_influx.write_api() as writer:
            logging.info('writing length:'+str(len(result_list)))
            writer.write(
                bucket='network-poll',
                record=result_list,
                record_measurement_key='server',
                record_tag_keys=['mac','linkType','measurement_type'],
                record_field_keys=['value'],
                record_time_key='timestamp',
                write_precision=WritePrecision.S)

if __name__ == '__main__':
    main()
