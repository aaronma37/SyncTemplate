#!/usr/bin/env python
import csv

import time
import rospy
import sys
import numpy as np
from std_msgs.msg import Float32
from std_msgs.msg import Empty as EmptyMsg
from std_msgs.msg import Int32
from dana.msg import dana_msg as Msg
from dana.msg import all_info as AllInfoMsg
import copy

rospy.init_node('Slave', anonymous=True)

val=[]
# line_iter=0
# m=9.0

STEP_SIZE=.1

with open('/home/aaron/catkin_ws/src/SyncTemplate/scaled_interp_Pref.csv') as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  line_count = 0
  for row in csv_reader:
      val.append(float(row[0])+30.0)
      line_count+=1
  max_iter=line_count

def cap(val,low,high):
  if val < low:
    return low
  if high is not None:
    if val>high:
      return high
  return val

class Slave:
	def __init__(self):
            if rospy.has_param("~ident"):
                self.ident = int(rospy.get_param("~ident"))
                # print(self.ident)
            else:
                print "Identity of this computer is not set. Exiting"
                exit()
            self.f=open('/home/aaron/catkin_ws/src/dana/scripts/'+str(self.ident)+".csv","w")

            with open('/home/aaron/catkin_ws/src/SyncTemplate/gu.csv') as csv_file:
              csv_reader = csv.reader(csv_file, delimiter=',')
              for row in csv_reader:
                 self.gu=(float(row[self.ident]))


            self.one_hop_neighbors=[]
            with open('/home/aaron/catkin_ws/src/SyncTemplate/go.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    self.go=(float(row[self.ident]))

            self.two_hop_neighbors=[]
            self.three_hop_neighbors=[]
            for i in range(100):
                try:
                    s=rospy.get_param("~incoming"+str(i))
                    self.one_hop_neighbors.append(int(s))
                except:
                    pass
                try:
                    s=rospy.get_param("~2incoming"+str(i))
                    self.two_hop_neighbors.append(int(s))
                except:
                    pass
                try:
                    s=rospy.get_param("~3incoming"+str(i))
                    self.three_hop_neighbors.append(int(s))
                except:
                    pass
            # print(self.ident,self.one_hop_neighbors,self.two_hop_neighbors,self.three_hop_neighbors)

            rospy.Subscriber('/outer_loop', Int32, self.outerLoopCB)
            self.ack_pub=rospy.Publisher('/'+str(self.ident)+'/ack', Msg, queue_size=10)
            # self.ack_pub=rospy.Publisher('/ack', Msg, queue_size=100)
            rospy.Subscriber('/all_info', AllInfoMsg, self.allInfoCB)
            self.state=Msg()
            self.state.id=int(self.ident)
            if self.ident==0:
              self.state.P=val[0]

        def outerLoopCB(self,msg):
            self.f.write(str(self.state.P)+"\n")
            self.iteration2=msg.data
            self.update_y()

        def allInfoCB(self,msg):
            '''
            Starting of a round.  Do some calculations, set val_msg and then send out to neighbors
            '''
            self.update(msg)
            self.pub()

        def pub(self):
          self.ack_pub.publish(self.state)


        def update(self,msg):
          P0=self.state.P
          y0=self.state.y
          lamu0=self.state.lamu
          lamo0=self.state.lamo

          #Lambdas
          self.state.lamu=cap(lamu0+STEP_SIZE*(self.gu-P0),0,None)
          self.state.lamo=cap(lamo0+STEP_SIZE*(-self.go+P0),0,None)
          #----------------

          #P
          p=0
          #self
          p+=.5118*y0
          #1hop
          # print(msg)
          for neighbor in self.one_hop_neighbors:
            ny=msg.y[neighbor]
            p+=-.2559*ny

          self.state.P=P0+p
          #----------------

          #Z
          z=0
          az=0
          #self
          az+=.3532*(2*P0-lamu0+lamo0)
          
          #1hop
          for neighbor in self.one_hop_neighbors:
            nP=msg.P[neighbor]
            nlamo=msg.lamo[neighbor]
            nlamu=msg.lamu[neighbor]
            az+=-.0090*(2*nP-nlamu+nlamo)

          #2hop
          for neighbor in self.two_hop_neighbors:
            nP=msg.P[neighbor]
            nlamo=msg.lamo[neighbor]
            nlamu=msg.lamu[neighbor]
            az+=-.2011*(2*nP-nlamu+nlamo)

          #3hop
          for neighbor in self.three_hop_neighbors:
            nP=msg.P[neighbor]
            nlamo=msg.lamo[neighbor]
            nlamu=msg.lamu[neighbor]
            az+=.0335*(2*nP-nlamu+nlamo)
            # if self.ident>3 and self.ident<7:
            #   print(msg.y[neighbor],neighbor,self.ident)

          self.state.y=-STEP_SIZE*az
          self.state.time=msg.time+1


        def update_y(self):
          if self.state.id==0:
            self.state.P+=val[self.iteration2]-val[self.iteration2-1]

        def run(self):
            while not rospy.is_shutdown():
              # self.pub()
              time.sleep(.1)

def main(args):
	manager=Slave()
	try:
		manager.run()
	except KeyboardInterrupt:
		print("Draw: Shutting down")

if __name__ == '__main__':
	main(sys.argv)
