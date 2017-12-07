import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

PIR_PIN = 19

GPIO.setup(PIR_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

#sleep(30)

inputNum = 0

try:
    while 1:

        if GPIO.input(PIR_PIN) != inputNum:
            print(str(GPIO.input(PIR_PIN)))
            inputNum = GPIO.input(PIR_PIN)
        sleep(0.5)

except KeyboardInterrupt:
	print("Exiting...")
	GPIO.cleanup() 
