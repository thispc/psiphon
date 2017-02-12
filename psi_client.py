#!/usr/bin/python
#
# Copyright (c) 2012, Psiphon Inc.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from sets import Set
from psi_api import Psiphon3Server
from psi_ssh_connection import SSHConnection, OSSHConnection
import json
import os
import subprocess
import optparse
import sys
import wget

SOCKS_PORT = 1080
DATA_FILENAME = "ANY"
ossh_glob=False
number=0


CLIENT_VERSION = 1
CLIENT_PLATFORM = 'Python'

LOCAL_HOST_IP = '127.0.0.1'
GLOBAL_HOST_IP = '0.0.0.0'


class Data(object):

    def __init__(self, data):
        self.data = data

    @staticmethod
    def load():
        try:
            with open("servers.dat", 'r') as data_file:
                temp=dict()
                temp2=dict()
                temp["propagation_channel_id"] = "FFFFFFFFFFFFFFFF"
                temp2["propagation_channel_id"] = "FFFFFFFFFFFFFFFF"
                temp["sponsor_id"] = "FFFFFFFFFFFFFFFF"
                temp2["sponsor_id"] = "FFFFFFFFFFFFFFFF"
                temp["servers"] = list()
                temp2["servers"] = list()
                tempdata=json.loads(data_file.read())
                for i in tempdata["servers"]:
                    loc = i.find('{"webServerCertificate":'.encode('hex'))
                    ob=json.loads(i[loc:].decode('hex'))
                    if(ob["region"] == DATA_FILENAME or DATA_FILENAME == "ANY"):
                        
                        if(ossh_glob == False):
                            sahi = ("OSSH" in ob["capabilities"]) and (ob["sshObfuscatedPort"] == 53)
                            
                            if sahi==False:
                                continue
                        temp["servers"].append(i)
                if number==0:
                    data = Data(temp)
                else:
                    try:
                        temp2["servers"].append(temp['servers'][number-1])
                    except (IOError, ValueError, KeyError, IndexError, TypeError) as error:
                        print '\nNot a valid server number\n'
                        sys.exit(2)
                    data=Data(temp2)
            # Validate
            data.servers()[0]
            data.propagation_channel_id()
            data.sponsor_id()
            
        except (IOError, ValueError, KeyError, IndexError, TypeError) as error:
            print '\nPlease obtain a valid %s file and try again.\n' % (DATA_FILENAME,)
            raise
        return data

    def save(self):
        
        
        with open('servers.dat','r') as serv_file:
            tempdata=json.loads(serv_file.read())
            currdata=self.data
            
            for i in currdata["servers"]:
                if i not in tempdata["servers"]:
                    print "New server Found!!!! Appending....."
                    tempdata["servers"].append(i)
                    
        with open('servers.new', 'w') as data_file:
            data_file.write(json.dumps(tempdata))
        os.rename('servers.new', 'servers.dat');
        

    def servers(self):
        return self.data['servers']

    def propagation_channel_id(self):
        return self.data['propagation_channel_id']

    def sponsor_id(self):
        return self.data['sponsor_id']

    def move_first_server_entry_to_bottom(self):
        servers = self.servers()
        if len(servers) > 1:
            servers.append(servers.pop(0))
            return True
        else:
            return False




def do_handshake(server, data, relay):

    handshake_response = server.handshake(relay)
    # handshake might update the server list with newly discovered servers
    data.save()
    return handshake_response


def print_sponsor_message(handshake_response):
    home_pages = handshake_response['Homepage']
    if len(home_pages) > 0:
        print '\nPlease visit our sponsor\'s homepage%s:' % ('s' if len(home_pages) > 1 else '',)
    for home_page in home_pages:
        print home_page
    print ''


def make_ssh_connection(server, relay, bind_all):

    if bind_all:
        listen_address=GLOBAL_HOST_IP
    else:
        listen_address=LOCAL_HOST_IP

    if relay == 'OSSH':
        ssh_connection = OSSHConnection(server, SOCKS_PORT, str(listen_address))
    elif relay == 'SSH':
        ssh_connection = SSHConnection(server, SOCKS_PORT, str(listen_address))
    else:
        assert False

    ssh_connection.connect()
    return ssh_connection


def connect_to_server(data, relay, bind_all, test=False):

    assert relay in ['SSH', 'OSSH']

    server = Psiphon3Server(data.servers(), data.propagation_channel_id(), data.sponsor_id(), CLIENT_VERSION, CLIENT_PLATFORM)

    if server.relay_not_supported(relay):
        raise Exception('Server does not support %s' % relay)
        print (server.ip_address)
        print (server.extended_config)
        server
    handshake_performed = False
    if not server.can_attempt_relay_before_handshake(relay):
        handshake_response = do_handshake(server, data, relay)
        handshake_performed = True

    ssh_connection = make_ssh_connection(server, relay, bind_all)
    ssh_connection.test_connection()

    server.set_socks_proxy(SOCKS_PORT)

    if not handshake_performed:
        try:
            handshake_response = do_handshake(server, data, relay)
            handshake_performed = True
        except Exception as e:
            print 'DEBUG: handshake request: ' + str(e)

    connected_performed = False
    if handshake_performed:
        print_sponsor_message(handshake_response)
        try:
            server.connected(relay)
            connected_performed = True
        except Exception as e:
            print 'DEBUG: connected request: ' + str(e)

    if test:
        print 'Testing connection to ip %s' % server.ip_address
        ssh_connection.disconnect_on_success(test_site=test)
    else:
        with open('servers.dat','r') as serv_file:
            tempdata=json.loads(serv_file.read())
            top_index = tempdata["servers"].index(data.servers()[0])
            tempdata["servers"].insert(0, tempdata["servers"].pop(top_index))
        with open('servers.new', 'w') as data_file:
            data_file.write(json.dumps(tempdata))
        os.rename('servers.new', 'servers.dat');
        
        print("SERVER CONNECTED :: " + str(server.extended_config['region']))
        print "IP Address :" + str(server.ip_address)
        

        print 'Press Ctrl-C to terminate.'
        try:
            ssh_connection.wait_for_disconnect()
        except KeyboardInterrupt as e:
            if connected_performed:
                try:
                    server.disconnected(relay)
                except Exception as e:
                    print 'DEBUG: disconnected request: ' + str(e)
            ssh_connection.disconnect()


