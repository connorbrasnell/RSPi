import time
import sys
import threading
import os

import httplib2
import oauth2client
from oauth2client import client, tools
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
import mimetypes
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.pyplot as plt

import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

import tkinter as tk
from tkinter import ttk
from tkinter import *

import MySQLdb as sql

import RPi.GPIO as GPIO

from PIL import ImageTk
import PIL.Image

import smbus

import socket
import select

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'client_id.json'
APPLICATION_NAME = 'Gmail API Python Send Email'

temp_sensor = '/sys/bus/w1/devices/28-0000095cb34f/w1_slave'

GPIO.setmode(GPIO.BCM)

WEEK_BUTT = 17
DAY_BUTT = 27
GPIO.setup(WEEK_BUTT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DAY_BUTT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

INC_LIGHT_BUTT = 11
DEC_LIGHT_BUTT = 9
GPIO.setup(INC_LIGHT_BUTT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DEC_LIGHT_BUTT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

LED1 = 5
LED2 = 6
LED3 = 13
LED4 = 19
LED5 = 26
GPIO.setup(LED1, GPIO.OUT)
GPIO.setup(LED2, GPIO.OUT)
GPIO.setup(LED3, GPIO.OUT)
GPIO.setup(LED4, GPIO.OUT)
GPIO.setup(LED5, GPIO.OUT)

lightCount = 0
lightCountMutex = False

# Connect to the database that holds all the historical footfall data
db = sql.connect("localhost","RSPiUser","RSComponents","RSPi" )
cursor = db.cursor()

# Paramaters to set up a socket that listens to the footfall counter Pi
host = ''
port = 4564

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket Created")
socketError = False
conn = 0
connected = False

# Get I2C bus
bus = smbus.SMBus(1)

# TSL2561 address, 0x39(57)
# Select control register, 0x00(00) with command register, 0x80(128)
#		0x03(03)	Power ON mode
bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
# TSL2561 address, 0x39(57)
# Select timing register, 0x01(01) with command register, 0x80(128)
#		0x02(02)	Nominal integration time = 402ms
bus.write_byte_data(0x39, 0x01 | 0x80, 0x02)

time.sleep(0.5)

lightValueList = []

insideTempList = []

appClose = False # Used by second thread to know when the program has been closed

currentDay = "Monday"
currentDate = '1996-02-15'
dayAverage = [0,0,0,0,0]
timePeriodAverage = [0,0,0,0,0]
footfallWeekX = ['','Mon','Tue','Wed','Thu','Fri']
xAxisCoords = [1,2,3,4,5]
footfallDayX = ['','7am-','9am-','11am-','1pm-','3pm-']

footfallGraphChoice = 0 # Decides which footfall graph to switch to

customerCountInt = 0 # Counts the total amount of customers in a day
timePeriodCount = [0,0,0,0,0]

titleFont = {'fontname':'DejaVu Sans'} # Default Mac Python font

# Set up the Tkinter GUI
root = tk.Tk()
root.wm_title("RS Pi")

# Variables used to update the customer count label
customerCount = StringVar()
customerCount.set(str(customerCountInt))

style.use("ggplot")

# Temperate/Light graph setup
fig = plt.figure(figsize=(0.2,0.2))
plt.subplots_adjust(bottom=0.05, top=0.91, hspace=0.4)

# Footfall graph setup
figFootfall = plt.figure(figsize=(0.2,0.2))
footfallAxis = figFootfall.add_subplot(1,1,1)

# Individual temperature/light graphs being added to the figure
outsideTempAxis = fig.add_subplot(3,1,1)
insideTempAxis = fig.add_subplot(3,1,2)
lightAxis = fig.add_subplot(3,1,3)

# Hide the x axis of all the temperature/light graphs
outsideTempAxis.xaxis.set_visible(False)
insideTempAxis.xaxis.set_visible(False)
lightAxis.xaxis.set_visible(False)

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-email-send.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def SendMessage(sender, to, subject, msgHtml, msgPlain, attachmentFile=None):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    if attachmentFile:
        message1 = createMessageWithAttachment(sender, to, subject, msgHtml, msgPlain, attachmentFile)
    else:
        message1 = CreateMessageHtml(sender, to, subject, msgHtml, msgPlain)
    result = SendMessageInternal(service, "me", message1)
    return result

def SendMessageInternal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
        return("Error")
    return "OK"

def CreateMessageHtml(sender, to, subject, msgHtml, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    msg.attach(MIMEText(msgHtml, 'html'))
    raw = base64.urlsafe_b64encode(bytes(msg.as_string(), 'UTF-8'))
    raw = raw.decode()
    return {'raw': raw}

def animateOutside(i):
    """
    Function called to update the Outside Temperature graph
    """
    data = open("data_files/outsideTemp.txt","r").read()
    splitData = data.split('\n')

    xsO = []
    ysO = []

    currentY = 0 # Stores the current temperature

    # For each line in the text file, add the x and y values into two arrays
    for eachLine in splitData:
        if len(eachLine) > 1:
            x,y = eachLine.split(',')
            xsO.append(int(x))
            ysO.append(int(y))
            currentY = y

    currentY = currentY + '\N{DEGREE SIGN}C' # Update the current temperature

    # Clear the graph
    outsideTempAxis.cla()

    # Set the titles and labels
    outsideTempAxis.set_title('Outside Temperature', fontsize=20, **titleFont)
    outsideTempAxis.set_ylabel('Degrees (\N{DEGREE SIGN}C)', fontsize=10)
    outsideTempAxis.annotate(currentY, xy=(0.955, 1.05), xycoords='axes fraction',fontsize=14, **titleFont)

    # Plot the graph with the updated points
    outsideTempAxis.plot(xsO,ysO,'r')

def read_temperature():
    f = open(temp_sensor, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temperature()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temperature()
    temp_output = lines[1].find('t=')
    if temp_output != -1:
        temp_string = lines[1].strip()[temp_output+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def animateInside(i):
    """
    Function called to update the Inside Temperature graph
    """

    global insideTempList

    currentTemperature = round(read_temp(),1)

    if len(insideTempList) >= 480:
        insideTempList = insideTempList[20:]
        
    insideTempList.append(currentTemperature)
    
    currentTemperature = str(currentTemperature) + '\N{DEGREE SIGN}C' # Update the current temperature

    # Clear the graph
    insideTempAxis.cla()

    # Set the titles and labels
    insideTempAxis.set_title('Inside Temperature', fontsize=20, **titleFont)
    insideTempAxis.set_ylabel('Degrees (\N{DEGREE SIGN}C)', fontsize=10)
    insideTempAxis.annotate(currentTemperature, xy=(0.955, 1.05), xycoords='axes fraction',fontsize=14, **titleFont)

    # Plot the graph with the updated points
    insideTempAxis.plot(insideTempList,'r')

    insideTempAxis.set_ylim(ymin=0,ymax=(max(insideTempList)+10))

def animateLight(i):
    """
    Function called to update the Light graph
    """

    global lightValueList
    
    # Read data back from 0x0C(12) with command register, 0x80(128), 2 bytes
    # ch0 LSB, ch0 MSB
    data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)

    # Read data back from 0x0E(14) with command register, 0x80(128), 2 bytes
    # ch1 LSB, ch1 MSB
    data1 = bus.read_i2c_block_data(0x39, 0x0E | 0x80, 2)

    # Convert the data
    currentLightLevel = data[1] * 256 + data[0]

    if len(lightValueList) >= 100:
        lightValueList = lightValueList[10:]
        
    lightValueList.append(currentLightLevel)
    
    currentLightLevel = str(currentLightLevel) + ' Lux' # Update the current light level

    # Clear the graph
    lightAxis.cla()

    # Set the titles and labels
    lightAxis.set_title('Light Level', fontsize=20, **titleFont)
    lightAxis.set_ylabel('Lux', fontsize=10)
    lightAxis.annotate(currentLightLevel, xy=(0.91, 1.05), xycoords='axes fraction',fontsize=14, **titleFont)

    # Plot the graph with the updated points
    lightAxis.plot(lightValueList,'r')

    lightAxis.set_ylim(ymin=0,ymax=(max(lightValueList)+200))

def plotWeeklyFootfall():
    """
    Plots the weekly historical footfall graph
    """

    # Clear the graph
    footfallAxis.cla()

    # Set the titles and labels
    footfallAxis.set_title('Weekly Footfall', fontsize=20, **titleFont)
    footfallAxis.set_ylabel('Footfall', fontsize=10)

    # Plot the graph, specifying that it should be a bar graph
    footfallAxis.bar(xAxisCoords,dayAverage, 0.5,color=['red'],align="center")
    footfallAxis.set_xticklabels(footfallWeekX)

    # Draw the graph on the screen
    figFootfall.canvas.draw()


def plotDailyFootfall():
    """
    Plots the daily historical footfall graph
    """

    # Clear the graph
    footfallAxis.cla()

    # Set the titles and labels
    footfallAxis.set_title('Daily Footfall', fontsize=20, **titleFont)
    footfallAxis.set_ylabel('Footfall', fontsize=10)

    # Plot the graph, specifying that it should be a bar graph
    footfallAxis.bar(xAxisCoords,timePeriodAverage, 0.5,color=['red'],align="center")
    footfallAxis.set_xticklabels(footfallDayX)

    # Draw the graph on the screen
    figFootfall.canvas.draw()

def updateFootfall():
    """
    Update the footfall information in the variables/text file/database

    - Check if date in text file matches the current date
    - If the date matches
        - If variables < text file
            - Add variables and text file values, update text file and variables with that number
        - If variables >= text file
            - Set text file values to variable values
    - If the date does not match
        - Add the variable values to the text file values
        - Write those values to the database with the date from the text file
        - Reset the variable values, the text file values and the date to the current date on the text file
        - Call startOfDay()
    """

    global customerCountInt
    global timePeriodCount

    data = open("data_files/daysFootfall.txt","r").read()
    splitData = data.split('\n')

    textFileValues = []

    textFileValues.append(int(splitData[0]))
    textFileValues.append(int(splitData[1]))
    textFileValues.append(int(splitData[2]))
    textFileValues.append(int(splitData[3]))
    textFileValues.append(int(splitData[4]))
    textFileValues.append(int(splitData[5]))
    textFileValues.append(splitData[6])

    textFileDate = splitData[6]

    # Check the logic in the function comment
    if currentDate == textFileDate:
        if customerCountInt < textFileValues[0]:

            combined = textFileValues[0] + customerCountInt
            textFileValues[0] = combined
            customerCountInt = combined

            customerCount.set(str(customerCountInt))

            for i in range(len(textFileValues)-2):
                combined = textFileValues[i+1] + timePeriodCount[i]
                textFileValues[i+1] = combined
                timePeriodCount[i] = combined

            for i in range(len(textFileValues)-1):
                textFileValues[i] = str(textFileValues[i])

            output = open('data_files/daysFootfall.txt', 'w').close()
            output = open('data_files/daysFootfall.txt', 'w')
            output.write('\n'.join(textFileValues))
            output.close()

        elif customerCountInt > textFileValues[0]:

            replaceTextFileValues = []

            replaceTextFileValues.append(str(customerCountInt))
            replaceTextFileValues.append(str(timePeriodCount[0]))
            replaceTextFileValues.append(str(timePeriodCount[1]))
            replaceTextFileValues.append(str(timePeriodCount[2]))
            replaceTextFileValues.append(str(timePeriodCount[3]))
            replaceTextFileValues.append(str(timePeriodCount[4]))
            replaceTextFileValues.append(currentDate)

            output = open('data_files/daysFootfall.txt', 'w').close()
            output = open('data_files/daysFootfall.txt', 'w')
            output.write('\n'.join(replaceTextFileValues))
            output.close()

    else:

        combined = textFileValues[0] + customerCountInt
        textFileValues[0] = combined
        customerCountInt = combined

        customerCount.set(str(customerCountInt))

        for i in range(len(textFileValues)-2):
            combined = textFileValues[i+1] + timePeriodCount[i]
            textFileValues[i+1] = combined
            timePeriodCount[i] = combined

        customerCountInt = 0
        customerCount.set(str(customerCountInt))

        for i in range(len(timePeriodCount)):
            timePeriodCount[i] = 0

        replaceTextFileValues = []

        replaceTextFileValues.append(str(customerCountInt))
        replaceTextFileValues.append(str(timePeriodCount[0]))
        replaceTextFileValues.append(str(timePeriodCount[1]))
        replaceTextFileValues.append(str(timePeriodCount[2]))
        replaceTextFileValues.append(str(timePeriodCount[3]))
        replaceTextFileValues.append(str(timePeriodCount[4]))
        replaceTextFileValues.append(currentDate)

        output = open('data_files/daysFootfall.txt', 'w').close()
        output = open('data_files/daysFootfall.txt', 'w')
        output.write('\n'.join(replaceTextFileValues))
        output.close()

        yesterdayDay = calculateCurrentDay(datetime.datetime.strptime(textFileDate,'%Y-%m-%d'))

        try:
            cursor.execute("INSERT INTO weekly(day, todaydate, count) VALUES (%s,%s,%s)", (yesterdayDay, textFileDate, textFileValues[0]))
            cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (yesterdayDay, textFileDate, 1, textFileValues[1]))
            cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (yesterdayDay, textFileDate, 2, textFileValues[2]))
            cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (yesterdayDay, textFileDate, 3, textFileValues[3]))
            cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (yesterdayDay, textFileDate, 4, textFileValues[4]))
            cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (yesterdayDay, textFileDate, 5, textFileValues[5]))

            db.commit()
        except Exception as e:
            # Problem with the queries, keep it atomic and roll back any changes
            print(e)
            print("Rollback")
            db.rollback()

        to = "connorbrasnell@gmail.com"
        sender = "RSPiFootfall@gmail.com"
        subject = "Footfall Today"
        msgHtml = "Hi<br /><br />Today's footfall was " + str(textFileValues[0])
        msgPlain = ""
        SendMessage(sender, to, subject, msgHtml, msgPlain)

        startOfDayDB()

    root.after(900000, updateFootfall) # Call the function every 15 minutes
    #root.after(5000, updateFootfall)

