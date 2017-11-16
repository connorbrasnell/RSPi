import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.pyplot as plt
import time
import datetime
from datetime import date
import sys
import MySQLdb as sql
from dateutil.relativedelta import relativedelta

import tkinter as tk
from tkinter import ttk

db = sql.connect("localhost","RSPiUser","RSComponents","RSPi" )
cursor = db.cursor()

currentDay = "Monday"
currentDate = '1996-02-15'
dayAverage = [0,0,0,0,0]
timePeriodAverage = [0,0,0,0,0,0,0]
footfallWeekX = ['Mon','Tue','Wed','Thu','Fri']
footfallDayX = ['7:00am-','8:30am-','10:00am-','11:30am-','1:00pm-','2:30pm-','4:00pm-']

style.use("ggplot")

fig = plt.figure()
plt.subplots_adjust(bottom=0.05, top=0.91, hspace=0.4)

figFootfall = plt.figure(figsize=(4,2))
footfallAxis = figFootfall.add_subplot(1,1,1)

outsideTempAxis = fig.add_subplot(3,1,1)
insideTempAxis = fig.add_subplot(3,1,2)
lightAxis = fig.add_subplot(3,1,3)

outsideTempAxis.xaxis.set_visible(False)
insideTempAxis.xaxis.set_visible(False)
lightAxis.xaxis.set_visible(False)

def animateOutside(i):
    data = open("outsideTemp.txt","r").read()
    splitData = data.split('\n')

    xsO = []
    ysO = []

    currentY = 0

    for eachLine in splitData:
        if len(eachLine) > 1:
            x,y = eachLine.split(',')
            xsO.append(int(x))
            ysO.append(int(y))
            currentY = y

    currentY = currentY + '\N{DEGREE SIGN}C'

    outsideTempAxis.cla()

    outsideTempAxis.set_title('Outside Temperature', fontsize=12)
    outsideTempAxis.set_ylabel('Degrees (\N{DEGREE SIGN}C)', fontsize=10)
    outsideTempAxis.annotate(currentY, xy=(0.92, 1.05), xycoords='axes fraction')

    outsideTempAxis.plot(xsO,ysO)

def animateInside(i):
    data = open("insideTemp.txt","r").read()
    splitData = data.split('\n')

    xsI = []
    ysI = []

    currentY = 0

    for eachLine in splitData:
        if len(eachLine) > 1:
            x,y = eachLine.split(',')
            xsI.append(int(x))
            ysI.append(int(y))
            currentY = y

    currentY = currentY + '\N{DEGREE SIGN}C'

    insideTempAxis.cla()
    insideTempAxis.set_title('Inside Temperature', fontsize=12)
    insideTempAxis.set_ylabel('Degrees (\N{DEGREE SIGN}C)', fontsize=10)
    insideTempAxis.annotate(currentY, xy=(0.92, 1.05), xycoords='axes fraction')
    insideTempAxis.plot(xsI,ysI)

def animateLight(i):
    data = open("lightLevel.txt","r").read()
    splitData = data.split('\n')

    xsL = []
    ysL = []

    currentY = 0

    for eachLine in splitData:
        if len(eachLine) > 1:
            x,y = eachLine.split(',')
            xsL.append(int(x))
            ysL.append(int(y))
            currentY = y

    currentY = currentY + ' Lux'

    lightAxis.cla()
    lightAxis.set_title('Light Level', fontsize=12)
    lightAxis.set_ylabel('Lux', fontsize=10)
    lightAxis.annotate(currentY, xy=(0.84, 1.05), xycoords='axes fraction')
    lightAxis.plot(xsL,ysL)

def plotWeeklyFootfall():

    footfallAxis.clear()
    footfallAxis.set_title('Weekly Footfall', fontsize=12)
    footfallAxis.set_ylabel('Footfall', fontsize=10)
    footfallAxis.set_xlabel('Day', fontsize=10)
    footfallAxis.bar(footfallWeekX,dayAverage, 0.5)
    footfallAxis.set_xticklabels(footfallWeekX)

    figFootfall.canvas.draw()

def plotDailyFootfall():
    footfallAxis.cla()
    footfallAxis.set_title('Daily Footfall', fontsize=12)
    footfallAxis.set_ylabel('Footfall', fontsize=10)
    footfallAxis.set_xlabel('Time', fontsize=10)
    footfallAxis.plot(footfallDayX,timePeriodAverage)