def _test_executable(path):
    if os.path.isfile(path):
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.call(path, stdout=devnull, stderr=devnull)
                return True
        except OSError:
            pass
    return False


def connect(bind_all, test=False):
    data = Data.load()
    while True:
        top=data.servers()[0]
        loc = top.find('{"webServerCertificate":'.encode('hex'))
        ob=json.loads(top[loc:].decode('hex'))
        
        print "Trying to connect to "+ob["region"]+" : " + ob["ipAddress"]


        try:
            relay = 'SSH'
            # NOTE that this path is also hard-coded in psi_ssh_connection
            ossh_path = './ssh'
            if _test_executable(ossh_path):
                relay = 'OSSH'
            else:
                print '%s is not a valid executable. Using standard ssh.' % (ossh_path,)

            connect_to_server(data, relay, bind_all, test)
            break
        except Exception as error:
            print 'DEBUG: %s connection: %s' % (relay, str(error))
            server = Psiphon3Server(data.servers(), data.propagation_channel_id(), data.sponsor_id(), CLIENT_VERSION, CLIENT_PLATFORM)
            
            
            if test:
                break
            if not data.move_first_server_entry_to_bottom():
                print 'DEBUG: could not reorder servers'
                
            data.save()
            print 'Trying next server...'


def test_all_servers(bind_all=False):

    data = Data.load()
    for _ in data.servers():
        connect(bind_all, test=True)
        print 'DEBUG: moving server to bottom'
        if not data.move_first_server_entry_to_bottom():
            print "could not reorder servers"
            break
        data.save()
def update():

    if os.path.exists("server_list"):
        os.remove("server_list")
    url ="https://s3.amazonaws.com//0ubz-2q11-gi9y/server_list"
    wget.download(url)
    f = open('server_list','r')
    lol=f.read()
    lol = json.loads(lol)
    lol = lol["data"]
    serv = lol.split('\n')
    regions = dict()
    regions["propagation_channel_id"] = "FFFFFFFFFFFFFFFF"
    regions["sponsor_id"] = "FFFFFFFFFFFFFFFF"
    regions["servers"] = list()
    for i in serv:
        loc = i.find('{"webServerCertificate":'.encode('hex'))
        js = i[loc:].decode('hex')
        js = json.loads(js)
        
        regions["servers"].append(i)
        
    json.dump(regions, open('servers.dat', 'w'))
    
        

def showall(reg="ANY"):
    regions=Set()

    try:
        with open("servers.dat", 'r') as data_file:

            data = json.loads(data_file.read())
            i=0
            print "\nNumber\tIP\t\tRegion\tOSSH"
            for ser in data['servers']:
                loc = ser.find('{"webServerCertificate":'.encode('hex'))
                ob=json.loads(ser[loc:].decode('hex'))
                if((ob['region']!=reg and reg!="ANY") or (ossh_glob == False and (("OSSH" not in ob["capabilities"]) or (ob["sshObfuscatedPort"] != 53)) ) ):
                    continue
                regions.add(ob['region'])
                i=i+1
                print (str(i) +"\t"+ ob['ipAddress'] + "\t" + ob['region'] +"\t" + str("OSSH" in ob['capabilities']))
            print regions
    except (IOError, ValueError, KeyError, IndexError, TypeError) as error:
        print '\nCountry not available or not valid.\n'
        sys.exit(2)

if __name__ == "__main__":
    
    parser = optparse.OptionParser('usage: %prog [options]')
    parser.add_option("--expose", "-e", dest="expose",     
                        action="store_true", help="Expose SOCKS proxy to the network")
    parser.add_option("--test-servers", "-t", dest="test_servers",
                        action="store_true", help="Test all servers")
    parser.add_option("--reg", "-r", dest="region",action="store", help="Regions")
    parser.add_option("--show","-s", dest="show_servers",action="store_true", help="Show available servers")
    parser.add_option("--port", "-p", dest="port",action="store",type=int, help="Local Port")
    parser.add_option("--update", "-u", dest="uflag",action="store_true", help="Update Servers")
    parser.add_option("--sid", "-i", dest="sid",action="store",type=int, help="Server number")
    parser.add_option("--all", "-a", dest="ossh_val",action="store_true", help="Include Non OSSH servers also")
    (options, args) = parser.parse_args()
    if options.ossh_val is not None:
        ossh_glob = options.ossh_val
    if (options.uflag):
        update()
        sys.exit(2)
    if options.region is not None:
        DATA_FILENAME=options.region
    if options.show_servers:
        showall(DATA_FILENAME)
        sys.exit(2)
    if options.port is not None:
        SOCKS_PORT=options.port
    if options.sid is not None:
        number=options.sid
    if options.test_servers:
        test_all_servers()
    elif options.expose:
        connect(True)
    else:
        connect(False)
