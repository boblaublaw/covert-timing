#!/usr/bin/env python
from netfilterqueuewrapper import NetfilterQueueWrapper
from time import sleep,time
from sys import exc_info
from coverttime import CovertChannel
import subprocess

def netstatSelect():
    """This function will prompt the user for a locally terminated connection using netstat."""
    p = subprocess.Popen('netstat -W -n -a -A inet | grep ESTABLISHED', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval=p.wait()
    connections=map(lambda line: line.rstrip(), p.stdout.readlines())

    if len(connections) == 0:
        print 'No active connections detected.'
        return

    # show the netstat output as numbered lines
    lineNumber=1
    for line in connections:
        print str(lineNumber) + ': ' + line
        lineNumber+=1

    print "Select line number: "
    selectedLine=int(raw_input()) - 1

    #tcp        0      0 172.16.65.148:ssh       172.16.65.1:53698       ESTABLISHED
    proto, ignore1, ignore2, dst, src, ignore3 = connections[selectedLine].split()
    rip,rport = src.split(':')
    lip,lport = dst.split(':')

    # create two dictionaries and return them
    remote={ 'table':'OUTPUT', 'ip':rip, 'proto':proto, 'port':rport }
    local= { 'table':'INPUT',  'ip':lip, 'proto':proto, 'port':lport }
    return local, remote

try:
    # create an covertchannel object 
    a=CovertChannel()

    # use the netstatSelect method to select a locally terminated connection
    local, remote = netstatSelect()

    # assign the callback Functions
    local['callback'] = a.measure_jitter
    remote['callback'] = a.induce_jitter

    localShim = NetfilterQueueWrapper(**local)
    remoteShim = NetfilterQueueWrapper(**remote)

    # this is where interactive input and output would be handled
    while 1:
        sleep(0.1)
        # interactive stuff happens here

except KeyboardInterrupt:
    print "all done."

# vi: set ts=4 sw=4 expandtab: 
