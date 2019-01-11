# Jevois_yolo
Python script for controlling a Jevois smart camera using the Yolo library

**Jevois_yolo_frontdoor**
Use  Jevois smart camera to detect a person at the front door and send a text message with the picture to my cell phone.

Use the default Yolo on the Jevois without any additional training. Connect Jevois to Raspberry Pi 3B and run a python script that sets up the Jevois, waits for a person to be detected, copy a photo to Google Drive, and sends a text message with the attached photo to my phone. Copy all photos to Google Drive, but only send one text every 5 minutes. Turns out I can’t attach a photo, but it’s trivial to attach a link that my phone displays as a photo.

Python script to set up Jevois is already basically done from my previous work. Sending a text using Twilio is pretty easy. Uses motion_uploader from http://jeremyblythe.blogspot.com to upload photos.

The changes to motion uploader are to comment out some stuff that I didn't use plus fixed up motion_uploader for Python 3 style print

Install google drive APIs and http2lib and twilio
Pip3 install httplib2
sudo pip3 install --upgrade google-api-python-client
pip3 install --upgrade oauth2client
pip3 install twilio 

Chmod + x the python script

Profit!
