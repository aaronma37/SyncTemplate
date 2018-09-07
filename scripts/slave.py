#!/usr/bin/env python

import time
import rospy
import sys
import random

from std_msgs.msg import Float32
from std_msgs.msg import Int32
from SyncTemplate.msg import TwoScalarMsg
from SyncTemplate.msg import AckMsg

rospy.init_node('Slave', anonymous=True)

class Slave:
	def __init__(self):
            if rospy.has_param("~ident"):
                self.ident = rospy.get_param("~ident")
            else:
                print "Identity of this computer is not set. Exiting"
                exit()

            self.outgoing_pub =rospy.Publisher('edge', TwoScalarMsg, queue_size=100)

            self.incoming_neighbors={}
            for i in range(100):
                try:
                    s=rospy.get_param("~incoming"+str(i))
                    self.incoming_neighbors[s] = [False,TwoScalarMsg()]
                    print "Agent", self.ident, "now listening to", s
                except:
                    pass

            self.check_sum=None
            self.ack_publisher =rospy.Publisher('ack', AckMsg, queue_size=100)
            rospy.Subscriber('/sync_flag', Int32, self.flagCB)
            for s in self.incoming_neighbors.keys():
                rospy.Subscriber('/'+s+'/edge', TwoScalarMsg, self.neighborCB)

        def flagCB(self,msg):
            print "Agent",self.ident,"receiving round flag"
            for v in self.incoming_neighbors.values():
                v[0]=False
            self.check_sum=msg.data
            val_msg=TwoScalarMsg()
            val_msg.id=self.ident

            '''
            Starting of a round.  Do some calculations, set val_msg and then send out to neighbors
            '''
            print "Agent",self.ident,"sending msg to neighbor"
            self.outgoing_pub.publish(val_msg)

        def neighborCB(self,msg):
            print "Agent",self.ident,"received msg",msg
            try:
                self.incoming_neighbors[msg.id][0]=True
            except Exception,e: print str(e)
            if self.check_all_sent_from_neighbors():
                self.send_ack()

        def check_all_sent_from_neighbors(self):
            for v in self.incoming_neighbors.values():
                if v[0] ==False:
                    return False
            '''
            All values received from neighbors.  some computation probably goes here and then an acknowledgement is sent to the synchronizer.
            '''
            return True

        def send_ack(self):
            for v in self.incoming_neighbors.values():
                v[0]=False
            ack_response=AckMsg()
            ack_response.id=self.ident
            ack_response.check_sum=self.check_sum
            print "Agent",self.ident,"sending ack"
            self.ack_publisher.publish(ack_response)

        def run(self):
            while not rospy.is_shutdown():
                time.sleep(1)

def main(args):
	manager=Slave()
	try:
		manager.run()
	except KeyboardInterrupt:
		print("Draw: Shutting down")

if __name__ == '__main__':
	main(sys.argv)