def calculateCurrentDay(day):
    """
    Given a date, calculate the str day
    """

    currentDayInt = day.weekday()

    if currentDayInt == 0:
        currentDay = 'Monday'
    elif currentDayInt == 1:
        currentDay = 'Tuesday'
    elif currentDayInt == 2:
        currentDay = 'Wednesday'
    elif currentDayInt == 3:
        currentDay = 'Thursday'
    elif currentDayInt == 4:
        currentDay = 'Friday'
    elif currentDayInt == 5:
        currentDay = 'Saturday'
    elif currentDayInt == 6:
        currentDay = 'Sunday'

    return currentDay

def endOfDayDB():
    """
    Commit the current status of the text file to the database

    *** Testing purposes only
    """

    global currentDate

    data = open("data_files/daysFootfall.txt","r").read()
    splitData = data.split('\n')

    footfallValues = []

    footfallValues.append(int(splitData[0]))
    footfallValues.append(int(splitData[1]))
    footfallValues.append(int(splitData[2]))
    footfallValues.append(int(splitData[3]))
    footfallValues.append(int(splitData[4]))
    footfallValues.append(int(splitData[5]))

    try:
        cursor.execute("INSERT INTO weekly(day, todaydate, count) VALUES (%s,%s,%s)", (currentDay, currentDate, footfallValues[0]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 1, footfallValues[1]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 2, footfallValues[2]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 3, footfallValues[3]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 4, footfallValues[4]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 5, footfallValues[5]))

        db.commit()
    except Exception as e:
        print(e)
        print("Rollback")
        db.rollback()

