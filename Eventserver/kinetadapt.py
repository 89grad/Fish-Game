#!/usr/bin/python

#
#   Copyright 2012 89grad GmbH
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
#   Event server that relays Events from the Kinect to the game
#
#   Fish Installation for Muesumsnacht Bern 2012
#   Author: Florian Baumgartner <florian.baumgartner@89grad.ch>
#   

import select
import socket
import sys
from datetime import datetime

status={'xaccel':0.0,'yaccel':0.0,'flags':''}

def process_data(d):
    global status
    d=d.rstrip().lstrip()
    #print repr(d)
    if d.startswith('get'):
        s='status %f %f %s' % (status['xaccel'],status['yaccel'],status['flags'])
        status['flags']='' 
        return s

    if d.startswith('set Hover:'):
        d=d[len('set Hover:'):].lstrip()
        x,y=d.split(',')
        status['xaccel']=(float(x)-1.5)/1.5
        status['yaccel']=(float(y)-4.0)/4.0
        print "accel update: %s" % repr(status)
        return 'ok'

    if d.startswith('set Select:'):
        d=d[len('set Select:'):].lstrip()
        a,f=d.split(' ')
        x,y=a.split(',')
        status['xaccel']=(float(x)-1.5)/1.5
        status['yaccel']=(float(y)-4.0)/4.0
        for i in ['Backward','Forward']:
            if i in f: status['flags']=i

        print "flags update: %s" % repr(status)
        return 'ok'

    if d.startswith('set Wave:'):
        status['xaccel']=0.0
        status['yaccel']=0.0
        status['flags'] = 'Wave'
        print "flags update: Wave"
        return 'ok'

    if d.startswith('set Trackstop:'):
        status['xaccel']=0.0
        status['yaccel']=0.0
        status['flags'] = 'Tstop'
        print "flags update: Tstop"
        return 'ok'

    if d.startswith('set Trackstart:'):
        status['xaccel']=0.0
        status['yaccel']=0.0
        status['flags'] = 'Tstart'
        print "flags update: Tstart"
        return 'ok'


    print 'unknown input: %s -> error' % repr(d)
    return 'error'


def server(host,port):
    backlog = 5
    size = 1024

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host,port))
        server.listen(backlog)
    except socket.error:
        print 'cannot bind, address probably in use, wait a few secs'
        sys.exit(0);
        
    input = [server]

    statusline=''
    while True:
        inputready,outputready,exceptready = select.select(input,[],[])
        for s in inputready:

            if s == server:
                # handle the server socket
                client, address = server.accept()
                print "incoming connection from %s" % repr(address)
                input.append(client)

#            elif s == sys.stdin:
#                # handle standard input
#                sys.stdin.readline()

            else:
                # handle all other sockets
                data = s.recv(size)
                if data:
                    s.send(process_data(data)+'\n')
                else:
                    s.close()
                    input.remove(s)
    
    server.close() 


print "listening on all interfaces on port 8000"

server('',8000)
