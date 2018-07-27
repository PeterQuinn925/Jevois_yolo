#!/usr/bin/python3

import os,sys
import time
import shutil
import cv2
import serial
import logging
from datetime import datetime

def SendParm(cmd):
   ser.write (cmd)
   time.sleep(1)
   line = ser.readline()
   if Headless:
      logging.info(cmd.decode('utf8'))
      logging.info(line.decode('utf8'))
   else:
      print (cmd.decode('utf8'))
      print (line.decode('utf8'))
      
#main -------
Headless=True
thresh=50 # default detection threshold
if len(sys.argv)>1:
   if sys.argv[1]=='-show':
      Headless=False
   elif 'thresh' in sys.argv[1]: 
      thresh_arg=sys.argv[1].split("=")
      thresh=int(thresh_arg[1])

if len(sys.argv)>2:
   if 'thresh' in sys.argv[2]:
      thresh_arg=sys.argv[2].split("=")
      thresh=int(thresh_arg[1])

if os.name == 'nt':
   folder = 'C:\\users\\peter/jevois_capture'
   logfile = 'c:\\users\\peter/jevois.log'
   port = 'COM6'
   camno = 1
else: #linux
   folder = '/home/pi/jevois_capture'
   logfile = '/home/pi/jevois.log'
   port = '/dev/ttyACM0'
   camno = 0

logging.basicConfig(filename=logfile,level=logging.DEBUG)
logging.info('------- Jevois Cam Startup --------')
ser = serial.Serial(port,115200,timeout=1)

# No windows in headless
if not Headless:
   cv2.namedWindow("jevois", cv2.WINDOW_NORMAL)
   cv2.resizeWindow("jevois",1280,480) 

# cam 0 on pi, cam 1 on PC
camera = cv2.VideoCapture(camno)

#initialize the jevois cam. See below - don't change these as it will change the Jevois engine from YOLO to something else
camera.set(3,1280) #width
camera.set(4,480) #height
camera.set(5,15) #fps
s,img = camera.read()
#wait for Yolo to load on camera.
time.sleep(10)


#setmapping2 YUYV 640 480 15.0 JeVois DarknetYOLO
#setmapping 15
#### this setmappings stuff is not useful here. It uses the values
#### in the camera x y and FPS to look up the mode in the list.
#### Left in the script as it's useful place to copy from when debugging
#
# YOLO variables are documented here: http://jevois.org/moddoc/DarknetYOLO/modinfo.html
#
#SendParm (b'setpar serlog USB\n') #too many debug msgs. Only use if you have trouble
#
##################################################
# To use your own network and weights, put these parmeters in
# JEVOIS:/modules/JeVois/DarknetYOLO/params.cfg 
#datacfg=cfg/my_obj.data
#cfgfile=cfg/my.cfg
#weightfile=weights/my.weights
######################################################

SendParm (b'setpar serstyle Normal\n') #use Normal format to include types and coordinates
time.sleep(2)
SendParm (b'setpar serout All\n') # output everything on serial
time.sleep(2)
tps = 'setpar thresh '+str(thresh)+'\n'
thresh_param = tps.encode('utf-8')
SendParm (thresh_param) # set the threshold for detection %

while True:
   s,img = camera.read()
   if not Headless:
      cv2.imshow("jevois", img )
      cv2.waitKey(1)
   line = ser.readline()
   if not Headless:
      print (line.decode('utf8'))
   #example output when capturing a selection //changed with Yolov3 update
   # b'N2 person:51.5 -1394 -697 841 1519
   #   N2 id:confidence       x     y     w    h 
   # http://jevois.org/qa/index.php?qa=2079&qa_1=yolo-coordinate-output-to-serial-what-data-is-output
   # coord system is -1000 to 1000 with 0,0 in the cam center. http://jevois.org/doc/group__coordhelpers.html
   # x,y appears to be the upper left of the box
   
   if len(line)>0:
      if "DKY" in str(line): 
         pass #do nothing
      elif "OK" in str(line):
         pass #do nothing
      else:
         line_split = line.split(b" ")
         if len(line_split)>5:
            line_split[1] = line_split[1].decode('utf8') #line_split[1] is the class of object found and confidence%
            id_conf = line_split[1].split(":") #split again on : to separate the class and confidence
            class_id = id_conf[0]
            conf = id_conf[1] #for future use
            x = int(line_split[2])
            y = int(line_split[3])
            w = int(line_split[4])
            h = int(line_split[5])
            x=int(x+w/2) #move x to center of the box
            y=int(y+h/2) #move y to center of the box
            #convert to pixels using 640x480
            #scale x to 640 width from 2000 (-1000 to 1000) and offset by 640/2
            x = int(x*640/2000+320)
            w = int(w*640/4000)
            #scale y to 480 height from 1500 (-750 to 750) and offset by 480/2. 
            y = int(y*480/1500+240)
            h = int(h*480/3000)
            if not Headless:
               print ("x= "+str(x))
               print ("y= "+str(y))
               print ("w= "+str(w))
               print ("h= "+str(h))
         
            folder1 = folder + "/" + class_id + "/"
            #todo test if conf is greater than thresh. Should always be the case
            if Headless:
               logging.info(class_id+" found")
            else:
               print (class_id+" found")
         
            if class_id != "person" and class_id != "cat":
               #can't handle all the other classes yet
               folder1 = folder + "/other/"

            imagefile = datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss%f') + '.jpg'

            if Headless:
                logging.info("writing image: "+imagefile)
            else:
               print("writing image: "+imagefile)
            crop_img = img[0:480, 0:640] # crop to single image.
            #crop_img = img[0:480, 640:1280] # use if you want the Yolo results
            cv2.circle(crop_img,(x,y),25,(0,255,0),5)
            cv2.rectangle(crop_img,(x-w,y-h),(x+w,y+h),(255,255,0),5)
            cv2.imwrite(folder1+imagefile,crop_img)
      

   