def startOfDayDB():
    """
    Called every time the Pi starts up, and called at the end of updateFootfall, every 15 minutes

    - Finds current date
    - Finds date 6 months 6 months ago
    - Removes all enties in the database from more than 6 months ago
    - Find the averages for all the time periods for the current day
    - Find the averages for all the days
    - Put these values in the variables stored in the application
    """

    global currentDate
    global currentDay
    global dayAverage
    global timePeriodAverage

    currentDate = time.strftime('%Y-%m-%d')
    sixMonthsAgo = date.today() + relativedelta(months=-6)

    currentDay = calculateCurrentDay(datetime.datetime.strptime(currentDate,'%Y-%m-%d'))

    sql00 = """DELETE FROM weekly WHERE todaydate < '%s'""" % (sixMonthsAgo)
    sql01 = """DELETE FROM daily WHERE todaydate < '%s'""" % (sixMonthsAgo)

    try:
        cursor.execute(sql00)
        cursor.execute(sql01)
        db.commit()
    except Exception as e:
        print(e)
        print("Rollback")
        db.rollback()

    sql1 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM daily WHERE day='%s' AND timeperiod=1""" % (currentDay)
    sql2 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM daily WHERE day='%s' AND timeperiod=2""" % (currentDay)
    sql3 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM daily WHERE day='%s' AND timeperiod=3""" % (currentDay)
    sql4 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM daily WHERE day='%s' AND timeperiod=4""" % (currentDay)
    sql5 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM daily WHERE day='%s' AND timeperiod=5""" % (currentDay)

    sql6 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM weekly WHERE day='Monday'"""
    sql7 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM weekly WHERE day='Tuesday'"""
    sql8 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM weekly WHERE day='Wednesday'"""
    sql9 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM weekly WHERE day='Thursday'"""
    sql10 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM weekly WHERE day='Friday'"""

    try:

        cursor.execute(sql1)
        timePeriodAverage[0] = cursor.fetchall()[0][0]
        cursor.execute(sql2)
        timePeriodAverage[1] = cursor.fetchall()[0][0]
        cursor.execute(sql3)
        timePeriodAverage[2] = cursor.fetchall()[0][0]
        cursor.execute(sql4)
        timePeriodAverage[3] = cursor.fetchall()[0][0]
        cursor.execute(sql5)
        timePeriodAverage[4] = cursor.fetchall()[0][0]

        cursor.execute(sql6)
        dayAverage[0] = cursor.fetchall()[0][0]
        cursor.execute(sql7)
        dayAverage[1] = cursor.fetchall()[0][0]
        cursor.execute(sql8)
        dayAverage[2] = cursor.fetchall()[0][0]
        cursor.execute(sql9)
        dayAverage[3] = cursor.fetchall()[0][0]
        cursor.execute(sql10)
        dayAverage[4] = cursor.fetchall()[0][0]

        db.commit()
    except Exception as e:
        print(e)
        print("Rollback")
        db.rollback()

    for i in range(5):
        if timePeriodAverage[i] == None:
            timePeriodAverage[i] = 0
        if dayAverage[i] == None:
            dayAverage[i] = 0

