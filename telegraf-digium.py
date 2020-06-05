#!/usr/bin/env python

import sys
import getopt
import re
import ssl
import mechanize
import cookielib
import urllib
import json
from pprint import pprint
from datetime import datetime

class Digium():
    def __init__(self, host, port, user, password, ssl_skip_verification=False):
        self.host = "https://" + host + ":" + port
        self.user = user
        self.password = password
        self.ssl_skip_verification = ssl_skip_verification
        self.cookiejar = cookielib.LWPCookieJar()
        self.connect = self.api_connect()

    def api_connect(self):
        data = {
            'admin_uid': self.user,
            'admin_password': self.password
        }
        data_str = '&'.join(['%s=%s' % (k,v) for k,v in data.items()])

        if self.ssl_skip_verification is True:
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context
        req = mechanize.Request("%s/admin/main.html" % self.host, data_str)
        self.cookiejar.add_cookie_header(req)
        res = mechanize.urlopen(req)
        lines = res.read()
     
        # Check if logged in
        if re.search("Welcome,\s+%s" % self.user, lines) is None:
            print('%s: login incorrect for user %s' % (self.host, self.user))
            sys.exit(-1)
        return 0

    def api_request(self, data):
        data_str = json.dumps(data, separators=(',',':'))
        req = mechanize.Request("%s/json" % self.host, data_str)
        res = mechanize.urlopen(req)
        lines = res.read()
        response = json.loads(lines)
        result = json.loads(response['response']['result'])
        return result

def main(argv):

    ##
    ## Default parameters
    ##

    host = '127.0.0.1'
    port = '443'
    user = 'admin'
    password = 'admin'
    ssl_skip_verification = False
    help_line = "Usage: monitor.py -h <DIGIUM_HOST> [--port <PORT>] -u <USER> -p <PASSWORD> [--ssl_skip_verification]"

    ##
    ## Get options
    ##

    try:
        opts, args = getopt.getopt(argv, "h:u:p:",["port=", "help", "ssl_skip_verification"])
    except getopt.GetoptError:
        print help_line
        sys.exit(2)
    for opt, arg in opts:
        if opt == "--help":
            print help_line
            sys.exit()
        elif opt == "-h":
            host = arg
        elif opt == "--port":
            port = arg
        elif opt == "-u":
            user = arg
        elif opt =="-p":
            password = arg
        elif opt == "--ssl_skip_verification":
            ssl_skip_verification = True

    ##
    ## Run baby run
    ##

    gw = Digium(host=host, port=port, user=user, password=password, ssl_skip_verification=ssl_skip_verification)

    request_calls = {
        "request" : {
            "method": "statistics.list",
        }
    }
    request_status = {
        "request" : {
            "method": "connection_status.list",
        }
    }
    request_gw_info = {
        "request" : {
            "method": "gateway.list",
        }
    }
    request_update = {
        "request" : {
            "method": "update.list",
        }
    }
    response = gw.api_request(request_calls)
    calls = response['statistics']
    response = gw.api_request(request_status)
    status = response['connection_status']
    response = gw.api_request(request_gw_info)
    gw_info = response['gateway']
    response = gw.api_request(request_update)
    update = response['update']

    ##
    ## Format to InfluxDB style
    ## https://docs.influxdata.com/influxdb/v1.8/write_protocols/line_protocol_tutorial/
    ##

    connections = ''
    for port in status['t1_e1_interfaces']:
        connections += "pri-%s=%d," % (port['name'], 1 if port['status_desc'] == 'Up, Active' else 0)
    for port in status['sip_endpoints']:
        if port['status_desc']['latency'] != "Unmonitored":
            connections += "sip-%s=%s," % (port['name'], 0 if port['status_desc']['latency'] == 'UNREACHABLE' else 1)
            connections += "sip-latency-%s=%s," % (port['name'], "null" if port['status_desc']['latency'] == 'UNREACHABLE' else port['status_desc']['latency'])
        else:
            connections += "sip-%s=null," % port['name']
            connections += "sip-latency-%s=null," % port['name']
    print ("digium calls_active=%si,calls_max=%si,calls_processed=%si,temperature=%s,%s,update_available=%s" % (
        calls['active'],
        calls['maxcalls'],
        calls['processed'],
        gw_info['temperature'][:-2],
        connections[:-1],
        "True" if update['update_available'] == 1 else "False"))

if __name__ == "__main__":
   main(sys.argv[1:])
