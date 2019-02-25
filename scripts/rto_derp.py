#!/usr/bin/env python
import csv

import time
import rospy
import sys
from std_msgs.msg import Float32
from std_msgs.msg import Empty as EmptyMsg
from std_msgs.msg import Int32
from SyncTemplate.msg import rto_derp_msg as Msg
from SyncTemplate.msg import AckMsg
import copy

rospy.init_node('Slave', anonymous=True)

val=[]
line_iter=0
m=9.0

with open('/home/aaron/catkin_ws/src/SyncTemplate/scaled_interp_Pref.csv') as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  line_count = 0
  for row in csv_reader:
      val.append(float(row[0]))
      line_count+=1
  max_iter=line_count

class Slave:
	def __init__(self):
            if rospy.has_param("~ident"):
                self.ident = int(rospy.get_param("~ident"))
            else:
                print "Identity of this computer is not set. Exiting"
                exit()
            self.f=open('/home/aaron/catkin_ws/src/SyncTemplate/scripts/'+str(self.ident)+".csv","w")

            # if self.ident==1:
            #     with open('/home/aaron/catkin_ws/src/SyncTemplate/scaled_interp_Pref.csv') as csv_file:
            #         csv_reader = csv.reader(csv_file, delimiter=',')
            #         line_count = 0
            #         for row in csv_reader:
            #             val.append(float(row[0]))
            #             line_count+=1
            #         max_iter=line_count

            with open('/home/aaron/catkin_ws/src/SyncTemplate/gu.csv') as csv_file:
              csv_reader = csv.reader(csv_file, delimiter=',')
              for row in csv_reader:
                 self.gu=(float(row[self.ident-1]))

            with open('/home/aaron/catkin_ws/src/SyncTemplate/go.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    self.go=(float(row[self.ident-1]))

            self.outgoing_pub =rospy.Publisher('edge', Msg, queue_size=1)
            self.error_pub =rospy.Publisher('/error', EmptyMsg, queue_size=1)

            self.incoming_neighbors={}
            self.incoming_neighbors_2={}
            for i in range(100):
                try:
                    s=rospy.get_param("~incoming"+str(i))
                    self.incoming_neighbors[s] = {}
                    print "Agent", self.ident, "now listening to", s
                except:
                    pass
                try:
                    s=rospy.get_param("~2incoming"+str(i))
                    self.incoming_neighbors_2[s] = {}
                    print "Agent", self.ident, "now 2 hop listening to", s
                except:
                    pass

            self.check_sum=None
            self.ack_publisher =rospy.Publisher('ack', AckMsg, queue_size=1)
            rospy.Subscriber('/sync_flag', Int32, self.flagCB)
            rospy.Subscriber('/outer_loop', Int32, self.outerLoopCB)
            self.sub_list=[]
            for s in self.incoming_neighbors.keys():
                self.sub_list.append(rospy.Subscriber('/'+s+'/edge', Msg, self.neighborCB))
            for s in self.incoming_neighbors_2.keys():
                self.sub_list.append(rospy.Subscriber('/'+s+'/edge', Msg, self.neighborCB))
            self.iteration2=0
            self.check_list=[0]
            self.validated={}

            self.val_list={}
            self.reset_vals()
            self.update_flag=False
            self.Pr=val[0]

        def reset_vals(self):
          self.val_list[0]=Msg()
          self.val_list[0].val0=0
          self.val_list[0].P=0.0
          self.val_list[0].y=0.0
          self.val_list[0].lam=0.0
          self.val_list[0].id=str(self.ident)

        def copy_val_msg(self,v1,v2):
          v1.val0=v2.val0
          v1.val1=v2.val1
          v1.val2=v2.val2
          v1.id=v2.id
          return v1

        def outerLoopCB(self,msg):
            if self.val_list[self.check_list[0]].y==0:
              self.f.write(str(self.gu)+"\n")
            else:
              self.f.write(str(self.gu+(self.val_list[self.check_list[0]].P/self.val_list[self.check_list[0]].y)*(self.go-self.gu))+"\n")

            self.iteration2=msg.data
            self.update_y()

        def flagCB(self,msg):
            '''
            Starting of a round.  Do some calculations, set val_msg and then send out to neighbors
            '''
            if msg.data in self.check_list:
              if msg.data==self.check_list[1]:
                self.pub()
                return
            self.check_sum=msg.data
            self.check_list.append(msg.data)
            self.val_list[msg.data]=Msg()
            self.val_list[msg.data].val0=msg.data
            self.val_list[msg.data].id=str(self.ident)
            if len(self.val_list)>2:
              del self.val_list[self.check_list[0]]
              del self.check_list[0]
            self.update_flag=True
            self.pub()

        def pub(self):
          if len(self.val_list)<1:
            raise Exception('Small list error')
            return
          elif len(self.val_list)==2:
            if self.check_sum!=self.check_list[1]:
              raise Exception('check(SUM',self.check_sum,self.check_list,self.ident)
              return
          print self.val_list[self.check_list[0]],self.check_list
          self.outgoing_pub.publish(self.val_list[self.check_list[0]])

        # def update(self):
        #   z_sum=0.0
        #   y_sum=0.0
        #   for k,yz in self.incoming_neighbors.items():
        #       y_sum+=yz[self.check_list[0]][1]
        #       z_sum+=yz[self.check_list[0]][2]
        #   y=1./3.*(self.val_list[self.check_list[0]].val1+y_sum)
        #   z=1./3.*(self.val_list[self.check_list[0]].val2+z_sum)
        #   self.val_list[self.check_list[1]].val1=y
        #   self.val_list[self.check_list[1]].val2=z

        def update(self):
          P0=self.val_list[self.check_list[0]].P
          y0=self.val_list[self.check_list[0]].y
          lam0=self.val_list[self.check_list[0]].lam
          sum_P=0
          sum_y=0
          sum2_y=0
          sum_Pr=0
          sum_lam=0

          for k,neighbor in self.incoming_neighbors.items():
            sum_P+=neighbor[self.check_list[0]]['y']
            sum_y+=neighbor[self.check_list[0]]['lambda']+neighbor[self.check_list[0]]['P']
            sum_Pr+=self.Pr/m
            sum_lam+=neighbor[self.check_list[0]]['y']

          for k,neighbor in self.incoming_neighbors_2.items():
            sum2_y+=neighbor[self.check_list[0]]['y']

          self.val_list[self.check_list[1]].P=P0-.1*(2.0*P0+lam0+P0+sum_P-self.Pr/m)
          self.val_list[self.check_list[1]].y=y0-.1*(sum_y+sum2_y-sum_Pr)
          self.val_list[self.check_list[1]].lam=lam0-.1*(P0+sum_lam-self.Pr/m)

        def neighborCB(self,msg):
            if msg.val0 != self.check_list[0]:
              return
            if msg.id in self.incoming_neighbors.keys():
              if self.incoming_neighbors[msg.id].get(msg.val0) is None:
                self.incoming_neighbors[msg.id][msg.val0]={}
                self.incoming_neighbors[msg.id][msg.val0]['y']=msg.y
                self.incoming_neighbors[msg.id][msg.val0]['lambda']=msg.lam
                self.incoming_neighbors[msg.id][msg.val0]['P']=msg.P
              elif self.incoming_neighbors[msg.id][msg.val0] is False:
                self.incoming_neighbors[msg.id][msg.val0]={}
                self.incoming_neighbors[msg.id][msg.val0]['y']=msg.y
                self.incoming_neighbors[msg.id][msg.val0]['lambda']=msg.lam
                self.incoming_neighbors[msg.id][msg.val0]['P']=msg.P
                return
              else:
                self.incoming_neighbors[msg.id][msg.val0]=None
                return
              if len(self.val_list)<2:
                raise Exception('ERROR1')
                return
            elif msg.id in self.incoming_neighbors_2.keys():
              if self.incoming_neighbors_2[msg.id].get(msg.val0) is None:
                self.incoming_neighbors_2[msg.id][msg.val0]={}
                self.incoming_neighbors_2[msg.id][msg.val0]['y']=msg.y
                self.incoming_neighbors_2[msg.id][msg.val0]['lambda']=msg.lam
                self.incoming_neighbors_2[msg.id][msg.val0]['P']=msg.P
              elif self.incoming_neighbors_2[msg.id][msg.val0] is False:
                self.incoming_neighbors_2[msg.id][msg.val0]={}
                self.incoming_neighbors_2[msg.id][msg.val0]['y']=msg.y
                self.incoming_neighbors_2[msg.id][msg.val0]['lambda']=msg.lam
                self.incoming_neighbors_2[msg.id][msg.val0]['P']=msg.P
                return
              else:
                self.incoming_neighbors_2[msg.id][msg.val0]=None
                return
              if len(self.val_list)<2:
                raise Exception('ERROR1')
                return

            for k,v in self.incoming_neighbors.items():
                if v.get(self.check_list[0]) is None:
                  return
                if v[self.check_list[0]]==False:
                  del v[self.check_list[0]]
                  return

            for k,v in self.incoming_neighbors_2.items():
                if v.get(self.check_list[0]) is None:
                  return
                if v[self.check_list[0]]==False:
                  del v[self.check_list[0]]
                  return

            self.update()
            '''
            All values received from neighbors.  some computation probably goes here and then an acknowledgement is sent to the synchronizer.
            '''
            self.send_ack()

        def send_ack(self):
            for v in self.incoming_neighbors.values():
                v[0]=False
            ack_response=AckMsg()
            ack_response.id=str(self.ident)
            ack_response.check_sum=self.check_sum
            if self.check_sum==None:
              return
            self.ack_publisher.publish(ack_response)

        def update_y(self):
          self.incoming_neighbors={}
          for i in range(100):
              try:
                  s=rospy.get_param("~incoming"+str(i))
                  self.incoming_neighbors[s] = {}
                  print "Agent", self.ident, "now listening to", s
              except:
                  pass
          self.check_list=[0]
          self.val_list={}
          self.reset_vals()
          # self.val_list[0]=Msg()
          # self.val_list[0].val0=0
          # if self.ident==1:
          #   self.val_list[0].P=float(val[self.iteration2]-self.gu)
          # else:
          #   self.val_list[0].P=float(-self.gu)
          # self.val_list[0].y=float(self.go-self.gu)
          # self.val_list[0].lam=0.0
          # self.val_list[0].id=str(self.ident)
          self.Pr=val[self.iteration2]
          print self.Pr,"NEW_PR"

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
