#!/usr/bin/python3
TWaccount_sid = 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
TWauth_token = 'lotsarandomchars'

import os,sys
import time
import shutil
import cv2
import numpy
import serial
import logging
from datetime import datetime
from twilio.rest import Client
import uploader

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
#default to not headless when debugging in Idle
if 'idlelib.run' in sys.modules:
   #idle
   Headless=False

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
   cfg_path = 'c:/Users/peter/frontdoorcam/uploader.cfg'
   port = 'COM7'
   camno = 0
else: #linux
   folder = '/home/pi/jevois_capture'
   logfile = '/home/pi/jevois.log'
   cfg_path = '/home/pi/frontdoorcam/uploader.cfg'
   port = '/dev/ttyACM0'
   camno = 0

logging.basicConfig(filename=logfile,level=logging.DEBUG)
logging.info('------- Jevois Cam Startup --------')

ser = serial.Serial(port,115200,timeout=0.01)

# No windows in headless
if not Headless:
   cv2.namedWindow("jevois", cv2.WINDOW_NORMAL)
   cv2.resizeWindow("jevois",1280,480) 


camera = cv2.VideoCapture(camno)

#initialize the jevois cam. See below - don't change these as it will change the Jevois engine from YOLO to something else
camera.set(3,1280) #width
camera.set(4,480) #height
camera.set(5,15) #fps
s,img = camera.read()
#wait for Yolo to load on camera.
time.sleep(120)


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

#set up Twilio for sending text messages
client = Client(TWaccount_sid, TWauth_token)
text_time = time.time() #initialize the time of last text to now

n_img = 6 #save this many images per capture - useful if the cam is slow to detect
img = numpy.empty(n_img, dtype=object)


while True:
   if not Headless:
      cv2.imshow("jevois", img[0] )
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
            conf = id_conf[1] 
            folder1 = folder + "/" + class_id + "/"
            #todo test if conf is greater than thresh. Should always be the case
            if Headless:
               logging.info(class_id+" found:"+conf)
            else:
               print (class_id+" found:"+conf)
         
            if class_id != "person" and class_id != "cat":
               #can't handle all the other classes yet
               folder1 = folder + "/other/"

            imagefile = datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss%f') + '.jpg'

            if Headless:
                logging.info("writing image: "+imagefile)
            else:
               print("writing image: "+imagefile)
            #crop_img = img[0:480, 0:640] # crop to single image.
            for i in range(0,n_img): #there might be a delay, capture many images
               s,img[i] = camera.read()
            img0 = img[5]
            crop_img = img0[0:480, 640:1280] # use if you want the Yolo results
            cv2.imwrite(folder1+imagefile,crop_img)
#            for i in range(0,n_img-1):
#               cv2.imwrite(folder1+str(i)+'_'+imagefile,img[i])

            #Upload image to Google Drive
            #Call Blythe's code to do this
            try:
                logging.basicConfig(level=logging.ERROR)
                #'Thanks to:'
                #'Motion Uploader - uploads videos and snapshots to Google Drive\n'
                #'   by Jeremy Blythe (http://jeremyblythe.blogspot.com)
                img_path = folder1+imagefile #actual filename to copy
                option = 'video' #using video even though it's not a video
                if not os.path.exists(cfg_path):
                     exit('Config file does not exist [%s]' % cfg_path)    
                if not os.path.exists(img_path):
                     exit('Source file does not exist [%s]' % vid_path)
                med_URL = uploader.MotionUploader(cfg_path).upload_video(img_path)        
            except Exception as e:
               exit('Error: [%s]' % e)

            #erase the file locally
            os.remove(folder1+imagefile)


            if (time.time() - text_time)> 300: #don't send texts more than one every 5 minutes
               text_time = time.time() #reset last text time to now
               text_body = class_id + " is at the front door. "+ med_URL+ " Conf: " + conf
               #can't get actual filename for jpg to pass via media_URL, so including it as a link
               
               message = client.messages.create(body=text_body,
                                                from_='+1415555573',
                                                to='+14155551212')
               print (message.sid)

                                                