def updateFootfallGraph(but):
    """
    Depending on the button pressed, update the current footfall graph or switch to the other graph
    """

    global footfallGraphChoice

    if but == 0:
        plotWeeklyFootfall()
    else:
        plotDailyFootfall()

def increaseCustomerCount():
    """
    - Increase the customer count variable
    - Increase the corrosponding time period variable
    - Update the customer count label on the GUI
    """

    global customerCountInt
    global timePeriodCount

    customerCountInt = customerCountInt + 1
    customerCount.set(str(customerCountInt))

    baseTime = datetime.datetime.now().replace(hour=7, minute=0, second=0)
    currentTime = datetime.datetime.now()

    difference = ((currentTime - baseTime).total_seconds()) / 60

    if difference < 120:
        timePeriodCount[0] = timePeriodCount[0] + 1
    elif difference < 240:
        timePeriodCount[1] = timePeriodCount[1] + 1
    elif difference < 360:
        timePeriodCount[2] = timePeriodCount[2] + 1
    elif difference < 480:
        timePeriodCount[3] = timePeriodCount[3] + 1
    elif difference < 660:
        timePeriodCount[4] = timePeriodCount[4] + 1

def setupServer():
    """
    Set up the server for the footfall Pi to connect to
    """

    global socketError

    # Set up server
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host,port))
    except socket.error as msg:
        socketError = True
        print("Error when trying to bind")
        print(msg)
    else:
        print("Binding Successful")
        socketError = False


