# ovh-networkInterfaceController-poller
Script that polls OVHcloud API to gather network metrics about the subscribed bare metal servers.

The script will check for all subscribed bare metal servers with a get to : '/dedicated/server'

For each mac address of the servers, it will query upload/download speeds , packets per second and errors. The result is inserted into a time-series database (InfluxDB). It can then be graphed using any compliant tool (Grafana being one example).

This script can be launched from an hourly CRON. 

Required environment variables :
- OVH_CONSUMER_KEY
- OVH_APP_SECRET 
- OVH_APP_KEY
- INFLUX_TOKEN
- INFLUX_URL
- INFLUX_ORG
- INFLUX_BUCKET

The first three environment variables can be generated on OVHcloud's website (cf documentation: https://docs.ovh.com/gb/en/api/first-steps-with-ovh-api/#advanced-usage-pair-ovhcloud-apis-with-an-application_2 ).

A docker file is provided to run the script in Docker (useful if InfluxDB is only accessible on a docker network), to be launched with docker :

```
docker build -t ovh-network-poller
docker run -it --rm \
	--network=influxdb-network --name ovh-network-poller  \
	-e OVH_CONSUMER_KEY="aaaa" \
	-e OVH_APP_SECRET="bbbb" \
	-e OVH_APP_KEY="cccc" \
	-e INFLUX_TOKEN="dddd" \
	-e INFLUX_URL="http://influxdb:8086" \
	-e INFLUX_ORG="ovh" \
	-e INFLUX_BUCKET="network-poll" \
	ovh-network-poller --yearly

```
