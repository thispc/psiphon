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


import pexpect
import hashlib
import base64
import sys
import socket
import time


class SSHConnection(object):

    def __init__(self, server, listen_port, listen_address):
        self.ip_address = server.get_ip_address()
        self.port = server.get_ssh_port()
        self.username = server.get_username()
        self.password = server.get_password_for_ssh_authentication()
        self.host_key = server.get_host_key()
        self.listen_port = listen_port
        self.listen_address = listen_address
        self.ssh = None

    def __del__(self):
        if self.ssh:
            self.ssh.terminate()

    # Get the RSA key fingerprint from the host's SSH_Host_Key
    # Based on:
    # http://stackoverflow.com/questions/6682815/deriving-an-ssh-fingerprint-from-a-public-key-in-python
    def _ssh_fingerprint(self):
        base64_key = base64.b64decode(self.host_key)
        md5_hash = hashlib.md5(base64_key).hexdigest()
        return ':'.join(a + b for a, b in zip(md5_hash[::2], md5_hash[1::2]))

    def command_line(self):
        cmd_line = ('ssh -C -D %s:%d -N -p %s %s@%s' %
                                 (self.listen_address, self.listen_port, self.port, self.username, self.ip_address))
        return cmd_line

    def connect(self):
        self.ssh = pexpect.spawn(self.command_line())
        # Print ssh output:
        #self.ssh.logfile_read = sys.stdout
        prompt = self.ssh.expect([self._ssh_fingerprint(), 'Password:'])
        if prompt == 0:
            self.ssh.sendline('yes')
            self.ssh.expect('Password:')
            self.ssh.sendline(self.password)
        else:
            self.ssh.sendline(self.password)

    def test_connection(self):
        MAX_WAIT_SECONDS = 10
        for i in range(MAX_WAIT_SECONDS):
            try:
                socket.socket().connect((self.listen_address, self.listen_port))
            except:
                if i < MAX_WAIT_SECONDS - 1:
                    time.sleep(1)
                else:
                    raise
        print '\nYour SOCKS proxy is now running at %s:%d' % (self.listen_address, self.listen_port)

    def disconnect_on_success(self, test_site=False):
        try:
            response = 200 # setting default as ok
            if test_site:
                import psi_website_checker
                response = psi_website_checker.check_default_sites()
                print 'Site Response %s' % (response)   
            if response != 200:
                print 'FAILED!'
            self.disconnect()
        except ImportError as error:
            print 'Failed importing module: %s' % str(error)
            raise error
        except Exception as error:
            print 'Failed: %s' % str(error)

    def wait_for_disconnect(self):
        self.ssh.wait()
        raise Exception('SSH disconnected unexpectedly')

    def disconnect(self):
        print 'Terminating...'
        self.ssh.terminate()
        print 'Connection closed'


class OSSHConnection(SSHConnection):

    def __init__(self, server, listen_port, listen_address):
        SSHConnection.__init__(self, server, listen_port, listen_address)
        self.port = server.get_obfuscated_ssh_port()
        self.obfuscate_keyword = server.get_obfuscate_keyword()

    def command_line(self):
        cmd_line = ('./ssh -C -D %s:%d -N -p %s -z -Z %s %s@%s' %
                                 (self.listen_address, self.listen_port, self.port, self.obfuscate_keyword,
                                  self.username, self.ip_address))
        return cmd_line


