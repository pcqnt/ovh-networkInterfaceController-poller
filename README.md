# ovh-networkInterfaceController-poller
Script that polls OVHcloud API networkInterfaceController of a bare metal to insert into InfluxDB

The script will check for all subscribed bare metal servers with a get to : '/dedicated/server'

For each mac address of the servers , it will query upload/download speeds , packets per second and errors. The result is inserted into a time-series database (InfluxDB).
