# import the necessary packages
from __future__ import print_function
from PIL import Image
from PIL import ImageTk
from PIL import ImageDraw
import tkinter as tki
import threading
import datetime
import imutils
import cv2
import os
import pytesseract
import re

class PhotoBoothApp:
	def __init__(self, vs, outputPath):
		# store the video stream object and output path, then initialize
		# the most recently read frame, thread for reading frames, and
		# the thread stop event
		self.vs = vs
		self.outputPath = outputPath
		self.frame = None
		self.thread = None
		self.stopEvent = None
		
		self.menuScreen = True
		self.captureScreen = False
		self.infoScreen = False

		# initialize the root window and image panel
		self.root = tki.Tk()
		self.panel = None
		
		self.startBtn = tki.Button(self.root, text="Start", width = 20,
			command=self.startScanner)
		self.startBtn.pack(fill="both", expand="no", padx=10,
			pady=10)
		
		self.backBtn = tki.Button(self.root, text="Scan Again", width = 20,
			command=self.scanMode)
		self.backBtn.pack(fill="both", expand="no", padx=10,
			pady=10)
		
		self.backBtn.pack_forget()

		# create a button, that when pressed, will take the current
		# frame and save it to file
		self.btn = tki.Button(self.root, text="Capture!", width = 10,
			command=self.takeSnapshot)
		self.btn.pack(side="right", fill="both", expand="yes", padx=10,pady=10)
		
		self.btn.pack_forget()

		# start a thread that constantly pools the video sensor for
		# the most recently read frame
		self.stopEvent = threading.Event()
		#self.thread = threading.Thread(target=self.videoLoop, args=())
		#self.thread.start()
		
		#self.videoLoop()

		# set a callback to handle when the window is closed
		self.root.wm_title("Stock Scanner")
		self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

	def videoLoop(self):
		# DISCLAIMER:
		# I'm not a GUI developer, nor do I even pretend to be. This
		# try/except statement is a pretty ugly hack to get around
		# a RunTime error that Tkinter throws due to threading
		try:
			# keep looping over frames until we are instructed to stop
			if not self.stopEvent.is_set():
				# grab the frame from the video stream and resize it to
				# have a maximum width of 300 pixels
				self.frame = self.vs.read()
				self.frame = imutils.resize(self.frame, width=650)
		
				# OpenCV represents images in BGR order; however PIL
				# represents images in RGB order, so we need to swap
				# the channels, then convert to PIL and ImageTk format
				image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
				image = Image.fromarray(image)
				
				#cv2.rectangle(image,(400,0),(600,400),(0,255,0),10)
				draw = ImageDraw.Draw(image)
				draw.line([221,142,244,142],fill="red", width=5)
				draw.line([221,142,221,165],fill="red", width=5)
				draw.line([221,235,221,212],fill="red", width=5)
				draw.line([221,235,244,235],fill="red", width=5)
				draw.line([429,142,406,142],fill="red", width=5)
				draw.line([429,142,429,165],fill="red", width=5)
				draw.line([429,235,429,212],fill="red", width=5)
				draw.line([429,235,406,235],fill="red", width=5)
				
				draw.line([0,390,650,390],fill="red") # Shows buttom of camera
				del draw
				
				image = ImageTk.PhotoImage(image)
		
				# if the panel is not None, we need to initialize it
				if self.panel is None:
					self.panel = tki.Label(image=image)
					self.panel.image = image
					self.panel.pack(side="left", padx=10, pady=10)
		
				# otherwise, simply update the panel
				else:
					self.panel.configure(image=image)
					self.panel.image = image

		except RuntimeError as e:
			print("[INFO] caught a RuntimeError")
			
		if self.captureScreen == True:
                    self.panel.after(10,self.videoLoop)

	def takeSnapshot(self):

                # load the example image and convert it to grayscale
                image = self.frame.copy()[142:235, 221:429]
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                #cv2.imshow("Image", gray)

                #gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

                #gray = cv2.medianBlur(gray, 3)

                # write the grayscale image to disk as a temporary file so we can
                # apply OCR to it
                filename = "{}.png".format(os.getpid())
                cv2.imwrite(filename, gray)

                # load the image as a PIL/Pillow image, apply OCR, and then delete
                # the temporary file
                text = pytesseract.image_to_string(Image.open(filename))
                os.remove(filename)
                #print(text)
                
                matches = []
                checkOrder = []
                
                matches.append(re.findall(r"\d{3}\-\d{4}",text))
                matches.append(re.findall(r"\d{3}\-\d{3}",text))
                
                matches.append(re.findall(r"\d{7}",text))
                matches.append(re.findall(r"\d{6}",text))
                
                matches.append(re.findall(r"\d{3}\s\d{4}",text))
                matches.append(re.findall(r"\d{3}\s\d{3}",text))
                
                #print("Matched (XXX-XXXX): " + str(matches[0]))
                #print("Matched (XXX-XXX): " + str(matches[1]))
                #print("Matched (XXXXXXX): " + str(matches[2]))
                #print("Matched (XXXXXX): " + str(matches[3]))
                #print("Matched (XXX XXXX): " + str(matches[4]))
                #print("Matched (XXX XXX): " + str(matches[5]))
                
                for i in range(6):
                    for j in range(len(matches[i])):
                        checkOrder.append(matches[i][j])
                
                #print ("\nMatches: " + str(matches) + "\n")
                print ("\nCheck Order: " + str(checkOrder) + "\n")
##                
##                for i in range(len(checkOrder)):
##                    if getApi(checkOrder[i]) != '':
##                        outputValues = values
##                        break
##                    
##                if outputValues == '':
##                    print("Please try again, no product found")
##                else:
##                    print(outputValues)
                
                #cv2.imshow("Output", gray)
                
                if len(checkOrder) > 0:
                    self.btn.pack_forget()
                    self.panel.pack_forget()
                    self.backBtn.pack()
                    self.captureScreen = False
                    self.infoScreen = True

	def scanMode(self):
		self.backBtn.pack_forget()
		self.panel.pack(side="left", padx=10, pady=10)
		self.infoScreen = False
		self.captureScreen = True
		#self.panel = None
		self.videoLoop()
		self.btn.pack(side="right", fill="both", expand="yes", padx=10,pady=10)
		
	def startScanner(self):
		self.startBtn.pack_forget()
		#self.panel.pack()
		self.menuScreen = False
		self.captureScreen = True
		self.videoLoop()
		self.btn.pack(side="right", fill="both", expand="yes", padx=10,pady=10)

	def onClose(self):
		# set the stop event, cleanup the camera, and allow the rest of
		# the quit process to continue
		print("[INFO] closing...")
		self.stopEvent.set()
		self.vs.stop()
		self.root.quit()
