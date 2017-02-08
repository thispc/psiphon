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


import os
import sys
import httplib
import ssl
import binascii
import json
sys.path.insert(0, 'SocksiPy')
import socks
import socket
socket.socket = socks.socksocket
import urllib2


#
# Psiphon 3 Server API
#

class Psiphon3Server(object):

    def __init__(self, servers, propagation_channel_id, sponsor_id, client_version, client_platform):
        self.servers = servers
        server_entry = binascii.unhexlify(servers[0]).split(" ")
        (self.ip_address, self.web_server_port, self.web_server_secret,
         self.web_server_certificate) = server_entry[:4]
        # read the new json config element of the server entry, if present
        self.extended_config = None
        if len(server_entry) > 4:
            try:
                self.extended_config = json.loads(' '.join(server_entry[4:]))
            except Exception:
                pass
        self.propagation_channel_id = propagation_channel_id
        self.sponsor_id = sponsor_id
        self.client_version = client_version
        self.client_platform = client_platform
        self.handshake_response = None
        self.client_session_id = os.urandom(16).encode('hex')
        socks.setdefaultproxy()
        handler = CertificateMatchingHTTPSHandler(self.web_server_certificate)
        self.opener = urllib2.build_opener(handler)

    def set_socks_proxy(self, proxy_port):
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', proxy_port)

    def _has_extended_config_key(self, key):
        if not self.extended_config: return False
        return key in self.extended_config

    def _has_extended_config_value(self, key):
        if not self._has_extended_config_key(key): return False
        return ((type(self.extended_config[key]) == str and len(self.extended_config[key]) > 0) or
                (type(self.extended_config[key]) == unicode and len(self.extended_config[key]) > 0) or
                (type(self.extended_config[key]) == int and self.extended_config[key] != 0) or
                (type(self.extended_config[key]) == list))
 
    # This will return False if there is not enough information in the server entry to determine
    # if the relay protocol is supported.
    def relay_not_supported(self, relay_protocol):
        if relay_protocol not in ['SSH', 'OSSH']: return True
        if self._has_extended_config_value('capabilities'):
            return relay_protocol not in self.extended_config['capabilities']
        if relay_protocol == 'SSH':
            if (self._has_extended_config_key('sshPort') and
                not self._has_extended_config_value('sshPort')): return True
        elif relay_protocol == 'OSSH':
            if (self._has_extended_config_key('sshObfuscatedPort') and
                not self._has_extended_config_value('sshObfuscatedPort')): return True
            if (self._has_extended_config_key('sshObfuscatedKey') and
                not self._has_extended_config_value('sshObfuscatedKey')): return True
        else:
            return True
        return False

    def can_attempt_relay_before_handshake(self, relay_protocol):
        if relay_protocol not in ['SSH', 'OSSH']: return False
        if not self._has_extended_config_value('sshUsername'): return False
        if not self._has_extended_config_value('sshPassword'): return False
        if not self._has_extended_config_value('sshHostKey'): return False
        if relay_protocol == 'SSH':
            if not self._has_extended_config_value('sshPort'): return False
        elif relay_protocol == 'OSSH':
            if not self._has_extended_config_value('sshObfuscatedPort'): return False
            if not self._has_extended_config_value('sshObfuscatedKey'): return False
        else:
            return False
        return True

    # handshake
    # Note that self.servers may be updated with newly discovered servers after a successful handshake
    # TODO: upgrade the current server entry if not self.extended_config
    # TODO: page view regexes
    def handshake(self, relay_protocol):
        request_url = (self._common_request_url(relay_protocol) % ('handshake',) + '&' +
                       '&'.join(['known_server=%s' % (binascii.unhexlify(server).split(" ")[0],) for server in self.servers]))
        response = self.opener.open(request_url).read()
        self.handshake_response = {'Upgrade': '',
                                   'SSHPort': '',
                                   'SSHUsername': '',
                                   'SSHPassword': '',
                                   'SSHHostKey': '',
                                   'SSHSessionID': '',
                                   'SSHObfuscatedPort': '',
                                   'SSHObfuscatedKey': '',
                                   'PSK': '',
                                   'Homepage': []}

        for line in response.split('\n'):
            key, value = line.split(': ', 1)
            if key in self.handshake_response.keys():
                if type(self.handshake_response[key]) == list:
                    self.handshake_response[key].append(value)
                else:
                    self.handshake_response[key] = value
            if key == 'Server':
                # discovery
                if value not in self.servers:
                    self.servers.insert(1, value)
            if key == 'SSHSessionID':
                self.ssh_session_id = value

        return self.handshake_response

    def get_ip_address(self):
        return self.ip_address

    def get_ssh_port(self):
        if self.handshake_response:
            return self.handshake_response['SSHPort']
        if self._has_extended_config_value('sshPort'):
            return self.extended_config['sshPort']
        return None

    def get_username(self):
        if self.handshake_response:
            return self.handshake_response['SSHUsername']
        if self._has_extended_config_value('sshUsername'):
            return self.extended_config['sshUsername']
        return None

    def get_password(self):
        if self.handshake_response:
            return self.handshake_response['SSHPassword']
        if self._has_extended_config_value('sshPassword'):
            return self.extended_config['sshPassword']
        return None

    def get_password_for_ssh_authentication(self):
        return self.client_session_id + self.get_password()

    def get_host_key(self):
        if self.handshake_response:
            return self.handshake_response['SSHHostKey']
        if self._has_extended_config_value('sshHostKey'):
            return self.extended_config['sshHostKey']
        return None

    def get_obfuscated_ssh_port(self):
        if self.handshake_response:
            return self.handshake_response['SSHObfuscatedPort']
        if self._has_extended_config_value('sshObfuscatedPort'):
            return self.extended_config['sshObfuscatedPort']
        return None

    def get_obfuscate_keyword(self):
        if self.handshake_response:
            return self.handshake_response['SSHObfuscatedKey']
        if self._has_extended_config_value('sshObfuscatedKey'):
            return self.extended_config['sshObfuscatedKey']
        return None

    # TODO: download

    # connected
    # For SSH and OSSH, SSHSessionID from the handshake response is used when session_id is None
    # For VPN, the VPN IP Address should be used for session_id (ie. 10.0.0.2)
    def connected(self, relay_protocol, session_id=None):
        if not session_id and relay_protocol in ['SSH', 'OSSH']:
            session_id = self.ssh_session_id
        assert session_id is not None

        request_url = (self._common_request_url(relay_protocol) % ('connected',) +
                       '&session_id=%s' % (session_id,))
        self.opener.open(request_url)

    # disconnected
    # For SSH and OSSH, SSHSessionID from the handshake response is used when session_id is None
    # For VPN, this should not be called
    def disconnected(self, relay_protocol, session_id=None):
        assert relay_protocol not in ['VPN']
        if not session_id and relay_protocol in ['SSH', 'OSSH']:
            session_id = self.ssh_session_id
        assert session_id is not None

        request_url = (self._common_request_url(relay_protocol) % ('status',) +
                       '&session_id=%s&connected=%s' % (session_id, '0'))
        self.opener.open(request_url)

    # TODO: failed

    # TODO: status

    def _common_request_url(self, relay_protocol):
        assert relay_protocol in ['VPN','SSH','OSSH']
        return 'https://%s:%s/%%s?server_secret=%s&propagation_channel_id=%s&sponsor_id=%s&client_version=%s&client_platform=%s&relay_protocol=%s&client_session_id=%s' % (
            self.ip_address, self.web_server_port, self.web_server_secret,
            self.propagation_channel_id, self.sponsor_id, self.client_version,
            self.client_platform, relay_protocol, self.client_session_id)


