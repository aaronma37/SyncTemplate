#!/usr/bin/env python

import time
import rospy
import sys
import random
from copy import deepcopy

from std_msgs.msg import Float32
from std_msgs.msg import Int32
from std_msgs.msg import Empty as EmptyMsg
from dana.msg import all_info as AllInfoMsg
from dana.msg import dana_msg as DanaMsg

rospy.init_node('Master', anonymous=True)
all_info_pub=rospy.Publisher('/all_info', AllInfoMsg, queue_size=1)
outer_loop_pub =rospy.Publisher('/outer_loop', Int32, queue_size=1)

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
              rospy.Subscriber(s+'/ack', DanaMsg, self.sentCB)
            # rospy.Subscriber('/ack', DanaMsg, self.sentCB)

            self.all_info_msg=AllInfoMsg()
            self.reset_all_info()
            time.sleep(2)
            # self.pub()
            self.reset_all_info()
            self.iterate()
            self.outer_iteration=Int32()
            self.outer_iteration.data=0

        def sentCB(self,msg):
            # print('msg from', msg.id,msg.time,self.all_info_msg.time)
            # print(msg)
            if msg.time==self.all_info_msg.time:
              self.all_info_msg.P[msg.id]=msg.P
              self.all_info_msg.y[msg.id]=msg.y
              self.all_info_msg.lamu[msg.id]=msg.lamu
              self.all_info_msg.lamo[msg.id]=msg.lamo
              self.all_info_msg.recv[msg.id]=True
              # print(self.all_info_msg)
              try:
                self.slaves[msg.id]=True
              except Exception,e: print str(e)
              # print(msg)
              # print(self.all_info_msg,'iterate')
            else:
              print("wrong time",msg.id, msg.P, msg.time, self.all_info_msg.time)

        def check_all_sent(self):
            for v in self.all_info_msg.recv:
                # print(v)
                if v is False:
                    return False
            print(self.all_info_msg.recv)
            return True

        def reset_all_info(self):
            self.all_info_msg.time+=1
            self.all_info_msg.P=[0.0]*9
            self.all_info_msg.y=[0.0]*9
            self.all_info_msg.lamo=[0.0]*9
            self.all_info_msg.lamu=[0.0]*9
            self.all_info_msg.recv=[False]*9

        def verify(self,msg):
            pairs=[[1,8],[2,7],[3,6]]
            for p in pairs:
              if msg.P[p[0]] != msg.P[p[1]]:
                print msg.P[p[0]],msg.P[p[1]],p

        def iterate(self):
            print(self.all_info_msg,'iterate',sum(self.all_info_msg.P))
            self.verify(self.all_info_msg)
            # time.sleep(.01)
            temp_msg=deepcopy(self.all_info_msg)
            self.reset_all_info()
            self.pub(temp_msg)
            for k,v in self.slaves.items():
                self.slaves[k]=False

        def pub(self,msg):
            all_info_pub.publish(msg)

        def outer_loop_inc(self):
          self.all_info_msg.time=0
          outer_loop_pub.publish(self.outer_iteration)
          self.iterate()
          # self.pub(temp_msg)
          # self.reset_all_info()

        def run(self):
            now=time.time()
            while not rospy.is_shutdown():
              if time.time()-now>2:
                self.outer_iteration.data+=1
                time.sleep(.25)
                now=time.time()
                self.outer_loop_inc()
              time.sleep(.001)
              if self.check_all_sent():
                  self.iterate()

def main(args):
	manager=Master()
	try:
		manager.run()
	except KeyboardInterrupt:
		print("Draw: Shutting down")

if __name__ == '__main__':
	main(sys.argv)









