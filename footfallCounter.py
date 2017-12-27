import RPi.GPIO as GPIO
from time import sleep
import time
import socket
import threading
from io import BytesIO
import subprocess
import os
from datetime import datetime
from PIL import Image

#GPIO.setmode(GPIO.BCM)

#PIR_PIN = 21 # Pin the output of the PIR sensor is connected to

# Set up the PIR Pin with an internal pull down resistor to pull to 0
# and stop any fluctuations accidently registering
#GPIO.setup(PIR_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

#sleep(40) # Wait for the PIR sensor to warm up

# Connection paramaters for the server running on the main Pi
host = '192.168.1.157'
port = 4564

disconnectCount = ''
connected = False

# Motion detection settings:
# Threshold (how much a pixel has to change by to be marked as "changed")
# Sensitivity (how many changed pixels before capturing an image)
# ForceCapture (whether to force an image to be captured every forceCaptureTime seconds)
threshold = 10
sensitivity = 6000
footfallCount = 0

detected = False
detectedCount = 0

def setupSocket():
        """
        Set up the socket that will be used to communicate with the
        main Pi
        """

        global connected
        global s
        global disconnectCount

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while connected == False:
                try:
                        s.connect((host,port))
                except socket.error as msg:
                        print("Failed to connect")
                        sleep(10)
                        continue
                else:
                        connected = True

                        # On a reconnect, send any pending footfall
                        # +1 for the initial send that doesn't send
                        # a fault
                        s.send(str.encode(disconnectCount))
                        if disconnectCount != '':
                                s.send(str.encode('1'))
                        disconnectCount = ''
        return s

def sendNewCustomer():
        """
        Communicate to the main Pi that the PIR sensor has detected
        a customer walking through the door
        """

        global connected
        global disconnectCount
        global s
        
        if connected == True:
                try:
                        s.send(str.encode("1\n"))
                except socket.error as msg:
                        print("Unable to send message: " + str(msg))
                        print("Added to disconnectedCount")
                        disconnectCount = disconnectCount + '1'
                        connected = False

                        # If the server has gone down, connect again
                        # but on a seperate thread so footfall still
                        # counts
                        t = threading.Thread(target = setupSocket)
                        t.start()
        else:
                print("Added to disconnectedCount")
                disconnectCount = disconnectCount + '1' 

def motionCall(PIR_PIN):
        """
        When the PIR triggers an interrupt, this function is called.
        motionCall checks to make sure the pin is set, if so it will
        print to the console and communicate with the main Pi
        """
	
        #if GPIO.input(PIR_PIN) == 1:
                #print("Motion Detected!")
                #sendNewCustomer()
        sendNewCustomer()

s = setupSocket()
print("Completed socket setup")

# Capture a small test image (for motion detection)
def captureTestImage():
        command = "raspistill -w %s -h %s -n -t 1 -roi 0.22,0,0.55,0.55 -e bmp -o -" % (200, 150)
        imageData = BytesIO()
        imageData.write(subprocess.check_output(command, shell=True))
        imageData.seek(0)
        im = Image.open(imageData)
        buffer = im.load()
        imageData.close()
        return im, buffer

# Get first image
image1, buffer1 = captureTestImage()

try:
        # Add an interrupt when the PIR sets the output pin to 1
        #GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=motionCall)

        while 1:
                # Keep the program running
                #sleep(1)

                # Get comparison image
                image2, buffer2 = captureTestImage()

                # Count changed pixels
                changedPixels = 0
                for x in range(0, 200):
                        for y in  range(0, 150):
                                # Just check green channel as it's the highest quality channel
                                pixdiff = abs(buffer1[x,y][1] - buffer2[x,y][1])
                                if pixdiff > threshold:
                                        changedPixels += 1

                #print("Changed Pixels: " + str(changedPixels))
                # Save an image if pixels changed
                if changedPixels > sensitivity:
                        #print("Changed Pixels: " + str(changedPixels))
                        if detectedCount == 1:
                                if detected == False:
                                        detected = True
                                        footfallCount = footfallCount + 1
                                        print("Motion Detected! " + str(footfallCount))
                                        #lastCapture = time.time()
                                        #saveImage(saveWidth, saveHeight, diskSpaceToReserve)
                                        detectedCount = 0
                                        sendNewCustomer()
                        elif detectedCount == 0:
                                detectedCount = 1	
                else:
                        detectedCount = 0
                        if detected == True:
                                print("Zero")
                                detected = False

                # Swap comparison buffers
                image1 = image2
                buffer1 = buffer2        
		
except KeyboardInterrupt:
	print("Exiting...")
	s.close() # Close the socket when exiting
	#GPIO.cleanup() # Clean up the GPIO's, unsetting any pins used
