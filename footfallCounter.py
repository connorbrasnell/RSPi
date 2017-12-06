import RPi.GPIO as GPIO
from time import sleep
import socket
import threading

GPIO.setmode(GPIO.BCM)

PIR_PIN = 21 # Pin the output of the PIR sensor is connected to

# Set up the PIR Pin with an internal pull down resistor to pull to 0
# and stop any fluctuations accidently registering
GPIO.setup(PIR_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

sleep(40) # Wait for the PIR sensor to warm up

# Connection paramaters for the server running on the main Pi
host = '192.168.1.157'
port = 4564

disconnectCount = ''
connected = False

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
	
        if GPIO.input(PIR_PIN) == 1:
                print("Motion Detected!")
                sendNewCustomer()

s = setupSocket()
print("Completed socket setup")

try:
	# Add an interrupt when the PIR sets the output pin to 1
	GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=motionCall)
	
	while 1:
                # Keep the program running
		sleep(1)
		
except KeyboardInterrupt:
	print("Exiting...")
	s.close() # Close the socket when exiting
	GPIO.cleanup() # Clean up the GPIO's, unsetting any pins used
