# telegraf-digium
Telegraf plugin to monitor a Digium Series gateway.
This can used as an [[ inputs.exec ]] in a telegraf config file.

## How to
```
python telegraf-digium.py -h <DIGIUM_HOST> [--port <PORT>] -u <USER> -p <PASSWORD> [--ssl_skip_verification]
```

## Features
From Digium API (https://wiki.asterisk.org/wiki/display/DIGIUM/Gateway+API+Methods)
* Current calls usage - calls_active=
* Max calls - calls_max=
* Number of call processed - calls_processed=
* Temperature - temperature=
* Status of E1/T1 ports - pri-port1= (1 = UP, Active; 0 = Error)
* Status of SIP endpoints - sip-MYTRUNK= (if qualified: 1 = UP, Active; 0 = Error; null otherwise)
* Latency of each SIP endpoints - sip-latency-MYTRUNK= (in ms,if qualified; null otherwise)
* Update available - update_available= (boolean)

## TODO
* Convert it to Go code, in order to have a fullpackaged binary. Python multi-dependancies are baaaad
* Monitor each E1/T1 port, with the current usage in number of used channels and % of channels
* Monitor uptime
