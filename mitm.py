#!/usr/bin/env python
from netfilterqueuewrapper import NetfilterQueueWrapper
from coverttime import CovertChannel
from time import sleep,time
from sys import exc_info
import subprocess, curses

def netstatSelect(stdscr):
    """This function will prompt the user for a locally terminated connection using netstat."""
    p = subprocess.Popen('netstat -W -n -a -A inet | grep ESTABLISHED', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval=p.wait()
    connections=map(lambda line: line.rstrip(), p.stdout.readlines())

    if len(connections) == 0:
        stdscr.addstr('No active connections detected.\n')
        return

    # show the netstat output as numbered lines
    lineNumber=1
    for line in connections:
        stdscr.addstr(str(lineNumber) + ':' + line + '\n')
        lineNumber+=1

    stdscr.addstr("Select line number: ")
    x=stdscr.getstr()
    stdscr.addstr(x)
    selectedLine=int(x) - 1
    stdscr.addstr("\nSelected line = " + str(selectedLine) + '\n')

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
    local['callback'] = cc.measure_jitter
    remote['callback'] = cc.induce_jitter

    localShim = NetfilterQueueWrapper(**local)
    remoteShim = NetfilterQueueWrapper(**remote)

    # this is where interactive input and output would be handled
    while 1:
        sleep(0.1)
        stdscr.refresh()
        while cc.delays.empty() == False:
            delay=cc.delays.get()
            delaystr=str(delay)
            stdscr.addstr(delaystr + '\n')
        # interactive stuff happens here

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print "all done."


# vi: set ts=4 sw=4 expandtab: 