def getLiveFootfall():
    """
    Seperate thread to listen to the open socket for data from the footfall Pi
    """

    global s
    global conn
    global waiting_on_data

    while appClose == False:

        connected = False
        
        print("Start listening")
        s.listen(1)
        conn,address = s.accept()
        print("Connected to: ", address[0] + ":" + str(address[1]))

        if address[0] == '127.0.0.1':
            print("Application closed")
            conn.close()
            break

        if address[0] != '192.168.1.143' and address[0] != '192.168.1.118':
            print("Wrong IP address connected")
            conn.close()
        else:
            connected = True
            conn.settimeout(2)
            
            while appClose == False:
                
                try:
                    data = conn.recv(1)
                except socket.timeout as msg:    
                    continue
                except socket.error as msg:
                    waiting_on_data = False
                    print("Error when trying to receive: " + msg)
                else:
                    data = data.decode('utf-8')
                    if data == '': # Means the connection had closed
                        conn.close()
                        print("Disconnect")
                        conn.settimeout(None)
                        break
                    if data == "1":
                        increaseCustomerCount()

def changeFootfallWeekly(PIN):
    if GPIO.input(WEEK_BUTT) == 0:
        updateFootfallGraph(0)

def changeFootfallDaily(PIN):
    if GPIO.input(DAY_BUTT) == 0:
        updateFootfallGraph(1)