#
# CertificateMatchingHTTPSHandler
#
# Adapted from CertValidatingHTTPSConnection and VerifiedHTTPSHandler
# http://stackoverflow.com/questions/1087227/validate-ssl-certificates-with-python
#

class InvalidCertificateException(httplib.HTTPException, urllib2.URLError):

    def __init__(self, host, cert, reason):
        httplib.HTTPException.__init__(self)
        self.host = host
        self.cert = cert
        self.reason = reason

    def __str__(self):
        return ('Host %s returned an invalid certificate (%s) %s\n' %
                (self.host, self.reason, self.cert))


class CertificateMatchingHTTPSConnection(httplib.HTTPConnection):

    def __init__(self, host, expected_server_certificate, **kwargs):
        httplib.HTTPConnection.__init__(self, host, **kwargs)
        self.expected_server_certificate = expected_server_certificate

    def connect(self):
        sock = socket.create_connection((self.host, self.port))
        self.sock = ssl.wrap_socket(sock)
        cert = ssl.DER_cert_to_PEM_cert(self.sock.getpeercert(True))
        # Remove newlines and -----BEGIN CERTIFICATE----- and -----END CERTIFICATE-----
        cert = ''.join(cert.splitlines())[len('-----BEGIN CERTIFICATE-----'):-len('-----END CERTIFICATE-----')]
        if cert != self.expected_server_certificate:
            raise InvalidCertificateException(self.host, cert,
                                              'server presented the wrong certificate')


class CertificateMatchingHTTPSHandler(urllib2.HTTPSHandler):

    def __init__(self, expected_server_certificate):
        urllib2.AbstractHTTPHandler.__init__(self)
        self.expected_server_certificate = expected_server_certificate

    def https_open(self, req):
        def http_class_wrapper(host, **kwargs):
            return CertificateMatchingHTTPSConnection(
                    host, self.expected_server_certificate, **kwargs)

        try:
            return self.do_open(http_class_wrapper, req)
        except urllib2.URLError, e:
            if type(e.reason) == ssl.SSLError and e.reason.args[0] == 1:
                raise InvalidCertificateException(req.host, '',
                                                  e.reason.args[1])
            raise

    https_request = urllib2.HTTPSHandler.do_request_ 


