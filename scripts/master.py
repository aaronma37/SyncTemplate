#!/usr/bin/env python

import time
import rospy
import sys
import random

from std_msgs.msg import Float32
from std_msgs.msg import Int32
from std_msgs.msg import Empty as EmptyMsg
from SyncTemplate.msg import AckMsg

rospy.init_node('Master', anonymous=True)
sync_flag_pub =rospy.Publisher('/sync_flag', Int32, queue_size=100)
outer_loop_pub =rospy.Publisher('/outer_loop', EmptyMsg, queue_size=1)

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
            time.sleep(.5)
            self.check_sum=Int32()
            self.check_sum.data=0
            self.send_flag()

        def sentCB(self,msg):
            try:
                if msg.check_sum==self.check_sum.data:
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
            # self.check_sum=Int32()
            # self.check_sum.data=random.randint(0,10000)
            self.check_sum.data+=1
            # self.pub()

        def pub(self):
            sync_flag_pub.publish(self.check_sum)

        def outer_loop_inc(self):
          # self.check_sum.data=1
          outer_loop_pub.publish(EmptyMsg())
          time.sleep(2)

        def run(self):
            now=time.time()
            while not rospy.is_shutdown():
              if time.time()-now>3:
                time.sleep(.25)
                now=time.time()
                self.outer_loop_inc()

              self.pub()
              time.sleep(.001)

def main(args):
	manager=Master()
	try:
		manager.run()
	except KeyboardInterrupt:
		print("Draw: Shutting down")

if __name__ == '__main__':
	main(sys.argv)









