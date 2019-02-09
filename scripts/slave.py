#!/usr/bin/env python
import csv

import time
import rospy
import sys
from std_msgs.msg import Float32
from std_msgs.msg import Int32
from SyncTemplate.msg import TwoScalarMsg
from SyncTemplate.msg import AckMsg

rospy.init_node('Slave', anonymous=True)

val=[]
line_iter=0

if rospy.has_param("~master"):
    master = rospy.get_param("~master")



class Slave:
	def __init__(self):
            if rospy.has_param("~ident"):
                self.ident = int(rospy.get_param("~ident"))
            else:
                print "Identity of this computer is not set. Exiting"
                exit()

            if self.ident==1:
                with open('/home/aaron/catkin_ws/src/ratio_consensus/scripts/scaled_interp_Pref.csv') as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    line_count = 0
                    for row in csv_reader:
                        val.append(float(row[0]))
                        line_count+=1
                    max_iter=line_count

            with open('/home/aaron/catkin_ws/src/ratio_consensus/scripts/gu.csv') as csv_file:
              csv_reader = csv.reader(csv_file, delimiter=',')
              for row in csv_reader:
                 self.gu=(float(row[self.ident-1]))

            with open('/home/aaron/catkin_ws/src/ratio_consensus/scripts/go.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    self.go=(float(row[self.ident-1]))

            self.outgoing_pub =rospy.Publisher('edge', TwoScalarMsg, queue_size=1)

            self.incoming_neighbors={}
            for i in range(100):
                try:
                    s=rospy.get_param("~incoming"+str(i))
                    self.incoming_neighbors[s] = [False,TwoScalarMsg()]
                    print "Agent", self.ident, "now listening to", s
                except:
                    pass

            self.check_sum=None
            self.ack_publisher =rospy.Publisher('ack', AckMsg, queue_size=1)
            rospy.Subscriber('/sync_flag', Int32, self.flagCB)
            for s in self.incoming_neighbors.keys():
                rospy.Subscriber('/'+s+'/edge', TwoScalarMsg, self.neighborCB)
            self.val_msg=TwoScalarMsg()
            self.val_msg.id=str(self.ident)
            # self.val_msg.val1=self.ident
            print self.ident
            if self.ident==1:
              self.val_msg.val1=float(val[0]-self.gu)
            else:
              self.val_msg.val1=float(-self.gu)
            self.val_msg.val2=float(self.go-self.gu)
            print self.val_msg

        def flagCB(self,msg):
            # print "Agent",self.ident,"receiving round flag"
            for v in self.incoming_neighbors.values():
              v[0]=False
            self.check_sum=msg.data
            # print self.check_sum
            # val_msg=TwoScalarMsg()
            # val_msg.id=self.ident

            '''
            Starting of a round.  Do some calculations, set val_msg and then send out to neighbors
            '''
            # print "Agent",self.ident,"sending msg to neighbor"
            self.outgoing_pub.publish(self.val_msg)


        def neighborCB(self,msg):
            # print "Agent",self.ident,"received msg",msg
            try:
                self.incoming_neighbors[msg.id][0]=True
                self.incoming_neighbors[msg.id][1].val1=msg.val1
                self.incoming_neighbors[msg.id][1].val2=msg.val2
            except Exception,e: print str(e)
            if self.check_all_sent_from_neighbors():
                self.send_ack()

        def check_all_sent_from_neighbors(self):
            for k,v in self.incoming_neighbors.items():
                # print k,v
                if v[0] ==False:
                    return False

            z_sum=0.0
            y_sum=0.0
            for k,yz in self.incoming_neighbors.items():
                print k,yz
                y_sum+=yz[1].val1
                z_sum+=yz[1].val2
            y=1./3.*(self.val_msg.val1+y_sum)
            z=1./3.*(self.val_msg.val2+z_sum)
            # time.time(1)

            self.val_msg.val1=y
            self.val_msg.val2=z

            # self.yz_msg=Quaternion()
            # self.yz_msg.y=y
            # self.yz_msg.z=z
            # self.yz_msg.x=int(self.iteration+1)
            # self.yz_msg.w=int(ident)
            # self.iteration+=1
            # self.pub()
            '''
            All values received from neighbors.  some computation probably goes here and then an acknowledgement is sent to the synchronizer.
            '''
            return True

        def send_ack(self):
            for v in self.incoming_neighbors.values():
                v[0]=False
            ack_response=AckMsg()
            ack_response.id=str(self.ident)
            ack_response.check_sum=self.check_sum
            # print "Agent",self.ident,"sending ack"
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
