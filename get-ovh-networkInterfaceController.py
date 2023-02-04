#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
import os
import json
import ovh
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS

# Load env variables 
# APP_KEY="xxx"
# APP_SECRET="yyy"
# CONSUMER_KEY="zzzz"
# MAC_ADDR="00:11:22:33:44:55"
# SERVICE_NAME="ns1234567.ip-1-2-3.eu"
from dotenv import dotenv_values
config=dotenv_values(".env")

debug=True
# Instanciate an OVH Client.
# You can generate new credentials with full access to your account on
# the token creation page
client = ovh.Client(
    endpoint='ovh-eu',               # Endpoint of API OVH Europe (List of available endpoints)
    application_key=config['APP_KEY'],    # Application Key
    application_secret=config['APP_SECRET'], # Application Secret
    consumer_key=config['CONSUMER_KEY'],       # Consumer Key
)

mrtg_types=['traffic:upload','traffic:download', 'errors:upload', 'errors:download', 'packets:upload','packets:download']

for i in mrtg_types : 
    result = client.get("/dedicated/server/"+config['SERVICE_NAME']+"/networkInterfaceController/"+config['MAC_ADDR']+"/mrtg", 
        period="hourly", # mrtg period (type: dedicated.server.MrtgPeriodEnum)
        type=i, # mrtg type (type: dedicated.server.MrtgTypeEnum)
        )
    if debug:
        print(result)
    for j in result:
        point= Point(i)
        point.tag('type',config['SERVICE_NAME'])
        point.time(int(j['timestamp'])*1000000000)
        for key, value in j["value"].items():
            try :
                x= int(value)
                point.field( key , x )
            except:
                point.field(key,value)

        with InfluxDBClient.from_config_file("config.toml") as influxclient:
            with influxclient.write_api(write_options=SYNCHRONOUS) as writer:
                try:
                    writer.write(bucket="my-bucket", record=[point])
                except:
                    continue

#
# Flux Query : 
#from(bucket: "my-bucket")
#  |> range(start: v.timeRangeStart, stop:v.timeRangeStop)
