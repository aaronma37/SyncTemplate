import csv
val=[]
for i in range(1,10):
  val.append([])
  with open('/home/aaron/catkin_ws/src/SyncTemplate/scripts/'+str(i)+'.csv') as     csv_file:
    csv_reader = csv.reader(csv_file, delimiter='\n')
    line_count = 0
    for row in csv_reader:
      # print row
      val[-1].append(float(row[0]))


for a in range(54):
  l=0
  for v in val:
    l+=v[a]
  print a+1,l

