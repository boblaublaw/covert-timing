#!/usr/bin/env python
from netfilterqueue import NetfilterQueue, COPY_META
import threading
import subprocess
from atexit import register

globalconnspecnum=0

class NetfilterQueueWrapper(NetfilterQueue):
    """NetfilterQueueWrapper is an object used to set up and tear down NFQUEUE iptables rules."""

    def __init__(self, table='INPUT', ip='127.0.0.1', proto='tcp', port='6667', callback=None):
        super(NetfilterQueueWrapper,self).__init__()
        global globalconnspecnum
        self.connspec=''
        globalconnspecnum += 1
        self.connspecnum = globalconnspecnum
        self.callback=callback

        # create the rule specification
        self.connspec = table + ' -d ' + ip + '/32 -p ' + proto + ' --dport ' + port + ' -j NFQUEUE --queue-num ' + str(self.connspecnum)

        # run the appropriate iptables command and make sure it finishes
        p = subprocess.Popen('iptables -I ' + self.connspec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval=p.wait()

        # associate the NFQUEUE number with the wrapper function 
        self.bind(self.connspecnum, self.wrapper_func, mode=COPY_META)

        # we explicitly clean up before destructors get called
        register(self.cleanup)

        # launch a thread to listen for the callback method
        t = threading.Thread(target=self.run, args = ())

        # we have no way to stop these threads once they are launched, so we mark them as daemons
        t.daemon=True
        t.start()

    def wrapper_func(self, pkt):
        """This function ensures that we dont forget to accept the intercepted packet."""
        if self.callback != None:
            self.callback()
        pkt.accept()

    def cleanup(self):
        """This will tear down the nfqueue and issue the iptables command to stop interfering with the traffic."""
        if self.connspecnum != None:
            p = subprocess.Popen('iptables -D' + self.connspec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            retval=p.wait()
            self.connspec=''
            self.connspecnum=None
            super(NetfilterQueueWrapper,self).unbind()

# vi: set ts=4 sw=4 expandtab: 
