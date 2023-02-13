# ovh-networkInterfaceController-poller
Script that polls OVHcloud API to gather network metrics about the subscribed bare metal servers.

The script will check for all subscribed bare metal servers with a get to : '/dedicated/server'

For each mac address of the servers, it will query upload/download speeds , packets per second and errors. The result is inserted into a time-series database (InfluxDB). It can then be graphed using any compliant tool (Grafana being one example).

This script can be launched from an hourly CRON. 

A docker file is provided to run the script in Docker (useful if InfluxDB is only accessible on a docker network), to be launched with docker :

```
docker build -t ovh-network-poller
docker run -it --rm \
	--network=influxdb-network --name ovh-network-poller  \
	-e OVH_CONSUMER_KEY="aaa" \
	-e OVH_APP_SECRET="bbb" \
	-e OVH_APP_KEY="ccc" \
	-e INFLUX_TOKEN="ddd" \
	ovh-network-poller --yearly

```
