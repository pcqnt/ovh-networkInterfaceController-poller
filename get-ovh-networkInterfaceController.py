#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
import ovh
from influxdb_client import InfluxDBClient
from influxdb_client.domain.write_precision import WritePrecision
from dataclasses import dataclass
from os import environ
import logging
import argparse
import asyncio

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

def get_metrics(client_ovh, interfaces_to_poll, chosen_period,mrtg_type):
    result_list=[]
    for interface in interfaces_to_poll:
        url= '/dedicated/server/'+interface.servername+'/networkInterfaceController/'+interface.mac+'/mrtg'
        try:
            result = client_ovh.get(url, period=chosen_period, type=mrtg_type,)
        except:
            logging.info('API Error (this can be caused by a disconnected interface on the server): '+url+' '+str(interface))
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
                        value= value,
                        linkType=interface.linkType,
                        measurement_type=mrtg_type ))
    return result_list

async def main():
    
    parser = argparse.ArgumentParser(description='OVHcloud network API Poller')
    parser.add_argument('--hourly',help='Poll for last hour (default)', action='store_true')
    parser.add_argument('--daily',help='Poll for last day', action='store_true')
    parser.add_argument('--weekly',help='Poll for last week', action='store_true')
    parser.add_argument('--monthly',help='Poll for last month',action='store_true')
    parser.add_argument('--yearly',help='Poll for last year',action='store_true')
    parser.add_argument('--verbose',action='store_true')
    args= parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    if args.yearly:
        period= 'yearly'
    elif args.monthly:
        period='monthly'
    elif args.weekly:
        period='weekly'
    elif args.daily:
        period='daily'
    else:
        period='hourly'

    client_ovh = ovh.Client(
        endpoint='ovh-eu',               # Endpoint of API OVH Europe (List of available endpoints)
        application_key=environ['OVH_APP_KEY'],    # Application Key
        application_secret=environ['OVH_APP_SECRET'], # Application Secret
        consumer_key=environ['OVH_CONSUMER_KEY'],       # Consumer Key
    ) 
    influx_token=environ['INFLUX_TOKEN']
    influx_url=environ['INFLUX_URL']
    influx_org=environ['INFLUX_ORG']
    influx_bucket=environ['INFLUX_BUCKET']

    all_interfaces=get_all_interfaces(client_ovh)
    
    result_list_of_lists= await asyncio.gather(
        asyncio.to_thread(get_metrics, client_ovh, all_interfaces, period,'traffic:upload'),
        asyncio.to_thread(get_metrics, client_ovh, all_interfaces, period,'traffic:download'),
        asyncio.to_thread(get_metrics, client_ovh, all_interfaces, period,'errors:upload'),
        asyncio.to_thread(get_metrics, client_ovh, all_interfaces, period,'errors:download'),
        asyncio.to_thread(get_metrics, client_ovh, all_interfaces, period,'packets:upload'),
        asyncio.to_thread(get_metrics, client_ovh, all_interfaces, period,'packets:download'),
    )
    result_list=[]
    for sublist in result_list_of_lists:
        for item in sublist:
            result_list.append(item)

    with InfluxDBClient(url=influx_url,
            token=influx_token, org=influx_org) as client_influx:
        with client_influx.write_api() as writer:
            logging.info('writing length:'+str(len(result_list)))
            writer.write(
                bucket=influx_bucket,
                record=result_list,
                record_measurement_key='server',
                record_tag_keys=['mac','linkType','measurement_type'],
                record_field_keys=['value'],
                record_time_key='timestamp',
                write_precision=WritePrecision.S)

if __name__ == '__main__':
    asyncio.run(main())