def increaseLight(PIN):

    global lightCount
    global lightCountMutex

    if lightCountMutex == False:

        lightCountMutex = True

        if GPIO.input(INC_LIGHT_BUTT) == 0:
            if lightCount < 5:
                lightCount = lightCount + 1

                if lightCount == 1:
                    GPIO.output(LED1,GPIO.HIGH)
                elif lightCount == 2:
                    GPIO.output(LED2,GPIO.HIGH)
                elif lightCount == 3:
                    GPIO.output(LED3,GPIO.HIGH)
                elif lightCount == 4:
                    GPIO.output(LED4,GPIO.HIGH)
                elif lightCount == 5:
                    GPIO.output(LED5,GPIO.HIGH)

        lightCountMutex = False

def decreaseLight(PIN):

    global lightCount
    global lightCountMutex

    if lightCountMutex == False:

        lightCountMutex = True

        if GPIO.input(DEC_LIGHT_BUTT) == 0:
            if lightCount > 0:
                lightCount = lightCount - 1

                if lightCount == 0:
                    GPIO.output(LED1,GPIO.LOW)
                elif lightCount == 1:
                    GPIO.output(LED2,GPIO.LOW)
                elif lightCount == 2:
                    GPIO.output(LED3,GPIO.LOW)
                elif lightCount == 3:
                    GPIO.output(LED4,GPIO.LOW)
                elif lightCount == 4:
                    GPIO.output(LED5,GPIO.LOW)

        lightCountMutex = False

# Container has 2 columns and 13 rows
container = tk.Frame(root, background='white')
container.pack(side="top", fill="both", expand = True)

# Set the minimum dimensions of the rows and columns
container.grid_columnconfigure(0, weight=1, minsize=480)
container.grid_columnconfigure(1, weight=1, minsize=720)

for row in range(13):
    container.grid_rowconfigure(row, weight=1, minsize=60)

##topContainer = tk.Frame(container,bg="white")
##topContainer.grid(column=0,row=0,rowspan=7,sticky='nesw')
##
##topContainer.grid_columnconfigure(0, weight=1)
##
##topContainer.grid_rowconfigure(0,weight=1)
##topContainer.grid_rowconfigure(7,weight=1)
##
##label = tk.Label(topContainer, text="Live Traffic Map/Videos",bg='white')
##label.grid(column=0,row=1)
##
##retrieveTest = tk.Button(topContainer, text = 'Start of Day', command = startOfDayDB)
##retrieveTest.grid(column=0,row=2)
##
##insertTest = tk.Button(topContainer, text = 'End of Day', command = endOfDayDB)
##insertTest.grid(column=0,row=3)
##
##updateFootfallButton = tk.Button(topContainer, text = 'Update Footfall', command = lambda: updateFootfallGraph(0))
##updateFootfallButton.grid(column=0,row=4)
##
##changeFootfall = tk.Button(topContainer, text = 'Change Footfall', command = lambda: updateFootfallGraph(1))
##changeFootfall.grid(column=0,row=5)
##
##addCustomer = tk.Button(topContainer, text = 'Add Customer', command = increaseCustomerCount)
##addCustomer.grid(column=0,row=6)

