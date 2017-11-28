# import the necessary packages
from __future__ import print_function
from PIL import Image
from PIL import ImageTk
import tkinter as tki
import threading
import datetime
import imutils
import cv2
import os
import pytesseract

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

		# initialize the root window and image panel
		self.root = tki.Tk()
		self.panel = None

		# create a button, that when pressed, will take the current
		# frame and save it to file
		btn = tki.Button(self.root, text="Snapshot!",
			command=self.takeSnapshot)
		btn.pack(side="bottom", fill="both", expand="yes", padx=10,
			pady=10)

		# start a thread that constantly pools the video sensor for
		# the most recently read frame
		self.stopEvent = threading.Event()
		#self.thread = threading.Thread(target=self.videoLoop, args=())
		#self.thread.start()
		self.videoLoop()

		# set a callback to handle when the window is closed
		self.root.wm_title("PyImageSearch PhotoBooth")
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
				self.frame = imutils.resize(self.frame, width=300)
		
				# OpenCV represents images in BGR order; however PIL
				# represents images in RGB order, so we need to swap
				# the channels, then convert to PIL and ImageTk format
				image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
				image = Image.fromarray(image)
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
		self.panel.after(10,self.videoLoop)

	def takeSnapshot(self):
                # grab the current timestamp and use it to construct the
                # output path
                ts = datetime.datetime.now()
                filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
                p = os.path.sep.join((self.outputPath, filename))

                # save the file
                cv2.imwrite(p, self.frame.copy())
                print("[INFO] saved {}".format(filename))

                fileToParse = "camera_output/" + filename

                # load the example image and convert it to grayscale
                #image = cv2.imread("camera_output/4.jpg")
                image = cv2.imread(fileToParse)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                #cv2.imshow("Image", gray)

                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

                gray = cv2.medianBlur(gray, 3)

                # write the grayscale image to disk as a temporary file so we can
                # apply OCR to it
                filename = "{}.png".format(os.getpid())
                cv2.imwrite(filename, gray)

                # load the image as a PIL/Pillow image, apply OCR, and then delete
                # the temporary file
                text = pytesseract.image_to_string(Image.open(filename))
                os.remove(filename)
                print(text)
                
                
                
                #cv2.imshow("Output", gray)

	def onClose(self):
		# set the stop event, cleanup the camera, and allow the rest of
		# the quit process to continue
		print("[INFO] closing...")
		self.stopEvent.set()
		self.vs.stop()
		self.root.quit()