#!/usr/bin/env python

import time
import rospy
import sys
import random

from std_msgs.msg import Float32
from std_msgs.msg import Int32
from SyncTemplate.msg import AckMsg

rospy.init_node('Master', anonymous=True)
sync_flag_pub =rospy.Publisher('/sync_flag', Int32, queue_size=100)

class Master:
	def __init__(self):
            self.slaves={}
            for i in range(10):
                try:
                    s=rospy.get_param("~slave"+str(i))
                    self.slaves[s]=True
                    print "slave: ", s, " added to synchronizer." 
                except:
                    pass

            for s in self.slaves.keys():
                rospy.Subscriber(s+'/ack', AckMsg, self.sentCB)
            time.sleep(3)
            self.check_sum=None
            self.send_flag()

        def sentCB(self,msg):
            try:
                self.slaves[msg.id]=True
            except Exception,e: print str(e)
            if self.check_all_sent():
                self.send_flag()

        def check_all_sent(self):
            # for k,v in self.slaves.items():
            #   print k,v
            for v in self.slaves.values():
                if v == False:
                    return False

            return True

        def send_flag(self):
            # time.sleep(1)
            for k,v in self.slaves.items():
                self.slaves[k]=False

            # for k,v in self.slaves.items():
            #   print k,v,'after'
            self.check_sum=Int32()
            self.check_sum.data=random.randint(0,10000)
            self.pub()

        def pub(self):
            sync_flag_pub.publish(self.check_sum)

        def run(self):
            while not rospy.is_shutdown():
                self.pub()
                time.sleep(1)

def main(args):
	manager=Master()
	try:
		manager.run()
	except KeyboardInterrupt:
		print("Draw: Shutting down")

if __name__ == '__main__':
	main(sys.argv)