original = PIL.Image.open("images/rs-components.png")
resized = original.resize((514,427),PIL.Image.ANTIALIAS)
photo = ImageTk.PhotoImage(resized)

label = tk.Label(container, image=photo,bg='white')
label.grid(column=0,row=0,rowspan=7,sticky='nesw')

customersContainer = tk.Frame(container,bg='#482D60')
customersContainer.grid(column=0,row=7,rowspan=1,sticky='nesw')

customersContainer.grid_rowconfigure(0, weight=1)

customersContainer.grid_columnconfigure(0,weight=1)
customersContainer.grid_columnconfigure(4,weight=1)

customerCountLabel1 = tk.Label(customersContainer, text = 'Today:', fg='white', bg='#482D60', font='"DejaVu Sans" 14 bold')
customerCountLabel1.grid(column=1,row=0,rowspan=1,sticky='nesw')

customerCountLabel2 = tk.Label(customersContainer, textvariable=customerCount, fg='white', bg='#482D60', font='"DejaVu Sans" 14')
customerCountLabel2.grid(column=2,row=0,rowspan=1,sticky='nesw')

customerCountLabel3 = tk.Label(customersContainer, text = 'customers', fg='white', bg='#482D60', font='"DejaVu Sans" 14')
customerCountLabel3.grid(column=3,row=0,rowspan=1,sticky='nesw')

canvasFootfall = FigureCanvasTkAgg(figFootfall, container)
canvasFootfall.get_tk_widget().grid(column=0,row=8,rowspan=5,sticky='nesw',pady=(20,0))
canvasFootfall.get_tk_widget().configure(background='white',highlightcolor='white',highlightbackground='white')

canvas = FigureCanvasTkAgg(fig, container)
canvas.get_tk_widget().grid(column=1,row=0,rowspan=12,sticky='nesw')
canvas.get_tk_widget().configure(background='white',highlightcolor='white',highlightbackground='white')

label = tk.Label(container, text="Absolute Radio: American Idiot by Green Day",fg='white',bg='red',font='"DejaVu Sans" 12 bold')
label.grid(column=1,row=12,rowspan=1,sticky='nesw')

# Set up the button interrupts
GPIO.add_event_detect(WEEK_BUTT,GPIO.FALLING, callback = changeFootfallWeekly)
GPIO.add_event_detect(DAY_BUTT,GPIO.FALLING, callback = changeFootfallDaily)

GPIO.add_event_detect(INC_LIGHT_BUTT,GPIO.FALLING, callback = increaseLight, bouncetime=200)
GPIO.add_event_detect(DEC_LIGHT_BUTT,GPIO.FALLING, callback = decreaseLight, bouncetime=200)

# Initially run startOfDay to set up, then start the updateFootfall loop
startOfDayDB()
updateFootfall()

# Set the temperature/light graphs to be updated every second
aniOutside = animation.FuncAnimation(fig, animateOutside, interval=1000)
aniInside = animation.FuncAnimation(fig, animateInside, interval=180000)
aniLight = animation.FuncAnimation(fig, animateLight, interval=1000)

# Start with the weekly footfall graph
plotWeeklyFootfall()

# Set up the server to listen for a connection from the footfall Pi
setupServer()

# Set up the seperate thread to read data from the footfall Pi
t = threading.Thread(target = getLiveFootfall)
t.start()

def cleanupLEDS():
    GPIO.output(LED1,GPIO.LOW)
    GPIO.output(LED2,GPIO.LOW)
    GPIO.output(LED3,GPIO.LOW)
    GPIO.output(LED4,GPIO.LOW)
    GPIO.output(LED5,GPIO.LOW)

def on_close():
    """
    Clean everything up when the 'x' button is pressed

    - Close the socket
    - Stop the second thread
    - Close the connection to the database
    - Close the tkinter instance
    - Close the program
    """

    global appClose

    appClose = True
    if socketError == False:
        if connected == False:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host,port))
        elif connected == True:
            print("Client still connected when closing")
            conn.close()
    s.shutdown(1)
    print("Closing Socket")
    s.close()
    cleanupLEDS()
    GPIO.cleanup()
    db.close()
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW",  on_close)

# Start the main program loop
root.mainloop()
