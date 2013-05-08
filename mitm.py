#!/usr/bin/env python
from netfilterqueuewrapper import NetfilterQueueWrapper
from coverttime import CovertChannel
from time import sleep,time
from sys import exc_info
import subprocess, curses

def netstatSelect(window):
    """This function will prompt the user for a locally terminated connection using 
    netstat."""
    netstatCmd = 'netstat -W -n -a -A inet | grep ESTABLISHED'
    p = subprocess.Popen(netstatCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval=p.wait()
    connections=map(lambda line: line.rstrip(), p.stdout.readlines())

    if len(connections) == 0:
        raise Exception('Netstat shows no ESTABLISHED connections.')

    # show the netstat output as numbered lines
    lineNumber=1
    for line in connections:
        window.addstr(str(lineNumber) + ':' + line + '\n')
        lineNumber+=1

    window.addstr("Select line number: ")
    x=window.getstr()
    window.addstr(x)
    selectedLine=int(x) - 1
    window.addstr("\nSelected line = " + str(selectedLine) + '\n')

    #tcp        0      0 172.16.65.148:ssh       172.16.65.1:53698       ESTABLISHED
    proto, ignore1, ignore2, dst, src, ignore3 = connections[selectedLine].split()
    rip,rport = src.split(':')
    lip,lport = dst.split(':')

    # create two dictionaries and return them
    remote={ 'table':'OUTPUT', 'ip':rip, 'proto':proto, 'port':rport }
    local= { 'table':'INPUT',  'ip':lip, 'proto':proto, 'port':lport }
    return local, remote

def main(stdscr):
    # create an covertchannel object 
    cc=CovertChannel()

    # use the netstatSelect method to select a locally terminated connection
    # in the future this could be extended/modified to support FORWARD
    # packets for traffic passing through this host.
    local, remote = netstatSelect(stdscr)

    # assign the callback Functions
    local['callback'] = cc.record_packet
    remote['callback'] = cc.induce_jitter

    localShim = NetfilterQueueWrapper(**local)
    remoteShim = NetfilterQueueWrapper(**remote)

    # this is where interactive input and output would be handled

    lastNumDelays = 0 
    while True:
        sleep(0.0001)
        cc.calculate_delays()
        numDelays = len(cc.delays)
        if numDelays == lastNumDelays:
            continue
        stdscr.clear()
        y, x = stdscr.getmaxyx()
        lines=min(y,numDelays) 
        stats=list(cc.delays)[-lines:]
        while len(stats) > 1:
            datum = stats.pop(0)
            stdscr.addstr( 'packet ' + str(datum[0]) + ' at ' + str(datum[1]) + ' ' + ("%05f" % datum[2] ) + '\n')
        stdscr.refresh()
        lastNumDelays=numDelays

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print "all done."


# vi: set ts=4 sw=4 expandtab: 