def endOfDayDB():

    global currentDate

    data = open("daysFootfall.txt","r").read()
    splitData = data.split('\n')

    footfallValues = []

    for eachLine in splitData:
        if eachLine != '':
            footfallValues.append(int(eachLine))

    #currentDate = time.strftime('%Y-%m-%d')

    try:
        cursor.execute("INSERT INTO weekly(day, todaydate, count) VALUES (%s,%s,%s)", (currentDay, currentDate, footfallValues[0]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 1, footfallValues[1]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 2, footfallValues[2]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 3, footfallValues[3]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 4, footfallValues[4]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 5, footfallValues[5]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 6, footfallValues[6]))
        cursor.execute("INSERT INTO daily(day, todaydate, timeperiod, count) VALUES (%s,%s,%s,%s)", (currentDay, currentDate, 7, footfallValues[7]))

        db.commit()
    except Exception as e:
        print(e)
        print("Rollback")
        db.rollback()

def startOfDayDB():

    global currentDate
    global currentDay
    global dayAverage
    global timePeriodAverage

    currentDate = time.strftime('%Y-%m-%d')
    sixMonthsAgo = date.today() + relativedelta(months=-6)

    currentDayInt = datetime.datetime.today().weekday()
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

    sql1 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM weekly GROUP BY day"""

    sql2 = """SELECT CAST(AVG(count) AS UNSIGNED) FROM daily WHERE day='%s' GROUP BY timeperiod""" % (currentDay)

    try:

        cursor.execute(sql1)
        results = cursor.fetchall()

        dayAverage[0] = results[0][0]
        dayAverage[1] = results[1][0]
        dayAverage[2] = results[2][0]
        dayAverage[3] = results[3][0]
        dayAverage[4] = results[4][0]

        cursor.execute(sql2)
        results = cursor.fetchall()

        timePeriodAverage[0] = results[0][0]
        timePeriodAverage[1] = results[1][0]
        timePeriodAverage[2] = results[2][0]
        timePeriodAverage[3] = results[3][0]
        timePeriodAverage[4] = results[4][0]
        timePeriodAverage[5] = results[5][0]
        timePeriodAverage[6] = results[6][0]

        db.commit()
    except Exception as e:
        print(e)
        print("Rollback")
        db.rollback()

    print("Day Average: ", dayAverage)
    print("Time Period Average: ", timePeriodAverage)


root = tk.Tk()

container = tk.Frame(root)
frame = tk.Frame(container, borderwidth=5, relief="sunken", width=200, height=100)
container.grid(column=0, row=0)



#tk.Tk.wm_title(self, "RS Pi")

#container = tk.Frame(self)
#container.pack(side="top", fill="both", expand = True)
# Container has 2 columns and 13 rows

for col in range(2):
    container.grid_columnconfigure(col, weight=1)

for row in range(13):
    container.grid_rowconfigure(row, weight=1)

topContainer = tk.Frame(container,bg="skyblue")
topContainer.grid(column=0,row=0,rowspan=7,sticky='nesw')

#label = tk.Label(container, text="Live Traffic Map/Videos",bg='skyblue')
#label.grid(column=0,row=0,rowspan=7,sticky='nesw')

label = tk.Label(topContainer, text="Live Traffic Map/Videos",bg='skyblue')
label.grid(column=0,row=0)

retrieveTest = tk.Button(topContainer, text = 'Start of Day', command = startOfDayDB)
retrieveTest.grid(column=0,row=1)

insertTest = tk.Button(topContainer, text = 'End of Day', command = endOfDayDB)
insertTest.grid(column=0,row=2)

updateFootfall = tk.Button(topContainer, text = 'Update Footfall', command = plotWeeklyFootfall)
updateFootfall.grid(column=0,row=3)

label = tk.Label(container, text="Today: 43 Customers",bg='orange')
label.grid(column=0,row=7,rowspan=1,sticky='nesw')

#label = tk.Label(container, text="Footfall Graphs",fg='white',bg='red')
#label.grid(column=0,row=8,rowspan=5,sticky='nesw')

canvasFootfall = FigureCanvasTkAgg(figFootfall, container)
canvasFootfall.get_tk_widget().grid(column=0,row=8,rowspan=5,sticky='nesw')

canvas = FigureCanvasTkAgg(fig, container)
canvas.get_tk_widget().grid(column=1,row=0,rowspan=12,sticky='nesw')

label = tk.Label(container, text="Absolute Radio: American Idiot by Green Day",fg='white',bg='red',font='bold')
label.grid(column=1,row=12,rowspan=1,sticky='nesw')



aniOutside = animation.FuncAnimation(fig, animateOutside, interval=1000)
aniInside = animation.FuncAnimation(fig, animateInside, interval=1000)
aniLight = animation.FuncAnimation(fig, animateLight, interval=1000)

plotWeeklyFootfall()

def on_close():
    db.close()
    display.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW",  on_close)

root.mainloop()
